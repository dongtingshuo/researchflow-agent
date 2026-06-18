"""Evaluation and verification package."""

from src.evaluation.experiment import (
    DEFAULT_BENCHMARK_CASES,
    EVALUATION_METRICS,
    EVALUATION_MODES,
    BenchmarkCase,
    EvaluationResult,
    EvaluationRow,
    generate_benchmark_template,
    generate_evaluation_table,
)
from src.evaluation.verifier import (
    ReproductionClaimCheck,
    ReproductionVerificationResult,
    VerificationIssue,
    VerificationResult,
    verify_reproduction_artifacts,
    verify_workflow_outputs,
)

__all__ = [
    "EVALUATION_METRICS",
    "EVALUATION_MODES",
    "DEFAULT_BENCHMARK_CASES",
    "BenchmarkCase",
    "EvaluationResult",
    "EvaluationRow",
    "ReproductionClaimCheck",
    "ReproductionVerificationResult",
    "VerificationIssue",
    "VerificationResult",
    "generate_benchmark_template",
    "generate_evaluation_table",
    "verify_reproduction_artifacts",
    "verify_workflow_outputs",
]
