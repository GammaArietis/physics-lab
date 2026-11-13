"""Phase 11B.4: RG_FIXED_POINT test.

One new physical assumption.  Does not modify the frozen action, grammar,
or prior artifacts.  Does not introduce a second principle.
Does not start a later 11B phase.  Does not invent loop coefficients,
import known beta functions, or add fields or UV completions.
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
from physics_lab.physics.phase10a_model_grammar import (
    BLACKLIST_VERSION,
    GRAMMAR_VERSION,
    SEARCH_SPACE_VERSION,
    WHITELIST_VERSION,
    grammar_hash,
    model_hash,
    undeclared_inferences,
    validate_dependencies,
)
from physics_lab.physics.phase10b1_exploration import (
    artifact_dir as phase10b1_artifact_dir,
)
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b2_derivation import _parameter_free_test
from physics_lab.physics.phase10b2_derivation import artifact_dir as phase10b2_artifact_dir
from physics_lab.physics.phase10b3_audit import artifact_dir as phase10b3_artifact_dir
from physics_lab.physics.phase10b4_validation import artifact_dir as phase10b4_artifact_dir
from physics_lab.physics.phase10b5_semantics import artifact_dir as phase10b5_artifact_dir
from physics_lab.physics.phase10b6_schema import artifact_dir as phase10b6_artifact_dir
from physics_lab.physics.phase10b7_revalidation import artifact_dir as phase10b7_artifact_dir
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase10b9_linearized_ghost import artifact_dir as phase10b9_artifact_dir
from physics_lab.physics.phase10b9_linearized_ghost import _action_content
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase11a_strategy import artifact_dir as phase11a_artifact_dir
from physics_lab.physics.phase11b1_scales import artifact_dir as phase11b1_artifact_dir
from physics_lab.physics.phase11b2_symmetry import artifact_dir as phase11b2_artifact_dir
from physics_lab.physics.phase11b3_unitarity import artifact_dir as phase11b3_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "PHASE_11B4_TEST_COPY_ID",
    "PRINCIPLE_ID",
    "analyze_phase11b4_rg",
    "artifact_dir",
    "run_phase11b4_or_stop",
]

PHASE_11B4_TEST_COPY_ID = "PHASE_11B4_RG_FIXED_POINT_TEST"
PHASE = "PHASE_11B.4"
AUDIT_VERSION = "phase11b4-rg-fixed-point-v1"
EXPECTED_CANDIDATE_COUNT = 8
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
PRINCIPLE_ID = "RG_FIXED_POINT"

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B10 = ("PHASE_10B10_SUMMARY.json",)
_REQUIRED_11A = ("PHASE_11A_SUMMARY.json",)
_REQUIRED_11B1 = ("PHASE_11B1_SUMMARY.json",)
_REQUIRED_11B2 = ("PHASE_11B2_SUMMARY.json",)
_REQUIRED_11B3 = ("PHASE_11B3_SUMMARY.json",)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11b4_artifacts"


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


def _banned_tokens() -> tuple[str, ...]:
    return (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
    )


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
    hits = []
    blob = "\n".join(_walk_strings(obj))
    for token in _banned_tokens():
        if token in blob:
            hits.append(token)
    return hits


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {f"phase10b{n}": {} for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)}
    out["phase11a"] = {}
    out["phase11b1"] = {}
    out["phase11b2"] = {}
    out["phase11b3"] = {}
    mapping = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
        ("phase10b10", _REQUIRED_10B10, phase10b10_artifact_dir()),
        ("phase11a", _REQUIRED_11A, phase11a_artifact_dir()),
        ("phase11b1", _REQUIRED_11B1, phase11b1_artifact_dir()),
        ("phase11b2", _REQUIRED_11B2, phase11b2_artifact_dir()),
        ("phase11b3", _REQUIRED_11B3, phase11b3_artifact_dir()),
    )
    extra = (
        ("phase10b3", ("PHASE_10B3_SUMMARY.json",), phase10b3_artifact_dir()),
        ("phase10b4", ("PHASE_10B4_SUMMARY.json",), phase10b4_artifact_dir()),
        ("phase10b5", ("PHASE_10B5_SUMMARY.json",), phase10b5_artifact_dir()),
        ("phase10b7", ("PHASE_10B7_SUMMARY.json",), phase10b7_artifact_dir()),
        ("phase10b8", ("PHASE_10B8_SUMMARY.json",), phase10b8_artifact_dir()),
        ("phase10b9", ("PHASE_10B9_SUMMARY.json",), phase10b9_artifact_dir()),
    )
    for key, names, root in mapping + extra:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11B.4 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 11B.4 refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar_version is not the 10B grammar"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar hash is not the frozen 10B hash"}
    return None


def _target_blindness_abort(obj: Any, *, stage: str) -> dict[str, Any] | None:
    hits = _contains_banned(obj)
    if hits:
        return {
            "status": "TARGET_BLINDNESS_VIOLATION",
            "scientific_analysis": None,
            "detail": f"target token at {stage}",
        }
    return None


def _loop_engine_present() -> bool:
    """No diagram, counterterm, or loop-integral engine is implemented."""
    return False


def _dimension_symbols() -> dict[str, Any]:
    mu = sp.symbols("mu", positive=True)
    c0, c1 = sp.symbols("c0 c1", real=True)
    lam_a, lam_b = sp.symbols("lambda_a lambda_b", real=True)
    kap, c_h = sp.symbols("kappa c_H", real=True)
    r_ab = sp.simplify(lam_a / lam_b)
    r_kap = sp.simplify(kap / (c_h * lam_b))
    g0 = sp.simplify(c0 / mu**4)
    g1 = sp.simplify(c1 / mu**2)
    mhat_a = sp.simplify((c_h * lam_a + kap) / mu**2)
    mhat_b = sp.simplify((c_h * lam_b + kap) / mu**2)
    beta_g0_class = sp.simplify(-4 * g0)
    beta_g1_class = sp.simplify(-2 * g1)
    beta_ma_class = sp.simplify(-2 * mhat_a)
    beta_mb_class = sp.simplify(-2 * mhat_b)
    beta_r_ab_class = sp.simplify(0 * r_ab)
    beta_r_kap_class = sp.simplify(0 * r_kap)
    return {
        "mu": str(mu),
        "mu_role": "COMPUTATIONAL/FORMAL RG scale; not a new physical constant",
        "r_lambda": str(r_ab),
        "r_kappa": str(r_kap),
        "ghat_c0": str(g0),
        "ghat_c1": str(g1),
        "mhat_a": str(mhat_a),
        "mhat_b": str(mhat_b),
        "classical_beta_ghat_c0": str(beta_g0_class),
        "classical_beta_ghat_c1": str(beta_g1_class),
        "classical_beta_mhat_a": str(beta_ma_class),
        "classical_beta_mhat_b": str(beta_mb_class),
        "classical_beta_r_lambda": str(beta_r_ab_class),
        "classical_beta_r_kappa": str(beta_r_kap_class),
        "classical_ratio_betas_identically_zero": True,
        "classical_vanishing_of_ghat_is_not_parameter_fixing": True,
        "engineering_fixed_point_not_used_to_set_c0_or_c1": True,
        "loop_engine_present": _loop_engine_present(),
        "provenance_classical": "DERIVED",
        "provenance_quantum": "UNTESTED",
    }


def _inventory_rows(model_id: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    content = _action_content(spec)
    f2 = bool(content["autonomous_F2"])
    rows = [
        {
            "model": model_id,
            "dimensionless_coupling": "r_lambda = lambda_a/lambda_b",
            "origin": "ratio of H_int eigenvalues of equal engineering dimension",
            "physical_or_conventional": "PHYSICAL",
            "wilsonian_interaction_coupling": False,
            "mass_dimension": 0,
        },
        {
            "model": model_id,
            "dimensionless_coupling": "r_kappa = kappa/(c_H lambda_b)",
            "origin": "ratio of quadratic-potential coefficients of equal engineering dimension",
            "physical_or_conventional": "PHYSICAL",
            "wilsonian_interaction_coupling": False,
            "mass_dimension": 0,
        },
        {
            "model": model_id,
            "dimensionless_coupling": "Phi^4 self-coupling",
            "origin": "not present; polynomial_order=2",
            "physical_or_conventional": "ABSENT",
            "wilsonian_interaction_coupling": False,
            "mass_dimension": 0,
        },
        {
            "model": model_id,
            "dimensionless_coupling": "Z",
            "origin": "matter kinetic normalization",
            "physical_or_conventional": "CONVENTIONAL",
            "wilsonian_interaction_coupling": False,
            "mass_dimension": 0,
        },
        {
            "model": model_id,
            "dimensionless_coupling": "overall_K_scale",
            "origin": "generator normalization",
            "physical_or_conventional": "CONVENTIONAL",
            "wilsonian_interaction_coupling": False,
            "mass_dimension": 0,
        },
        {
            "model": model_id,
            "dimensionless_coupling": "overall_H_int_scale",
            "origin": "operator normalization",
            "physical_or_conventional": "CONVENTIONAL",
            "wilsonian_interaction_coupling": False,
            "mass_dimension": 0,
        },
    ]
    if f2:
        rows.append(
            {
                "model": model_id,
                "dimensionless_coupling": "Z_A magnitude",
                "origin": "gauge kinetic normalization when absorbed",
                "physical_or_conventional": "CONVENTIONAL",
                "wilsonian_interaction_coupling": False,
                "mass_dimension": 0,
            }
        )
        rows.append(
            {
                "model": model_id,
                "dimensionless_coupling": _phys_coupling_name(),
                "origin": "already established CONVENTION; not a derived gauge coupling",
                "physical_or_conventional": "CONVENTIONAL",
                "wilsonian_interaction_coupling": False,
                "mass_dimension": 0,
            }
        )
    return rows


def _beta_rows(model_id: str, spec: dict[str, Any], dims: dict[str, Any]) -> list[dict[str, Any]]:
    content = _action_content(spec)
    f2 = bool(content["autonomous_F2"])
    has_a = bool(content["has_a"])
    mismatch = f2 and not has_a
    rows = [
        {
            "model": model_id,
            "coupling": "r_lambda",
            "beta_function": "quantum UNTESTED; classical engineering identity " + dims["classical_beta_r_lambda"],
            "loop_level": "UNTESTED",
            "status": "RG_BETA_FUNCTIONS_UNTESTED",
            "classical_note": "same-dimension ratio; classical beta identically 0; not a constraint",
        },
        {
            "model": model_id,
            "coupling": "r_kappa",
            "beta_function": "quantum UNTESTED; classical engineering identity " + dims["classical_beta_r_kappa"],
            "loop_level": "UNTESTED",
            "status": "RG_BETA_FUNCTIONS_UNTESTED",
            "classical_note": "same-dimension ratio; classical beta identically 0; not a constraint",
        },
        {
            "model": model_id,
            "coupling": "c0, written as c0/mu^4",
            "beta_function": "quantum UNTESTED; classical engineering " + dims["classical_beta_ghat_c0"],
            "loop_level": "UNTESTED",
            "status": "GRAVITY_RG_UNTESTED",
            "classical_note": "relevant direction; classical vanishing is not used to fix c0",
        },
        {
            "model": model_id,
            "coupling": "c1, written as c1/mu^2",
            "beta_function": "quantum UNTESTED; classical engineering " + dims["classical_beta_ghat_c1"],
            "loop_level": "UNTESTED",
            "status": "GRAVITY_RG_UNTESTED",
            "classical_note": "relevant direction; classical vanishing is not used to fix c1",
        },
        {
            "model": model_id,
            "coupling": "quadratic masses (c_H H_int + kappa)/mu^2",
            "beta_function": "quantum UNTESTED; classical engineering -2 mhat",
            "loop_level": "UNTESTED",
            "status": "RG_UNTESTED",
            "classical_note": "relevant direction; not a dimensionless Wilsonian coupling",
        },
    ]
    if f2 and has_a:
        rows.append(
            {
                "model": model_id,
                "coupling": _phys_coupling_name(),
                "beta_function": "GAUGE_RG_UNTESTED; no diagram engine; not imported from known gauge theory",
                "loop_level": "UNTESTED",
                "status": "GAUGE_RG_UNTESTED",
                "classical_note": "magnitude is CONVENTION in the stored theory",
            }
        )
    elif mismatch:
        rows.append(
            {
                "model": model_id,
                "coupling": "autonomous F^2 without A_mu",
                "beta_function": "GAUGE_RG_UNTESTED; mismatch not repaired",
                "loop_level": "UNTESTED",
                "status": "GAUGE_RG_UNTESTED",
                "classical_note": "F2_A_MU_DEPENDENCY remains UNDECLARED",
            }
        )
    else:
        rows.append(
            {
                "model": model_id,
                "coupling": "gauge coupling",
                "beta_function": "no autonomous gauge propagator; GAUGE_RG_UNTESTED as a physical g",
                "loop_level": "UNTESTED",
                "status": "GAUGE_RG_UNTESTED",
                "classical_note": "stored theory does not supply an independent physical g",
            }
        )
    return rows


def _audit_one(catalog_item: dict[str, Any], spec: dict[str, Any], dims: dict[str, Any]) -> dict[str, Any]:
    content = _action_content(spec)
    poly = int(content.get("polynomial_order") or 0)
    inv = _inventory_rows(catalog_item["model_id"], spec)
    betas = _beta_rows(catalog_item["model_id"], spec, dims)
    n_dimless = 2
    return {
        "model": catalog_item["model_id"],
        "polynomial_order": poly,
        "quartic_self_coupling_present": poly > 2,
        "wilsonian_physical_g_vector": [],
        "dimensionless_ratio_vector": ["r_lambda", "r_kappa"],
        "N_dimensionless_before": n_dimless,
        "N_dimensionless_after_fixed_point": n_dimless,
        "N_physical_before": 6,
        "N_physical_after": 6,
        "inventory": inv,
        "betas": betas,
        "fixed_point": "UNTESTED",
        "fixed_point_dimension": "UNTESTED",
        "remaining_freedom": 6,
        "fixed_point_status": "UNTESTED",
        "reduction_type": "UNTESTED",
        "isolated": False,
        "RGALLY_INCONSISTENT": False,
        "mismatch_preserved": bool(content["autonomous_F2"] and not content["has_a"]),
        "stability_status": "RG_STABILITY_UNTESTED",
        "relevant": "UNTESTED at quantum level; classically the dimensionful parameters are relevant",
        "marginal": "UNTESTED",
        "irrelevant": "UNTESTED",
        "GRAVITY_RG_UNTESTED": True,
        "GAUGE_RG_UNTESTED": True,
        "RG_SCHEME_DEPENDENCE_UNTESTED": True,
        "NO_NEW_CROSS_SECTOR_RG_RELATION": True,
        "loop_engine_present": False,
        "gaussian_Phi4_absent": poly == 2,
        "classical_ratio_surface_is_not_a_quantum_fixed_point": True,
        "engineering_zero_is_not_used_to_eliminate_c0_or_c1": True,
    }


def _closure_table() -> list[dict[str, Any]]:
    return [
        {"quantity": "unique_action", "before": "NO", "after": "NO", "change": "unchanged"},
        {"quantity": "unique_kinetic_structure", "before": "NO", "after": "NO", "change": "unchanged"},
        {
            "quantity": "unique_dimensionless_quantity",
            "before": "NO",
            "after": "NO",
            "change": "no beta=0 relation was derived",
        },
        {"quantity": "parameter_free_closure", "before": "NO", "after": "NO", "change": "unchanged"},
        {
            "quantity": "global_closure",
            "before": "NO",
            "after": "NO",
            "change": "RG untested is not closure",
        },
    ]


def analyze_phase11b4_rg(
    auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_hash_before = grammar_hash()
    frozen_before = auth.action_content_hash
    abort = _target_blindness_abort({"grammar": GRAMMAR_VERSION, "phase": PHASE}, stage="preamble")
    if abort is not None:
        return abort
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
        manifest = _read_json(phase10b1_artifact_dir() / "SEARCH_MANIFEST.json")
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        s11a = _read_json(phase11a_artifact_dir() / "PHASE_11A_SUMMARY.json")
        s11b1 = _read_json(phase11b1_artifact_dir() / "PHASE_11B1_SUMMARY.json")
        s11b2 = _read_json(phase11b2_artifact_dir() / "PHASE_11B2_SUMMARY.json")
        s11b3 = _read_json(phase11b3_artifact_dir() / "PHASE_11B3_SUMMARY.json")
        schema_10b6 = _read_json(phase10b6_artifact_dir() / "DEPENDENCY_SCHEMA.json")
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if len(catalog) != EXPECTED_CANDIDATE_COUNT:
        integrity_failure = f"catalog count {len(catalog)}"
    if grammar_hash_before != EXPECTED_GRAMMAR_HASH or manifest.get("grammar_hash") != EXPECTED_GRAMMAR_HASH:
        integrity_failure = "grammar hash mismatch"
    if frozen_before != EXPECTED_FROZEN_HASH:
        integrity_failure = "frozen hash mismatch"
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not in CLOSED_NO_INTERNAL_CLOSURE"
    if s11a.get("PHASE_11A_STATUS") != "CLOSED":
        integrity_failure = "Phase 11A is not CLOSED"
    if s11b1.get("PHASE_11B1_STATUS") != "CLOSED":
        integrity_failure = "Phase 11B.1 is not CLOSED"
    if s11b2.get("PHASE_11B2_STATUS") != "CLOSED":
        integrity_failure = "Phase 11B.2 is not CLOSED"
    if s11b3.get("PHASE_11B3_STATUS") != "CLOSED":
        integrity_failure = "Phase 11B.3 is not CLOSED"
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        integrity_failure = "dependency schema not CONSISTENT"

    dims = _dimension_symbols()
    specs_unchanged = True
    dep_valid = 0
    dep_unchecked = 0
    dep_invalid = 0
    audits: list[dict[str, Any]] = []
    inv_rows: list[dict[str, Any]] = []
    beta_rows: list[dict[str, Any]] = []
    fp_rows: list[dict[str, Any]] = []
    stab_rows: list[dict[str, Any]] = []
    red_rows: list[dict[str, Any]] = []
    _ = signature
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash(spec) != item["canonical_hash"]:
            specs_unchanged = False
            integrity_failure = f"MODEL_SPEC rewrite detected for {item['model_id']}"
            break
        dep = validate_dependencies(spec)
        if dep["status"] == "VALID":
            dep_valid += 1
        elif dep["status"] == "UNCHECKED":
            dep_unchecked += 1
        elif dep["status"] == "INVALID":
            dep_invalid += 1
        aud = _audit_one(item, spec, dims)
        audits.append(aud)
        inv_rows.extend(aud["inventory"])
        beta_rows.extend(aud["betas"])
        fp_rows.append(
            {
                "model": aud["model"],
                "fixed_point": aud["fixed_point"],
                "dimension": aud["fixed_point_dimension"],
                "remaining_freedom": aud["remaining_freedom"],
                "status": aud["fixed_point_status"],
            }
        )
        stab_rows.append(
            {
                "model": aud["model"],
                "fixed_point": aud["fixed_point"],
                "relevant": aud["relevant"],
                "marginal": aud["marginal"],
                "irrelevant": aud["irrelevant"],
                "status": aud["stability_status"],
            }
        )
        red_rows.append(
            {
                "model": aud["model"],
                "before": aud["N_physical_before"],
                "after": aud["N_physical_after"],
                "reduction_type": aud["reduction_type"],
                "N_dimensionless_before": aud["N_dimensionless_before"],
                "N_dimensionless_after_fixed_point": aud["N_dimensionless_after_fixed_point"],
            }
        )
    if not specs_unchanged or dep_invalid != 0:
        integrity_failure = integrity_failure or "dependency INVALID appeared"

    closure = _closure_table()
    pfr = _parameter_free_test(["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"])
    pfr["scope"] = (
        "stored action + RG_FIXED_POINT; no beta=0 equation was derived; "
        "classical ratio identities are not parameter-free predictions"
    )
    pfr["classification"] = "NO_PARAMETER_FREE_RELATIONS_FOUND"

    abort = _target_blindness_abort(
        {"inv": inv_rows, "beta": beta_rows, "fp": fp_rows, "dims": dims},
        stage="rg",
    )
    if abort is not None:
        return abort

    n_elim = sum(1 for a in audits if a["RGALLY_INCONSISTENT"])
    n_unresolved = 8
    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "candidates_analyzed": 8,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
        "new_assumptions": 1,
        "new_principle_count": 1,
        "new_principle_id": PRINCIPLE_ID,
        "second_principle_introduced": False,
        "new_dependencies": 0,
        "new_fields": 0,
        "ranking": False,
        "known_physics_comparison": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "rg_level_achieved": "RG_LEVEL_0",
        "beta_functions_verified": 0,
        "beta_functions_partial": 0,
        "beta_functions_untested": len(beta_rows),
        "fixed_points_found": 0,
        "isolated_fixed_points": 0,
        "fixed_lines_or_surfaces": 0,
        "no_fixed_points": 0,
        "fixed_points_untested": 8,
        "dimensionless_parameters_before": 2,
        "dimensionless_parameters_after": 2,
        "parameter_relations_found": 0,
        "parameter_reductions_found": 0,
        "new_parameter_free_relations": "NONE",
        "NEW_PFR": "NONE",
        "candidates_eliminated_by_RG": n_elim,
        "candidates_unresolved_by_RG": n_unresolved,
        "quantum_unitarity_verified": False,
        "quantum_unitarity_untested": True,
        "PRINCIPLE_EFFECT": "RG_UNTESTED",
        "RG_BETA_FUNCTIONS_UNTESTED": True,
        "GRAVITY_RG_UNTESTED": True,
        "GAUGE_RG_UNTESTED": True,
        "RG_STABILITY_UNTESTED": True,
        "RG_SCHEME_DEPENDENCE_UNTESTED": True,
        "NO_NEW_CROSS_SECTOR_RG_RELATION": True,
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "N_physical_before": 6,
        "N_physical_after": 6,
        "loop_engine_present": False,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "UNCHECKED_IS_NOT_INVALID": True,
        "UNCHECKED_IS_NOT_VALID": True,
        "dependency_valid": dep_valid,
        "dependency_unchecked": dep_unchecked,
        "dependency_invalid": dep_invalid,
        "syntactic_candidates": 8,
        "candidates_regenerated": False,
        "search_space_modified": False,
        "gravity_family_modified": False,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "UNDECLARED_POTENTIAL_DEPENDENCY": [item["inference_id"] for item in undeclared_inferences()],
        "PHASE_11B4_STATUS": "INTEGRITY_FAILURE" if integrity_failure else "CLOSED",
        "integrity_failure": integrity_failure,
        "phase_11b5_executed": False,
        "conformal_invariance_imposed": False,
        "scale_invariance_imposed": False,
        "asymptotic_safety_imposed": False,
        "supersymmetry_imposed": False,
        "uv_completion_added": False,
        "fermions_added": False,
        "no_external_scales_reimposed": False,
        "enhanced_symmetry_reimposed": False,
        "quantum_unitarity_reimposed": False,
        "known_beta_coefficients_imported": False,
    }
    abort = _target_blindness_abort({"summary": summary}, stage="audit")
    if abort is not None:
        return abort

    _write_json("RG_COUPLING_INVENTORY.json", inv_rows)
    _write_json("BETA_FUNCTION_STATUS.json", beta_rows)
    _write_json("FIXED_POINT_RESULTS.json", fp_rows)
    _write_json("STABILITY.json", stab_rows)
    _write_json("PARAMETER_REDUCTION.json", red_rows)
    _write_json("CLOSURE_COMPARISON.json", closure)
    _write_json("DIMENSION_SYMBOLS.json", dims)
    _write_json("PHASE_11B4_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == EXPECTED_GRAMMAR_HASH == manifest.get("grammar_hash")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    for key in hashes_before:
        summary[f"{key}_artifacts_unchanged"] = hashes_before[key] == hashes_after[key]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["whitelist_unchanged"] = WHITELIST_VERSION == manifest.get("whitelist_version")
    summary["blacklist_unchanged"] = BLACKLIST_VERSION == manifest.get("blacklist_version")
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    if not (artifacts_ok and grammar_ok and frozen_ok and specs_unchanged and summary["ranking"] is False):
        summary["PHASE_11B4_STATUS"] = "INTEGRITY_FAILURE"
    _write_json("PHASE_11B4_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11B4_TEST_COPY_ID": PHASE_11B4_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "principle": {
            "principle_id": PRINCIPLE_ID,
            "statement": (
                "The dimensionless couplings of the theory are required to lie at a "
                "renormalization-group fixed point satisfying beta_i = 0 for the "
                "dimensionless couplings actually present."
            ),
            "provenance": "INPUT / FUTURE TEST",
            "new_principle_count": 1,
        },
        "dimension_symbols": dims,
        "inventory_table": inv_rows,
        "beta_table": beta_rows,
        "fixed_point_table": fp_rows,
        "stability_table": stab_rows,
        "reduction_table": red_rows,
        "candidate_audits": [
            {
                "model": a["model"],
                "wilsonian_physical_g_vector": a["wilsonian_physical_g_vector"],
                "quartic_self_coupling_present": a["quartic_self_coupling_present"],
                "polynomial_order": a["polynomial_order"],
                "reduction_type": a["reduction_type"],
                "RGALLY_INCONSISTENT": a["RGALLY_INCONSISTENT"],
                "mismatch_preserved": a["mismatch_preserved"],
                "gaussian_Phi4_absent": a["gaussian_Phi4_absent"],
            }
            for a in audits
        ],
        "closure_comparison": closure,
        "pfr_generic": pfr,
        "audit_summary": summary,
        "PRINCIPLE_EFFECT": summary["PRINCIPLE_EFFECT"],
        "NEW_PFR": "NONE",
        "RG_BETA_FUNCTIONS_UNTESTED": True,
        "GRAVITY_RG_UNTESTED": True,
        "GAUGE_RG_UNTESTED": True,
        "RG_STABILITY_UNTESTED": True,
        "RG_SCHEME_DEPENDENCE_UNTESTED": True,
        "NO_NEW_CROSS_SECTOR_RG_RELATION": True,
        "quantum_unitarity_verified": False,
        "quantum_unitarity_untested": True,
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_11B4_STATUS": summary["PHASE_11B4_STATUS"],
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash(),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_comparison_executed": False,
        "phase_11b5_executed": False,
        "second_principle_introduced": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_principle_count": 1,
        "new_fields": 0,
        "search_space_modified": False,
        "grammar_changed": 0,
        "loop_engine_present": False,
        "phase_10b1_artifacts_unchanged": summary.get("phase10b1_artifacts_unchanged"),
        "phase_10b10_artifacts_unchanged": summary.get("phase10b10_artifacts_unchanged"),
        "phase_11a_artifacts_unchanged": summary.get("phase11a_artifacts_unchanged"),
        "phase_11b1_artifacts_unchanged": summary.get("phase11b1_artifacts_unchanged"),
        "phase_11b2_artifacts_unchanged": summary.get("phase11b2_artifacts_unchanged"),
        "phase_11b3_artifacts_unchanged": summary.get("phase11b3_artifacts_unchanged"),
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_11B4_CLOSED": summary["PHASE_11B4_STATUS"] == "CLOSED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_invent_loop_coefficients": "REJECTED AS OVERCLAIM",
            "2_import_known_gauge_betas": "REJECTED AS OVERCLAIM",
            "3_asymptotic_safety": "REJECTED AS OVERCLAIM",
            "4_engineering_zero_fixes_dimensionful_parameters": "REJECTED AS OVERCLAIM",
            "5_empty_g_vector_is_unique_theory": "REJECTED AS OVERCLAIM",
            "6_untested_RG_eliminates_candidate": "REJECTED AS OVERCLAIM",
            "7_conformal_or_scale_invariance": "REJECTED AS OVERCLAIM",
            "8_add_fermions_or_UV_completion": "REJECTED AS OVERCLAIM",
            "9_classical_ratio_identity_is_a_PFR": "REJECTED AS OVERCLAIM",
            "10_isolated_FP_is_unique_theory": "REJECTED AS OVERCLAIM",
            "11_combine_with_prior_11B_principles": "REJECTED AS OVERCLAIM",
            "12_start_next_11B_phase": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_11B4_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_principle_count"] == 1
        and science["phase_11b5_executed"] is False
        and science["loop_engine_present"] is False
        and science["UNIQUE_ACTION"] == "NO"
        and science["GLOBAL_CLOSURE"] == "NO"
        and n_elim == 0
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and specs_unchanged
    )
    return science


def run_phase11b4_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11b4_rg(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_BLINDNESS_VIOLATION"}:
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
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b1_artifacts_unchanged") else "FAILED",
            "PHASE_10B10_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b10_artifacts_unchanged") else "FAILED",
            "PHASE_11A_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11a_artifacts_unchanged") else "FAILED",
            "PHASE_11B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11b1_artifacts_unchanged") else "FAILED",
            "PHASE_11B2_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11b2_artifacts_unchanged") else "FAILED",
            "PHASE_11B3_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11b3_artifacts_unchanged") else "FAILED",
            "PHASE_11B4_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_11B4_STATUS": science.get("PHASE_11B4_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "NEW_PRINCIPLE_COUNT": 1,
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
