"""Researcher Agent responsible for executing web queries and collecting structured evidence."""

import time
from typing import List, Optional, Tuple
from google import genai

from src.agents.base import BaseAgent
from src.schemas.evidence import EvidenceItem, SourceMetadata
from src.schemas.research import SearchQuery
from src.tools.web_search import WebSearchTool
from src.utils.logging import logger

RESEARCHER_SYSTEM_INSTRUCTION = """
You are a Lead Autonomous Web Researcher.
Your mission is to gather authoritative, timely, and verifiable empirical evidence from diverse web sources.
You systematically execute search queries, validate source credibility, and collect traceable facts.
"""


class ResearcherAgent(BaseAgent):
    """Agent that executes web searches, collects sources, and extracts structured evidence."""

    def __init__(
        self,
        client: Optional[genai.Client] = None,
        search_tool: Optional[WebSearchTool] = None,
        mock_mode: bool = False,
    ):
        super().__init__(
            name="WebResearcher",
            system_instruction=RESEARCHER_SYSTEM_INSTRUCTION,
            client=client,
            mock_mode=mock_mode,
        )
        self.search_tool = search_tool or WebSearchTool(client=self.client, mock_mode=mock_mode)

    def execute_research(
        self,
        queries: List[SearchQuery],
        existing_sources: Optional[List[SourceMetadata]] = None,
        existing_evidence: Optional[List[EvidenceItem]] = None,
    ) -> Tuple[List[SourceMetadata], List[EvidenceItem]]:
        """Execute a batch of search queries and merge new findings with existing evidence."""
        logger.info(f"[Researcher] Executing research across {len(queries)} queries...")

        all_sources: List[SourceMetadata] = list(existing_sources or [])
        all_evidence: List[EvidenceItem] = list(existing_evidence or [])

        seen_urls = {s.url for s in all_sources if s.url}
        seen_titles = {s.title.lower() for s in all_sources}
        seen_claims = {e.claim.lower() for e in all_evidence}

        for sq in queries:
            try:
                sources, evidence_items, _ = self.search_tool.search(
                    query=sq.query,
                    topic=sq.rationale,
                )

                # Deduplicate and register sources
                for source in sources:
                    if source.url and source.url in seen_urls:
                        continue
                    if source.title.lower() in seen_titles:
                        continue

                    all_sources.append(source)
                    if source.url:
                        seen_urls.add(source.url)
                    seen_titles.add(source.title.lower())

                # Deduplicate and register evidence items
                for ev in evidence_items:
                    claim_key = ev.claim.strip().lower()
                    if claim_key in seen_claims:
                        continue
                    all_evidence.append(ev)
                    seen_claims.add(claim_key)

                # Polite delay between searches to protect per-minute rate limits
                if not self.mock_mode:
                    time.sleep(2.5)

            except Exception as e:
                logger.error(f"[Researcher] Failed executing query '{sq.query}': {e}")

        logger.info(
            f"[Researcher] Research batch complete. Total accumulated sources: {len(all_sources)}, evidence: {len(all_evidence)}."
        )
        return all_sources, all_evidence
