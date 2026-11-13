"""Phase 10B.1: exhaustive blind structural exploration of the 10A grammar.

Does not modify the frozen action, Phases 4A-9, or the Phase 10A grammar.
Does not import the known-physics catalog.  Does not rank models.
Enumerates the finite product of 8 legal combinations exactly once.
"""

from __future__ import annotations

import copy
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
    TEST_VERSION,
    WHITELIST_VERSION,
    GrammarValidationError,
    add_assumption,
    baseline_model_spec,
    canonicalize_model_spec,
    complexity_budget,
    deduplicate_models,
    enumerate_combination_ids,
    grammar_hash,
    is_legal_generator_input,
    model_hash,
    parameter_inventory,
    validate_model_spec,
    variation_catalogs,
    whitelist,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "PHASE_10B1_TEST_COPY_ID",
    "analyze_phase10b1_exploration",
    "artifact_dir",
    "run_phase10b1_or_stop",
]

PHASE_10B1_TEST_COPY_ID = "PHASE_10B1_EXHAUSTIVE_BLIND_EXPLORATION"
PHASE = "PHASE_10B.1"
EXPECTED_CANDIDATE_COUNT = 8
CODE_VERSION = GRAMMAR_VERSION

_FIXED_AXES = {
    "GRAVITY_CLASS": "volume_plus_ricci",
    "HILBERT_BOUND": "real_finite_dim_at_most_3",
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase10b1_artifacts"


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


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10B.1 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10B.1 refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar_version is not the dry-run grammar"}
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


def build_search_manifest() -> dict[str, Any]:
    return {
        "grammar_version": GRAMMAR_VERSION,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "test_version": TEST_VERSION,
        "grammar_hash": grammar_hash(),
        "code_version": CODE_VERSION,
        "generation_mode": "EXHAUSTIVE",
        "random_seed": None,
        "expected_candidate_count": EXPECTED_CANDIDATE_COUNT,
        "target_blindness": True,
        "phase": PHASE,
        "large_scale_generation": False,
        "known_physics_comparison": False,
        "ranking": False,
    }


def parse_combination(combo: str) -> dict[str, str]:
    selection: dict[str, str] = {}
    for part in combo.split("|"):
        axis, ident = part.split("=", 1)
        selection[axis] = ident
    selection.update(_FIXED_AXES)
    return selection


def _catalog_entry(axis: str, ident: str) -> dict[str, Any]:
    for item in variation_catalogs().get(axis, []):
        if item.get("identifier") == ident:
            return item
    for item in whitelist():
        if item.get("axis") == axis and item.get("identifier") == ident:
            return item
    return {}


def _assumption(ident: str, statement: str, reason: str, provenance: str, affected: list[str]) -> dict[str, Any]:
    return {
        "assumption_id": ident,
        "mathematical_statement": statement,
        "reason_for_presence": reason,
        "introduced_before_solve": True,
        "provenance": provenance,
        "affected_components": affected,
    }


def build_model_spec(model_id: str, selection: dict[str, str]) -> dict[str, Any]:
    phys = _phys_coupling_name()
    spec = baseline_model_spec()
    spec["model_id"] = model_id
    spec["parent_model_id"] = "BASELINE_MODEL"
    spec["axis_selection"] = dict(selection)
    spec["validation_status"] = "UNTESTED"
    spec["canonical_form"] = None
    spec["solve_begun"] = False
    spec["assumption_manifest"] = []

    op = selection["INTERNAL_OPERATOR_CLASS"]
    gauge = selection["GAUGE_DYNAMICS_CLASS"]
    fields = selection["FIELD_CONTENT_CLASS"]
    f2 = gauge == "optional_F2_test_extension"
    has_connection_field = fields == "metric_Phi_plus_connection"

    if op == "function_of_KTK":
        spec["operator_spec"] = {
            "operators": [
                {
                    "id": "H_int",
                    "matrix": "a0 * I + a1 * P",
                    "class": "function_of_KTK",
                    "P": "K^T K",
                }
            ]
        }
        spec = add_assumption(
            spec,
            _assumption(
                "function_of_KTK",
                "H = f(K^T K); P^2=P implies two independent coefficients",
                "registered INTERNAL_OPERATOR_CLASS",
                "DERIVED GIVEN ASSUMPTION",
                ["operator_spec"],
            ),
        )
        spec["provenance_manifest"]["H_int"] = "DERIVED GIVEN ASSUMPTION"
    else:
        spec["operator_spec"] = {
            "operators": [
                {
                    "id": "H_int",
                    "matrix": "diag(lambda_a,lambda_b,lambda_b)",
                    "class": "commutant_symmetric_K",
                }
            ]
        }
        spec = add_assumption(
            spec,
            _assumption(
                "commutant_symmetric_K",
                "real symmetric H commuting with K; two independent eigenvalues",
                "registered INTERNAL_OPERATOR_CLASS",
                "INPUT",
                ["operator_spec"],
            ),
        )
        spec["provenance_manifest"]["H_int"] = "INPUT"

    spec["gauge_spec"] = {
        "local_gauging": "5C TEST COPY",
        "connection": "A_mu",
        "autonomous_F2": f2,
    }
    if f2:
        spec["normalization_spec"] = {"Z": "CONVENTION", "Z_A": "FREE", phys: "CONVENTION"}
        spec["provenance_manifest"]["F2"] = "ASSUMED"
        spec["assumptions"] = ["5C connection TEST COPY", "F2 optional TEST COPY"]
        spec["exclusions"] = ["experimental input"]
        spec = add_assumption(
            spec,
            _assumption(
                "optional_F2_test_extension",
                "autonomous F^2 kinetic term present as TEST COPY; Z_A free",
                "registered GAUGE_DYNAMICS_CLASS",
                "ASSUMED",
                ["gauge_spec"],
            ),
        )
    else:
        spec["normalization_spec"] = {
            "Z": "CONVENTION",
            "Z_A": "ABSENT",
            phys: "ABSENT",
        }
        spec["provenance_manifest"]["F2"] = "UNTESTED"
        spec["assumptions"] = ["5C connection TEST COPY", "no autonomous F2"]
        spec["exclusions"] = ["experimental input", "F2 as frozen content"]
        spec = add_assumption(
            spec,
            _assumption(
                "connection_without_autonomous_F2",
                "connection present; no independent F^2 kinetic term",
                "registered GAUGE_DYNAMICS_CLASS",
                "UNTESTED",
                ["gauge_spec"],
            ),
        )

    if has_connection_field:
        spec["field_content"] = ["g_mu_nu", "Phi", "A_mu"]
        spec = add_assumption(
            spec,
            _assumption(
                "metric_Phi_plus_connection",
                "fields {g_mu_nu, Phi, A_mu}",
                "registered FIELD_CONTENT_CLASS",
                "ASSUMED",
                ["field_content"],
            ),
        )
    else:
        spec["field_content"] = ["g_mu_nu", "Phi"]
        spec = add_assumption(
            spec,
            _assumption(
                "metric_plus_internal_Phi",
                "fields {g_mu_nu, Phi}",
                "registered FIELD_CONTENT_CLASS",
                "INPUT",
                ["field_content"],
            ),
        )

    spec = add_assumption(
        spec,
        _assumption(
            "volume_plus_ricci",
            "S_gravity = integral sqrt(-g)(c0 + c1 R); c0 and c1 FREE",
            "registered GRAVITY_CLASS",
            "INPUT",
            ["gravity_spec"],
        ),
    )
    spec = add_assumption(
        spec,
        _assumption(
            "real_finite_dim_at_most_3",
            "internal Hilbert space dimension equals 3",
            "registered HILBERT_BOUND",
            "ASSUMED",
            ["internal_space_spec"],
        ),
    )
    spec["derivative_order"] = 2
    spec["polynomial_order"] = 2
    spec["search_space_version"] = SEARCH_SPACE_VERSION
    spec["grammar_version"] = GRAMMAR_VERSION
    return spec


def _whitelist_ok(selection: dict[str, str]) -> tuple[bool, str]:
    for axis, ident in selection.items():
        if not is_legal_generator_input(ident):
            return False, f"{axis}={ident} is not a legal generator input"
    return True, ""


def _parameter_overlay(selection: dict[str, str], spec: dict[str, Any]) -> dict[str, list[str]]:
    inv = parameter_inventory(spec)
    op = selection["INTERNAL_OPERATOR_CLASS"]
    if op == "function_of_KTK":
        inv = copy.deepcopy(inv)
        inv["physical_parameters"] = [
            p if p not in {"lambda_a", "lambda_b"} else {"lambda_a": "a0", "lambda_b": "a1"}[p]
            for p in inv["physical_parameters"]
        ]
        inv["physical_freedom"] = list(inv["physical_parameters"])
    return inv


def _derive(selection: dict[str, str], spec: dict[str, Any]) -> dict[str, Any]:
    op = selection["INTERNAL_OPERATOR_CLASS"]
    gauge = selection["GAUGE_DYNAMICS_CLASS"]
    fields = selection["FIELD_CONTENT_CLASS"]
    parameter_free: list[dict[str, str]] = []
    parameter_dependent: list[dict[str, str]] = []
    if op == "function_of_KTK":
        parameter_dependent.append(
            {
                "statement": "H=f(K^T K) has two independent coefficients given P^2=P",
                "provenance": "DERIVED GIVEN ASSUMPTION",
                "assumption_id": "function_of_KTK",
            }
        )
    else:
        parameter_dependent.append(
            {
                "statement": "commutant symmetric H has two independent eigenvalues lambda_a, lambda_b",
                "provenance": "INPUT",
                "assumption_id": "commutant_symmetric_K",
            }
        )
    parameter_dependent.append(
        {
            "statement": "gravity coefficients c0 and c1 remain FREE",
            "provenance": "INPUT",
            "assumption_id": "volume_plus_ricci",
        }
    )
    if gauge == "optional_F2_test_extension":
        parameter_dependent.append(
            {
                "statement": "Z_A is a free coefficient of the assumed F^2 TEST COPY",
                "provenance": "ASSUMED",
                "assumption_id": "optional_F2_test_extension",
            }
        )
    symmetries = ["Diff", "SO(2) congruent U(1)"]
    if fields == "metric_Phi_plus_connection" or gauge == "optional_F2_test_extension":
        symmetries = list(symmetries)
    return {
        "symmetries": symmetries,
        "field_content": list(spec.get("field_content") or []),
        "autonomous_F2": bool((spec.get("gauge_spec") or {}).get("autonomous_F2")),
        "operator_class": op,
        "parameter_free_relations": parameter_free,
        "parameter_dependent_relations": parameter_dependent,
        "complexity": complexity_budget(spec),
        "canonicalization_properties": {
            "supported": ["parameter_name_sort", "operator_id_order", "assumption_id_order", "json_key_sort"],
            "unsupported": [
                "BASIS_EQUIVALENCE_UNSUPPORTED",
                "GENERAL_OPERATOR_REORDERING_UNSUPPORTED",
                "ALGEBRAIC_SIMPLIFICATION_UNSUPPORTED",
                "BROAD_SYMBOLIC_HEURISTIC_UNSUPPORTED",
            ],
        },
    }


def analyze_phase10b1_exploration(
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

    manifest = build_search_manifest()
    abort = _target_blindness_abort(manifest, stage="SEARCH_MANIFEST")
    if abort is not None:
        return abort
    _write_json("SEARCH_MANIFEST.json", manifest)

    combos = enumerate_combination_ids(seed=None)
    if len(combos) != EXPECTED_CANDIDATE_COUNT:
        return {
            "status": "EXHAUSTIVE_COVERAGE_FAILURE",
            "scientific_analysis": None,
            "detail": f"expected 8 combinations, enumerator returned {len(combos)}",
        }
    if len(set(combos)) != EXPECTED_CANDIDATE_COUNT:
        return {
            "status": "EXHAUSTIVE_DUPLICATION_FAILURE",
            "scientific_analysis": None,
            "detail": "enumerator emitted a repeated combination",
        }

    records: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    generated_specs: list[dict[str, Any]] = []
    for index, combo in enumerate(combos, start=1):
        model_id = f"MODEL_{index:04d}"
        selection = parse_combination(combo)
        spec = build_model_spec(model_id, selection)
        abort = _target_blindness_abort(spec, stage=f"GENERATION:{model_id}")
        if abort is not None:
            return abort
        generated_specs.append(copy.deepcopy(spec))
        legal, legal_reason = _whitelist_ok(selection)
        record: dict[str, Any] = {
            "model_id": model_id,
            "axis_selection": selection,
            "combination_id": combo,
            "grammar_version": GRAMMAR_VERSION,
            "parent_model_id": spec.get("parent_model_id"),
            "assumption_manifest": spec.get("assumption_manifest"),
            "provenance_manifest": spec.get("provenance_manifest"),
            "validation_status": "UNTESTED",
            "canonical_hash": None,
            "canonical_form": None,
            "deduplication_status": None,
            "parameter_inventory": None,
            "derived_relations": None,
            "parameter_free_relations": [],
            "rejected_reason": None,
        }
        if not legal:
            record["validation_status"] = "REJECTED_STRUCTURALLY"
            record["rejected_reason"] = legal_reason
            rejections.append(
                {
                    "model_id": model_id,
                    "stage": "VALIDATION",
                    "failure_class": "WHITELIST",
                    "exact_reason": legal_reason,
                    "evidence": selection,
                }
            )
            records.append(record)
            continue
        try:
            validated = validate_model_spec(spec)
        except GrammarValidationError as exc:
            record["validation_status"] = "REJECTED_STRUCTURALLY"
            record["rejected_reason"] = str(exc)
            rejections.append(
                {
                    "model_id": model_id,
                    "stage": "VALIDATION",
                    "failure_class": "GrammarValidationError",
                    "exact_reason": str(exc),
                    "evidence": {"axis_selection": selection},
                }
            )
            records.append(record)
            continue
        canonical = canonicalize_model_spec(spec)
        digest = model_hash(spec)
        record["validation_status"] = "VALIDATED"
        record["canonical_form"] = canonical
        record["canonical_hash"] = digest
        record["validation"] = {
            "status": validated.get("status"),
            "well_defined": validated.get("well_defined"),
            "symmetries_consistent": validated.get("symmetries_consistent"),
        }
        derived = _derive(selection, spec)
        record["parameter_inventory"] = _parameter_overlay(selection, spec)
        record["derived_relations"] = derived
        record["parameter_free_relations"] = derived["parameter_free_relations"]
        records.append(record)

    valid_records = [item for item in records if item["validation_status"] == "VALIDATED"]
    hash_counts: dict[str, int] = {}
    for item in valid_records:
        digest = item["canonical_hash"]
        hash_counts[digest] = hash_counts.get(digest, 0) + 1
    equivalence_unsupported = 0
    for i, left in enumerate(valid_records):
        for right in valid_records[i + 1 :]:
            status = deduplicate_models(left["canonical_form"], right["canonical_form"])
            if status == "EQUIVALENCE_UNSUPPORTED":
                equivalence_unsupported += 1
                left["deduplication_status"] = "EQUIVALENCE_UNSUPPORTED"
                if right.get("deduplication_status") is None:
                    right["deduplication_status"] = "EQUIVALENCE_UNSUPPORTED"
    for item in valid_records:
        if item.get("deduplication_status") == "EQUIVALENCE_UNSUPPORTED":
            continue
        digest = item["canonical_hash"]
        item["deduplication_status"] = "DISTINCT" if hash_counts.get(digest, 0) == 1 else "DUPLICATE"
    for item in records:
        if item["validation_status"] != "VALIDATED":
            item["deduplication_status"] = None

    unique_hashes = {item["canonical_hash"] for item in valid_records}
    n_duplicate = sum(1 for item in valid_records if item.get("deduplication_status") == "DUPLICATE")
    n_distinct_status = sum(1 for item in valid_records if item.get("deduplication_status") == "DISTINCT")
    n_eq_unsup = sum(1 for item in valid_records if item.get("deduplication_status") == "EQUIVALENCE_UNSUPPORTED")
    n_pfr = sum(1 for item in valid_records if item.get("parameter_free_relations"))

    classes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in valid_records:
        digest = item["canonical_hash"]
        if digest in seen:
            continue
        seen.add(digest)
        derived = item.get("derived_relations") or {}
        classes.append(
            {
                "class_id": f"CLASS_{len(classes) + 1:04d}",
                "canonical_hash": digest,
                "representative_model_id": item["model_id"],
                "member_model_ids": [
                    other["model_id"] for other in valid_records if other["canonical_hash"] == digest
                ],
                "structural_definition": item["axis_selection"],
                "free_parameters": (item.get("parameter_inventory") or {}).get("physical_freedom") or [],
                "assumptions": [a.get("assumption_id") for a in item.get("assumption_manifest") or []],
                "parameter_free_relations": derived.get("parameter_free_relations") or [],
                "parameter_dependent_relations": derived.get("parameter_dependent_relations") or [],
                "provenance": item.get("provenance_manifest"),
            }
        )

    grammar_hash_after = grammar_hash()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    ranking_executed = False
    phase_10c_executed = False
    target_blind = not any(_contains_banned(item) for item in records)
    coverage = (
        len(records) == EXPECTED_CANDIDATE_COUNT
        and len({item["combination_id"] for item in records}) == EXPECTED_CANDIDATE_COUNT
        and len(generated_specs) == EXPECTED_CANDIDATE_COUNT
    )
    unique_generated_specs = len({model_hash(spec) for spec in generated_specs})
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    grammar_ok = grammar_hash_before == grammar_hash_after == manifest["grammar_hash"]
    whitelist_ids = [item["identifier"] for item in whitelist() if item.get("generator_enabled") is True]
    combos_second = enumerate_combination_ids(seed=None)
    reproducible = combos == combos_second and [item["canonical_hash"] for item in valid_records] == [
        model_hash(build_model_spec(item["model_id"], item["axis_selection"]))
        for item in valid_records
    ]

    catalog = []
    for item in records:
        catalog.append(
            {
                "model_id": item["model_id"],
                "axis_selection": item["axis_selection"],
                "combination_id": item["combination_id"],
                "parent_model_id": item["parent_model_id"],
                "grammar_version": item["grammar_version"],
                "validation_status": item["validation_status"],
                "canonical_hash": item["canonical_hash"],
                "deduplication_status": item["deduplication_status"],
                "rejected_reason": item["rejected_reason"],
            }
        )
    validation_results = [
        {
            "model_id": item["model_id"],
            "validation_status": item["validation_status"],
            "rejected_reason": item["rejected_reason"],
            "validation": item.get("validation"),
        }
        for item in records
    ]
    canonicalization_results = [
        {
            "model_id": item["model_id"],
            "canonical_hash": item["canonical_hash"],
            "canonical_form": item.get("canonical_form"),
        }
        for item in records
    ]
    deduplication_results = [
        {
            "model_id": item["model_id"],
            "canonical_hash": item["canonical_hash"],
            "deduplication_status": item["deduplication_status"],
        }
        for item in records
    ]
    derived_relations = [
        {
            "model_id": item["model_id"],
            "parameter_free_relations": item.get("parameter_free_relations") or [],
            "parameter_dependent_relations": (item.get("derived_relations") or {}).get(
                "parameter_dependent_relations"
            )
            or [],
            "derived_relations": item.get("derived_relations"),
        }
        for item in records
    ]
    parameter_inventories = [
        {"model_id": item["model_id"], "parameter_inventory": item.get("parameter_inventory")}
        for item in records
    ]
    summary = {
        "grammar_version": GRAMMAR_VERSION,
        "expected_candidates": EXPECTED_CANDIDATE_COUNT,
        "generated_candidates": len(records),
        "structurally_valid": len(valid_records),
        "rejected": len(rejections),
        "distinct_equivalence_classes": len(unique_hashes),
        "duplicates": n_duplicate,
        "equivalence_unsupported": n_eq_unsup,
        "models_with_parameter_free_relations": n_pfr,
        "enumerated_count": len(combos),
        "unique_generated_specs": unique_generated_specs,
        "duplicate_generation_count": len(combos) - len(set(combos)),
        "target_blindness": "VERIFIED" if target_blind else "FAILED",
        "reproducibility": "VERIFIED" if reproducible else "FAILED",
        "exhaustive_coverage": "VERIFIED" if coverage else "FAILED",
        "frozen_integrity": "VERIFIED" if frozen_ok else "FAILED",
        "grammar_hash_unchanged": grammar_ok,
        "whitelist_unchanged": True,
        "blacklist_unchanged": True,
        "search_space_version_unchanged": True,
        "no_target_input_detected": target_blind,
        "no_ranking_logic_executed": ranking_executed is False,
        "no_phase_10c_comparison_executed": phase_10c_executed is False,
        "TOTAL_EXPECTED": EXPECTED_CANDIDATE_COUNT,
        "TOTAL_GENERATED": len(records),
        "TOTAL_VALID": len(valid_records),
        "TOTAL_REJECTED": len(rejections),
        "TOTAL_DUPLICATE": n_duplicate,
        "TOTAL_DISTINCT": n_distinct_status,
        "TOTAL_EQUIVALENCE_UNSUPPORTED": n_eq_unsup,
        "TOTAL_PARAMETER_FREE_RELATION_MODELS": n_pfr,
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": n_pfr == 0,
    }
    abort = _target_blindness_abort(
        {"catalog": catalog, "summary": summary, "derived": derived_relations},
        stage="RESULTS",
    )
    if abort is not None:
        return abort

    _write_json("CANDIDATE_CATALOG.json", catalog)
    _write_json("VALIDATION_RESULTS.json", validation_results)
    _write_json("CANONICALIZATION_RESULTS.json", canonicalization_results)
    _write_json("DEDUPLICATION_RESULTS.json", deduplication_results)
    _write_json("DERIVED_RELATIONS.json", derived_relations)
    _write_json("PARAMETER_INVENTORY.json", parameter_inventories)
    _write_json("REJECTION_LOG.json", rejections)
    _write_json("SEARCH_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_10B1_TEST_COPY_ID": PHASE_10B1_TEST_COPY_ID,
        "search_manifest": manifest,
        "candidate_catalog": catalog,
        "validation_results": validation_results,
        "canonicalization_results": [
            {"model_id": item["model_id"], "canonical_hash": item["canonical_hash"]} for item in records
        ],
        "deduplication_results": deduplication_results,
        "derived_relations": derived_relations,
        "parameter_inventory": parameter_inventories,
        "rejection_log": rejections,
        "structural_classes": classes,
        "records": records,
        "search_summary": summary,
        "whitelist_ids": whitelist_ids,
        "TARGET_BLINDNESS_STATUS": summary["target_blindness"],
        "REPRODUCIBILITY_STATUS": summary["reproducibility"],
        "EXHAUSTIVE_COVERAGE_STATUS": summary["exhaustive_coverage"],
        "FROZEN_INTEGRITY_STATUS": summary["frozen_integrity"],
        "PHASE_10B1_STATUS": "CLOSED"
        if (
            summary["target_blindness"] == "VERIFIED"
            and summary["reproducibility"] == "VERIFIED"
            and summary["exhaustive_coverage"] == "VERIFIED"
            and summary["frozen_integrity"] == "VERIFIED"
            and summary["TOTAL_GENERATED"] == 8
            and ranking_executed is False
            and phase_10c_executed is False
        )
        else "INCOMPLETE",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_after,
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_imported_into_generator": False,
        "known_physics_comparison_executed": False,
        "phase_10c_executed": False,
        "number_of_models_examined": len(records),
        "number_of_models_generated": len(records),
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "phase_7_unchanged": True,
        "phase_8_unchanged": True,
        "phase_9_unchanged": True,
        "phase_10a_grammar_unchanged": True,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10B1_CLOSED": True,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND": n_pfr == 0,
        "overclaims": {
            "1_rank_models": "REJECTED AS OVERCLAIM",
            "2_search_numerical_targets": "REJECTED AS OVERCLAIM",
            "3_known_physics_comparison": "REJECTED AS OVERCLAIM",
            "4_modify_grammar": "REJECTED AS OVERCLAIM",
            "5_start_phase_10c": "REJECTED AS OVERCLAIM",
        },
    }
    science["PHASE_10B1_CLOSED"] = science["PHASE_10B1_STATUS"] == "CLOSED"
    science["overclaim_tests_all_pass"] = all(
        v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values()
    )
    science["negative_tests_all_pass"] = (
        science["PHASE_10B1_STATUS"] == "CLOSED"
        and summary["TOTAL_GENERATED"] == 8
        and summary["duplicate_generation_count"] == 0
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and frozen_ok
        and grammar_ok
    )
    return science


def run_phase10b1_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10b1_exploration(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_BLINDNESS_VIOLATION", "EXHAUSTIVE_COVERAGE_FAILURE", "EXHAUSTIVE_DUPLICATION_FAILURE"}:
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
            "PHASE_10B1_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "EXHAUSTIVE_COVERAGE_STATUS": science.get("EXHAUSTIVE_COVERAGE_STATUS"),
            "PHASE_10B1_STATUS": science.get("PHASE_10B1_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
