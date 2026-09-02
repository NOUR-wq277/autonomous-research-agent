"""Evaluation framework for assessing research quality, citation coverage, source quality, and latency."""

import re
import time
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from src.evaluation.dataset import BENCHMARK_DATASET, BenchmarkTestCase
from src.schemas.report import FinalReport, ResearchResponse
from src.services.research_service import ResearchService
from src.utils.logging import logger


class EvaluationMetrics(BaseModel):
    """Calculated metrics for a single research execution."""

    test_case_id: str
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Completeness of required sections and themes.")
    source_quality_score: float = Field(..., ge=0.0, le=1.0, description="Average reliability score of cited sources.")
    citation_coverage: float = Field(..., ge=0.0, le=1.0, description="Proportion of key claims containing citations.")
    entity_coverage: float = Field(..., ge=0.0, le=1.0, description="Proportion of expected entities identified.")
    duration_seconds: float
    iterations: int
    total_sources: int
    total_evidence: int


class ResearchEvaluator:
    """Evaluates agent performance against benchmark datasets."""

    def __init__(self, service: ResearchService):
        self.service = service

    def evaluate_response(
        self,
        test_case: BenchmarkTestCase,
        response: ResearchResponse,
    ) -> EvaluationMetrics:
        """Calculate evaluation scores from a research response."""
        report = response.report

        # 1. Completeness Score: check presence and depth of key sections
        section_weights = [
            bool(report.executive_summary and len(report.executive_summary) > 100),
            bool(report.key_findings and len(report.key_findings) >= 3),
            bool(report.sections and len(report.sections) >= 2),
            bool(report.opportunities and len(report.opportunities) >= 2),
            bool(report.risks_challenges and len(report.risks_challenges) >= 2),
            bool(report.recommendations and len(report.recommendations) >= 2),
            bool(report.sources and len(report.sources) >= 2),
        ]
        completeness_score = round(sum(section_weights) / len(section_weights), 2)

        # 2. Source Quality Score: average reliability of all sources
        if report.sources:
            avg_rel = sum(s.reliability_score for s in report.sources) / len(report.sources)
            source_quality_score = round(avg_rel, 2)
        else:
            source_quality_score = 0.0

        # 3. Citation Coverage: check percentage of key findings containing [n]
        cited_findings = 0
        citation_pattern = r"\[\d+\]"
        for kf in report.key_findings:
            if re.search(citation_pattern, kf):
                cited_findings += 1
        citation_coverage = round(
            (cited_findings / len(report.key_findings)) if report.key_findings else 0.0, 2
        )

        # 4. Entity Coverage: check expected entities in full markdown
        matched_entities = 0
        text_lower = report.full_markdown.lower()
        for entity in test_case.expected_entities:
            if entity.lower() in text_lower:
                matched_entities += 1
        entity_coverage = round(
            (matched_entities / len(test_case.expected_entities)) if test_case.expected_entities else 1.0, 2
        )

        return EvaluationMetrics(
            test_case_id=test_case.id,
            completeness_score=completeness_score,
            source_quality_score=source_quality_score,
            citation_coverage=citation_coverage,
            entity_coverage=entity_coverage,
            duration_seconds=response.metadata.get("duration_seconds", 0.0),
            iterations=response.metadata.get("iterations", 1),
            total_sources=response.sources_count,
            total_evidence=response.evidence_count,
        )

    def run_benchmark(self, mock_mode: bool = True) -> List[EvaluationMetrics]:
        """Execute benchmark evaluation across all test cases."""
        results: List[EvaluationMetrics] = []
        logger.info(f"Starting Benchmark Evaluation across {len(BENCHMARK_DATASET)} test cases...")

        for tc in BENCHMARK_DATASET:
            logger.info(f"Running evaluation on '{tc.id}'...")
            response = self.service.run_research(tc.question)
            metrics = self.evaluate_response(tc, response)
            results.append(metrics)

        self._print_summary(results)
        return results

    def _print_summary(self, results: List[EvaluationMetrics]) -> None:
        """Print formatted benchmark summary table."""
        print("\n" + "=" * 80)
        print("  AUTONOMOUS RESEARCH AGENT - BENCHMARK EVALUATION RESULTS")
        print("=" * 80)
        print(
            f"{'Test Case ID':<22} | {'Complete':<9} | {'Src Qual':<9} | {'Citation':<9} | {'Entity':<7} | {'Iter':<5} | {'Latency':<7}"
        )
        print("-" * 80)

        for m in results:
            print(
                f"{m.test_case_id:<22} | {m.completeness_score:<9.2f} | {m.source_quality_score:<9.2f} | "
                f"{m.citation_coverage:<9.2f} | {m.entity_coverage:<7.2f} | {m.iterations:<5} | {m.duration_seconds:<7.2f}s"
            )

        avg_complete = sum(m.completeness_score for m in results) / len(results)
        avg_src = sum(m.source_quality_score for m in results) / len(results)
        avg_cite = sum(m.citation_coverage for m in results) / len(results)
        avg_entity = sum(m.entity_coverage for m in results) / len(results)
        avg_latency = sum(m.duration_seconds for m in results) / len(results)

        print("-" * 80)
        print(
            f"{'AVERAGE':<22} | {avg_complete:<9.2f} | {avg_src:<9.2f} | {avg_cite:<9.2f} | {avg_entity:<7.2f} | {'-':<5} | {avg_latency:<7.2f}s"
        )
        print("=" * 80 + "\n")


if __name__ == "__main__":
    service = ResearchService(mock_mode=True)
    evaluator = ResearchEvaluator(service)
    evaluator.run_benchmark(mock_mode=True)
