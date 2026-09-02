"""Benchmark evaluation dataset for the Autonomous Research Agent."""

from typing import Dict, List
from pydantic import BaseModel, Field


class BenchmarkTestCase(BaseModel):
    """A test case in the evaluation benchmark."""

    id: str = Field(..., description="Unique benchmark case ID.")
    category: str = Field(..., description="Research domain.")
    question: str = Field(..., description="The user research prompt.")
    expected_entities: List[str] = Field(
        default_factory=list, description="Key entities or institutions that should be identified."
    )
    expected_themes: List[str] = Field(
        default_factory=list, description="Core themes or topics expected in thorough research."
    )


BENCHMARK_DATASET: List[BenchmarkTestCase] = [
    BenchmarkTestCase(
        id="saudi_ai_market",
        category="Market Intelligence",
        question=(
            "Analyze the AI automation market in Saudi Arabia. "
            "Identify major players, government initiatives, opportunities, risks, and market trends."
        ),
        expected_entities=["SDAIA", "PIF", "Alat", "STC", "Aramco"],
        expected_themes=["Vision 2030", "Sovereign AI", "Arabic LLMs", "Enterprise Automation", "Data Sovereignty"],
    ),
    BenchmarkTestCase(
        id="quantum_finance",
        category="Deep Tech",
        question=(
            "Investigate the application of Quantum Computing in Financial Portfolio Optimization. "
            "Identify current algorithms, leading institutions, timeline for quantum advantage, and major limitations."
        ),
        expected_entities=["IBM", "D-Wave", "JPMorgan", "Goldman Sachs"],
        expected_themes=["QAOA", "Quantum Annealing", "NISQ Limitations", "Arbitrage", "Risk Modeling"],
    ),
    BenchmarkTestCase(
        id="devops_ai_agents",
        category="Software Engineering",
        question=(
            "Evaluate Autonomous AI Agents for DevOps and SRE Incident Remediation. "
            "Analyze current capabilities, production architectures, security risks, and market leaders."
        ),
        expected_entities=["PagerDuty", "Datadog", "Dynatrace"],
        expected_themes=["Root Cause Analysis", "Automated Rollbacks", "RBAC", "Self-Healing", "Hallucination Risk"],
    ),
]
