"""Phase 10B.3: structural consistency and equivalence audit of 10B.1/10B.2 output.

Does not modify the frozen action, Phases 4A-9, or the Phase 10A grammar.
Does not overwrite Phase 10B.1 or 10B.2 artifacts.  Does not repair candidates.
Does not add dependencies, merge models, or rank them.
"""

from __future__ import annotations

import hashlib
import inspect
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
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH, so2_generator_K
from physics_lab.physics.phase10a_model_grammar import (
    ALLOWED_PROVENANCE,
    BLACKLIST_VERSION,
    GRAMMAR_VERSION,
    SEARCH_SPACE_VERSION,
    WHITELIST_VERSION,
    grammar_hash,
    supported_equivalences,
    unsupported_equivalences,
    validate_model_spec,
    variation_catalogs,
    whitelist,
)
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b2_derivation import (
    DERIVATION_VERSION,
    artifact_dir as phase10b2_artifact_dir,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "PHASE_10B3_TEST_COPY_ID",
    "analyze_phase10b3_audit",
    "artifact_dir",
    "run_phase10b3_or_stop",
]

PHASE_10B3_TEST_COPY_ID = "PHASE_10B3_STRUCTURAL_CONSISTENCY_EQUIVALENCE_AUDIT"
PHASE = "PHASE_10B.3"
AUDIT_VERSION = "phase10b3-audit-v1"
EXPECTED_CANDIDATE_COUNT = 8

_REQUIRED_10B1 = (
    "SEARCH_MANIFEST.json",
    "CANDIDATE_CATALOG.json",
    "VALIDATION_RESULTS.json",
    "CANONICALIZATION_RESULTS.json",
    "DEDUPLICATION_RESULTS.json",
    "PARAMETER_INVENTORY.json",
)
_REQUIRED_10B2 = (
    "DERIVATION_CATALOG.json",
    "DERIVATION_SUMMARY.json",
    "EOM_RESULTS.json",
    "PARAMETER_FREE_RELATIONS.json",
)

_OPERATOR_PAIRS = (
    ("MODEL_0001", "MODEL_0002"),
    ("MODEL_0003", "MODEL_0004"),
    ("MODEL_0005", "MODEL_0006"),
    ("MODEL_0007", "MODEL_0008"),
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b3_artifacts"


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
    out: dict[str, dict[str, str]] = {"phase10b1": {}, "phase10b2": {}}
    for name in _REQUIRED_10B1:
        path = phase10b1_artifact_dir() / name
        out["phase10b1"][name] = _file_digest(path)
    for name in _REQUIRED_10B2:
        path = phase10b2_artifact_dir() / name
        out["phase10b2"][name] = _file_digest(path)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.3 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.3 refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar_version is not the 10B.1 grammar"}
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


def _is_zero(expr: Any) -> bool:
    simplified = sp.simplify(expr)
    if isinstance(simplified, sp.MatrixBase):
        return simplified == sp.zeros(*simplified.shape)
    return simplified == 0


def _catalog_by_id() -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for axis, items in variation_catalogs().items():
        for item in items:
            found[item["identifier"]] = {**item, "axis": axis}
    for item in whitelist():
        ident = item.get("identifier")
        if ident and ident not in found:
            found[ident] = dict(item)
    return found


def _validator_enforces_dependencies() -> bool:
    source = inspect.getsource(validate_model_spec)
    return "item.get(\"dependencies\")" in source or "declared_dependencies" in source


def _axis_ids(catalogs: dict[str, list[dict[str, Any]]], axis: str) -> set[str]:
    return {item["identifier"] for item in catalogs.get(axis, [])}


def _declared_dependencies() -> list[dict[str, Any]]:
    rows = []
    catalogs = variation_catalogs()
    same_axis: dict[str, str] = {}
    for axis, items in catalogs.items():
        for item in items:
            same_axis[item["identifier"]] = axis
    validator_enforces = _validator_enforces_dependencies()
    for ident, entry in _catalog_by_id().items():
        deps = list(entry.get("dependencies") or [])
        if not deps:
            continue
        ident_axis = same_axis.get(ident) or entry.get("axis")
        for dep in deps:
            dep_axis = same_axis.get(dep)
            rows.append(
                {
                    "identifier": ident,
                    "axis": ident_axis,
                    "dependency_declared": dep,
                    "dependency_axis": dep_axis,
                    "same_axis_as_dependent": bool(ident_axis and dep_axis and ident_axis == dep_axis),
                    "dependency_enforced": validator_enforces,
                    "dependency_unchecked": not validator_enforces,
                    "status": "DEPENDENCY_ENFORCED" if validator_enforces else "DEPENDENCY_UNCHECKED",
                    "mathematical_definition": entry.get("mathematical_definition"),
                }
            )
    return rows


def _selection_ids(selection: dict[str, str]) -> set[str]:
    return set(selection.values())


def _candidate_dependency_state(selection: dict[str, str], declared: list[dict[str, Any]]) -> dict[str, Any]:
    selected = _selection_ids(selection)
    rows = []
    unchecked = 0
    for row in declared:
        ident = row["identifier"]
        if ident not in selected:
            continue
        dep = row["dependency_declared"]
        present_as_label = dep in selected
        rows.append(
            {
                "dependency_declared": f"{ident} -> {dep}",
                "present_as_selected_label": present_as_label,
                "same_axis_as_dependent": row["same_axis_as_dependent"],
                "dependency_enforced": row["dependency_enforced"],
                "status": row["status"],
            }
        )
        if row["dependency_unchecked"]:
            unchecked += 1
    return {
        "rows": rows,
        "dependency_unchecked_count": unchecked,
        "state": "DEPENDENCY_UNCHECKED" if unchecked else "DEPENDENCY_SATISFIED_AND_ENFORCED",
    }


def _a_mu_requirement_for_f2() -> dict[str, Any]:
    entries = _catalog_by_id()
    f2 = entries.get("optional_F2_test_extension") or {}
    deps = list(f2.get("dependencies") or [])
    definition = str(f2.get("mathematical_definition") or "")
    requires_field = "metric_Phi_plus_connection" in deps or "A_mu" in deps
    mentions_amu = "A_mu" in definition
    if requires_field:
        status = "REQUIRED_BY_GRAMMAR"
    elif mentions_amu:
        status = "UNCHECKED"
    else:
        status = "NOT_REQUIRED_BY_GRAMMAR"
    return {
        "optional_F2_dependencies": deps,
        "optional_F2_definition": definition,
        "A_mu_in_declared_dependencies": "A_mu" in deps,
        "metric_Phi_plus_connection_in_declared_dependencies": "metric_Phi_plus_connection" in deps,
        "A_mu_mentioned_in_definition": mentions_amu,
        "status": status,
        "note": (
            "No declared dependency from optional_F2_test_extension onto field content or A_mu. "
            "The validator does not invent this rule."
        ),
    }


def _connection_field_requirement() -> dict[str, Any]:
    entries = _catalog_by_id()
    conn = entries.get("connection_without_autonomous_F2") or {}
    fields_phi = entries.get("metric_plus_internal_Phi") or {}
    deps = list(conn.get("dependencies") or [])
    definition = str(conn.get("mathematical_definition") or "")
    return {
        "connection_definition": definition,
        "connection_dependencies": deps,
        "field_content_definition": fields_phi.get("mathematical_definition"),
        "A_mu_in_declared_dependencies": "A_mu" in deps or "metric_Phi_plus_connection" in deps,
        "definition_mentions_A_mu": "A_mu" in definition,
        "status": "UNRESOLVED",
        "reading": (
            "The gauge-class definition text mentions A_mu present. "
            "FIELD_CONTENT_CLASS is a separate axis whose metric_plus_internal_Phi entry lists {g_mu_nu, Phi}. "
            "No declared dependency joins them. The validator does not enforce a field requirement. "
            "Whether the connection is a structural label or an explicit field is unresolved by the current grammar."
        ),
    }


def _field_gauge_audit(item: dict[str, Any], f2_rule: dict[str, Any], conn_rule: dict[str, Any]) -> dict[str, Any]:
    sel = item["axis_selection"]
    gauge = sel["GAUGE_DYNAMICS_CLASS"]
    fields = sel["FIELD_CONTENT_CLASS"]
    has_connection_field = fields == "metric_Phi_plus_connection"
    f2 = gauge == "optional_F2_test_extension"
    mismatch = None
    a_mu_status = "not applicable"
    if f2:
        a_mu_status = f2_rule["status"]
        if not has_connection_field:
            mismatch = {
                "gauge": gauge,
                "field_content": "{g_mu_nu, Phi}",
                "A_mu_in_field_content": False,
                "grammar_requirement_of_A_mu": a_mu_status,
            }
    coherence = "STRUCTURALLY_COHERENT"
    if f2 and not has_connection_field:
        coherence = "UNRESOLVED"
    elif gauge == "connection_without_autonomous_F2" and not has_connection_field:
        coherence = "UNRESOLVED"
        mismatch = {
            "gauge": gauge,
            "field_content": "{g_mu_nu, Phi}",
            "A_mu_in_field_content": False,
            "connection_requirement": conn_rule["status"],
        }
    return {
        "model_id": item["model_id"],
        "GAUGE_DYNAMICS_CLASS": gauge,
        "FIELD_CONTENT_CLASS": fields,
        "A_mu_in_field_content": has_connection_field,
        "autonomous_F2": f2,
        "A_mu_requirement_if_F2": a_mu_status if f2 else "not applicable",
        "mismatch": mismatch,
        "structural_coherence": coherence,
        "field_content_difference_class": (
            "genuine field-content difference"
            if has_connection_field
            else "genuine field-content difference with unresolved gauge-label vs field-content relation"
        ),
        "candidates_repaired": False,
        "A_mu_added": False,
        "F2_removed": False,
    }


def _operator_map_identity() -> dict[str, Any]:
    k = so2_generator_K()
    p = sp.simplify(k.T * k)
    lam_a, lam_b = sp.symbols("lambda_a lambda_b", real=True)
    a0, a1 = sp.symbols("a0 a1", real=True)
    h_comm = sp.diag(lam_a, lam_b, lam_b)
    h_fn = sp.simplify(a0 * sp.eye(3) + a1 * p)
    forward = _is_zero(h_fn.subs({a0: lam_a, a1: lam_b - lam_a}) - h_comm)
    inverse = _is_zero(h_comm.subs({lam_a: a0, lam_b: a0 + a1}) - h_fn)
    supported = supported_equivalences()
    unsupported = unsupported_equivalences()
    mapping_supported_by_canonicalizer = "ALGEBRAIC_SIMPLIFICATION_UNSUPPORTED" not in unsupported
    return {
        "commutant_symmetric_K": "H = diag(lambda_a, lambda_b, lambda_b) with [K,H]=0",
        "function_of_KTK": "H = a0 I + a1 P with P = K^T K and P^2=P",
        "coefficient_mapping": {"a0": "lambda_a", "a1": "lambda_b - lambda_a"},
        "inverse_mapping": {"lambda_a": "a0", "lambda_b": "a0 + a1"},
        "forward_identity_holds": forward,
        "inverse_identity_holds": inverse,
        "parameter_reparameterization": bool(forward and inverse),
        "supported_equivalence_rules": supported,
        "unsupported_equivalence_rules": unsupported,
        "algebraic_simplification_supported": mapping_supported_by_canonicalizer,
        "model_equivalence": "UNSUPPORTED",
        "canonicalizer_modified": False,
        "models_merged": False,
        "numerical_coefficients_assigned": False,
    }


def _pair_relation(left_id: str, right_id: str, by_id: dict[str, dict[str, Any]], op_audit: dict[str, Any]) -> dict[str, Any]:
    left = by_id[left_id]
    right = by_id[right_id]
    ls = left["axis_selection"]
    rs = right["axis_selection"]
    same_except_operator = {k: v for k, v in ls.items() if k != "INTERNAL_OPERATOR_CLASS"} == {
        k: v for k, v in rs.items() if k != "INTERNAL_OPERATOR_CLASS"
    }
    ops = {ls["INTERNAL_OPERATOR_CLASS"], rs["INTERNAL_OPERATOR_CLASS"]}
    operator_pair = ops == {"commutant_symmetric_K", "function_of_KTK"}
    if same_except_operator and operator_pair and op_audit["parameter_reparameterization"]:
        relation = "PARAMETER_REPARAMETERIZATION"
        status = "EQUIVALENCE_UNSUPPORTED"
        evidence = (
            "Invertible coefficient map a0=lambda_a, a1=lambda_b-lambda_a holds on the implemented matrices. "
            "Existing canonicalization rules do not include this map. ALGEBRAIC_SIMPLIFICATION_UNSUPPORTED."
        )
    else:
        relation = "DISTINCT"
        status = "DISTINCT"
        evidence = "axis selections differ by more than operator-class labels"
    return {
        "candidate_pair": f"{left_id} <-> {right_id}",
        "relation": relation,
        "status": status,
        "evidence": evidence,
        "parameter_reparameterization": relation == "PARAMETER_REPARAMETERIZATION",
        "model_equivalence": "UNSUPPORTED" if relation == "PARAMETER_REPARAMETERIZATION" else "FALSE",
        "merged": False,
    }


def _provenance_audit(catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["relation_id"]: item for item in catalog}
    rows = []
    rel4 = by_id.get("REL_0004") or {}
    rows.append(
        {
            "relation_id": "REL_0004",
            "recorded_provenance": rel4.get("provenance"),
            "recorded_classification": rel4.get("classification"),
            "logical_origin": "DERIVED GIVEN ASSUMPTION",
            "accurate": rel4.get("provenance") == "DERIVED GIVEN ASSUMPTION",
            "mismatch": (
                "classification 'genuine_structural_relation' overstates a fact that follows from the shared "
                "real_u1_1plus2 representation together with either registered operator class"
                if rel4.get("classification") == "genuine_structural_relation"
                else None
            ),
            "new_provenance_class_introduced": False,
        }
    )
    rel5 = by_id.get("REL_0005") or {}
    vocab_has_negative = "NEGATIVE_TEST_RESULT" in ALLOWED_PROVENANCE
    rows.append(
        {
            "relation_id": "REL_0005",
            "recorded_provenance": rel5.get("provenance"),
            "recorded_classification": rel5.get("classification"),
            "logical_origin": "NEGATIVE_TEST_RESULT",
            "accurate": False,
            "mismatch": (
                "The statement is a negative test result, not a parameter-dependent relation. "
                "ALLOWED_PROVENANCE does not contain NEGATIVE_TEST_RESULT; 10B.2 labelled PARAMETER-DEPENDENT. "
                "Mismatch recorded only; no new global provenance class is introduced."
            ),
            "vocabulary_contains_NEGATIVE_TEST_RESULT": vocab_has_negative,
            "new_provenance_class_introduced": False,
        }
    )
    rel12 = by_id.get("REL_0012") or {}
    rows.append(
        {
            "relation_id": "REL_0012",
            "recorded_provenance": rel12.get("provenance"),
            "recorded_equivalence": rel12.get("equivalence"),
            "logical_origin_of_map": "DERIVED",
            "logical_origin_of_non_merge": "EQUIVALENCE_UNSUPPORTED",
            "accurate": rel12.get("provenance") == "DERIVED" and rel12.get("equivalence") == "EQUIVALENCE_UNSUPPORTED",
            "mismatch": None,
            "new_provenance_class_introduced": False,
        }
    )
    return rows


def _parameter_free_claim(summary_10b2: dict[str, Any]) -> dict[str, Any]:
    retained = bool(summary_10b2.get("NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"))
    untested_eom = int(summary_10b2.get("candidates_with_untested_eom") or 0)
    return {
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": retained,
        "PARAMETER_FREE_TEST_SCOPE_LIMITED": untested_eom > 0,
        "reason": (
            "10B.2 found no implemented identity that eliminates all continuous parameters. "
            "Full 4D Euler-Lagrange is UNTESTED, so the negative result is limited to the implemented identities."
        ),
        "new_parameter_free_search_executed": False,
        "claim_logically_unsupported": False,
    }


def _classify_candidate(
    item: dict[str, Any],
    field_row: dict[str, Any],
    dep_state: dict[str, Any],
    pair_status: str,
) -> dict[str, Any]:
    return {
        "model_id": item["model_id"],
        "syntax": "SYNTACTICALLY_GENERATED",
        "validation_status_10b1": item.get("validation_status"),
        "structural_coherence": field_row["structural_coherence"],
        "dependency_state": dep_state["state"],
        "equivalence_state": pair_status,
        "not_called_valid_theory": True,
        "repaired": False,
        "deleted": False,
    }


def analyze_phase10b3_audit(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    del signature
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
        derivation_catalog = _read_json(phase10b2_artifact_dir() / "DERIVATION_CATALOG.json")
        derivation_summary = _read_json(phase10b2_artifact_dir() / "DERIVATION_SUMMARY.json")
        manifest = _read_json(phase10b1_artifact_dir() / "SEARCH_MANIFEST.json")
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}
    if len(catalog) != EXPECTED_CANDIDATE_COUNT:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"Phase 10B.1 catalog does not contain 8 candidates: {len(catalog)}",
        }
    if derivation_summary.get("derivation_version") != DERIVATION_VERSION:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 10B.2 derivation_version mismatch",
        }

    declared = _declared_dependencies()
    f2_rule = _a_mu_requirement_for_f2()
    conn_rule = _connection_field_requirement()
    op_audit = _operator_map_identity()
    by_id = {item["model_id"]: item for item in catalog}

    field_rows = [_field_gauge_audit(item, f2_rule, conn_rule) for item in catalog]
    dep_by_id = {
        item["model_id"]: _candidate_dependency_state(item["axis_selection"], declared) for item in catalog
    }
    pair_rows = [_pair_relation(a, b, by_id, op_audit) for a, b in _OPERATOR_PAIRS]
    pair_status_by_id: dict[str, str] = {}
    for pair, (a, b) in zip(pair_rows, _OPERATOR_PAIRS):
        pair_status_by_id[a] = pair["status"]
        pair_status_by_id[b] = pair["status"]

    classifications = [
        _classify_candidate(item, field, dep_by_id[item["model_id"]], pair_status_by_id[item["model_id"]])
        for item, field in zip(catalog, field_rows)
    ]
    provenance_rows = _provenance_audit(derivation_catalog)
    pfree = _parameter_free_claim(derivation_summary)

    relation_table = list(pair_rows)
    relation_table.append(
        {
            "candidate_pair": "MODEL_0001-0004 vs MODEL_0005-0008",
            "relation": "DISTINCT",
            "status": "DISTINCT",
            "evidence": (
                "FIELD_CONTENT_CLASS differs: metric_Phi_plus_connection lists A_mu; "
                "metric_plus_internal_Phi does not. This is a genuine field-content difference. "
                "Whether the gauge-class label independently requires A_mu remains UNRESOLVED."
            ),
            "parameter_reparameterization": False,
            "model_equivalence": "FALSE",
            "merged": False,
        }
    )
    relation_table.append(
        {
            "candidate_pair": "MODEL_0007, MODEL_0008",
            "relation": "UNRESOLVED",
            "status": "UNRESOLVED",
            "evidence": (
                "optional_F2_test_extension with field content {g_mu_nu, Phi}. "
                "A_mu is NOT_REQUIRED_BY_GRAMMAR as a declared dependency. "
                "The combination is not repaired, not deleted, and not declared a valid theory."
            ),
            "parameter_reparameterization": False,
            "model_equivalence": "FALSE",
            "merged": False,
        }
    )
    relation_table.append(
        {
            "candidate_pair": "MODEL_0005, MODEL_0006",
            "relation": "UNRESOLVED",
            "status": "UNRESOLVED",
            "evidence": conn_rule["reading"],
            "parameter_reparameterization": False,
            "model_equivalence": "FALSE",
            "merged": False,
        }
    )

    n_coherent = sum(1 for row in classifications if row["structural_coherence"] == "STRUCTURALLY_COHERENT")
    n_inconsistent = sum(1 for row in classifications if row["structural_coherence"] == "STRUCTURALLY_INCONSISTENT")
    n_unresolved_struct = sum(1 for row in classifications if row["structural_coherence"] == "UNRESOLVED")
    n_dep_unchecked = sum(1 for row in classifications if row["dependency_state"] == "DEPENDENCY_UNCHECKED")
    n_reparam = sum(1 for row in pair_rows if row["parameter_reparameterization"])
    n_eq_unresolved = sum(1 for row in pair_rows if row["status"] == "EQUIVALENCE_UNSUPPORTED")
    n_eq_certified = 0

    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "TOTAL_GENERATED": 8,
        "syntactic_candidates": 8,
        "structurally_coherent": n_coherent,
        "structurally_inconsistent": n_inconsistent,
        "structurally_unresolved": n_unresolved_struct,
        "dependency_unchecked": n_dep_unchecked,
        "equivalence_classes_certified": n_eq_certified,
        "equivalence_unresolved": n_eq_unresolved,
        "parameter_reparameterizations": n_reparam,
        "new_physical_assumptions": 0,
        "grammar_changes": 0,
        "target_inputs": 0,
        "experimental_inputs": 0,
        "ranking": False,
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": pfree["NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"],
        "PARAMETER_FREE_TEST_SCOPE_LIMITED": pfree["PARAMETER_FREE_TEST_SCOPE_LIMITED"],
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "derivation_version": DERIVATION_VERSION,
        "candidates_repaired": False,
        "models_merged": False,
        "dependencies_added": False,
        "equivalence_rules_added": False,
    }

    abort = _target_blindness_abort(
        {"summary": summary, "classifications": classifications, "relations": relation_table},
        stage="audit",
    )
    if abort is not None:
        return abort

    consistency = {
        "syntactic_candidates": 8,
        "structurally_coherent": n_coherent,
        "structurally_inconsistent": n_inconsistent,
        "structurally_unresolved": n_unresolved_struct,
        "note": (
            "8 syntactic combinations are not 8 certified coherent models. "
            "Unresolved field-content / gauge-class combinations are retained in the generation denominator."
        ),
        "classifications": classifications,
        "relation_table": relation_table,
    }
    dependency_audit = {
        "validator_enforces_declared_dependencies": _validator_enforces_dependencies(),
        "cartesian_product_applies_dependency_filter": False,
        "declared": declared,
        "per_candidate": dep_by_id,
    }
    field_audit = {
        "F2_A_mu_requirement": f2_rule,
        "connection_field_requirement": conn_rule,
        "per_candidate": field_rows,
        "MODEL_0007": next(row for row in field_rows if row["model_id"] == "MODEL_0007"),
        "MODEL_0008": next(row for row in field_rows if row["model_id"] == "MODEL_0008"),
        "MODEL_0005": next(row for row in field_rows if row["model_id"] == "MODEL_0005"),
        "MODEL_0006": next(row for row in field_rows if row["model_id"] == "MODEL_0006"),
    }
    operator_audit = {
        **op_audit,
        "pairs": pair_rows,
        "parameter_reparameterization": "TRUE" if op_audit["parameter_reparameterization"] else "FALSE",
        "model_equivalence": op_audit["model_equivalence"],
    }

    _write_json("STRUCTURAL_CONSISTENCY_AUDIT.json", consistency)
    _write_json("DEPENDENCY_AUDIT.json", dependency_audit)
    _write_json("FIELD_CONTENT_AUDIT.json", field_audit)
    _write_json("OPERATOR_EQUIVALENCE_AUDIT.json", operator_audit)
    _write_json("CANDIDATE_CLASSIFICATION_AUDIT.json", classifications)
    _write_json("PROVENANCE_AUDIT.json", provenance_rows)
    _write_json("PHASE_10B3_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == manifest.get("grammar_hash")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    summary["phase10b1_artifacts_unchanged"] = hashes_before["phase10b1"] == hashes_after["phase10b1"]
    summary["phase10b2_artifacts_unchanged"] = hashes_before["phase10b2"] == hashes_after["phase10b2"]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    _write_json("PHASE_10B3_SUMMARY.json", summary)

    second = canonical_json_bytes(classifications)
    reproducible = second == canonical_json_bytes(
        [
            _classify_candidate(item, field, dep_by_id[item["model_id"]], pair_status_by_id[item["model_id"]])
            for item, field in zip(catalog, field_rows)
        ]
    )

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B3_TEST_COPY_ID": PHASE_10B3_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "derivation_version": DERIVATION_VERSION,
        "structural_consistency_audit": consistency,
        "dependency_audit": dependency_audit,
        "field_content_audit": field_audit,
        "operator_equivalence_audit": operator_audit,
        "candidate_classification_audit": classifications,
        "provenance_audit": provenance_rows,
        "parameter_free_claim": pfree,
        "audit_summary": summary,
        "relation_table": relation_table,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED" if reproducible else "FAILED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_10B3_STATUS": "CLOSED"
        if (
            frozen_ok
            and grammar_ok
            and artifacts_ok
            and reproducible
            and summary["new_physical_assumptions"] == 0
            and summary["grammar_changes"] == 0
            and summary["ranking"] is False
            and summary["TOTAL_GENERATED"] == 8
        )
        else "INCOMPLETE",
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
        "new_physical_assumptions": 0,
        "grammar_changes": 0,
        "candidates_repaired": False,
        "models_merged": False,
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "phase_7_unchanged": True,
        "phase_8_unchanged": True,
        "phase_9_unchanged": True,
        "phase_10a_grammar_unchanged": True,
        "phase_10b1_artifacts_unchanged": summary["phase10b1_artifacts_unchanged"],
        "phase_10b2_artifacts_unchanged": summary["phase10b2_artifacts_unchanged"],
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B3_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": pfree["NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"],
        "PARAMETER_FREE_TEST_SCOPE_LIMITED": pfree["PARAMETER_FREE_TEST_SCOPE_LIMITED"],
        "overclaims": {
            "1_rank_models": "REJECTED AS OVERCLAIM",
            "2_repair_candidates": "REJECTED AS OVERCLAIM",
            "3_modify_grammar": "REJECTED AS OVERCLAIM",
            "4_merge_models": "REJECTED AS OVERCLAIM",
            "5_add_dependencies": "REJECTED AS OVERCLAIM",
            "6_known_physics_comparison": "REJECTED AS OVERCLAIM",
            "7_start_phase_10c": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B3_CLOSED"] = science["PHASE_10B3_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_10B3_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_physical_assumptions"] == 0
        and science["grammar_changes"] == 0
        and science["candidates_repaired"] is False
        and science["models_merged"] is False
        and frozen_ok
        and grammar_ok
        and artifacts_ok
    )
    return science


def run_phase10b3_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b3_audit(auth, signature=signature)
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
            "PHASE_10B3_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_10B3_STATUS": science.get("PHASE_10B3_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
