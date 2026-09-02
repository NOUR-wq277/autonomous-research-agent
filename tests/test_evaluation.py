"""Unit tests for the evaluation framework."""

import pytest
from src.evaluation.dataset import BENCHMARK_DATASET
from src.evaluation.evaluator import ResearchEvaluator
from src.services.research_service import ResearchService


def test_benchmark_dataset_integrity():
    assert len(BENCHMARK_DATASET) >= 3
    for tc in BENCHMARK_DATASET:
        assert tc.id is not None
        assert len(tc.question) > 10
        assert len(tc.expected_entities) >= 1
        assert len(tc.expected_themes) >= 1


def test_evaluator_metrics_calculation():
    service = ResearchService(mock_mode=True)
    evaluator = ResearchEvaluator(service)

    test_case = BENCHMARK_DATASET[0]
    response = service.run_research(test_case.question)
    metrics = evaluator.evaluate_response(test_case, response)

    assert metrics.test_case_id == test_case.id
    assert 0.0 <= metrics.completeness_score <= 1.0
    assert 0.0 <= metrics.source_quality_score <= 1.0
    assert 0.0 <= metrics.citation_coverage <= 1.0
    assert 0.0 <= metrics.entity_coverage <= 1.0
    assert metrics.total_sources >= 2
    assert metrics.total_evidence >= 2


def test_benchmark_suite_execution():
    service = ResearchService(mock_mode=True)
    evaluator = ResearchEvaluator(service)
    results = evaluator.run_benchmark(mock_mode=True)

    assert len(results) == len(BENCHMARK_DATASET)
    for m in results:
        assert m.completeness_score > 0.5
        assert m.source_quality_score > 0.5
