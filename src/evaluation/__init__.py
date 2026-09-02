"""Evaluation package initialization."""

from src.evaluation.dataset import BENCHMARK_DATASET, BenchmarkTestCase
from src.evaluation.evaluator import EvaluationMetrics, ResearchEvaluator

__all__ = [
    "BENCHMARK_DATASET",
    "BenchmarkTestCase",
    "EvaluationMetrics",
    "ResearchEvaluator",
]
