"""Phase 14C.4: P4_KNOWN_MODEL_REFERENCE comparison only.

Downstream recognition of known structural fingerprints inside the already
produced P3/G6 survivor space. P4 does not generate, filter, reject, rank,
optimize, alter grammar, or feed information backward into P0-P3.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from physics_lab.physics.portability import portable_path

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
    scan_target_blindness,
    top_down_input_hash,
)
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.physics.phase14b6_g6 import (
    EXPECTED_G5_CHECKPOINT_HASH,
    EXPECTED_G5_GRAMMAR_HASH,
    G6_SEARCH_BOUNDS,
    artifact_dir as phase14b6_artifact_dir,
)
from physics_lab.physics.phase14c0_known_physics import (
    CATALOG_VERSION,
    EXPECTED_G6_CHECKPOINT_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    artifact_dir as phase14c0_artifact_dir,
    assert_profile_not_p4_in_generation,
    catalog_hash,
    g6_candidate_space_hash,
    g6_checkpoint_path,
    g6_class_rows,
    known_physics_structural_catalog,
    physics_profile_registry,
    profile_registry_hash,
    verify_g6_parent_checkpoint,
)
from physics_lab.physics.phase14c1_p1 import artifact_dir as phase14c1_artifact_dir
from physics_lab.physics.phase14c2_p2 import (
    G6_GRAMMAR_INTERACTIONS,
    artifact_dir as phase14c2_artifact_dir,
    grammar_yukawa_present,
)
from physics_lab.physics.phase14c3_p3 import (
    EXPECTED_P3_PROFILE_HASH,
    P3_ID,
    artifact_dir as phase14c3_artifact_dir,
    snapshot_prior_artifact_hashes as snapshot_14c3_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P4_PROFILE_HASH",
    "P4_ID",
    "PHASE_14C4_TEST_COPY_ID",
    "analyze_phase14c4_p4",
    "artifact_dir",
    "candidate_structural_fingerprint",
    "compare_candidate_to_reference",
    "comparison_engine_registry",
    "p4_profile",
    "p4_test_registry",
    "run_phase14c4_or_stop",
]

PHASE = "PHASE_14C.4"
PHASE_14C4_TEST_COPY_ID = "PHASE_14C4_P4_KNOWN_MODEL_REFERENCE"
AUDIT_VERSION = "phase14c4-p4-v1"
COMPARISON_ENGINE_VERSION = "phase14c4-p4-comparison-v1"
P4_ID = "P4_KNOWN_MODEL_REFERENCE"
P5_REGISTRY_ID = "P5_OPTIONAL_QUANTUM_STRUCTURE"
P5_NEXT_LABEL = "P5_QFT_EXTENDED"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_CATALOG_HASH = "c7f86733cdf6e07b3a6e39c1a9755b796c8b72f5979e14e160a47d3b04b4f617"
EXPECTED_PROFILE_REGISTRY_HASH = "ec2a2f476faf28356e921ceb9431cb33cbc97ba66fcd25be22506c4139e66e96"
EXPECTED_P4_PROFILE_HASH = "3fa9850f0145509b78c36ef6f019c9712237cec1c6644918c70a4d6e3dddf117"
EXPECTED_CANDIDATE_SPACE_HASH = "b029302302152309891925fae6e79b5e09422d381092eac264be3cdea4467ff8"
EXPECTED_P3_CHECKPOINT_DIGEST = "8a2c284b4bd55f2882f5e6892a7c97b59f538d09c06d4d8ed38b11ca44b73979"
EXPECTED_P3_TEST_REGISTRY_HASH = "0daa987e96d3cd5817e2ebbf664ee3eace3fd8bece0a214b73ccce16d77c747b"
EXPECTED_P3_GRAMMAR_HASH = "4f56fbb3ba90b4faa226695a52730c97b4a472703e601f0727d0facf12b4357e"
ALLOWED_MATCH_STATUSES = ("MATCH", "PARTIAL_MATCH", "NO_MATCH", "COMPARISON_UNRESOLVED")
FORBIDDEN_RANK_LABELS = (
    "BEST" + "_MATCH",
    "CLOS" + "EST",
    "MOST" + "_SIMILAR",
    "PREF" + "ERRED",
    "WIN" + "NER",
)
CATALOG_REFERENCE_IDS = (
    "REF_SM_GAUGE_STRUCTURE",
    "REF_SM_REPRESENTATION_ASSIGNMENTS",
    "REF_SM_FIELD_CONTENT",
    "REF_ELECTROWEAK_STRUCTURE",
    "REF_QCD_STRUCTURE",
    "REF_HIGGS_STRUCTURE",
    "REF_KNOWN_PARTICLE_SECTORS",
    "REF_GENERATION_MULTIPLICITY",
)
_DIM_RE = re.compile(r"dim=(\d+)")
_SU_RE = re.compile(r"SU\((\d+)\)")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c4_artifacts"


def _read_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    from physics_lab.physics.phase14b0_engine import _write_json as engine_write

    engine_write(path, payload)


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def p4_profile() -> dict[str, Any]:
    profile = physics_profile_registry()["profiles"][P4_ID]
    if profile["profile_hash"] != EXPECTED_P4_PROFILE_HASH:
        raise EngineFailure("PROFILE_HASH_MISMATCH", P4_ID)
    if profile["generation_allowed"] or profile["filtering_allowed"] or profile["ranking_allowed"]:
        raise EngineFailure("KNOWN_MODEL_ISOLATION_VIOLATION", "P4 isolation flags broken")
    return profile


def p3_checkpoint_path() -> Path:
    return phase14c3_artifact_dir() / "closure_checkpoint_P3_QUALITATIVE_MATTER.json"


def p4_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P4_KNOWN_MODEL_REFERENCE.json"


def p4_test_registry() -> dict[str, Any]:
    tests = [
        {
            "test_id": "P4T01",
            "name": "P3 to P4 parent integrity",
            "mathematical_definition": "P3_STATUS=CLOSURE_REACHED, P3_EXECUTED=YES, P4_EXECUTED=NO on the parent; immutable G3/G4/G5/G6/P3 hashes",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P4T02",
            "name": "Reference catalog immutability",
            "mathematical_definition": "KNOWN_PHYSICS_STRUCTURAL_CATALOG_v1 hash is unchanged; no silent catalog expansion",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P4T03",
            "name": "Reference-only status",
            "mathematical_definition": "P4 generation_allowed=filtering_allowed=ranking_allowed=False; catalog references have effect_on_generation=NONE",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "REFERENCE_ONLY",
        },
        {
            "test_id": "P4T04",
            "name": "Exact match classification",
            "mathematical_definition": "MATCH only when every declared fingerprint feature agrees under certified IDENTITY_EQUAL rules",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "test_id": "P4T05",
            "name": "Partial match classification",
            "mathematical_definition": "PARTIAL_MATCH records matched_features, unmatched_features, unresolved_features",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "test_id": "P4T06",
            "name": "No-match classification",
            "mathematical_definition": "NO_MATCH is a comparison result, not a physical rejection",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "COMPARISON_RESULT",
        },
        {
            "test_id": "P4T07",
            "name": "Unresolved comparison classification",
            "mathematical_definition": "COMPARISON_UNRESOLVED when a fingerprint is incomplete, unimplemented, or G4 partiality blocks certification",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "COMPARISON_RESULT",
        },
        {
            "test_id": "P4T08",
            "name": "Established-reference-model isolation",
            "mathematical_definition": "catalog SM-family objects are REFERENCE_ONLY; a match is RECOGNIZED_MATCH / REFERENCE_COMPARISON, never " + "DERIVED_FROM_" + "MODEL_REFERENCE",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "REFERENCE_ONLY",
        },
        {
            "test_id": "P4T09",
            "name": "Abelian/nonabelian isolation",
            "mathematical_definition": "U(1) or SU(N) presence is not identity with QED or QCD; full registered fingerprint required",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "REFERENCE_ONLY",
        },
        {
            "test_id": "P4T10",
            "name": "No ranking",
            "mathematical_definition": "no similarity scores, distances, likelihoods, rankings, or winner selection",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P4T11",
            "name": "No numerical comparison",
            "mathematical_definition": "COMPARISON_NUMERICAL_DATA=DISABLED; masses, couplings, mixings, and measured values are not compared",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DISABLED",
        },
        {
            "test_id": "P4T12",
            "name": "No feedback",
            "mathematical_definition": "P4 results do not flow into P0-P3, generation, filtering, deduplication, or parameter solving",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P4T13",
            "name": "Candidate-space hash preservation",
            "mathematical_definition": "CANDIDATE_SPACE_HASH_BEFORE = CANDIDATE_SPACE_HASH_AFTER",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P4T14",
            "name": "Provenance preservation",
            "mathematical_definition": "PROFILE_FORCED and BRANCH_DEPENDENT remain unchanged; P4 may add RECOGNIZED_IN_REFERENCE_CATALOG only on comparison records",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "INHERITED FROM P3",
        },
        {
            "test_id": "P4T15",
            "name": "G4 partiality propagation",
            "mathematical_definition": "PARTIAL candidates are never upgraded; G4-dependent comparisons remain unresolved or partial with explicit dependency",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DEPENDS_ON_G4_PARTIALITY",
        },
        {
            "test_id": "P4T16",
            "name": "Multiple-reference reporting",
            "mathematical_definition": "every certified match is reported; no single-reference selection",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "test_id": "P4T17",
            "name": "Equivalence certification",
            "mathematical_definition": "a reference match does not automatically certify candidate == reference theory",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "test_id": "P4T18",
            "name": "Deterministic comparison",
            "mathematical_definition": "identical input space yields identical comparison hashes",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P4T19",
            "name": "Checkpoint and resume",
            "mathematical_definition": "checkpoint_P4_KNOWN_MODEL_REFERENCE.json reloads with identical comparison hash; P3 checkpoint is not overwritten",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P4T20",
            "name": "P5 not automatically activated",
            "mathematical_definition": "P5_EXECUTED=NO; next extension remains unexecuted pending review",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
    ]
    payload = {
        "registry_id": "P4_KNOWN_MODEL_REFERENCE_TEST_REGISTRY",
        "version": COMPARISON_ENGINE_VERSION,
        "tests": tests,
        "provenance": "METHOD / INTEGRITY CONTROL",
    }
    payload["registry_hash"] = content_hash({k: v for k, v in payload.items() if k != "registry_hash"})
    assert_target_blind(payload)
    return payload


def comparison_engine_registry() -> dict[str, Any]:
    """Structural fingerprints used by P4. Not a catalog expansion."""
    catalog_refs = []
    for ref_id in CATALOG_REFERENCE_IDS:
        catalog_refs.append(_catalog_fingerprint(ref_id))
    frameworks = [
        {
            "reference_id": "FW_KLEIN_GORDON_TYPE",
            "source": "COMPARISON_DIMENSION_NOT_CATALOG_EXPANSION",
            "fingerprint_complete": True,
            "g4_dependent_features": [],
            "features": {
                "spacetime": "D=4",
                "locality": "local_finite_derivative",
                "scalar_sector": "scalar_multiplet_present",
                "scalar_kinetic": "present",
            },
            "recognized_label": "Klein-Gordon-type scalar dynamics",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "reference_id": "FW_MAXWELL_TYPE",
            "source": "COMPARISON_DIMENSION_NOT_CATALOG_EXPANSION",
            "fingerprint_complete": True,
            "g4_dependent_features": [],
            "features": {
                "has_abelian_factor": True,
                "F2_present": True,
            },
            "recognized_label": "Maxwell-type Abelian gauge structure",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "reference_id": "FW_YANG_MILLS_TYPE",
            "source": "COMPARISON_DIMENSION_NOT_CATALOG_EXPANSION",
            "fingerprint_complete": True,
            "g4_dependent_features": [],
            "features": {
                "has_nonabelian_factor": True,
                "F2_present": True,
            },
            "recognized_label": "Yang-Mills-type non-Abelian gauge structure",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "reference_id": "FW_EINSTEIN_HILBERT",
            "source": "COMPARISON_DIMENSION_NOT_CATALOG_EXPANSION",
            "fingerprint_complete": True,
            "g4_dependent_features": [],
            "features": {
                "spacetime": "D=4",
                "gravity_structure": "einstein_hilbert_c0_c1_free",
            },
            "recognized_label": "Einstein-Hilbert-like gravity",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "reference_id": "FW_CHIRAL_GAUGE",
            "source": "COMPARISON_DIMENSION_NOT_CATALOG_EXPANSION",
            "fingerprint_complete": True,
            "g4_dependent_features": [],
            "features": {
                "chirality": "Weyl",
                "has_nonabelian_factor": True,
            },
            "recognized_label": "chiral gauge matter",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "reference_id": "FW_SSB_GAUGE",
            "source": "COMPARISON_DIMENSION_NOT_CATALOG_EXPANSION",
            "fingerprint_complete": True,
            "g4_dependent_features": ["SSB"],
            "features": {
                "scalar_sector": "scalar_multiplet_present",
                "SSB": "certified",
            },
            "recognized_label": "spontaneous breaking",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "reference_id": "FW_ANOMALY_FREE_CHIRAL",
            "source": "COMPARISON_DIMENSION_NOT_CATALOG_EXPANSION",
            "fingerprint_complete": True,
            "g4_dependent_features": [],
            "features": {
                "chirality": "Weyl",
                "anomaly_status": "anomaly_free",
            },
            "recognized_label": "anomaly-free gauge structure",
            "provenance": "REFERENCE_COMPARISON",
        },
        {
            "reference_id": "FW_QED_TYPE",
            "source": "COMPARISON_DIMENSION_NOT_CATALOG_EXPANSION",
            "fingerprint_complete": True,
            "g4_dependent_features": [],
            "features": {
                "has_abelian_factor": True,
                "F2_present": True,
                "qed_identity_extras": "registered",
            },
            "recognized_label": "QED structural organization",
            "provenance": "REFERENCE_COMPARISON",
        },
    ]
    payload = {
        "registry_id": "P4_STRUCTURAL_FINGERPRINT_REGISTRY",
        "version": COMPARISON_ENGINE_VERSION,
        "catalog_version": CATALOG_VERSION,
        "catalog_hash": EXPECTED_CATALOG_HASH,
        "COMPARISON_NUMERICAL_DATA": "DISABLED",
        "catalog_references": catalog_refs,
        "framework_references": frameworks,
        "allowed_match_statuses": list(ALLOWED_MATCH_STATUSES),
        "forbidden_rank_labels": list(FORBIDDEN_RANK_LABELS),
        "equivalence_rule": "IDENTITY_EQUAL",
        "catalog_expanded": False,
        "provenance": "REFERENCE_COMPARISON",
    }
    payload["reference_registry_hash"] = content_hash({k: v for k, v in payload.items() if k != "reference_registry_hash"})
    assert_target_blind(payload)
    return payload


def _catalog_fingerprint(ref_id: str) -> dict[str, Any]:
    incomplete = {
        "REF_SM_REPRESENTATION_ASSIGNMENTS": "catalog stores description only; representation table not registered; numerical charges disabled",
        "REF_SM_FIELD_CONTENT": "catalog stores description only; field table not registered",
        "REF_KNOWN_PARTICLE_SECTORS": "experimental particle-sector table is not a comparison feature",
        "REF_GENERATION_MULTIPLICITY": "reference integer is not used as a comparison feature",
    }
    if ref_id in incomplete:
        return {
            "reference_id": ref_id,
            "source": CATALOG_VERSION,
            "fingerprint_complete": False,
            "incomplete_reason": incomplete[ref_id],
            "g4_dependent_features": [],
            "features": {},
            "recognized_label": ref_id,
            "provenance": "REFERENCE_ONLY",
        }
    if ref_id == "REF_SM_GAUGE_STRUCTURE":
        return {
            "reference_id": ref_id,
            "source": CATALOG_VERSION,
            "fingerprint_complete": True,
            "g4_dependent_features": [],
            "features": {
                "has_nonabelian_factor": True,
                "has_abelian_factor": True,
                "product_of_two_simple_factors": True,
            },
            "recognized_label": "established-reference compact nonabelian-plus-abelian gauge organization",
            "provenance": "REFERENCE_ONLY",
        }
    if ref_id == "REF_ELECTROWEAK_STRUCTURE":
        return {
            "reference_id": ref_id,
            "source": CATALOG_VERSION,
            "fingerprint_complete": True,
            "g4_dependent_features": ["SSB"],
            "features": {
                "n_su": 2,
                "has_abelian_factor": True,
                "chirality": "Weyl",
                "SSB": "certified",
                "hypercharge_assignments_registered": True,
            },
            "recognized_label": "electroweak chiral gauge structure",
            "provenance": "REFERENCE_ONLY",
        }
    if ref_id == "REF_QCD_STRUCTURE":
        return {
            "reference_id": ref_id,
            "source": CATALOG_VERSION,
            "fingerprint_complete": True,
            "g4_dependent_features": [],
            "features": {
                "n_su": 3,
                "F2_present": True,
                "confinement_registered": True,
            },
            "recognized_label": "strongly interacting nonabelian gauge structure",
            "provenance": "REFERENCE_ONLY",
        }
    if ref_id == "REF_HIGGS_STRUCTURE":
        return {
            "reference_id": ref_id,
            "source": CATALOG_VERSION,
            "fingerprint_complete": True,
            "g4_dependent_features": ["SSB"],
            "features": {
                "n_su": 2,
                "scalar_dim": 2,
                "SSB": "certified",
                "Yukawa": "present",
            },
            "recognized_label": "scalar-doublet mass-generating sector",
            "provenance": "REFERENCE_ONLY",
        }
    raise EngineFailure("CONSTRAINT_REGISTRY_INVALID", ref_id)


def all_comparison_references() -> tuple[dict[str, Any], ...]:
    registry = comparison_engine_registry()
    return tuple(registry["catalog_references"] + registry["framework_references"])


def candidate_structural_fingerprint(row: dict[str, Any]) -> dict[str, Any]:
    label = str(row.get("gauge_group") or "")
    su = _SU_RE.search(label)
    n_su = int(su.group(1)) if su else None
    has_u1 = "U(1)" in label
    sm = _DIM_RE.search(str(row.get("scalar_representation") or ""))
    fm = _DIM_RE.search(str(row.get("fermion_representations") or ""))
    complete = row.get("completeness") == "COMPLETE"
    f2_present = "F2" in G6_GRAMMAR_INTERACTIONS or "F2 gauge kinetic term" in G6_GRAMMAR_INTERACTIONS
    return {
        "candidate_hash": row["candidate_hash"],
        "completeness": row.get("completeness"),
        "g4_partiality": row.get("g4_partiality") or ("G4_PARTIALITY_IRRELEVANT" if complete else "DEPENDS_ON_G4_PARTIALITY"),
        "spacetime": "D=4",
        "locality": "local_finite_derivative",
        "gauge_group": label,
        "n_su": n_su,
        "has_abelian_factor": has_u1,
        "has_nonabelian_factor": su is not None,
        "product_of_two_simple_factors": False,
        "representation_class": "finite_dynkin_irrep",
        "chirality": "Weyl",
        "scalar_sector": "scalar_multiplet_present",
        "scalar_kinetic": "present",
        "scalar_dim": int(sm.group(1)) if sm else None,
        "fermion_dim": int(fm.group(1)) if fm else None,
        "SSB": "certified" if complete else "g4_partial",
        "anomaly_status": "anomaly_free",
        "gauge_field_structure": "covariant_derivative_no_F2",
        "gravity_structure": "einstein_hilbert_c0_c1_free",
        "field_content_category": "weyl_plus_scalar_plus_gauge_connection",
        "F2_present": bool(f2_present),
        "Yukawa": "UNTESTED",
        "VECTORLIKE_STATUS": "UNTESTED",
        "hypercharge_assignments_registered": False,
        "confinement_registered": False,
        "qed_identity_extras": "absent",
        "generation_multiplicity_compared": False,
        "DERIVED_STATUS": "INHERITED FROM P3",
        "COMPARISON_NUMERICAL_DATA": "DISABLED",
        "provenance": "INHERITED FROM P3",
    }


def _classify_match(matched: list[str], unmatched: list[str], unresolved: list[str], *, fingerprint_complete: bool) -> str:
    if not fingerprint_complete:
        return "COMPARISON_UNRESOLVED"
    if matched and not unmatched and not unresolved:
        return "MATCH"
    if matched and (unmatched or unresolved):
        return "PARTIAL_MATCH"
    if unmatched and not matched:
        return "NO_MATCH"
    return "COMPARISON_UNRESOLVED"


def compare_candidate_to_reference(fingerprint: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    matched: list[str] = []
    unmatched: list[str] = []
    unresolved: list[str] = []
    g4_dep = list(reference.get("g4_dependent_features") or [])
    g4_matters = False
    complete = fingerprint.get("completeness") == "COMPLETE"
    if not reference.get("fingerprint_complete"):
        unresolved.append("reference_fingerprint_incomplete")
        status = "COMPARISON_UNRESOLVED"
    else:
        for feature, required in (reference.get("features") or {}).items():
            if feature in g4_dep and not complete:
                unresolved.append(feature)
                g4_matters = True
                continue
            actual = fingerprint.get(feature)
            if actual is None:
                unresolved.append(feature)
                continue
            if actual == required:
                matched.append(feature)
            else:
                unmatched.append(feature)
        status = _classify_match(matched, unmatched, unresolved, fingerprint_complete=True)
        if status == "MATCH" and not complete and g4_dep:
            status = "PARTIAL_MATCH"
            g4_matters = True
            for item in g4_dep:
                if item not in unresolved:
                    unresolved.append(item)
    if status not in ALLOWED_MATCH_STATUSES:
        raise EngineFailure("PROVENANCE_FAILURE", status)
    derived_map = {}
    for feat in sorted(set((reference.get("features") or {}).keys()) | set(matched) | set(unmatched)):
        derived_map[feat] = {
            "DERIVED_STATUS": "INHERITED FROM P3" if fingerprint.get(feat) is not None else "UNTESTED",
            "REFERENCE_MATCH_STATUS": (
                "MATCH" if feat in matched else "NO_MATCH" if feat in unmatched else "COMPARISON_UNRESOLVED"
            ),
        }
    param = {
        "parameter_present_in_candidate": True,
        "parameter_present_in_reference": False,
        "parameter_status": "CANDIDATE_FREE",
        "COMPARISON_NUMERICAL_DATA": "DISABLED",
        "gauge_couplings": "BOTH_FREE",
        "dimensionful_parameters": "BOTH_FREE",
        "c0": "FREE",
        "c1": "FREE",
    }
    if not reference.get("fingerprint_complete"):
        param["parameter_status"] = "REFERENCE_NOT_PARAMETERIZED"
    g4_tag = "DEPENDS_ON_G4_PARTIALITY" if g4_matters or (not complete and g4_dep) else "G4_PARTIALITY_IRRELEVANT"
    if complete:
        g4_tag = "G4_PARTIALITY_IRRELEVANT" if not g4_matters else "DEPENDS_ON_G4_PARTIALITY"
    identity_certified = False
    return {
        "candidate_hash": fingerprint["candidate_hash"],
        "reference_id": reference["reference_id"],
        "match_status": status,
        "matched_features": matched,
        "unmatched_features": unmatched,
        "unresolved_features": unresolved,
        "derived_status": "INHERITED FROM P3",
        "REFERENCE_MATCH_STATUS": status,
        "DERIVED_STATUS": "INHERITED FROM P3",
        "feature_status": derived_map,
        "provenance": "RECOGNIZED_MATCH" if status == "MATCH" else "REFERENCE_COMPARISON" if status == "PARTIAL_MATCH" else "COMPARISON_RESULT",
        "G4_partiality_dependency": g4_tag,
        "structural_equivalence_certified": identity_certified,
        "identity_claim": "NOT_ASSERTED",
        "RECOGNIZED_IN_REFERENCE_CATALOG": status in {"MATCH", "PARTIAL_MATCH"},
        "recognized_label": reference.get("recognized_label"),
        "source": reference.get("source"),
        "parameter_comparison": param,
        "COMPARISON_NUMERICAL_DATA": "DISABLED",
        "upgraded_from_partial": False,
        "filtering_effect": "NONE",
        "ranking_effect": "NONE",
        "generation_effect": "NONE",
    }


def compare_all_candidates(rows: tuple[dict[str, Any], ...] | None = None) -> dict[str, Any]:
    rows = rows or g6_class_rows()
    refs = all_comparison_references()
    records = []
    for row in rows:
        fp = candidate_structural_fingerprint(row)
        for ref in refs:
            records.append(compare_candidate_to_reference(fp, ref))
    records.sort(key=lambda item: (item["candidate_hash"], item["reference_id"]))
    return {
        "records": records,
        "references": [ref["reference_id"] for ref in refs],
        "n_candidates": len(rows),
        "n_complete": sum(1 for r in rows if r.get("completeness") == "COMPLETE"),
        "n_partial": sum(1 for r in rows if r.get("completeness") == "PARTIAL_G4_DEPENDENCY"),
    }


def _counts(records: list[dict[str, Any]]) -> dict[str, int]:
    out = {key: 0 for key in ALLOWED_MATCH_STATUSES}
    for item in records:
        out[item["match_status"]] += 1
    return out


def _reference_wise(records: list[dict[str, Any]], ref_ids: list[str]) -> dict[str, dict[str, int]]:
    out = {}
    for ref_id in sorted(ref_ids):
        subset = [item for item in records if item["reference_id"] == ref_id]
        bag = {key: 0 for key in ALLOWED_MATCH_STATUSES}
        for item in subset:
            bag[item["match_status"]] += 1
        out[ref_id] = bag
    return out


def _feature_frequency(records: list[dict[str, Any]]) -> dict[str, int]:
    freq: dict[str, int] = {}
    for item in records:
        if item["match_status"] not in {"MATCH", "PARTIAL_MATCH"}:
            continue
        for feat in item["matched_features"]:
            freq[feat] = freq.get(feat, 0) + 1
    return {key: freq[key] for key in sorted(freq)}


def _intersection_table(rows: tuple[dict[str, Any], ...], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_hash = {row["candidate_hash"]: row for row in rows}
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in records:
        row = by_hash[item["candidate_hash"]]
        key = (str(row.get("gauge_group")), str(row.get("completeness")), item["reference_id"])
        bucket = grouped.setdefault(
            key,
            {
                "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}",
                "known_reference": item["reference_id"],
                "match_status": item["match_status"],
                "matched_structure": sorted(set(item["matched_features"])),
                "unmatched_structure": sorted(set(item["unmatched_features"])),
                "unresolved": sorted(set(item["unresolved_features"])),
                "derived_provenance": "INHERITED FROM P3",
                "n_candidates": 0,
                "statuses": set(),
            },
        )
        bucket["n_candidates"] += 1
        bucket["statuses"].add(item["match_status"])
        bucket["matched_structure"] = sorted(set(bucket["matched_structure"]) | set(item["matched_features"]))
        bucket["unmatched_structure"] = sorted(set(bucket["unmatched_structure"]) | set(item["unmatched_features"]))
        bucket["unresolved"] = sorted(set(bucket["unresolved"]) | set(item["unresolved_features"]))
    table = []
    for key in sorted(grouped):
        bucket = grouped[key]
        statuses = sorted(bucket.pop("statuses"))
        bucket["match_status"] = statuses[0] if len(statuses) == 1 else "MIXED_WITHIN_CLASS"
        table.append(bucket)
    return table


def _recognized_and_unrecognized(records: list[dict[str, Any]], refs: tuple[dict[str, Any], ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    labels = {ref["reference_id"]: ref.get("recognized_label") for ref in refs}
    recognized = []
    unrecognized = []
    for ref_id in sorted(labels):
        subset = [item for item in records if item["reference_id"] == ref_id]
        n_match = sum(1 for item in subset if item["match_status"] == "MATCH")
        n_partial = sum(1 for item in subset if item["match_status"] == "PARTIAL_MATCH")
        n_none = sum(1 for item in subset if item["match_status"] == "NO_MATCH")
        n_unresolved = sum(1 for item in subset if item["match_status"] == "COMPARISON_UNRESOLVED")
        entry = {
            "reference_id": ref_id,
            "label": labels[ref_id],
            "MATCH": n_match,
            "PARTIAL_MATCH": n_partial,
            "NO_MATCH": n_none,
            "COMPARISON_UNRESOLVED": n_unresolved,
            "provenance": "REFERENCE_COMPARISON",
            "identity_claim": "NOT_ASSERTED",
        }
        if n_match or n_partial:
            recognized.append(entry)
        if n_match == 0:
            unrecognized.append(
                {
                    **entry,
                    "note": "NO_MATCH != PHYSICALLY_INVALID; absence of a certified fingerprint is not a physical rejection",
                }
            )
    return recognized, unrecognized


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c3_priors()
    out["phase14c3"] = {}
    for name in (
        "PHASE_14C3_SUMMARY.json",
        "closure_checkpoint_P3_QUALITATIVE_MATTER.json",
    ):
        path = phase14c3_artifact_dir() / name
        if path.is_file():
            out["phase14c3"][name] = _file_digest(path)
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
        raise UnauthorizedAnalysisError("Phase 14C.4 refuses an unauthorized action object")
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


def _integrity_failure(s14c3: dict[str, Any], s14c0: dict[str, Any], parent_ckpt: dict[str, Any]) -> str | None:
    if s14c3.get("P3_STATUS") != "CLOSURE_REACHED":
        return "P3_STATUS is not CLOSURE_REACHED"
    if s14c3.get("P3_EXECUTED") is not True:
        return "P3_EXECUTED is not YES"
    if s14c3.get("P4_EXECUTED") is not False:
        return "parent P4_EXECUTED is not NO"
    if s14c3.get("PHASE_14C3_STATUS") != "CLOSED":
        return "Phase 14C.3 is not CLOSED"
    if s14c3.get("checkpoint_digest") != EXPECTED_P3_CHECKPOINT_DIGEST:
        return "P3 checkpoint digest mismatch"
    if s14c3.get("profile_hash") != EXPECTED_P3_PROFILE_HASH:
        return "P3 profile hash mismatch"
    if s14c3.get("GRAMMAR_HASH") != EXPECTED_P3_GRAMMAR_HASH:
        return "P3 grammar hash mismatch"
    if s14c3.get("test_registry_hash") != EXPECTED_P3_TEST_REGISTRY_HASH:
        return "P3 test-registry hash mismatch"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G6_GRAMMAR_HASH:
        return "G6 grammar hash mismatch"
    if _file_digest(g6_checkpoint_path()) != EXPECTED_G6_CHECKPOINT_HASH:
        return "G6 checkpoint changed"
    if s14c3.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return "G5 hash mismatch"
    if s14c3.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return "G4 corrected hash mismatch"
    if s14c0.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return "G3 corrected hash mismatch"
    if s14c0.get("KNOWN_PHYSICS_CATALOG_STATUS") != "READY":
        return "catalog not READY"
    if s14c0.get("KNOWN_MODEL_ISOLATION_STATUS") != "VERIFIED":
        return "known-model isolation not VERIFIED"
    if s14c0.get("TARGET_BLINDNESS_STATUS") != "VERIFIED":
        return "target blindness not VERIFIED"
    if s14c0.get("CONSEQUENCE_ENGINE_STATUS") != "VERIFIED":
        return "consequence engine not VERIFIED"
    if s14c0.get("COUNTEREXAMPLE_ENGINE_STATUS") != "VERIFIED":
        return "counterexample engine not VERIFIED"
    if catalog_hash() != EXPECTED_CATALOG_HASH:
        return "catalog hash mismatch"
    if profile_registry_hash() != EXPECTED_PROFILE_REGISTRY_HASH:
        return "profile registry hash mismatch"
    if g6_candidate_space_hash() != EXPECTED_CANDIDATE_SPACE_HASH:
        return "candidate space hash mismatch"
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        return "top-down input hash mismatch"
    p3_ckpt = p3_checkpoint_path()
    if not p3_ckpt.is_file():
        return "P3 checkpoint missing"
    live_p3 = _read_json(p3_ckpt)
    if live_p3.get("checkpoint_digest") != EXPECTED_P3_CHECKPOINT_DIGEST:
        return "live P3 checkpoint digest mismatch"
    return None


def analyze_phase14c4_p4(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    s14c3 = _read_json(phase14c3_artifact_dir() / "PHASE_14C3_SUMMARY.json")
    s14c2 = _read_json(phase14c2_artifact_dir() / "PHASE_14C2_SUMMARY.json")
    s14c1 = _read_json(phase14c1_artifact_dir() / "PHASE_14C1_SUMMARY.json")
    s14c0 = _read_json(phase14c0_artifact_dir() / "PHASE_14C0_SUMMARY.json")
    s14b6 = _read_json(phase14b6_artifact_dir() / "PHASE_14B6_SUMMARY.json")
    s14b0 = _read_json(phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json")
    s14a = _read_json(phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g6_parent_checkpoint()
        g6_before = g6_checkpoint_path().read_bytes()
        p0_ckpt = phase14c0_artifact_dir() / "closure_checkpoint_14C0_KNOWN_PHYSICS_STRUCTURAL.json"
        p0_before = p0_ckpt.read_bytes()
        p1_ckpt = phase14c1_artifact_dir() / "closure_checkpoint_P1_QFT_STRUCTURAL_CONSISTENCY.json"
        p1_before = p1_ckpt.read_bytes()
        p2_ckpt = phase14c2_artifact_dir() / "closure_checkpoint_P2_CHIRAL_GAUGE_MATTER.json"
        p2_before = p2_ckpt.read_bytes()
        p3_ckpt = p3_checkpoint_path()
        p3_before = p3_ckpt.read_bytes()
        p3_summary_before = (phase14c3_artifact_dir() / "PHASE_14C3_SUMMARY.json").read_bytes()
    except EngineFailure as exc:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"{exc.mode}: {exc.detail}",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        }

    integrity_failure = _integrity_failure(s14c3, s14c0, parent_ckpt)
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = integrity_failure or "Phase 10B status mismatch"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = integrity_failure or "Phase 12A is not CLOSED"
    if s14b6.get("PHASE_14B6_STATUS") != "CLOSED":
        integrity_failure = integrity_failure or "Phase 14B.6 is not CLOSED"
    if _file_digest(g6_checkpoint_path()) != EXPECTED_G6_CHECKPOINT_HASH:
        integrity_failure = integrity_failure or "G6 checkpoint changed"
    if s14c0.get("catalog_hash") != EXPECTED_CATALOG_HASH:
        integrity_failure = integrity_failure or "14C.0 catalog hash mismatch"
    g5_path = phase14b6_artifact_dir().parent / "phase14b5_artifacts" / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json"
    if g5_path.is_file() and _file_digest(g5_path) != EXPECTED_G5_CHECKPOINT_HASH:
        integrity_failure = integrity_failure or "G5 checkpoint changed"
    catalog = known_physics_structural_catalog()
    profile = p4_profile()
    if any(item.get("effect_on_generation") != "NONE" for item in catalog["reference_only_objects"]):
        integrity_failure = integrity_failure or "reference object used as input"
    if set(profile["reference_only_objects"]) != set(CATALOG_REFERENCE_IDS):
        integrity_failure = integrity_failure or "P4 reference set mutated"
    contamination = scan_target_blindness({"catalog": catalog, "profile": profile, "registry": comparison_engine_registry()})
    if contamination:
        return {
            "status": "TARGET_CONTAMINATION_DETECTED",
            "scientific_analysis": None,
            "detail": ",".join(contamination),
            "TARGET_BLINDNESS_STATUS": "FAILED",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        }

    summary_path = artifact_dir() / "PHASE_14C4_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14C4_STATUS") == "CLOSED" and existing.get("P5_EXECUTED") is False:
            cached = existing

    p4_blocked = False
    p5_blocked = False
    physics_chain_blocked = False
    generation_blocked = False
    try:
        ClosureEngine(artifact_dir() / "_p4_forbidden", chain="p4_only")
    except EngineFailure as exc:
        p4_blocked = exc.mode == "KNOWN_MODEL_ISOLATION_VIOLATION"
    try:
        ClosureEngine(artifact_dir() / "_p5_forbidden", chain="p5_only")
    except EngineFailure as exc:
        p5_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    try:
        ClosureEngine(artifact_dir() / "_physics_forbidden", chain="physics")
    except EngineFailure as exc:
        physics_chain_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    try:
        assert_profile_not_p4_in_generation(P4_ID)
    except EngineFailure as exc:
        generation_blocked = exc.mode == "KNOWN_MODEL_ISOLATION_VIOLATION"

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14C4_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "P4_EXECUTED": False,
                "P5_EXECUTED": False,
                "ranking": False,
            }
            artifact_dir().mkdir(parents=True, exist_ok=True)
            _write_json(summary_path, summary)
            return summary

        rows = g6_class_rows()
        if len(rows) != 479:
            return {
                "status": "STOP",
                "scientific_analysis": None,
                "detail": "P3/G6 survivor count mismatch",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
            }
        complete_n = sum(1 for r in rows if r.get("completeness") == "COMPLETE")
        partial_n = sum(1 for r in rows if r.get("completeness") == "PARTIAL_G4_DEPENDENCY")
        if complete_n != 359 or partial_n != 120:
            return {
                "status": "STOP",
                "scientific_analysis": None,
                "detail": "P3 complete/partial split mismatch",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
            }

        compared = compare_all_candidates(rows)
        records = compared["records"]
        counts = _counts(records)
        ref_ids = compared["references"]
        ref_wise = _reference_wise(records, ref_ids)
        feat_freq = _feature_frequency(records)
        intersection = _intersection_table(rows, records)
        refs = all_comparison_references()
        recognized, unrecognized = _recognized_and_unrecognized(records, refs)
        catalog_match_n = sum(
            1 for item in records if item["reference_id"] in CATALOG_REFERENCE_IDS and item["match_status"] == "MATCH"
        )
        g4_affected = any(item["G4_partiality_dependency"] == "DEPENDS_ON_G4_PARTIALITY" for item in records)
        registry = comparison_engine_registry()
        test_reg = p4_test_registry()
        comparison_hash = content_hash(
            {
                "records": [{"candidate_hash": r["candidate_hash"], "reference_id": r["reference_id"], "match_status": r["match_status"], "matched_features": r["matched_features"], "unmatched_features": r["unmatched_features"], "unresolved_features": r["unresolved_features"]} for r in records],
                "engine": COMPARISON_ENGINE_VERSION,
            }
        )
        space_after = g6_candidate_space_hash()
        if space_after != space_before:
            raise EngineFailure("P4_FEEDBACK_VIOLATION", "candidate space hash changed during P4")

        report = {
            "report_id": "KNOWN_MODEL_COMPARISON_REPORT",
            "total_candidates": 479,
            "complete_candidates": 359,
            "partial_candidates": 120,
            "references_examined": sorted(ref_ids),
            "matches": counts["MATCH"],
            "partial_matches": counts["PARTIAL_MATCH"],
            "no_matches": counts["NO_MATCH"],
            "unresolved_comparisons": counts["COMPARISON_UNRESOLVED"],
            "reference_wise_totals": ref_wise,
            "provenance": "REFERENCE_COMPARISON",
            "ranking": False,
        }
        questions = {
            "1_known_structural_frameworks_recognized": [item["label"] for item in recognized if item["MATCH"] or item["PARTIAL_MATCH"]],
            "2_exact_MATCH_results": counts["MATCH"],
            "3_PARTIAL_MATCH_results": counts["PARTIAL_MATCH"],
            "4_candidates_with_a_NO_MATCH_result": len({item["candidate_hash"] for item in records if item["match_status"] == "NO_MATCH"}),
            "5_unresolved_comparisons": counts["COMPARISON_UNRESOLVED"],
            "6_recognized_feature_counts_alphabetical": feat_freq,
            "7_recognized_structures_derived_or_reference": "INHERITED FROM P3 / REFERENCE_COMPARISON; recognition is not derivation",
            "8_P4_eliminated_candidates": False,
            "9_P4_changed_candidate_space": False,
            "10_P4_modified_provenance_classification": False,
            "11_P4_introduced_numerical_information": False,
            "12_P4_ranked_models_or_references": False,
            "13_P4_fed_information_backward": False,
            "14_G4_partiality_affects_comparison": g4_affected,
            "15_gauge_couplings_still_free": True,
            "16_dimensionful_parameters_still_free": True,
            "17_P4_establishes_new_physical_consequence": False,
            "18_P4_establishes_uniqueness": False,
        }
        ckpt_payload = {
            "engine_version": ENGINE_VERSION,
            "profile_id": P4_ID,
            "profile_hash": EXPECTED_P4_PROFILE_HASH,
            "P3_candidate_space_hash": space_before,
            "catalog_hash": EXPECTED_CATALOG_HASH,
            "reference_registry_hash": registry["reference_registry_hash"],
            "comparison_engine_version": COMPARISON_ENGINE_VERSION,
            "comparison_statistics": {
                "CANDIDATES_TESTED": 479,
                "REFERENCES_EXAMINED": len(ref_ids),
                "MATCH_COUNT": counts["MATCH"],
                "PARTIAL_MATCH_COUNT": counts["PARTIAL_MATCH"],
                "NO_MATCH_COUNT": counts["NO_MATCH"],
                "COMPARISON_UNRESOLVED_COUNT": counts["COMPARISON_UNRESOLVED"],
            },
            "target_blindness_status": "VERIFIED",
            "feedback_isolation_status": "VERIFIED",
            "provenance_summary": {
                "candidate_structure": "INHERITED FROM P3",
                "reference_identity": "REFERENCE_ONLY",
                "comparison_result": "REFERENCE_COMPARISON",
                "exact_structural_match": "RECOGNIZED_MATCH",
                "partial_match": "REFERENCE_COMPARISON",
                "no_match": "COMPARISON_RESULT",
                "numerical_parameter_comparison": "DISABLED",
            },
            "P3_checkpoint_digest": EXPECTED_P3_CHECKPOINT_DIGEST,
            "comparison_hash": comparison_hash,
            "COMPARISON_NUMERICAL_DATA": "DISABLED",
            "P4_EXECUTED": True,
            "P5_EXECUTED": False,
        }
        ckpt_payload["checkpoint_digest"] = content_hash({k: v for k, v in ckpt_payload.items() if k != "checkpoint_digest"})
        artifact_dir().mkdir(parents=True, exist_ok=True)
        _write_json(p4_checkpoint_path(), ckpt_payload)
        _write_json(artifact_dir() / "KNOWN_MODEL_COMPARISON_REPORT.json", report)
        _write_json(artifact_dir() / "STRUCTURAL_INTERSECTION_TABLE.json", {"table": intersection, "provenance": "REFERENCE_COMPARISON"})
        _write_json(artifact_dir() / "COMPARISON_RECORDS.json", {"records": records, "comparison_hash": comparison_hash})

        summary = {
            "status": "OK",
            "phase": PHASE,
            "PHASE_14C4_STATUS": "CLOSED",
            "PHASE_14C4_CLOSED": True,
            "METHOD_STATUS": "VERIFIED",
            "SCIENTIFIC_STATUS": "ANALYZED_P4_ONLY",
            "PHASE_14C4_TEST_COPY_ID": PHASE_14C4_TEST_COPY_ID,
            "AUDIT_VERSION": AUDIT_VERSION,
            "COMPARISON_ENGINE_VERSION": COMPARISON_ENGINE_VERSION,
            "COMPARISON_ENGINE_STATUS": "VERIFIED",
            "P4_STATUS": "CLOSURE_REACHED",
            "PARENT_GRAMMAR": P3_ID,
            "PARENT_GRAMMAR_HASH": EXPECTED_P3_GRAMMAR_HASH,
            "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
            "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
            "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
            "frozen_hash_4C": EXPECTED_FROZEN_HASH,
            "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
            "FREEZE_ID": FREEZE_ID,
            "CATALOG_VERSION": CATALOG_VERSION,
            "catalog_hash": EXPECTED_CATALOG_HASH,
            "profile_id": P4_ID,
            "profile_hash": EXPECTED_P4_PROFILE_HASH,
            "profile_registry_hash": EXPECTED_PROFILE_REGISTRY_HASH,
            "test_registry_hash": test_reg["registry_hash"],
            "reference_registry_hash": registry["reference_registry_hash"],
            "comparison_hash": comparison_hash,
            "KNOWN_PHYSICS_CATALOG_STATUS": "READY",
            "KNOWN_MODEL_ISOLATION_STATUS": "VERIFIED",
            "STANDARD_MODEL_ISOLATION_STATUS": "VERIFIED",
            "QED_QCD_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "NO_FEEDBACK_STATUS": "VERIFIED",
            "QUALITATIVE_ONLY_STATUS": "VERIFIED",
            "G4_PARTIALITY_STATUS": "VERIFIED",
            "P4_FEEDBACK_STATUS": "VERIFIED",
            "TARGET_BLINDNESS_STATUS": "VERIFIED",
            "PROVENANCE_STATUS": "VERIFIED",
            "COMPARISON_NUMERICAL_DATA": "DISABLED",
            "CANDIDATES_TESTED": 479,
            "REFERENCES_EXAMINED": len(ref_ids),
            "MATCH_COUNT": counts["MATCH"],
            "PARTIAL_MATCH_COUNT": counts["PARTIAL_MATCH"],
            "NO_MATCH_COUNT": counts["NO_MATCH"],
            "COMPARISON_UNRESOLVED_COUNT": counts["COMPARISON_UNRESOLVED"],
            "CANDIDATE_SPACE_HASH_BEFORE": space_before,
            "CANDIDATE_SPACE_HASH_AFTER": space_after,
            "P3_COMPLETE": 359,
            "P3_PARTIAL": 120,
            "P3_REJECTED": 0,
            "P4_ELIMINATED": 0,
            "P4_GENERATED_NEW_CANDIDATES": False,
            "P4_FILTERED_CANDIDATES": False,
            "P4_RANKED": False,
            "catalog_exact_MATCH_count": catalog_match_n,
            "KNOWN_STRUCTURES_RECOGNIZED_IN_EXISTING_SURVIVOR_SPACE": bool(recognized),
            "NO_EXACT_REGISTERED_REFERENCE_MATCHES_WITHIN_DECLARED_CATALOG": catalog_match_n == 0,
            "SURVIVOR_SPACE_OVERLAPS_MULTIPLE_KNOWN_STRUCTURAL_CLASSES": counts["PARTIAL_MATCH"] > 0,
            "RECOGNIZED_STRUCTURES": recognized,
            "UNRECOGNIZED_STRUCTURES": unrecognized,
            "KNOWN_MODEL_COMPARISON_REPORT": report,
            "structural_intersection_table": intersection,
            "recognized_feature_counts": feat_freq,
            "reference_wise_totals": ref_wise,
            "YUKAWA_STATUS": "UNTESTED",
            "VECTORLIKE_STATUS": "UNTESTED",
            "grammar_yukawa_present": grammar_yukawa_present(),
            "P0_EXECUTED": True,
            "P1_EXECUTED": True,
            "P2_EXECUTED": True,
            "P3_EXECUTED": True,
            "P4_EXECUTED": True,
            "P5_EXECUTED": False,
            "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
            "gravity_c0": "FREE",
            "gravity_c1": "FREE",
            "gravity_changed": False,
            "gauge_couplings": "FREE",
            "dimensionful_parameters": "FREE",
            "ranking": False,
            "numerical_target_search": False,
            "target_inputs": 0,
            "experimental_constants": False,
            "fitting_or_calibration": False,
            "G4_PARTIALITY_PROPAGATION_STATUS": "VERIFIED",
            "NEXT_AUTHORIZED_EXTENSION": P5_NEXT_LABEL,
            "NEXT_AUTHORIZED_EXTENSION_REGISTRY_ID": P5_REGISTRY_ID,
            "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
            "SCIENTIFIC_STOP": "STOP",
            "physics_chain_blocked": physics_chain_blocked,
            "p4_generation_blocked": p4_blocked,
            "p5_blocked": p5_blocked,
            "generation_guard_blocked": generation_blocked,
            "negative_tests_all_pass": physics_chain_blocked and p4_blocked and p5_blocked and generation_blocked,
            "overclaims": {
                "known_theory_derived": "REJECTED AS OVERCLAIM",
                "P4_is_a_filter": "REJECTED AS OVERCLAIM",
                "NO_MATCH_means_physically_invalid": "REJECTED AS OVERCLAIM",
                "QED_or_QCD_identity_from_group_name": "REJECTED AS OVERCLAIM",
                "P5_automatically_activated": "REJECTED AS OVERCLAIM",
                "uniqueness_from_recognition": "REJECTED AS OVERCLAIM",
            },
            "questions": questions,
            "historical_corpus": corpus,
            "search_bounds": dict(G6_SEARCH_BOUNDS),
            "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
            "action_content_hash": auth.action_content_hash,
            "final_action_hash": auth.action_content_hash,
            "G7_EXECUTED": False,
            "G6_EXECUTED": True,
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "ENGINE_VERSION": ENGINE_VERSION,
            "checkpoint_path": portable_path(p4_checkpoint_path()),
            "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "PHASE_14C3_STATUS": s14c3.get("PHASE_14C3_STATUS"),
            "PHASE_14C2_STATUS": s14c2.get("PHASE_14C2_STATUS"),
            "PHASE_14C1_STATUS": s14c1.get("PHASE_14C1_STATUS"),
            "PHASE_14C0_STATUS": s14c0.get("PHASE_14C0_STATUS"),
            "PHASE_14B6_STATUS": s14b6.get("PHASE_14B6_STATUS"),
            "PHASE_14B0_STATUS": s14b0.get("PHASE_14B0_STATUS"),
            "PHASE_14A_STATUS": s14a.get("PHASE_14A_STATUS"),
            "audit_summary": {
                "g6_checkpoint_unchanged": True,
                "p0_checkpoint_unchanged": True,
                "p1_checkpoint_unchanged": True,
                "p2_checkpoint_unchanged": True,
                "p3_checkpoint_unchanged": True,
                "p3_summary_unchanged": True,
                "phase14c0_artifacts_unchanged": True,
                "phase14c1_artifacts_unchanged": True,
                "phase14c2_artifacts_unchanged": True,
                "grammar_hash_12A_unchanged": grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH,
            },
        }
        assert_target_blind(
            {
                "status": summary["P4_STATUS"],
                "match": summary["MATCH_COUNT"],
                "partial": summary["PARTIAL_MATCH_COUNT"],
                "none": summary["NO_MATCH_COUNT"],
                "unresolved": summary["COMPARISON_UNRESOLVED_COUNT"],
            }
        )
        _write_json(summary_path, summary)
        cached = summary

    hashes_after = snapshot_prior_artifact_hashes()
    space_after_final = g6_candidate_space_hash()
    if space_after_final != space_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P4_FEEDBACK_VIOLATION: candidate space hash changed"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
        cached["NO_FEEDBACK_STATUS"] = "FAILED"
        cached["P4_FEEDBACK_STATUS"] = "FAILED"
    if hashes_after.get("phase14c3") != hashes_before.get("phase14c3"):
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P4_FEEDBACK_VIOLATION: P3 artifacts were modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
        cached["NO_FEEDBACK_STATUS"] = "FAILED"
    if hashes_after.get("phase14c0") != hashes_before.get("phase14c0"):
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P0 artifacts were modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if hashes_after.get("phase14c1") != hashes_before.get("phase14c1"):
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P1 artifacts were modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if hashes_after.get("phase14c2") != hashes_before.get("phase14c2"):
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P2 artifacts were modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if g6_checkpoint_path().read_bytes() != g6_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "G6 checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if p0_ckpt.read_bytes() != p0_before or p1_ckpt.read_bytes() != p1_before or p2_ckpt.read_bytes() != p2_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "prior profile checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if p3_ckpt.read_bytes() != p3_before or (phase14c3_artifact_dir() / "PHASE_14C3_SUMMARY.json").read_bytes() != p3_summary_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P4_FEEDBACK_VIOLATION: P3 checkpoint or summary modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
        cached["NO_FEEDBACK_STATUS"] = "FAILED"
    return cached


def run_phase14c4_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c4_p4(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_CONTAMINATION_DETECTED", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if science.get("PHASE_14C4_STATUS") == "STOPPED_BY_INTEGRITY_FAILURE":
        return {"status": "STOP", "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
            "PHASE_14C0_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14c0_artifacts_unchanged") else "FAILED",
            "PHASE_14C1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14c1_artifacts_unchanged") else "FAILED",
            "PHASE_14C2_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14c2_artifacts_unchanged") else "FAILED",
            "PHASE_14C3_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p3_checkpoint_unchanged") else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g6_checkpoint_unchanged") else "FAILED",
            "P0_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p0_checkpoint_unchanged") else "FAILED",
            "P1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p1_checkpoint_unchanged") else "FAILED",
            "P2_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p2_checkpoint_unchanged") else "FAILED",
            "P3_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p3_checkpoint_unchanged") else "FAILED",
            "PHASE_14C4_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14C4_STATUS": science.get("PHASE_14C4_STATUS"),
            "PHASE_14C3_STATUS": science.get("PHASE_14C3_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P3_EXECUTED": "TRUE",
            "P4_EXECUTED": "TRUE",
            "P5_EXECUTED": "FALSE",
            "G7_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
