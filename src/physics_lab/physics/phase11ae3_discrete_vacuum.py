"""Phase 11AE.3: vacuum selection on the discrete T10 moduli set.

T09 is reopened only after T10. The Coleman-Weinberg potential is evaluated
on the four already stabilized points. The flux-tension minimization is not
run again.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.core.provenance import Provenance
from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.internal_spectrum import implemented_branch_II_m2
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11af_modulus_stabilization import artifact_dir as phase11af_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import QuantumEffectivePotential
from physics_lab.physics.spacetime import MOSTLY_PLUS, canonical_prefactor

__all__ = [
    "CLOSURE_TARGET",
    "PHASE_11AE3_STATUS",
    "T09_STATUS",
    "run_phase_11AE_3_execution",
]

PHASE = "PHASE_11AE.3"
PHASE_11AE3_STATUS = "OPEN"
T09_STATUS = "UNFROZEN"
CLOSURE_TARGET = "SINGLE_VACUUM"
_SIGN_PAIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ae3_artifacts"


def _magnitude_symbols() -> dict[str, Any]:
    charge_a, charge_b = sp.symbols("Q_a Q_b", positive=True)
    tension_a, tension_b = sp.symbols("T_a T_b", positive=True)
    return {
        "Q_a": charge_a,
        "Q_b": charge_b,
        "T_a": tension_a,
        "T_b": tension_b,
        "lambda_a": sp.sqrt(charge_a) / tension_a ** sp.Rational(1, 4),
        "lambda_b": sp.sqrt(charge_b) / tension_b ** sp.Rational(1, 4),
    }


def _loop_value(mass_a: Any, mass_b: Any, mu: Any, scheme_c: Any) -> Any:
    """One copy of the lambda_a mode and two copies of the lambda_b mode."""
    loop = (mass_a**2) * (sp.log(mass_a / mu**2) - scheme_c)
    loop += 2 * (mass_b**2) * (sp.log(mass_b / mu**2) - scheme_c)
    coefficient = sp.Integer(1) / (sp.Integer(64) * sp.pi**2)
    return sp.simplify(coefficient * loop)


def _branch_rows(sign_of_c_h: int, magnitudes: dict[str, Any], signature: str) -> list[dict[str, Any]]:
    kinetic = canonical_prefactor(signature)
    c_h = sp.symbols("c_H", positive=True)
    if sign_of_c_h < 0:
        c_h = -c_h
    mu, scheme_c = sp.symbols("mu c", positive=True)
    rows = []
    for sign_a, sign_b in _SIGN_PAIRS:
        lambda_a = sp.simplify(sign_a * magnitudes["lambda_a"])
        lambda_b = sp.simplify(sign_b * magnitudes["lambda_b"])
        mass_a = sp.simplify(implemented_branch_II_m2(c_h, kinetic, lambda_a, signature))
        mass_b = sp.simplify(implemented_branch_II_m2(c_h, kinetic, lambda_b, signature))
        real_spectrum = bool(mass_a.is_positive and mass_b.is_positive)
        row = {
            "lambda_signs": [sign_a, sign_b],
            "c_H_sign": sign_of_c_h,
            "mass_a2": str(mass_a),
            "mass_b2": str(mass_b),
            "mass_a2_positive": bool(mass_a.is_positive),
            "mass_b2_positive": bool(mass_b.is_positive),
            "real_spectrum": real_spectrum,
            "complex_log": not real_spectrum,
            "V_1loop": str(_loop_value(mass_a, mass_b, mu, scheme_c)) if real_spectrum else "NOT_REAL",
        }
        rows.append(row)
    return rows


def _values_match_across_real_branches(magnitudes: dict[str, Any], signature: str) -> bool:
    kinetic = canonical_prefactor(signature)
    c_h = sp.symbols("c_H", positive=True)
    mu, scheme_c = sp.symbols("mu c", positive=True)
    positive_corner = _loop_value(
        implemented_branch_II_m2(c_h, kinetic, -magnitudes["lambda_a"], signature),
        implemented_branch_II_m2(c_h, kinetic, -magnitudes["lambda_b"], signature),
        mu,
        scheme_c,
    )
    negative_corner = _loop_value(
        implemented_branch_II_m2(-c_h, kinetic, magnitudes["lambda_a"], signature),
        implemented_branch_II_m2(-c_h, kinetic, magnitudes["lambda_b"], signature),
        mu,
        scheme_c,
    )
    return bool(sp.simplify(positive_corner - negative_corner) == 0)


def _evaluate_set(signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    magnitudes = _magnitude_symbols()
    rows = _branch_rows(1, magnitudes, signature) + _branch_rows(-1, magnitudes, signature)
    real_rows = [row for row in rows if row["real_spectrum"]]
    ill_defined = any(row["complex_log"] for row in rows)
    same_real_value = _values_match_across_real_branches(magnitudes, signature)
    unique = (not ill_defined) and len(real_rows) == 1
    return {
        "admissible_space": [
            {"lambda_a": "sqrt(Q_a)/T_a**(1/4)", "lambda_b": "sqrt(Q_b)/T_b**(1/4)", "signs": list(pair)}
            for pair in _SIGN_PAIRS
        ],
        "rows": rows,
        "real_configurations": [
            {"lambda_signs": row["lambda_signs"], "c_H_sign": row["c_H_sign"], "V_1loop": row["V_1loop"]}
            for row in real_rows
        ],
        "ill_defined_for_some_signs": ill_defined,
        "real_values_match_across_c_H_sign": same_real_value,
        "selection_is_unique": unique,
        "selected_signs": real_rows[0]["lambda_signs"] if unique else None,
    }


def run_phase_11AE_3_execution(*, signature: str = MOSTLY_PLUS, write_artifacts: bool = False) -> dict[str, Any]:
    """Evaluate Coleman-Weinberg on the four T10 points.

    SINGLE_VACUUM is fixed before that evaluation. A complex mass eigenvalue
    keeps the closure at DOMAIN_UNREDUCED.
    """
    potential = QuantumEffectivePotential()
    opening = {
        "entry": "Phase 11AE.3 opening",
        "PHASE": PHASE,
        "T09_STATUS": T09_STATUS,
        "T10_reexecuted": False,
        "simultaneous_activation": False,
        "functional": "QuantumEffectivePotential",
        "functional_provenance": potential.provenance,
    }
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
    }
    provenance_log: list[dict[str, Any]] = [opening, closure_entry]
    if potential.provenance != Provenance.ASSUMED.value or potential.derived is not False:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "quantum potential is not the sealed assumed input",
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
        }
    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "frozen 4C hash",
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
        }
    evaluation = _evaluate_set(signature)
    single = bool(evaluation["selection_is_unique"]) and not evaluation["ill_defined_for_some_signs"]
    observed = "SINGLE_VACUUM" if single else "DOMAIN_UNREDUCED"
    program_status = "CLOSED_UNDER_DECLARED_SCOPE" if single else "DOMAIN_UNREDUCED"
    provenance_log.append(
        {
            "entry": "discrete Coleman-Weinberg evaluation",
            "ill_defined_for_some_signs": evaluation["ill_defined_for_some_signs"],
            "real_configuration_count": len(evaluation["real_configurations"]),
            "real_values_match_across_c_H_sign": evaluation["real_values_match_across_c_H_sign"],
            "Provenance": potential.provenance,
        }
    )
    comparison = {
        "entry": "closure comparison",
        "criterion": CLOSURE_TARGET,
        "observed": observed,
        "objective_met": observed == CLOSURE_TARGET,
        "PROGRAM_CLOSURE_STATUS": program_status,
        "post_hoc_validation": False,
        "closure_target_used_as_filter": False,
    }
    provenance_log.append(comparison)
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11AE3_STATUS": PHASE_11AE3_STATUS,
        "T09_STATUS": T09_STATUS,
        "T10_reexecuted": False,
        "simultaneous_activation": False,
        "functional_provenance": potential.provenance,
        "action_content_hash": digest,
        "admissible_space_count": 4,
        "evaluation": evaluation,
        "closure_comparison": comparison,
        "observed": observed,
        "objective_met": comparison["objective_met"],
        "PROGRAM_CLOSURE_STATUS": program_status,
        "provenance_log": provenance_log,
        "new_parameter_count": 0,
        "frozen_action_modified": False,
    }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AE3_DISCRETE_VACUUM.json"
        if destination.resolve().is_relative_to(phase11af_artifact_dir().resolve()):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(payload) + b"\n")
    return payload
