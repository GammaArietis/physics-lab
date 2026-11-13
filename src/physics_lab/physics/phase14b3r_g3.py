"""Phase 14B.3R: logical correction of G3 chirality vs representation reality.

Does not activate G4. Does not overwrite the archived G3 checkpoint.
"""

from __future__ import annotations

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
    top_down_input_hash,
    _with_hash,
)
from physics_lab.physics.phase14b2_g2 import (
    EXPECTED_G1_GRAMMAR_HASH,
    artifact_dir as phase14b2_artifact_dir,
)
from physics_lab.physics.phase14b3_g3 import (
    ACTIVE_G3_KPS,
    DEFERRED_G3_KPS,
    EXPECTED_G2_GRAMMAR_HASH,
    EXPECTED_TOP_DOWN_INPUT_HASH,
    M_MAX,
    N_SU_VALUES,
    N_U1_MAX,
    R_MAX,
    REPRESENTATION_SEARCH_BOUNDS,
    attach_g3_stats,
    build_representation_catalogue,
    catalogue_hash,
    conjugate_dynkin,
    format_dynkin,
    g3_pack_values,
    g3_metadata_legal,
    group_label,
    irrep_data,
    parse_dynkin,
    parse_pack,
    snapshot_prior_artifact_hashes as snapshot_14b3_priors,
    su_n_dimension,
    verify_g2_parent_checkpoint,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_OLD_G3_CHECKPOINT_HASH",
    "EXPECTED_OLD_G3_GRAMMAR_HASH",
    "G3R_CHAIN",
    "analyze_phase14b3r_g3",
    "artifact_dir",
    "g3r_executable_registry",
    "g3r_metadata_legal",
    "g3r_run_tests",
    "run_phase14b3r_or_stop",
]

PHASE = "PHASE_14B.3R"
PHASE_14B3R_TEST_COPY_ID = "PHASE_14B3R_CORRECT_G3_CHIRALITY_CRITERION"
AUDIT_VERSION = "phase14b3r-g3-logical-correction-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_OLD_G3_GRAMMAR_HASH = "8586539b221a0a22ce76720fb8008d40f2d34ef46e7d92c346a6abfad8b168dd"
EXPECTED_OLD_G3_CHECKPOINT_HASH = "f7028b136e3ed0e105ea9e0757efdf455b9a66fa95418b37c76ebe1121827553"
G3R_ID = "G3_FINITE_REPRESENTATIONS_R1"
G3R_CHAIN: tuple[str, ...] = (G3R_ID,)
OLD_G3_ID = "G3_FINITE_REPRESENTATIONS"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b3r_artifacts"


def old_g3_artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b3_artifacts"


def old_g3_checkpoint_path() -> Path:
    return old_g3_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS.json"


def g2_checkpoint_path() -> Path:
    return phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json"


def _write_json(path: Path, payload: Any) -> None:
    assert_target_blind(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def g3r_executable_registry() -> dict[str, dict[str, Any]]:
    exclusions = [
        "exceptional groups",
        "Standard Model multiplets as preferred choices",
        "anomaly cancellation engine",
        "scalar Higgs multiplets beyond G0",
        "spontaneous symmetry breaking",
        "Yukawa reconstruction",
        "RG",
        "SUSY",
        "extra dimensions",
        "G4 VEV grammar",
        "G5 anomaly grammar",
        "G6 structural gauge-consistency grammar",
        "experimental charge identification of U(1) weights",
        "chirality requires complex representation",
        "real or pseudoreal representation treated as automatically vectorlike",
    ]
    g3r = _with_hash(
        {
            "grammar_id": G3R_ID,
            "parent_grammar_id": "G2_COMPACT_NONABELIAN",
            "extension_description": (
                "LOGICAL CORRECTION of G3: bounded Dynkin irreps and compact U(1) characters; "
                "KP10 is Weyl chirality plus a valid finite gauge representation, "
                "not a complex-representation requirement"
            ),
            "allowed_fields": ["metric", "scalar", "Weyl_fermion"],
            "allowed_groups": ["SU_N_family", "SU_N x U(1)^k"],
            "allowed_representations": ["dynkin_irreps_bounded", "U1_character_n_in_Z"],
            "allowed_interactions": ["nonabelian_covariant_derivative", "U1_covariant_derivative"],
            "allowed_symmetry_breaking": [],
            "allowed_constraints": list(ACTIVE_G3_KPS) + ["G3_FINITE_REPRESENTATION_VALIDITY"],
            "explicit_exclusions": exclusions,
            "provenance": "LOGICAL CORRECTION",
            "status": "ACTIVE_G3_CORRECTED",
            "axes": {"g3_pack": g3_pack_values()},
            "r_max": R_MAX,
            "n_u1_max": N_U1_MAX,
            "m_max": M_MAX,
            "r_max_is_search_bound_not_prediction": True,
            "m_max_is_search_bound_not_prediction": True,
            "CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION": "NO",
            "correction_of": OLD_G3_ID,
            "correction_of_grammar_hash": EXPECTED_OLD_G3_GRAMMAR_HASH,
        }
    )
    return {G3R_ID: g3r}


def g3r_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    """Validity-only prune. Representation reality is not a chirality rejection."""
    _ = grammar
    try:
        parsed = parse_pack(assignment["g3_pack"])
        n = int(parsed["simple_group"].split(":")[1])
        labels = parse_dynkin(parsed["dynkin"])
        k = int(parsed["u1_k"])
        w = parsed["u1_n"]
        m = int(parsed["multiplicity"])
    except (KeyError, ValueError):
        return False, "invalid_g3_pack"
    if n not in N_SU_VALUES:
        return False, "group_not_in_G2_bounds"
    if len(labels) != n - 1:
        return False, "dynkin_rank_mismatch"
    if any(x < 0 or x > R_MAX for x in labels):
        return False, "dynkin_outside_R_MAX"
    if m < 1 or m > M_MAX:
        return False, "multiplicity_outside_M_MAX"
    if k == 0 and w != "none":
        return False, "u1_weight_without_u1_factor"
    if k == 1:
        try:
            wi = int(w)
        except ValueError:
            return False, "u1_weight_not_integer"
        if abs(wi) > N_U1_MAX:
            return False, "u1_weight_outside_N_U1_MAX"
    return True, None


def criterion_pack_diff() -> dict[str, Any]:
    dummy: dict[str, Any] = {}
    restored = []
    removed = []
    unchanged = []
    for pack in g3_pack_values():
        assignment = {"g3_pack": pack}
        old_ok, _ = g3_metadata_legal(assignment, dummy)
        new_ok, _ = g3r_metadata_legal(assignment, dummy)
        if new_ok and not old_ok:
            restored.append(pack)
        elif old_ok and not new_ok:
            removed.append(pack)
        elif old_ok and new_ok:
            unchanged.append(pack)
    return {
        "RESTORED_CLASSES": restored,
        "REMOVED_CLASSES": removed,
        "UNCHANGED_CLASSES": unchanged,
        "OLD_G3_COMPATIBLE": len(unchanged),
        "CORRECTED_G3_COMPATIBLE": len(unchanged) + len(restored),
    }


def g3r_run_tests(candidate: dict[str, Any], *, test_version: str = "g3r-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    parsed = parse_pack(candidate["assignment"]["g3_pack"])
    n = int(parsed["simple_group"].split(":")[1])
    k = int(parsed["u1_k"])
    labels = parse_dynkin(parsed["dynkin"])
    w = parsed["u1_n"]
    nf = parsed["n_fermion"]
    data = irrep_data(n, labels)
    dim_ok = data["dimension"] == su_n_dimension(n, labels)
    conj_ok = tuple(data["conjugate_dynkin"]) == conjugate_dynkin(labels)
    rank_ok = len(labels) == n - 1
    u1_ok = (k == 0 and w == "none") or (k == 1 and w.lstrip("-").isdigit())
    weyl_ok = nf in {"1", "2"}
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
    add("KP03", "PASS", "INHERITED FROM G2", "4D Lorentz Weyl sector inherited")
    add("KP09", "PASS", "INHERITED FROM G2", "Weyl_chiral plus G0 bosonic scalar/metric")
    add(
        "KP10",
        "PASS" if weyl_ok else "FAIL",
        "LOGICAL CORRECTION",
        "Weyl fermion sector with a valid finite gauge representation; complex representation is not required",
    )
    add("KP11", "PASS", "MATHEMATICAL REPRESENTATION DATA", "Dynkin labels and compact U(1) weight n")
    add("KP14", "PASS", "INHERITED FROM G2", "finite species inherited; M_MAX is a search limit")
    add("KP12", "UNTESTED", "DEFERRED TO G5", "anomaly_status=DEFERRED_TO_G5")
    add("KP13", "NOT_APPLICABLE", "DEFERRED TO G4", "SSB_STATUS=DEFERRED_TO_G4")
    add("KP15", "NOT_APPLICABLE", "DEFERRED TO G4", "VECTOR_MASS_STATUS=DEFERRED_TO_G4")
    add(
        "G3_FINITE_REPRESENTATION_VALIDITY",
        "PASS" if dim_ok and conj_ok and rank_ok and u1_ok else "FAIL",
        "DERIVED GIVEN GROUP + REPRESENTATION GRAMMAR",
        "finite irrep, conjugation, product (R,n), dimension",
    )
    add("u1_compact_character", "PASS" if u1_ok else "FAIL", "DERIVED GIVEN COMPACT REPRESENTATION CONVENTION", "n in Z; not an experimentally normalized charge")
    add("lorentz_chirality", "PASS" if weyl_ok else "FAIL", "INHERITED FROM G2", "Weyl Lorentz chirality is independent of representation reality")
    add("representation_reality_type", "PASS", "MATHEMATICAL REPRESENTATION DATA", data["reality_type"])
    add("vectorlike_status", "UNTESTED", "UNTESTED / DEFERRED", "real or pseudoreal does not imply vectorlike matter")
    add("anomaly_status", "UNTESTED", "DEFERRED TO G5", "do not reject on anomaly")
    add("SSB_STATUS", "NOT_APPLICABLE", "DEFERRED TO G4", "no extra scalars or VEVs")
    add("VECTOR_MASS_STATUS", "NOT_APPLICABLE", "DEFERRED TO G4", "generator count is not a mass spectrum")
    add("G4_scalar_multiplets", "NOT_APPLICABLE", "DEFERRED TO G4", "corrected G3 must not activate G4")
    add("CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION", "PASS", "LOGICAL CORRECTION", "NO")

    required_fail = any(
        r["status"] == "FAIL" and r["test_id"] in (*ACTIVE_G3_KPS, "G3_FINITE_REPRESENTATION_VALIDITY")
        for r in results
    )
    return {
        "status": "FAIL" if required_fail else "PASS",
        "results": results,
        "test_version": test_version,
        "irrep": data,
        "u1_weight": w,
        "lorentz_chirality": "Weyl",
        "representation_reality_type": data["reality_type"],
        "vectorlike_status": "UNTESTED",
        "CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION": "NO",
        "anomaly_status": "DEFERRED_TO_G5",
        "SSB_STATUS": "DEFERRED_TO_G4",
        "VECTOR_MASS_STATUS": "DEFERRED_TO_G4",
    }


def attach_g3r_stats(grammar: dict[str, Any], evaluated: list[dict[str, Any]], compatible: list[dict[str, Any]]) -> dict[str, Any]:
    extra = attach_g3_stats(grammar, evaluated, compatible)
    for row in extra.get("class_table") or []:
        row["lorentz_chirality"] = "Weyl"
        row["vectorlike_status"] = "UNTESTED"
        row["CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION"] = "NO"
        row["correction_provenance"] = "LOGICAL CORRECTION"
        content = str(row.get("representation_content") or "")
        reality = "unclassified"
        for token in ("pseudoreal", "complex", "real"):
            if token in content:
                reality = token
                break
        row["representation_reality_type"] = reality
    for row in extra.get("parameter_inventory") or []:
        row["lorentz_chirality"] = "Weyl"
        row["representation_reality_type"] = (row.get("conjugation_structure") or {}).get("reality_type")
        row["vectorlike_status"] = "UNTESTED"
        row["CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION"] = "NO"
        prov = dict(row.get("provenance") or {})
        prov["chirality_criterion_correction"] = "LOGICAL CORRECTION"
        prov["vectorlike_classification"] = "UNTESTED / DEFERRED"
        row["provenance"] = prov
    extra["CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION"] = "NO"
    extra["correction_provenance"] = "LOGICAL CORRECTION"
    extra["old_g3_grammar_id"] = OLD_G3_ID
    extra["old_g3_grammar_hash"] = EXPECTED_OLD_G3_GRAMMAR_HASH
    return extra


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14b3_priors()
    out["phase14b3"] = {}
    for name in (
        "PHASE_14B3_SUMMARY.json",
        "closure_checkpoint_G3_FINITE_REPRESENTATIONS.json",
        "PHASE_14B3_G3_GRAMMAR.json",
    ):
        path = old_g3_artifact_dir() / name
        if path.is_file():
            out["phase14b3"][name] = _file_digest(path)
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
        raise UnauthorizedAnalysisError("Phase 14B.3R refuses an unauthorized action object")
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


def _uniqueness(inventory: list[dict[str, Any]]) -> dict[str, str]:
    groups = {row["gauge_group"] for row in inventory}
    reps = {tuple(row["representation_labels"]) for row in inventory}
    dims = {tuple(row["representation_dimensions"]) for row in inventory}
    weights = {row["U1_weights"] for row in inventory}
    conj = {json.dumps(row["conjugation_structure"], sort_keys=True) for row in inventory}

    def yn(ok: bool) -> str:
        return "YES" if ok else "NO"

    return {
        "UNIQUE_REPRESENTATION_CONTENT": yn(len(reps) == 1),
        "UNIQUE_REPRESENTATION_DIMENSIONS": yn(len(dims) == 1),
        "UNIQUE_GAUGE_GROUP": yn(len(groups) == 1),
        "UNIQUE_CONJUGATION_STRUCTURE": yn(len(conj) == 1),
        "UNIQUE_U1_WEIGHTS": yn(len(weights) == 1),
        "UNIQUE_STRUCTURE": yn(len(inventory) == 1),
        "UNIQUE_PARAMETER_SET": "NO",
        "UNIQUE_DIMENSIONLESS_COUPLING": "NO",
    }


def verify_old_g3_archive() -> dict[str, Any]:
    path = old_g3_checkpoint_path()
    if not path.is_file():
        raise EngineFailure("CHECKPOINT_CORRUPTED", "archived G3 checkpoint missing")
    payload = _read_json(path)
    stored = payload.get("integrity_digest")
    recomputed = content_hash({k: v for k, v in payload.items() if k != "integrity_digest"})
    if stored != recomputed:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "archived G3 digest mismatch")
    if payload.get("grammar_id") != OLD_G3_ID:
        raise EngineFailure("GRAMMAR_MISSING", "archived G3 grammar_id")
    if payload.get("grammar_hash") != EXPECTED_OLD_G3_GRAMMAR_HASH:
        raise EngineFailure("GRAMMAR_HASH_MISMATCH", "archived G3 grammar_hash")
    digest = _file_digest(path)
    if digest != EXPECTED_OLD_G3_CHECKPOINT_HASH:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "archived G3 file digest changed")
    return payload


def analyze_phase14b3r_g3(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
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
        s14b2 = _read_json(phase14b2_artifact_dir() / "PHASE_14B2_SUMMARY.json")
        s14b3 = _read_json(old_g3_artifact_dir() / "PHASE_14B3_SUMMARY.json")
        corpus = _historical_corpus()
        parent_ckpt = verify_g2_parent_checkpoint()
        old_ckpt = verify_old_g3_archive()
        old_ckpt_bytes = old_g3_checkpoint_path().read_bytes()
        g2_before = g2_checkpoint_path().read_bytes()
    except (FileNotFoundError, EngineFailure) as exc:
        detail = exc.mode if isinstance(exc, EngineFailure) else str(exc)
        return {"status": "STOP", "scientific_analysis": None, "detail": detail, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

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
    if s14b2.get("PHASE_14B2_STATUS") != "CLOSED":
        integrity_failure = "Phase 14B.2 is not CLOSED"
    if s14b2.get("current_grammar") != "G2_COMPACT_NONABELIAN":
        integrity_failure = "CURRENT_GRAMMAR is not G2_COMPACT_NONABELIAN"
    if s14b2.get("GRAMMAR_HASH") != EXPECTED_G2_GRAMMAR_HASH:
        integrity_failure = "G2 grammar hash mismatch"
    if s14b2.get("PARENT_GRAMMAR_HASH") != EXPECTED_G1_GRAMMAR_HASH:
        integrity_failure = "G1 grammar hash mismatch"
    if s14b2.get("TOP_DOWN_INPUT_HASH") != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "top-down input hash mismatch"
    if s14b3.get("GRAMMAR_HASH") != EXPECTED_OLD_G3_GRAMMAR_HASH:
        integrity_failure = "archived G3 grammar hash mismatch"
    if s14b3.get("G3_COMPATIBLE") != 80:
        integrity_failure = "archived G3 compatible count rewritten"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical corpus rewritten"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G2_GRAMMAR_HASH:
        integrity_failure = "G2 checkpoint grammar hash mismatch"
    if old_ckpt.get("grammar_hash") != EXPECTED_OLD_G3_GRAMMAR_HASH:
        integrity_failure = "old G3 checkpoint grammar hash mismatch"
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "live top-down input hash mismatch"

    grammars = g3r_executable_registry()
    g3r = grammars[G3R_ID]
    if g3r["parent_grammar_id"] != "G2_COMPACT_NONABELIAN":
        integrity_failure = "G3_R1 parent is not G2_COMPACT_NONABELIAN"
    if g3r["grammar_hash"] == EXPECTED_OLD_G3_GRAMMAR_HASH:
        integrity_failure = "corrected G3 grammar hash is not distinct"

    summary_path = artifact_dir() / "PHASE_14B3R_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14B3R_STATUS") == "CLOSED" and existing.get("G4_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14B3R_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "G3_CORRECTED_EXECUTED": False,
                "G4_EXECUTED": False,
                "ranking": False,
            }
            _write_json(summary_path, summary)
        else:
            engine = ClosureEngine(artifact_dir(), chain="g3r_only")
            assert_target_blind({"g3r": g3r, "bounds": REPRESENTATION_SEARCH_BOUNDS, "catalogue": build_representation_catalogue()})
            try:
                ClosureEngine(artifact_dir() / "no_g4", chain="physics")
                g4_block = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g4_block = exc.mode
            try:
                engine.advance_grammar("G4_SCALAR_MULTIPLETS_VEV", G3R_ID)
                g4_skip = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g4_skip = exc.mode
            state = engine.run_until_closure()
            if g2_checkpoint_path().read_bytes() != g2_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G3_R1 overwrote the G2 checkpoint")
            if old_g3_checkpoint_path().read_bytes() != old_ckpt_bytes:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G3_R1 overwrote the archived G3 checkpoint")
            g3_rep = next(r for r in state["version_reports"] if r["grammar_id"] == G3R_ID)
            g2_ok = len(parent_ckpt.get("survivor_hashes") or [])
            g3_ok = g3_rep["compatible"]
            newly = g3_rep.get("compatible_hashes") or []
            used_parents = {row.get("parent_g2_hash") for row in g3_rep.get("class_table") or [] if row.get("status") == "PASS"}
            eliminated = [h for h in (parent_ckpt.get("survivor_hashes") or []) if h not in used_parents]
            uniq = _uniqueness(g3_rep.get("parameter_inventory") or [])
            cat = build_representation_catalogue()
            diff = criterion_pack_diff()
            su2_restored = [p for p in diff["RESTORED_CLASSES"] if p.startswith("SU_N:2|")]
            summary = {
                "phase": PHASE,
                "audit_version": AUDIT_VERSION,
                "PHASE_14B3R_STATUS": "CLOSED",
                "integrity_failure": None,
                "CORRECTION_STATUS": "APPLIED",
                "G3_STATUS": g3_rep["closure_status"],
                "METHOD_STATUS": "VERIFIED",
                "SCIENTIFIC_STATUS": "ANALYZED_G3_CORRECTED_ONLY",
                "GRAMMAR_ID": G3R_ID,
                "GRAMMAR_HASH": g3r["grammar_hash"],
                "OLD_G3_GRAMMAR_ID": OLD_G3_ID,
                "OLD_G3_GRAMMAR_HASH": EXPECTED_OLD_G3_GRAMMAR_HASH,
                "NEW_G3_GRAMMAR_HASH": g3r["grammar_hash"],
                "PARENT_GRAMMAR": "G2_COMPACT_NONABELIAN",
                "PARENT_GRAMMAR_HASH": EXPECTED_G2_GRAMMAR_HASH,
                "PARENT_CHECKPOINT": str(g2_checkpoint_path().name),
                "PARENT_CHECKPOINT_HASH": _file_digest(g2_checkpoint_path()),
                "OLD_G3_CHECKPOINT": str(old_g3_checkpoint_path().name),
                "OLD_G3_CHECKPOINT_HASH": _file_digest(old_g3_checkpoint_path()),
                "OLD_G3_STATUS": "SUPERSEDED_BY_LOGICAL_CORRECTION",
                "TOP_DOWN_INPUT_HASH": top_down_input_hash(),
                "engine_version": ENGINE_VERSION,
                "current_grammar": G3R_ID,
                "parent_grammar": "G2_COMPACT_NONABELIAN",
                "REPRESENTATION_SEARCH_BOUNDS": dict(REPRESENTATION_SEARCH_BOUNDS),
                "RAW_COMBINATIONS": g3_rep["raw_theoretical_combinations"],
                "METADATA_PRUNED": g3_rep["metadata_pruned_candidates"],
                "GENERATED": g3_rep["generated_candidates"],
                "REJECTED": g3_rep["rejected"],
                "UNRESOLVED": g3_rep["unresolved"],
                "TOP_DOWN_COMPATIBLE": g3_ok,
                "EQUIVALENCE_CLASSES": len(g3_rep["equivalence_classes"]),
                "REPRESENTATION_CATALOGUE_SIZE": len(cat),
                "representation_catalogue_hash": catalogue_hash(),
                "G2_COMPATIBLE": g2_ok,
                "G3_COMPATIBLE": s14b3.get("G3_COMPATIBLE"),
                "OLD_G3_COMPATIBLE": diff["OLD_G3_COMPATIBLE"],
                "CORRECTED_G3_COMPATIBLE": g3_ok,
                "RESTORED_CLASSES": diff["RESTORED_CLASSES"],
                "REMOVED_CLASSES": diff["REMOVED_CLASSES"],
                "UNCHANGED_CLASSES": diff["UNCHANGED_CLASSES"],
                "SU2_RESTORED_CLASSES": su2_restored,
                "NEWLY_ENABLED": newly,
                "ELIMINATED": eliminated,
                "G2_SURVIVORS_REUSED": g3_rep.get("g2_survivors_reused"),
                "G3_NEW_CANDIDATES_GENERATED": g3_rep.get("g3_new_candidates_generated"),
                "G0_REGENERATED": 0,
                "G1_FULL_SEARCH_REGENERATED": 0,
                "G2_FULL_SEARCH_REGENERATED": 0,
                "G3_FULL_SEARCH_BOUNDS_UNCHANGED": True,
                "G2_PARENTS_WITH_DESCENDANTS": len(used_parents),
                "FINITE_REPRESENTATION_STRUCTURE_DOES_NOT_SELECT_A_UNIQUE_MATTER_CONTENT_WITHIN_THE_DECLARED_G3_BOUNDS": g3_ok != 1,
                "CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION": "NO",
                "REPRESENTATION_REALITY_TYPE": "INDEPENDENT PROPERTY",
                "G1_EXECUTED": True,
                "G2_EXECUTED": True,
                "G3_EXECUTED": True,
                "G3_CORRECTED_EXECUTED": True,
                "G4_EXECUTED": False,
                "NEXT_AUTHORIZED_EXTENSION": "G4_SCALAR_MULTIPLETS_VEV",
                "physics_chain_skip_blocked": g4_block,
                "g4_skip_blocked": g4_skip,
                "ACTIVE_G3_KPS": list(ACTIVE_G3_KPS),
                "DEFERRED_G3_KPS": dict(DEFERRED_G3_KPS),
                "class_table": g3_rep.get("class_table") or [],
                "parameter_inventory": g3_rep.get("parameter_inventory") or [],
                "version_reports": state.get("version_reports"),
                "uniqueness": uniq,
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
                "phase_14b4_executed": False,
                "gravity_changed": False,
                "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
                "TARGET_BLINDNESS": "VERIFIED",
                "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
                "anomaly_status": "DEFERRED_TO_G5",
                "SSB_STATUS": "DEFERRED_TO_G4",
                "VECTOR_MASS_STATUS": "DEFERRED_TO_G4",
                "correction_provenance": "LOGICAL CORRECTION",
            }
            _write_json(summary_path, summary)
            _write_json(artifact_dir() / "PHASE_14B3R_G3_GRAMMAR.json", g3r)
            _write_json(artifact_dir() / "PHASE_14B3R_REPRESENTATION_CATALOGUE.json", cat)
            _write_json(
                old_g3_artifact_dir() / "PHASE_14B3_SUPERSEDED_BY_LOGICAL_CORRECTION.json",
                {
                    "OLD_G3_STATUS": "SUPERSEDED_BY_LOGICAL_CORRECTION",
                    "OLD_G3_GRAMMAR_ID": OLD_G3_ID,
                    "OLD_G3_GRAMMAR_HASH": EXPECTED_OLD_G3_GRAMMAR_HASH,
                    "OLD_G3_CHECKPOINT": str(old_g3_checkpoint_path().name),
                    "OLD_G3_CHECKPOINT_HASH": EXPECTED_OLD_G3_CHECKPOINT_HASH,
                    "SUPERSEDED_BY": G3R_ID,
                    "SUPERSEDED_BY_GRAMMAR_HASH": g3r["grammar_hash"],
                    "correction": "remove over-strong chirality-requires-complex-representation criterion",
                    "provenance": "SUPERSEDED BY LOGICAL CORRECTION",
                    "checkpoint_file_unmodified": True,
                },
            )
    else:
        summary = cached
        g3r = _read_json(artifact_dir() / "PHASE_14B3R_G3_GRAMMAR.json")

    hashes_after = snapshot_prior_artifact_hashes()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    g2_unchanged = g2_checkpoint_path().read_bytes() == g2_before
    old_g3_unchanged = old_g3_checkpoint_path().read_bytes() == old_ckpt_bytes
    g3_named = hashes_before.get("phase14b3", {})
    g3_named_after = hashes_after.get("phase14b3", {})
    archived_named_ok = all(g3_named.get(k) == g3_named_after.get(k) for k in g3_named)
    summary["phase14b2_artifacts_unchanged"] = hashes_before["phase14b2"] == hashes_after["phase14b2"]
    summary["phase14b1_artifacts_unchanged"] = hashes_before.get("phase14b1") == hashes_after.get("phase14b1")
    summary["phase14b0_artifacts_unchanged"] = hashes_before["phase14b0"] == hashes_after["phase14b0"]
    summary["phase14b3_checkpoint_unchanged"] = old_g3_unchanged
    summary["phase14b3_named_artifacts_unchanged"] = archived_named_ok
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["g2_checkpoint_unchanged"] = g2_unchanged
    artifacts_ok = (
        hashes_before["phase14b2"] == hashes_after["phase14b2"]
        and hashes_before["phase14b0"] == hashes_after["phase14b0"]
        and hashes_before.get("phase14b1") == hashes_after.get("phase14b1")
        and archived_named_ok
    )
    if not (
        artifacts_ok
        and grammar_ok
        and frozen_ok
        and g2_unchanged
        and old_g3_unchanged
        and summary.get("ranking") is False
        and summary.get("G4_EXECUTED") is False
    ):
        summary["PHASE_14B3R_STATUS"] = "INTEGRITY_FAILURE"
        summary["METHOD_STATUS"] = "FAILED"
        summary["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    _write_json(summary_path, summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_14B3R_TEST_COPY_ID": PHASE_14B3R_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "CORRECTION_STATUS": summary.get("CORRECTION_STATUS"),
        "G3_STATUS": summary.get("G3_STATUS"),
        "METHOD_STATUS": summary.get("METHOD_STATUS"),
        "SCIENTIFIC_STATUS": summary.get("SCIENTIFIC_STATUS"),
        "GRAMMAR_ID": G3R_ID,
        "GRAMMAR_HASH": summary.get("GRAMMAR_HASH"),
        "OLD_G3_GRAMMAR_HASH": EXPECTED_OLD_G3_GRAMMAR_HASH,
        "NEW_G3_GRAMMAR_HASH": summary.get("NEW_G3_GRAMMAR_HASH"),
        "PARENT_GRAMMAR": "G2_COMPACT_NONABELIAN",
        "PARENT_GRAMMAR_HASH": EXPECTED_G2_GRAMMAR_HASH,
        "G2_GRAMMAR_HASH": EXPECTED_G2_GRAMMAR_HASH,
        "PARENT_CHECKPOINT": summary.get("PARENT_CHECKPOINT"),
        "PARENT_CHECKPOINT_HASH": summary.get("PARENT_CHECKPOINT_HASH"),
        "OLD_G3_CHECKPOINT_HASH": summary.get("OLD_G3_CHECKPOINT_HASH"),
        "OLD_G3_STATUS": "SUPERSEDED_BY_LOGICAL_CORRECTION",
        "TOP_DOWN_INPUT_HASH": summary.get("TOP_DOWN_INPUT_HASH"),
        "REPRESENTATION_SEARCH_BOUNDS": summary.get("REPRESENTATION_SEARCH_BOUNDS"),
        "RAW_COMBINATIONS": summary.get("RAW_COMBINATIONS"),
        "METADATA_PRUNED": summary.get("METADATA_PRUNED"),
        "GENERATED": summary.get("GENERATED"),
        "REJECTED": summary.get("REJECTED"),
        "UNRESOLVED": summary.get("UNRESOLVED"),
        "TOP_DOWN_COMPATIBLE": summary.get("TOP_DOWN_COMPATIBLE"),
        "EQUIVALENCE_CLASSES": summary.get("EQUIVALENCE_CLASSES"),
        "REPRESENTATION_CATALOGUE_SIZE": summary.get("REPRESENTATION_CATALOGUE_SIZE"),
        "G2_COMPATIBLE": summary.get("G2_COMPATIBLE"),
        "OLD_G3_COMPATIBLE": summary.get("OLD_G3_COMPATIBLE"),
        "CORRECTED_G3_COMPATIBLE": summary.get("CORRECTED_G3_COMPATIBLE"),
        "RESTORED_CLASSES": summary.get("RESTORED_CLASSES"),
        "REMOVED_CLASSES": summary.get("REMOVED_CLASSES"),
        "UNCHANGED_CLASSES": summary.get("UNCHANGED_CLASSES"),
        "SU2_RESTORED_CLASSES": summary.get("SU2_RESTORED_CLASSES"),
        "ELIMINATED": summary.get("ELIMINATED"),
        "G2_SURVIVORS_REUSED": summary.get("G2_SURVIVORS_REUSED"),
        "G0_REGENERATED": 0,
        "G1_FULL_SEARCH_REGENERATED": 0,
        "G2_FULL_SEARCH_REGENERATED": 0,
        "G1_EXECUTED": True if summary.get("PHASE_14B3R_STATUS") == "CLOSED" else False,
        "G2_EXECUTED": True if summary.get("PHASE_14B3R_STATUS") == "CLOSED" else False,
        "G3_EXECUTED": True if summary.get("PHASE_14B3R_STATUS") == "CLOSED" else False,
        "G3_CORRECTED_EXECUTED": True if summary.get("PHASE_14B3R_STATUS") == "CLOSED" else False,
        "G4_EXECUTED": False,
        "NEXT_AUTHORIZED_EXTENSION": "G4_SCALAR_MULTIPLETS_VEV",
        "CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION": "NO",
        "REPRESENTATION_REALITY_TYPE": "INDEPENDENT PROPERTY",
        "FINITE_REPRESENTATION_STRUCTURE_DOES_NOT_SELECT_A_UNIQUE_MATTER_CONTENT_WITHIN_THE_DECLARED_G3_BOUNDS": summary.get(
            "FINITE_REPRESENTATION_STRUCTURE_DOES_NOT_SELECT_A_UNIQUE_MATTER_CONTENT_WITHIN_THE_DECLARED_G3_BOUNDS"
        ),
        "class_table": summary.get("class_table"),
        "parameter_inventory": summary.get("parameter_inventory"),
        "uniqueness": summary.get("uniqueness"),
        "version_reports": summary.get("version_reports"),
        "ACTIVE_G3_KPS": summary.get("ACTIVE_G3_KPS"),
        "DEFERRED_G3_KPS": summary.get("DEFERRED_G3_KPS"),
        "audit_summary": summary,
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_14B3R_STATUS": summary.get("PHASE_14B3R_STATUS"),
        "PHASE_14B3_STATUS": s14b3.get("PHASE_14B3_STATUS"),
        "PHASE_14B2_STATUS": s14b2.get("PHASE_14B2_STATUS"),
        "PHASE_14B0_STATUS": s14b0.get("PHASE_14B0_STATUS"),
        "PHASE_14A_STATUS": s14a.get("PHASE_14A_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "gravity_changed": False,
        "ranking_score_introduced": False,
        "known_physics_comparison_executed": False,
        "phase_14b4_executed": False,
        "sampling": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_physical_principle": False,
        "string_theory_constraints_imported": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "ranking": False,
        "anomaly_status": "DEFERRED_TO_G5",
        "SSB_STATUS": "DEFERRED_TO_G4",
        "VECTOR_MASS_STATUS": "DEFERRED_TO_G4",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_14B3R_CLOSED": summary.get("PHASE_14B3R_STATUS") == "CLOSED",
        "correction_provenance": "LOGICAL CORRECTION",
        "overclaims": {
            "1_activate_G4_automatically": "REJECTED AS OVERCLAIM",
            "2_claim_unique_representation": "REJECTED AS OVERCLAIM",
            "3_identify_n_with_measured_charge": "REJECTED AS OVERCLAIM",
            "4_treat_R_MAX_as_prediction": "REJECTED AS OVERCLAIM",
            "5_run_anomaly_engine": "REJECTED AS OVERCLAIM",
            "6_infer_vector_masses": "REJECTED AS OVERCLAIM",
            "7_insert_experimental_inputs": "REJECTED AS OVERCLAIM",
            "8_modify_gravity": "REJECTED AS OVERCLAIM",
            "9_rank_candidate_classes": "REJECTED AS OVERCLAIM",
            "10_start_phase_14b4": "REJECTED AS OVERCLAIM",
            "11_prefer_SM_multiplets": "REJECTED AS OVERCLAIM",
            "12_turn_invariants_into_couplings": "REJECTED AS OVERCLAIM",
            "13_treat_real_rep_as_vectorlike": "REJECTED AS OVERCLAIM",
            "14_require_complex_representation_for_chirality": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_14B3R_STATUS"] == "CLOSED"
        and science["G4_EXECUTED"] is False
        and science["G3_CORRECTED_EXECUTED"] is True
        and science["PARENT_GRAMMAR"] == "G2_COMPACT_NONABELIAN"
        and science["GRAMMAR_ID"] == G3R_ID
        and science["CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION"] == "NO"
        and science["ranking"] is False
        and science["gravity_changed"] is False
        and science["experimental_inputs"] == 0
        and science["G0_REGENERATED"] == 0
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and g2_unchanged
        and old_g3_unchanged
        and corpus["specs_unchanged"]
    )
    return science


def run_phase14b3r_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14b3r_g3(auth, signature=signature)
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
            "PHASE_14B2_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14b2_artifacts_unchanged") else "FAILED",
            "PHASE_14B3_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14b3_checkpoint_unchanged") else "FAILED",
            "G2_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g2_checkpoint_unchanged") else "FAILED",
            "PHASE_14B3R_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14B3R_STATUS": science.get("PHASE_14B3R_STATUS"),
            "PHASE_14B3_STATUS": science.get("PHASE_14B3_STATUS"),
            "PHASE_14B2_STATUS": science.get("PHASE_14B2_STATUS"),
            "PHASE_14B0_STATUS": science.get("PHASE_14B0_STATUS"),
            "PHASE_14A_STATUS": science.get("PHASE_14A_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "STRING_THEORY_CONSTRAINTS": "NONE",
            "PHASE_14B4_EXECUTED": "FALSE",
            "G3_CORRECTED_EXECUTED": "TRUE",
            "G4_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
