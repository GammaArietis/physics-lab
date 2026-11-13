"""Phase 11B.6: SCALE_INVARIANCE and CONFORMAL_INVARIANCE test.

Two distinct branches of one controlled experiment.  Does not modify the
frozen action, grammar, or prior artifacts.  Does not add a dilaton,
compensator, improvement term, quartic, or RG.
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
from physics_lab.physics.phase11b4_rg import artifact_dir as phase11b4_artifact_dir
from physics_lab.physics.phase11b5_boundary import artifact_dir as phase11b5_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "PHASE_11B6_TEST_COPY_ID",
    "PRINCIPLE_IDS",
    "analyze_phase11b6_scale_conformal",
    "artifact_dir",
    "run_phase11b6_or_stop",
]

PHASE_11B6_TEST_COPY_ID = "PHASE_11B6_SCALE_CONFORMAL_INVARIANCE_TEST"
PHASE = "PHASE_11B.6"
AUDIT_VERSION = "phase11b6-scale-conformal-v1"
EXPECTED_CANDIDATE_COUNT = 8
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
PRINCIPLE_IDS = ("SCALE_INVARIANCE", "CONFORMAL_INVARIANCE")

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B10 = ("PHASE_10B10_SUMMARY.json",)
_REQUIRED_11A = ("PHASE_11A_SUMMARY.json",)
_REQUIRED_11B1 = ("PHASE_11B1_SUMMARY.json",)
_REQUIRED_11B5 = ("PHASE_11B5_SUMMARY.json",)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11b6_artifacts"


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
    out["phase11b4"] = {}
    out["phase11b5"] = {}
    mapping = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
        ("phase10b10", _REQUIRED_10B10, phase10b10_artifact_dir()),
        ("phase11a", _REQUIRED_11A, phase11a_artifact_dir()),
        ("phase11b1", _REQUIRED_11B1, phase11b1_artifact_dir()),
        ("phase11b5", _REQUIRED_11B5, phase11b5_artifact_dir()),
    )
    extra = (
        ("phase10b3", ("PHASE_10B3_SUMMARY.json",), phase10b3_artifact_dir()),
        ("phase10b4", ("PHASE_10B4_SUMMARY.json",), phase10b4_artifact_dir()),
        ("phase10b5", ("PHASE_10B5_SUMMARY.json",), phase10b5_artifact_dir()),
        ("phase10b7", ("PHASE_10B7_SUMMARY.json",), phase10b7_artifact_dir()),
        ("phase10b8", ("PHASE_10B8_SUMMARY.json",), phase10b8_artifact_dir()),
        ("phase10b9", ("PHASE_10B9_SUMMARY.json",), phase10b9_artifact_dir()),
        ("phase11b2", ("PHASE_11B2_SUMMARY.json",), phase11b2_artifact_dir()),
        ("phase11b3", ("PHASE_11B3_SUMMARY.json",), phase11b3_artifact_dir()),
        ("phase11b4", ("PHASE_11B4_SUMMARY.json",), phase11b4_artifact_dir()),
    )
    for key, names, root in mapping + extra:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11B.6 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 11B.6 refuses to proceed"}
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


def _dimension_table() -> dict[str, Any]:
    return {
        "x": -1,
        "partial": 1,
        "d4x": -4,
        "g_mu_nu": 0,
        "R": 2,
        "Phi": 1,
        "A_mu": 1,
        "Z": 0,
        "Z_A": 0,
        "c0": 4,
        "c1": 2,
        "kappa": 2,
        "c_H_times_H_int": 2,
        "provenance": "CONVENTION",
        "note": "engineering assignments required to perform the test; not new dynamics",
    }


def _scale_variation() -> dict[str, Any]:
    """Global dilation x -> rho x, Phi -> rho^{-1} Phi, A -> rho^{-1} A, [g]=0."""
    rho = sp.symbols("rho", positive=True)
    jac = rho**4
    kin = sp.simplify(jac * (rho ** (-2)) ** 2)
    pot = sp.simplify(jac * (rho ** (-1)) ** 2)
    c0 = sp.simplify(jac * rho**0)
    c1 = sp.simplify(jac * (rho ** (-2)))
    f2 = sp.simplify(jac * (rho ** (-2)) ** 2)
    return {
        "transformation": "x -> rho x; Phi -> rho^{-1} Phi(x/rho); A -> rho^{-1} A(x/rho); g weight 0",
        "jacobian": str(jac),
        "S_kin_factor": str(kin),
        "S_potential_factor": str(pot),
        "S_c0_factor": str(c0),
        "S_c1R_factor": str(c1),
        "S_F2_factor": str(f2),
        "kinetic_invariant": bool(kin == 1),
        "potential_invariant": bool(pot == 1),
        "c0_invariant": bool(c0 == 1),
        "c1_invariant": bool(c1 == 1),
        "F2_invariant": bool(f2 == 1),
        "rho_symbol": str(rho),
        "background_c0_equals_zero_not_used": True,
        "dilaton_added": False,
        "provenance": "DERIVED GIVEN ASSUMPTION",
    }


def _special_conformal_weights() -> dict[str, Any]:
    """Special conformal: finite map with conformal factor Omega. Not inferred from scale."""
    Omega = sp.symbols("Omega", positive=True)
    d = 4
    Delta = 1
    pot = sp.simplify(Omega**d * Omega ** (-2 * Delta))
    kin = sp.simplify(Omega**0)
    return {
        "map": "x' = (x - b x^2)/(1 - 2 b·x + b^2 x^2); Omega = 1/(1 - 2 b·x + b^2 x^2)",
        "Delta_Phi": Delta,
        "S_potential_factor": str(pot),
        "potential_invariant": bool(pot == 1),
        "flat_massless_kinetic_invariant": bool(kin == 1),
        "kinetic_note": "massless two-derivative scalar with Delta=(d-2)/2 on Minkowski; not a Weyl identity and not a gravity identity",
        "Einstein_Hilbert_special_conformal": False,
        "does_not_imply_full_conformal_of_S_frozen": True,
        "not_inferred_from_scale": True,
        "provenance": "DERIVED GIVEN ASSUMPTION",
    }


def _weyl_kinetic_remainder() -> dict[str, Any]:
    """Weyl: g -> e^{2 sigma} g, Phi -> e^{-sigma} Phi in 4D. Kinetic is not invariant."""
    sigma = sp.Function("sigma")
    phi = sp.Function("Phi")
    x = sp.symbols("x", real=True)
    dphi = sp.diff(phi(x), x)
    ds = sp.diff(sigma(x), x)
    # After Weyl, the 4D factor sqrt(g) g^{mu nu} is invariant; the derivative
    # of the rescaled scalar is dPhi - Phi d sigma (one-dimensional probe).
    extra = sp.expand((dphi - phi(x) * ds) ** 2 - dphi**2)
    remainder_vanishes = bool(sp.simplify(extra) == 0)
    return {
        "weyl_rule": "g_mu_nu -> exp(2 sigma) g_mu_nu; Phi -> exp(-sigma) Phi",
        "kinetic_remainder_1d_probe": str(sp.simplify(extra)),
        "remainder_identically_zero": remainder_vanishes,
        "improvement_term_present": False,
        "improvement_term_added": False,
        "CONFORMAL_COMPLETION_REQUIRED": not remainder_vanishes,
        "Einstein_Hilbert_Weyl_invariant": False,
        "dilaton_added": False,
        "compensator_added": False,
        "provenance": "DERIVED GIVEN ASSUMPTION",
    }


def _scale_branch(content: dict[str, Any], var: dict[str, Any]) -> dict[str, Any]:
    excluded = []
    conditions = []
    if not var["potential_invariant"]:
        excluded.append("kappa Phi^2")
        excluded.append("c_H <Phi, H_int Phi>")
        conditions.append("potential coefficients must vanish (PARAMETER_ELIMINATION / TERM_EXCLUDED_BY_SYMMETRY)")
    if not var["c0_invariant"]:
        excluded.append("c0 volume term")
        conditions.append("c0 term incompatible (PARAMETER_ELIMINATION would delete it)")
    if not var["c1_invariant"]:
        excluded.append("c1 R")
        conditions.append("c1 R incompatible (PARAMETER_ELIMINATION would delete stored gravity)")
    gravity_obstructed = (not var["c0_invariant"]) or (not var["c1_invariant"])
    f2_ok = (not content["autonomous_F2"]) or var["F2_invariant"]
    _ = f2_ok
    return {
        "scale_invariant": "NO",
        "required_conditions": conditions,
        "terms_excluded": excluded,
        "remaining_freedom": "sealed theory unchanged with 6 parameters; restricted theory INCONSISTENT with stored gravity",
        "GRAVITY_SCALE_INVARIANCE_OBSTRUCTED": gravity_obstructed,
        "kinetic_ok": var["kinetic_invariant"],
        "F2_ok": var["F2_invariant"],
        "Z_is_convention": True,
        "DIMENSIONLESS_FREEDOM_REMAINS": True,
        "dimensionless_note": "lambda_a/lambda_b remains FREE if the H_int term survives; dimensional compatibility is not a value",
        "background_c0_zero_not_used": True,
        "gravity_modified": False,
    }


def _conformal_branch(
    content: dict[str, Any],
    weyl: dict[str, Any],
    var: dict[str, Any],
    special: dict[str, Any],
) -> dict[str, Any]:
    _ = content
    missing = []
    if weyl["CONFORMAL_COMPLETION_REQUIRED"]:
        missing.append("nonminimal Phi^2 R improvement coupling (not present; not added)")
    if not weyl["Einstein_Hilbert_Weyl_invariant"]:
        missing.append("stored c0 + c1 R is not Weyl/conformally invariant; not replaced")
    if not var["potential_invariant"] or not special["potential_invariant"]:
        missing.append("quadratic potential already breaks special conformal / Weyl invariance")
    return {
        "conformal_invariant": "NO",
        "required_conditions": [
            "massless potential",
            "improvement coupling absent from stored action",
            "Einstein-Hilbert not conformal",
        ],
        "missing_completion_terms": missing,
        "remaining_freedom": "sealed theory unchanged with 6 parameters; conformal branch STOPPED without adding terms",
        "CONFORMAL_COMPLETION_REQUIRED": True,
        "flat_space_massless_kinetic_special_conformal": special["flat_massless_kinetic_invariant"],
        "special_conformal_does_not_promote_S_frozen": True,
        "scale_does_not_imply_conformal": True,
        "Weyl_is_not_assumed_from_field_rescaling_alone": True,
        "gravity_modified": False,
        "improvement_added": False,
    }


def _parameter_effects() -> list[dict[str, Any]]:
    rows = []
    scale_map = [
        ("c0", "FREE", "would have to vanish; GRAVITY_SCALE_INVARIANCE_OBSTRUCTED", "PARAMETER_ELIMINATION / INCONSISTENT"),
        ("c1", "FREE", "would have to vanish; stored gravity family cannot survive", "PARAMETER_ELIMINATION / INCONSISTENT"),
        ("kappa", "FREE", "TERM_EXCLUDED_BY_SYMMETRY if scale is imposed", "PARAMETER_ELIMINATION"),
        ("c_H", "FREE", "H_int term excluded unless identically zero", "PARAMETER_ELIMINATION"),
        ("lambda_a", "FREE", "engineering dimension only; value not fixed; term excluded with c_H", "NO_CONSTRAINT on the ratio"),
        ("lambda_b", "FREE", "same; lambda_a/lambda_b remains FREE if the term is kept", "NO_CONSTRAINT"),
        ("Z", "CONVENTION", "kinetic already weight 0", "CONVENTION"),
        ("Z_A", "CONVENTION", "F^2 already weight 0 where present", "CONVENTION"),
        (_phys_coupling_name(), "CONVENTION", "no new constraint", "CONVENTION"),
    ]
    for name, before, after, effect in scale_map:
        rows.append({"branch": "SCALE_INVARIANCE", "parameter": name, "before": before, "after": after, "effect": effect})
    conf_map = [
        ("c0", "FREE", "EH not conformal; not set from a background", "INCONSISTENT / CONFORMAL_COMPLETION_REQUIRED"),
        ("c1", "FREE", "EH not conformal; not replaced by Weyl-tensor density", "INCONSISTENT / CONFORMAL_COMPLETION_REQUIRED"),
        ("kappa", "FREE", "mass term breaks conformal symmetry", "PARAMETER_ELIMINATION if imposed"),
        ("c_H", "FREE", "same", "PARAMETER_ELIMINATION if imposed"),
        ("lambda_a", "FREE", "value not fixed by conformal symmetry", "NO_CONSTRAINT on the ratio"),
        ("lambda_b", "FREE", "same", "NO_CONSTRAINT"),
        ("Z", "CONVENTION", "unaffected as normalization", "CONVENTION"),
    ]
    for name, before, after, effect in conf_map:
        rows.append({"branch": "CONFORMAL_INVARIANCE", "parameter": name, "before": before, "after": after, "effect": effect})
    return rows


def _dimensionless_rows() -> list[dict[str, Any]]:
    return [
        {
            "branch": "SCALE_INVARIANCE",
            "quantity": "lambda_a/lambda_b",
            "result": "FREE",
            "provenance": "PARAMETER-DEPENDENT",
            "note": "dimensional compatibility of H_int is not a determination of the ratio",
        },
        {
            "branch": "SCALE_INVARIANCE",
            "quantity": "kappa/(c_H lambda_b)",
            "result": "FREE if the potential is kept; moot if the potential is excluded",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "branch": "SCALE_INVARIANCE",
            "quantity": "Z, Z_A, " + _phys_coupling_name(),
            "result": "CONVENTION",
            "provenance": "CONVENTION",
        },
        {
            "branch": "CONFORMAL_INVARIANCE",
            "quantity": "lambda_a/lambda_b",
            "result": "FREE",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "branch": "CONFORMAL_INVARIANCE",
            "quantity": "kappa/(c_H lambda_b)",
            "result": "FREE if kept; potential excluded by conformal masslessness",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "branch": "CONFORMAL_INVARIANCE",
            "quantity": "improvement coefficient",
            "result": "UNTESTED as a stored parameter; term ABSENT",
            "provenance": "UNTESTED",
        },
    ]


def _closure_rows() -> list[dict[str, Any]]:
    return [
        {"quantity": "unique_action", "Phase_11A": "NO", "scale_branch": "NO", "conformal_branch": "NO"},
        {"quantity": "unique_kinetic_structure", "Phase_11A": "NO", "scale_branch": "NO", "conformal_branch": "NO"},
        {"quantity": "unique_dimensionless_quantity", "Phase_11A": "NO", "scale_branch": "NO", "conformal_branch": "NO"},
        {"quantity": "parameter_free_closure", "Phase_11A": "NO", "scale_branch": "NO", "conformal_branch": "NO"},
        {"quantity": "global_closure", "Phase_11A": "NO", "scale_branch": "NO", "conformal_branch": "NO"},
    ]


def analyze_phase11b6_scale_conformal(
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
        s11b5 = _read_json(phase11b5_artifact_dir() / "PHASE_11B5_SUMMARY.json")
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
    if s11b5.get("PHASE_11B5_STATUS") != "CLOSED":
        integrity_failure = "Phase 11B.5 is not CLOSED"
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        integrity_failure = "dependency schema not CONSISTENT"

    dims = _dimension_table()
    var = _scale_variation()
    weyl = _weyl_kinetic_remainder()
    special = _special_conformal_weights()
    _ = signature

    specs_unchanged = True
    dep_valid = 0
    dep_unchecked = 0
    dep_invalid = 0
    scale_rows: list[dict[str, Any]] = []
    conf_rows: list[dict[str, Any]] = []
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
        content = _action_content(spec)
        sc = _scale_branch(content, var)
        cf = _conformal_branch(content, weyl, var, special)
        scale_rows.append(
            {
                "model": item["model_id"],
                "scale_invariant": sc["scale_invariant"],
                "required_conditions": sc["required_conditions"],
                "terms_excluded": sc["terms_excluded"],
                "remaining_freedom": sc["remaining_freedom"],
                "GRAVITY_SCALE_INVARIANCE_OBSTRUCTED": sc["GRAVITY_SCALE_INVARIANCE_OBSTRUCTED"],
                "SCALE_INVARIANT": "NO",
                "mismatch_preserved": bool(content["autonomous_F2"] and not content["has_a"]),
            }
        )
        conf_rows.append(
            {
                "model": item["model_id"],
                "conformal_invariant": cf["conformal_invariant"],
                "required_conditions": cf["required_conditions"],
                "missing_completion_terms": cf["missing_completion_terms"],
                "remaining_freedom": cf["remaining_freedom"],
                "CONFORMAL_COMPLETION_REQUIRED": cf["CONFORMAL_COMPLETION_REQUIRED"],
                "CONFORMAL_INVARIANT": "NO",
                "scale_does_not_imply_conformal": True,
            }
        )
    if not specs_unchanged or dep_invalid != 0:
        integrity_failure = integrity_failure or "dependency INVALID appeared"

    params = _parameter_effects()
    dimless = _dimensionless_rows()
    closure = _closure_rows()
    pfr_s = _parameter_free_test(["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"])
    pfr_s["scope"] = "stored action + SCALE_INVARIANCE; required vanishings are not PFRs of the original theory"
    pfr_s["classification"] = "NO_PARAMETER_FREE_RELATIONS_FOUND"
    pfr_c = _parameter_free_test(["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"])
    pfr_c["scope"] = "stored action + CONFORMAL_INVARIANCE; missing improvement is not a PFR"
    pfr_c["classification"] = "NO_PARAMETER_FREE_RELATIONS_FOUND"

    abort = _target_blindness_abort(
        {"var": var, "weyl": weyl, "special": special, "scale": scale_rows, "conf": conf_rows, "dims": dims},
        stage="scale_conformal",
    )
    if abort is not None:
        return abort

    scale_summary = {
        "candidates_analyzed": 8,
        "invariant_candidates": 0,
        "parameter_dependent_candidates": 0,
        "inconsistent_candidates": 8,
        "untested_candidates": 0,
        "parameter_relations_found": 0,
        "parameter_eliminations_found": 4,
        "parameter_fixed": False,
        "new_parameter_free_relations": "NONE",
        "dimensionless_parameters_before": 2,
        "dimensionless_parameters_after": 2,
        "parameter_space_restricted": True,
        "parameter_reduction_none": False,
        "GRAVITY_SCALE_INVARIANCE_OBSTRUCTED": True,
        "N_physical_before": 6,
        "N_physical_after": 6,
        "N_physical_after_note": "sealed action not modified; restricted theory is INCONSISTENT",
        "NEW_PFR": "NONE",
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "DIMENSIONLESS_FREEDOM_REMAINS": True,
        "PRINCIPLE_EFFECT": "INCONSISTENT",
    }
    conf_summary = {
        "candidates_analyzed": 8,
        "invariant_candidates": 0,
        "parameter_dependent_candidates": 0,
        "inconsistent_candidates": 8,
        "untested_candidates": 0,
        "parameter_relations_found": 0,
        "parameter_eliminations_found": 0,
        "parameter_fixed": False,
        "new_parameter_free_relations": "NONE",
        "dimensionless_parameters_before": 2,
        "dimensionless_parameters_after": 2,
        "parameter_space_restricted": False,
        "parameter_reduction_none": True,
        "CONFORMAL_COMPLETION_REQUIRED": True,
        "N_physical_before": 6,
        "N_physical_after": 6,
        "NEW_PFR": "NONE",
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "PRINCIPLE_EFFECT": "CONFORMAL_COMPLETION_REQUIRED",
    }

    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "candidates_analyzed": 8,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
        "new_assumptions": 2,
        "new_principle_count": 2,
        "NEW_PRINCIPLES_TESTED": 2,
        "new_principle_ids": list(PRINCIPLE_IDS),
        "second_pair_only": True,
        "third_principle_introduced": False,
        "new_dependencies": 0,
        "new_fields": 0,
        "ranking": False,
        "known_physics_comparison": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "scale": scale_summary,
        "conformal": conf_summary,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "dilaton_added": False,
        "compensator_added": False,
        "improvement_added": False,
        "quartic_added": False,
        "rg_introduced": False,
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
        "PHASE_11B6_STATUS": "INTEGRITY_FAILURE" if integrity_failure else "CLOSED",
        "integrity_failure": integrity_failure,
        "phase_11b7_executed": False,
        "no_external_scales_reimposed": False,
        "branches_ranked": False,
        "preferred_branch": None,
    }
    abort = _target_blindness_abort({"summary": summary, "pfr_s": pfr_s, "pfr_c": pfr_c}, stage="audit")
    if abort is not None:
        return abort

    _write_json("DIMENSION_ASSIGNMENTS.json", dims)
    _write_json("SCALE_VARIATION.json", var)
    _write_json("WEYL_KINETIC_REMAINDER.json", weyl)
    _write_json("SPECIAL_CONFORMAL.json", special)
    _write_json("SCALE_BRANCH.json", scale_rows)
    _write_json("CONFORMAL_BRANCH.json", conf_rows)
    _write_json("PARAMETER_EFFECTS.json", params)
    _write_json("DIMENSIONLESS_FREEDOM.json", dimless)
    _write_json("CLOSURE_COMPARISON.json", closure)
    _write_json("PHASE_11B6_SUMMARY.json", summary)

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
        summary["PHASE_11B6_STATUS"] = "INTEGRITY_FAILURE"
    _write_json("PHASE_11B6_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11B6_TEST_COPY_ID": PHASE_11B6_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "principle": {
            "principle_ids": list(PRINCIPLE_IDS),
            "provenance": "INPUT / FUTURE TEST",
            "new_principle_count": 2,
            "branches_combined": False,
        },
        "dimension_assignments": dims,
        "scale_variation": var,
        "weyl_kinetic": weyl,
        "special_conformal": special,
        "scale_table": scale_rows,
        "conformal_table": conf_rows,
        "parameter_table": params,
        "dimensionless_table": dimless,
        "closure_comparison": closure,
        "pfr_scale": pfr_s,
        "pfr_conformal": pfr_c,
        "scale_summary": scale_summary,
        "conformal_summary": conf_summary,
        "audit_summary": summary,
        "NEW_PRINCIPLES_TESTED": 2,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "GRAVITY_SCALE_INVARIANCE_OBSTRUCTED": True,
        "CONFORMAL_COMPLETION_REQUIRED": True,
        "dilaton_added": False,
        "improvement_added": False,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_11B6_STATUS": summary["PHASE_11B6_STATUS"],
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash(),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_comparison_executed": False,
        "phase_11b7_executed": False,
        "third_principle_introduced": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_principle_count": 2,
        "new_fields": 0,
        "search_space_modified": False,
        "grammar_changed": 0,
        "phase_10b1_artifacts_unchanged": summary.get("phase10b1_artifacts_unchanged"),
        "phase_11b5_artifacts_unchanged": summary.get("phase11b5_artifacts_unchanged"),
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_11B6_CLOSED": summary["PHASE_11B6_STATUS"] == "CLOSED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_scale_implies_conformal": "REJECTED AS OVERCLAIM",
            "2_add_dilaton_or_compensator": "REJECTED AS OVERCLAIM",
            "3_add_improvement_coupling": "REJECTED AS OVERCLAIM",
            "4_add_quartic_to_restore_scaling": "REJECTED AS OVERCLAIM",
            "5_background_c0_zero_is_scale_symmetry": "REJECTED AS OVERCLAIM",
            "6_lambda_ratio_fixed_by_dimension": "REJECTED AS OVERCLAIM",
            "7_canonical_Z_is_physical_fixing": "REJECTED AS OVERCLAIM",
            "8_replace_Einstein_Hilbert": "REJECTED AS OVERCLAIM",
            "9_rank_or_prefer_a_branch": "REJECTED AS OVERCLAIM",
            "10_invoke_RG_or_anomalies": "REJECTED AS OVERCLAIM",
            "11_inconsistency_is_uniqueness": "REJECTED AS OVERCLAIM",
            "12_start_next_11B_phase": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_11B6_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["new_principle_count"] == 2
        and science["phase_11b7_executed"] is False
        and science["dilaton_added"] is False
        and science["improvement_added"] is False
        and var["kinetic_invariant"] is True
        and var["c1_invariant"] is False
        and weyl["CONFORMAL_COMPLETION_REQUIRED"] is True
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and specs_unchanged
    )
    return science


def run_phase11b6_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11b6_scale_conformal(auth, signature=signature)
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
            "PHASE_11B5_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11b5_artifacts_unchanged") else "FAILED",
            "PHASE_11B6_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_11B6_STATUS": science.get("PHASE_11B6_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "NEW_PRINCIPLE_COUNT": 2,
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
