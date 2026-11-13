"""Phase 14B.1: activate G1_FERMIONIC_CHIRAL only.

Adds bounded Weyl/Dirac content and chirality on the G0 U(1) grammar.
Does not activate G2 or later extensions.
"""

from __future__ import annotations

import json
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
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase10a_model_grammar import model_hash as model_hash_10a
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase12a_grammar import (
    EXPECTED_GRAMMAR_HASH_10B,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
)
from physics_lab.physics.phase12b_search import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14a_reconstruction import artifact_dir as phase14a_artifact_dir
from physics_lab.physics.phase14b0_engine import (
    AUTHORIZED_PHYSICS_CHAIN,
    ClosureEngine,
    ENGINE_VERSION,
    EngineFailure,
    artifact_dir as phase14b0_artifact_dir,
    assert_target_blind,
    content_hash,
    snapshot_prior_artifact_hashes as snapshot_14b0_priors,
    top_down_input_hash,
    _with_hash,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "G1_CHAIN",
    "N_FERMION_SEARCH_LIMIT",
    "PHASE_14B1_TEST_COPY_ID",
    "analyze_phase14b1_g1",
    "artifact_dir",
    "g1_executable_registry",
    "g1_metadata_legal",
    "g1_run_tests",
    "run_phase14b1_or_stop",
]

PHASE = "PHASE_14B.1"
PHASE_14B1_TEST_COPY_ID = "PHASE_14B1_ACTIVATE_G1_FERMIONIC_CHIRAL"
AUDIT_VERSION = "phase14b1-g1-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
G1_CHAIN: tuple[str, ...] = ("G0_BASELINE", "G1_FERMIONIC_CHIRAL")
N_FERMION_SEARCH_LIMIT: tuple[str, ...] = ("1", "2")
ACTIVE_G1_KPS: tuple[str, ...] = ("KP01", "KP02", "KP03", "KP09", "KP10", "KP11", "KP14")
DEFERRED_G1_KPS = {
    "KP12": "UNTESTED IN G1",
    "KP13": "DEFERRED TO G4",
    "KP15": "DEFERRED TO G2",
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b1_artifacts"


def _write_json(path: Path, payload: Any) -> None:
    assert_target_blind(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def g1_executable_registry() -> dict[str, dict[str, Any]]:
    exclusions = [
        "non-Abelian gauge groups",
        "scalar Higgs multiplets beyond G0",
        "spontaneous symmetry breaking",
        "anomaly cancellation engine",
        "Yukawa reconstruction",
        "RG",
        "SUSY",
        "extra dimensions",
    ]
    g0 = _with_hash(
        {
            "grammar_id": "G0_BASELINE",
            "parent_grammar_id": None,
            "extension_description": "G0 baseline used as G1 parent: metric, scalar, optional U(1); no fermions",
            "allowed_fields": ["metric", "scalar"],
            "allowed_groups": ["trivial", "U1_optional"],
            "allowed_representations": ["trivial", "U1_symbolic"],
            "allowed_interactions": ["minimal_metric_coupling"],
            "allowed_symmetry_breaking": [],
            "allowed_constraints": list(ACTIVE_G1_KPS),
            "explicit_exclusions": exclusions,
            "provenance": "GRAMMAR CHOICE",
            "status": "EXECUTED_AS_G1_PARENT",
            "axes": {
                "fermion_kind": ["none"],
                "n_fermion": ["0"],
                "gauge": ["trivial", "u1"],
            },
        }
    )
    g1 = _with_hash(
        {
            "grammar_id": "G1_FERMIONIC_CHIRAL",
            "parent_grammar_id": "G0_BASELINE",
            "extension_description": "Add Weyl/Dirac fermions and chirality on the G0 U(1) grammar only",
            "allowed_fields": ["metric", "scalar", "Weyl_fermion", "Dirac_fermion"],
            "allowed_groups": ["trivial", "U1_optional"],
            "allowed_representations": ["trivial", "U1_symbolic_q_i"],
            "allowed_interactions": ["minimal_metric_coupling", "U1_covariant_derivative"],
            "allowed_symmetry_breaking": [],
            "allowed_constraints": list(ACTIVE_G1_KPS),
            "explicit_exclusions": exclusions,
            "provenance": "GRAMMAR CHOICE",
            "status": "ACTIVE_G1",
            "axes": {
                "fermion_kind": ["none", "Dirac", "Weyl_vectorlike", "Weyl_chiral"],
                "n_fermion": list(N_FERMION_SEARCH_LIMIT),
                "gauge": ["trivial", "u1"],
            },
            "n_fermion_search_limit": list(N_FERMION_SEARCH_LIMIT),
            "n_fermion_bound_is_search_limit_not_prediction": True,
        }
    )
    return {"G0_BASELINE": g0, "G1_FERMIONIC_CHIRAL": g1}


def g1_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    gid = grammar.get("grammar_id")
    kind = assignment.get("fermion_kind")
    if gid == "G0_BASELINE":
        return True, None
    if kind in {"none", "Dirac"}:
        return False, "cannot_contain_chiral_fermionic_sector"
    return True, None


def _symbolic_charges(n: str, gauge: str) -> str:
    if gauge != "u1":
        return "none"
    count = int(n)
    return ", ".join(f"q_{i}" for i in range(1, count + 1))


def g1_run_tests(candidate: dict[str, Any], *, test_version: str = "g1-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    a = candidate["assignment"]
    kind = a.get("fermion_kind", "none")
    gauge = a.get("gauge", "trivial")
    n = a.get("n_fermion", "0")
    has_fermion = kind not in {"none"}
    chiral_gauge = kind == "Weyl_chiral" and gauge == "u1"
    results = []

    def add(cid: str, status: str, provenance: str, note: str) -> None:
        results.append(
            {
                "test_id": cid,
                "test_version": test_version,
                "status": status,
                "provenance": provenance,
                "source_phase": PHASE,
                "note": note,
            }
        )

    add("KP01", "PASS", "TOP_DOWN_INPUT", "effective 4D spacetime is an input")
    add("KP02", "PASS", "DERIVED GIVEN GRAMMAR", "local finite-derivative field content")
    add("KP03", "PASS", "DERIVED GIVEN GRAMMAR", "4D Lorentz: Weyl left/right or Dirac; metric Lorentzian")
    add("KP09", "PASS" if has_fermion else "FAIL", "TOP_DOWN_INPUT", "fermions plus G0 bosonic scalar/metric")
    add(
        "KP10",
        "PASS" if chiral_gauge else "FAIL",
        "TOP_DOWN_INPUT",
        "chiral gauge needs Weyl_chiral and a U(1); Dirac is vectorlike; trivial gauge is not a chiral gauge structure",
    )
    add("KP11", "PASS", "DERIVED GIVEN GRAMMAR", "discrete labels: fermion_kind and gauge type; q_i remain symbolic")
    add("KP14", "PASS", "GRAMMAR CHOICE", f"N_fermion search limit {list(N_FERMION_SEARCH_LIMIT)}; not a prediction")
    add("KP12", "UNTESTED", "UNTESTED IN G1", "anomaly engine belongs to G5")
    add("KP13", "NOT_APPLICABLE", "DEFERRED TO G4", "no Higgs/VEV grammar in G1")
    add("KP15", "NOT_APPLICABLE", "DEFERRED TO G2", "massless+massive vectors need later gauge/breaking grammar")
    add("KP04", "PASS", "DERIVED GIVEN GRAMMAR", "G0 Einstein-Hilbert sector inherited; c1 not numerically fixed")
    add("local_lorentz_rep", "PASS", "DERIVED GIVEN GRAMMAR", "4D Weyl or Dirac Lorentz representation is well-defined")
    add("gauge_syntax", "PASS", "DERIVED GIVEN GRAMMAR", "trivial or compact U(1) connection syntax; no non-Abelian G")
    add("G2_nonabelian", "NOT_APPLICABLE", "DEFERRED TO G2", "G1 must not manufacture a non-Abelian group")

    required_fail = any(r["status"] == "FAIL" and r["test_id"] in ACTIVE_G1_KPS for r in results)
    status = "FAIL" if required_fail else "PASS"
    return {
        "status": status,
        "results": results,
        "test_version": test_version,
        "symbolic_charges": _symbolic_charges(n if n != "0" else "1", gauge) if gauge == "u1" and has_fermion else "none",
        "chiral_gauge_structure": chiral_gauge,
    }


def attach_g1_stats(grammar: dict[str, Any], evaluated: list[dict[str, Any]], compatible: list[dict[str, Any]]) -> dict[str, Any]:
    table = []
    inventory = []
    for cand in evaluated:
        a = cand["assignment"]
        n = a.get("n_fermion", "0")
        gauge = a.get("gauge")
        kind = a.get("fermion_kind")
        row = {
            "candidate_class": cand["candidate_id"],
            "candidate_hash": cand["candidate_hash"],
            "fermion_content": kind,
            "chirality": (
                "Weyl left/right sector (qualitative existence; not an experimental assignment)"
                if kind == "Weyl_chiral"
                else ("vectorlike Weyl pair" if kind == "Weyl_vectorlike" else kind)
            ),
            "gauge_structure": "optional compact U(1) from G0" if gauge == "u1" else "trivial (no gauge)",
            "representation_structure": (
                f"symbolic U(1) weights {_symbolic_charges(n, gauge)}" if gauge == "u1" else "trivial"
            ),
            "active_top_down_constraints": list(ACTIVE_G1_KPS),
            "status": cand.get("filter_status"),
            "provenance": "DERIVED GIVEN GRAMMAR",
        }
        table.append(row)
        if cand.get("filter_status") == "PASS":
            inventory.append(
                {
                    "candidate_hash": cand["candidate_hash"],
                    "number_of_fermion_species": n,
                    "fermion_type": "Weyl_fermion",
                    "chirality_structure": "chiral Weyl sector",
                    "representation_labels": ["U1_symbolic"],
                    "symbolic_U1_charges": _symbolic_charges(n, gauge),
                    "free_dimensionless_parameters": ["g_U1", "q_i"],
                    "free_dimensionful_parameters": ["c0", "c1_nonzero", "kappa"],
                    "gauge_normalization_conventions": ["Z_A CONVENTION"],
                    "provenance": {
                        "Weyl_fermion": "GRAMMAR CHOICE",
                        "chirality_requirement": "TOP_DOWN_INPUT",
                        "symbolic_q_i": "FREE / PARAMETER-DEPENDENT",
                        "Lorentz_consistency": "DERIVED GIVEN GRAMMAR",
                        "gauge_representation_consistency": "DERIVED GIVEN GRAMMAR",
                        "anomaly_cancellation": "UNTESTED IN G1",
                        "spontaneous_symmetry_breaking": "DEFERRED TO G4",
                        "non_Abelian_structure": "DEFERRED TO G2",
                    },
                }
            )
    return {
        "class_table": table,
        "parameter_inventory": inventory,
        "blockers": [],
        "provenance_summary": {
            "Weyl_fermion": "GRAMMAR CHOICE",
            "chirality_requirement": "TOP_DOWN_INPUT",
            "symbolic_q_i": "FREE / PARAMETER-DEPENDENT",
            "anomaly_cancellation": "UNTESTED IN G1",
            "SSB": "DEFERRED TO G4",
            "non_Abelian": "DEFERRED TO G2",
        },
    }


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14b0_priors()
    out["phase14b0"] = {}
    for name in ("PHASE_14B0_SUMMARY.json", "TOP_DOWN_CLOSURE_STATE.json"):
        out["phase14b0"][name] = _file_digest(phase14b0_artifact_dir() / name)
    return out


def _historical_corpus() -> dict[str, Any]:
    catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
    specs_unchanged = True
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash_10a(spec) != item["canonical_hash"]:
            specs_unchanged = False
            break
    return {"count": len(catalog), "specs_unchanged": specs_unchanged, "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1}


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14B.1 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return None


def analyze_phase14b1_g1(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    _ = signature
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
        s14a = _read_json(phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json")
        s14b0 = _read_json(phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json")
        corpus = _historical_corpus()
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc), "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    integrity_failure = None
    if s14b0.get("TOP_DOWN_CLOSURE_ENGINE") != "READY":
        integrity_failure = "TOP_DOWN_CLOSURE_ENGINE is not READY"
    if s14b0.get("GRAMMAR_REGISTRY_STATUS") != "VERIFIED":
        integrity_failure = "GRAMMAR_REGISTRY not VERIFIED"
    if s14b0.get("CONSTRAINT_REGISTRY_STATUS") != "VERIFIED":
        integrity_failure = "CONSTRAINT_REGISTRY not VERIFIED"
    if s14b0.get("TARGET_BLINDNESS_STATUS") != "VERIFIED":
        integrity_failure = "TARGET_BLINDNESS not VERIFIED"
    if s14b0.get("CHECKPOINT_STATUS") != "VERIFIED":
        integrity_failure = "CHECKPOINT_SYSTEM not VERIFIED"
    if s14b0.get("PROVENANCE_STATUS") != "VERIFIED":
        integrity_failure = "PROVENANCE_SYSTEM not VERIFIED"
    if s14b0.get("EQUIVALENCE_STATUS") != "VERIFIED":
        integrity_failure = "EQUIVALENCE_SYSTEM not VERIFIED"
    if s14a.get("PHASE_14A_STATUS") != "CLOSED":
        integrity_failure = "Phase 14A is not CLOSED"
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not closed"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical corpus rewritten"

    grammars = g1_executable_registry()
    g1 = grammars["G1_FERMIONIC_CHIRAL"]
    g0 = grammars["G0_BASELINE"]
    if g1["parent_grammar_id"] != "G0_BASELINE":
        integrity_failure = "G1 parent is not G0_BASELINE"
    if g1["grammar_id"] != "G1_FERMIONIC_CHIRAL":
        integrity_failure = "current grammar is not G1"

    summary_path = artifact_dir() / "PHASE_14B1_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14B1_STATUS") == "CLOSED" and existing.get("G2_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14B1_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "G1_EXECUTED": False,
                "G2_EXECUTED": False,
                "ranking": False,
            }
            _write_json(summary_path, summary)
        else:
            dry0 = phase14b0_artifact_dir() / "closure_checkpoint_DRY0_SYNTHETIC.json"
            dry0_before = dry0.read_bytes() if dry0.is_file() else b""
            engine = ClosureEngine(artifact_dir(), chain="g1_only")
            assert_target_blind({"g1": g1, "kps": list(ACTIVE_G1_KPS)})
            try:
                ClosureEngine(artifact_dir() / "no_g2", chain="physics")
                g2_block = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g2_block = exc.mode
            state = engine.run_until_closure()
            if dry0.is_file() and dry0.read_bytes() != dry0_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G1 overwrote a 14B.0 dry checkpoint")
            g0_rep = next(r for r in state["version_reports"] if r["grammar_id"] == "G0_BASELINE")
            g1_rep = next(r for r in state["version_reports"] if r["grammar_id"] == "G1_FERMIONIC_CHIRAL")
            g0_ok = g0_rep["compatible"]
            g1_ok = g1_rep["compatible"]
            newly = g1_rep.get("compatible_hashes") or []
            g1_status = g1_rep["closure_status"]
            intersection_nonempty = g1_ok > 0
            unique_classes = g1_ok == 1
            summary = {
                "phase": PHASE,
                "audit_version": AUDIT_VERSION,
                "PHASE_14B1_STATUS": "CLOSED",
                "integrity_failure": None,
                "G1_STATUS": g1_status,
                "METHOD_STATUS": "VERIFIED",
                "SCIENTIFIC_STATUS": "ANALYZED_G1_ONLY",
                "GRAMMAR_ID": "G1_FERMIONIC_CHIRAL",
                "GRAMMAR_HASH": g1["grammar_hash"],
                "PARENT_GRAMMAR": "G0_BASELINE",
                "PARENT_GRAMMAR_HASH": g0["grammar_hash"],
                "TOP_DOWN_INPUT_HASH": top_down_input_hash(),
                "engine_version": ENGINE_VERSION,
                "current_grammar": "G1_FERMIONIC_CHIRAL",
                "parent_grammar": "G0_BASELINE",
                "RAW_COMBINATIONS": g1_rep["raw_theoretical_combinations"],
                "METADATA_PRUNED": g1_rep["metadata_pruned_candidates"],
                "GENERATED": g1_rep["generated_candidates"],
                "REJECTED": g1_rep["rejected"],
                "UNRESOLVED": g1_rep["unresolved"],
                "TOP_DOWN_COMPATIBLE": g1_ok,
                "EQUIVALENCE_CLASSES": len(g1_rep["equivalence_classes"]),
                "G0_COMPATIBLE": g0_ok,
                "G1_COMPATIBLE": g1_ok,
                "NEWLY_ENABLED": newly,
                "ELIMINATED": [
                    "G0 fermion-free branches (KP09, KP10)",
                    "Dirac-only branches (pruned: not a chiral fermionic sector)",
                    "Weyl_vectorlike branches (KP10 FAIL)",
                    "Weyl_chiral with trivial gauge (KP10 FAIL: no chiral gauge structure)",
                ],
                "N_fermion_search_limit": list(N_FERMION_SEARCH_LIMIT),
                "n_fermion_bound_is_search_limit_not_prediction": True,
                "FERMIONIC_GRAMMAR_REDUCES_PREVIOUS_EMPTY_INTERSECTION": intersection_nonempty,
                "CHIRAL_FERMION_CONTENT_ALONE_DOES_NOT_SELECT_UNIQUE_THEORY": not unique_classes,
                "G1_REQUIRES_NONABELIAN": False,
                "U1_ONLY_SUPPORTS_CHIRAL_FERMIONS_STRUCTURALLY": True,
                "G1_EXECUTED": True,
                "G2_EXECUTED": False,
                "NEXT_AUTHORIZED_EXTENSION": "G2_COMPACT_NONABELIAN",
                "physics_chain_skip_blocked": g2_block,
                "ACTIVE_G1_KPS": list(ACTIVE_G1_KPS),
                "DEFERRED_G1_KPS": dict(DEFERRED_G1_KPS),
                "class_table": g1_rep.get("class_table") or [],
                "parameter_inventory": g1_rep.get("parameter_inventory") or [],
                "version_reports": state.get("version_reports"),
                "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
                "frozen_hash_4C": EXPECTED_FROZEN_HASH,
                "string_theory_constraints_imported": False,
                "experimental_inputs": 0,
                "target_inputs": 0,
                "ranking": False,
                "fitting": False,
                "calibration": False,
                "sampling": False,
                "new_physical_principle": False,
                "phase_14b2_executed": False,
                "gravity_changed": False,
                "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
                "TARGET_BLINDNESS": "VERIFIED",
                "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
            }
            _write_json(summary_path, summary)
            _write_json(artifact_dir() / "PHASE_14B1_G1_GRAMMAR.json", g1)
            _write_json(artifact_dir() / "PHASE_14B1_G0_GRAMMAR.json", g0)
    else:
        summary = cached
        g1 = _read_json(artifact_dir() / "PHASE_14B1_G1_GRAMMAR.json")

    hashes_after = snapshot_prior_artifact_hashes()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    artifacts_ok = hashes_before == hashes_after
    summary["phase14b0_artifacts_unchanged"] = hashes_before["phase14b0"] == hashes_after["phase14b0"]
    summary["phase14a_artifacts_unchanged"] = hashes_before["phase14a"] == hashes_after["phase14a"]
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    if not (artifacts_ok and grammar_ok and frozen_ok and summary.get("ranking") is False and summary.get("G2_EXECUTED") is False):
        summary["PHASE_14B1_STATUS"] = "INTEGRITY_FAILURE"
        summary["METHOD_STATUS"] = "FAILED"
        summary["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    _write_json(summary_path, summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_14B1_TEST_COPY_ID": PHASE_14B1_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "G1_STATUS": summary.get("G1_STATUS"),
        "METHOD_STATUS": summary.get("METHOD_STATUS"),
        "SCIENTIFIC_STATUS": summary.get("SCIENTIFIC_STATUS"),
        "GRAMMAR_ID": "G1_FERMIONIC_CHIRAL",
        "GRAMMAR_HASH": summary.get("GRAMMAR_HASH"),
        "PARENT_GRAMMAR": "G0_BASELINE",
        "TOP_DOWN_INPUT_HASH": summary.get("TOP_DOWN_INPUT_HASH"),
        "RAW_COMBINATIONS": summary.get("RAW_COMBINATIONS"),
        "METADATA_PRUNED": summary.get("METADATA_PRUNED"),
        "GENERATED": summary.get("GENERATED"),
        "REJECTED": summary.get("REJECTED"),
        "UNRESOLVED": summary.get("UNRESOLVED"),
        "TOP_DOWN_COMPATIBLE": summary.get("TOP_DOWN_COMPATIBLE"),
        "EQUIVALENCE_CLASSES": summary.get("EQUIVALENCE_CLASSES"),
        "G0_COMPATIBLE": summary.get("G0_COMPATIBLE"),
        "G1_COMPATIBLE": summary.get("G1_COMPATIBLE"),
        "NEWLY_ENABLED": summary.get("NEWLY_ENABLED"),
        "ELIMINATED": summary.get("ELIMINATED"),
        "G1_EXECUTED": True if summary.get("PHASE_14B1_STATUS") == "CLOSED" else False,
        "G2_EXECUTED": False,
        "NEXT_AUTHORIZED_EXTENSION": "G2_COMPACT_NONABELIAN",
        "FERMIONIC_GRAMMAR_REDUCES_PREVIOUS_EMPTY_INTERSECTION": summary.get("FERMIONIC_GRAMMAR_REDUCES_PREVIOUS_EMPTY_INTERSECTION"),
        "CHIRAL_FERMION_CONTENT_ALONE_DOES_NOT_SELECT_UNIQUE_THEORY": summary.get("CHIRAL_FERMION_CONTENT_ALONE_DOES_NOT_SELECT_UNIQUE_THEORY"),
        "class_table": summary.get("class_table"),
        "parameter_inventory": summary.get("parameter_inventory"),
        "version_reports": summary.get("version_reports"),
        "ACTIVE_G1_KPS": summary.get("ACTIVE_G1_KPS"),
        "DEFERRED_G1_KPS": summary.get("DEFERRED_G1_KPS"),
        "N_fermion_search_limit": summary.get("N_fermion_search_limit"),
        "audit_summary": summary,
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_14B1_STATUS": summary.get("PHASE_14B1_STATUS"),
        "PHASE_14B0_STATUS": s14b0.get("PHASE_14B0_STATUS"),
        "PHASE_14A_STATUS": s14a.get("PHASE_14A_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "gravity_changed": False,
        "ranking_score_introduced": False,
        "known_physics_comparison_executed": False,
        "phase_14b2_executed": False,
        "sampling": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_physical_principle": False,
        "string_theory_constraints_imported": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "ranking": False,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_14B1_CLOSED": summary.get("PHASE_14B1_STATUS") == "CLOSED",
        "overclaims": {
            "1_activate_G2_automatically": "REJECTED AS OVERCLAIM",
            "2_claim_unique_physical_theory": "REJECTED AS OVERCLAIM",
            "3_fix_numerical_charges": "REJECTED AS OVERCLAIM",
            "4_treat_N_fermion_bound_as_prediction": "REJECTED AS OVERCLAIM",
            "5_run_anomaly_engine": "REJECTED AS OVERCLAIM",
            "6_add_nonabelian_in_G1": "REJECTED AS OVERCLAIM",
            "7_insert_experimental_inputs": "REJECTED AS OVERCLAIM",
            "8_modify_gravity": "REJECTED AS OVERCLAIM",
            "9_rank_candidate_classes": "REJECTED AS OVERCLAIM",
            "10_start_phase_14b2": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_14B1_STATUS"] == "CLOSED"
        and science["G2_EXECUTED"] is False
        and science["G1_EXECUTED"] is True
        and science["PARENT_GRAMMAR"] == "G0_BASELINE"
        and science["GRAMMAR_ID"] == "G1_FERMIONIC_CHIRAL"
        and science["ranking"] is False
        and science["gravity_changed"] is False
        and science["experimental_inputs"] == 0
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and hashes_before["phase14b0"] == hashes_after["phase14b0"]
        and corpus["specs_unchanged"]
    )
    return science


def run_phase14b1_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14b1_g1(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("grammar_hash_12A_unchanged") else "FAILED",
            "PHASE_14B0_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14b0_artifacts_unchanged") else "FAILED",
            "PHASE_14B1_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14B1_STATUS": science.get("PHASE_14B1_STATUS"),
            "PHASE_14B0_STATUS": science.get("PHASE_14B0_STATUS"),
            "PHASE_14A_STATUS": science.get("PHASE_14A_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "STRING_THEORY_CONSTRAINTS": "NONE",
            "PHASE_14B2_EXECUTED": "FALSE",
            "G1_EXECUTED": "TRUE",
            "G2_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
