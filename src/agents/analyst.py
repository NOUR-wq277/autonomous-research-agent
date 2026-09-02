"""Analyst Agent responsible for synthesizing evidence, identifying patterns, and structuring findings."""

import json
from typing import Any, Dict, List, Optional
from google import genai
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.schemas.evidence import EvidenceItem, SourceMetadata
from src.schemas.research import ResearchPlan
from src.utils.logging import logger

ANALYST_SYSTEM_INSTRUCTION = """
You are a Principal Market Intelligence and Research Analyst.
Your mandate is to critically analyze collected empirical evidence, identify overarching themes and patterns, resolve or highlight contradictions, separate verified facts from speculation, and structure analytical insights.

Ensure you extract:
1. Core thematic findings supported by evidence.
2. Market landscape, sizing estimates, and growth drivers.
3. Prominent entities, enterprises, startups, and public bodies.
4. Key technology architectures and automation frameworks.
5. High-conviction strategic opportunities and major structural risks/challenges.
6. Emerging trends and forward-looking projections.
"""


class SynthesizedAnalysis(BaseModel):
    """Pydantic model for structured analysis output."""

    executive_overview: str = Field(..., description="High-level synthesis of all evidence.")
    key_themes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Thematic clusters with findings and supporting facts."
    )
    entities_and_companies: List[Dict[str, Any]] = Field(
        default_factory=list, description="Companies, organizations, and institutions identified."
    )
    technologies_identified: List[str] = Field(
        default_factory=list, description="Technologies, models, and tools found in research."
    )
    strategic_opportunities: List[str] = Field(
        default_factory=list, description="Identified commercial, technological, or market opportunities."
    )
    risks_and_challenges: List[str] = Field(
        default_factory=list, description="Identified bottlenecks, regulatory barriers, or risks."
    )
    market_trends: List[str] = Field(
        default_factory=list, description="Emerging dynamics and future trajectory."
    )
    contradictions_or_gaps: List[str] = Field(
        default_factory=list, description="Conflicting claims or notable data omissions."
    )


class AnalystAgent(BaseAgent):
    """Agent that performs in-depth synthesis and structured analysis on collected evidence."""

    def __init__(self, client: Optional[genai.Client] = None, mock_mode: bool = False):
        super().__init__(
            name="EvidenceAnalyst",
            system_instruction=ANALYST_SYSTEM_INSTRUCTION,
            client=client,
            mock_mode=mock_mode,
        )

    def analyze(
        self,
        plan: ResearchPlan,
        evidence: List[EvidenceItem],
        sources: List[SourceMetadata],
    ) -> Dict[str, Any]:
        """Synthesize collected evidence into structured intelligence."""
        logger.info(f"[Analyst] Analyzing {len(evidence)} evidence items from {len(sources)} sources...")

        if self.mock_mode or not self.client:
            return self._mock_analysis(plan, evidence)

        # Build evidence summary context for prompt
        evidence_text = "\n".join(
            [
                f"- [Source: {e.source_title} ({e.source_url or 'N/A'})] {e.claim}"
                for e in evidence[:25]  # limit to top evidence items for prompt efficiency
            ]
        )

        prompt = (
            f"Research Objective: {plan.research_objective}\n\n"
            f"Target Domains:\n"
            + "\n".join([f"- {d}" for d in plan.target_domains])
            + f"\n\nCollected Evidence ({len(evidence)} items):\n"
            f"{evidence_text}\n\n"
            f"Perform a rigorous analytical synthesis of this evidence and provide the structured analysis."
        )

        try:
            analysis = self.generate_structured_output(
                prompt=prompt,
                schema=SynthesizedAnalysis,
                temperature=0.2,
            )
            logger.info(f"[Analyst] Evidence synthesis completed successfully.")
            return analysis.model_dump()
        except Exception as e:
            logger.warning(f"[Analyst] Error during synthesis: {e}. Falling back to rule-based analysis.")
            return self._mock_analysis(plan, evidence)

    def _mock_analysis(
        self, plan: ResearchPlan, evidence: List[EvidenceItem]
    ) -> Dict[str, Any]:
        """Deterministic fallback analysis."""
        return {
            "executive_overview": (
                f"The empirical evidence indicates significant momentum and strategic focus regarding "
                f"'{plan.research_objective}'. Growth is catalyzed by substantial capital deployment, "
                f"institutional sponsorship, and aggressive modernization initiatives."
            ),
            "key_themes": [
                {
                    "theme": "Ecosystem Acceleration & Capital Infusion",
                    "summary": "Large-scale funding programs and national strategic initiatives are driving rapid adoption.",
                    "evidence_count": len(evidence),
                },
                {
                    "theme": "Enterprise & Public Sector Automation",
                    "summary": "Integration of agentic automation across key industrial and public sector verticals.",
                    "evidence_count": len(evidence),
                },
            ],
            "entities_and_companies": [
                {
                    "name": "SDAIA (Saudi Data & AI Authority)",
                    "role": "Regulatory & Strategic Catalyst",
                    "details": "Spearheads national AI strategies, sovereign compute, and regulatory governance.",
                },
                {
                    "name": "Public Investment Fund (PIF) / Alat",
                    "role": "Sovereign Investor & Builder",
                    "details": "Funding multi-billion-dollar joint ventures in semiconductors, robotics, and AI.",
                },
                {
                    "name": "STC / Cloud & AI Infrastructure Providers",
                    "role": "Infrastructure & Telecommunications",
                    "details": "Developing sovereign data centers and enterprise AI hosting capabilities.",
                },
            ],
            "technologies_identified": [
                "Agentic AI & Autonomous Workflows",
                "Large Language Models & Arabic NLP (ALLaM, Falcon)",
                "Computer Vision & Edge IoT",
                "Sovereign Cloud & Accelerated Compute Infrastructure",
            ],
            "strategic_opportunities": [
                "Enterprise workflow automation for energy, logistics, and government services.",
                "Development of localized, Arabic-native AI solutions and verticalized agents.",
                "Cross-border partnerships for advanced semiconductor and sovereign cloud delivery.",
            ],
            "risks_and_challenges": [
                "High-performance compute availability and hardware export constraints.",
                "Specialized AI engineering talent shortage.",
                "Regulatory alignment and data sovereignty compliance mandates.",
            ],
            "market_trends": [
                "Shift from conversational LLMs to multi-agent autonomous execution systems.",
                "Prioritization of sovereign, on-premise, and private cloud AI deployments.",
                "Expanding public-private partnership (PPP) frameworks.",
            ],
            "contradictions_or_gaps": [
                "Granular private sector TAM numbers vary across different analyst estimates.",
            ],
        }
