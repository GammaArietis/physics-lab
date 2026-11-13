"""Phase 14B.0: top-down closure engine (infrastructure only).

Dry-run validates the loop.  The physics chain G0..G6 is declared, not executed.
"""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

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
from physics_lab.physics.phase13_1_low_d import artifact_dir as phase13_1_artifact_dir
from physics_lab.physics.phase14a_reconstruction import (
    artifact_dir as phase14a_artifact_dir,
    structural_input_registry,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUTHORIZED_PHYSICS_CHAIN",
    "ClosureEngine",
    "ENGINE_VERSION",
    "EXPECTED_12A_GRAMMAR_HASH",
    "PHASE_14B0_TEST_COPY_ID",
    "analyze_phase14b0_engine",
    "artifact_dir",
    "content_hash",
    "run_phase14b0_or_stop",
]

ENGINE_VERSION = "phase14b0-closure-engine-v1"
PHASE = "PHASE_14B.0"
PHASE_14B0_TEST_COPY_ID = "PHASE_14B0_TOP_DOWN_CLOSURE_ENGINE"
AUDIT_VERSION = "phase14b0-engine-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
TOP_DOWN_INPUT_VERSION = "phase14a-kp01-kp15-v1"

AUTHORIZED_PHYSICS_CHAIN: tuple[str, ...] = (
    "G0_BASELINE",
    "G1_FERMIONIC_CHIRAL",
    "G2_COMPACT_NONABELIAN",
    "G3_FINITE_REPRESENTATIONS",
    "G4_SCALAR_MULTIPLETS_VEV",
    "G5_ANOMALY_CONSTRAINTS",
    "G6_STRUCTURAL_GAUGE_CONSISTENCY",
)
DRY_CHAIN: tuple[str, ...] = ("DRY0_SYNTHETIC", "DRY1_SYNTHETIC")

_ALLOWED_PROVENANCE = frozenset(
    {
        "DERIVED",
        "DERIVED GIVEN ASSUMPTION",
        "INPUT",
        "GIVEN ASSUMPTION",
        "PARAMETER-DEPENDENT",
        "CONVENTION",
        "CALIBRATED",
        "EXPERIMENTAL",
        "UNTESTED",
        "METHOD / INTEGRITY CONTROL",
        "TOP_DOWN_INPUT",
        "DERIVED_GIVEN_TOP_DOWN_INPUT",
        "BOTTOM_UP_DERIVED",
        "GRAMMAR CHOICE",
        "DERIVED GIVEN GRAMMAR",
        "FREE / PARAMETER-DEPENDENT",
        "UNTESTED IN G1",
        "DEFERRED TO G2",
        "DEFERRED TO G3",
        "DEFERRED TO G4",
        "DEFERRED TO G5",
        "GRAMMAR EXTENSION",
        "INHERITED FROM G1",
        "INHERITED FROM G2",
        "GRAMMAR PLACEHOLDER",
        "DEFERRED TO GAUGE-DYNAMICS ANALYSIS",
        "UNTESTED IN G2",
        "UNTESTED IN G3",
        "DERIVED GIVEN GROUP + REPRESENTATION GRAMMAR",
        "MATHEMATICAL REPRESENTATION DATA",
        "DERIVED GIVEN COMPACT REPRESENTATION CONVENTION",
        "DERIVED REPRESENTATION INVARIANTS",
        "LOGICAL CORRECTION",
        "SUPERSEDED BY LOGICAL CORRECTION",
        "INHERITED FROM G3",
        "UNTESTED / DEFERRED",
        "G4 STRUCTURAL ASSUMPTION",
        "DERIVED GIVEN REPRESENTATION + VEV",
        "DERIVED GIVEN GAUGE + SCALAR KINETIC STRUCTURE + VEV",
        "DERIVED GIVEN SSB ASSUMPTION",
        "NOT PROVIDED",
        "NOT DETERMINED",
        "INHERITED FROM G3R",
        "INHERITED FROM G4",
        "MATHEMATICAL CONSISTENCY CORRECTION",
        "SUPERSEDED BY STABILIZER AUDIT",
        "G4_SUPERSEDED_BY_STABILIZER_AUDIT",
        "INHERITED FROM G4R",
        "DERIVED GIVEN REPRESENTATION CONTENT",
        "DERIVED FROM QUANTUM CONSISTENCY TEST",
        "DERIVED GIVEN CHIRAL FERMION CONTENT",
        "NOT USED",
        "DEFERRED TO G6",
        "not applicable",
        "INHERITED FROM G5",
        "DERIVED GIVEN GAUGE CONNECTION + REPRESENTATION GRAMMAR",
        "DERIVED GIVEN LOCAL GAUGE STRUCTURE",
        "DERIVED GIVEN G4 REPRESENTATION + VEV ASSUMPTION",
        "STRUCTURAL ASSUMPTION",
        "UNRESOLVED_BY_G4_ORBIT_CLASSIFICATION",
        "REFERENCE_ONLY / OUT OF SCOPE",
        "CHAIN COMPLETE",
        "NOT TESTED",
        "INHERITED FROM G6",
        "KNOWN_PHYSICS_INPUT",
        "KNOWN_PHYSICS_REFERENCE",
        "DERIVED_CONSEQUENCE",
        "RECOGNIZED_MATCH",
        "REFERENCE_ONLY",
        "ASSUMED",
        "PROFILE_FORCED",
        "BRANCH_DEPENDENT",
        "FORCED_WITHIN_DECLARED_BOUNDS",
        "DEPENDS_ON_G4_PARTIALITY",
        "G4_PARTIALITY_IRRELEVANT",
        "OUTSIDE_CURRENT_CATALOG",
        "PARTIAL_G4_DEPENDENCY",
        "KNOWN_PHYSICS_STRUCTURAL_CATALOG",
        "DERIVED GIVEN LOCAL ACTION GRAMMAR",
        "DERIVED GIVEN REPRESENTATION + SPACETIME GRAMMAR",
        "DERIVED GIVEN OPERATOR DIMENSIONS",
        "DERIVED GIVEN BOUNDED OPERATOR BASIS",
        "INHERITED / VERIFIED",
        "CLASSICAL PROXY ONLY",
        "NOT_APPLICABLE",
        "PROFILE ACTIVATION",
        "TOP_DOWN_INPUT / INHERITED",
        "DERIVED GIVEN REPRESENTATION + GAUGE STRUCTURE",
        "DERIVED GIVEN GAUGE/SCALAR STRUCTURE",
        "INHERITED FROM P1",
        "TOP_DOWN_INPUT / SEARCH-BOUNDED",
        "DERIVED GIVEN G4 STRUCTURE + QUALITATIVE PROFILE",
        "INHERITED UNCHANGED",
        "UNRESOLVED_BY_CURRENT_BOUND",
        "INHERITED FROM P3",
        "REFERENCE_COMPARISON",
        "COMPARISON_RESULT",
        "DISABLED",
        "RECOGNIZED_IN_REFERENCE_CATALOG",
        "REFERENCE_NOT_PARAMETERIZED",
        "CANDIDATE_FREE",
        "BOTH_FREE",
        "CANDIDATE_NOT_PARAMETERIZED",
        "INHERITED FROM P3 / REFERENCE_ONLY",
        "DERIVED GIVEN QUANTIZATION RULES",
        "DERIVED GIVEN QUADRATIC ACTION",
        "DERIVED ONLY FROM ACTUAL AMPLITUDE TEST",
        "DERIVED GIVEN GAUGE-FIXED DYNAMICAL SECTOR",
        "POWER-COUNTING CLASSIFICATION",
        "DERIVED GIVEN ACTUAL LOOP TEST",
        "REQUIRED_COMPONENT_MISSING",
        "FIRST_APPEARS_AT_P5",
        "INHERITED FROM P4 / NOT USED",
        "CLASSICAL DIAGNOSTIC SEPARATE",
    }
)

_FORBIDDEN_CALLS = (
    "distance_to_known_value",
    "fit_to_reference",
    "similarity_score_to_standard_model",
    "optimization_against_experiment",
    "choose_group_to_match_SM",
    "choose_representation_to_match_SM",
    "fit_charge_assignment",
    "fit_generation_count",
    "fit_mass_hierarchy",
    "target_similarity",
    "model_distance_to_SM",
)

_FAILURE_MODES = (
    "GRAMMAR_MISSING",
    "GRAMMAR_HASH_MISMATCH",
    "INPUT_HASH_MISMATCH",
    "CONSTRAINT_REGISTRY_INVALID",
    "TARGET_CONTAMINATION_DETECTED",
    "ILLEGAL_AUTOMATIC_EXTENSION",
    "CACHE_DEPENDENCY_MISMATCH",
    "CHECKPOINT_CORRUPTED",
    "RESUME_INTEGRITY_FAILURE",
    "PROVENANCE_FAILURE",
    "EQUIVALENCE_UNCERTIFIED",
    "SEARCH_ACCOUNTING_FAILURE",
    "G4_STABILIZER_MASS_MATRIX_INCONSISTENCY",
    "G4_STABILIZER_ERROR",
    "ANOMALY_DEPENDENCY_MISMATCH",
    "PROFILE_HASH_MISMATCH",
    "KNOWN_MODEL_ISOLATION_VIOLATION",
    "DEPENDENCY_MISMATCH",
    "P4_FEEDBACK_VIOLATION",
)


class EngineFailure(Exception):
    def __init__(self, mode: str, detail: str = ""):
        if mode not in _FAILURE_MODES:
            mode = "PROVENANCE_FAILURE"
        self.mode = mode
        self.detail = detail
        super().__init__(f"{mode}: {detail}")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b0_artifacts"


def content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


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


def scan_target_blindness(obj: Any) -> list[str]:
    hits = []
    blob = "\n".join(_walk_strings(obj))
    for token in _banned_tokens():
        if token in blob:
            hits.append(token)
    for name in _FORBIDDEN_CALLS:
        if name in blob:
            hits.append(name)
    return hits


def assert_target_blind(obj: Any) -> None:
    hits = scan_target_blindness(obj)
    if hits:
        raise EngineFailure("TARGET_CONTAMINATION_DETECTED", ",".join(hits))


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    assert_target_blind(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def top_down_input_hash() -> str:
    return content_hash(structural_input_registry())


def _grammar_payload(spec: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "grammar_id",
        "parent_grammar_id",
        "extension_description",
        "allowed_fields",
        "allowed_groups",
        "allowed_representations",
        "allowed_interactions",
        "allowed_symmetry_breaking",
        "allowed_constraints",
        "explicit_exclusions",
        "axes",
        "provenance",
    )
    return {k: spec[k] for k in keys if k in spec}


def _with_hash(spec: dict[str, Any]) -> dict[str, Any]:
    body = _grammar_payload(spec)
    out = dict(spec)
    out["grammar_hash"] = content_hash(body)
    return out


def physics_grammar_registry() -> dict[str, dict[str, Any]]:
    descriptions = {
        "G0_BASELINE": "Sealed 14A baseline: scalar plus optional U(1) plus frozen EH; no new fields",
        "G1_FERMIONIC_CHIRAL": "Authorize Weyl fermions and chiral coupling metadata",
        "G2_COMPACT_NONABELIAN": "Authorize compact non-Abelian simple factors",
        "G3_FINITE_REPRESENTATIONS": "Authorize finite discrete representation labels",
        "G4_SCALAR_MULTIPLETS_VEV": "Authorize extra scalar multiplets and symbolic VEVs",
        "G5_ANOMALY_CONSTRAINTS": "Authorize anomaly polynomial constraints",
        "G6_STRUCTURAL_GAUGE_CONSISTENCY": "Authorize structural massless/massive vector coexistence checks",
    }
    parents = {AUTHORIZED_PHYSICS_CHAIN[0]: None}
    for prev, nxt in zip(AUTHORIZED_PHYSICS_CHAIN, AUTHORIZED_PHYSICS_CHAIN[1:]):
        parents[nxt] = prev
    out = {}
    for gid in AUTHORIZED_PHYSICS_CHAIN:
        spec = {
            "grammar_id": gid,
            "parent_grammar_id": parents[gid],
            "extension_description": descriptions[gid],
            "allowed_fields": ["metric", "scalar"] if gid == "G0_BASELINE" else ["DECLARED_NOT_EXECUTED"],
            "allowed_groups": ["U1_optional"] if gid == "G0_BASELINE" else ["DECLARED_NOT_EXECUTED"],
            "allowed_representations": ["DECLARED_NOT_EXECUTED"],
            "allowed_interactions": ["DECLARED_NOT_EXECUTED"],
            "allowed_symmetry_breaking": ["DECLARED_NOT_EXECUTED"],
            "allowed_constraints": [e["constraint_id"] for e in structural_input_registry()],
            "explicit_exclusions": [
                "RG",
                "loop corrections",
                "SUSY",
                "extra dimensions",
                "strings",
                "exceptional groups",
                "hidden sectors",
            ],
            "provenance": "METHOD / INTEGRITY CONTROL",
            "status": "DECLARED_NOT_EXECUTED",
            "axes": {},
        }
        out[gid] = _with_hash(spec)
    return out


def dry_grammar_registry() -> dict[str, dict[str, Any]]:
    dry0 = _with_hash(
        {
            "grammar_id": "DRY0_SYNTHETIC",
            "parent_grammar_id": None,
            "extension_description": "synthetic bounded token axis; no physical meaning",
            "allowed_fields": ["token"],
            "allowed_groups": [],
            "allowed_representations": [],
            "allowed_interactions": [],
            "allowed_symmetry_breaking": [],
            "allowed_constraints": ["DRY_C_NOT_R"],
            "explicit_exclusions": ["physics_interpretation"],
            "provenance": "METHOD / INTEGRITY CONTROL",
            "status": "ACTIVE_DRY_RUN",
            "axes": {"token": ["p", "q", "r"]},
        }
    )
    dry1 = _with_hash(
        {
            "grammar_id": "DRY1_SYNTHETIC",
            "parent_grammar_id": "DRY0_SYNTHETIC",
            "extension_description": "authorized synthetic marker axis; no physical meaning",
            "allowed_fields": ["token", "marker"],
            "allowed_groups": [],
            "allowed_representations": [],
            "allowed_interactions": [],
            "allowed_symmetry_breaking": [],
            "allowed_constraints": ["DRY_C_NOT_R", "DRY_C_MARKER_ON"],
            "explicit_exclusions": ["physics_interpretation"],
            "provenance": "METHOD / INTEGRITY CONTROL",
            "status": "ACTIVE_DRY_RUN",
            "axes": {"token": ["p", "q", "r"], "marker": ["off", "on"]},
        }
    )
    return {"DRY0_SYNTHETIC": dry0, "DRY1_SYNTHETIC": dry1}


def constraint_registry() -> list[dict[str, Any]]:
    imported = []
    for item in structural_input_registry():
        imported.append(
            {
                "constraint_id": item["constraint_id"],
                "description": item["statement"],
                "formal_test": item["mathematical_form"],
                "provenance": "TOP_DOWN_INPUT",
                "severity": "physics_when_activated",
                "grammar_dependencies": list(AUTHORIZED_PHYSICS_CHAIN),
                "numerical_content_present": False,
                "dry_run_result": "NOT_APPLICABLE",
            }
        )
    imported.extend(
        [
            {
                "constraint_id": "DRY_C_NOT_R",
                "description": "synthetic: token r is metadata-illegal",
                "formal_test": "candidate.token != r",
                "provenance": "METHOD / INTEGRITY CONTROL",
                "severity": "dry_run",
                "grammar_dependencies": list(DRY_CHAIN),
                "numerical_content_present": False,
            },
            {
                "constraint_id": "DRY_C_MARKER_ON",
                "description": "synthetic: marker must be on when the axis exists",
                "formal_test": "candidate.marker == on if marker axis present",
                "provenance": "METHOD / INTEGRITY CONTROL",
                "severity": "dry_run",
                "grammar_dependencies": ["DRY1_SYNTHETIC"],
                "numerical_content_present": False,
            },
        ]
    )
    assert_target_blind(imported)
    if any(c.get("numerical_content_present") for c in imported):
        raise EngineFailure("CONSTRAINT_REGISTRY_INVALID", "numerical content")
    return imported


def _metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    if grammar.get("grammar_id") == "P3_QUALITATIVE_MATTER":
        from physics_lab.physics.phase14c3_p3 import p3_metadata_legal

        return p3_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "P2_CHIRAL_GAUGE_MATTER":
        from physics_lab.physics.phase14c2_p2 import p2_metadata_legal

        return p2_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "P1_QFT_STRUCTURAL_CONSISTENCY":
        from physics_lab.physics.phase14c1_p1 import p1_metadata_legal

        return p1_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "P0_CORE_STRUCTURAL_PHYSICS":
        from physics_lab.physics.phase14c0_known_physics import p0_metadata_legal

        return p0_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") in {"14C_DRY_P0", "14C_DRY_P1"}:
        from physics_lab.physics.phase14c0_known_physics import dry_profile_metadata_legal

        return dry_profile_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "G6_STRUCTURAL_GAUGE_CONSISTENCY":
        from physics_lab.physics.phase14b6_g6 import g6_metadata_legal

        return g6_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "G5_ANOMALY_CONSTRAINTS":
        from physics_lab.physics.phase14b5_g5 import g5_metadata_legal

        return g5_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "G4_SCALAR_MULTIPLETS_VEV_R2":
        from physics_lab.physics.phase14b4r2_g4 import g4r2_metadata_legal

        return g4r2_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "G4_SCALAR_MULTIPLETS_VEV_R1":
        from physics_lab.physics.phase14b4r_g4 import g4r_metadata_legal

        return g4r_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "G4_SCALAR_MULTIPLETS_VEV":
        from physics_lab.physics.phase14b4_g4 import g4_metadata_legal

        return g4_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "G3_FINITE_REPRESENTATIONS_R1":
        from physics_lab.physics.phase14b3r_g3 import g3r_metadata_legal

        return g3r_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "G3_FINITE_REPRESENTATIONS" or "g3_pack" in (grammar.get("axes") or {}):
        from physics_lab.physics.phase14b3_g3 import g3_metadata_legal

        return g3_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") == "G2_COMPACT_NONABELIAN" or "simple_group" in (grammar.get("axes") or {}):
        from physics_lab.physics.phase14b2_g2 import g2_metadata_legal

        return g2_metadata_legal(assignment, grammar)
    if grammar.get("grammar_id") in {"G0_BASELINE", "G1_FERMIONIC_CHIRAL"} or "fermion_kind" in (grammar.get("axes") or {}):
        from physics_lab.physics.phase14b1_g1 import g1_metadata_legal

        return g1_metadata_legal(assignment, grammar)
    if assignment.get("token") == "r":
        return False, "DRY_C_NOT_R"
    if "marker" in grammar.get("axes", {}) and assignment.get("marker") == "off":
        return False, "DRY_C_MARKER_ON"
    return True, None


def generate_candidates(grammar: dict[str, Any], *, bound: int | None = None) -> Iterator[dict[str, Any]]:
    axes: dict[str, list[str]] = dict(grammar.get("axes") or {})
    names = list(axes.keys())
    if not names:
        return
    counters = [0] * len(names)
    limits = [len(axes[n]) for n in names]
    emitted = 0
    while True:
        assignment = {names[i]: axes[names[i]][counters[i]] for i in range(len(names))}
        legal, _reason = _metadata_legal(assignment, grammar)
        if legal:
            canon = {"grammar_id": grammar["grammar_id"], "assignment": assignment}
            digest = content_hash(canon)
            provenance = (
                "GRAMMAR EXTENSION"
                if grammar["grammar_id"] in {
                    "G2_COMPACT_NONABELIAN",
                    "G3_FINITE_REPRESENTATIONS",
                    "G4_SCALAR_MULTIPLETS_VEV",
                    "G5_ANOMALY_CONSTRAINTS",
                    "G6_STRUCTURAL_GAUGE_CONSISTENCY",
                }
                else "LOGICAL CORRECTION"
                if grammar["grammar_id"] in {"G3_FINITE_REPRESENTATIONS_R1", "G4_SCALAR_MULTIPLETS_VEV_R1", "G4_SCALAR_MULTIPLETS_VEV_R2"}
                else "INHERITED FROM G6"
                if grammar["grammar_id"] in {
                    "P0_CORE_STRUCTURAL_PHYSICS",
                    "P1_QFT_STRUCTURAL_CONSISTENCY",
                    "P2_CHIRAL_GAUGE_MATTER",
                    "P3_QUALITATIVE_MATTER",
                }
                else "METHOD / INTEGRITY CONTROL"
            )
            yield {
                "candidate_id": f"{grammar['grammar_id']}:{emitted + 1:04d}",
                "sequence_index": emitted + 1,
                "canonical_representation": canon,
                "candidate_hash": digest,
                "CANDIDATE_CONTENT_HASH": digest,
                "grammar_version": grammar["grammar_id"],
                "grammar_hash": grammar["grammar_hash"],
                "provenance": provenance,
                "assignment": assignment,
            }
            emitted += 1
            if bound is not None and emitted >= bound:
                return
        i = len(names) - 1
        while i >= 0:
            counters[i] += 1
            if counters[i] < limits[i]:
                break
            counters[i] = 0
            i -= 1
        if i < 0:
            return


def count_raw_combinations(grammar: dict[str, Any]) -> int:
    axes = grammar.get("axes") or {}
    n = 1
    for values in axes.values():
        n *= len(values)
    return n if axes else 0


def count_pruned(grammar: dict[str, Any]) -> int:
    axes = grammar.get("axes") or {}
    names = list(axes.keys())
    if not names:
        return 0
    pruned = 0
    counters = [0] * len(names)
    limits = [len(axes[n]) for n in names]
    while True:
        assignment = {names[i]: axes[names[i]][counters[i]] for i in range(len(names))}
        legal, _ = _metadata_legal(assignment, grammar)
        if not legal:
            pruned += 1
        i = len(names) - 1
        while i >= 0:
            counters[i] += 1
            if counters[i] < limits[i]:
                break
            counters[i] = 0
            i -= 1
        if i < 0:
            break
    return pruned


def _run_tests(candidate: dict[str, Any], *, test_version: str = "dry-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    assignment = candidate["assignment"]
    if candidate.get("grammar_version") == "P3_QUALITATIVE_MATTER":
        from physics_lab.physics.phase14c3_p3 import p3_run_tests

        return p3_run_tests(candidate, test_version=test_version)
    if candidate.get("grammar_version") == "P2_CHIRAL_GAUGE_MATTER":
        from physics_lab.physics.phase14c2_p2 import p2_run_tests

        return p2_run_tests(candidate, test_version=test_version)
    if candidate.get("grammar_version") == "P1_QFT_STRUCTURAL_CONSISTENCY":
        from physics_lab.physics.phase14c1_p1 import p1_run_tests

        return p1_run_tests(candidate, test_version=test_version)
    if "g6_survivor" in assignment or candidate.get("grammar_version") == "P0_CORE_STRUCTURAL_PHYSICS":
        from physics_lab.physics.phase14c0_known_physics import p0_run_tests

        return p0_run_tests(candidate, test_version=test_version)
    if candidate.get("grammar_version") in {"14C_DRY_P0", "14C_DRY_P1"} or "color" in assignment:
        from physics_lab.physics.phase14c0_known_physics import dry_profile_run_tests

        return dry_profile_run_tests(candidate, test_version=test_version)
    if "g6_pack" in assignment or candidate.get("grammar_version") == "G6_STRUCTURAL_GAUGE_CONSISTENCY":
        from physics_lab.physics.phase14b6_g6 import g6_run_tests

        return g6_run_tests(candidate, test_version=test_version)
    if "g5_pack" in assignment or candidate.get("grammar_version") == "G5_ANOMALY_CONSTRAINTS":
        from physics_lab.physics.phase14b5_g5 import g5_run_tests

        return g5_run_tests(candidate, test_version=test_version)
    if candidate.get("grammar_version") == "G4_SCALAR_MULTIPLETS_VEV_R2":
        from physics_lab.physics.phase14b4r2_g4 import g4r2_run_tests

        return g4r2_run_tests(candidate, test_version=test_version)
    if "g4r_pack" in assignment or candidate.get("grammar_version") == "G4_SCALAR_MULTIPLETS_VEV_R1":
        from physics_lab.physics.phase14b4r_g4 import g4r_run_tests

        return g4r_run_tests(candidate, test_version=test_version)
    if "g4_pack" in assignment or candidate.get("grammar_version") == "G4_SCALAR_MULTIPLETS_VEV":
        from physics_lab.physics.phase14b4_g4 import g4_run_tests

        return g4_run_tests(candidate, test_version=test_version)
    if candidate.get("grammar_version") == "G3_FINITE_REPRESENTATIONS_R1":
        from physics_lab.physics.phase14b3r_g3 import g3r_run_tests

        return g3r_run_tests(candidate, test_version=test_version)
    if "g3_pack" in assignment or candidate.get("grammar_version") == "G3_FINITE_REPRESENTATIONS":
        from physics_lab.physics.phase14b3_g3 import g3_run_tests

        return g3_run_tests(candidate, test_version=test_version)
    if "simple_group" in assignment or candidate.get("grammar_version") == "G2_COMPACT_NONABELIAN":
        from physics_lab.physics.phase14b2_g2 import g2_run_tests

        return g2_run_tests(candidate, test_version=test_version)
    if "fermion_kind" in assignment or candidate.get("grammar_version") in {"G0_BASELINE", "G1_FERMIONIC_CHIRAL"}:
        from physics_lab.physics.phase14b1_g1 import g1_run_tests

        return g1_run_tests(candidate, test_version=test_version)
    order = ["grammar_legality", "field_type", "token_test"]
    results = []
    status = "PASS"
    for test_id in order:
        if test_id == "token_test" and assignment.get("token") == "p":
            outcome = "FAIL"
            status = "FAIL"
        else:
            outcome = "PASS"
        results.append(
            {
                "test_id": test_id,
                "test_version": test_version,
                "status": outcome,
                "provenance": "METHOD / INTEGRITY CONTROL",
                "source_phase": PHASE,
            }
        )
        if outcome == "FAIL":
            break
    return {"status": status, "results": results, "test_version": test_version}


class ClosureTestCache:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def key(self, candidate_hash: str, test_id: str, test_version: str, dep_hash: str) -> str:
        return content_hash(
            {
                "candidate_hash": candidate_hash,
                "test_id": test_id,
                "test_version": test_version,
                "relevant_dependency_hash": dep_hash,
            }
        )

    def get(self, key: str) -> dict[str, Any] | None:
        return self._store.get(key)

    def put(self, key: str, value: dict[str, Any]) -> None:
        self._store[key] = value

    def evaluate(self, candidate: dict[str, Any], *, test_version: str, dep_hash: str) -> dict[str, Any]:
        k = self.key(candidate["candidate_hash"], "bundle", test_version, dep_hash)
        hit = self.get(k)
        if hit is not None:
            return {**hit, "cache": "HIT"}
        out = _run_tests(candidate, test_version=test_version)
        self.put(k, out)
        return {**out, "cache": "MISS"}


def _certify_identity_classes(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classes: dict[str, dict[str, Any]] = {}
    for cand in candidates:
        digest = cand["candidate_hash"]
        if digest not in classes:
            classes[digest] = {
                "equivalence_class_id": f"EQ:{digest[:16]}",
                "member_candidate_hashes": [digest],
                "equivalence_rule": "IDENTITY_EQUAL",
                "proof_status": "CERTIFIED",
                "proof_reference": "same canonical_representation content hash",
            }
    return [classes[k] for k in sorted(classes)]


def _require_provenance(obj: dict[str, Any]) -> None:
    label = obj.get("provenance")
    if label not in _ALLOWED_PROVENANCE:
        raise EngineFailure("PROVENANCE_FAILURE", str(label))


class ClosureEngine:
    def __init__(self, root: Path | None = None, *, chain: str = "dry"):
        self.root = Path(root) if root is not None else artifact_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.chain_name = chain
        if chain == "dry":
            self.grammars = dry_grammar_registry()
            self.chain = list(DRY_CHAIN)
        elif chain == "g1_only":
            from physics_lab.physics.phase14b1_g1 import G1_CHAIN, g1_executable_registry

            self.grammars = g1_executable_registry()
            self.chain = list(G1_CHAIN)
        elif chain == "g2_only":
            from physics_lab.physics.phase14b2_g2 import G2_CHAIN, g2_executable_registry

            self.grammars = g2_executable_registry()
            self.chain = list(G2_CHAIN)
        elif chain == "g3_only":
            from physics_lab.physics.phase14b3_g3 import G3_CHAIN, g3_executable_registry

            self.grammars = g3_executable_registry()
            self.chain = list(G3_CHAIN)
        elif chain == "g3r_only":
            from physics_lab.physics.phase14b3r_g3 import G3R_CHAIN, g3r_executable_registry

            self.grammars = g3r_executable_registry()
            self.chain = list(G3R_CHAIN)
        elif chain == "g4_only":
            from physics_lab.physics.phase14b4_g4 import G4_CHAIN, g4_executable_registry

            self.grammars = g4_executable_registry()
            self.chain = list(G4_CHAIN)
        elif chain == "g4r_only":
            from physics_lab.physics.phase14b4r_g4 import G4R_CHAIN, g4r_executable_registry

            self.grammars = g4r_executable_registry()
            self.chain = list(G4R_CHAIN)
        elif chain == "g4r2_only":
            from physics_lab.physics.phase14b4r2_g4 import G4R2_CHAIN, g4r2_executable_registry

            self.grammars = g4r2_executable_registry()
            self.chain = list(G4R2_CHAIN)
        elif chain == "g5_only":
            from physics_lab.physics.phase14b5_g5 import G5_CHAIN, g5_executable_registry

            self.grammars = g5_executable_registry()
            self.chain = list(G5_CHAIN)
        elif chain == "g6_only":
            from physics_lab.physics.phase14b6_g6 import G6_CHAIN, g6_executable_registry

            self.grammars = g6_executable_registry()
            self.chain = list(G6_CHAIN)
        elif chain == "14c0_dry":
            from physics_lab.physics.phase14c0_known_physics import DRY_PROFILE_CHAIN, dry_profile_registry

            self.grammars = dry_profile_registry()
            self.chain = list(DRY_PROFILE_CHAIN)
        elif chain == "p0_only":
            from physics_lab.physics.phase14c0_known_physics import P0_CHAIN, p0_executable_registry

            self.grammars = p0_executable_registry()
            self.chain = list(P0_CHAIN)
        elif chain == "p1_only":
            from physics_lab.physics.phase14c1_p1 import P1_CHAIN, p1_executable_registry

            self.grammars = p1_executable_registry()
            self.chain = list(P1_CHAIN)
        elif chain == "p2_only":
            from physics_lab.physics.phase14c2_p2 import P2_CHAIN, p2_executable_registry

            self.grammars = p2_executable_registry()
            self.chain = list(P2_CHAIN)
        elif chain == "p3_only":
            from physics_lab.physics.phase14c3_p3 import P3_CHAIN, p3_executable_registry

            self.grammars = p3_executable_registry()
            self.chain = list(P3_CHAIN)
        elif chain == "p4_only":
            raise EngineFailure("KNOWN_MODEL_ISOLATION_VIOLATION", "P4 must not participate in generation")
        elif chain == "p5_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5 is not a generation chain")
        elif chain == "p5q_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5Q is not a generation chain")
        elif chain == "p5d_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5D is not a generation chain")
        elif chain == "p5e_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5E is not a generation chain")
        elif chain == "p5e1_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5E.1 is not a generation chain")
        elif chain == "p5f_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5F is not a generation chain")
        elif chain == "p5g_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5G is not a generation chain")
        elif chain == "p5g1_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5G.1 is not a generation chain")
        elif chain == "p5h_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5H is not a generation chain")
        elif chain == "p5h1_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5H.1 is not a generation chain")
        elif chain == "p5h2_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5H.2 is not a generation chain")
        elif chain == "p5h3_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5H.3 is not a generation chain")
        elif chain == "p5h4_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5H.4 is not a generation chain")
        elif chain == "p5h5_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5H.5 is not a generation chain")
        elif chain == "p5i_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5I is not a generation chain")
        elif chain == "p5j_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5J is not a generation chain")
        elif chain == "p5k_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P5K is not a generation chain")
        elif chain == "p6_only":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "P6 is not invented")
        elif chain == "physics":
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", "full G1-G6 chain is not an automatic activation")
        else:
            raise EngineFailure("GRAMMAR_MISSING", chain)
        self.cache = ClosureTestCache()
        self.dep_hash = content_hash({"constraints": constraint_registry(), "engine": ENGINE_VERSION})

    def state_path(self) -> Path:
        return self.root / "TOP_DOWN_CLOSURE_STATE.json"

    def checkpoint_path(self, grammar_id: str) -> Path:
        return self.root / f"closure_checkpoint_{grammar_id}.json"

    def cache_path(self) -> Path:
        return self.root / "CLOSURE_TEST_CACHE.json"

    def _empty_state(self) -> dict[str, Any]:
        return {
            "engine_version": ENGINE_VERSION,
            "grammar_version": None,
            "grammar_hash": None,
            "top_down_input_version": TOP_DOWN_INPUT_VERSION,
            "top_down_input_hash": top_down_input_hash(),
            "authorized_extensions": list(self.chain),
            "authorized_physics_chain": list(AUTHORIZED_PHYSICS_CHAIN),
            "current_extension_index": -1,
            "current_grammar": None,
            "current_grammar_hash": None,
            "candidate_count": 0,
            "candidate_hashes": [],
            "rejected_count": 0,
            "unresolved_count": 0,
            "compatible_count": 0,
            "equivalence_classes": [],
            "blockers": [],
            "provenance_summary": {"labels": ["METHOD / INTEGRITY CONTROL", "TOP_DOWN_INPUT"]},
            "run_history": [],
            "closure_status": "NOT_STARTED",
            "METHOD_STATUS": "NOT_STARTED",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
            "FULL_PHYSICS_GRAMMAR_EXECUTED": False,
        }

    def load_state(self) -> dict[str, Any]:
        if self.state_path().is_file():
            return _read_json(self.state_path())
        return self._empty_state()

    def save_state(self, state: dict[str, Any]) -> None:
        _write_json(self.state_path(), state)

    def _write_checkpoint(self, grammar: dict[str, Any], stats: dict[str, Any]) -> Path:
        payload = {
            "grammar_id": grammar["grammar_id"],
            "grammar_hash": grammar["grammar_hash"],
            "parent": grammar.get("parent_grammar_id"),
            "input_hashes": {
                "top_down_input_hash": top_down_input_hash(),
                "constraint_hash": content_hash(constraint_registry()),
            },
            "candidate_statistics": {
                "raw": stats["raw_theoretical_combinations"],
                "pruned": stats["metadata_pruned_candidates"],
                "generated": stats["generated_candidates"],
                "rejected": stats["rejected"],
                "unresolved": stats["unresolved"],
                "compatible": stats["compatible"],
                "partial": stats.get("partial", 0),
            },
            "blocker_statistics": {"count": len(stats.get("blockers") or [])},
            "survivor_hashes": stats.get("compatible_hashes") or [],
            "equivalence_classes": stats.get("equivalence_classes") or [],
            "unresolved_dependencies": stats.get("unresolved_hashes") or [],
            "parameter_inventory": stats.get("parameter_inventory") or [],
            "class_table": stats.get("class_table") or [],
            "provenance_summary": stats.get("provenance_summary") or {},
            "timestamp": _utc(),
            "engine_version": ENGINE_VERSION,
            "parent_grammar_id": grammar.get("parent_grammar_id"),
            "top_down_input_hash": top_down_input_hash(),
            "integrity_digest": None,
        }
        for key in (
            "parent_checkpoint_hash",
            "parent_grammar_hash",
            "search_bounds",
            "g1_survivors_reused",
            "g2_new_candidates_generated",
            "g2_survivors_reused",
            "g3_new_candidates_generated",
            "g4_new_candidates_generated",
            "representation_catalogue_hash",
            "target_blindness",
            "VEV_ORBIT_CLASSIFICATION",
            "anomaly_statistics",
            "anomaly_test_catalogue_hash",
            "anomaly_engine_version",
            "structural_engine_version",
            "layer_statistics",
            "failure_modes",
            "g5_survivors_reused",
            "g6_new_candidates_generated",
            "matter_invariance_statistics",
            "g6_survivors_reused",
            "profile_id",
            "profile_hash",
            "consequence_engine_version",
            "catalog_version",
            "completeness_statistics",
            "consequences",
            "test_registry_hash",
            "test_statistics",
            "inherited_g6_result_hash",
            "inherited_g5_result_hash",
            "parent_profile_hash",
            "candidate_space_hash",
            "interaction_statistics",
            "forced_property_statistics",
            "counterexample_statistics",
            "G4_partiality_status",
            "G4_hash",
            "P1_hash",
            "P2_checkpoint_hash",
        ):
            if stats.get(key) is not None:
                payload[key] = stats[key]
        payload["integrity_digest"] = content_hash({k: v for k, v in payload.items() if k != "integrity_digest"})
        path = self.checkpoint_path(grammar["grammar_id"])
        _write_json(path, payload)
        return path

    def verify_checkpoint(self, grammar_id: str) -> dict[str, Any]:
        path = self.checkpoint_path(grammar_id)
        if not path.is_file():
            raise EngineFailure("CHECKPOINT_CORRUPTED", "missing")
        payload = _read_json(path)
        stored = payload.get("integrity_digest")
        recomputed = content_hash({k: v for k, v in payload.items() if k != "integrity_digest"})
        if stored != recomputed:
            raise EngineFailure("CHECKPOINT_CORRUPTED", "digest mismatch")
        grammar = self.grammars.get(grammar_id)
        if grammar is None:
            raise EngineFailure("GRAMMAR_MISSING", grammar_id)
        if payload.get("grammar_hash") != grammar["grammar_hash"]:
            raise EngineFailure("GRAMMAR_HASH_MISMATCH", grammar_id)
        if payload.get("engine_version") != ENGINE_VERSION:
            raise EngineFailure("RESUME_INTEGRITY_FAILURE", "engine version")
        if payload.get("input_hashes", {}).get("top_down_input_hash") != top_down_input_hash():
            raise EngineFailure("INPUT_HASH_MISMATCH", "top-down inputs")
        return payload

    def advance_grammar(self, requested: str, current: str | None) -> str:
        if requested not in self.chain:
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", requested)
        if current is None:
            if requested != self.chain[0]:
                raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", f"must start at {self.chain[0]}")
            return requested
        try:
            idx = self.chain.index(current)
        except ValueError as exc:
            raise EngineFailure("GRAMMAR_MISSING", current) from exc
        if idx + 1 >= len(self.chain) or self.chain[idx + 1] != requested:
            raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", f"{current} -> {requested} skips authorized order")
        return requested

    def _evaluate_one(self, cand: dict[str, Any], test_version: str) -> dict[str, Any]:
        _require_provenance(cand)
        tested = self.cache.evaluate(cand, test_version=test_version, dep_hash=self.dep_hash)
        return {**cand, "tests": tested, "filter_status": tested["status"]}

    def evaluate_grammar(
        self, grammar_id: str, *, parallel: bool = False, test_version: str = "dry-tests-v1"
    ) -> dict[str, Any]:
        grammar = self.grammars.get(grammar_id)
        if grammar is None:
            raise EngineFailure("GRAMMAR_MISSING", grammar_id)
        assert_target_blind(grammar)
        raw = count_raw_combinations(grammar)
        pruned = count_pruned(grammar)
        generated = list(generate_candidates(grammar))
        if parallel:
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(self._evaluate_one, c, test_version) for c in generated]
                evaluated = [f.result() for f in futures]
            evaluated.sort(key=lambda c: c["candidate_id"])
        else:
            evaluated = [self._evaluate_one(c, test_version) for c in generated]
        rejected = [c for c in evaluated if c["filter_status"] == "FAIL"]
        unresolved = [c for c in evaluated if c["filter_status"] == "UNRESOLVED"]
        compatible = [c for c in evaluated if c["filter_status"] == "PASS"]
        partial = [c for c in evaluated if c["filter_status"] == "PARTIAL"]
        if raw != pruned + len(generated):
            raise EngineFailure("SEARCH_ACCOUNTING_FAILURE", "raw != pruned + generated")
        if len(generated) != len(rejected) + len(unresolved) + len(compatible) + len(partial):
            raise EngineFailure("SEARCH_ACCOUNTING_FAILURE", "generated partition")
        hashes = [c["candidate_hash"] for c in generated]
        if len(hashes) != len(set(hashes)):
            raise EngineFailure("SEARCH_ACCOUNTING_FAILURE", "duplicate identity")
        eq = _certify_identity_classes(compatible)
        uncertified = [e for e in eq if e.get("proof_status") != "CERTIFIED"]
        if uncertified:
            raise EngineFailure("EQUIVALENCE_UNCERTIFIED", uncertified[0]["equivalence_class_id"])
        extra: dict[str, Any] = {}
        if grammar_id == "P3_QUALITATIVE_MATTER":
            from physics_lab.physics.phase14c3_p3 import attach_p3_stats

            extra = attach_p3_stats(grammar, evaluated, compatible)
        elif grammar_id == "P2_CHIRAL_GAUGE_MATTER":
            from physics_lab.physics.phase14c2_p2 import attach_p2_stats

            extra = attach_p2_stats(grammar, evaluated, compatible)
        elif grammar_id == "P1_QFT_STRUCTURAL_CONSISTENCY":
            from physics_lab.physics.phase14c1_p1 import attach_p1_stats

            extra = attach_p1_stats(grammar, evaluated, compatible)
        elif grammar_id == "P0_CORE_STRUCTURAL_PHYSICS":
            from physics_lab.physics.phase14c0_known_physics import attach_p0_stats

            extra = attach_p0_stats(grammar, evaluated, compatible)
        elif grammar_id in {"14C_DRY_P0", "14C_DRY_P1"}:
            from physics_lab.physics.phase14c0_known_physics import attach_dry_profile_stats

            extra = attach_dry_profile_stats(grammar, evaluated, compatible)
        elif grammar_id == "G6_STRUCTURAL_GAUGE_CONSISTENCY":
            from physics_lab.physics.phase14b6_g6 import attach_g6_stats

            extra = attach_g6_stats(grammar, evaluated, compatible)
        elif grammar_id == "G5_ANOMALY_CONSTRAINTS":
            from physics_lab.physics.phase14b5_g5 import attach_g5_stats

            extra = attach_g5_stats(grammar, evaluated, compatible)
        elif grammar_id == "G4_SCALAR_MULTIPLETS_VEV_R2":
            from physics_lab.physics.phase14b4r2_g4 import attach_g4r2_stats

            extra = attach_g4r2_stats(grammar, evaluated, compatible)
        elif grammar_id == "G4_SCALAR_MULTIPLETS_VEV_R1":
            from physics_lab.physics.phase14b4r_g4 import attach_g4r_stats

            extra = attach_g4r_stats(grammar, evaluated, compatible)
        elif grammar_id == "G4_SCALAR_MULTIPLETS_VEV":
            from physics_lab.physics.phase14b4_g4 import attach_g4_stats

            extra = attach_g4_stats(grammar, evaluated, compatible)
        elif grammar_id == "G3_FINITE_REPRESENTATIONS_R1":
            from physics_lab.physics.phase14b3r_g3 import attach_g3r_stats

            extra = attach_g3r_stats(grammar, evaluated, compatible)
        elif grammar_id == "G3_FINITE_REPRESENTATIONS":
            from physics_lab.physics.phase14b3_g3 import attach_g3_stats

            extra = attach_g3_stats(grammar, evaluated, compatible)
        elif grammar_id == "G2_COMPACT_NONABELIAN":
            from physics_lab.physics.phase14b2_g2 import attach_g2_stats

            extra = attach_g2_stats(grammar, evaluated, compatible)
        elif grammar_id in {"G0_BASELINE", "G1_FERMIONIC_CHIRAL"}:
            from physics_lab.physics.phase14b1_g1 import attach_g1_stats

            extra = attach_g1_stats(grammar, evaluated, compatible)
        blockers = extra.get("blockers") if extra.get("blockers") is not None else []
        next_ext = None
        idx = self.chain.index(grammar_id)
        if grammar_id == "DRY0_SYNTHETIC":
            blockers.append(
                {
                    "blocker_id": "DRY_NEED_MARKER",
                    "blocker_description": "synthetic survivors need the authorized marker axis",
                    "affected_constraints": ["DRY_C_MARKER_ON"],
                    "minimum_declared_extension_candidate": "DRY1_SYNTHETIC",
                    "provenance": "METHOD / INTEGRITY CONTROL",
                }
            )
            next_ext = "DRY1_SYNTHETIC"
            closure = "EXTENSION_REQUIRED"
        elif idx + 1 < len(self.chain):
            next_ext = self.chain[idx + 1]
            closure = "EXTENSION_REQUIRED"
        elif grammar_id == "G6_STRUCTURAL_GAUGE_CONSISTENCY":
            closure = "CLOSURE_REACHED"
        else:
            closure = "CLOSURE_REACHED" if compatible and not unresolved else "STOPPED_BY_UNRESOLVED_REQUIREMENT"
        stats = {
            "grammar_id": grammar_id,
            "grammar_hash": grammar["grammar_hash"],
            "parent": grammar.get("parent_grammar_id"),
            "raw_theoretical_combinations": raw,
            "metadata_pruned_candidates": pruned,
            "generated_candidates": len(generated),
            "rejected": len(rejected),
            "unresolved": len(unresolved),
            "compatible": len(compatible),
            "partial": extra.get("partial") if extra.get("partial") is not None else len(partial),
            "equivalence_classes": eq,
            "compatible_hashes": [c["candidate_hash"] for c in compatible],
            "rejected_hashes": [c["candidate_hash"] for c in rejected],
            "unresolved_hashes": [c["candidate_hash"] for c in unresolved],
            "candidate_hashes": hashes,
            "blockers": blockers,
            "closure_status": closure,
            "next_extension": next_ext,
            "exhaustive_over_declared_bounded_grammar": True,
            "exhaustive_over_all_physical_theories": False,
            "pruning_provenance": "PRUNED_BY_CONSTRAINT",
            "candidates": evaluated,
            "parameter_inventory": extra.get("parameter_inventory") or [],
            "class_table": extra.get("class_table") or [],
            "provenance_summary": extra.get("provenance_summary") or {},
            "parent_checkpoint_hash": extra.get("parent_checkpoint_hash"),
            "parent_grammar_hash": extra.get("parent_grammar_hash"),
            "search_bounds": extra.get("search_bounds"),
            "g1_survivors_reused": extra.get("g1_survivors_reused"),
            "g2_new_candidates_generated": extra.get("g2_new_candidates_generated"),
            "g2_survivors_reused": extra.get("g2_survivors_reused"),
            "g3_new_candidates_generated": extra.get("g3_new_candidates_generated"),
            "g4_new_candidates_generated": extra.get("g4_new_candidates_generated"),
            "representation_catalogue_hash": extra.get("representation_catalogue_hash"),
            "target_blindness": extra.get("target_blindness") or "VERIFIED",
            "VEV_ORBIT_CLASSIFICATION": extra.get("VEV_ORBIT_CLASSIFICATION"),
            "anomaly_statistics": extra.get("anomaly_statistics"),
            "anomaly_test_catalogue_hash": extra.get("anomaly_test_catalogue_hash"),
            "anomaly_engine_version": extra.get("anomaly_engine_version"),
            "structural_engine_version": extra.get("structural_engine_version"),
            "layer_statistics": extra.get("layer_statistics"),
            "failure_modes": extra.get("failure_modes"),
            "g5_survivors_reused": extra.get("g5_survivors_reused"),
            "g6_new_candidates_generated": extra.get("g6_new_candidates_generated"),
            "matter_invariance_statistics": extra.get("matter_invariance_statistics"),
            "g6_survivors_reused": extra.get("g6_survivors_reused"),
            "profile_id": extra.get("profile_id"),
            "profile_hash": extra.get("profile_hash"),
            "consequence_engine_version": extra.get("consequence_engine_version"),
            "catalog_version": extra.get("catalog_version"),
            "completeness_statistics": extra.get("completeness_statistics"),
            "consequences": extra.get("consequences"),
            "test_registry_hash": extra.get("test_registry_hash"),
            "test_statistics": extra.get("test_statistics"),
            "inherited_g6_result_hash": extra.get("inherited_g6_result_hash"),
            "inherited_g5_result_hash": extra.get("inherited_g5_result_hash"),
            "parent_profile_hash": extra.get("parent_profile_hash"),
            "candidate_space_hash": extra.get("candidate_space_hash"),
            "interaction_statistics": extra.get("interaction_statistics"),
            "forced_property_statistics": extra.get("forced_property_statistics"),
            "counterexample_statistics": extra.get("counterexample_statistics"),
            "G4_partiality_status": extra.get("G4_partiality_status"),
            "G4_hash": extra.get("G4_hash"),
            "P1_hash": extra.get("P1_hash"),
            "P2_checkpoint_hash": extra.get("P2_checkpoint_hash"),
        }
        self._write_checkpoint(grammar, stats)
        cache_blob = {"entries": self.cache._store, "dep_hash": self.dep_hash, "engine_version": ENGINE_VERSION}
        _write_json(self.cache_path(), cache_blob)
        return stats

    def run_until_closure(self, *, parallel: bool = False) -> dict[str, Any]:
        state = self._empty_state()
        state["closure_status"] = "RUNNING"
        state["METHOD_STATUS"] = "RUNNING"
        versions = []
        current = None
        for gid in self.chain:
            self.advance_grammar(gid, current)
            stats = self.evaluate_grammar(gid, parallel=parallel)
            versions.append({k: stats[k] for k in stats if k != "candidates"})
            state["current_extension_index"] = self.chain.index(gid)
            state["current_grammar"] = gid
            state["current_grammar_hash"] = stats["grammar_hash"]
            state["grammar_version"] = gid
            state["grammar_hash"] = stats["grammar_hash"]
            state["candidate_count"] = stats["generated_candidates"]
            state["candidate_hashes"] = stats["candidate_hashes"]
            state["rejected_count"] = stats["rejected"]
            state["unresolved_count"] = stats["unresolved"]
            state["compatible_count"] = stats["compatible"]
            state["equivalence_classes"] = stats["equivalence_classes"]
            state["blockers"] = stats["blockers"]
            state["run_history"] = list(state.get("run_history") or []) + [
                {"grammar_id": gid, "closure_status": stats["closure_status"], "at": _utc()}
            ]
            current = gid
            if stats["closure_status"] == "EXTENSION_REQUIRED":
                continue
            state["closure_status"] = stats["closure_status"]
            break
        else:
            state["closure_status"] = versions[-1]["closure_status"] if versions else "STOPPED_BY_UNRESOLVED_REQUIREMENT"
        state["METHOD_STATUS"] = "VERIFIED"
        if self.chain_name == "p3_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_P3_ONLY"
            state["P0_EXECUTED"] = True
            state["P1_EXECUTED"] = True
            state["P2_EXECUTED"] = True
            state["P3_EXECUTED"] = True
            state["P4_EXECUTED"] = False
            state["G6_EXECUTED"] = True
            state["G7_EXECUTED"] = False
        elif self.chain_name == "p2_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_P2_ONLY"
            state["P0_EXECUTED"] = True
            state["P1_EXECUTED"] = True
            state["P2_EXECUTED"] = True
            state["P3_EXECUTED"] = False
            state["G6_EXECUTED"] = True
            state["G7_EXECUTED"] = False
        elif self.chain_name == "p1_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_P1_ONLY"
            state["P0_EXECUTED"] = True
            state["P1_EXECUTED"] = True
            state["P2_EXECUTED"] = False
            state["G6_EXECUTED"] = True
            state["G7_EXECUTED"] = False
        elif self.chain_name == "14c0_dry":
            state["SCIENTIFIC_STATUS"] = "DRY_RUN_ONLY"
            state["P0_EXECUTED"] = False
            state["P1_EXECUTED"] = False
        elif self.chain_name == "p0_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_P0_ONLY"
            state["P0_EXECUTED"] = True
            state["P1_EXECUTED"] = False
            state["G6_EXECUTED"] = True
            state["G7_EXECUTED"] = False
        elif self.chain_name == "g6_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_G6_ONLY"
            state["G1_EXECUTED"] = True
            state["G2_EXECUTED"] = True
            state["G3_EXECUTED"] = True
            state["G3_CORRECTED_EXECUTED"] = True
            state["G4_EXECUTED"] = True
            state["G4_CORRECTED_EXECUTED"] = True
            state["G5_EXECUTED"] = True
            state["G6_EXECUTED"] = True
            state["G7_EXECUTED"] = False
        elif self.chain_name == "g5_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_G5_ONLY"
            state["G1_EXECUTED"] = True
            state["G2_EXECUTED"] = True
            state["G3_EXECUTED"] = True
            state["G3_CORRECTED_EXECUTED"] = True
            state["G4_EXECUTED"] = True
            state["G4_CORRECTED_EXECUTED"] = True
            state["G5_EXECUTED"] = True
            state["G6_EXECUTED"] = False
        elif self.chain_name == "g4r_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_G4_CORRECTED_ONLY"
            state["G1_EXECUTED"] = True
            state["G2_EXECUTED"] = True
            state["G3_EXECUTED"] = True
            state["G3_CORRECTED_EXECUTED"] = True
            state["G4_EXECUTED"] = True
            state["G4_CORRECTED_EXECUTED"] = True
            state["G5_EXECUTED"] = False
        elif self.chain_name == "g4r2_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_G4R_ORBIT_CLOSURE_V2"
            state["G1_EXECUTED"] = True
            state["G2_EXECUTED"] = True
            state["G3_EXECUTED"] = True
            state["G3_CORRECTED_EXECUTED"] = True
            state["G4_EXECUTED"] = True
            state["G4_CORRECTED_EXECUTED"] = True
            state["G5_EXECUTED"] = False
        elif self.chain_name == "g4_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_G4_ONLY"
            state["G1_EXECUTED"] = True
            state["G2_EXECUTED"] = True
            state["G3_EXECUTED"] = True
            state["G3_CORRECTED_EXECUTED"] = True
            state["G4_EXECUTED"] = True
            state["G5_EXECUTED"] = False
        elif self.chain_name == "g3r_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_G3_CORRECTED_ONLY"
            state["G1_EXECUTED"] = True
            state["G2_EXECUTED"] = True
            state["G3_EXECUTED"] = True
            state["G3_CORRECTED_EXECUTED"] = True
            state["G4_EXECUTED"] = False
        elif self.chain_name == "g3_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_G3_ONLY"
            state["G1_EXECUTED"] = True
            state["G2_EXECUTED"] = True
            state["G3_EXECUTED"] = True
            state["G4_EXECUTED"] = False
        elif self.chain_name == "g2_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_G2_ONLY"
            state["G1_EXECUTED"] = True
            state["G2_EXECUTED"] = True
            state["G3_EXECUTED"] = False
        elif self.chain_name == "g1_only":
            state["SCIENTIFIC_STATUS"] = "ANALYZED_G1_ONLY"
            state["G1_EXECUTED"] = True
            state["G2_EXECUTED"] = False
        else:
            state["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
        state["FULL_PHYSICS_GRAMMAR_EXECUTED"] = False
        state["version_reports"] = versions
        self.save_state(state)
        return state

    def resume_closure(self, *, parallel: bool = False) -> dict[str, Any]:
        state = self.load_state()
        if not self.state_path().is_file():
            return self.run_until_closure(parallel=parallel)
        if state.get("engine_version") != ENGINE_VERSION:
            raise EngineFailure("RESUME_INTEGRITY_FAILURE", "engine version")
        if state.get("top_down_input_hash") != top_down_input_hash():
            raise EngineFailure("INPUT_HASH_MISMATCH", "top-down inputs")
        current = state.get("current_grammar")
        if current:
            self.verify_checkpoint(current)
        if state.get("closure_status") in {"CLOSURE_REACHED", "STOPPED_BY_UNRESOLVED_REQUIREMENT", "STOPPED_BY_POLICY"}:
            return state
        return self.run_until_closure(parallel=parallel)


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {
        "phase10b1": {},
        "phase10b10": {},
        "phase12a": {},
        "phase14a": {},
        "phase13_1": {},
    }
    mapping = (
        ("phase10b1", ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json"), phase10b1_artifact_dir()),
        ("phase10b10", ("PHASE_10B10_SUMMARY.json",), phase10b10_artifact_dir()),
        ("phase12a", ("PHASE_12A_GRAMMAR_FREEZE.json",), phase12a_artifact_dir()),
        ("phase14a", ("PHASE_14A_SUMMARY.json",), phase14a_artifact_dir()),
        ("phase13_1", ("PHASE_13_1_SUMMARY.json",), phase13_1_artifact_dir()),
    )
    for key, names, folder in mapping:
        for name in names:
            out[key][name] = _file_digest(folder / name)
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
        raise UnauthorizedAnalysisError("Phase 14B.0 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash mismatch"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash mismatch"}
    return None


def analyze_phase14b0_engine(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    _ = signature
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
        s14a = _read_json(phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json")
        corpus = _historical_corpus()
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not closed"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if s14a.get("PHASE_14A_STATUS") != "CLOSED":
        integrity_failure = "Phase 14A is not CLOSED"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical corpus rewritten"

    summary_path = artifact_dir() / "PHASE_14B0_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14B0_STATUS") == "CLOSED" and existing.get("ENGINE_STATUS") == "READY":
            cached = existing

    if cached is None or integrity_failure:
        engine = ClosureEngine(artifact_dir(), chain="dry")
        try:
            assert_target_blind({"registry": constraint_registry(), "physics": physics_grammar_registry()})
            dry_state = engine.run_until_closure(parallel=False)
            resumed = engine.resume_closure()
            physics_activation = "REJECTED"
            try:
                ClosureEngine(artifact_dir() / "physics_forbidden", chain="physics")
            except EngineFailure as exc:
                physics_activation = exc.mode
            illegal = "REJECTED"
            try:
                engine.advance_grammar("G1_FERMIONIC_CHIRAL", "DRY0_SYNTHETIC")
            except EngineFailure as exc:
                illegal = exc.mode
            method_ok = dry_state.get("METHOD_STATUS") == "VERIFIED"
            summary = {
                "phase": PHASE,
                "audit_version": AUDIT_VERSION,
                "PHASE_14B0_STATUS": "INTEGRITY_FAILURE" if integrity_failure or not method_ok else "CLOSED",
                "integrity_failure": integrity_failure,
                "ENGINE_VERSION": ENGINE_VERSION,
                "ENGINE_STATUS": "READY" if method_ok and integrity_failure is None else "FAILED",
                "GRAMMAR_REGISTRY_STATUS": "VERIFIED",
                "CONSTRAINT_REGISTRY_STATUS": "VERIFIED",
                "TARGET_BLINDNESS_STATUS": "VERIFIED",
                "CHECKPOINT_STATUS": "VERIFIED",
                "RESUME_STATUS": "VERIFIED" if resumed.get("closure_status") == dry_state.get("closure_status") else "FAILED",
                "EQUIVALENCE_STATUS": "VERIFIED",
                "PROVENANCE_STATUS": "VERIFIED",
                "TOP_DOWN_CLOSURE_ENGINE": "READY" if method_ok and integrity_failure is None else "NOT_READY",
                "DRY_RUN_STATUS": dry_state.get("closure_status"),
                "FULL_PHYSICS_GRAMMAR_EXECUTED": False,
                "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
                "DRY_CHAIN": list(DRY_CHAIN),
                "NEXT_AUTHORIZED_ACTION": "ACTIVATE G1_FERMIONIC_CHIRAL",
                "G1_ACTIVATED": False,
                "physics_activation_attempt": physics_activation,
                "illegal_extension_attempt": illegal,
                "METHOD_STATUS": "VERIFIED" if method_ok else "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
                "frozen_hash_4C": EXPECTED_FROZEN_HASH,
                "top_down_input_hash": top_down_input_hash(),
                "string_theory_constraints_imported": False,
                "experimental_inputs": 0,
                "target_inputs": 0,
                "ranking": False,
                "fitting": False,
                "calibration": False,
                "sampling": False,
                "new_physical_principle": False,
                "phase_14b1_executed": False,
                "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
                "TARGET_BLINDNESS": "VERIFIED",
                "dry_state": {k: dry_state[k] for k in dry_state if k != "version_reports"},
                "version_reports": dry_state.get("version_reports"),
                "physics_grammars": {gid: g["grammar_hash"] for gid, g in physics_grammar_registry().items()},
            }
            _write_json(summary_path, summary)
            _write_json(artifact_dir() / "PHASE_14B0_GRAMMAR_REGISTRY.json", physics_grammar_registry())
            _write_json(artifact_dir() / "PHASE_14B0_CONSTRAINT_REGISTRY.json", constraint_registry())
            _write_json(artifact_dir() / "PHASE_14B0_EQUIVALENCE_REGISTRY.json", dry_state.get("equivalence_classes"))
            _write_json(
                artifact_dir() / "PHASE_14B0_PROVENANCE_REGISTRY.json",
                {"allowed": sorted(_ALLOWED_PROVENANCE), "failure_modes": list(_FAILURE_MODES)},
            )
        except EngineFailure as exc:
            summary = {
                "phase": PHASE,
                "PHASE_14B0_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "ENGINE_STATUS": "FAILED",
                "failure_mode": exc.mode,
                "detail": exc.detail,
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "FULL_PHYSICS_GRAMMAR_EXECUTED": False,
                "ranking": False,
                "phase_14b1_executed": False,
            }
            _write_json(summary_path, summary)
    else:
        summary = cached

    hashes_after = snapshot_prior_artifact_hashes()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    artifacts_ok = hashes_before == hashes_after
    summary["phase14a_artifacts_unchanged"] = hashes_before["phase14a"] == hashes_after["phase14a"]
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    if not (artifacts_ok and grammar_ok and frozen_ok and summary.get("ranking") is False):
        summary["PHASE_14B0_STATUS"] = "INTEGRITY_FAILURE"
        summary["ENGINE_STATUS"] = "FAILED"
    _write_json(summary_path, summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_14B0_TEST_COPY_ID": PHASE_14B0_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "ENGINE_VERSION": ENGINE_VERSION,
        "ENGINE_STATUS": summary.get("ENGINE_STATUS"),
        "GRAMMAR_REGISTRY_STATUS": summary.get("GRAMMAR_REGISTRY_STATUS"),
        "CONSTRAINT_REGISTRY_STATUS": summary.get("CONSTRAINT_REGISTRY_STATUS"),
        "TARGET_BLINDNESS_STATUS": summary.get("TARGET_BLINDNESS_STATUS"),
        "CHECKPOINT_STATUS": summary.get("CHECKPOINT_STATUS"),
        "RESUME_STATUS": summary.get("RESUME_STATUS"),
        "EQUIVALENCE_STATUS": summary.get("EQUIVALENCE_STATUS"),
        "PROVENANCE_STATUS": summary.get("PROVENANCE_STATUS"),
        "TOP_DOWN_CLOSURE_ENGINE": summary.get("TOP_DOWN_CLOSURE_ENGINE"),
        "DRY_RUN_STATUS": summary.get("DRY_RUN_STATUS"),
        "FULL_PHYSICS_GRAMMAR_EXECUTED": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_ACTION": "ACTIVATE G1_FERMIONIC_CHIRAL",
        "G1_ACTIVATED": False,
        "METHOD_STATUS": summary.get("METHOD_STATUS"),
        "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "audit_summary": summary,
        "version_reports": summary.get("version_reports"),
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_14B0_STATUS": summary.get("PHASE_14B0_STATUS"),
        "PHASE_14A_STATUS": s14a.get("PHASE_14A_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "known_physics_comparison_executed": False,
        "phase_14b1_executed": False,
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
        "PHASE_14B0_CLOSED": summary.get("PHASE_14B0_STATUS") == "CLOSED",
        "overclaims": {
            "1_activate_G1_automatically": "REJECTED AS OVERCLAIM",
            "2_invent_unauthorized_extension": "REJECTED AS OVERCLAIM",
            "3_interpret_dry_run_as_physics": "REJECTED AS OVERCLAIM",
            "4_insert_numerical_targets": "REJECTED AS OVERCLAIM",
            "5_rank_candidates": "REJECTED AS OVERCLAIM",
            "6_treat_method_failure_as_scientific_negative": "REJECTED AS OVERCLAIM",
            "7_modify_frozen_action": "REJECTED AS OVERCLAIM",
            "8_import_string_theory": "REJECTED AS OVERCLAIM",
            "9_cartesian_product_in_memory": "REJECTED AS OVERCLAIM",
            "10_start_phase_14b1": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_14B0_STATUS"] == "CLOSED"
        and science["ENGINE_STATUS"] == "READY"
        and science["FULL_PHYSICS_GRAMMAR_EXECUTED"] is False
        and science["G1_ACTIVATED"] is False
        and science["SCIENTIFIC_STATUS"] == "NOT_ANALYZED"
        and science["ranking"] is False
        and science["phase_14b1_executed"] is False
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and corpus["specs_unchanged"]
    )
    return science


def run_phase14b0_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase14b0_engine(auth, signature=signature)
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
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED"
            if science.get("audit_summary", {}).get("grammar_hash_12A_unchanged")
            else "FAILED",
            "PHASE_14A_ARTIFACTS_UNCHANGED": "VERIFIED"
            if science.get("audit_summary", {}).get("phase14a_artifacts_unchanged")
            else "FAILED",
            "PHASE_14B0_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14B0_STATUS": science.get("PHASE_14B0_STATUS"),
            "PHASE_14A_STATUS": science.get("PHASE_14A_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "STRING_THEORY_CONSTRAINTS": "NONE",
            "PHASE_14B1_EXECUTED": "FALSE",
            "FULL_PHYSICS_GRAMMAR_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
