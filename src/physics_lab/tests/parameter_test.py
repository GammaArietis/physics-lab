"""Parameter provenance checks used by the validator."""

from __future__ import annotations

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import ModelResult
from physics_lab.validation.checks import CheckResult, CheckStatus


def check_parameters(model: Model, result: ModelResult) -> CheckResult:
    illegal = [
        p.name
        for p in result.parameters
        if p.provenance is Provenance.EXPERIMENTAL
    ]
    if illegal:
        return CheckResult(
            name="Parameter provenance",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters were present during derivation: "
            + ", ".join(illegal),
        )

    inserted_as_derived = []
    for p in result.parameters:
        if p.provenance is Provenance.DERIVED and not p.dependencies and not p.formula:
            inserted_as_derived.append(p.name)
    if inserted_as_derived:
        return CheckResult(
            name="Parameter provenance",
            status=CheckStatus.FAIL,
            message="Inserted parameters labelled DERIVED: "
            + ", ".join(inserted_as_derived),
        )

    n_free = len(result.parameters.free_parameters())
    n_cal = len(result.parameters.calibrated())
    return CheckResult(
        name="Parameter provenance",
        status=CheckStatus.PASS,
        message=f"Provenance consistent. Free={n_free}, calibrated={n_cal}.",
        details={"free": n_free, "calibrated": n_cal},
    )
