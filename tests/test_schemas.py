"""Unit tests for Pydantic data schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.evidence import EvidenceCollection, EvidenceItem, SourceMetadata
from src.schemas.report import FinalReport, ReportSection, ResearchRequest, ResearchResponse
from src.schemas.research import ResearchPlan, ResearchSubQuestion, SearchQuery, VerificationResult


def test_search_query_schema():
    sq = SearchQuery(
        query="AI market Saudi Arabia",
        rationale="Identify market size and growth drivers",
        priority=1,
    )
    assert sq.query == "AI market Saudi Arabia"
    assert sq.priority == 1


def test_research_subquestion_schema():
    subq = ResearchSubQuestion(
        id="SQ1",
        question="What are the key government initiatives?",
        objective="Find SDAIA and PIF strategies",
        suggested_search_directions=["SDAIA", "Vision 2030"],
        priority=1,
    )
    assert subq.id == "SQ1"
    assert len(subq.suggested_search_directions) == 2


def test_research_plan_schema():
    plan = ResearchPlan(
        research_objective="Comprehensive AI Market analysis",
        target_domains=["Market Size", "Startups"],
        subquestions=[
            ResearchSubQuestion(
                id="SQ1",
                question="What is the TAM?",
                objective="Identify market size",
                priority=1,
            )
        ],
        search_queries=[
            SearchQuery(
                query="Saudi AI market TAM",
                rationale="Quantify addressable market",
                priority=1,
            )
        ],
    )
    assert len(plan.subquestions) == 1
    assert len(plan.search_queries) == 1


def test_source_and_evidence_collection():
    src1 = SourceMetadata(
        id="src_1",
        title="Reuters: Saudi AI Investments",
        url="https://www.reuters.com/technology/saudi-ai",
        domain="reuters.com",
        source_type="reputable_news",
        reliability_score=0.9,
    )
    src2 = SourceMetadata(
        id="src_2",
        title="Reuters: Saudi AI Investments",
        url="https://www.reuters.com/technology/saudi-ai",
        domain="reuters.com",
    )

    ev1 = EvidenceItem(
        id="ev_1",
        source_id="src_1",
        source_title="Reuters",
        claim="Saudi Arabia plans a $40B AI fund.",
        snippet="Saudi Arabia plans a $40B AI fund according to official sources.",
        confidence=0.95,
    )

    col = EvidenceCollection()
    col.add_source(src1)
    col.add_source(src2)  # Should deduplicate
    assert len(col.sources) == 1

    col.add_evidence(ev1)
    assert len(col.evidence_items) == 1
    assert col.get_source_by_id("src_1") is not None
    assert col.get_source_by_id("non_existent") is None


def test_verification_result_schema():
    vr = VerificationResult(
        is_sufficient=True,
        confidence=0.92,
        missing_topics=[],
        claims_needing_verification=[],
        reason="Evidence is sufficient and verified across multiple authoritative sources.",
    )
    assert vr.is_sufficient is True
    assert vr.confidence == 0.92

    # Test confidence validation range
    with pytest.raises(ValidationError):
        VerificationResult(
            is_sufficient=True,
            confidence=1.5,  # Out of 0.0 - 1.0 bounds
            reason="Invalid",
        )


def test_final_report_schema():
    src = SourceMetadata(id="src_1", title="SDAIA Official", url="https://sdaia.gov.sa")
    report = FinalReport(
        title="AI Market Report",
        executive_summary="Summary text...",
        research_objective="Objective text...",
        key_findings=["Finding 1 [1]", "Finding 2 [1]"],
        sections=[
            ReportSection(
                title="Overview",
                content="Section body text...",
                key_takeaways=["Takeaway 1"],
                citations=["[1]"],
            )
        ],
        companies_entities=[{"name": "SDAIA", "role": "Catalyst"}],
        technologies=["LLMs", "Autonomous Agents"],
        opportunities=["Workflow Automation"],
        risks_challenges=["Compute Shortage"],
        market_trends=["Agentic AI"],
        recommendations=["Invest early"],
        limitations=["Market is nascent"],
        sources=[src],
        full_markdown="# Report...",
    )
    assert report.title == "AI Market Report"
    assert len(report.key_findings) == 2
    assert len(report.sources) == 1


def test_research_request_validation():
    req = ResearchRequest(question="What is the future of AI in healthcare?")
    assert len(req.question) > 5

    with pytest.raises(ValidationError):
        ResearchRequest(question="Hi")  # Too short (min_length=5)
