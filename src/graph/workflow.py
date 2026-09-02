"""LangGraph StateGraph definition and workflow construction."""

import time
from typing import Any, Dict, List, Literal, Optional
from google import genai
from langgraph.graph import END, START, StateGraph

from src.agents.analyst import AnalystAgent
from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearcherAgent
from src.agents.verifier import VerifierAgent
from src.agents.writer import WriterAgent
from src.config.settings import get_settings
from src.graph.state import ResearchState
from src.schemas.research import SearchQuery
from src.utils.logging import logger


class ResearchWorkflowBuilder:
    """Builder class to construct and compile the LangGraph agentic research graph."""

    def __init__(
        self,
        client: Optional[genai.Client] = None,
        mock_mode: bool = False,
    ):
        self.settings = get_settings()
        self.client = client
        self.mock_mode = mock_mode

        # Initialize agents
        self.planner = PlannerAgent(client=self.client, mock_mode=self.mock_mode)
        self.researcher = ResearcherAgent(client=self.client, mock_mode=self.mock_mode)
        self.analyst = AnalystAgent(client=self.client, mock_mode=self.mock_mode)
        self.verifier = VerifierAgent(client=self.client, mock_mode=self.mock_mode)
        self.writer = WriterAgent(client=self.client, mock_mode=self.mock_mode)

    # --------------------------------------------------------
    # Node 1: Planner
    # --------------------------------------------------------
    def planner_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node that produces the structured research plan and initial queries."""
        logger.info(">>> [Workflow] Executing Planner Node")
        question = state["question"]
        try:
            plan = self.planner.plan(question)
            return {
                "plan": plan,
                "search_queries": plan.search_queries[: self.settings.max_search_queries],
            }
        except Exception as e:
            logger.error(f"[Workflow] Error in planner_node: {e}")
            return {
                "errors": state.get("errors", []) + [f"Planner error: {e}"],
            }

    # --------------------------------------------------------
    # Node 2: Researcher
    # --------------------------------------------------------
    def researcher_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node that executes web research using current search queries."""
        iteration = state.get("iteration", 0) + 1
        logger.info(f">>> [Workflow] Executing Researcher Node (Iteration {iteration})")

        queries = state.get("search_queries", [])
        existing_sources = state.get("sources", [])
        existing_evidence = state.get("evidence", [])

        try:
            sources, evidence = self.researcher.execute_research(
                queries=queries,
                existing_sources=existing_sources,
                existing_evidence=existing_evidence,
            )
            return {
                "iteration": iteration,
                "sources": sources,
                "evidence": evidence,
            }
        except Exception as e:
            logger.error(f"[Workflow] Error in researcher_node: {e}")
            return {
                "iteration": iteration,
                "errors": state.get("errors", []) + [f"Researcher error: {e}"],
            }

    # --------------------------------------------------------
    # Node 3: Analyst
    # --------------------------------------------------------
    def analyst_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node that performs analytical synthesis on collected evidence."""
        logger.info(">>> [Workflow] Executing Analyst Node")
        plan = state["plan"]
        evidence = state.get("evidence", [])
        sources = state.get("sources", [])

        try:
            analysis = self.analyst.analyze(
                plan=plan,
                evidence=evidence,
                sources=sources,
            )
            return {"analysis": analysis}
        except Exception as e:
            logger.error(f"[Workflow] Error in analyst_node: {e}")
            return {
                "errors": state.get("errors", []) + [f"Analyst error: {e}"],
            }

    # --------------------------------------------------------
    # Node 4: Verifier
    # --------------------------------------------------------
    def verifier_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node that audits evidence sufficiency and decides if more research is required."""
        logger.info(">>> [Workflow] Executing Verifier Node")
        question = state["question"]
        plan = state["plan"]
        sources = state.get("sources", [])
        evidence = state.get("evidence", [])
        analysis = state.get("analysis", {})
        iteration = state.get("iteration", 1)
        max_iterations = state.get("max_iterations", self.settings.max_research_iterations)

        try:
            verification = self.verifier.verify(
                question=question,
                plan=plan,
                sources=sources,
                evidence=evidence,
                analysis=analysis,
                iteration=iteration,
                max_iterations=max_iterations,
            )

            # If follow-up queries suggested, update search_queries for next iteration
            next_queries: List[SearchQuery] = []
            if not verification.is_sufficient and verification.suggested_queries:
                next_queries = verification.suggested_queries[: self.settings.max_search_queries]
            elif not verification.is_sufficient and verification.missing_topics:
                next_queries = [
                    SearchQuery(
                        query=f"{question} {topic}",
                        rationale=f"Deep dive into missing topic: {topic}",
                        priority=1,
                    )
                    for topic in verification.missing_topics[: self.settings.max_search_queries]
                ]

            return {
                "verification": verification,
                "missing_topics": verification.missing_topics,
                "search_queries": next_queries if next_queries else state.get("search_queries", []),
            }
        except Exception as e:
            logger.error(f"[Workflow] Error in verifier_node: {e}")
            return {
                "errors": state.get("errors", []) + [f"Verifier error: {e}"],
            }

    # --------------------------------------------------------
    # Node 5: Writer
    # --------------------------------------------------------
    def writer_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node that creates the final publication-ready research report."""
        logger.info(">>> [Workflow] Executing Writer Node")
        question = state["question"]
        plan = state["plan"]
        sources = state.get("sources", [])
        evidence = state.get("evidence", [])
        analysis = state.get("analysis", {})

        try:
            final_report = self.writer.write_report(
                question=question,
                plan=plan,
                sources=sources,
                evidence=evidence,
                analysis=analysis,
            )
            return {"final_report": final_report}
        except Exception as e:
            logger.error(f"[Workflow] Error in writer_node: {e}")
            return {
                "errors": state.get("errors", []) + [f"Writer error: {e}"],
            }

    # --------------------------------------------------------
    # Conditional Edge Router
    # --------------------------------------------------------
    def should_continue_research(
        self, state: ResearchState
    ) -> Literal["researcher", "writer"]:
        """Conditional routing decision: loop back to researcher or continue to writer."""
        verification = state.get("verification")
        iteration = state.get("iteration", 1)
        max_iterations = state.get("max_iterations", self.settings.max_research_iterations)

        if not verification:
            logger.warning("[Router] No verification found; proceeding to writer.")
            return "writer"

        if not verification.is_sufficient and iteration < max_iterations:
            logger.info(
                f"[Router] Evidence insufficient ({verification.reason[:60]}...). "
                f"Looping back to Researcher (Iteration {iteration + 1}/{max_iterations})."
            )
            return "researcher"

        logger.info(
            f"[Router] Evidence sufficient or max iterations ({iteration}/{max_iterations}) reached. "
            f"Routing to Writer Agent."
        )
        return "writer"

    # --------------------------------------------------------
    # Graph Construction
    # --------------------------------------------------------
    def build_graph(self):
        """Construct and compile the LangGraph agent state machine."""
        workflow = StateGraph(ResearchState)

        # Add Nodes
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("researcher", self.researcher_node)
        workflow.add_node("analyst", self.analyst_node)
        workflow.add_node("verifier", self.verifier_node)
        workflow.add_node("writer", self.writer_node)

        # Add Edges
        workflow.add_edge(START, "planner")
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "analyst")
        workflow.add_edge("analyst", "verifier")

        # Conditional Edge from Verifier
        workflow.add_conditional_edges(
            "verifier",
            self.should_continue_research,
            {
                "researcher": "researcher",
                "writer": "writer",
            },
        )

        workflow.add_edge("writer", END)

        return workflow.compile()


def create_research_graph(
    client: Optional[genai.Client] = None,
    mock_mode: bool = False,
):
    """Factory helper to build and compile the research workflow graph."""
    builder = ResearchWorkflowBuilder(client=client, mock_mode=mock_mode)
    return builder.build_graph()
