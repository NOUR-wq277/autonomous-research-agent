"""Unit tests for specialized agent components."""

import pytest
from src.agents.analyst import AnalystAgent
from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearcherAgent
from src.agents.verifier import VerifierAgent
from src.agents.writer import WriterAgent
from src.schemas.evidence import EvidenceItem, SourceMetadata
from src.schemas.research import ResearchPlan, SearchQuery


@pytest.fixture
def sample_plan():
    return ResearchPlan(
        research_objective="Investigate Enterprise AI in Saudi Arabia",
        target_domains=["Market Size", "Players", "Risks"],
        subquestions=[],
        search_queries=[
            SearchQuery(
                query="Saudi Arabia Enterprise AI players",
                rationale="Identify leading commercial actors",
                priority=1,
            )
        ],
    )


@pytest.fixture
def sample_sources():
    return [
        SourceMetadata(
            id="src_1",
            title="SDAIA National Strategy",
            url="https://sdaia.gov.sa",
            domain="sdaia.gov.sa",
            source_type="official_government",
            reliability_score=0.95,
        ),
        SourceMetadata(
            id="src_2",
            title="Reuters Tech Report",
            url="https://reuters.com/tech",
            domain="reuters.com",
            source_type="reputable_news",
            reliability_score=0.88,
        ),
    ]


@pytest.fixture
def sample_evidence(sample_sources):
    return [
        EvidenceItem(
            id="ev_1",
            source_id="src_1",
            source_title="SDAIA National Strategy",
            source_url="https://sdaia.gov.sa",
            claim="Vision 2030 aims to position Saudi Arabia among the top 15 AI nations globally.",
            snippet="Targeting top 15 global AI ranking with 20,000 specialists trained by 2030.",
            confidence=0.95,
        ),
        EvidenceItem(
            id="ev_2",
            source_id="src_2",
            source_title="Reuters Tech Report",
            source_url="https://reuters.com/tech",
            claim="Major investments into localized sovereign AI compute infrastructure.",
            snippet="Billions invested into high-performance computing centers.",
            confidence=0.88,
        ),
    ]


def test_planner_agent_mock():
    planner = PlannerAgent(mock_mode=True)
    plan = planner.plan("Analyze the robotics automation sector in Japan")

    assert plan.research_objective is not None
    assert len(plan.subquestions) >= 3
    assert len(plan.search_queries) >= 3
    assert plan.search_queries[0].priority == 1


def test_researcher_agent_mock(sample_plan):
    researcher = ResearcherAgent(mock_mode=True)
    sources, evidence = researcher.execute_research(queries=sample_plan.search_queries)

    assert len(sources) >= 2
    assert len(evidence) >= 2
    assert evidence[0].source_id == sources[0].id


def test_analyst_agent_mock(sample_plan, sample_sources, sample_evidence):
    analyst = AnalystAgent(mock_mode=True)
    analysis = analyst.analyze(
        plan=sample_plan,
        evidence=sample_evidence,
        sources=sample_sources,
    )

    assert "executive_overview" in analysis
    assert len(analysis["technologies_identified"]) >= 1
    assert len(analysis["strategic_opportunities"]) >= 1
    assert len(analysis["risks_and_challenges"]) >= 1


def test_verifier_agent_mock(sample_plan, sample_sources, sample_evidence):
    verifier = VerifierAgent(mock_mode=True)
    analysis = {"key_themes": [{"theme": "Growth"}]}

    # Iteration 1: should request follow-up if max_iterations > 1
    result_iter1 = verifier.verify(
        question="Saudi AI Market",
        plan=sample_plan,
        sources=sample_sources,
        evidence=sample_evidence,
        analysis=analysis,
        iteration=1,
        max_iterations=3,
    )
    assert result_iter1.is_sufficient is False
    assert len(result_iter1.suggested_queries) >= 1

    # Iteration 2: should approve sufficiency
    result_iter2 = verifier.verify(
        question="Saudi AI Market",
        plan=sample_plan,
        sources=sample_sources,
        evidence=sample_evidence,
        analysis=analysis,
        iteration=2,
        max_iterations=3,
    )
    assert result_iter2.is_sufficient is True
    assert result_iter2.confidence >= 0.85


def test_writer_agent_mock(sample_plan, sample_sources, sample_evidence):
    writer = WriterAgent(mock_mode=True)
    analysis = {
        "executive_overview": "Overview text",
        "entities_and_companies": [{"name": "SDAIA", "role": "Catalyst"}],
        "technologies_identified": ["Agents", "LLMs"],
        "strategic_opportunities": ["Automated ERP"],
        "risks_and_challenges": ["Compute availability"],
        "market_trends": ["Multi-agent systems"],
    }

    report = writer.write_report(
        question="Saudi AI Market",
        plan=sample_plan,
        sources=sample_sources,
        evidence=sample_evidence,
        analysis=analysis,
    )

    assert report.title is not None
    assert len(report.key_findings) >= 2
    assert len(report.sections) >= 2
    assert len(report.sources) == len(sample_sources)
    assert "# Strategic Intelligence Report" in report.full_markdown
