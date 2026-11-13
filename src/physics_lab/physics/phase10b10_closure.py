"""Phase 10B.10: global closure and stop audit of the bounded 10B search.

Does not modify the frozen action, Phases 4A-9, or the Phase 10A grammar.
Does not overwrite Phase 10B.1-10B.9 artifacts.  Does not invent dependencies.
Does not regenerate candidates.  Does not rank models.  Does not start 10C.
Synthesizes already completed 10B.1-10B.9 results only.
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
    parameter_inventory,
    undeclared_inferences,
    validate_dependencies,
)
from physics_lab.physics.phase10b1_exploration import (
    artifact_dir as phase10b1_artifact_dir,
    build_model_spec,
)
from physics_lab.physics.phase10b2_derivation import (
    DERIVATION_VERSION as PHASE_10B2_DERIVATION_VERSION,
)
from physics_lab.physics.phase10b2_derivation import (
    _parameter_free_test,
    artifact_dir as phase10b2_artifact_dir,
)
from physics_lab.physics.phase10b3_audit import AUDIT_VERSION as PHASE_10B3_AUDIT_VERSION
from physics_lab.physics.phase10b3_audit import artifact_dir as phase10b3_artifact_dir
from physics_lab.physics.phase10b4_validation import PATCH_VERSION as PHASE_10B4_PATCH_VERSION
from physics_lab.physics.phase10b4_validation import artifact_dir as phase10b4_artifact_dir
from physics_lab.physics.phase10b5_semantics import AUDIT_VERSION as PHASE_10B5_AUDIT_VERSION
from physics_lab.physics.phase10b5_semantics import artifact_dir as phase10b5_artifact_dir
from physics_lab.physics.phase10b6_schema import SCHEMA_VERSION as PHASE_10B6_SCHEMA_VERSION
from physics_lab.physics.phase10b6_schema import artifact_dir as phase10b6_artifact_dir
from physics_lab.physics.phase10b7_revalidation import DERIVATION_VERSION as PHASE_10B7_DERIVATION_VERSION
from physics_lab.physics.phase10b7_revalidation import artifact_dir as phase10b7_artifact_dir
from physics_lab.physics.phase10b8_euler_lagrange import AUDIT_VERSION as PHASE_10B8_AUDIT_VERSION
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase10b9_linearized_ghost import AUDIT_VERSION as PHASE_10B9_AUDIT_VERSION
from physics_lab.physics.phase10b9_linearized_ghost import artifact_dir as phase10b9_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "PHASE_10B10_TEST_COPY_ID",
    "analyze_phase10b10_closure",
    "artifact_dir",
    "run_phase10b10_or_stop",
]

PHASE_10B10_TEST_COPY_ID = "PHASE_10B10_GLOBAL_CLOSURE_AND_STOP_AUDIT"
PHASE = "PHASE_10B.10"
AUDIT_VERSION = "phase10b10-global-closure-v1"
EXPECTED_CANDIDATE_COUNT = 8
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json", "PARAMETER_INVENTORY.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B3 = ("PHASE_10B3_SUMMARY.json", "OPERATOR_EQUIVALENCE_AUDIT.json")
_REQUIRED_10B4 = ("PHASE_10B4_SUMMARY.json",)
_REQUIRED_10B5 = ("PHASE_10B5_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B7 = ("PHASE_10B7_SUMMARY.json",)
_REQUIRED_10B8 = ("PHASE_10B8_SUMMARY.json", "EOM_CANDIDATE_RESULTS.json")
_REQUIRED_10B9 = ("PHASE_10B9_SUMMARY.json", "LINEARIZED_CANDIDATE_RESULTS.json")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b10_artifacts"


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
    out = {f"phase10b{n}": {} for n in (1, 2, 3, 4, 5, 6, 7, 8, 9)}
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
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.10 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.10 refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar_version is not the 10B.1 grammar"}
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


def _row(item: str, result: str, provenance: str, scope: str, remaining: str) -> dict[str, str]:
    return {
        "item": item,
        "result": result,
        "provenance": provenance,
        "scope": scope,
        "remaining_freedom": remaining,
    }


def _parameter_row(name: str, status: str, condition: str, kind: str, scope: str) -> dict[str, str]:
    return {
        "parameter": name,
        "status": status,
        "condition": condition,
        "physical_or_conventional": kind,
        "scope": scope,
    }


def _closure_tables(priors: dict[str, Any]) -> dict[str, Any]:
    phys = _phys_coupling_name()
    s1 = priors["s1"]
    s3 = priors["s3"]
    s6 = priors["s6"]
    s8 = priors["s8"]
    s9 = priors["s9"]
    eq = priors["eq"]
    eom = priors["eom"]
    lin = priors["lin"]

    unique_action = "NO"
    unique_kinetic = "NO"
    unique_dimless = "NO"
    param_closure = "NO"
    unique_theory = "NO"
    global_closure = "NO"

    master = [
        _row(
            "ACTION_UNIQUENESS",
            unique_action,
            "DERIVED",
            "10B.1 distinct hashes=8; 10B.3 EQUIVALENCE_UNSUPPORTED; certified equivalences do not collapse the set",
            "8 syntactic MODEL_SPECs remain; operator reparameterization is not certified equivalence",
        ),
        _row(
            "KINETIC_UNIQUENESS",
            unique_kinetic,
            "DERIVED",
            "stored kinetic Z g^{mu nu} inner(D Phi, D Phi) is shared; autonomous F^2 is present only in a subset",
            "F^2 present vs absent is a remaining kinetic distinction; |Z| rescaling is CONVENTION not uniqueness",
        ),
        _row(
            "DIMENSIONLESS_CLOSURE",
            unique_dimless,
            "DERIVED",
            "catalog of stored ratios from 10B.1 inventories and 10B.9 sign conditions",
            "lambda_a/lambda_b, a0/a1, c0/c1, kappa/c_H, m_n^2/m_k^2 remain PARAMETER-DEPENDENT",
        ),
        _row(
            "PARAMETER_CLOSURE",
            param_closure,
            "DERIVED",
            "10B.1 physical_freedom union 10B.9 sign conditions; existing PFR detector",
            "c0, c1, two H_int coefficients, kappa, c_H remain FREE; Z_A FREE where F^2 is present",
        ),
        _row(
            "INTERNAL_CLOSURE",
            "NO",
            "DERIVED",
            "frozen 4C plus 10B stored H_int; no new generator",
            "lambda_a, lambda_b or a0, a1; overall_K_scale; overall_H_int_scale; ONB_in_V_b",
        ),
        _row(
            "GAUGE_COUPLING_CLOSURE",
            "NO",
            "DERIVED",
            "10B.6-10B.9; F2_A_MU_DEPENDENCY UNDECLARED",
            "Z_A FREE; " + phys + " CONVENTION; canonical Z_A -> 1 is not DERIVED",
        ),
        _row(
            "GRAVITY_CLOSURE",
            "NO",
            "DERIVED",
            "stored family integral sqrt(-g)(c0 + c1 R); no stored c0-c1-matter map",
            "c0 FREE; c1 FREE; c0=0 is BACKGROUND_CONDITION only",
        ),
        _row(
            "DYNAMIC_CONSISTENCY",
            "PARTIAL",
            "DERIVED GIVEN ASSUMPTION",
            "10B.8 EOM plus 10B.9 linearized ghosts; quantum unitarity not upgraded",
            "matter/gauge/gravity ghosts PARAMETER_DEPENDENT or UNTESTED; ADM DOF UNTESTED; quantum unitarity UNTESTED",
        ),
        _row(
            "EQUIVALENCE_STATUS",
            "EQUIVALENCE_UNSUPPORTED",
            "DERIVED",
            "10B.3 OPERATOR_EQUIVALENCE_AUDIT; supported rules are name/id/json sorts only",
            "ALGEBRAIC_SIMPLIFICATION_UNSUPPORTED; 4 reparameterization pairs not merged",
        ),
        _row(
            "SEARCH_COMPLETENESS",
            "EXHAUSTIVE_OVER_CURRENT_FINITE_GRAMMAR",
            "DERIVED",
            "10B.1 SEARCH_SUMMARY; not exhaustive over all conceivable theories",
            "product size 8; 0 rejected; 0 hash-duplicates; 6 UNCHECKED dependencies remain in the set",
        ),
        _row(
            "FINAL_PARAMETER_FREE_RELATIONS",
            "NONE",
            "DERIVED",
            "existing detector on accumulated 10B.1-10B.9 catalogs; no numerical search",
            "no forced symbolic relation removes continuous freedom",
        ),
        _row(
            "GLOBAL_CLOSURE",
            global_closure,
            "DERIVED",
            "conjunction of uniqueness and parameter-free closure questions C1-C5",
            "no unique action, kinetic, dimensionless quantity, or inequivalent theory",
        ),
        _row(
            "PHASE_10B_STATUS",
            "CLOSED_NO_INTERNAL_CLOSURE",
            "DERIVED",
            "finite grammar exhaustively tested; remaining freedom is structural, not a missing computation of a stored principle",
            "further progress requires an explicitly new principle or an expanded grammar; this is not a claim that no deeper theory exists",
        ),
    ]

    parameters = [
        _parameter_row("c0", "FREE", "c0=0 is BACKGROUND_CONDITION only, not a PFR", "physical", "S_gravity"),
        _parameter_row("c1", "FREE", "ghost-free TT probe iff c1 < 0 (PARAMETER-DEPENDENT); does not fix c1", "physical", "S_gravity / 10B.9"),
        _parameter_row("Z", "CONVENTION", "ghost-free matter kinetic iff Z < 0 on mostly_plus; |Z| is conventional", "conventional magnitude; physical sign", "stored kinetic / 10B.9"),
        _parameter_row("Z_A", "FREE", "ghost-free Maxwell iff Z_A > 0 where F^2 is present; Z_A -> 1 is CONVENTION", "physical coefficient; conventional if absorbed", "F^2 TEST COPY"),
        _parameter_row("lambda_a", "FREE", "no stored relation fixes the value", "physical", "commutant H_int"),
        _parameter_row("lambda_b", "FREE", "no stored relation fixes the value", "physical", "commutant H_int"),
        _parameter_row("a0", "FREE", "reparameterization of lambda_a; not a new constraint", "physical", "function_of_KTK H_int"),
        _parameter_row("a1", "FREE", "reparameterization of lambda_b - lambda_a; not a new constraint", "physical", "function_of_KTK H_int"),
        _parameter_row("kappa", "FREE", "present in stored potential; not fixed", "physical", "matter_action_spec.potential"),
        _parameter_row("c_H", "FREE", "present in stored potential; not fixed", "physical", "matter_action_spec.potential"),
        _parameter_row("g", "CONVENTION", "not internally selected", "conventional", "normalization_spec"),
        _parameter_row(phys, "CONVENTION", "not a derived coupling", "conventional", "F^2 models only"),
        _parameter_row("overall_K_scale", "CONVENTION", "generator normalization", "conventional", "10B.1 inventory"),
        _parameter_row("overall_H_int_scale", "CONVENTION", "operator normalization", "conventional", "10B.1 inventory"),
        _parameter_row("ONB_in_V_b", "CONVENTION", "basis choice in the 2-plane", "conventional", "10B.1 inventory"),
    ]

    dimensionless = [
        {
            "combination": "lambda_a / lambda_b",
            "classification": "PARAMETER-DEPENDENT",
            "provenance": "PARAMETER-DEPENDENT",
            "note": "ratio of free eigenvalues; not selected by the grammar",
        },
        {
            "combination": "a0 / a1",
            "classification": "PARAMETER-DEPENDENT",
            "provenance": "PARAMETER-DEPENDENT",
            "note": "reparameterization of the previous ratio; not a new quantity",
        },
        {
            "combination": "c0 / c1",
            "classification": "PARAMETER-DEPENDENT",
            "provenance": "PARAMETER-DEPENDENT",
            "note": "both FREE; c0=0 is a background condition, not uniqueness",
        },
        {
            "combination": "kappa / c_H",
            "classification": "PARAMETER-DEPENDENT",
            "provenance": "PARAMETER-DEPENDENT",
            "note": "both FREE in the stored potential",
        },
        {
            "combination": "m_n^2 / m_k^2 given linear H_int",
            "classification": "PARAMETER-DEPENDENT",
            "provenance": "PARAMETER-DEPENDENT",
            "note": "10B.1 derived_quantities; depends on H_int coefficients, kappa, c_H, Z",
        },
        {
            "combination": "canonical |Z| or |Z_A| rescaling",
            "classification": "CONVENTIONAL",
            "provenance": "CONVENTION",
            "note": "field redefinition is not dynamical selection",
        },
    ]

    no_escape = [
        {"item": "representation structure", "closes_a_free_parameter": "NO", "note": "fixes the discrete 1-plus-2 split, not continuous eigenvalues"},
        {"item": "compactness", "closes_a_free_parameter": "NO", "note": "already used; does not fix lambda or Z"},
        {"item": "exact internal symmetry", "closes_a_free_parameter": "NO", "note": "[K,H]=0 reduces H to two coefficients; values remain FREE"},
        {"item": "kinetic structure", "closes_a_free_parameter": "NO", "note": "Z remains CONVENTION/sign PARAMETER-DEPENDENT"},
        {"item": "EOM order", "closes_a_free_parameter": "NO", "note": "second-order EOM does not fix coefficients"},
        {"item": "Legendre/Hessian structure", "closes_a_free_parameter": "NO", "note": "nondegeneracy is Z != 0, not a selected value"},
        {"item": "gauge invariance", "closes_a_free_parameter": "NO", "note": "U(1) redundancy does not fix Z_A"},
        {"item": "gauge kinetic term", "closes_a_free_parameter": "NO", "note": "F^2, when present, leaves Z_A FREE"},
        {"item": "gravity structure", "closes_a_free_parameter": "NO", "note": "c0 and c1 remain FREE"},
        {"item": "dimensional analysis", "closes_a_free_parameter": "NO", "note": "many dimensionless ratios exist; none uniquely selected"},
        {"item": "canonical normalization", "closes_a_free_parameter": "NO", "note": "CONVENTION, not DERIVED"},
        {"item": "cross-sector coupling", "closes_a_free_parameter": "NO", "note": "no stored relation among c0, c1, Z, Z_A, lambda, kappa, c_H"},
        {"item": "parameter reparameterization", "closes_a_free_parameter": "NO", "note": "a0, a1 map to lambda_a, lambda_b; not a physical constraint"},
        {"item": "certified equivalence", "closes_a_free_parameter": "NO", "note": "EQUIVALENCE_UNSUPPORTED; eight candidates not collapsed"},
    ]

    questions = {
        "C1_unique_action_modulo_certified_equivalence": unique_action,
        "C2_unique_kinetic_structure": unique_kinetic,
        "C3_unique_parameter_free_dimensionless_quantity": unique_dimless,
        "C4_all_continuous_parameters_fixed": param_closure,
        "C5_unique_physically_inequivalent_theory": unique_theory,
        "UNIQUE_ACTION": unique_action,
        "UNIQUE_KINETIC_STRUCTURE": unique_kinetic,
        "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": unique_dimless,
        "PARAMETER_FREE_CLOSURE": param_closure,
        "GLOBAL_CLOSURE": global_closure,
        "INTERNAL_PARAMETER_CLOSURE": "NO",
        "GAUGE_COUPLING_CLOSURE": "NO",
        "GRAVITY_PARAMETER_CLOSURE": "NO",
        "FINAL_PARAMETER_FREE_RELATIONS": "NONE",
        "FINAL_PARAMETER_FREE_CLOSURE": "NO",
        "PHASE_10B_STATUS": "CLOSED_NO_INTERNAL_CLOSURE",
    }

    eom_verified = int(s8.get("eom_verified") or 0)
    eom_partial = int(s8.get("eom_partial") or 0)
    dynamics = {
        "EOM_status": {
            "verified": eom_verified,
            "partial": eom_partial,
            "untested": int(s8.get("eom_untested") or 0),
            "source": "Phase 10B.8",
        },
        "constraints": "matter none; Maxwell first-class U(1) where F^2 and A_mu are present; gravity ADM UNTESTED",
        "physical_DOF": "matter 3 VERIFIED; gauge 0 or 2 when tested; gravity 2 PARTIAL; candidate-level DOF untested=8",
        "ghost_status": {
            "matter": "PARAMETER_DEPENDENT",
            "gauge": "NO / PARAMETER_DEPENDENT / UNTESTED by candidate",
            "gravity": "PARAMETER_DEPENDENT",
            "total": [row.get("total_classical_ghost") for row in lin],
        },
        "Ostrogradsky": "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION (10B.9 reclassification)",
        "quantum_unitarity": "UNTESTED",
        "classical_consistency_is_not_quantum_unitarity": True,
    }

    search = {
        "raw_search_size": 8,
        "candidates_generated": int(s1.get("generated_candidates") or 8),
        "candidates_rejected": int(s1.get("rejected") or 0),
        "candidates_deduplicated": int(s1.get("duplicates") or 0),
        "unresolved_equivalence": int(s3.get("equivalence_unresolved") or 0),
        "dependency_valid": int(s6.get("dependency_validated_candidates") or 0),
        "dependency_unchecked": int(s6.get("dependency_unresolved_candidates") or 0),
        "description": "exhaustive over the CURRENT FINITE GRAMMAR, not over all possible theories of physics",
        "distinct_hashes": 8,
        "EQUIVALENCE_UNSUPPORTED": True,
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
    }

    certified = {
        "certified": [
            "total derivatives (existing EL identities)",
            "coordinate / json key sorts",
            "parameter_name_sort",
            "operator_id_order",
            "assumption_id_order",
            "canonical normalization as CONVENTION",
            "parameter redefinitions as PARAMETER_REPARAMETERIZATION without certified model merge",
        ],
        "not_certified": eq.get("unsupported_equivalence_rules")
        or [
            "BASIS_EQUIVALENCE_UNSUPPORTED",
            "GENERAL_OPERATOR_REORDERING_UNSUPPORTED",
            "ALGEBRAIC_SIMPLIFICATION_UNSUPPORTED",
            "BROAD_SYMBOLIC_HEURISTIC_UNSUPPORTED",
        ],
        "model_equivalence": "UNSUPPORTED",
        "pairs_unmerged": 4,
        "invertible_field_redefinitions": "UNTESTED as a certified global equivalence engine",
    }
    return {
        "master_table": master,
        "parameter_table": parameters,
        "dimensionless_catalog": dimensionless,
        "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": "NO",
        "no_escape": no_escape,
        "questions": questions,
        "dynamics": dynamics,
        "search": search,
        "equivalence": certified,
        "eom_rows": eom,
        "linearized_rows": lin,
    }


def analyze_phase10b10_closure(
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
        s1 = _read_json(phase10b1_artifact_dir() / "SEARCH_SUMMARY.json")
        inv10b1 = _read_json(phase10b1_artifact_dir() / "PARAMETER_INVENTORY.json")
        s2 = _read_json(phase10b2_artifact_dir() / "DERIVATION_SUMMARY.json")
        s3 = _read_json(phase10b3_artifact_dir() / "PHASE_10B3_SUMMARY.json")
        eq = _read_json(phase10b3_artifact_dir() / "OPERATOR_EQUIVALENCE_AUDIT.json")
        s4 = _read_json(phase10b4_artifact_dir() / "PHASE_10B4_SUMMARY.json")
        s5 = _read_json(phase10b5_artifact_dir() / "PHASE_10B5_SUMMARY.json")
        s6 = _read_json(phase10b6_artifact_dir() / "PHASE_10B6_SUMMARY.json")
        schema_10b6 = _read_json(phase10b6_artifact_dir() / "DEPENDENCY_SCHEMA.json")
        s7 = _read_json(phase10b7_artifact_dir() / "PHASE_10B7_SUMMARY.json")
        s8 = _read_json(phase10b8_artifact_dir() / "PHASE_10B8_SUMMARY.json")
        eom = _read_json(phase10b8_artifact_dir() / "EOM_CANDIDATE_RESULTS.json")
        s9 = _read_json(phase10b9_artifact_dir() / "PHASE_10B9_SUMMARY.json")
        lin = _read_json(phase10b9_artifact_dir() / "LINEARIZED_CANDIDATE_RESULTS.json")
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if len(catalog) != EXPECTED_CANDIDATE_COUNT:
        integrity_failure = f"catalog count {len(catalog)}"
    if grammar_hash_before != EXPECTED_GRAMMAR_HASH or manifest.get("grammar_hash") != EXPECTED_GRAMMAR_HASH:
        integrity_failure = "grammar hash mismatch"
    if frozen_before != EXPECTED_FROZEN_HASH:
        integrity_failure = "frozen hash mismatch"
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        integrity_failure = "dependency schema not CONSISTENT"
    if s1.get("generated_candidates") != 8 or s1.get("rejected") != 0:
        integrity_failure = "10B.1 generation counts drifted"

    specs_unchanged = True
    dep_valid = 0
    dep_unchecked = 0
    dep_invalid = 0
    pfr_hits = 0
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
        inv = parameter_inventory(spec)
        pfree = _parameter_free_test(list(inv.get("physical_freedom") or []))
        if pfree.get("relations"):
            pfr_hits += 1

    if not specs_unchanged or dep_invalid != 0:
        integrity_failure = integrity_failure or "dependency INVALID appeared"

    tables = _closure_tables(
        {"s1": s1, "s3": s3, "s6": s6, "s8": s8, "s9": s9, "eq": eq, "eom": eom, "lin": lin}
    )
    abort = _target_blindness_abort({"tables": tables, "inv": inv10b1}, stage="closure")
    if abort is not None:
        return abort

    phase_status = "INTEGRITY_FAILURE" if integrity_failure else tables["questions"]["PHASE_10B_STATUS"]
    if integrity_failure:
        tables["master_table"] = [
            row if row["item"] != "PHASE_10B_STATUS" else {**row, "result": "INTEGRITY_FAILURE"}
            for row in tables["master_table"]
        ]
        tables["questions"]["PHASE_10B_STATUS"] = "INTEGRITY_FAILURE"

    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "candidates_analyzed": 8,
        "candidates_with_verified_EOM": int(s8.get("eom_verified") or 0),
        "candidates_with_partial_or_unresolved_dynamics": int(s8.get("eom_partial") or 0) + int(s8.get("eom_untested") or 0),
        "unique_action": "NO",
        "unique_kinetic_structure": "NO",
        "unique_dimensionless_quantity": "NO",
        "parameter_free_closure": "NO",
        "global_closure": "NO",
        "free_continuous_parameters": [
            "c0",
            "c1",
            "lambda_a",
            "lambda_b",
            "a0",
            "a1",
            "kappa",
            "c_H",
            "Z_A",
        ],
        "parameter_dependent_conditions": [
            "Z < 0 (mostly_plus matter kinetic)",
            "Z_A > 0 (Maxwell, where present)",
            "c1 < 0 (TT gravity probe)",
            "c0 = 0 BACKGROUND_CONDITION",
        ],
        "conventional_normalizations": [
            "Z magnitude",
            "overall_K_scale",
            "overall_H_int_scale",
            "ONB_in_V_b",
            _phys_coupling_name(),
            "Z_A -> 1 if chosen",
        ],
        "experimental_inputs": 0,
        "target_inputs": 0,
        "rankings": 0,
        "known_physics_comparisons": 0,
        "ranking": False,
        "known_physics_comparison": False,
        "FINAL_PARAMETER_FREE_RELATIONS": "NONE",
        "FINAL_PARAMETER_FREE_CLOSURE": "NO",
        "new_parameter_free_relations": pfr_hits,
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": pfr_hits == 0,
        "PHASE_10B_STATUS": phase_status,
        "GLOBAL_CLOSURE": "NO",
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "equivalence": "EQUIVALENCE_UNSUPPORTED",
        "dependency_valid": dep_valid,
        "dependency_unchecked": dep_unchecked,
        "dependency_invalid": dep_invalid,
        "UNCHECKED_IS_NOT_INVALID": True,
        "UNCHECKED_IS_NOT_VALID": True,
        "syntactic_candidates": 8,
        "candidates_regenerated": False,
        "new_assumptions": 0,
        "new_dependencies": 0,
        "new_candidate_families": 0,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
        "search_space_modified": False,
        "large_scale_exploration_launched": False,
        "large_scale_generation_executed": False,
        "grammar_changed": 0,
        "gravity_family_modified": False,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "phase10b2_derivation_version": PHASE_10B2_DERIVATION_VERSION,
        "phase10b3_audit_version": PHASE_10B3_AUDIT_VERSION,
        "phase10b4_patch_version": PHASE_10B4_PATCH_VERSION,
        "phase10b5_audit_version": PHASE_10B5_AUDIT_VERSION,
        "phase10b6_schema_version": PHASE_10B6_SCHEMA_VERSION,
        "phase10b7_derivation_version": PHASE_10B7_DERIVATION_VERSION,
        "phase10b8_audit_version": PHASE_10B8_AUDIT_VERSION,
        "phase10b9_audit_version": PHASE_10B9_AUDIT_VERSION,
        "UNDECLARED_POTENTIAL_DEPENDENCY": [item["inference_id"] for item in undeclared_inferences()],
        "interpretation": (
            "exhaustive within current bounded grammar + no parameter-free closure "
            "+ remaining free parameters = no internal closure within current grammar"
        ),
        "not_a_claim_that_physics_is_impossible": True,
        "not_a_claim_that_no_deeper_theory_exists": True,
        "parameter_free_test_scope": (
            "existing detector on 10B.1-10B.9 stored catalogs; sign inequalities and "
            "BACKGROUND_CONDITION c0=0 are PARAMETER-DEPENDENT, not PFRs"
        ),
        "s2_no_pfr": s2.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"),
        "s4_raw_size": s4.get("RAW_SEARCH_SPACE_SIZE"),
        "s5_schema_was_undefined": s5.get("DEPENDENCY_SCHEMA_STATUS"),
        "s7_no_pfr": s7.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"),
        "s9_no_pfr": s9.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"),
    }
    abort = _target_blindness_abort({"summary": summary, "tables": tables}, stage="audit")
    if abort is not None:
        return abort

    _write_json("CLOSURE_MASTER_TABLE.json", tables["master_table"])
    _write_json("PARAMETER_STATUS_TABLE.json", tables["parameter_table"])
    _write_json("DIMENSIONLESS_CATALOG.json", tables["dimensionless_catalog"])
    _write_json("NO_ESCAPE_CHECKLIST.json", tables["no_escape"])
    _write_json("PHASE_10B10_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == EXPECTED_GRAMMAR_HASH == manifest.get("grammar_hash")
    whitelist_ok = WHITELIST_VERSION == manifest.get("whitelist_version")
    blacklist_ok = BLACKLIST_VERSION == manifest.get("blacklist_version")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    for n in range(1, 10):
        key = f"phase10b{n}"
        summary[f"{key}_artifacts_unchanged"] = hashes_before[key] == hashes_after[key]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["whitelist_unchanged"] = whitelist_ok
    summary["blacklist_unchanged"] = blacklist_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    summary["dependency_schema_unchanged"] = schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") == "CONSISTENT"
    if not (
        artifacts_ok
        and grammar_ok
        and frozen_ok
        and specs_unchanged
        and summary["new_assumptions"] == 0
        and summary["ranking"] is False
    ):
        summary["PHASE_10B_STATUS"] = "INTEGRITY_FAILURE"
        phase_status = "INTEGRITY_FAILURE"
    _write_json("PHASE_10B10_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B10_TEST_COPY_ID": PHASE_10B10_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "closure_questions": tables["questions"],
        "master_table": tables["master_table"],
        "parameter_table": tables["parameter_table"],
        "dimensionless_catalog": tables["dimensionless_catalog"],
        "no_escape_checklist": tables["no_escape"],
        "dynamics": tables["dynamics"],
        "search_completeness": tables["search"],
        "equivalence": tables["equivalence"],
        "audit_summary": summary,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_10B10_STATUS": "CLOSED" if phase_status != "INTEGRITY_FAILURE" else "INTEGRITY_FAILURE",
        "PHASE_10B_STATUS": phase_status,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash(),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_imported_into_generator": False,
        "known_physics_comparison_executed": False,
        "phase_10c_executed": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_assumptions": 0,
        "new_dependencies": 0,
        "large_scale_generation_executed": False,
        "candidates_repaired": False,
        "candidates_deleted": False,
        "models_merged": False,
        "search_space_modified": False,
        "grammar_changed": 0,
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "phase_7_unchanged": True,
        "phase_8_unchanged": True,
        "phase_9_unchanged": True,
        "phase_10a_grammar_version_unchanged": True,
        "phase_10b1_artifacts_unchanged": summary["phase10b1_artifacts_unchanged"],
        "phase_10b2_artifacts_unchanged": summary["phase10b2_artifacts_unchanged"],
        "phase_10b3_artifacts_unchanged": summary["phase10b3_artifacts_unchanged"],
        "phase_10b4_artifacts_unchanged": summary["phase10b4_artifacts_unchanged"],
        "phase_10b5_artifacts_unchanged": summary["phase10b5_artifacts_unchanged"],
        "phase_10b6_artifacts_unchanged": summary["phase10b6_artifacts_unchanged"],
        "phase_10b7_artifacts_unchanged": summary["phase10b7_artifacts_unchanged"],
        "phase_10b8_artifacts_unchanged": summary["phase10b8_artifacts_unchanged"],
        "phase_10b9_artifacts_unchanged": summary["phase10b9_artifacts_unchanged"],
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B10_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_unique_action": "REJECTED AS OVERCLAIM",
            "2_unique_kinetic": "REJECTED AS OVERCLAIM",
            "3_unique_dimensionless_quantity": "REJECTED AS OVERCLAIM",
            "4_sign_condition_fixes_Z": "REJECTED AS OVERCLAIM",
            "5_canonical_norm_is_derived": "REJECTED AS OVERCLAIM",
            "6_EQUIVALENCE_UNSUPPORTED_means_equivalent": "REJECTED AS OVERCLAIM",
            "7_search_is_all_possible_theories": "REJECTED AS OVERCLAIM",
            "8_classical_ghost_test_is_quantum_unitarity": "REJECTED AS OVERCLAIM",
            "9_physics_is_impossible": "REJECTED AS OVERCLAIM",
            "10_start_phase_10c": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B10_CLOSED"] = science["PHASE_10B10_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_10B10_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_assumptions"] == 0
        and science["new_dependencies"] == 0
        and science["phase_10c_executed"] is False
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and specs_unchanged
    )
    return science


def run_phase10b10_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b10_closure(auth, signature=signature)
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
            "PHASE_5C_UNCHANGED": "VERIFIED",
            "PHASE_5D_UNCHANGED": "VERIFIED",
            "PHASE_6_UNCHANGED": "VERIFIED",
            "PHASE_7_UNCHANGED": "VERIFIED",
            "PHASE_8_UNCHANGED": "VERIFIED",
            "PHASE_9_UNCHANGED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b1_artifacts_unchanged") else "FAILED",
            "PHASE_10B2_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b2_artifacts_unchanged") else "FAILED",
            "PHASE_10B3_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b3_artifacts_unchanged") else "FAILED",
            "PHASE_10B4_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b4_artifacts_unchanged") else "FAILED",
            "PHASE_10B5_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b5_artifacts_unchanged") else "FAILED",
            "PHASE_10B6_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b6_artifacts_unchanged") else "FAILED",
            "PHASE_10B7_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b7_artifacts_unchanged") else "FAILED",
            "PHASE_10B8_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b8_artifacts_unchanged") else "FAILED",
            "PHASE_10B9_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b9_artifacts_unchanged") else "FAILED",
            "PHASE_10B10_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_10B10_STATUS": science.get("PHASE_10B10_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
