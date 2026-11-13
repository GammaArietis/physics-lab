"""Versioned records for candidate theories."""

from physics_lab.registry.theory_candidate import (
    SCHEMA_PATH,
    SCHEMA_VERSION,
    TheoryCandidateValidationError,
    load_theory_candidate,
    validate_theory_candidate,
    validate_theory_candidate_file,
)
from physics_lab.registry.reference_pipeline import (
    DEFAULT_CANDIDATE_PATH,
    REFERENCE_CANDIDATE_ID,
    REFERENCE_PIPELINE_VERSION,
    ReferencePipelineError,
    build_reference_model,
    run_reference_pipeline,
    write_reference_pipeline_report,
)
from physics_lab.registry.reference_closure import (
    REFERENCE_CLOSURE_VERSION,
    ReferenceClosureError,
    audit_reference_closure,
)
from physics_lab.registry.experimental_comparison import (
    ComparisonAuthorizationError,
    DATASET_SCHEMA_VERSION,
    EXPERIMENTAL_COMPARISON_VERSION,
    ExperimentalComparisonError,
    load_experimental_dataset,
    run_isolated_experimental_comparison,
    validate_experimental_dataset,
    write_isolated_comparison_report,
)

__all__ = [
    "SCHEMA_PATH",
    "SCHEMA_VERSION",
    "TheoryCandidateValidationError",
    "load_theory_candidate",
    "validate_theory_candidate",
    "validate_theory_candidate_file",
    "DEFAULT_CANDIDATE_PATH",
    "REFERENCE_CANDIDATE_ID",
    "REFERENCE_PIPELINE_VERSION",
    "ReferencePipelineError",
    "build_reference_model",
    "run_reference_pipeline",
    "write_reference_pipeline_report",
    "REFERENCE_CLOSURE_VERSION",
    "ReferenceClosureError",
    "audit_reference_closure",
    "ComparisonAuthorizationError",
    "DATASET_SCHEMA_VERSION",
    "EXPERIMENTAL_COMPARISON_VERSION",
    "ExperimentalComparisonError",
    "load_experimental_dataset",
    "run_isolated_experimental_comparison",
    "validate_experimental_dataset",
    "write_isolated_comparison_report",
]
