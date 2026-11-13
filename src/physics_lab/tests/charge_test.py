"""Charge quantization and fractional-charge pattern tests."""

from __future__ import annotations

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.physics.charge import (
    charge_quantization_from_circle,
    inspect_charge_fractions,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def check_charge_quantization(model: Model, result: ModelResult) -> CheckResult:
    charges = [row.charge for row in result.mass_charge_table if row.charge is not None]
    if not charges:
        return CheckResult(
            name="Charge quantization",
            status=CheckStatus.UNTESTED,
            message="No charge observable was evaluated.",
        )
    report = charge_quantization_from_circle(charges)
    if report["quantization"] == "DERIVED":
        status = CheckStatus.PASS
        message = (
            "Charge quantization: DERIVED. "
            f"Absolute charge normalization: {report['absolute_normalization']}."
        )
    elif report["quantization"] == "FAIL":
        status = CheckStatus.FAIL
        message = "Charge values are not proportional to the integer quantum number n."
    else:
        status = CheckStatus.UNTESTED
        message = "Could not test q_n ∝ n."
    return CheckResult(
        name="Charge quantization",
        status=status,
        message=message,
        details=report,
    )


def check_fractional_charge(model: Model, result: ModelResult) -> CheckResult:
    charges = [row.charge for row in result.mass_charge_table if row.charge is not None]
    if not charges:
        # C3 explicitly does not assign q = n/3.
        if result.metadata.get("charge_fractions") in {"NOT YET DERIVED", "NOT ASSIGNED"}:
            return CheckResult(
                name="Fractional charge",
                status=CheckStatus.UNTESTED,
                message=(
                    "Charge fractions 1/3: not assigned. "
                    "C3 sector labels and transformation phases are not charges."
                ),
            )
        return CheckResult(
            name="Fractional charge",
            status=CheckStatus.UNTESTED,
            message="No charge spectrum to inspect.",
        )

    report = inspect_charge_fractions(
        [q.numeric() for q in charges],
        result.parameters,
    )
    if report.status == "NOT A PREDICTION":
        return CheckResult(
            name="Fractional charge",
            status=CheckStatus.CALIBRATED if report.inserted_one_third else CheckStatus.FAIL,
            message=report.message,
            details={"found": report.found_fractions, "inserted": report.inserted_one_third},
        )
    if report.status == "CANDIDATE DERIVED":
        return CheckResult(
            name="Fractional charge",
            status=CheckStatus.PASS,
            message=report.message,
            details={"found": report.found_fractions},
        )
    return CheckResult(
        name="Fractional charge",
        status=CheckStatus.UNTESTED,
        message=report.message,
        details={"found": report.found_fractions},
    )
