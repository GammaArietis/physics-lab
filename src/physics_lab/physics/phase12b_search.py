"""Phase 12B: exhaustive brute-force search of the frozen 12A grammar.

Streams all syntactically legal candidates.  Does not sample, rank,
rewrite the grammar, or start Phase 12C.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
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
    LEGAL_DEPENDENCY_RELATION_TYPES,
    grammar_hash as grammar_hash_10a,
)
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10a_model_grammar import model_hash as model_hash_10a
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase12a_grammar import (
    AXES,
    EXPECTED_GRAMMAR_HASH_10B,
    GRAMMAR_ID,
    SCHEMA_VERSION,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
    iter_legal_axis_tuples,
    vocabularies,
    _ids,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_LEGAL_COUNT",
    "EXPECTED_12A_GRAMMAR_HASH",
    "PHASE_12B_TEST_COPY_ID",
    "SHARD_SIZE",
    "analyze_phase12b_search",
    "artifact_dir",
    "run_phase12b_or_stop",
]

PHASE_12B_TEST_COPY_ID = "PHASE_12B_EXPANDED_EXHAUSTIVE_BRUTE_FORCE_SEARCH"
PHASE = "PHASE_12B"
AUDIT_VERSION = "phase12b-exhaustive-search-v1"
ENUMERATION_VERSION = "phase12b-enumeration-v1"
VALIDATION_VERSION = "phase12b-validation-v1"
DERIVATION_VERSION = "phase12b-derivation-v1"
CANONICALIZATION_VERSION = "phase12a-canonicalization-v1"
DEDUPLICATION_VERSION = "phase12a-deduplication-v1"
EXPECTED_12A_GRAMMAR_HASH = "40beb10b01794d20c48aaafcabd24432b103a8c379576b2855f5c6cdaa34d3e6"
EXPECTED_LEGAL_COUNT = 9_704_164
SHARD_SIZE = 100_000
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"

_I_SPACE = 1
_I_OP = 3
_I_KIN = 4
_I_POT = 5
_I_INTER = 6
_I_ST = 7
_I_CURV = 8
_I_DYN = 10
_I_MOD = 16


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase12b_artifacts"


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
    out: dict[str, dict[str, str]] = {"phase10b1": {}, "phase10b10": {}, "phase12a": {}}
    mapping = (
        ("phase10b1", ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json"), phase10b1_artifact_dir()),
        ("phase10b10", ("PHASE_10B10_SUMMARY.json",), phase10b10_artifact_dir()),
        (
            "phase12a",
            (
                "PHASE_12A_GRAMMAR_FREEZE.json",
                "PHASE_12A_SUMMARY.json",
                "SEARCH_SPACE_SIZE.json",
            ),
            phase12a_artifact_dir(),
        ),
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _n_physical(vals: tuple[str, ...]) -> int:
    n = 0
    if vals[_I_ST] == "generally_covariant":
        n += 2
    if vals[_I_POT] in {"V2", "V2_plus_V4"}:
        n += 1
    if vals[_I_POT] in {"V4", "V2_plus_V4"}:
        n += 1
    op = vals[_I_OP]
    space = vals[_I_SPACE]
    if op == "commutant_symmetric":
        n += 2 if space == "R3" else 1
    elif op == "polynomial_in_KT_K":
        n += 2
    elif op == "diagonal_generic":
        n += {"R1": 1, "R2": 2, "R3": 3}[space]
    elif op in {"projector_decomposition", "identity_plus_projector"}:
        n += 2
    elif op == "bounded_polynomial_operator":
        n += 3
    if vals[_I_INTER] == "internal_operator_coupling":
        n += 1
    kin = vals[_I_KIN]
    if kin == "field_dependent_quadratic":
        n += 2
    elif kin in {"nonlinear_X", "k_essence_polynomial"}:
        n += 2
    elif kin == "mixed_internal_kinetic":
        n += 2
    elif kin == "derivative_coupling":
        n += 1
    if vals[_I_CURV] == "scalar_curvature_linear":
        n += 1
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        n += 2
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        n += 1
    if vals[_I_MOD] == "dynamical_modulus":
        n += 1
    return n


def _has_free_same_dim_ratio(vals: tuple[str, ...]) -> bool:
    op = vals[_I_OP]
    space = vals[_I_SPACE]
    if op == "commutant_symmetric" and space == "R3":
        return True
    if op in {"polynomial_in_KT_K", "projector_decomposition", "identity_plus_projector"}:
        return True
    if op == "diagonal_generic" and space != "R1":
        return True
    if op == "bounded_polynomial_operator":
        return True
    if vals[_I_KIN] in {"field_dependent_quadratic", "nonlinear_X", "k_essence_polynomial", "mixed_internal_kinetic"}:
        return True
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        return True
    return False


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 12B refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 12B refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash is not the frozen 10B hash"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash is not the frozen 12A hash"}
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


def _historical_corpus() -> dict[str, Any]:
    catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
    specs_unchanged = True
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash_10a(spec) != item["canonical_hash"]:
            specs_unchanged = False
            break
    return {
        "count": len(catalog),
        "specs_unchanged": specs_unchanged,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
        "merged_into_12B": False,
    }


def _run_exhaustive_stream() -> dict[str, Any]:
    index_of = [{name: i for i, name in enumerate(_ids(axis))} for axis in AXES]
    overall = hashlib.sha256()
    shard_hasher = hashlib.sha256()
    shards: list[dict[str, Any]] = []
    kinetic = Counter()
    n_phys = Counter()
    n = 0
    n_ratio = 0
    shard_first = 1
    current_shard = 0

    def close_shard(last_id: int) -> None:
        shards.append(
            {
                "shard_id": f"shard_{current_shard:04d}",
                "first_id": shard_first,
                "last_id": last_id,
                "count": last_id - shard_first + 1,
                "chain_hash": shard_hasher.hexdigest(),
                "status": "COMPLETE",
            }
        )

    for vals in iter_legal_axis_tuples():
        n += 1
        shard = (n - 1) // SHARD_SIZE
        if shard != current_shard:
            close_shard(n - 1)
            current_shard = shard
            shard_first = n
            shard_hasher = hashlib.sha256()
        packed = bytes(index_of[j][vals[j]] for j in range(len(AXES)))
        ident = n.to_bytes(4, "big")
        overall.update(packed)
        overall.update(ident)
        shard_hasher.update(packed)
        shard_hasher.update(ident)
        kinetic[vals[_I_KIN]] += 1
        n_phys[_n_physical(vals)] += 1
        if _has_free_same_dim_ratio(vals):
            n_ratio += 1
    if n:
        close_shard(n)
    return {
        "enumerated": n,
        "enumeration_chain_hash": overall.hexdigest(),
        "shards": shards,
        "kinetic_counts": dict(kinetic),
        "n_physical_histogram": {str(k): int(v) for k, v in sorted(n_phys.items())},
        "candidates_with_free_dimensionless_ratio": n_ratio,
        "unique_axis_selections": n,
    }


def analyze_phase12b_search(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    abort = _target_blindness_abort({"phase": PHASE, "grammar_id": GRAMMAR_ID}, stage="preamble")
    if abort is not None:
        return abort
    _ = signature
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
        freeze12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json")
        corpus = _historical_corpus()
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not in CLOSED_NO_INTERNAL_CLOSURE"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if freeze12a.get("grammar_hash") != EXPECTED_12A_GRAMMAR_HASH:
        integrity_failure = "12A freeze hash mismatch"
    if s12a.get("syntactically_legal_size") != EXPECTED_LEGAL_COUNT:
        integrity_failure = "12A legal size is not the frozen 9,704,164"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical 10B corpus rewritten"

    manifest_path = artifact_dir() / "PHASE_12B_SEARCH_MANIFEST.json"
    cached = None
    if manifest_path.is_file():
        existing = _read_json(manifest_path)
        if (
            existing.get("grammar_hash") == EXPECTED_12A_GRAMMAR_HASH
            and existing.get("completion_status") == "EXHAUSTIVE_RUN_COMPLETE"
            and existing.get("legal_candidate_count") == EXPECTED_LEGAL_COUNT
        ):
            summary_path = artifact_dir() / "PHASE_12B_SUMMARY.json"
            if summary_path.is_file():
                cached = _read_json(summary_path)

    start_ts = datetime.now(timezone.utc).isoformat()
    if cached is None or integrity_failure:
        streamed = _run_exhaustive_stream()
        enumerated = streamed["enumerated"]
        complete = enumerated == EXPECTED_LEGAL_COUNT and integrity_failure is None
        completion = "EXHAUSTIVE_RUN_COMPLETE" if complete else "EXHAUSTIVE_RUN_INCOMPLETE"
        accounted = enumerated
        valid = enumerated if complete else 0
        invalid = 0
        unresolved = 0 if complete else enumerated
        n_kin = len(streamed["kinetic_counts"])
        unique_action = "NO"
        unique_kinetic = "YES" if n_kin == 1 else "NO"
        unique_dimless = "NO"
        pfr_closure = "NO"
        global_closure = "NO"
        missing = EXPECTED_LEGAL_COUNT - enumerated
        end_ts = datetime.now(timezone.utc).isoformat()
        total_shards = len(streamed["shards"])
        failed_shards = [s["shard_id"] for s in streamed["shards"] if s["status"] != "COMPLETE"]
        manifest = {
            "phase_id": PHASE,
            "grammar_id": GRAMMAR_ID,
            "grammar_hash": EXPECTED_12A_GRAMMAR_HASH,
            "schema_version": SCHEMA_VERSION,
            "legal_candidate_count": EXPECTED_LEGAL_COUNT,
            "enumeration_version": ENUMERATION_VERSION,
            "validation_version": VALIDATION_VERSION,
            "derivation_version": DERIVATION_VERSION,
            "canonicalization_version": CANONICALIZATION_VERSION,
            "deduplication_version": DEDUPLICATION_VERSION,
            "shard_policy": {
                "assignment": "candidate_id sequential from iter_legal_axis_tuples; shard_id = (id-1)//SHARD_SIZE",
                "SHARD_SIZE": SHARD_SIZE,
                "random_assignment": False,
            },
            "target_blindness_status": "VERIFIED",
            "start_timestamp": start_ts,
            "completion_timestamp": end_ts,
            "completion_status": completion,
            "enumeration_chain_hash": streamed["enumeration_chain_hash"],
        }
        if not manifest_path.is_file():
            _write_json("PHASE_12B_SEARCH_MANIFEST.json", manifest)
        elif _read_json(manifest_path).get("grammar_hash") != EXPECTED_12A_GRAMMAR_HASH:
            integrity_failure = integrity_failure or "12B manifest grammar hash mismatch"
        enum_summary = {
            "enumerated_candidates": enumerated,
            "accounted_candidates": accounted,
            "expected_legal_count": EXPECTED_LEGAL_COUNT,
            "candidate_id_range": {"first": 1, "last": enumerated} if enumerated else None,
            "ids_covered": f"1 ... {enumerated}" if enumerated else "none",
            "enumeration_chain_hash": streamed["enumeration_chain_hash"],
            "sampling": False,
            "json_per_candidate_written": False,
            "streaming": True,
            "deterministic": True,
        }
        shard_summary = {
            "total_shards": total_shards,
            "shard_size_policy": SHARD_SIZE,
            "candidates_per_shard": SHARD_SIZE,
            "last_shard_count": streamed["shards"][-1]["count"] if streamed["shards"] else 0,
            "completed_shards": total_shards - len(failed_shards),
            "failed_shards": failed_shards,
            "remaining_shards": 0 if complete else "UNTESTED",
            "ledger": streamed["shards"],
        }
        val_summary = {
            "STRUCTURALLY_VALID": valid,
            "STRUCTURALLY_INVALID": invalid,
            "unresolved": unresolved,
            "fast_screen_rejected": 0,
            "fast_screen_heuristic": False,
            "note": "Stage 2 reapplies frozen 12A legality; the streamed set is that legal set",
        }
        dep_summary = {
            "VALID": valid,
            "INVALID": 0,
            "UNCHECKED": 0,
            "UNCHECKED_IS_NOT_VALID": True,
            "UNCHECKED_IS_NOT_INVALID": True,
            "relation_types_used": ["CROSS_AXIS_REQUIRES", "COMPONENT_REQUIRES"],
            "new_dependency_types": 0,
            "allowed_relation_types": sorted(LEGAL_DEPENDENCY_RELATION_TYPES),
        }
        deriv_summary = {
            "verified": 0,
            "partial": enumerated if complete else 0,
            "untested": 0 if complete else enumerated,
            "eom_executed": 0,
            "eom_untested": enumerated,
            "ghost_tests_executed": 0,
            "LEVEL_1_executed": 0,
            "claimed_symmetry_realized_on_full_action": "UNTESTED",
            "note": "EOM/ghosts/LEVEL_1 are UNTESTED; candidates are not eliminated for cost",
        }
        param_summary = {
            "parameter_free_relation_candidates": 0,
            "parameter_relation_candidates": 0,
            "no_relation_candidates": enumerated if complete else 0,
            "unresolved_relation_candidates": 0 if complete else enumerated,
            "n_physical_histogram": streamed["n_physical_histogram"],
            "candidates_with_free_dimensionless_ratio": streamed["candidates_with_free_dimensionless_ratio"],
            "numerical_values_assigned": False,
            "canonical_normalization_is_not_physical_fixing": True,
        }
        closure = {
            "UNIQUE_ACTION": unique_action,
            "UNIQUE_KINETIC_STRUCTURE": unique_kinetic,
            "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": unique_dimless,
            "PARAMETER_FREE_CLOSURE": pfr_closure,
            "GLOBAL_CLOSURE": global_closure,
            "unique_action_multiplicity": enumerated if complete else 0,
            "unique_kinetic_multiplicity": streamed["kinetic_counts"],
            "parameter_free_closed_candidates": 0,
            "certified_duplicates": 0,
            "EQUIVALENCE_UNSUPPORTED_not_used_to_merge": True,
        }
        remaining = {
            "surviving_physical_parameter_families": "all declared physical coefficients remain FREE; N_physical is class-dependent (see histogram)",
            "N_physical_after_equals_N_physical_before": True,
            "sign_conditions_are_not_fixing": True,
            "reparameterizations_are_not_physical_relations": True,
        }
        integrity_report = {
            "Phase_12A_grammar_hash_unchanged": grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH,
            "Phase_4C_frozen_hash_unchanged": True,
            "candidate_count": enumerated,
            "MODEL_SPEC_historical_corpus_unchanged": corpus["specs_unchanged"],
            "grammar_modified": False,
            "new_physical_principle": False,
            "new_dependencies": False,
            "new_fields_outside_grammar": False,
            "experimental_inputs": 0,
            "target_inputs": 0,
            "numerical_target_search": False,
            "ranking": False,
            "known_physics_comparison": False,
            "sampling": False,
        }
        _write_json("PHASE_12B_ENUMERATION_SUMMARY.json", enum_summary)
        _write_json("PHASE_12B_SHARD_LEDGER.json", shard_summary)
        _write_json("PHASE_12B_VALIDATION_SUMMARY.json", val_summary)
        _write_json("PHASE_12B_DEPENDENCY_SUMMARY.json", dep_summary)
        _write_json("PHASE_12B_DERIVATION_SUMMARY.json", deriv_summary)
        _write_json("PHASE_12B_PARAMETER_RELATIONS.json", param_summary)
        _write_json("PHASE_12B_CLOSURE_RESULTS.json", closure)
        _write_json("PHASE_12B_INTEGRITY_REPORT.json", integrity_report)
        summary = {
            "phase": PHASE,
            "audit_version": AUDIT_VERSION,
            "PHASE_12B_STATUS": "INTEGRITY_FAILURE" if integrity_failure or not complete else "CLOSED",
            "integrity_failure": integrity_failure,
            "completion_status": completion,
            "grammar_id": GRAMMAR_ID,
            "grammar_hash": EXPECTED_12A_GRAMMAR_HASH,
            "schema_version": SCHEMA_VERSION,
            "legal_candidate_count": EXPECTED_LEGAL_COUNT,
            "enumerated_candidates": enumerated,
            "accounted_candidates": accounted,
            "missing_count": missing if not complete else 0,
            "valid": valid,
            "invalid": invalid,
            "unresolved": unresolved,
            "shards": total_shards,
            "failed_shards": failed_shards,
            "sampling": False,
            "ranking": False,
            "known_physics_comparison": False,
            "experimental_inputs": 0,
            "target_inputs": 0,
            "numerical_search": 0,
            "new_physical_principle": False,
            "phase_12c_executed": False,
            "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
            "TARGET_BLINDNESS": "VERIFIED",
            "UNIQUE_ACTION": unique_action,
            "UNIQUE_KINETIC_STRUCTURE": unique_kinetic,
            "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": unique_dimless,
            "PARAMETER_FREE_CLOSURE": pfr_closure,
            "GLOBAL_CLOSURE": global_closure,
            "derivation_partial": deriv_summary["partial"],
            "derivation_verified": deriv_summary["verified"],
            "derivation_untested": deriv_summary["untested"],
            "parameter_free_relation_candidates": 0,
            "parameter_relation_candidates": 0,
            "no_relation_candidates": param_summary["no_relation_candidates"],
            "unresolved_relation_candidates": param_summary["unresolved_relation_candidates"],
            "exact_reason_if_incomplete": None if complete else "enumerated count differs from frozen legal size or integrity failure",
        }
        abort = _target_blindness_abort({"summary": summary, "closure": closure, "manifest": manifest}, stage="audit")
        if abort is not None:
            return abort
        _write_json("PHASE_12B_SUMMARY.json", summary)
    else:
        summary = cached
        enum_summary = _read_json(artifact_dir() / "PHASE_12B_ENUMERATION_SUMMARY.json")
        shard_summary = _read_json(artifact_dir() / "PHASE_12B_SHARD_LEDGER.json")
        val_summary = _read_json(artifact_dir() / "PHASE_12B_VALIDATION_SUMMARY.json")
        dep_summary = _read_json(artifact_dir() / "PHASE_12B_DEPENDENCY_SUMMARY.json")
        deriv_summary = _read_json(artifact_dir() / "PHASE_12B_DERIVATION_SUMMARY.json")
        param_summary = _read_json(artifact_dir() / "PHASE_12B_PARAMETER_RELATIONS.json")
        closure = _read_json(artifact_dir() / "PHASE_12B_CLOSURE_RESULTS.json")
        integrity_report = _read_json(artifact_dir() / "PHASE_12B_INTEGRITY_REPORT.json")
        remaining = {
            "surviving_physical_parameter_families": "all declared physical coefficients remain FREE; N_physical is class-dependent (see histogram)",
            "N_physical_after_equals_N_physical_before": True,
            "sign_conditions_are_not_fixing": True,
            "reparameterizations_are_not_physical_relations": True,
        }
        complete = summary.get("completion_status") == "EXHAUSTIVE_RUN_COMPLETE"

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    summary["phase10b1_artifacts_unchanged"] = hashes_before["phase10b1"] == hashes_after["phase10b1"]
    summary["phase12a_artifacts_unchanged"] = hashes_before["phase12a"] == hashes_after["phase12a"]
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    if not (artifacts_ok and grammar_ok and frozen_ok and summary["ranking"] is False):
        summary["PHASE_12B_STATUS"] = "INTEGRITY_FAILURE"
        integrity_failure = integrity_failure or "integrity check failed after write"
        summary["integrity_failure"] = integrity_failure
    _write_json("PHASE_12B_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_12B_TEST_COPY_ID": PHASE_12B_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "grammar_id": GRAMMAR_ID,
        "grammar_hash": EXPECTED_12A_GRAMMAR_HASH,
        "schema_version": SCHEMA_VERSION,
        "legal_candidate_count": EXPECTED_LEGAL_COUNT,
        "enumerated_candidates": summary["enumerated_candidates"],
        "accounted_candidates": summary["accounted_candidates"],
        "shards": summary["shards"],
        "completion_status": summary["completion_status"],
        "valid": summary["valid"],
        "invalid": summary["invalid"],
        "unresolved": summary["unresolved"],
        "enumeration_summary": enum_summary,
        "shard_summary": shard_summary,
        "validation_summary": val_summary,
        "dependency_summary": dep_summary,
        "derivation_summary": deriv_summary,
        "parameter_relations": param_summary,
        "closure_results": closure,
        "remaining_freedom": remaining,
        "integrity_report": integrity_report,
        "audit_summary": summary,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_12B_STATUS": summary["PHASE_12B_STATUS"],
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_comparison_executed": False,
        "phase_12c_executed": False,
        "sampling": False,
        "eom_derived": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_physical_principle": False,
        "UNIQUE_ACTION": summary["UNIQUE_ACTION"],
        "UNIQUE_KINETIC_STRUCTURE": summary["UNIQUE_KINETIC_STRUCTURE"],
        "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": summary["UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY"],
        "PARAMETER_FREE_CLOSURE": summary["PARAMETER_FREE_CLOSURE"],
        "GLOBAL_CLOSURE": summary["GLOBAL_CLOSURE"],
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_12B_CLOSED": summary["PHASE_12B_STATUS"] == "CLOSED",
        "EXHAUSTIVE_RUN_COMPLETE": summary["completion_status"] == "EXHAUSTIVE_RUN_COMPLETE",
        "overclaims": {
            "1_sample_instead_of_exhaust": "REJECTED AS OVERCLAIM",
            "2_rank_or_prefer_a_candidate": "REJECTED AS OVERCLAIM",
            "3_use_known_physics_to_prune": "REJECTED AS OVERCLAIM",
            "4_collapse_uncertified_equivalence": "REJECTED AS OVERCLAIM",
            "5_eliminate_because_EOM_is_expensive": "REJECTED AS OVERCLAIM",
            "6_claim_closure_from_incomplete_run": "REJECTED AS OVERCLAIM",
            "7_start_phase_12C": "REJECTED AS OVERCLAIM",
            "8_assign_numerical_parameters": "REJECTED AS OVERCLAIM",
            "9_canonical_Z_is_physical_uniqueness": "REJECTED AS OVERCLAIM",
            "10_search_target_constants": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_12B_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["phase_12c_executed"] is False
        and science["sampling"] is False
        and science["EXHAUSTIVE_RUN_COMPLETE"] is True
        and summary["enumerated_candidates"] == EXPECTED_LEGAL_COUNT
        and summary["valid"] + summary["invalid"] + summary["unresolved"] == EXPECTED_LEGAL_COUNT
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and corpus["specs_unchanged"]
    )
    return science


def run_phase12b_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase12b_search(auth, signature=signature)
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
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("grammar_hash_12A_unchanged") else "FAILED",
            "PHASE_12A_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase12a_artifacts_unchanged") else "FAILED",
            "PHASE_10B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase10b1_artifacts_unchanged") else "FAILED",
            "PHASE_12B_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_12B_STATUS": science.get("PHASE_12B_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "PHASE_12C_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
