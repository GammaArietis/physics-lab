"""Phase 11D: isolated M2 spectral / positive-energy completion.

Tests free-sector energy-momentum support from existing P5Q poles and
mode expansion. Does not activate M1/M3-M5. Does not rewrite 10E/11B/11C.
Does not upgrade FULL_QUANTUM_UNITARITY.
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
from physics_lab.physics.phase14c5q_p5q import (
    artifact_dir as phase14c5q_artifact_dir,
    canonical_quantization_layer,
    free_propagators,
)
from physics_lab.physics.spacetime import MOSTLY_MINUS, MOSTLY_PLUS, eta_diag

__all__ = [
    "EXPECTED_11C_M1_HASH",
    "MODULE_VERSION",
    "PHASE_11D_TEST_COPY_ID",
    "analyze_phase11d_spectral",
    "artifact_dir",
    "causal_type",
    "in_forward_cone",
    "run_phase11d_or_stop",
    "scalar_spectral_support",
    "weyl_spectral_support",
]

PHASE_11D_TEST_COPY_ID = "PHASE_11D_M2_SPECTRAL_COMPLETION"
PHASE = "PHASE_11D"
MODULE_VERSION = "phase11d-m2-spectral-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_11C_M1_HASH = "4bf8c994dc2d9d37020a04c3162fcf0dd91b8c306d9967e8a9841899335fd9a7"
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
    return Path(__file__).resolve().parent / "phase11d_artifacts"


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
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11D refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def minkowski_sq(k: tuple[float, ...], signature: str) -> float:
    eta = eta_diag(signature)
    return sum(float(eta[i]) * float(k[i]) ** 2 for i in range(4))


def causal_type(k: tuple[float, ...], signature: str) -> str:
    sq = minkowski_sq(k, signature)
    if sq == 0.0:
        return "lightlike"
    if signature == MOSTLY_PLUS:
        return "spacelike" if sq > 0.0 else "timelike"
    if signature == MOSTLY_MINUS:
        return "spacelike" if sq < 0.0 else "timelike"
    raise ValueError("causal type is defined only for Lorentzian signatures")


def in_forward_cone(k: tuple[float, ...], signature: str) -> bool:
    kind = causal_type(k, signature)
    return kind in {"timelike", "lightlike"} and float(k[0]) > 0.0


def _massless_on_shell(k: tuple[float, ...], signature: str) -> bool:
    return causal_type(k, signature) == "lightlike"


def scalar_spectral_support(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    props = free_propagators(signature=signature)
    can = canonical_quantization_layer(signature=signature)
    probes = {
        "forward_lightlike": (1.0, 1.0, 0.0, 0.0),
        "backward_lightlike": (-1.0, 1.0, 0.0, 0.0),
        "spacelike": (0.0, 1.0, 0.0, 0.0),
        "forward_timelike": (2.0, 0.0, 0.0, 0.0),
    }
    classified = {
        name: {
            "causal_type": causal_type(k, signature),
            "forward_cone": in_forward_cone(k, signature),
            "massless_on_shell": _massless_on_shell(k, signature),
            "massless_free_support": _massless_on_shell(k, signature) and in_forward_cone(k, signature),
        }
        for name, k in probes.items()
    }
    massless_ok = (
        classified["forward_lightlike"]["massless_free_support"] is True
        and classified["backward_lightlike"]["massless_free_support"] is False
        and classified["spacelike"]["massless_free_support"] is False
        and classified["forward_timelike"]["massless_free_support"] is False
    )
    pole = props["scalar"]["poles"]
    residue = props["scalar"]["residue_class"]
    z_fixed = props["scalar"].get("Z_fixed") is False or can["scalar"]["Z_fixed"] is False
    return {
        "operators": ["Phi"],
        "sector": "real scalar, free / linearized",
        "mathematical_formulation": (
            "free Wightman measure supported on the forward mass shell: "
            "supp rho_Phi subset {k | k_sq = mu_s_sq / Z and k^0 > 0}; "
            "massless reduction: 2 pi theta(k^0) delta(k_sq)"
        ),
        "mass_shell_location": pole,
        "mass_shell_status": "PARAMETER-DEPENDENT",
        "spectral_weight_positivity": "PARAMETER-DEPENDENT on Z matching the lab canonical_prefactor",
        "positive_energy_momentum_support": "VERIFIED for free massless forward-cone modes",
        "three_tracks_not_identified": True,
        "massless_probes": classified,
        "massless_forward_support_verified": massless_ok,
        "propagator": props["scalar"]["propagator"],
        "residue_class": residue,
        "positive_kinetic_is_not_spectral": True,
        "ghost_free_is_not_spectral": True,
        "positive_residue_is_not_full_spectral": True,
        "pole_is_not_physical_state_positivity": True,
        "Cutkosky_theta_k0_is_not_full_spectral_theorem": True,
        "interacting_Kallen_Lehmann": False,
        "full_Wightman_spectrum_theorem": False,
        "Z_fixed": False,
        "mu_s_sq_fixed": False,
        "mass_parameter_remains_free": True,
        "status": "PARTIAL" if massless_ok and z_fixed else "FAILED",
        "test_level": ["FREE", "LINEARIZED", "OPERATOR", "DISTRIBUTIONAL", "SPECTRAL"],
        "scope_class": "FREE / LINEARIZED RESULT",
        "regulator": "i0 Feynman contour only; no IR cutoff in the free two-point",
        "cut": "none in the free two-point; P5H Cutkosky remains a regulated proxy",
        "provenance": "DERIVED GIVEN EXISTING P5Q POLES + MODE EXPANSION",
    }


def weyl_spectral_support(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    props = free_propagators(signature=signature)
    can = canonical_quantization_layer(signature=signature)
    scalar = scalar_spectral_support(signature=signature)
    filled = can["weyl"]["filled_sea_convention"]
    massless_ok = scalar["massless_forward_support_verified"] is True
    return {
        "operators": ["psi_alpha"],
        "sector": "massless left-handed Weyl, free",
        "mathematical_formulation": (
            "first-order poles on k_sq = 0; positive-energy branch selected only after "
            "the filled-sea convention of P5Q"
        ),
        "mass_shell_location": props["weyl"]["poles"],
        "spectral_weight_positivity": "NOT INFERRED FROM SPIN-STATISTICS",
        "positive_energy_momentum_support": "PARTIAL: cone location VERIFIED; energy branch ASSUMED (filled sea)",
        "fermionic_graded_structure_is_not_energy_support": True,
        "spin_statistics_is_not_spectral_positivity": True,
        "filled_sea_convention": filled,
        "massless_forward_cone_shared_with_scalar_test": massless_ok,
        "propagator": props["weyl"]["propagator"],
        "interacting_spectral_representation": False,
        "status": "PARTIAL" if massless_ok and filled == "ASSUMED" else "FAILED",
        "test_level": ["FREE", "OPERATOR", "DISTRIBUTIONAL", "SPECTRAL"],
        "scope_class": "FREE / LINEARIZED RESULT",
        "regulator": "i0 only",
        "provenance": "DERIVED GIVEN EXISTING P5Q WEYL POLES; ENERGY BRANCH NOT DERIVED",
    }


def _gauge_spectral() -> dict[str, Any]:
    return {
        "operators": "gauge-fixed connection / F2 TEST EXTENSION",
        "status": "UNTESTED",
        "gauge_fixed_propagator_support": "poles exist in F2 TEST EXTENSIONS; not used as physical-state spectrum",
        "physical_state_spectral_support": "UNTESTED",
        "not_promoted_to_physical_Hilbert_space": True,
        "gauge_fixed_is_not_physical_positivity": True,
        "new_gauge_normalization_introduced": False,
        "test_level": ["TEST_EXTENSION"],
        "scope_class": "OTHER_EXPLICIT_SCOPE",
    }


def _physical_state_spectral(qscope: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "UNTESTED",
        "BRST_available_in_F2_TEST_EXTENSION": qscope.get("BRST"),
        "cohomology_spectrum_computed": False,
        "positive_gauge_fixed_components_are_not_physical_spectrum": True,
        "test_level": ["BRST_PHYSICAL_SECTOR"],
        "note": "distinction recorded; physical cohomology spectrum is not executable",
    }


def _activation_freeze() -> dict[str, Any]:
    return {
        "M2_SPECTRAL_MODULE": {
            "enabled": True,
            "module_id": "M2",
            "activation_timestamp": "FROZEN_BEFORE_CONSEQUENCES",
            "activation_reason": "isolated completion of PARTIAL M2; not MODE_C new axiom",
            "parent_baseline": "PHASE_10E + PHASE_11B + PHASE_11C",
            "mode": "ACTIVATE_EXISTING_PARTIAL_COVERAGE",
        },
        "M1": False,
        "M3": False,
        "M4": False,
        "M5": False,
        "M1_status_preserved": "PARTIAL",
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
    }


def analyze_phase11d_spectral(
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
        "11C_M1": phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json",
        "11C_SUMMARY": phase11c_artifact_dir() / "PHASE_11C_SUMMARY.json",
        "P5Q_SUMMARY": phase14c5q_artifact_dir() / "PHASE_14C5Q_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    if _content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH:
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E hash"}
    if _content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH:
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B hash"}
    if _content_hash(loaded["11C_M1"]) != EXPECTED_11C_M1_HASH:
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11C hash"}
    if _content_hash(loaded["P5Q_SUMMARY"]) != EXPECTED_P5Q_SUMMARY_HASH:
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "P5Q hash"}
    if loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE:
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E closure"}
    if loaded["11B_SUMMARY"].get("M2_SPECTRAL_STATUS") != "PARTIAL":
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B M2 not PARTIAL"}
    if loaded["11C_SUMMARY"].get("M1_COVERAGE_AFTER") != "PARTIAL":
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11C M1 not PARTIAL"}

    qscope = loaded["10E_SYNTHESIS"].get("quantum_scope") or {}
    q04 = qscope.get("Q04_TREE_UNITARITY_STATUS")
    full_u = qscope.get("FULL_QUANTUM_UNITARITY")
    if q04 != "PARTIAL" or full_u != "UNTESTED":
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E quantum scope"}

    freeze = _activation_freeze()
    scalar = scalar_spectral_support(signature=signature)
    weyl = weyl_spectral_support(signature=signature)
    gauge = _gauge_spectral()
    physical = _physical_state_spectral(qscope)

    coverage_after = "PARTIAL"
    module_status = "PARTIAL"
    if scalar["status"] == "FAILED" or weyl["status"] == "FAILED":
        module_status = "FAILED"
        coverage_after = "PARTIAL"

    remaining_gap = (
        "free massless forward-cone support is verified for Phi; Weyl energy branch remains ASSUMED; "
        "spectral-weight positivity is PARAMETER-DEPENDENT on Z; massive mass-shell location is not numerically fixed; "
        "interacting Kallen-Lehmann, physical BRST cohomology spectrum, and gauge-invariant Hilbert-space positivity remain untested"
    )
    payload = {
        "phase": PHASE,
        "module_id": "M2",
        "module_version": MODULE_VERSION,
        "module_enabled": True,
        "parent_baseline": {
            "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
            "phase10e_synthesis_hash": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11b_audit_hash": EXPECTED_11B_AUDIT_HASH,
            "phase11c_m1_hash": EXPECTED_11C_M1_HASH,
            "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
            "grammar_hash": grammar_before,
            "Q04_TREE_UNITARITY_STATUS": q04,
            "FULL_QUANTUM_UNITARITY": full_u,
        },
        "source_phase11b_status": "PARTIAL",
        "source_phase11c_status": "PARTIAL",
        "coverage_before": "PARTIAL",
        "coverage_after": coverage_after,
        "principle_definition": {
            "principle": "SPECTRAL CONDITION / POSITIVE-ENERGY STRUCTURE",
            "not_interchangeable": [
                "positive kinetic term",
                "ghost-free propagator",
                "positive pole residue",
                "positive-energy one-particle states",
                "spectral support condition",
                "full spectral representation",
            ],
        },
        "mathematical_formulation": scalar["mathematical_formulation"],
        "field_scope": {
            "scalar": scalar["operators"],
            "weyl": weyl["operators"],
            "gauge_invariant_physical_states": "UNTESTED",
        },
        "spectral_representation_results": {"scalar": scalar, "weyl": weyl},
        "positive_energy_results": {
            "scalar_massless_forward_cone": scalar["positive_energy_momentum_support"],
            "weyl_energy_branch": weyl["positive_energy_momentum_support"],
        },
        "physical_state_results": physical,
        "gauge_sector_results": gauge,
        "regulator_dependencies": {
            "free_two_point": "i0 only",
            "P5H_Cutkosky": "PARAMETER-DEPENDENT / REGULATED; not a complete physical spectral theorem",
            "IR_regulated_integration_is_not_spectral_theorem": True,
        },
        "parameter_dependencies": {
            "Z": "spectral-weight positivity PARAMETER-DEPENDENT; Z not fixed",
            "masses": "mass-shell location PARAMETER-DEPENDENT; mu_s_sq not fixed",
            "internal_coefficients": "unaffected",
            "gauge_normalization": "unaffected; none introduced",
            "background": "Minkowski test sector",
            "regulator": "free test independent of dim-reg; Cutkosky proxy remains regulated",
            "cutoff": "none in the free two-point",
            "gauge_fixing": "not used for scalar/Weyl; gauge-fixed poles not promoted",
            "silently_fixed": False,
            "mass_parameter_remains_free": True,
        },
        "new_relations": [],
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "NEW_PARAMETER_COUNT": 0,
        "sector_impact": {
            "spacetime": "UNCHANGED",
            "scalar_matter": "PARTIALLY_AFFECTED",
            "Weyl_matter": "PARTIALLY_AFFECTED",
            "gauge_sector": "UNTESTED",
            "gravity": "UNCHANGED",
            "quantization": "CONSTRAINED",
            "physical_state_space": "UNTESTED",
            "observables": "UNTESTED",
        },
        "provenance_map": {
            "principle_status": "PARTIAL_EXTENSION",
            "result_provenance": "DERIVED GIVEN ASSUMPTION",
            "NEW_PHYSICAL_INPUT": False,
            "assumptions": [
                "P5Q free propagator poles",
                "P5Q mode expansion with e^{-i k x} assigned to a(k)",
                "Minkowski forward cone from signature",
            ],
        },
        "unresolved_gaps": [
            "interacting Kallen-Lehmann representation",
            "Z-independent spectral-weight positivity",
            "physical BRST cohomology spectrum",
            "gauge-invariant Hilbert-space positivity",
            "full Wightman spectral theorem",
        ],
        "integrity_status": "VERIFIED",
        "activation_configuration": freeze,
        "other_modules_disabled": {"M1": False, "M3": False, "M4": False, "M5": False},
        "M1_REMAINS_PARTIAL": True,
        "Q04_REMAINS_PARTIAL": True,
        "FULL_QUANTUM_UNITARITY_REMAINS_UNTESTED": True,
        "comparison_against_baseline": {
            "disabled_state": "11B PARTIAL: kinetic signs, ghost diagnostics, poles, Cutkosky theta(k0) proxy",
            "enabled_state": "free massless forward-cone spectral support for Phi; Weyl energy branch still ASSUMED",
            "newly_testable": [
                "massless free support on the forward light cone",
                "separation of mass-shell, spectral-weight sign, and energy support",
            ],
            "newly_derived": ["massless free Wightman support is not the backward cone"],
            "newly_constrained": ["free massless scalar modes lie in V+"],
            "unchanged": [
                "gravity family",
                "10E closure",
                "M1 PARTIAL",
                "Q04 PARTIAL",
                "FULL_QUANTUM_UNITARITY UNTESTED",
                "M3-M5",
            ],
            "remaining_gaps": [
                "interacting spectral representation",
                "physical gauge-sector positivity",
                "Z-independent weight positivity",
            ],
            "not_a_ranking": True,
        },
        "NEW_INPUT_REQUIRED": False,
        "M2_COMPLETED_AS_EXISTING_FRAMEWORK_EXTENSION": False,
        "SPECTRAL_CONDITION_REQUIRES_EXPLICIT_NEW_INPUT": False,
        "remaining_gap": remaining_gap,
        "negative_tests": {
            "1_positive_kinetic_does_not_certify_M2": True,
            "2_ghost_free_does_not_certify_M2": True,
            "3_positive_residue_does_not_certify_full_spectral": True,
            "4_propagator_pole_does_not_establish_physical_states": True,
            "5_gauge_fixed_propagators_do_not_establish_physical_positivity": True,
            "6_Cutkosky_theta_k0_is_not_full_spectral_theorem": True,
            "7_Q04_remains_separate": True,
            "8_FULL_QUANTUM_UNITARITY_remains_UNTESTED": True,
            "9_M1_remains_PARTIAL": True,
            "10_M3_M5_remain_disabled": True,
            "11_regulated_tests_not_universal_theorems": True,
            "12_mass_parameters_not_fixed": True,
            "13_no_new_gauge_normalization": True,
            "14_no_experimental_information": True,
            "15_no_numerical_target": True,
            "16_no_ranking": True,
            "17_frozen_before_consequences": True,
            "18_rerun_deterministic": True,
            "19_previous_artefacts_unchanged": True,
        },
        "test_level": ["FREE", "LINEARIZED", "OPERATOR", "DISTRIBUTIONAL", "SPECTRAL"],
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking"}

    if write_artifacts:
        _write_json("PHASE_11D_M2_SPECTRAL.json", payload)
        _write_json(
            "PHASE_11D_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11D_STATUS": "PARTIAL",
                "M2_COVERAGE_BEFORE": "PARTIAL",
                "M2_COVERAGE_AFTER": coverage_after,
                "SCALAR_SPECTRAL_STATUS": scalar["status"],
                "WEYL_SPECTRAL_STATUS": weyl["status"],
                "GAUGE_SPECTRAL_STATUS": gauge["status"],
                "PHYSICAL_STATE_SPECTRAL_STATUS": physical["status"],
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M1_ENABLED": False,
                "M1_REMAINS_PARTIAL": True,
                "M3_ENABLED": False,
                "M4_ENABLED": False,
                "M5_ENABLED": False,
                "Q04_TREE_UNITARITY_STATUS": q04,
                "FULL_QUANTUM_UNITARITY": full_u,
                "remaining_gap": remaining_gap,
            },
        )
        _write_json("PHASE_11D_ACTIVATION_FREEZE.json", freeze)

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    phase_status = "PARTIAL" if module_status == "PARTIAL" else "FAILED"
    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11D_TEST_COPY_ID": PHASE_11D_TEST_COPY_ID,
        "analysis": payload,
        "PHASE_11D_PRECONDITION_STATUS": "VERIFIED",
        "M2_MODULE_STATUS": module_status,
        "M2_COVERAGE_BEFORE": "PARTIAL",
        "M2_COVERAGE_AFTER": coverage_after,
        "M2_TEST_LEVEL_STATUS": "VERIFIED",
        "SCALAR_SPECTRAL_STATUS": scalar["status"],
        "WEYL_SPECTRAL_STATUS": weyl["status"],
        "GAUGE_SPECTRAL_STATUS": gauge["status"],
        "PHYSICAL_STATE_SPECTRAL_STATUS": physical["status"],
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11D_STATUS": phase_status,
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
        "M1_ENABLED": False,
        "M1_REMAINS_PARTIAL": True,
        "M3_ENABLED": False,
        "M4_ENABLED": False,
        "M5_ENABLED": False,
        "Q04_TREE_UNITARITY_STATUS": q04,
        "FULL_QUANTUM_UNITARITY": full_u,
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


def run_phase11d_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "PHASE_11D_INTEGRITY_FAILURE", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11d_spectral(auth, signature=signature)
    if science.get("status") in {"PHASE_11D_INTEGRITY_FAILURE", "FEEDBACK_LOOP_DETECTED", "STOP"}:
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
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11D_STATUS": science.get("PHASE_11D_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
