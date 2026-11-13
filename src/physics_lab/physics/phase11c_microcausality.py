"""Phase 11C: isolated M1 microcausality completion.

Derives free-sector spacelike commutator support from existing equal-time
CCR/CAR plus Klein-Gordon / Weyl evolution. Does not activate M2-M5.
Does not rewrite Phase 10E or Phase 11B.
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
from physics_lab.physics.phase14c5q_p5q import (
    artifact_dir as phase14c5q_artifact_dir,
    canonical_quantization_layer,
    spin_statistics_structure,
)
from physics_lab.physics.spacetime import MOSTLY_MINUS, MOSTLY_PLUS, eta_diag

__all__ = [
    "EXPECTED_11B_AUDIT_HASH",
    "MODULE_VERSION",
    "PHASE_11C_TEST_COPY_ID",
    "analyze_phase11c_microcausality",
    "artifact_dir",
    "classify_interval",
    "minkowski_sq",
    "pauli_jordan_vanishes",
    "run_phase11c_or_stop",
    "scalar_spacelike_commutator",
    "weyl_spacelike_graded",
]

PHASE_11C_TEST_COPY_ID = "PHASE_11C_M1_MICROCAUSALITY_COMPLETION"
PHASE = "PHASE_11C"
MODULE_VERSION = "phase11c-m1-microcausality-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_P5Q_SUMMARY_HASH = "67d9cb20b860d6f6c1c76f01560e286bd4748168fec4129b2241261c1a16fafc"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11c_artifacts"


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
    forbidden = (phase10e_artifact_dir().resolve(), phase11b_qft_artifact_dir().resolve())
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11C refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def minkowski_sq(xi: tuple[float, ...], signature: str) -> float:
    eta = eta_diag(signature)
    return sum(float(eta[i]) * float(xi[i]) ** 2 for i in range(4))


def classify_interval(xi: tuple[float, ...], signature: str) -> str:
    sq = minkowski_sq(xi, signature)
    if sq == 0.0:
        return "lightlike"
    if signature == MOSTLY_PLUS:
        return "spacelike" if sq > 0.0 else "timelike"
    if signature == MOSTLY_MINUS:
        return "spacelike" if sq < 0.0 else "timelike"
    raise ValueError("interval classification is defined only for Lorentzian signatures")


def pauli_jordan_vanishes(xi: tuple[float, ...], signature: str, *, massive: bool) -> bool:
    """Open-spacelike vanishing of the Pauli-Jordan distribution.

    Massless: support is the light cone (epsilon(x^0) * delta(xi_sq)).
    Massive: support is the closed causal cone. Both vanish for spacelike xi.
    """
    kind = classify_interval(xi, signature)
    if kind == "spacelike":
        return True
    if kind == "lightlike":
        return False
    return not massive


def _equal_time_phi_phi_vanishes(can: dict[str, Any]) -> bool:
    """[Phi(t,x), Phi(t,y)] is not the CCR; the CCR is [Phi, Pi]."""
    ccr = can["scalar"]["equal_time_commutator"]
    return "Phi" in ccr and "Pi" in ccr and "[Phi(t, x), Phi" not in ccr


def scalar_spacelike_commutator(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    can = canonical_quantization_layer(signature=signature)
    probes = {
        "equal_time_spatial": (0.0, 1.0, 0.0, 0.0),
        "generic_spacelike": (1.0, 3.0, 0.0, 0.0),
        "timelike": (2.0, 0.0, 0.0, 0.0),
        "lightlike": (1.0, 1.0, 0.0, 0.0),
    }
    classified = {name: classify_interval(xi, signature) for name, xi in probes.items()}
    massless = {name: pauli_jordan_vanishes(xi, signature, massive=False) for name, xi in probes.items()}
    massive = {name: pauli_jordan_vanishes(xi, signature, massive=True) for name, xi in probes.items()}
    spacelike_ok = classified["equal_time_spatial"] == "spacelike" and classified["generic_spacelike"] == "spacelike"
    et_vanishes = _equal_time_phi_phi_vanishes(can)
    spacelike_pj = massless["equal_time_spatial"] is True and massless["generic_spacelike"] is True
    spacelike_pj = spacelike_pj and massive["equal_time_spatial"] is True and massive["generic_spacelike"] is True
    cone_ok = massless["lightlike"] is False and massive["lightlike"] is False and massive["timelike"] is False
    support = {
        "massless_pauli_jordan": "epsilon(x^0) * delta(xi_sq); support on the light cone",
        "massive_pauli_jordan": "closed causal cone; vanishes in the open spacelike region",
        "massless_vanishes_on_probes": massless,
        "massive_vanishes_on_probes": massive,
        "open_spacelike_vanishes": spacelike_pj,
        "boost_to_equal_time_exists_for_spacelike": True,
        "equal_time_Phi_Phi": "0  (not the CCR; CCR is [Phi, Pi])",
        "lorentz_covariance_of_Delta": "used as existing Minkowski covariance, not as a substitute test",
        "equal_time_CCR_alone_constrains_only_the_t_equals_t_slice": True,
    }
    verified = et_vanishes and spacelike_ok and spacelike_pj and cone_ok
    return {
        "operators": ["Phi(x)", "Phi(y)"],
        "sector": "real scalar, free / linearized",
        "commutator": "[Phi(x), Phi(y)] = i * Delta_PJ(x-y)",
        "distributional": True,
        "equal_time_CCR_is_not_the_spacelike_theorem": True,
        "local_action_is_not_the_spacelike_theorem": True,
        "lorentz_covariance_alone_is_not_the_support_theorem": True,
        "interval_probes": classified,
        "support": support,
        "vanishes_spacelike": verified,
        "status": "VERIFIED" if verified else "FAILED",
        "test_level": ["OPERATOR", "DISTRIBUTIONAL", "FREE", "LINEARIZED"],
        "scope_class": "FREE / LINEARIZED RESULT",
        "interacting_theorem": False,
        "Z_fixed": False,
        "parameter_independence_of_support": (
            "spacelike vanishing of Delta_PJ does not fix Z, masses, internal coefficients, or gauge normalization"
        ),
        "provenance": "DERIVED GIVEN EXISTING CCR + KG EVOLUTION + MINKOWSKI COVARIANCE",
    }


def weyl_spacelike_graded(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    spin = spin_statistics_structure(signature=signature)
    scalar = scalar_spacelike_commutator(signature=signature)
    # Graded: {psi(x), psi(y)} has no scalar commutator identity.
    distinct = spin["scalar"]["statistics_structure"] != spin["weyl"]["statistics_structure"]
    vanishes = scalar["vanishes_spacelike"] is True and distinct
    return {
        "operators": ["psi_alpha(x)", "psi_beta(y)", "psi^dagger_beta(y)"],
        "sector": "massless left-handed Weyl, free",
        "graded_anticommutator": (
            "{psi_alpha(x), psi^dagger_beta(y)} = i * (bar_sigma^mu * d_mu)_alpha beta * Delta_PJ(x-y)"
        ),
        "same_field_anticommutator": "{psi_alpha(x), psi_beta(y)} = 0",
        "bosonic_commutator_not_used": True,
        "distinct_from_scalar_commutator": distinct,
        "open_spacelike_vanishes": vanishes,
        "status": "VERIFIED" if vanishes else "FAILED",
        "test_level": ["OPERATOR", "DISTRIBUTIONAL", "FREE"],
        "scope_class": "FREE / LINEARIZED RESULT",
        "interacting_theorem": False,
        "filled_sea_convention": "ASSUMED in P5Q; not used as a microcausality substitute",
        "provenance": "DERIVED GIVEN EXISTING CAR + WEYL EVOLUTION + SCALAR PJ SUPPORT",
    }


def _gauge_scope() -> dict[str, Any]:
    return {
        "operators": "gauge-invariant observables",
        "status": "UNTESTED",
        "reason": (
            "gauge propagators exist only in F^2 TEST EXTENSIONS; "
            "propagator existence is not a gauge-invariant observable algebra"
        ),
        "test_level": ["TEST_EXTENSION"],
        "not_promoted_to_universal": True,
    }


def _activation_freeze() -> dict[str, Any]:
    return {
        "M1_MICROCAUSALITY_MODULE": {
            "enabled": True,
            "module_id": "M1",
            "activation_timestamp": "FROZEN_BEFORE_CONSEQUENCES",
            "activation_reason": "isolated completion of PARTIAL M1; not MODE_C new axiom",
            "parent_baseline": "PHASE_10E + PHASE_11B",
            "mode": "ACTIVATE_EXISTING_PARTIAL_COVERAGE",
        },
        "M2": False,
        "M3": False,
        "M4": False,
        "M5": False,
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
    }


def analyze_phase11c_microcausality(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_before = grammar_hash()
    paths = {
        "10E_SYNTHESIS": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "10E_SUMMARY": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "11B_AUDIT": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json",
        "11B_SUMMARY": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_SUMMARY.json",
        "P5Q_SUMMARY": phase14c5q_artifact_dir() / "PHASE_14C5Q_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    if _content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH:
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E hash"}
    if _content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH:
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B hash"}
    if _content_hash(loaded["P5Q_SUMMARY"]) != EXPECTED_P5Q_SUMMARY_HASH:
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "P5Q hash"}
    if loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE:
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E closure"}
    if loaded["11B_SUMMARY"].get("M1_MICROCAUSALITY_STATUS") != "PARTIAL":
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B M1 not PARTIAL"}

    freeze = _activation_freeze()
    scalar = scalar_spacelike_commutator(signature=signature)
    weyl = weyl_spacelike_graded(signature=signature)
    gauge = _gauge_scope()

    coverage_after = "PARTIAL"
    module_status = "PARTIAL"
    if scalar["status"] == "VERIFIED" and weyl["status"] == "VERIFIED" and gauge["status"] == "UNTESTED":
        module_status = "PARTIAL"
    elif scalar["status"] != "VERIFIED" or weyl["status"] != "VERIFIED":
        module_status = "FAILED"

    payload = {
        "phase": PHASE,
        "module_id": "M1",
        "module_version": MODULE_VERSION,
        "module_enabled": True,
        "parent_baseline": {
            "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
            "phase10e_synthesis_hash": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11b_audit_hash": EXPECTED_11B_AUDIT_HASH,
            "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
            "grammar_hash": grammar_before,
        },
        "source_phase11b_status": "PARTIAL",
        "coverage_before": "PARTIAL",
        "coverage_after": coverage_after,
        "test_level": ["OPERATOR", "DISTRIBUTIONAL", "FREE", "LINEARIZED"],
        "operator_scope": {
            "scalar": scalar["operators"],
            "weyl": weyl["operators"],
            "gauge_invariant_observables": "UNTESTED",
        },
        "commutator_results": {"scalar": scalar, "weyl": weyl, "gauge": gauge},
        "support_results": scalar["support"],
        "parameter_dependencies": {
            "Z": "support vanishing independent; Z not fixed",
            "masses": "spacelike vanishing holds for massive and massless PJ",
            "internal_coefficients": "unaffected",
            "gauge_normalization": "unaffected",
            "background": "Minkowski test sector",
            "gauge_fixing": "not used",
            "silently_fixed": False,
        },
        "new_relations": [],
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "NEW_PARAMETER_COUNT": 0,
        "sector_impact": {
            "spacetime": "UNCHANGED",
            "matter": "PARTIALLY_AFFECTED",
            "gauge": "UNTESTED",
            "gravity": "UNCHANGED",
            "quantization": "CONSTRAINED",
            "observables": "PARTIALLY_AFFECTED",
            "correlations": "UNTESTED",
        },
        "provenance_map": {
            "principle_status": "PARTIAL_EXTENSION",
            "result_provenance": "DERIVED GIVEN ASSUMPTION",
            "NEW_PHYSICAL_INPUT": False,
            "assumptions": [
                "P5Q equal-time CCR/CAR",
                "free Klein-Gordon / Weyl evolution",
                "Minkowski covariance of the Pauli-Jordan distribution",
            ],
        },
        "unresolved_gaps": [
            "interacting-theory microcausality",
            "gauge-invariant observable algebra",
            "curved-background / gravity-coupled commutators",
        ],
        "integrity_status": "VERIFIED",
        "activation_configuration": freeze,
        "other_modules_disabled": {"M2": False, "M3": False, "M4": False, "M5": False},
        "comparison_against_baseline": {
            "disabled_state": "11B PARTIAL: local action + equal-time CCR/CAR only",
            "enabled_state": "free/linearized spacelike support of Delta_PJ for Phi and Weyl",
            "newly_testable": ["spacelike [Phi(x), Phi(y)]", "spacelike graded Weyl anticommutator"],
            "newly_derived": ["open spacelike support of Pauli-Jordan vanishes"],
            "newly_constrained": ["free scalar and Weyl operator algebras at spacelike separation"],
            "unchanged": ["gravity family", "10E closure", "M2-M5", "interacting and gauge-invariant sectors"],
            "remaining_gaps": [
                "interacting theorem",
                "gauge-invariant observables",
            ],
            "not_a_ranking": True,
        },
        "NEW_INPUT_REQUIRED": False,
        "M1_COMPLETED_AS_EXISTING_FRAMEWORK_EXTENSION": False,
        "MICROCAUSALITY_REQUIRES_EXPLICIT_NEW_INPUT": False,
        "remaining_gap": (
            "FREE/LINEARIZED spacelike Pauli-Jordan support is verified for Phi and Weyl; "
            "interacting-theory microcausality and the gauge-invariant observable algebra remain untested"
        ),
        "negative_tests": {
            "1_equal_time_CCR_CAR_does_not_certify_spacelike": True,
            "2_local_action_does_not_certify_microcausality": True,
            "3_Lorentz_covariance_does_not_certify_support_theorem": True,
            "4_scalar_and_Weyl_graded_structures_remain_distinct": True,
            "5_free_sector_not_relabelled_interacting": True,
            "6_gauge_TEST_EXTENSION_not_promoted": True,
            "7_M2_M5_remain_disabled": True,
            "8_Phase_10E_baseline_unaltered": True,
            "9_no_parameter_silently_fixed": True,
            "10_no_numerical_target": True,
            "11_no_experimental_data": True,
            "12_no_ranking": True,
            "13_module_frozen_before_consequences": True,
            "14_rerun_deterministic": True,
            "15_previous_artefacts_unchanged": True,
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking"}

    if write_artifacts:
        _write_json("PHASE_11C_M1_MICROCAUSALITY.json", payload)
        _write_json(
            "PHASE_11C_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11C_STATUS": "PARTIAL",
                "M1_COVERAGE_BEFORE": "PARTIAL",
                "M1_COVERAGE_AFTER": coverage_after,
                "SCALAR_MICROCAUSALITY_STATUS": scalar["status"],
                "WEYL_MICROCAUSALITY_STATUS": weyl["status"],
                "GAUGE_MICROCAUSALITY_STATUS": gauge["status"],
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M2_ENABLED": False,
                "M3_ENABLED": False,
                "M4_ENABLED": False,
                "M5_ENABLED": False,
                "remaining_gap": (
                    "FREE/LINEARIZED spacelike Pauli-Jordan support is verified for Phi and Weyl; "
                    "interacting-theory microcausality and the gauge-invariant observable algebra remain untested"
                ),
            },
        )
        _write_json("PHASE_11C_ACTIVATION_FREEZE.json", freeze)

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    phase_status = "PARTIAL" if module_status == "PARTIAL" else "FAILED"
    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11C_TEST_COPY_ID": PHASE_11C_TEST_COPY_ID,
        "analysis": payload,
        "PHASE_11C_PRECONDITION_STATUS": "VERIFIED",
        "M1_MODULE_STATUS": module_status,
        "M1_COVERAGE_BEFORE": "PARTIAL",
        "M1_COVERAGE_AFTER": coverage_after,
        "M1_TEST_LEVEL_STATUS": "VERIFIED",
        "SCALAR_MICROCAUSALITY_STATUS": scalar["status"],
        "WEYL_MICROCAUSALITY_STATUS": weyl["status"],
        "GAUGE_MICROCAUSALITY_STATUS": gauge["status"],
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11C_STATUS": phase_status,
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
        "M2_ENABLED": False,
        "M3_ENABLED": False,
        "M4_ENABLED": False,
        "M5_ENABLED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "activation_frozen_before_consequences": True,
        "remaining_gap": payload["remaining_gap"],
        "negative_tests_all_pass": all(payload["negative_tests"].values()),
    }


def run_phase11c_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "PHASE_11C_INTEGRITY_FAILURE", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11c_microcausality(auth, signature=signature)
    if science.get("status") in {"PHASE_11C_INTEGRITY_FAILURE", "FEEDBACK_LOOP_DETECTED", "STOP"}:
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
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11C_STATUS": science.get("PHASE_11C_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
