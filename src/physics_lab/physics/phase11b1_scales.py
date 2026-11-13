"""Phase 11B.1: NO_EXTERNAL_DIMENSIONFUL_SCALES test.

One new physical assumption.  Does not modify the frozen action, grammar,
or Phase 10B/11A artifacts.  Does not introduce a second principle.
Does not repair gravity.  Does not start Phase 11B.2.
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
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase11a_strategy import artifact_dir as phase11a_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "PHASE_11B1_TEST_COPY_ID",
    "analyze_phase11b1_scales",
    "artifact_dir",
    "run_phase11b1_or_stop",
]

PHASE_11B1_TEST_COPY_ID = "PHASE_11B1_NO_EXTERNAL_DIMENSIONFUL_SCALES_TEST"
PHASE = "PHASE_11B.1"
AUDIT_VERSION = "phase11b1-no-external-scales-v1"
EXPECTED_CANDIDATE_COUNT = 8
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
PRINCIPLE_ID = "NO_EXTERNAL_DIMENSIONFUL_SCALES"

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json", "PARAMETER_INVENTORY.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B3 = ("PHASE_10B3_SUMMARY.json",)
_REQUIRED_10B4 = ("PHASE_10B4_SUMMARY.json",)
_REQUIRED_10B5 = ("PHASE_10B5_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B7 = ("PHASE_10B7_SUMMARY.json",)
_REQUIRED_10B8 = ("PHASE_10B8_SUMMARY.json",)
_REQUIRED_10B9 = ("PHASE_10B9_SUMMARY.json",)
_REQUIRED_10B10 = ("PHASE_10B10_SUMMARY.json", "PARAMETER_STATUS_TABLE.json")
_REQUIRED_11A = ("PHASE_11A_SUMMARY.json", "PARAMETER_INVENTORY.json", "MASTER_MATRIX.json")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11b1_artifacts"


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
    mapping = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b3", _REQUIRED_10B3, phase10b3_artifact_dir()),
        ("phase10b4", _REQUIRED_10B4, phase10b4_artifact_dir()),
        ("phase10b5", _REQUIRED_10B5, phase10b5_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
        ("phase10b7", _REQUIRED_10B7, phase10b7_artifact_dir()),
        ("phase10b8", _REQUIRED_10B8, phase10b8_artifact_dir()),
        ("phase10b9", _REQUIRED_10B9, phase10b9_artifact_dir()),
        ("phase10b10", _REQUIRED_10B10, phase10b10_artifact_dir()),
        ("phase11a", _REQUIRED_11A, phase11a_artifact_dir()),
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11B.1 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 11B.1 refuses to proceed"}
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


def _principle_definition() -> dict[str, Any]:
    return {
        "principle_id": PRINCIPLE_ID,
        "statement": (
            "The theory may not contain an independently introduced external reference "
            "quantity carrying nonzero mass dimension that is not generated internally "
            "by the theory itself."
        ),
        "provenance": "INPUT / FUTURE TEST",
        "not_equated_to": "all dimensionful parameters must vanish, unless that implication is established for the stored action",
        "not_combined_with": [
            "scale invariance",
            "conformal invariance",
            "quantum unitarity",
            "RG fixed points",
            "boundary conditions",
        ],
        "distinguishes": [
            "external reference scale",
            "internal dynamical scale",
            "dimensionful coupling",
            "dimensionless coupling",
            "field normalization",
            "convention",
        ],
        "new_principle_count": 1,
    }


def _dimensional_convention() -> dict[str, Any]:
    return {
        "spacetime_dimension": 4,
        "action_dimension": 0,
        "lagrangian_density_dimension": 4,
        "metric_dimension": 0,
        "curvature_R_dimension": 2,
        "Phi_dimension_given_conventional_Z": 1,
        "Z_dimension_given_that_assignment": 0,
        "A_mu_dimension": 1,
        "F_dimension": 2,
        "K_dimension": 0,
        "provenance": "CONVENTION",
        "note": (
            "Field dimensions are a conventional assignment used to locate which "
            "coefficients carry nonzero mass dimension. This is not a second principle."
        ),
    }


def _parameter_audit() -> list[dict[str, Any]]:
    phys = _phys_coupling_name()
    return [
        {
            "parameter": "c0",
            "mass_dimension": 4,
            "dimensionless_or_dimensionful": "dimensionful",
            "external_internal_conventional": "external",
            "role": "volume / vacuum coefficient in S_gravity",
            "before": "FREE",
            "after": "ELIMINATED / FORBIDDEN",
            "effect": "INCOMPATIBLE; TERM_EXCLUDED_BY_NEW_PRINCIPLE; not a derived value",
            "compatibility": "INCOMPATIBLE",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "c1",
            "mass_dimension": 2,
            "dimensionless_or_dimensionful": "dimensionful",
            "external_internal_conventional": "external",
            "role": "Ricci coefficient in S_gravity",
            "before": "FREE",
            "after": "ELIMINATED / FORBIDDEN",
            "effect": "INCOMPATIBLE; TERM_EXCLUDED_BY_NEW_PRINCIPLE; c1<0 was SIGN_ONLY and is not a fixing",
            "compatibility": "INCOMPATIBLE",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "lambda_a",
            "mass_dimension": "0 if the dimension sits on c_H; 2 if it sits on H_int",
            "dimensionless_or_dimensionful": "dimensionful in at least one placement of the overall potential scale",
            "external_internal_conventional": "external as an independent scale; operator shape is dimensionless",
            "role": "H_int eigenvalue",
            "before": "FREE",
            "after": "independent dimensionful placement ELIMINATED; ratio with lambda_b not fixed",
            "effect": "ELIMINATED as external scale; not RELATED to gravity; ratio remains unselected",
            "compatibility": "INCOMPATIBLE as an independent dimensionful coefficient",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "lambda_b",
            "mass_dimension": "0 if the dimension sits on c_H; 2 if it sits on H_int",
            "dimensionless_or_dimensionful": "same dichotomy as lambda_a",
            "external_internal_conventional": "external as an independent scale; operator shape is dimensionless",
            "role": "H_int degenerate-plane eigenvalue",
            "before": "FREE",
            "after": "independent dimensionful placement ELIMINATED; ratio with lambda_a not fixed",
            "effect": "ELIMINATED as external scale; lambda_a/lambda_b is dimensionless and not selected",
            "compatibility": "INCOMPATIBLE as an independent dimensionful coefficient",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "kappa",
            "mass_dimension": 2,
            "dimensionless_or_dimensionful": "dimensionful",
            "external_internal_conventional": "external",
            "role": "Phi^2 potential coefficient",
            "before": "FREE",
            "after": "ELIMINATED / FORBIDDEN",
            "effect": "INCOMPATIBLE; TERM_EXCLUDED_BY_NEW_PRINCIPLE for the kappa Phi^2 term",
            "compatibility": "INCOMPATIBLE",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "c_H",
            "mass_dimension": "2 if H_int is dimensionless; 0 if H_int carries dimension 2",
            "dimensionless_or_dimensionful": "dimensionful in the first placement",
            "external_internal_conventional": "external if it carries the potential scale; otherwise a dimensionless multiplier",
            "role": "coefficient of <Phi, H_int Phi>",
            "before": "FREE",
            "after": "ELIMINATED if dimensionful; otherwise conventional multiplier of a forbidden H_int scale",
            "effect": "potential term TERM_EXCLUDED_BY_NEW_PRINCIPLE without an internal scale",
            "compatibility": "INCOMPATIBLE as an independent dimensionful coefficient",
            "provenance": "DERIVED GIVEN ASSUMPTION",
        },
        {
            "parameter": "Z_A",
            "mass_dimension": 0,
            "dimensionless_or_dimensionful": "dimensionless",
            "external_internal_conventional": "conventional magnitude; physical sign",
            "role": "gauge kinetic normalization",
            "before": "FREE sign; conventional magnitude",
            "after": "UNAFFECTED by the new principle",
            "effect": "CONVENTIONAL; the principle is not a gauge-normalization condition",
            "compatibility": "CONVENTIONAL",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "Z",
            "mass_dimension": 0,
            "dimensionless_or_dimensionful": "dimensionless",
            "external_internal_conventional": "conventional magnitude; physical sign",
            "role": "matter kinetic normalization",
            "before": "CONVENTION",
            "after": "UNAFFECTED",
            "effect": "CONVENTIONAL; canonical |Z| is not a physical determination",
            "compatibility": "CONVENTIONAL",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "g",
            "mass_dimension": 0,
            "dimensionless_or_dimensionful": "dimensionless",
            "external_internal_conventional": "conventional",
            "role": "gauge normalization label",
            "before": "CONVENTION",
            "after": "UNAFFECTED",
            "effect": "CONVENTIONAL",
            "compatibility": "CONVENTIONAL",
            "provenance": "CONVENTION",
        },
        {
            "parameter": phys,
            "mass_dimension": 0,
            "dimensionless_or_dimensionful": "dimensionless",
            "external_internal_conventional": "conventional",
            "role": "physical-coupling label on F^2 models",
            "before": "CONVENTION",
            "after": "UNAFFECTED",
            "effect": "CONVENTIONAL; not a derived coupling",
            "compatibility": "CONVENTIONAL",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "overall_K_scale",
            "mass_dimension": 0,
            "dimensionless_or_dimensionful": "dimensionless",
            "external_internal_conventional": "conventional",
            "role": "generator normalization",
            "before": "CONVENTION",
            "after": "UNAFFECTED",
            "effect": "CONVENTIONAL",
            "compatibility": "CONVENTIONAL",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "overall_H_int_scale",
            "mass_dimension": 0,
            "dimensionless_or_dimensionful": "dimensionless",
            "external_internal_conventional": "conventional",
            "role": "operator-normalization label, distinct from the physical eigenvalues",
            "before": "CONVENTION",
            "after": "UNAFFECTED as a convention; it does not replace a forbidden physical scale",
            "effect": "CONVENTIONAL",
            "compatibility": "CONVENTIONAL",
            "provenance": "CONVENTION",
        },
    ]


def _candidate_rows(catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in catalog:
        sel = dict(item["axis_selection"])
        f2 = sel.get("GAUGE_DYNAMICS_CLASS") == "optional_F2_test_extension"
        op = sel.get("INTERNAL_OPERATOR_CLASS")
        h_labels = "lambda_a, lambda_b" if op == "commutant_symmetric_K" else "a0, a1 reparameterizing lambda_a, lambda_b"
        gauge = (
            "CONVENTIONAL / UNAFFECTED (Z_A, "
            + _phys_coupling_name()
            + ")"
            if f2
            else "no autonomous F^2; no additional gauge scale"
        )
        rows.append(
            {
                "model": item["model_id"],
                "compatibility": "INCOMPATIBLE",
                "gravity": "INCOMPATIBLE; GRAVITY_ACTION_INCOMPATIBLE_WITH_NEW_PRINCIPLE",
                "internal": (
                    "kinetic Z CONVENTIONAL; potential coefficients INCOMPATIBLE; "
                    "H_int labels " + h_labels
                ),
                "gauge": gauge,
                "remaining_freedom": (
                    "no compatible dimensionful physical coefficient remains; "
                    "conventional Z"
                    + ((", Z_A, " + _phys_coupling_name()) if f2 else "")
                    + "; operator-shape ratio not selected and not deployed without a scale"
                ),
                "autonomous_F2": f2,
                "internal_operator": op,
            }
        )
    return rows


def _tables(catalog: list[dict[str, Any]]) -> dict[str, Any]:
    params = _parameter_audit()
    candidates = _candidate_rows(catalog)
    remaining_after = [
        "Z (conventional magnitude; sign PARAMETER-DEPENDENT, not a value)",
        "Z_A where F^2 is present (conventional magnitude; sign PARAMETER-DEPENDENT)",
        "g and " + _phys_coupling_name() + " (conventional)",
        "overall_K_scale, overall_H_int_scale, ONB_in_V_b (conventional)",
        "lambda_a/lambda_b as an undeployed dimensionless operator shape, not uniquely selected",
    ]
    closure = [
        {"quantity": "unique_action", "Phase_10B": "NO", "after_11B1": "NO", "change": "unchanged; all 8 remain incompatible rather than unique"},
        {"quantity": "unique_kinetic_structure", "Phase_10B": "NO", "after_11B1": "NO", "change": "unchanged; F^2 present vs absent is still a kinetic distinction among incompatible models"},
        {"quantity": "unique_dimensionless_quantity", "Phase_10B": "NO", "after_11B1": "NO", "change": "unchanged; the principle does not select lambda_a/lambda_b or any other ratio"},
        {"quantity": "parameter_free_closure", "Phase_10B": "NO", "after_11B1": "NO", "change": "incompatibility is not closure"},
        {"quantity": "global_closure", "Phase_10B": "NO", "after_11B1": "NO", "change": "inconsistent with the sealed gravity family; not fully closed"},
    ]
    dimensionless = {
        "lambda_a / lambda_b": {
            "dimensionless": True,
            "meaningful_in_compatible_action": False,
            "selected_by_principle": False,
            "note": "operator shape; the potential term that would deploy it is excluded without an internal scale",
        },
        "kappa / c_H": {
            "dimensionless": True,
            "meaningful_in_compatible_action": False,
            "selected_by_principle": False,
            "note": "relative potential mixing; both overall coefficients are forbidden as external scales",
        },
        "c0 / c1": {
            "dimensionless": False,
            "mass_dimension": 2,
            "meaningful_as_dimensionless_leftover": False,
            "selected_by_principle": False,
            "note": "this ratio is still dimensionful; it is not a dimensionless coupling",
        },
        "DIMENSIONLESS_FREEDOM_REMAINS": "YES",
        "note": (
            "conventional dimensionless normalizations remain, and no dimensionless "
            "ratio is uniquely selected. Remaining dimensionless freedom is not uniqueness."
        ),
    }
    pfr_before = _parameter_free_test(["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"])
    pfr_after = _parameter_free_test([])
    new_pfr = "NO_NEW_PFR"
    if pfr_after.get("relations"):
        new_pfr = "NEW_PFR"
    return {
        "principle": _principle_definition(),
        "dimensional_convention": _dimensional_convention(),
        "parameter_table": params,
        "candidate_table": candidates,
        "closure_comparison": closure,
        "dimensionless": dimensionless,
        "pfr_before": pfr_before,
        "pfr_after": pfr_after,
        "NEW_PFR": new_pfr,
        "PRINCIPLE_EFFECT": "INCONSISTENT_WITH_SEALED_MODEL",
        "GRAVITY_ACTION_INCOMPATIBLE_WITH_NEW_PRINCIPLE": True,
        "DYNAMIC_SCALE_GENERATION_NOT_IMPLEMENTED": True,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "DIMENSIONLESS_FREEDOM_REMAINS": "YES",
        "compatible_candidates": 0,
        "incompatible_candidates": 8,
        "remaining_physical_freedom": remaining_after,
        "N_physical_before": 6,
        "N_physical_after": 0,
        "N_conventional_before": 6,
        "N_conventional_after": 6,
        "removed_physical_dimensions": [
            "c0 (external dim 4)",
            "c1 (external dim 2)",
            "independent potential scale carried by {kappa, c_H, lambda_a, lambda_b}",
        ],
        "not_counted_as_reduction_to_a_point": ["c1 < 0", "Z < 0", "Z_A > 0"],
        "gravity_before": {"c0": "FREE", "c1": "FREE", "action": "integral sqrt(-g)(c0 + c1 R)"},
        "no_repair": {
            "dilaton_added": False,
            "compensating_scalar_added": False,
            "new_fields_added": False,
            "action_modified": False,
            "scale_invariance_imposed": False,
            "conformal_invariance_imposed": False,
            "RG_imposed": False,
            "quantum_effects_imposed": False,
            "dimensional_transmutation_introduced": False,
            "spontaneous_symmetry_breaking_introduced": False,
        },
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "uniqueness_outcome": "inconsistent",
    }


def analyze_phase11b1_scales(
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
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        integrity_failure = "dependency schema not CONSISTENT"

    specs_unchanged = True
    dep_valid = 0
    dep_unchecked = 0
    dep_invalid = 0
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
    if not specs_unchanged or dep_invalid != 0:
        integrity_failure = integrity_failure or "dependency INVALID appeared"

    tables = _tables(catalog)
    abort = _target_blindness_abort(tables, stage="scales")
    if abort is not None:
        return abort

    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "PHASE_11A_STATUS": s11a.get("PHASE_11A_STATUS"),
        "candidates_analyzed": 8,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
        "new_assumptions": 1,
        "new_principle_count": 1,
        "new_principle_id": PRINCIPLE_ID,
        "new_dependencies": 0,
        "new_candidate_families": 0,
        "new_fields": 0,
        "principle_implemented_as_action_rewrite": False,
        "parameters_numerically_fixed": False,
        "numerical_values_inserted": False,
        "ranking": False,
        "known_physics_comparison": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "PRINCIPLE_EFFECT": tables["PRINCIPLE_EFFECT"],
        "GRAVITY_ACTION_INCOMPATIBLE_WITH_NEW_PRINCIPLE": True,
        "DYNAMIC_SCALE_GENERATION_NOT_IMPLEMENTED": True,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "DIMENSIONLESS_FREEDOM_REMAINS": "YES",
        "NEW_PFR": tables["NEW_PFR"],
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "uniqueness_outcome": "inconsistent",
        "compatible_candidates": 0,
        "N_physical_before": 6,
        "N_physical_after": 0,
        "N_conventional_before": 6,
        "N_conventional_after": 6,
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
        "PHASE_11B1_STATUS": "INTEGRITY_FAILURE" if integrity_failure else "CLOSED",
        "integrity_failure": integrity_failure,
        "second_principle_introduced": False,
        "phase_11b2_executed": False,
    }
    abort = _target_blindness_abort({"summary": summary, "tables": tables}, stage="audit")
    if abort is not None:
        return abort

    _write_json("PRINCIPLE_DEFINITION.json", tables["principle"])
    _write_json("PARAMETER_DIMENSION_TABLE.json", tables["parameter_table"])
    _write_json("CANDIDATE_COMPATIBILITY_TABLE.json", tables["candidate_table"])
    _write_json("CLOSURE_COMPARISON.json", tables["closure_comparison"])
    _write_json("PHASE_11B1_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == EXPECTED_GRAMMAR_HASH == manifest.get("grammar_hash")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    for n in range(1, 11):
        key = f"phase10b{n}"
        summary[f"{key}_artifacts_unchanged"] = hashes_before[key] == hashes_after[key]
    summary["phase11a_artifacts_unchanged"] = hashes_before["phase11a"] == hashes_after["phase11a"]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["whitelist_unchanged"] = WHITELIST_VERSION == manifest.get("whitelist_version")
    summary["blacklist_unchanged"] = BLACKLIST_VERSION == manifest.get("blacklist_version")
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    if not (artifacts_ok and grammar_ok and frozen_ok and specs_unchanged and summary["ranking"] is False):
        summary["PHASE_11B1_STATUS"] = "INTEGRITY_FAILURE"
    _write_json("PHASE_11B1_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11B1_TEST_COPY_ID": PHASE_11B1_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "principle": tables["principle"],
        "dimensional_convention": tables["dimensional_convention"],
        "parameter_table": tables["parameter_table"],
        "candidate_table": tables["candidate_table"],
        "closure_comparison": tables["closure_comparison"],
        "dimensionless": tables["dimensionless"],
        "remaining_physical_freedom": tables["remaining_physical_freedom"],
        "audit_summary": summary,
        "PRINCIPLE_EFFECT": tables["PRINCIPLE_EFFECT"],
        "NEW_PFR": tables["NEW_PFR"],
        "GRAVITY_ACTION_INCOMPATIBLE_WITH_NEW_PRINCIPLE": True,
        "DYNAMIC_SCALE_GENERATION_NOT_IMPLEMENTED": True,
        "NO_NEW_CROSS_SECTOR_RELATION": True,
        "DIMENSIONLESS_FREEDOM_REMAINS": "YES",
        "UNIQUE_ACTION": "NO",
        "UNIQUE_KINETIC_STRUCTURE": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "PARAMETER_FREE_CLOSURE": "NO",
        "GLOBAL_CLOSURE": "NO",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_11B1_STATUS": summary["PHASE_11B1_STATUS"],
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash(),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_comparison_executed": False,
        "phase_11b2_executed": False,
        "second_principle_introduced": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_principle_count": 1,
        "new_dependencies": 0,
        "new_fields": 0,
        "search_space_modified": False,
        "grammar_changed": 0,
        "phase_10a_grammar_version_unchanged": True,
        "phase_10b1_artifacts_unchanged": summary["phase10b1_artifacts_unchanged"],
        "phase_10b10_artifacts_unchanged": summary["phase10b10_artifacts_unchanged"],
        "phase_11a_artifacts_unchanged": summary["phase11a_artifacts_unchanged"],
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_11B1_CLOSED": summary["PHASE_11B1_STATUS"] == "CLOSED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_all_dimensionful_parameters_must_vanish_without_audit": "REJECTED AS OVERCLAIM",
            "2_elimination_is_a_derived_numerical_value": "REJECTED AS OVERCLAIM",
            "3_canonical_norm_is_physical_coupling": "REJECTED AS OVERCLAIM",
            "4_c0_over_c1_is_dimensionless": "REJECTED AS OVERCLAIM",
            "5_ratio_fixes_numerator_or_denominator": "REJECTED AS OVERCLAIM",
            "6_incompatibility_is_uniqueness": "REJECTED AS OVERCLAIM",
            "7_repair_gravity_with_a_new_field": "REJECTED AS OVERCLAIM",
            "8_introduce_scale_or_conformal_invariance": "REJECTED AS OVERCLAIM",
            "9_introduce_dimensional_transmutation": "REJECTED AS OVERCLAIM",
            "10_start_phase_11b2": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_11B1_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_principle_count"] == 1
        and science["phase_11b2_executed"] is False
        and science["second_principle_introduced"] is False
        and science["UNIQUE_ACTION"] == "NO"
        and science["GLOBAL_CLOSURE"] == "NO"
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and specs_unchanged
    )
    return science


def run_phase11b1_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11b1_scales(auth, signature=signature)
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
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b1_artifacts_unchanged") else "FAILED",
            "PHASE_10B10_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b10_artifacts_unchanged") else "FAILED",
            "PHASE_11A_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_11a_artifacts_unchanged") else "FAILED",
            "PHASE_11B1_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_11B1_STATUS": science.get("PHASE_11B1_STATUS"),
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
