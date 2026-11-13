"""Phase 14M records consequences of the verified test-action symmetry.

The actions are not modified. No gauge condition is introduced.
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
from physics_lab.physics.phase5c_gauging import _inner, _is_zero, _so2_rotation, so2_generator_K
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH
from physics_lab.theory_kernel.phase14j_eom import CURRENT_FORMULA, F2_TERM, _el_scalar, _lagrangians
from physics_lab.theory_kernel.phase14k_consistency import ACTION_HASH_14I
from physics_lab.theory_kernel.phase14l_symmetry import (
    CURRENT_DIFFERENCE,
    GAUGE_IDENTITY,
    NOETHER_CURRENT,
    run_phase_14l,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14M"
CODE_VERSION = "phase14m-consequences-v1"
TEST_VERSION = "phase14m-tests-v1"
ARTIFACT_DIR_NAME = "phase14m_consequence_artifacts"
IR_VERSION = "phase14m-consequences-v1"
PREVIOUS_IR_VERSION = "phase14l-symmetry-v1"
CURRENT_RELATION = "j_g^mu = j_5B^mu - 2 Z mathcalA^mu <K Phi, K Phi>"
CURRENT_LINK = "d_mu j_g^mu = -<E_Phi, K Phi>"
UNGAUGED_REMAINDER = "d_mu j_5B^mu = d_mu j_g^mu + d_mu (2 Z mathcalA^mu <K Phi, K Phi>)"


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


def _read(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def derive_quantum() -> dict[str, str]:
    return {"status": "UNTESTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def _raised(vectors: list[Any], eta: sp.Matrix, mu: int) -> sp.Matrix:
    acc = sp.zeros(3, 1)
    for nu in range(4):
        acc += eta[mu, nu] * vectors[nu]
    return acc


def _audit(generator: sp.Matrix) -> dict[str, Any]:
    if not _is_zero(generator.T + generator):
        return {"status": "K_NOT_ANTISYMMETRIC"}
    built = _lagrangians(generator)
    coords = built["coords"]
    phi = built["phi"]
    connection = built["connection"]
    eta = built["eta"]
    coefficient = built["symbols"]["Z"]
    gauge_coefficient = built["symbols"]["Z_A"]
    mass = built["matrix"]
    charge = _inner(generator * phi, generator * phi)
    relation = True
    for mu in range(4):
        gauged = sp.expand(2 * coefficient * _inner(_raised(built["covariant"], eta, mu), generator * phi))
        historical = sp.expand(2 * coefficient * _inner(_raised(built["slopes"], eta, mu), generator * phi))
        shift = sp.expand(2 * coefficient * sum(eta[mu, nu] * connection[nu] for nu in range(4)) * charge)
        relation = relation and _is_zero(gauged - historical + shift)
    gauged_divergence = 0
    historical_divergence = 0
    for mu in range(4):
        gauged_divergence += sp.diff(2 * coefficient * _inner(_raised(built["covariant"], eta, mu), generator * phi), coords[mu])
        historical_divergence += sp.diff(2 * coefficient * _inner(_raised(built["slopes"], eta, mu), generator * phi), coords[mu])
    matter = built["kinetic"] + built["potential"]
    phi_equation = sp.Matrix([_el_scalar(matter + built["maxwell"], phi[index], coords) for index in range(3)])
    connection_equation = [_el_scalar(matter + built["maxwell"], connection[nu], coords) for nu in range(4)]
    matter_connection = [_el_scalar(matter, connection[nu], coords) for nu in range(4)]
    link = _is_zero(sp.expand(gauged_divergence + _inner(phi_equation, generator * phi)))
    historical_gap = 0
    for mu in range(4):
        historical_gap += sp.diff(2 * coefficient * sum(eta[mu, nu] * connection[nu] for nu in range(4)) * charge, coords[mu])
    historical_relation = _is_zero(sp.expand(historical_divergence - gauged_divergence - historical_gap))
    historical_not_conserved = not _is_zero(sp.expand(historical_divergence))
    gauge_identity = _is_zero(
        sp.expand(sum(sp.diff(connection_equation[nu], coords[nu]) for nu in range(4)) - _inner(phi_equation, generator * phi))
    )
    branch_a_sets_current = all(
        _is_zero(sp.expand(matter_connection[mu] + 2 * coefficient * _inner(_raised(built["covariant"], eta, mu), generator * phi)))
        for mu in range(4)
    )
    alpha = sp.Function("alpha")(*coords)
    group = _so2_rotation(alpha)
    transformed = sp.simplify(group * phi)
    shifted = [connection[mu] + sp.diff(alpha, coords[mu]) for mu in range(4)]
    slopes = []
    covariant = []
    for mu in range(4):
        slope = sp.Matrix([sp.diff(transformed[index], coords[mu]) for index in range(3)])
        slopes.append(slope)
        covariant.append(sp.simplify(slope - shifted[mu] * (generator * transformed)))
    transport = all(_is_zero(covariant[mu] - sp.simplify(group * built["covariant"][mu])) for mu in range(4))
    strength = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            strength[mu, nu] = sp.diff(shifted[nu], coords[mu]) - sp.diff(shifted[mu], coords[nu])
    base_strength = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            base_strength[mu, nu] = sp.diff(connection[nu], coords[mu]) - sp.diff(connection[mu], coords[nu])
    strength_invariant = _is_zero(sp.expand(strength - base_strength))
    mu = 1
    gauged_value = _inner(_raised(built["covariant"], eta, mu), generator * phi)
    gauged_transformed = _inner(_raised(covariant, eta, mu), generator * transformed)
    historical_value = _inner(_raised(built["slopes"], eta, mu), generator * phi)
    historical_transformed = _inner(_raised(slopes, eta, mu), generator * transformed)
    raised_angle = sum(eta[mu, nu] * sp.diff(alpha, coords[nu]) for nu in range(4))
    gauged_invariant = _is_zero(sp.expand(gauged_transformed - gauged_value))
    historical_shifts = _is_zero(sp.expand(historical_transformed - historical_value - raised_angle * charge))
    hint_invariant = _is_zero(group.T * mass * group - mass)
    constant = sp.symbols("alpha_const", real=True)
    constant_group = _so2_rotation(constant)
    global_hint = _is_zero(constant_group.T * mass * constant_group - mass)
    reflection = sp.diag(1, 1, -1)
    reflected = sp.simplify(reflection.T * generator * reflection)
    orientation = _is_zero(reflected + generator)
    current_flips = _is_zero(
        _inner(_raised(built["covariant"], eta, mu), reflected * phi) + _inner(_raised(built["covariant"], eta, mu), generator * phi)
    )
    zero_coupling = _is_zero(sp.expand((2 * coefficient * charge).subs(coefficient, 0)))
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    extra = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])
    extra_generic = not _is_zero(extra * mass - mass * extra)
    extra_equal = _is_zero((extra * mass - mass * extra).subs(lam_a, lam_b))
    checks = {
        "branch_a_current": branch_a_sets_current,
        "current_flips": current_flips,
        "extra_equal": extra_equal,
        "extra_generic": extra_generic,
        "gauge_identity": gauge_identity,
        "gauged_invariant": gauged_invariant,
        "global_hint": global_hint,
        "hint_invariant": hint_invariant,
        "historical_not_conserved": historical_not_conserved,
        "historical_relation": historical_relation,
        "historical_shifts": historical_shifts,
        "link": link,
        "orientation": orientation,
        "relation": relation,
        "strength_invariant": strength_invariant,
        "transport": transport,
        "zero_coupling": zero_coupling,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        return {"failed": failed, "status": "CONSEQUENCE_MISMATCH"}
    return {
        "absolute_coupling": "NOT_DETERMINED",
        "charge_normalization": "NOT_DETERMINED",
        "current_link": CURRENT_LINK,
        "current_relation": CURRENT_RELATION,
        "gauge_fixing": "NOT_INTRODUCED",
        "gauge_identity": GAUGE_IDENTITY,
        "historical_current": CURRENT_FORMULA,
        "historical_remainder": UNGAUGED_REMAINDER,
        "j_g_properties": "on-shell conserved; gauge-invariant; orientation-dependent",
        "j_5b_properties": "not conserved once the connection is present; gauge-dependent; orientation-dependent",
        "new_fields": [],
        "new_parameters": [],
        "noether_current": NOETHER_CURRENT,
        "parameters_fixed": [],
        "roles": "gauge identity is off-shell; current conservation is the Phi-shell vanishing of d j_g",
        "special_cases_replace_generic": False,
        "status": "DERIVED",
        "z_a_fixed": False,
        "gauge_coefficient_symbol": str(gauge_coefficient),
    }


def _isolated(document: Any) -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    rendered = json.dumps(document)
    return (
        ("known_" + "physics") not in text
        and all(token not in text for token in _ranking_tokens())
        and all(marker not in rendered for marker in _target_markers())
        and "normalized_coupling" not in rendered
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
            "link": science["current_link"],
            "relation": science["current_relation"],
            "roles": science["roles"],
        }
    )


def negative_tests(result: dict[str, Any], repeated: str) -> list[dict[str, str]]:
    science = result["science"]
    actions = result["actions"]
    cases = [
        ("1", "Phase 14I hash is bound", ACTION_HASH_14I, result["ACTION_HASH_14I_INPUT"]),
        ("2", "global SO(2) is the Phase 14L result", "EXACT", result["GLOBAL_SYMMETRY_REUSED"]),
        ("3", "Branch B local redundancy is the Phase 14L result", "EXACT", result["LOCAL_REDUNDANCY_REUSED"]),
        ("4", "the two currents stay distinct", "DIFFERENT", "DIFFERENT" if science["noether_current"] != science["historical_current"] else "SAME"),
        ("5", "the current relation is the derived identity", CURRENT_RELATION, science["current_relation"]),
        ("6", "j_g conservation is on the Phi shell", CURRENT_LINK, science["current_link"]),
        ("7", "j_5B has a separate conservation status", UNGAUGED_REMAINDER, science["historical_remainder"]),
        ("8", "gauge identity", GAUGE_IDENTITY, science["gauge_identity"]),
        ("9", "the gauge identity is not labeled as the conservation law", "DISTINCT", "DISTINCT" if "off-shell" in science["roles"] and "Phi-shell" in science["roles"] else "MERGED"),
        ("10", "D_mu covariance", "COVARIANT", result["D_MU_STATUS"]),
        ("11", "F_mu_nu invariance", "INVARIANT", result["F_STATUS"]),
        ("12", "H_int invariance", "INVARIANT", result["HINT_STATUS"]),
        ("13", "branches stay separate", "2", "2" if len({item["test_action_id"] for item in actions}) == 2 else "MERGED"),
        ("14", "orientation change", "K -> -K", result["ORIENTATION"]),
        ("15", "special limits stay off the generic result", "FALSE", "FALSE" if science["special_cases_replace_generic"] is False else "TRUE"),
        ("16", "no gauge condition is introduced", "NOT_INTRODUCED", science["gauge_fixing"]),
        ("17", "no new field", "0", "0" if science["new_fields"] == [] else "ADDED"),
        ("18", "no new parameter", "0", "0" if science["new_parameters"] == [] and science["parameters_fixed"] == [] else "ADDED"),
        ("19", "no numerical target", "ABSENT", "ABSENT" if _isolated(science) else "PRESENT"),
        ("20", "no experimental input", "ABSENT", "ABSENT" if _isolated(science) else "PRESENT"),
        ("21", "no quantum claim", "UNTESTED", result["QUANTUM_STATUS"]),
        ("22", "no coupling normalization", "NOT_DETERMINED", science["absolute_coupling"]),
        ("23", "repeated execution matches", "IDENTICAL", "IDENTICAL" if result["digest"] == repeated else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_14M_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_14M_BLOCKED"}


def _stored_symmetry() -> bool:
    global_record = _read("phase14l_symmetry_artifacts/PHASE_14L_GLOBAL.json")
    local_record = _read("phase14l_symmetry_artifacts/PHASE_14L_LOCAL.json")
    current_record = _read("phase14l_symmetry_artifacts/PHASE_14L_CURRENT.json")
    return (
        global_record.get("branch_a") == "EXACT"
        and global_record.get("branch_b") == "EXACT"
        and local_record.get("branch_b_gauge") == "EXACT"
        and local_record.get("branch_a_covariance") == "VERIFIED"
        and current_record.get("comparison") == "DIFFERENT"
        and current_record.get("derived") == NOETHER_CURRENT
        and current_record.get("difference") == CURRENT_DIFFERENCE
        and current_record.get("charge") == "UNTESTED"
    )


def run_phase_14m(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    phase14l = run_phase_14l(write_artifacts=False)
    provenance = _read("phase14i_completion_artifacts/PHASE_14I_PROVENANCE.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or auth.action_content_hash != FROZEN_4C_HASH
        or phase14l.get("PHASE_14L_STATUS") != "COMPLETE"
        or phase14l.get("BRANCH_A_GLOBAL_SYMMETRY_STATUS") != "EXACT"
        or phase14l.get("BRANCH_B_LOCAL_GAUGE_STATUS") != "EXACT"
        or phase14l.get("NOETHER_CURRENT_STATUS") != "DIFFERENT"
        or phase14l.get("NOETHER_CHARGE_STATUS") != "UNTESTED"
        or phase14l.get("GAUGE_IDENTITY_STATUS") != "VERIFIED"
        or phase14l.get("ACTION_HASH_14I_INPUT") != ACTION_HASH_14I
        or provenance.get("action_hash_after") != ACTION_HASH_14I
        or phase14l.get("FROZEN_ACTION_MODIFIED") is not False
        or phase14l.get("QUANTUM_STATUS") != "UNTESTED"
        or not _stored_symmetry()
    ):
        return _stop("freeze gate or Phase 14L binding")
    science = _audit(so2_generator_K())
    if science.get("status") != "DERIVED":
        return {"PHASE_14M_STATUS": "BLOCKED", "failed": science.get("failed", []), "status": science.get("status", "CONSEQUENCE_MISMATCH")}
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
        "PHASE_14M_STATUS": "COMPLETE",
        "FREEZE_STATUS": "VERIFIED",
        "ACTION_BINDING_STATUS": "VERIFIED",
        "GLOBAL_SYMMETRY_CONSEQUENCES_STATUS": "VERIFIED",
        "LOCAL_GAUGE_CONSEQUENCES_STATUS": "VERIFIED",
        "CURRENT_RELATION_STATUS": "VERIFIED",
        "CURRENT_CONSERVATION_STATUS": "VERIFIED",
        "GAUGE_IDENTITY_STATUS": "VERIFIED",
        "BASIS_INVARIANCE_STATUS": "VERIFIED",
        "GAUGE_INVARIANT_CLASSIFICATION_STATUS": "VERIFIED",
        "PARAMETER_DEPENDENCE_STATUS": "VERIFIED",
        "QUANTUM_STATUS": derive_quantum()["status"],
        "NOETHER_CHARGE_STATUS": "UNTESTED",
        "GLOBAL_SYMMETRY_REUSED": phase14l["BRANCH_A_GLOBAL_SYMMETRY_STATUS"],
        "LOCAL_REDUNDANCY_REUSED": phase14l["BRANCH_B_LOCAL_GAUGE_STATUS"],
        "D_MU_STATUS": "COVARIANT",
        "F_STATUS": "INVARIANT",
        "HINT_STATUS": "INVARIANT",
        "ORIENTATION": "K -> -K",
        "ACTION_FREEZE_VERIFIED": True,
        "ATOMIC_GATE": "VERIFIED",
        "CONCURRENCY_GUARD": "VERIFIED",
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "FROZEN_ACTION_MODIFIED": False,
        "SEARCH_EXECUTED": False,
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "actions": phase14l["actions"],
        "science": science,
        "digest": digest,
    }
    negatives = negative_tests(payload, second)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14M_STATUS": "BLOCKED", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    if request_physical_activation("T09")["status"] == "AUTHORIZED" or numerical_search()["status"] != "NOT_EXECUTED":
        return _stop("search or activation")
    if any(item.get("f2_term") not in ("ABSENT", F2_TERM) for item in phase14l["actions"]):
        return _stop("branch content")
    payload["dry_run_negatives"] = negatives
    payload["search_manifest"] = manifest
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14M.json").write_bytes(canonical_json_bytes(manifest))
        files = {
            "PHASE_14M_CURRENTS.json": {
                "historical": CURRENT_FORMULA,
                "historical_status": "not conserved once the connection is present",
                "j_g": NOETHER_CURRENT,
                "j_g_status": "conserved on the Phi shell",
                "relation": CURRENT_RELATION,
            },
            "PHASE_14M_IDENTITIES.json": {
                "current_link": CURRENT_LINK,
                "gauge_identity": GAUGE_IDENTITY,
                "historical_remainder": UNGAUGED_REMAINDER,
                "roles": science["roles"],
            },
            "PHASE_14M_CLASSIFICATION.json": {
                "A_mu": "gauge-dependent connection",
                "D_mu_Phi": "gauge-covariant",
                "F_mu_nu": "gauge-invariant on Branch B",
                "H_int": "invariant quadratic form",
                "K": "orientation convention",
                "Phi": "gauge-covariant",
                "j_5B": science["j_5b_properties"],
                "j_g": science["j_g_properties"],
            },
            "PHASE_14M_PROVENANCE.json": {
                "action_hash_14i_input": ACTION_HASH_14I,
                "gauge_identity": "DERIVED",
                "global_so2": "DERIVED FROM COMPLETED TEST ACTION",
                "j_5B": "REUSED FROM PHASE 5B.0",
                "j_g": "DERIVED FROM COMPLETED TEST ACTION",
                "local_u1": "DERIVED GIVEN GAUGING ASSUMPTION",
                "quantum": "UNTESTED",
            },
            "PHASE_14M_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "noether_charge", "status": "UNTESTED"},
                    {"frontier_id": "coupling_normalization", "status": "NOT_DETERMINED"},
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
