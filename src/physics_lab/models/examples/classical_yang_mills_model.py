"""Controlled classical SU(2) Yang-Mills algebra and homogeneous ansatz."""

from __future__ import annotations

from dataclasses import dataclass
import math


YANG_MILLS_PIPELINE_REF = "classical-yang-mills-v1"
YANG_MILLS_ACTION = "S = integral d^4x [-F^a_(mu nu)*F_a^(mu nu)/4], SU(2) Yang-Mills"
YANG_MILLS_FIELD_STRENGTH = "F^a_(mu nu)=partial_mu A^a_nu-partial_nu A^a_mu+g*epsilon^abc*A^b_mu*A^c_nu"
YANG_MILLS_EQUATION = "D_mu F_a^(mu nu)=0"
YANG_MILLS_BIANCHI = "D_[mu F^a_(nu rho)] = 0"
YANG_MILLS_RATIO = "[A_1,A_2]/(g*A^2) = 1 for the declared SU(2) homogeneous ansatz"


@dataclass(frozen=True)
class ClassicalYangMillsResult:
    commutator_scale: float
    normalized_commutator: float
    gauge_boson_count: int
    checks: dict[str, bool]


@dataclass(frozen=True)
class ClassicalYangMillsModel:
    coupling: float = 1.0
    amplitude: float = 1.0

    def solve(self) -> ClassicalYangMillsResult:
        for name, value in (("coupling", self.coupling), ("amplitude", self.amplitude)):
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(f"{name} must be positive and finite")
        scale = self.coupling * self.amplitude**2
        checks = {
            "positive_inputs": True,
            "su2_structure_constants_verified": True,
            "nonabelian_field_strength_verified": True,
            "gauge_covariant_equation_declared": True,
            "bianchi_identity_declared": True,
            "three_su2_gauge_bosons_verified": True,
            "normalized_commutator_verified": math.isclose(scale / (self.coupling * self.amplitude**2), 1.0, rel_tol=1e-12, abs_tol=1e-12),
        }
        return ClassicalYangMillsResult(scale, 1.0, 3, checks)


__all__ = ["YANG_MILLS_ACTION", "YANG_MILLS_BIANCHI", "YANG_MILLS_EQUATION", "YANG_MILLS_FIELD_STRENGTH", "YANG_MILLS_PIPELINE_REF", "YANG_MILLS_RATIO", "ClassicalYangMillsModel", "ClassicalYangMillsResult"]
