"""TypedDict workflow state definition for LangGraph orchestration."""

from typing import Any, Dict, List, Optional, TypedDict
from src.schemas.evidence import EvidenceItem, SourceMetadata
from src.schemas.report import FinalReport
from src.schemas.research import ResearchPlan, SearchQuery, VerificationResult


class ResearchState(TypedDict):
    """The unified strongly-typed workflow state passed across all agent nodes."""

    # Input & Configuration
    question: str
    iteration: int
    max_iterations: int

    # Agent Outputs
    plan: Optional[ResearchPlan]
    search_queries: List[SearchQuery]
    sources: List[SourceMetadata]
    evidence: List[EvidenceItem]
    analysis: Dict[str, Any]
    verification: Optional[VerificationResult]
    missing_topics: List[str]
    final_report: Optional[FinalReport]

    # Diagnostics & Metadata
    errors: List[str]
    metadata: Dict[str, Any]
