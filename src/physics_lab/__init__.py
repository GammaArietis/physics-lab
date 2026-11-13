"""Physics Model Laboratory.

A small computational lab for exploring speculative theoretical models
while keeping a strict distinction between what is derived, assumed,
calibrated, input, or experimental.
"""

from physics_lab.core.model import Model
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.models.loader import load_model
from physics_lab.reporting.audit import audit_parameters
from physics_lab.registry import (
    TheoryCandidateValidationError,
    load_theory_candidate,
    validate_theory_candidate,
)
from physics_lab.validation.validator import validate as validate

__all__ = [
    "Model",
    "Parameter",
    "ParameterRegistry",
    "Provenance",
    "load_model",
    "audit_parameters",
    "validate",
    "TheoryCandidateValidationError",
    "load_theory_candidate",
    "validate_theory_candidate",
]
__version__ = "0.1.0"
