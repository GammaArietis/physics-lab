"""Phase 11AE.4: close T09 on the residual parity class.

T09 is unfrozen here. The synthesis only reads Phase 11AF.2, 11AE.3, and
11AG.2. It does not add a parameter and does not rewrite those records.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae3_discrete_vacuum import artifact_dir as phase11ae3_artifact_dir
from physics_lab.physics.phase11ae3_discrete_vacuum import run_phase_11AE_3_execution
from physics_lab.physics.phase11af_modulus_stabilization import (
    ModulusStabilizationAuthorization_Balanced,
    run_phase_11AF_2_execution,
)
from physics_lab.physics.phase11af_modulus_stabilization import artifact_dir as phase11af_artifact_dir
from physics_lab.physics.phase11ag2_asymmetric_operator import (
    AsymmetricOperatorAuthorization,
    run_phase_11AG_2_execution,
)
from physics_lab.physics.phase11ag2_asymmetric_operator import artifact_dir as phase11ag2_artifact_dir
from physics_lab.physics.phase11ag_abfi_operators import artifact_dir as phase11ag_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "CLOSURE_TARGET",
    "PHASE_11AE4_STATUS",
    "T09_STATUS",
    "run_phase_11AE_4_synthesis",
]

PHASE = "PHASE_11AE.4"
PHASE_11AE4_STATUS = "OPEN"
T09_STATUS = "UNFROZEN"
CLOSURE_TARGET = "DEGENERATE_CLASS"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ae4_artifacts"


def _component_sign(text: str) -> int:
    expr = sp.sympify(text)
    value = sp.simplify(
        expr.subs(
            {
                sp.Symbol("Q_a"): 1,
                sp.Symbol("Q_b"): 1,
                sp.Symbol("T_a"): 1,
                sp.Symbol("T_b"): 1,
            }
        )
    )
    if value.is_positive:
        return 1
    if value.is_negative:
        return -1
    return 0


def _partner(pair: tuple[int, int]) -> tuple[int, int]:
    return (-pair[0], -pair[1])


def _orbit(pair: tuple[int, int]) -> frozenset[tuple[int, int]]:
    return frozenset((pair, _partner(pair)))


def _as_pair(signs: list[int]) -> tuple[int, int]:
    return (int(signs[0]), int(signs[1]))


def _orbit_payload(orbit: frozenset[tuple[int, int]]) -> list[list[int]]:
    return [list(pair) for pair in sorted(orbit)]


def _synthesize(signature: str) -> dict[str, Any]:
    moduli = run_phase_11AF_2_execution(
        ModulusStabilizationAuthorization_Balanced(),
        write_artifacts=False,
    )
    loop = run_phase_11AE_3_execution(write_artifacts=False, signature=signature)
    soft = run_phase_11AG_2_execution(
        AsymmetricOperatorAuthorization(),
        write_artifacts=False,
        signature=signature,
    )
    sign_pairs = []
    for item in moduli.get("stationarity", {}).get("finite_nonzero_solutions", []):
        sign_pairs.append((_component_sign(item["lambda_a"]), _component_sign(item["lambda_b"])))
    t10_orbits = {_orbit(pair) for pair in sign_pairs if 0 not in pair}
    real_rows = loop.get("evaluation", {}).get("real_configurations", [])
    real_pairs = [_as_pair(row["lambda_signs"]) for row in real_rows]
    real_orbits = {_orbit(pair) for pair in real_pairs}
    mixed_rows = [
        row for row in loop.get("evaluation", {}).get("rows", []) if row["lambda_signs"][0] != row["lambda_signs"][1]
    ]
    mixed_eliminated = bool(mixed_rows) and all(row["complex_log"] is True for row in mixed_rows)
    soft_pairs = [
        _as_pair(row["lambda_signs"]) for row in soft.get("configurations", []) if row.get("physically_valid")
    ]
    one_orbit = len(real_orbits) == 1 and len(real_pairs) == 2
    surviving = next(iter(real_orbits)) if one_orbit else frozenset()
    partners = one_orbit and surviving == _orbit(real_pairs[0]) and real_pairs[0] != real_pairs[1]
    same_sign_class = one_orbit and all(pair[0] == pair[1] for pair in surviving)
    eliminated = t10_orbits - real_orbits
    reduced = (
        moduli.get("PROGRAM_CLOSURE_STATUS") == "CLOSED_UNDER_DECLARED_SCOPE"
        and moduli.get("stationarity", {}).get("moduli_fixed") is True
        and moduli.get("stationarity", {}).get("solution_count") == 4
        and len(t10_orbits) == 2
        and mixed_eliminated
        and loop.get("evaluation", {}).get("real_values_match_across_c_H_sign") is True
        and partners
        and same_sign_class
        and len(eliminated) == 1
        and set(soft_pairs) == set(real_pairs)
        and soft.get("V_soft_invariant_under_sign_flip") is True
        and soft.get("valid_energy_difference") == "0"
        and soft.get("degeneracy_lifted") is False
        and soft.get("valid_state_count") == 2
    )
    return {
        "moduli_fixed_at_finite_value": moduli.get("stationarity", {}).get("moduli_fixed") is True,
        "t10_solution_count": moduli.get("stationarity", {}).get("solution_count"),
        "t10_orbits": [_orbit_payload(item) for item in sorted(t10_orbits, key=_orbit_payload)],
        "mixed_tachyonic_states_eliminated": mixed_eliminated,
        "quadratic_doublet_invariant": soft.get("V_soft_invariant_under_sign_flip") is True
        and soft.get("valid_energy_difference") == "0",
        "surviving_class": _orbit_payload(surviving) if one_orbit else [],
        "eliminated_class": [_orbit_payload(item) for item in sorted(eliminated, key=_orbit_payload)],
        "equivalence_class_count": len(real_orbits),
        "class_size": len(surviving),
        "symmetry": "Z_2",
        "parity_map": "(lambda_a, lambda_b) -> (-lambda_a, -lambda_b)",
        "V_adm": "Z_2 parity class of the same-sign moduli" if reduced else "NOT_REDUCED_TO_ONE_CLASS",
        "class_identified": reduced,
        "sources_ok": moduli.get("status") == "OK" and loop.get("status") == "OK" and soft.get("status") == "OK",
    }


def run_phase_11AE_4_synthesis(*, signature: str = MOSTLY_PLUS, write_artifacts: bool = False) -> dict[str, Any]:
    """Aggregate the residual vacuum into one parity class, if that is what remains.

    DEGENERATE_CLASS is logged before the aggregation. The historical 11AD
    decision is left untouched.
    """
    opening = {
        "entry": "Phase 11AE.4 opening",
        "PHASE": PHASE,
        "PHASE_11AE4_STATUS": PHASE_11AE4_STATUS,
        "T09_STATUS": T09_STATUS,
        "T10_reexecuted": False,
        "T11_activated": False,
        "simultaneous_activation": False,
        "parent_records_modified": False,
    }
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "closure_target_used_as_filter": False,
    }
    provenance_log: list[dict[str, Any]] = [opening, closure_entry]
    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "frozen 4C hash",
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    parents = {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "11AF2": phase11af_artifact_dir() / "PHASE_11AF2_EXECUTION.json",
        "11AE3": phase11ae3_artifact_dir() / "PHASE_11AE3_DISCRETE_VACUUM.json",
        "11AG": phase11ag_artifact_dir() / "PHASE_11AG_T13_CONTAINMENT.json",
        "11AG2": phase11ag2_artifact_dir() / "PHASE_11AG2_EXECUTION.json",
    }
    before = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    document_before = canonical_json_bytes(phase4c_action_document())
    synthesis = _synthesize(signature)
    document_after = canonical_json_bytes(phase4c_action_document())
    after = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    if document_after != document_before or after != before or not synthesis["sources_ok"]:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "parent record changed during synthesis" if after != before else "prior phase unread",
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": document_after != document_before,
        }
    identified = bool(synthesis["class_identified"])
    observed = CLOSURE_TARGET if identified else "NOT_A_SINGLE_DEGENERATE_CLASS"
    program_status = "CLOSED_UNDER_DECLARED_SCOPE" if identified else "NOT_CLOSED"
    t09_outcome = "CLOSED" if identified else T09_STATUS
    principle = "COMPLETED" if identified else "OPEN"
    provenance_log.append(
        {
            "entry": "vacuum synthesis",
            "moduli_fixed_at_finite_value": synthesis["moduli_fixed_at_finite_value"],
            "mixed_tachyonic_states_eliminated": synthesis["mixed_tachyonic_states_eliminated"],
            "quadratic_doublet_invariant": synthesis["quadratic_doublet_invariant"],
            "equivalence_class_count": synthesis["equivalence_class_count"],
            "symmetry": synthesis["symmetry"],
            "V_adm": synthesis["V_adm"],
            "new_parameter_count": 0,
        }
    )
    comparison = {
        "entry": "closure comparison",
        "criterion": CLOSURE_TARGET,
        "observed": observed,
        "objective_met": observed == CLOSURE_TARGET,
        "PROGRAM_CLOSURE_STATUS": program_status,
        "T09_STATUS": t09_outcome,
        "VACUUM_SELECTION_PRINCIPLE": principle,
        "completion": "degenerate parity vacuum" if identified else None,
        "post_hoc_validation": False,
        "closure_target_used_as_filter": False,
    }
    provenance_log.append(comparison)
    laboratory_state = {
        "PHASE": PHASE,
        "T09_STATUS": t09_outcome,
        "T09_PROGRAM_CLOSURE_STATUS": program_status,
        "VACUUM_SELECTION_PRINCIPLE": principle,
        "V_adm": synthesis["V_adm"],
        "symmetry": synthesis["symmetry"],
        "parent_11AD_decision_unchanged": True,
        "T10_reexecuted": False,
        "T11_activated": False,
        "new_parameter_count": 0,
    }
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11AE4_STATUS": PHASE_11AE4_STATUS,
        "T09_STATUS": t09_outcome,
        "T10_reexecuted": False,
        "T11_activated": False,
        "simultaneous_activation": False,
        "action_content_hash": digest,
        "frozen_action_modified": False,
        "parent_records_modified": False,
        "synthesis": synthesis,
        "closure_comparison": comparison,
        "observed": observed,
        "objective_met": comparison["objective_met"],
        "PROGRAM_CLOSURE_STATUS": program_status,
        "VACUUM_SELECTION_PRINCIPLE": principle,
        "laboratory_state": laboratory_state,
        "provenance_log": provenance_log,
        "new_parameter_count": 0,
    }
    if write_artifacts:
        destination = artifact_dir()
        forbidden = (
            phase11ad_artifact_dir().resolve(),
            phase11af_artifact_dir().resolve(),
            phase11ae3_artifact_dir().resolve(),
            phase11ag_artifact_dir().resolve(),
            phase11ag2_artifact_dir().resolve(),
        )
        if any(destination.resolve().is_relative_to(root) for root in forbidden):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_11AE4_SYNTHESIS.json").write_bytes(canonical_json_bytes(payload) + b"\n")
        (destination / "LABORATORY_STATE.json").write_bytes(canonical_json_bytes(laboratory_state) + b"\n")
    return payload
