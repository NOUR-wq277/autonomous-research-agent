"""High-level orchestration service for executing end-to-end research workflows."""

import time
from typing import Any, Dict, Optional
from google import genai

from src.config.settings import get_settings
from src.graph.workflow import create_research_graph
from src.schemas.report import FinalReport, ResearchResponse
from src.utils.logging import logger


class ResearchService:
    """Service that executes the autonomous research workflow and tracks observability metrics."""

    def __init__(
        self,
        client: Optional[genai.Client] = None,
        mock_mode: bool = False,
    ):
        self.settings = get_settings()
        self.client = client
        self.mock_mode = mock_mode
        self.graph = create_research_graph(client=self.client, mock_mode=self.mock_mode)

    def run_research(
        self,
        question: str,
        max_iterations: Optional[int] = None,
    ) -> ResearchResponse:
        """Execute the full agentic research graph for a user question."""
        start_time = time.time()
        logger.info(f"========== Starting Autonomous Research Pipeline: '{question}' ==========")

        limit_iterations = max_iterations or self.settings.max_research_iterations

        # Initialize workflow state
        initial_state = {
            "question": question,
            "iteration": 0,
            "max_iterations": limit_iterations,
            "plan": None,
            "search_queries": [],
            "sources": [],
            "evidence": [],
            "analysis": {},
            "verification": None,
            "missing_topics": [],
            "final_report": None,
            "errors": [],
            "metadata": {
                "start_time": start_time,
                "model": self.settings.gemini_model,
            },
        }

        # Invoke LangGraph state machine
        final_state = self.graph.invoke(initial_state)

        duration = round(time.time() - start_time, 2)
        sources = final_state.get("sources", [])
        evidence = final_state.get("evidence", [])
        final_report: Optional[FinalReport] = final_state.get("final_report")
        iterations = final_state.get("iteration", 1)

        logger.info(
            f"========== Research Pipeline Finished in {duration}s ({iterations} iterations, "
            f"{len(sources)} sources, {len(evidence)} evidence items) =========="
        )

        if not final_report:
            raise RuntimeError("Pipeline failed to produce a final report.")

        response = ResearchResponse(
            status="success",
            question=question,
            report=final_report,
            sources_count=len(sources),
            evidence_count=len(evidence),
            metadata={
                "duration_seconds": duration,
                "iterations": iterations,
                "primary_model": self.settings.gemini_model,
                "errors": final_state.get("errors", []),
                "verification_confidence": (
                    final_state["verification"].confidence if final_state.get("verification") else 1.0
                ),
            },
        )

        return response
