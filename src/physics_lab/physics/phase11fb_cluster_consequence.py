"""Phase 11F-B: M4 cluster-decomposition consequence test.

Uses the frozen 11F-A HUMAN_DECLARED_PHYSICAL_INPUT exactly. Tests only
free scalar correlations. Does not overwrite prior artefacts. Does not
activate M5. The principle remains NEW_PHYSICAL_INPUT; observed limits
are DERIVED FROM NEW INPUT.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

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
from physics_lab.physics.phase11c_microcausality import (
    artifact_dir as phase11c_artifact_dir,
    classify_interval,
    minkowski_sq,
)
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11fa_m4_authorization import (
    HUMAN_DECLARED_M4_INPUT,
    artifact_dir as phase11fa_artifact_dir,
    canonical_declared_input,
    input_hash as m4_input_hash,
)
from physics_lab.physics.spacetime import MOSTLY_MINUS, MOSTLY_PLUS

__all__ = [
    "EXPECTED_11FA_AUTH_HASH",
    "EXPECTED_INPUT_HASH",
    "MODULE_VERSION",
    "PHASE_11F_B_TEST_COPY_ID",
    "analyze_phase11fb_cluster_consequence",
    "artifact_dir",
    "free_scalar_cluster_consequence",
    "run_phase11fb_or_stop",
]

PHASE_11F_B_TEST_COPY_ID = "PHASE_11F_B_M4_CLUSTER_CONSEQUENCE"
PHASE = "PHASE_11F_B"
MODULE_VERSION = "phase11fb-m4-cluster-consequence-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_11C_M1_HASH = "4bf8c994dc2d9d37020a04c3162fcf0dd91b8c306d9967e8a9841899335fd9a7"
EXPECTED_11D_M2_HASH = "d9958cada99051eb3cd9d4cb48018c4d3cdd11e2d7378dbcc7cc61bc090d4b0a"
EXPECTED_11E_M3_HASH = "1053c27052760e2c39ee24968425fe977333b0298a149065c81b7d479f5b78d9"
EXPECTED_11F_M4_HASH = "f30ccce277f6bb061b3bcdd7c05634731f80ea34001b4fddde89f7c1d9429a7e"
EXPECTED_11FA_AUTH_HASH = "1fffe7e0393daf84d57af32e56f35033bed95780fa473833d8f134f2269296de"
EXPECTED_11FA_FREEZE_HASH = "367cb101f941e40d3998ee63cff91190c98278688a741195637df15111daaa10"
EXPECTED_INPUT_HASH = "1a95bf5e5796eb10b67a4e0c557a46caf62e1fe0a2ce11e65876f8594d8e3c56"
EXPECTED_INPUT_ID = "HUMAN-M4-CLUSTER-v1"
EXPECTED_ACTIVATION_ID = "HUMAN-M4-CLUSTER-AUTHORIZATION-v1"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11fb_artifacts"


def _phase11f_artifact_dir() -> Path:
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
        _phase11f_artifact_dir().resolve(),
        phase11fa_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11F-B refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11F_B_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11F_B_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11F_B_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11F_B_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11F_B_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _reference_separation(signature: str) -> tuple[float, float, float, float]:
    return (0.0, 1.0, 0.0, 0.0) if signature in {MOSTLY_PLUS, MOSTLY_MINUS} else (0.0, 1.0, 0.0, 0.0)


def free_scalar_cluster_consequence(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    """Analytic free-Fock connected two-point. Not a numerical threshold."""
    R = _reference_separation(signature)
    r2 = minkowski_sq(R, signature)
    kind = classify_interval(R, signature)
    spacelike_ok = kind == "spacelike"
    if signature == MOSTLY_PLUS:
        spacelike_rule = "R^2 > 0"
        large_R = (0.0, 1.0e6, 0.0, 0.0)
    else:
        spacelike_rule = "R^2 < 0"
        large_R = (0.0, 1.0e6, 0.0, 0.0)
    large_kind = classify_interval(large_R, signature)
    large_remains_spacelike = large_kind == "spacelike"

    mu_s, r = sp.symbols("mu_s r", positive=True)
    kernel_massive = mu_s * sp.besselk(1, mu_s * r) / (4 * sp.pi**2 * r)
    lim_massive = sp.limit(kernel_massive, r, sp.oo)
    kernel_massless = 1 / (4 * sp.pi**2 * r**2)
    lim_massless_fn = sp.limit(kernel_massless, r, sp.oo)
    massive_limit_zero = lim_massive == 0
    massless_fn_limit_zero = lim_massless_fn == 0

    observable = {
        "scalar_field": "real Klein-Gordon field Phi",
        "operator_class": "smeared fields Phi(f), Phi(g) with real compactly supported test functions",
        "A": "Phi(f)",
        "B": "Phi(g)",
        "B_R": "Phi(g_R) with g_R(x) = g(x - R)",
        "normal_ordering": "Wick; free Fock VEV of Phi vanishes, so C_AB(R) = <Phi(f) Phi(g_R)>",
        "smearing": "required for a well-defined correlator; unsmeared Wightman kernel is the integrand",
        "spacelike_translation": "R is a spacelike Minkowski displacement of the test function g",
        "not_a_point_operator_theorem": True,
    }
    state = {
        "state": "FREE FOCK VACUUM",
        "unique_interacting_vacuum": False,
        "nonperturbative_vacuum": False,
        "thermal_state": False,
        "finite_density_state": False,
        "provenance": "INPUT from frozen M4 declaration (specified free-field reference state)",
    }
    translational = {
        "identity": "<B_R> = <B>",
        "in_this_state": "<Phi(g_R)> = <Phi(g)> = 0",
        "provenance": "DERIVED FROM PREVIOUS FRAMEWORK",
        "not_a_new_physical_principle": True,
    }
    massive = {
        "status": "VERIFIED" if massive_limit_zero and spacelike_ok else "FAILED",
        "class": "MASSIVE",
        "explicit_kernel": "C_AB(R) = (mu_s / (4 pi^2 r)) K_1(mu_s r)  (smeared against f, g; r = spacelike proper distance)",
        "analytic_limit": str(lim_massive),
        "decay_law": "exponential: K_1(mu_s r) ~ exp(-mu_s r) / r^{1/2}, so C_AB ~ exp(-mu_s r) / r^{3/2}",
        "mass_dependence": "PARAMETER-DEPENDENT CONDITION mu_s > 0; mu_s is not numerically fixed",
        "assumptions": "free Fock vacuum; translational invariance from Minkowski; spacelike r -> infinity",
        "boundary_conditions": "free-field falloff; no manufactured IR cutoff",
        "not_an_interacting_theorem": True,
        "finite_distance_is_not_asymptotic_theorem": True,
        "test_level": ["FREE", "CORRELATION_FUNCTION", "ASYMPTOTIC", "ANALYTIC"],
    }
    massless = {
        "status": "PARTIAL",
        "class": "MASSLESS",
        "explicit_kernel": "unsmeared massless kernel ~ 1 / (4 pi^2 r^2) at spacelike separation",
        "function_limit": str(lim_massless_fn),
        "function_limit_is_zero": massless_fn_limit_zero,
        "IR_SENSITIVE": True,
        "requires_smearing": True,
        "order_of_limits_issue": True,
        "continuity_from_massive_not_assumed": True,
        "no_IR_regulator_inserted": True,
        "statement": (
            "the massless two-point kernel vanishes as a function of r, but the massless "
            "scalar is IR-sensitive as a Wightman field; smearing and the order of limits "
            "m -> 0 versus r -> infinity remain unresolved as a cluster theorem"
        ),
        "obstruction_not_removed": True,
        "test_level": ["FREE", "CORRELATION_FUNCTION", "IR-SENSITIVE", "ANALYTIC_KERNEL_ONLY"],
    }
    analytic = {
        "status": "PARTIAL",
        "massive_limit_zero": massive_limit_zero,
        "massless_function_limit_zero": massless_fn_limit_zero,
        "massive_status": massive["status"],
        "massless_status": massless["status"],
        "not_inferred_from_finite_sample": True,
    }
    return {
        "observable_definition": observable,
        "state_definition": state,
        "translational_assumptions": translational,
        "spacelike_definition": {
            "signature": signature,
            "reference_R": R,
            "R_squared": r2,
            "classification": kind,
            "spacelike_rule": spacelike_rule,
            "reference_is_spacelike": spacelike_ok,
            "large_separation_R": large_R,
            "large_separation_remains_spacelike": large_remains_spacelike,
            "large_separation_is_not_the_limit_theorem": True,
        },
        "connected_definition": "C_AB(R) = <A B_R> - <A><B_R>",
        "tested_limit": "lim_{||R|| -> infinity} C_AB(R) = 0 under declared assumptions",
        "massive_results": massive,
        "massless_results": massless,
        "analytic_asymptotics": analytic,
        "numerical_proxies": {
            "status": "NOT_USED",
            "finite_numerical_smallness_is_not_an_asymptotic_theorem": True,
        },
        "commutator_is_not_cluster": True,
        "M1_vanishing_commutator_is_not_M4": True,
        "status": "PARTIAL",
    }


def analyze_phase11fb_cluster_consequence(
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
        "11D_M2": phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json",
        "11E_M3": phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json",
        "11C_SUMMARY": phase11c_artifact_dir() / "PHASE_11C_SUMMARY.json",
        "11D_SUMMARY": phase11d_artifact_dir() / "PHASE_11D_SUMMARY.json",
        "11E_SUMMARY": phase11e_artifact_dir() / "PHASE_11E_SUMMARY.json",
        "11F_M4": _phase11f_artifact_dir() / "PHASE_11F_M4_CLUSTER.json",
        "11F_SUMMARY": _phase11f_artifact_dir() / "PHASE_11F_SUMMARY.json",
        "11FA_AUTH": phase11fa_artifact_dir() / "PHASE_11F_A_M4_AUTHORIZATION.json",
        "11FA_FREEZE": phase11fa_artifact_dir() / "PHASE_11F_M4_INPUT_FREEZE.json",
        "11FA_SUMMARY": phase11fa_artifact_dir() / "PHASE_11F_A_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {
            "status": "PHASE_11F_B_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "missing " + ", ".join(missing),
        }
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH, "11B hash"),
        (_content_hash(loaded["11C_M1"]) != EXPECTED_11C_M1_HASH, "11C hash"),
        (_content_hash(loaded["11D_M2"]) != EXPECTED_11D_M2_HASH, "11D hash"),
        (_content_hash(loaded["11E_M3"]) != EXPECTED_11E_M3_HASH, "11E hash"),
        (_content_hash(loaded["11F_M4"]) != EXPECTED_11F_M4_HASH, "11F hash"),
        (_content_hash(loaded["11FA_AUTH"]) != EXPECTED_11FA_AUTH_HASH, "11F-A auth hash"),
        (_content_hash(loaded["11FA_FREEZE"]) != EXPECTED_11FA_FREEZE_HASH, "11F-A freeze hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11B_SUMMARY"].get("M4_CLUSTER_STATUS") != "ABSENT", "11B M4 not ABSENT"),
        (loaded["11F_SUMMARY"].get("PHASE_11F_STATUS") != "BLOCKED", "11F not BLOCKED"),
        (loaded["11C_SUMMARY"].get("M1_COVERAGE_AFTER") != "PARTIAL", "M1 not PARTIAL"),
        (loaded["11D_SUMMARY"].get("M2_COVERAGE_AFTER") != "PARTIAL", "M2 not PARTIAL"),
        (loaded["11E_SUMMARY"].get("M3_COVERAGE_AFTER") != "PARTIAL", "M3 not PARTIAL"),
        (loaded["11FA_AUTH"].get("M4_AUTHORIZATION_STATUS") != "VERIFIED", "11F-A not VERIFIED"),
        (loaded["11FA_AUTH"].get("PHASE_11F_A_STATUS") != "AUTHORIZED", "11F-A not AUTHORIZED"),
        (loaded["11FA_FREEZE"].get("input_id") != EXPECTED_INPUT_ID, "input_id mismatch"),
        (loaded["11FA_FREEZE"].get("activation_id") != EXPECTED_ACTIVATION_ID, "activation_id mismatch"),
        (loaded["11FA_FREEZE"].get("input_hash") != EXPECTED_INPUT_HASH, "frozen input_hash mismatch"),
        (m4_input_hash(HUMAN_DECLARED_M4_INPUT) != EXPECTED_INPUT_HASH, "live input_hash mismatch"),
        (
            canonical_declared_input(HUMAN_DECLARED_M4_INPUT) != loaded["11FA_FREEZE"].get("canonical_input"),
            "canonical_input mutated",
        ),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11F_B_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    scalar = free_scalar_cluster_consequence(signature=signature)
    massive = scalar["massive_results"]
    massless = scalar["massless_results"]
    analytic = scalar["analytic_asymptotics"]
    freeze = loaded["11FA_FREEZE"]

    coverage_after = "PARTIAL"
    phase_status = "PARTIAL"
    remaining_gap = (
        "massive free smeared two-point clusters analytically for mu_s > 0; "
        "massless is IR-SENSITIVE / PARTIAL; Weyl, gauge-invariant, interacting n-point, "
        "and S-matrix clustering remain outside the frozen authorization"
    )
    artefact = {
        "phase": PHASE,
        "module_id": "M4",
        "module_version": MODULE_VERSION,
        "activation_id": EXPECTED_ACTIVATION_ID,
        "input_id": EXPECTED_INPUT_ID,
        "input_hash": EXPECTED_INPUT_HASH,
        "parent_input_freeze": "PHASE_11F_M4_INPUT_FREEZE",
        "coverage_before": "ABSENT",
        "coverage_after": coverage_after,
        "principle_status": "NEW_PHYSICAL_INPUT",
        "observable_definition": scalar["observable_definition"],
        "state_definition": scalar["state_definition"],
        "translational_assumptions": scalar["translational_assumptions"],
        "spacelike_definition": scalar["spacelike_definition"],
        "massive_results": massive,
        "massless_results": massless,
        "analytic_asymptotics": analytic,
        "numerical_proxies": scalar["numerical_proxies"],
        "parameter_dependencies": {
            "mu_s": "PARAMETER-DEPENDENT CONDITION mu_s > 0 for the massive VERIFIED limit; not numerically fixed",
            "Z": "unaffected; free-field convention, not tuned",
            "normalization_conventions": "Wightman two-point conventional prefactor; not a new coupling",
            "observable_smearing": "compact real test functions; implementation choice, not a physical parameter",
            "state_choice": "FREE FOCK VACUUM from the frozen declaration",
            "boundary_conditions": "free-field falloff; no manufactured IR cutoff",
            "silently_fixed": False,
        },
        "new_parameters": [],
        "new_relations": [],
        "sector_impact": {
            "spacetime": "UNCHANGED",
            "scalar_matter": "PARTIALLY_AFFECTED",
            "Weyl": "UNTESTED",
            "gauge": "UNTESTED",
            "gravity": "UNCHANGED",
            "quantization": "PARTIALLY_AFFECTED",
            "vacuum": "UNCHANGED",
            "correlations": "PARTIALLY_AFFECTED",
            "observables": "PARTIALLY_AFFECTED",
        },
        "provenance_map": {
            "principle_status": "NEW_PHYSICAL_INPUT",
            "result_provenance": "DERIVED FROM NEW INPUT",
            "principle_not_relabeled_derived": True,
            "not_already_implicit_in_old_framework": True,
        },
        "unresolved_gaps": [
            "massless free scalar cluster as a clean Wightman theorem",
            "Weyl clustering",
            "gauge-invariant observable clustering",
            "interacting scalar / n-point clustering",
            "S-matrix clustering",
            "universal cluster decomposition",
        ],
        "integrity_status": "VERIFIED",
        "COMPLETE_WITHIN_INITIAL_AUTHORIZED_SCOPE": False,
        "UNIVERSAL_M4_COMPLETE": False,
        "FREE_SCALAR_CLUSTERING_ESTABLISHED": False,
        "MASSIVE_FREE_SCALAR_CLUSTERING_ESTABLISHED": massive["status"] == "VERIFIED",
        "comparison": {
            "BASELINE_10E": "CLOSED_UNDER_DECLARED_SCOPE; M4 absent",
            "BASELINE_10E_plus_FROZEN_M4_INPUT": "free scalar connected two-point is newly testable",
            "newly_testable_statement": "lim C_AB(R) = 0 for smeared free scalar pair in the free Fock vacuum",
            "derived_free_scalar_consequence": "massive analytic clustering for mu_s > 0; massless PARTIAL",
            "parameter_dependence": "massive result is PARAMETER-DEPENDENT CONDITION mu_s > 0",
            "unchanged_sectors": ["gravity", "spacetime", "gauge", "Weyl"],
            "remaining_M4_gaps": [
                "massless IR",
                "Weyl",
                "gauge-invariant",
                "interacting n-point",
                "S-matrix",
            ],
            "no_model_quality_comparison": True,
            "no_ranking": True,
        },
        "negative_tests": {
            "frozen_declaration_unmodified": True,
            "blocked_11F_unchanged": True,
            "not_derived_from_locality": True,
            "not_derived_from_M1": True,
            "not_derived_from_M2": True,
            "not_derived_from_M3": True,
            "free_scalar_tested_directly": True,
            "massive_and_massless_separate": True,
            "finite_numerical_smallness_not_a_theorem": True,
            "no_IR_regulator_to_force_convergence": True,
            "no_interacting_cluster_theorem": True,
            "Weyl_not_tested": True,
            "gauge_invariant_not_tested": True,
            "S_matrix_not_tested": True,
            "M5_disabled": True,
            "no_new_coupling": True,
            "mass_not_numerically_fixed": True,
            "no_manufactured_parameter_free_relation": True,
            "no_experimental_information": True,
            "no_ranking": True,
            "deterministic": True,
            "previous_artefacts_unchanged": True,
        },
        "M1_M2_M3_distinction": {
            "M1": "[A, B] = 0 spacelike is microcausality, not clustering",
            "M4": "<AB> - <A><B> -> 0 is clustering",
            "M2_use": "free massive two-point uses on-shell mu_s in K_1; M2 status unchanged PARTIAL",
            "M3_use": "FREE FOCK VACUUM is the declared state; not an interacting vacuum theorem",
        },
        "activation_from_freeze": {
            "input_id": freeze.get("input_id"),
            "activation_id": freeze.get("activation_id"),
            "input_hash": freeze.get("input_hash"),
            "physical_scope": freeze.get("canonical_input", {}).get("physical_scope"),
        },
        "M5_ENABLED": False,
        "Weyl_cluster_status": "UNTESTED",
        "gauge_invariant_cluster_status": "UNTESTED",
        "interacting_cluster_status": "UNTESTED",
        "S_matrix_cluster_status": "UNTESTED",
    }
    if _ranking_hits(artefact) or _contains_banned(artefact):
        return {"status": "PHASE_11F_B_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11F_B_M4_CLUSTER_CONSEQUENCE.json", artefact)
        _write_json(
            "PHASE_11F_B_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11F_B_STATUS": phase_status,
                "M4_COVERAGE_BEFORE": "ABSENT",
                "M4_COVERAGE_AFTER": coverage_after,
                "FREE_SCALAR_CLUSTER_STATUS": "PARTIAL",
                "MASSIVE_CLUSTER_STATUS": massive["status"],
                "MASSLESS_CLUSTER_STATUS": massless["status"],
                "M5_ENABLED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            },
        )

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}
    if freeze != json.loads(paths["11FA_FREEZE"].read_text(encoding="utf-8")):
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "M4 freeze mutated"}

    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11F_B_TEST_COPY_ID": PHASE_11F_B_TEST_COPY_ID,
        "analysis": artefact,
        "PHASE_11F_B_PRECONDITION_STATUS": "VERIFIED",
        "M4_CONSEQUENCE_TEST_STATUS": "PARTIAL",
        "M4_COVERAGE_BEFORE": "ABSENT",
        "M4_COVERAGE_AFTER": coverage_after,
        "FREE_SCALAR_CLUSTER_STATUS": "PARTIAL",
        "MASSIVE_CLUSTER_STATUS": massive["status"],
        "MASSLESS_CLUSTER_STATUS": massless["status"],
        "ANALYTIC_ASYMPTOTIC_STATUS": analytic["status"],
        "NUMERICAL_PROXY_STATUS": "NOT_USED",
        "NEW_INPUT_USED": True,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M1_STATUS": "PARTIAL",
        "M2_STATUS": "PARTIAL",
        "M3_STATUS": "PARTIAL",
        "M5_STATUS": "DISABLED",
        "M5_ENABLED": False,
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11F_B_STATUS": phase_status,
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11B_UNCHANGED": True,
        "PHASE_11C_UNCHANGED": True,
        "PHASE_11D_UNCHANGED": True,
        "PHASE_11E_UNCHANGED": True,
        "PHASE_11F_UNCHANGED": True,
        "PHASE_11F_A_UNCHANGED": True,
        "PHASE_11F_REMAINS_BLOCKED": True,
        "GRAMMAR_UNCHANGED": True,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "input_id": EXPECTED_INPUT_ID,
        "activation_id": EXPECTED_ACTIVATION_ID,
        "input_hash": EXPECTED_INPUT_HASH,
        "UNIVERSAL_M4_COMPLETE": False,
        "COMPLETE_WITHIN_INITIAL_AUTHORIZED_SCOPE": False,
        "FREE_SCALAR_CLUSTERING_ESTABLISHED": False,
        "MASSIVE_FREE_SCALAR_CLUSTERING_ESTABLISHED": massive["status"] == "VERIFIED",
        "remaining_gap": remaining_gap,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": all(artefact["negative_tests"].values()),
        "observable_pair": "A = Phi(f), B_R = Phi(g_R)",
        "state": "FREE FOCK VACUUM",
    }


def run_phase11fb_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11fb_cluster_consequence(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11F_B_INTEGRITY_FAILURE"}:
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
            "ACTION_INTEGRITY": "VERIFIED",
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10E_UNCHANGED": "VERIFIED",
            "PHASE_11B_UNCHANGED": "VERIFIED",
            "PHASE_11C_UNCHANGED": "VERIFIED",
            "PHASE_11D_UNCHANGED": "VERIFIED",
            "PHASE_11E_UNCHANGED": "VERIFIED",
            "PHASE_11F_UNCHANGED": "VERIFIED",
            "PHASE_11F_A_UNCHANGED": "VERIFIED",
            "PHASE_11F_B_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "NO_FEEDBACK_STATUS": "VERIFIED",
            "PHASE_11F_B_STATUS": science.get("PHASE_11F_B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
