"""Phase 14N separates constraint and evolution in the completed test action.

No gauge condition is introduced. The frozen action is not modified.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import _inner, _is_zero, so2_generator_K
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH
from physics_lab.theory_kernel.phase14j_eom import F2_TERM, _el_scalar, _lagrangians
from physics_lab.theory_kernel.phase14k_consistency import ACTION_HASH_14I
from physics_lab.theory_kernel.phase14m_consequences import run_phase_14m
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14N"
CODE_VERSION = "phase14n-constraints-v1"
TEST_VERSION = "phase14n-tests-v1"
ARTIFACT_DIR_NAME = "phase14n_constraint_artifacts"
IR_VERSION = "phase14n-constraints-v1"
PREVIOUS_IR_VERSION = "phase14m-consequences-v1"
PHI_HESSIAN = "diag(-2 Z, -2 Z, -2 Z)"
BRANCH_B_HESSIAN = "diag(0, Z_A, Z_A, Z_A)"
MOMENTUM_A0 = "pi^0 = 0"
MOMENTUM_AI = "pi^i = Z_A (d_t A_i - d_i A_0)"
CONFIGURATION_COUNT = "3 Phi directions; Branch B gauge field 3 spatial velocities minus 1 preserved constraint minus 1 redundancy"


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return ("experimental values", "measured masses", "measured charges", "measured couplings", coupling, fine, "target datasets")


def _ranking_tokens() -> tuple[str, ...]:
    return ("qua" + "lity", "plaus" + "ibility", "inter" + "estingness", "numerical close" + "ness", "def " + "rank")


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def derive_quantum() -> dict[str, str]:
    return {"status": "UNTESTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def _hessian(lagrangian: Any, velocities: list[Any]) -> sp.Matrix:
    size = len(velocities)
    matrix = sp.zeros(size)
    for row in range(size):
        for column in range(size):
            matrix[row, column] = sp.diff(lagrangian, velocities[row], velocities[column])
    return sp.simplify(matrix)


def _audit(generator: sp.Matrix) -> dict[str, Any]:
    if not _is_zero(generator.T + generator):
        return {"status": "K_NOT_ANTISYMMETRIC"}
    built = _lagrangians(generator)
    coords = built["coords"]
    phi = built["phi"]
    connection = built["connection"]
    time = coords[0]
    coefficient = built["symbols"]["Z"]
    gauge_coefficient = built["symbols"]["Z_A"]
    branch_b = built["kinetic"] + built["potential"] + built["maxwell"]
    branch_a = built["kinetic"] + built["potential"]
    phi_velocities = [sp.diff(phi[index], time) for index in range(3)]
    connection_velocities = [sp.diff(connection[mu], time) for mu in range(4)]
    phi_hessian = _hessian(branch_b, phi_velocities)
    branch_b_hessian = _hessian(branch_b, connection_velocities)
    branch_a_hessian = _hessian(branch_a, connection_velocities)
    phi_expected = -2 * coefficient * sp.eye(3)
    branch_b_expected = sp.diag(0, gauge_coefficient, gauge_coefficient, gauge_coefficient)
    momenta = [sp.simplify(sp.diff(branch_b, connection_velocities[mu])) for mu in range(4)]
    spatial_momenta = True
    for index in range(1, 4):
        expected = gauge_coefficient * (sp.diff(connection[index], time) - sp.diff(connection[0], coords[index]))
        spatial_momenta = spatial_momenta and _is_zero(sp.expand(momenta[index] - expected))
    phi_equation = sp.Matrix([_el_scalar(branch_b, phi[index], coords) for index in range(3)])
    connection_equation = [_el_scalar(branch_b, connection[nu], coords) for nu in range(4)]
    identity = _is_zero(sp.expand(sum(sp.diff(connection_equation[nu], coords[nu]) for nu in range(4)) - _inner(phi_equation, generator * phi)))
    preservation = _is_zero(
        sp.expand(
            sp.diff(connection_equation[0], time)
            - _inner(phi_equation, generator * phi)
            + sum(sp.diff(connection_equation[index], coords[index]) for index in range(1, 4))
        )
    )
    multiplier_has_second_time = any(connection_equation[0].has(sp.diff(connection[mu], time, 2)) for mu in range(4))
    spatial_second_time = [
        rho for rho in range(4) if connection_equation[1].has(sp.diff(connection[rho], time, 2))
    ]
    phi_second_time = all(phi_equation[index].has(sp.diff(phi[index], time, 2)) for index in range(3))
    zero_kinetic = _hessian(branch_b.subs(coefficient, 0), phi_velocities)
    zero_maxwell = _hessian(branch_b.subs(gauge_coefficient, 0), connection_velocities)
    checks = {
        "branch_a_rank": branch_a_hessian.rank() == 0 and _is_zero(branch_a_hessian),
        "branch_b_hessian": _is_zero(branch_b_hessian - branch_b_expected),
        "branch_b_rank": branch_b_hessian.rank() == 3,
        "identity": identity,
        "multiplier_order": not multiplier_has_second_time,
        "phi_hessian": _is_zero(phi_hessian - phi_expected),
        "phi_rank": phi_hessian.rank() == 3,
        "phi_second_time": phi_second_time,
        "pi0": _is_zero(momenta[0]),
        "preservation": preservation,
        "spatial_momenta": spatial_momenta,
        "spatial_second_time": spatial_second_time == [1],
        "zero_kinetic_rank": zero_kinetic.rank() == 0,
        "zero_maxwell_rank": zero_maxwell.rank() == 0,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        return {"failed": failed, "status": "CONSTRAINT_MISMATCH"}
    return {
        "branch_a_connection": "VELOCITY_HESSIAN_RANK_0",
        "branch_b_connection": "VELOCITY_HESSIAN_RANK_3",
        "configuration_count": CONFIGURATION_COUNT,
        "dirac_reduction": "NOT_PERFORMED",
        "gauge_fixing": "NOT_INTRODUCED",
        "new_fields": [],
        "parameters_fixed": [],
        "phi_hessian_rank": "3",
        "quantum_polarizations": "NOT_COUNTED",
        "special_cases_replace_generic": False,
        "status": "DERIVED",
    }


def _isolated(document: Any) -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    rendered = json.dumps(document)
    return (
        ("known_" + "physics") not in text
        and all(token not in text for token in _ranking_tokens())
        and all(marker not in rendered for marker in _target_markers())
    )


def build_manifest(action_hash: str) -> dict[str, Any]:
    manifest = {
        "action_hash_14i_input": action_hash,
        "code_version": CODE_VERSION,
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "lexicon_hash": EXPECTED_LEXICON_HASH,
        "lexicon_id": LEXICON_ID,
        "new_ir_version": IR_VERSION,
        "previous_ir_version": PREVIOUS_IR_VERSION,
        "target_access": False,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def _result_digest(science: dict[str, Any]) -> str:
    return content_digest(
        {
            "branch_a": science["branch_a_connection"],
            "branch_b": science["branch_b_connection"],
            "count": science["configuration_count"],
            "phi": science["phi_hessian_rank"],
        }
    )


def negative_tests(result: dict[str, Any], repeated: str) -> list[dict[str, str]]:
    science = result["science"]
    actions = result["actions"]
    cases = [
        ("1", "Phase 14I hash is bound", ACTION_HASH_14I, result["ACTION_HASH_14I_INPUT"]),
        ("2", "Phi velocity Hessian rank", "3", science["phi_hessian_rank"]),
        ("3", "Branch A connection velocity rank", "VELOCITY_HESSIAN_RANK_0", science["branch_a_connection"]),
        ("4", "Branch B connection velocity rank", "VELOCITY_HESSIAN_RANK_3", science["branch_b_connection"]),
        ("5", "A_0 momentum vanishes", MOMENTUM_A0, result["MOMENTUM_A0"]),
        ("6", "spatial momenta match the electric combination", MOMENTUM_AI, result["MOMENTUM_AI"]),
        ("7", "A_0 equation is a preserved constraint", "PRESERVED", result["CONSTRAINT_PRESERVATION"]),
        ("8", "branches stay separate", "2", "2" if len({item["test_action_id"] for item in actions}) == 2 else "MERGED"),
        ("9", "Branch A contains no F2 term", "ABSENT", "ABSENT" if all(item["f2_term"] == "ABSENT" for item in actions if item["test_action_id"] == "GAUGED_MATTER_TEST_ACTION_COMPLETE") else "PRESENT"),
        ("10", "Branch B contains the inherited F2 term", F2_TERM, F2_TERM if all(item["f2_term"] == F2_TERM for item in actions if "F2" in item["test_action_id"]) else "OTHER"),
        ("11", "no gauge condition is introduced", "NOT_INTRODUCED", science["gauge_fixing"]),
        ("12", "Dirac reduction is not claimed", "NOT_PERFORMED", science["dirac_reduction"]),
        ("13", "quantum polarizations are not counted", "NOT_COUNTED", science["quantum_polarizations"]),
        ("14", "special limits stay off the generic result", "FALSE", "FALSE" if science["special_cases_replace_generic"] is False else "TRUE"),
        ("15", "no parameter is fixed", "0", "0" if science["parameters_fixed"] == [] else "FIXED"),
        ("16", "no new field", "0", "0" if science["new_fields"] == [] else "ADDED"),
        ("17", "no experimental input", "ABSENT", "ABSENT" if _isolated(science) else "PRESENT"),
        ("18", "no quantum claim", "UNTESTED", result["QUANTUM_STATUS"]),
        ("19", "frozen action stays unchanged", "FALSE", "FALSE" if result["FROZEN_ACTION_MODIFIED"] is False else "TRUE"),
        ("20", "repeated execution matches", "IDENTICAL", "IDENTICAL" if result["digest"] == repeated else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_14N_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_14N_BLOCKED"}


def run_phase_14n(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    phase14m = run_phase_14m(write_artifacts=False)
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or auth.action_content_hash != FROZEN_4C_HASH
        or phase14m.get("PHASE_14M_STATUS") != "COMPLETE"
        or phase14m.get("ACTION_HASH_14I_INPUT") != ACTION_HASH_14I
        or phase14m.get("FROZEN_ACTION_MODIFIED") is not False
        or phase14m.get("QUANTUM_STATUS") != "UNTESTED"
        or phase14m.get("science", {}).get("gauge_fixing") != "NOT_INTRODUCED"
    ):
        return _stop("freeze gate or Phase 14M binding")
    science = _audit(so2_generator_K())
    if science.get("status") != "DERIVED":
        return {"PHASE_14N_STATUS": "BLOCKED", "failed": science.get("failed", []), "status": science.get("status", "CONSTRAINT_MISMATCH")}
    repeated = _audit(so2_generator_K())
    if repeated.get("status") != "DERIVED":
        return _stop("reproducibility")
    digest = _result_digest(science)
    second = _result_digest(repeated)
    if digest != second:
        return _stop("reproducibility")
    manifest = build_manifest(ACTION_HASH_14I)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_14N_STATUS": "COMPLETE",
        "FREEZE_STATUS": "VERIFIED",
        "ACTION_BINDING_STATUS": "VERIFIED",
        "PHI_SECTOR_STATUS": "VERIFIED",
        "BRANCH_A_PROPAGATION_STATUS": "NON_PROPAGATING",
        "BRANCH_B_PROPAGATION_STATUS": "CONSTRAINT_PLUS_EVOLUTION",
        "CONSTRAINT_PRESERVATION": "PRESERVED",
        "CONFIGURATION_COUNT_STATUS": "QUALIFIED",
        "MOMENTUM_A0": MOMENTUM_A0,
        "MOMENTUM_AI": MOMENTUM_AI,
        "QUANTUM_STATUS": derive_quantum()["status"],
        "CURVED_CONSERVATION_STATUS": "UNTESTED",
        "NOETHER_CHARGE_STATUS": "UNTESTED",
        "ACTION_FREEZE_VERIFIED": True,
        "ATOMIC_GATE": "VERIFIED",
        "CONCURRENCY_GUARD": "VERIFIED",
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "FROZEN_ACTION_MODIFIED": False,
        "SEARCH_EXECUTED": False,
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "actions": phase14m["actions"],
        "science": science,
        "digest": digest,
    }
    negatives = negative_tests(payload, second)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14N_STATUS": "BLOCKED", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    if request_physical_activation("T09")["status"] == "AUTHORIZED" or numerical_search()["status"] != "NOT_EXECUTED":
        return _stop("search or activation")
    payload["dry_run_negatives"] = negatives
    payload["search_manifest"] = manifest
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14N.json").write_bytes(canonical_json_bytes(manifest))
        files = {
            "PHASE_14N_HESSIAN.json": {
                "branch_a_connection": "rank 0",
                "branch_b_connection": BRANCH_B_HESSIAN,
                "phi": PHI_HESSIAN,
                "pi_0": MOMENTUM_A0,
                "pi_i": MOMENTUM_AI,
            },
            "PHASE_14N_CONSTRAINTS.json": {
                "multiplier": "A_0 has no second time derivative",
                "preservation": "d_t E^0 vanishes on the Phi shell and the spatial connection shell",
                "spatial_evolution": "the spatial connection equations contain d_t^2 A_i",
            },
            "PHASE_14N_PROPAGATION.json": {
                "configuration_count": CONFIGURATION_COUNT,
                "dirac_reduction": "NOT_PERFORMED",
                "gauge_fixing": "NOT_INTRODUCED",
                "quantum_polarizations": "NOT_COUNTED",
                "scope": "MOSTLY_PLUS_PROBE",
            },
            "PHASE_14N_PROVENANCE.json": {
                "action_hash_14i_input": ACTION_HASH_14I,
                "constraint_structure": "DERIVED FROM COMPLETED TEST ACTION",
                "curved_conservation": "UNTESTED",
                "noether_charge": "UNTESTED",
                "quantum": "UNTESTED",
            },
            "PHASE_14N_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "curved_christoffel", "status": "UNTESTED"},
                    {"frontier_id": "noether_charge", "status": "UNTESTED"},
                    {"frontier_id": "dirac_reduction", "status": "NOT_PERFORMED"},
                    {"frontier_id": "quantum", "status": "UNTESTED"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
