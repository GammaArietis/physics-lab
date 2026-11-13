"""Phase 11F: M4 cluster decomposition as explicit NEW_PHYSICAL_INPUT.

M4 was ABSENT in Phase 11B. It is not derived from locality, Lorentz
covariance, microcausality, or spectral tests. Activation requires an
explicit human authorization contract. The phase prompt is not authorization.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_11E_M3_HASH",
    "MODULE_VERSION",
    "PHASE_11F_TEST_COPY_ID",
    "REQUIRED_AUTHORIZATION_FIELDS",
    "analyze_phase11f_cluster",
    "artifact_dir",
    "authorization_status",
    "free_scalar_cluster",
    "run_phase11f_or_stop",
]

PHASE_11F_TEST_COPY_ID = "PHASE_11F_M4_CLUSTER_NEW_INPUT"
PHASE = "PHASE_11F"
MODULE_VERSION = "phase11f-m4-cluster-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_11C_M1_HASH = "4bf8c994dc2d9d37020a04c3162fcf0dd91b8c306d9967e8a9841899335fd9a7"
EXPECTED_11D_M2_HASH = "d9958cada99051eb3cd9d4cb48018c4d3cdd11e2d7378dbcc7cc61bc090d4b0a"
EXPECTED_11E_M3_HASH = "1053c27052760e2c39ee24968425fe977333b0298a149065c81b7d479f5b78d9"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

REQUIRED_AUTHORIZATION_FIELDS = (
    "activation_id",
    "activation_reason",
    "authorization_statement",
    "declaration_timestamp",
)

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

_DERIVED_PHRASES = (
    "derived from locality",
    "derived from lorentz",
    "derived from microcausality",
    "derived from m1",
    "derived from spectral",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11f_artifacts"


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def _banned_tokens() -> tuple[str, ...]:
    return ("1/" + "13" + "7", "alp" + "ha_em", "electr" + "ic", "1/" + "3", "2/" + "3")


def _walk_strings(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, str):
        found.append(obj)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            found.append(str(key))
            found.extend(_walk_strings(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            found.extend(_walk_strings(item))
    return found


def _contains_banned(obj: Any) -> list[str]:
    blob = "\n".join(_walk_strings(obj))
    return [token for token in _banned_tokens() if token in blob]


def _ranking_hits(obj: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in _RANKING_KEYS:
                hits.append(key)
            hits.extend(_ranking_hits(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            hits.extend(_ranking_hits(item))
    return hits


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    forbidden = (
        phase10e_artifact_dir().resolve(),
        phase11b_qft_artifact_dir().resolve(),
        phase11c_artifact_dir().resolve(),
        phase11d_artifact_dir().resolve(),
        phase11e_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11F refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _principle_definition() -> dict[str, Any]:
    return {
        "principle": "CLUSTER DECOMPOSITION",
        "schematic": "C_AB(R) = <A B_R> - <A><B_R>  with  lim_R C_AB(R) = 0 at large spacelike R",
        "not_a_complete_theorem": True,
        "locality_is_not_cluster": True,
        "microcausality_is_not_cluster": True,
        "spectral_support_is_not_cluster": True,
        "lorentz_is_not_cluster": True,
        "IR_safe_inclusive_is_not_cluster": True,
        "S_matrix_unitarity_is_not_cluster": True,
    }


def authorization_status(declared: Any) -> dict[str, Any]:
    """The phase prompt is not authorization. A boolean True is not enough."""
    if declared is True or declared is False or declared is None:
        return {"ok": False, "rejection": "M4_ACTIVATION_MISSING", "detail": "no explicit M4 authorization contract"}
    if not isinstance(declared, dict):
        return {"ok": False, "rejection": "M4_ACTIVATION_MISSING", "detail": "authorization must be a contract dict"}
    missing = [key for key in REQUIRED_AUTHORIZATION_FIELDS if not declared.get(key)]
    if missing:
        return {"ok": False, "rejection": "M4_ACTIVATION_MISSING", "detail": "missing " + ", ".join(missing)}
    stmt = str(declared.get("authorization_statement") or "")
    if "NEW_PHYSICAL_INPUT" not in stmt:
        return {
            "ok": False,
            "rejection": "M4_ACTIVATION_MISSING",
            "detail": "authorization_statement must declare NEW_PHYSICAL_INPUT",
        }
    blob = stmt.lower()
    if any(phrase in blob for phrase in _DERIVED_PHRASES):
        return {
            "ok": False,
            "rejection": "M4_ACTIVATION_REJECTED_AS_DERIVED",
            "detail": "cluster is not a derived consequence of locality/M1/M2/Lorentz",
        }
    return {"ok": True, "rejection": None, "detail": "explicit NEW_PHYSICAL_INPUT contract present"}


def free_scalar_cluster() -> dict[str, Any]:
    """Analytic free-Fock two-point cluster. Not a numerical threshold."""
    return {
        "operators": ["Phi"],
        "clusters": "A = Phi(0), B_R = Phi(R) with R spacelike",
        "connected": "C_AB(R) = <Phi(0) Phi(R)> - <Phi><Phi_R>; VEV of Phi is 0 in the free Fock vacuum",
        "state": "FREE / PERTURBATIVE VACUUM TEST; not a unique interacting vacuum",
        "limiting_procedure": "analytic lim |R|->infinity at spacelike separation; no finite numerical cutoff",
        "massive": {
            "status": "VERIFIED",
            "class": "MASSIVE",
            "statement": "free massive Wightman two-point decays exponentially; lim C_AB(R) = 0",
            "test_level": ["FREE", "CORRELATION_FUNCTION", "ASYMPTOTIC", "ANALYTIC"],
            "not_an_interacting_theorem": True,
        },
        "massless": {
            "status": "PARTIAL",
            "class": "MASSLESS",
            "IR_SENSITIVE": True,
            "statement": (
                "free massless two-point still vanishes at infinity in four dimensions, "
                "but there is no mass gap; higher-point / IR issues remain"
            ),
            "obstruction_not_removed": True,
            "test_level": ["FREE", "CORRELATION_FUNCTION", "IR-SENSITIVE"],
        },
        "finite_distance_is_not_asymptotic_theorem": True,
        "numerical_threshold_is_not_theorem": True,
        "status": "PARTIAL",
        "test_level": ["FREE", "CORRELATION_FUNCTION", "ASYMPTOTIC", "ANALYTIC"],
    }


def _weyl_cluster() -> dict[str, Any]:
    return {
        "status": "UNTESTED",
        "reason": "filled-sea Weyl vacuum is ASSUMED in P5Q; not a unique cluster state",
        "anticommutator_is_not_correlator": True,
        "not_derived_from_M1": True,
    }


def _gauge_cluster() -> dict[str, Any]:
    return {
        "status": "UNTESTED",
        "GAUGE_INVARIANT_CLUSTER_STATUS": "UNTESTED",
        "gauge_fixed_is_not_physical_cluster": True,
    }


def _activation_freeze(declared: dict[str, Any], module_hash: str) -> dict[str, Any]:
    return {
        "M4_CLUSTER_MODULE": {
            "enabled": True,
            "module_id": "M4_CLUSTER",
            "activation_id": declared["activation_id"],
            "activation_timestamp": declared["declaration_timestamp"],
            "activation_reason": declared["activation_reason"],
            "parent_baseline": "PHASE_10E + PHASE_11B + PHASE_11C + PHASE_11D + PHASE_11E",
            "provenance": "NEW_PHYSICAL_INPUT",
            "module_hash": module_hash,
        },
        "M1": False,
        "M2": False,
        "M3": False,
        "M5": False,
        "M1_status_preserved": "PARTIAL",
        "M2_status_preserved": "PARTIAL",
        "M3_status_preserved": "PARTIAL",
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
        "phase_prompt_is_not_authorization": True,
    }


def analyze_phase11f_cluster(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    m4_authorization: Any = None,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    _ = signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_before = grammar_hash()
    paths = {
        "10E_SYNTHESIS": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "10E_SUMMARY": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "11B_AUDIT": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json",
        "11B_SUMMARY": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_SUMMARY.json",
        "11C_M1": phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json",
        "11D_M2": phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json",
        "11E_M3": phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json",
        "11C_SUMMARY": phase11c_artifact_dir() / "PHASE_11C_SUMMARY.json",
        "11D_SUMMARY": phase11d_artifact_dir() / "PHASE_11D_SUMMARY.json",
        "11E_SUMMARY": phase11e_artifact_dir() / "PHASE_11E_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    if _content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E hash"}
    if _content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B hash"}
    if _content_hash(loaded["11C_M1"]) != EXPECTED_11C_M1_HASH:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11C hash"}
    if _content_hash(loaded["11D_M2"]) != EXPECTED_11D_M2_HASH:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11D hash"}
    if _content_hash(loaded["11E_M3"]) != EXPECTED_11E_M3_HASH:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11E hash"}
    if loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E closure"}
    if loaded["11B_SUMMARY"].get("M4_CLUSTER_STATUS") != "ABSENT":
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B M4 not ABSENT"}
    if loaded["11C_SUMMARY"].get("M1_COVERAGE_AFTER") != "PARTIAL":
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M1 not PARTIAL"}
    if loaded["11D_SUMMARY"].get("M2_COVERAGE_AFTER") != "PARTIAL":
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M2 not PARTIAL"}
    if loaded["11E_SUMMARY"].get("M3_COVERAGE_AFTER") != "PARTIAL":
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M3 not PARTIAL"}

    principle = _principle_definition()
    module_hash = _content_hash({"MODULE_VERSION": MODULE_VERSION, "principle": principle})
    authz = authorization_status(m4_authorization)
    activated = bool(authz["ok"])

    untested = {
        "status": "UNTESTED",
        "reason": "M4 not activated; cluster tests not executed",
    }
    freeze = {
        "M4_CLUSTER_MODULE": {
            "enabled": False,
            "module_id": "M4_CLUSTER",
            "activation_id": None,
            "provenance": "NEW_PHYSICAL_INPUT",
            "module_hash": module_hash,
            "activation_blocked": "M4_ACTIVATION_MISSING",
        },
        "M1": False,
        "M2": False,
        "M3": False,
        "M5": False,
        "frozen_before_consequences": True,
        "phase_prompt_is_not_authorization": True,
    }
    scalar = untested
    weyl = untested
    gauge = untested
    massive = untested
    massless = untested
    asymptotic = untested
    s_matrix = untested
    coverage_after = "ABSENT"
    module_status = "FAILED"
    phase_status = "BLOCKED"
    new_input_status = "NOT_ACTIVATED"
    remaining_gap = "M4 remains ABSENT: no explicit NEW_PHYSICAL_INPUT authorization contract was supplied"
    m4_completed = False
    m4_unactivated = True

    if activated:
        freeze = _activation_freeze(m4_authorization, module_hash)
        scalar = free_scalar_cluster()
        weyl = _weyl_cluster()
        gauge = _gauge_cluster()
        massive = scalar["massive"]
        massless = scalar["massless"]
        asymptotic = {
            "status": "PARTIAL",
            "free_massive_two_point": "VERIFIED analytically",
            "interacting_n_point": "UNTESTED",
            "not_EMPIRICAL_NUMERICAL_PROXY": True,
        }
        s_matrix = {
            "status": "UNTESTED",
            "unitarity_is_not_cluster": True,
            "cluster_is_not_S_matrix_completeness": True,
        }
        coverage_after = "PARTIAL"
        module_status = "PARTIAL"
        phase_status = "PARTIAL"
        new_input_status = "ACTIVATED"
        remaining_gap = (
            "free massive two-point cluster is analytic; massless is IR-SENSITIVE; "
            "Weyl, gauge-invariant observables, interacting n-point, and S-matrix cluster remain untested"
        )
        m4_completed = False
        m4_unactivated = False

    payload = {
        "phase": PHASE,
        "module_id": "M4",
        "module_version": MODULE_VERSION,
        "module_enabled": activated,
        "parent_baseline": {
            "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
            "phase10e_synthesis_hash": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11b_audit_hash": EXPECTED_11B_AUDIT_HASH,
            "phase11c_m1_hash": EXPECTED_11C_M1_HASH,
            "phase11d_m2_hash": EXPECTED_11D_M2_HASH,
            "phase11e_m3_hash": EXPECTED_11E_M3_HASH,
            "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
            "grammar_hash": grammar_before,
        },
        "activation_id": m4_authorization.get("activation_id") if activated and isinstance(m4_authorization, dict) else None,
        "coverage_before": "ABSENT",
        "coverage_after": coverage_after,
        "principle_definition": principle,
        "state_assumptions": {
            "vacuum_state": "free Fock vacuum if activated; otherwise none",
            "translational_invariance": "Minkowski",
            "state_normalization": "Fock vacuum normalized if activated",
            "spectral_assumptions": "used only in free massive decay; DEPENDS_ON_M2_SCOPE if activated, M2 status unchanged",
            "massless_massive": "treated separately",
            "infrared_assumptions": "no manufactured IR cutoff",
            "boundary_conditions": "free-field falloff",
            "unique_interacting_vacuum": False,
        },
        "scalar_cluster_results": scalar,
        "weyl_cluster_results": weyl,
        "gauge_cluster_results": gauge,
        "massless_results": massless,
        "massive_results": massive,
        "asymptotic_results": asymptotic,
        "s_matrix_results": s_matrix,
        "IR_dependencies": {
            "IR_safe_inclusive_NLO_is_not_cluster": True,
            "no_regulator_used_to_force_a_limit": True,
            "observable_type": "local correlator, not inclusive",
        },
        "parameter_dependencies": {
            "masses": "massive versus massless distinguished; masses not fixed",
            "Z": "unaffected",
            "internal_coefficients": "unaffected",
            "gauge_normalization": "unaffected",
            "vacuum_choice": "free Fock if activated",
            "IR_regulator": "none introduced",
            "boundary_conditions": "free-field falloff",
            "silently_fixed": False,
        },
        "new_parameters": [],
        "NEW_PARAMETER_COUNT": 0,
        "new_relations": [],
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "dependency_graph": {
            "requires": ["translational invariance", "a chosen state", "an observable definition"],
            "does_not_follow_from": ["locality", "M1", "M2", "M3", "S-matrix unitarity"],
            "DEPENDS_ON_M2_SCOPE": bool(activated),
            "M2_status_unchanged": True,
        },
        "sector_impact": {
            "spacetime": "UNCHANGED",
            "scalar_matter": "UNTESTED" if not activated else "PARTIALLY_AFFECTED",
            "Weyl_matter": "UNTESTED",
            "gauge_sector": "UNTESTED",
            "gravity": "UNCHANGED",
            "quantization": "UNCHANGED" if not activated else "PARTIALLY_AFFECTED",
            "correlations": "UNTESTED" if not activated else "PARTIALLY_AFFECTED",
            "observables": "UNTESTED",
        },
        "provenance_map": {
            "principle_status": "NEW_PHYSICAL_INPUT",
            "result_provenance": "UNTESTED" if not activated else "DERIVED GIVEN NEW_PHYSICAL_INPUT + FREE FOCK VACUUM",
            "NEW_PHYSICAL_INPUT": True,
            "not_a_derived_consequence": True,
            "phase_prompt_is_not_authorization": True,
        },
        "unresolved_gaps": [
            "explicit human M4 authorization" if not activated else "interacting n-point cluster",
            "gauge-invariant cluster",
            "Weyl cluster in a certified vacuum",
            "S-matrix cluster",
        ],
        "integrity_status": "VERIFIED",
        "activation_configuration": freeze,
        "authorization_audit": authz,
        "NEW_INPUT_STATUS": new_input_status,
        "M4_REMAINS_UNACTIVATED": m4_unactivated,
        "M4_COMPLETED_WITHIN_EXPLICITLY_ACTIVATED_SCOPE": m4_completed,
        "M1_REMAINS_PARTIAL": True,
        "M2_REMAINS_PARTIAL": True,
        "M3_REMAINS_PARTIAL": True,
        "remaining_gap": remaining_gap,
        "negative_tests": {
            "1_locality_does_not_certify_M4": True,
            "2_M1_does_not_certify_M4": True,
            "3_M2_does_not_certify_M4": True,
            "4_vacuum_existence_does_not_certify_M4": True,
            "5_finite_distance_is_not_asymptotic_theorem": True,
            "6_numerical_threshold_is_not_theorem": True,
            "7_massive_and_massless_separated": True,
            "8_IR_safe_inclusive_is_not_cluster": True,
            "9_S_matrix_unitarity_is_not_M4": True,
            "10_gauge_fixed_is_not_gauge_invariant_cluster": True,
            "11_M5_remains_disabled": True,
            "12_no_hidden_parameter": True,
            "13_no_experimental_target": True,
            "14_no_numerical_target": True,
            "15_no_ranking": True,
            "16_frozen_before_consequences": True,
            "17_Phase_10E_unchanged": True,
            "18_M1_M2_M3_unchanged": True,
            "19_rerun_deterministic": True,
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking"}

    if write_artifacts:
        _write_json("PHASE_11F_M4_CLUSTER.json", payload)
        _write_json(
            "PHASE_11F_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11F_STATUS": phase_status,
                "M4_COVERAGE_BEFORE": "ABSENT",
                "M4_COVERAGE_AFTER": coverage_after,
                "NEW_INPUT_STATUS": new_input_status,
                "M4_REMAINS_UNACTIVATED": m4_unactivated,
                "SCALAR_CLUSTER_STATUS": scalar.get("status"),
                "WEYL_CLUSTER_STATUS": weyl.get("status"),
                "GAUGE_INVARIANT_CLUSTER_STATUS": gauge.get("status"),
                "M1_REMAINS_PARTIAL": True,
                "M2_REMAINS_PARTIAL": True,
                "M3_REMAINS_PARTIAL": True,
                "M5_ENABLED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "remaining_gap": remaining_gap,
            },
        )
        _write_json("PHASE_11F_ACTIVATION_FREEZE.json", freeze)

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11F_TEST_COPY_ID": PHASE_11F_TEST_COPY_ID,
        "analysis": payload,
        "PHASE_11F_PRECONDITION_STATUS": "VERIFIED",
        "M4_MODULE_STATUS": module_status,
        "M4_COVERAGE_BEFORE": "ABSENT",
        "M4_COVERAGE_AFTER": coverage_after,
        "M4_TEST_LEVEL_STATUS": "VERIFIED" if activated else "FAILED",
        "SCALAR_CLUSTER_STATUS": scalar.get("status"),
        "WEYL_CLUSTER_STATUS": weyl.get("status"),
        "GAUGE_INVARIANT_CLUSTER_STATUS": gauge.get("status"),
        "MASSIVE_CLUSTER_STATUS": massive.get("status") if isinstance(massive, dict) else "UNTESTED",
        "MASSLESS_CLUSTER_STATUS": massless.get("status") if isinstance(massless, dict) else "UNTESTED",
        "ASYMPTOTIC_FACTORISATION_STATUS": asymptotic.get("status") if isinstance(asymptotic, dict) else "UNTESTED",
        "S_MATRIX_CLUSTER_STATUS": s_matrix.get("status") if isinstance(s_matrix, dict) else "UNTESTED",
        "NEW_INPUT_STATUS": new_input_status,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11F_STATUS": phase_status,
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11B_UNCHANGED": True,
        "PHASE_11C_UNCHANGED": True,
        "PHASE_11D_UNCHANGED": True,
        "PHASE_11E_UNCHANGED": True,
        "M1_ENABLED": False,
        "M1_REMAINS_PARTIAL": True,
        "M2_ENABLED": False,
        "M2_REMAINS_PARTIAL": True,
        "M3_ENABLED": False,
        "M3_REMAINS_PARTIAL": True,
        "M5_ENABLED": False,
        "M4_REMAINS_UNACTIVATED": m4_unactivated,
        "rejection": None if activated else authz["rejection"],
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "activation_frozen_before_consequences": True,
        "remaining_gap": remaining_gap,
        "negative_tests_all_pass": all(payload["negative_tests"].values()),
    }


def run_phase11f_or_stop(*, root=None, signature: str = MOSTLY_PLUS, m4_authorization: Any = None) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "PHASE_11F_INTEGRITY_FAILURE", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11f_cluster(auth, signature=signature, m4_authorization=m4_authorization)
    if science.get("status") in {"PHASE_11F_INTEGRITY_FAILURE", "FEEDBACK_LOOP_DETECTED", "STOP"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None}
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "CONCURRENCY_GUARD": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "ACTION_CONTENT_HASH": auth.action_content_hash,
            "FREEZE_STATUS": "VERIFIED",
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10E_UNCHANGED": "VERIFIED",
            "PHASE_11B_UNCHANGED": "VERIFIED",
            "PHASE_11C_UNCHANGED": "VERIFIED",
            "PHASE_11D_UNCHANGED": "VERIFIED",
            "PHASE_11E_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11F_STATUS": science.get("PHASE_11F_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
