"""Integration tests for the LangGraph workflow state machine and routing."""

import pytest
from src.graph.workflow import ResearchWorkflowBuilder, create_research_graph
from src.schemas.research import VerificationResult
from src.services.research_service import ResearchService


def test_research_graph_compilation():
    """Verify that the LangGraph state machine compiles without errors."""
    graph = create_research_graph(mock_mode=True)
    assert graph is not None


def test_research_workflow_end_to_end_mock():
    """Verify full end-to-end execution of the state machine."""
    service = ResearchService(mock_mode=True)
    response = service.run_research(
        question="Analyze the AI automation market in Saudi Arabia.",
        max_iterations=2,
    )

    assert response.status == "success"
    assert response.report is not None
    assert len(response.report.key_findings) >= 2
    assert response.sources_count >= 2
    assert response.evidence_count >= 2
    assert response.metadata["iterations"] >= 1
    assert response.metadata["duration_seconds"] >= 0


def test_workflow_conditional_routing_insufficient_vs_sufficient():
    """Test conditional edge decision logic."""
    builder = ResearchWorkflowBuilder(mock_mode=True)

    # Case 1: Insufficient and iteration < max_iterations -> should route to 'researcher'
    state_insufficient = {
        "question": "Test",
        "iteration": 1,
        "max_iterations": 3,
        "verification": VerificationResult(
            is_sufficient=False,
            confidence=0.6,
            missing_topics=["More data needed"],
            claims_needing_verification=[],
            reason="Missing data",
        ),
    }
    decision = builder.should_continue_research(state_insufficient)
    assert decision == "researcher"

    # Case 2: Insufficient but reached max_iterations -> should route to 'writer'
    state_max_iter = {
        "question": "Test",
        "iteration": 3,
        "max_iterations": 3,
        "verification": VerificationResult(
            is_sufficient=False,
            confidence=0.6,
            missing_topics=["More data"],
            claims_needing_verification=[],
            reason="Missing data",
        ),
    }
    decision = builder.should_continue_research(state_max_iter)
    assert decision == "writer"

    # Case 3: Sufficient -> should route to 'writer'
    state_sufficient = {
        "question": "Test",
        "iteration": 1,
        "max_iterations": 3,
        "verification": VerificationResult(
            is_sufficient=True,
            confidence=0.95,
            missing_topics=[],
            claims_needing_verification=[],
            reason="Complete",
        ),
    }
    decision = builder.should_continue_research(state_sufficient)
    assert decision == "writer"
