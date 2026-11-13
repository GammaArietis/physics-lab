"""Symmetry checks."""

from __future__ import annotations

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.validation.checks import CheckResult, CheckStatus


def check_symmetry(model: Model, result: ModelResult) -> CheckResult:
    names = list(result.symmetries) or list(model.symmetries)
    if not names:
        if result.metadata.get("c3_detected") is False:
            return CheckResult(
                name="Symmetry",
                status=CheckStatus.FAIL,
                message="C3 was expected from V(theta)=V0(1-cos(3 theta)) but not detected.",
            )
        return CheckResult(
            name="Symmetry",
            status=CheckStatus.UNTESTED,
            message="No symmetry was declared or detected.",
        )

    extra = ""
    sectors = result.metadata.get("c3_sectors")
    if result.metadata.get("c3_residue_form"):
        extra = (
            f". Sectors from C3 characters: {sectors}. "
            "n = 3m+r: DERIVED FROM C3 SYMMETRY."
        )
    elif sectors is not None:
        extra = f". Sectors observed: {sectors}."
        if set(sectors) >= {0, 1, 2}:
            extra += " Three sectors: DERIVED."
        else:
            return CheckResult(
                name="Symmetry",
                status=CheckStatus.FAIL,
                message=f"C3 detected but sectors incomplete: {sectors}.",
                details={"symmetries": names, "sectors": sectors},
            )

    return CheckResult(
        name="Symmetry",
        status=CheckStatus.PASS,
        message="Detected: " + ", ".join(names) + extra,
        details={"symmetries": names, "sectors": sectors},
    )
