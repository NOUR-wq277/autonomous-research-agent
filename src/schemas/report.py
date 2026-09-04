"""Pydantic schemas for final report generation, citations, and API communication."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.schemas.evidence import SourceMetadata


class Citation(BaseModel):
    """Specific citation marker in the final report."""

    citation_id: str = Field(..., description="Citation reference tag, e.g. '[1]'.")
    source_id: str = Field(..., description="Referenced source ID.")
    title: str = Field(..., description="Title of the source.")
    url: Optional[str] = Field(None, description="Direct URL if available.")
    claim_supported: str = Field(..., description="The factual claim this citation validates.")


class ReportSection(BaseModel):
    """A structured section within the research report."""

    title: str = Field(..., description="Section title (e.g., 'Executive Summary', 'Market Dynamics').")
    content: str = Field(..., description="Detailed markdown content of the section.")
    key_takeaways: List[str] = Field(default_factory=list, description="Bullet points summarizing the section.")
    citations: List[str] = Field(default_factory=list, description="List of citation tags used, e.g. ['[1]', '[2]'].")


class EntityInfo(BaseModel):
    """Organization or enterprise identified in research."""

    name: str = Field(..., description="Entity or company name.")
    role: str = Field(default="", description="Role and strategic focus in the ecosystem.")
    details: str = Field(default="", description="Key initiatives, technologies, or details.")


class FinalReport(BaseModel):
    """The complete structured research report."""

    title: str = Field(..., description="Professional title of the research report.")
    executive_summary: str = Field(..., description="High-level executive summary.")
    research_objective: str = Field(..., description="The core research mandate.")
    key_findings: List[str] = Field(..., description="Major strategic and factual takeaways.")
    sections: List[ReportSection] = Field(..., description="Body sections covering detailed analysis.")
    companies_entities: List[EntityInfo] = Field(
        default_factory=list, description="Entities, companies, or organizations identified."
    )
    technologies: List[str] = Field(default_factory=list, description="Key technologies and tools discussed.")
    opportunities: List[str] = Field(default_factory=list, description="Identified strategic business opportunities.")
    risks_challenges: List[str] = Field(default_factory=list, description="Identified risks, bottlenecks, or challenges.")
    market_trends: List[str] = Field(default_factory=list, description="Future projections and industry trends.")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations.")
    limitations: List[str] = Field(default_factory=list, description="Research boundaries or unverified gaps.")
    sources: List[SourceMetadata] = Field(default_factory=list, description="Complete bibliography of cited sources.")
    full_markdown: str = Field(..., description="Ready-to-publish full markdown text of the report.")


# API Request / Response models
class ResearchRequest(BaseModel):
    """API request payload to initiate autonomous research."""

    question: str = Field(
        ...,
        min_length=5,
        max_length=1500,
        description="The research question or topic for the autonomous agent to investigate.",
        json_schema_extra={"example": "Analyze the AI automation market in Saudi Arabia. Identify major players, opportunities, and risks."},
    )
    max_iterations: Optional[int] = Field(
        None, ge=1, le=5, description="Override default maximum research iterations."
    )


class ResearchResponse(BaseModel):
    """API response containing the synthesized research report and execution metadata."""

    status: str = Field(default="success", description="Execution status: success or error.")
    question: str = Field(..., description="The original research question.")
    report: FinalReport = Field(..., description="The comprehensive structured research report.")
    sources_count: int = Field(..., description="Total unique sources cited.")
    evidence_count: int = Field(..., description="Total verified evidence items collected.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metrics (duration, iterations, model).")


class HealthResponse(BaseModel):
    """API health check response model."""

    status: str = Field(default="ok")
    version: str = Field(default="1.0.0")
    primary_model: str
    available_models: List[str]
