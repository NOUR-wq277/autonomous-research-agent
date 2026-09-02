"""Pydantic schemas for sources, evidence, and collected facts."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
    """Metadata tracking a discovered or cited web source."""

    id: str = Field(..., description="Unique source identifier, e.g., 'src_1'.")
    title: str = Field(..., description="Title of the web page or document.")
    url: Optional[str] = Field(None, description="Direct URL of the source if available.")
    domain: str = Field(default="web", description="Domain hostname (e.g. 'reuters.com').")
    source_type: str = Field(
        default="general_web",
        description="Type: official_government, academic_research, reputable_news, industry_report, general_web.",
    )
    reliability_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Estimated reliability score (0.0 to 1.0)."
    )
    published_date: Optional[str] = Field(None, description="Publication or access date if available.")


class EvidenceItem(BaseModel):
    """A specific factual claim or evidence snippet tied to a source."""

    id: str = Field(..., description="Unique evidence item identifier, e.g., 'ev_1'.")
    source_id: str = Field(..., description="ID of the parent SourceMetadata.")
    source_title: str = Field(..., description="Title of the source.")
    source_url: Optional[str] = Field(None, description="URL of the source.")
    claim: str = Field(..., description="The concrete factual point, statistic, or finding.")
    snippet: str = Field(..., description="Direct verbatim excerpt or summary from the source.")
    confidence: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Confidence in accuracy (0.0 to 1.0)."
    )
    relevance_topic: Optional[str] = Field(
        None, description="The topic/subquestion this evidence supports."
    )


class EvidenceCollection(BaseModel):
    """Aggregated container for all collected sources and evidence."""

    sources: List[SourceMetadata] = Field(default_factory=list, description="All tracked unique sources.")
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="All extracted evidence snippets.")

    def get_source_by_id(self, source_id: str) -> Optional[SourceMetadata]:
        """Find source metadata by ID."""
        for s in self.sources:
            if s.id == source_id:
                return s
        return None

    def add_source(self, source: SourceMetadata) -> None:
        """Add source if not already present by URL or title."""
        if not any(s.url == source.url and source.url is not None for s in self.sources):
            if not any(s.title.lower() == source.title.lower() for s in self.sources):
                self.sources.append(source)

    def add_evidence(self, evidence: EvidenceItem) -> None:
        """Add evidence item."""
        self.evidence_items.append(evidence)
