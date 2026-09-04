"""Verification Agent responsible for evaluating research quality, evidence sufficiency, and gap detection."""

from typing import Any, Dict, List, Optional
from google import genai

from src.agents.base import BaseAgent
from src.schemas.evidence import EvidenceItem, SourceMetadata
from src.schemas.research import ResearchPlan, SearchQuery, VerificationResult
from src.utils.logging import logger

VERIFIER_SYSTEM_INSTRUCTION = """
You are a Principal Research Verification & Fact-Checking Auditor.
Your mandate is to rigorously evaluate whether accumulated research evidence is sufficient, credible, and comprehensive enough to publish an authoritative, production-grade intelligence report.

Evaluation Criteria:
1. Coverage: Are all subquestions from the research plan adequately answered?
2. Source Diversity & Credibility: Are there multiple authoritative sources (news, government, academic, industry)?
3. Factual Grounding: Are key claims backed by specific data points, quotes, or statistics?
4. Completeness: Are there glaring gaps in key players, technologies, market sizing, opportunities, or risks?

Decision Rules:
- If evidence is thorough and covers the objective well -> is_sufficient = True (confidence >= 0.85).
- If key areas are unaddressed and need follow-up research -> is_sufficient = False (confidence < 0.80), list specific missing_topics and targeted suggested_queries.
- Never approve vague or empty research.
"""


class VerifierAgent(BaseAgent):
    """Agent that audits research sufficiency and triggers additional research loops if needed."""

    def __init__(self, client: Optional[genai.Client] = None, mock_mode: bool = False):
        super().__init__(
            name="ResearchVerifier",
            system_instruction=VERIFIER_SYSTEM_INSTRUCTION,
            client=client,
            mock_mode=mock_mode,
        )

    def verify(
        self,
        question: str,
        plan: ResearchPlan,
        sources: List[SourceMetadata],
        evidence: List[EvidenceItem],
        analysis: Dict[str, Any],
        iteration: int = 1,
        max_iterations: int = 3,
    ) -> VerificationResult:
        """Evaluate evidence completeness and decide whether more research iterations are required."""
        logger.info(
            f"[Verifier] Evaluating research sufficiency (Iteration {iteration}/{max_iterations})..."
        )

        if self.mock_mode:
            return self._mock_verification(iteration, max_iterations)

        # Baseline heuristic checks
        if not evidence or len(sources) < 2:
            logger.info("[Verifier] Insufficient evidence count or source diversity. Flagging for more research.")
            return VerificationResult(
                is_sufficient=False,
                confidence=0.4,
                missing_topics=["Comprehensive empirical data and multi-source corroboration"],
                claims_needing_verification=["General market statistics and player landscape"],
                reason=f"Insufficient source diversity ({len(sources)} sources) and evidence items ({len(evidence)} items).",
                suggested_queries=[
                    SearchQuery(
                        query=f"{question} market size data companies",
                        rationale="Broaden evidence base across reputable industry publications.",
                        priority=1,
                    )
                ],
            )

        # Build context for LLM verification
        sources_summary = "\n".join(
            [f"- [{s.id}] {s.title} ({s.domain}, type: {s.source_type}, rel: {s.reliability_score})" for s in sources]
        )
        evidence_summary = "\n".join(
            [f"- [{e.source_id}] {e.claim}" for e in evidence[:20]]
        )

        prompt = (
            f"Original Research Question:\n\"{question}\"\n\n"
            f"Research Plan Subquestions:\n"
            + "\n".join([f"- {sq.id}: {sq.question}" for sq in plan.subquestions])
            + f"\n\nCurrent Iteration: {iteration} of max {max_iterations}\n\n"
            f"Sources Evaluated ({len(sources)}):\n{sources_summary}\n\n"
            f"Evidence Items ({len(evidence)}):\n{evidence_summary}\n\n"
            f"Analysis Themes: {', '.join([t.get('theme', '') for t in analysis.get('key_themes', [])])}\n\n"
            f"Audit the evidence. Is this research sufficient to draft a definitive report? "
            f"If not, formulate specific suggested_queries for missing areas."
        )

        try:
            result = self.generate_structured_output(
                prompt=prompt,
                schema=VerificationResult,
                temperature=0.1,
            )
            # Safeguard: if reached max_iterations, force completion
            if iteration >= max_iterations and not result.is_sufficient:
                logger.info(
                    f"[Verifier] Max iterations ({max_iterations}) reached. Overriding is_sufficient to True for report synthesis."
                )
                result.is_sufficient = True
                result.reason += " (Reached maximum configured research iterations limit)."

            logger.info(
                f"[Verifier] Decision: is_sufficient={result.is_sufficient}, confidence={result.confidence:.2f}, reason: {result.reason[:80]}..."
            )
            return result

        except Exception as e:
            logger.error(f"[Verifier] Real verification failed: {e}")
            raise RuntimeError(f"Verifier Agent failed: {str(e)}")

    def _mock_verification(self, iteration: int, max_iterations: int) -> VerificationResult:
        """Deterministic verification fallback for offline testing."""
        if iteration == 1 and max_iterations > 1:
            return VerificationResult(
                is_sufficient=False,
                confidence=0.72,
                missing_topics=["Specific sovereign AI initiatives and vertical-specific enterprise adoption cases"],
                claims_needing_verification=["Capital deployment figures across private vs public funds"],
                reason="Initial evidence is solid but requires deeper verification of recent commercial announcements.",
                suggested_queries=[
                    SearchQuery(
                        query="Saudi Arabia AI automation vertical use cases enterprise STC Aramco",
                        rationale="Target specific commercial enterprise deployments.",
                        priority=1,
                    )
                ],
            )
        else:
            return VerificationResult(
                is_sufficient=True,
                confidence=0.91,
                missing_topics=[],
                claims_needing_verification=[],
                reason="All core subquestions are comprehensively supported by verified evidence.",
                suggested_queries=[],
            )
