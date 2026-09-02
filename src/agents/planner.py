"""Research Planner Agent responsible for breaking down research objectives into actionable plans."""

from typing import Optional
from google import genai

from src.agents.base import BaseAgent
from src.schemas.research import ResearchPlan, ResearchSubQuestion, SearchQuery
from src.utils.logging import logger

PLANNER_SYSTEM_INSTRUCTION = """
You are an Elite Research Planning Architect.
Your mandate is to take complex, multi-faceted research requests and decompose them into an exhaustive, highly structured research plan.

Guidelines:
1. Deconstruct the user's research topic into 3-5 distinct, non-overlapping subquestions.
2. Formulate 3-5 highly targeted, keyword-dense search queries designed for modern search engines.
3. Ensure coverage of:
   - Market sizing, economics, and macroeconomic context
   - Key entities, market leaders, emerging startups, and government regulators
   - Core technologies, infrastructure, and automation frameworks
   - Strategic business opportunities, ROI drivers, and market gaps
   - Structural challenges, regulatory bottlenecks, and operational risks
4. Return ONLY valid structured output conforming strictly to the requested schema.
"""


class PlannerAgent(BaseAgent):
    """Agent that creates a structured research plan from a high-level research question."""

    def __init__(self, client: Optional[genai.Client] = None, mock_mode: bool = False):
        super().__init__(
            name="ResearchPlanner",
            system_instruction=PLANNER_SYSTEM_INSTRUCTION,
            client=client,
            mock_mode=mock_mode,
        )

    def plan(self, question: str) -> ResearchPlan:
        """Generate a structured research plan for the provided research question."""
        logger.info(f"[Planner] Generating research plan for: '{question}'")

        if self.mock_mode or not self.client:
            return self._mock_plan(question)

        prompt = (
            f"User Research Request:\n\"{question}\"\n\n"
            f"Create a comprehensive, production-grade research plan to thoroughly investigate this topic.\n"
            f"Generate specific, actionable subquestions and search queries."
        )

        try:
            plan = self.generate_structured_output(
                prompt=prompt,
                schema=ResearchPlan,
                temperature=0.2,
            )
            logger.info(
                f"[Planner] Created plan with {len(plan.subquestions)} subquestions and {len(plan.search_queries)} search queries."
            )
            return plan
        except Exception as e:
            logger.warning(f"[Planner] Error during structured planning: {e}. Using deterministic plan generator.")
            return self._mock_plan(question)

    def _mock_plan(self, question: str) -> ResearchPlan:
        """Deterministic plan fallback for testing or recovery."""
        return ResearchPlan(
            research_objective=f"Comprehensive strategic and market analysis of: {question}",
            target_domains=[
                "Market Dynamics and Growth Forecasts",
                "Key Players and Enterprise Ecosystem",
                "Technology Stack and Adoption Rates",
                "Opportunities, Risks, and Regulatory Landscape",
            ],
            subquestions=[
                ResearchSubQuestion(
                    id="SQ1",
                    question=f"What is the current market scale, key drivers, and government initiatives related to {question}?",
                    objective="Identify total addressable market, growth rates, and public sector backing.",
                    suggested_search_directions=["market size", "government strategy", "investments"],
                    priority=1,
                ),
                ResearchSubQuestion(
                    id="SQ2",
                    question=f"Who are the prominent companies, startups, and technology providers active in {question}?",
                    objective="Map the competitive landscape and key institutional players.",
                    suggested_search_directions=["major companies", "startups", "partnerships"],
                    priority=1,
                ),
                ResearchSubQuestion(
                    id="SQ3",
                    question=f"What are the primary strategic opportunities, technology trends, and operational challenges in {question}?",
                    objective="Determine high-ROI opportunities and major bottlenecks.",
                    suggested_search_directions=["business opportunities", "challenges", "future trends"],
                    priority=2,
                ),
            ],
            search_queries=[
                SearchQuery(
                    query=f"{question} market size growth key players",
                    rationale="Captures primary market scope and institutional landscape.",
                    subquestion_id="SQ1",
                    priority=1,
                ),
                SearchQuery(
                    query=f"{question} top companies technology solutions case studies",
                    rationale="Uncovers concrete commercial and technological implementations.",
                    subquestion_id="SQ2",
                    priority=1,
                ),
                SearchQuery(
                    query=f"{question} regulatory framework challenges business opportunities",
                    rationale="Identifies policy constraints and investment opportunities.",
                    subquestion_id="SQ3",
                    priority=2,
                ),
            ],
            initial_hypotheses=[
                f"Significant capital deployment is driving rapid adoption in {question}.",
                "Regulatory readiness and talent availability represent key growth dependencies.",
            ],
        )
