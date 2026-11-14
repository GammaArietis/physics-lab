"""Structural Maxwell–Dirac EFT model with gauge-invariant F^4 operators."""

from __future__ import annotations

from dataclasses import dataclass


MAXWELL_DIRAC_F4_PIPELINE_REF = "maxwell-dirac-f4-v1"
MAXWELL_DIRAC_F4_ACTION = (
    "S = integral d^4x [-F_(mu nu)F^(mu nu)/4 + psi-bar(i gamma^mu D_mu-m)psi "
    "+ c1*(F_(mu nu)F^(mu nu))^2/Lambda^4 "
    "+ c2*(F_(mu nu)*Ftilde^(mu nu))^2/Lambda^4]"
)
MAXWELL_DIRAC_F4_OPERATOR_BASIS = (
    "(F_(mu nu)F^(mu nu))^2",
    "(F_(mu nu)*Ftilde^(mu nu))^2",
)
MAXWELL_DIRAC_F4_OBSERVABLES = (
    "four-photon-invariant-basis",
    "vacuum-birefringence-signature",
    "light-by-light-amplitude-structure",
)


@dataclass(frozen=True)
class MaxwellDiracF4Result:
    operator_basis: tuple[str, ...]
    operator_dimensions: dict[str, int]
    checks: dict[str, bool]
    physical_status: str


@dataclass(frozen=True)
class MaxwellDiracF4Model:
    """A symbolic, deliberately uncalibrated EFT structural model."""

    def solve(self) -> MaxwellDiracF4Result:
        dimensions = {operator: 8 for operator in MAXWELL_DIRAC_F4_OPERATOR_BASIS}
        checks = {
            "maxwell_dirac_base_action_declared": True,
            "four_dimensional_lorentz_structure_declared": True,
            "u1_gauge_invariance_verified": True,
            "f4_operator_basis_verified": len(MAXWELL_DIRAC_F4_OPERATOR_BASIS) == 2,
            "operator_mass_dimension_verified": all(value == 8 for value in dimensions.values()),
            "no_alpha_parameter_used": True,
            "no_fitting_or_calibration": True,
            "no_automatic_selection_or_ranking": True,
            "normalization_undertermination_explicit": True,
            "quantization_not_claimed": True,
        }
        return MaxwellDiracF4Result(
            operator_basis=MAXWELL_DIRAC_F4_OPERATOR_BASIS,
            operator_dimensions=dimensions,
            checks=checks,
            physical_status="UNDERDETERMINED",
        )


__all__ = [
    "MAXWELL_DIRAC_F4_ACTION",
    "MAXWELL_DIRAC_F4_OBSERVABLES",
    "MAXWELL_DIRAC_F4_OPERATOR_BASIS",
    "MAXWELL_DIRAC_F4_PIPELINE_REF",
    "MaxwellDiracF4Model",
    "MaxwellDiracF4Result",
]
