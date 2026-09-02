"""Pydantic schemas for research planning, queries, and verification."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Specific search query generated for research."""

    query: str = Field(..., description="The exact search string to query the web.")
    rationale: str = Field(..., description="Why this query is essential for the research objective.")
    subquestion_id: Optional[str] = Field(None, description="The ID of the subquestion this query addresses.")
    priority: int = Field(default=1, ge=1, le=5, description="Search priority from 1 (highest) to 5.")


class ResearchSubQuestion(BaseModel):
    """A sub-component research question breaking down the main objective."""

    id: str = Field(..., description="Unique subquestion identifier, e.g., 'SQ1'.")
    question: str = Field(..., description="The granular research question.")
    objective: str = Field(..., description="What specific data points or facts are needed.")
    suggested_search_directions: List[str] = Field(
        default_factory=list, description="Keywords or angles to explore."
    )
    priority: int = Field(default=1, ge=1, le=5, description="Priority from 1 (highest) to 5.")


class ResearchPlan(BaseModel):
    """The structured research plan produced by the Planner Agent."""

    research_objective: str = Field(..., description="Refined, comprehensive objective of the research.")
    target_domains: List[str] = Field(
        default_factory=list, description="Key domain areas to investigate (e.g., market size, regulation, key players)."
    )
    subquestions: List[ResearchSubQuestion] = Field(
        ..., description="List of decomposed research subquestions."
    )
    search_queries: List[SearchQuery] = Field(
        ..., description="Initial targeted search queries to execute."
    )
    initial_hypotheses: List[str] = Field(
        default_factory=list, description="Initial working hypotheses or assumptions to test."
    )


class VerificationResult(BaseModel):
    """Verification assessment produced by the Verifier Agent."""

    is_sufficient: bool = Field(
        ..., description="True if collected evidence is sufficient to produce an authoritative report."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score in the evidence quality and coverage (0.0 to 1.0)."
    )
    missing_topics: List[str] = Field(
        default_factory=list, description="Crucial topics, data points, or entities that lack sufficient evidence."
    )
    claims_needing_verification: List[str] = Field(
        default_factory=list, description="Specific factual claims that require secondary source corroboration."
    )
    reason: str = Field(
        ..., description="Detailed explanation of the sufficiency decision."
    )
    suggested_queries: List[SearchQuery] = Field(
        default_factory=list, description="Targeted follow-up search queries if research is insufficient."
    )
