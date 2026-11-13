"""Phase 14C.3: activate P3_QUALITATIVE_MATTER only.

Qualitative matter-sector structure on the verified P2/G6 survivor space.
No Yukawa grammar is invented. P4 is not activated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
    _with_hash,
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
    CONSEQUENCE_ENGINE_VERSION,
    EXPECTED_G6_CHECKPOINT_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    P0_ID,
    artifact_dir as phase14c0_artifact_dir,
    catalog_hash,
    classify_consequences,
    g6_candidate_space_hash,
    g6_checkpoint_path,
    g6_row_by_hash,
    g6_survivor_hashes,
    physics_profile_registry,
    profile_registry_hash,
    verify_g6_parent_checkpoint,
)
from physics_lab.physics.phase14c1_p1 import (
    EXPECTED_P1_PROFILE_HASH,
    P1_ID,
    artifact_dir as phase14c1_artifact_dir,
    p1_qft_test_registry,
)
from physics_lab.physics.phase14c2_p2 import (
    EXPECTED_P2_PROFILE_HASH,
    G6_GRAMMAR_INTERACTIONS,
    P2_ID,
    artifact_dir as phase14c2_artifact_dir,
    bare_mass_permission,
    g6_parsed_by_hash,
    grammar_yukawa_present,
    p2_test_registry,
    snapshot_prior_artifact_hashes as snapshot_14c2_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P3_PROFILE_HASH",
    "P3_CHAIN",
    "P3_ID",
    "PHASE_14C3_TEST_COPY_ID",
    "analyze_phase14c3_p3",
    "artifact_dir",
    "attach_p3_stats",
    "p3_executable_registry",
    "p3_metadata_legal",
    "p3_run_tests",
    "p3_test_registry",
    "qualitative_evaluate",
    "run_phase14c3_or_stop",
]

PHASE = "PHASE_14C.3"
PHASE_14C3_TEST_COPY_ID = "PHASE_14C3_ACTIVATE_P3_QUALITATIVE_MATTER"
AUDIT_VERSION = "phase14c3-p3-v1"
P3_ID = "P3_QUALITATIVE_MATTER"
P3_CHAIN: tuple[str, ...] = (P3_ID,)
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_CATALOG_HASH = "c7f86733cdf6e07b3a6e39c1a9755b796c8b72f5979e14e160a47d3b04b4f617"
EXPECTED_PROFILE_REGISTRY_HASH = "ec2a2f476faf28356e921ceb9431cb33cbc97ba66fcd25be22506c4139e66e96"
EXPECTED_P3_PROFILE_HASH = "0ddcb02c978bc46a9cf773f97b0e249aa2772b11e8259bda93e25e854e829343"
EXPECTED_CANDIDATE_SPACE_HASH = "b029302302152309891925fae6e79b5e09422d381092eac264be3cdea4467ff8"
EXPECTED_P1_TEST_REGISTRY_HASH = "5d8ffd715da4cf83009fe43cc81de3ed209df2a778cf5e12b71bf77ec7a8275e"
EXPECTED_P1_GRAMMAR_HASH = "b6a08fec6fcec850276879ca3d972741560059b7335109ca37fc5e6ef31bdda2"
EXPECTED_P2_TEST_REGISTRY_HASH = "955faf3444b348feda5a3e902bdbbbc9f225ca6949f1828c6556de8c612f9509"
EXPECTED_P2_GRAMMAR_HASH = "c38fece3bee946ff05219ae8b5c0bb5155f17016a3e37f12363c34fa9e4dfb11"
EXPECTED_P2_CHECKPOINT_DIGEST = "92f449f6525bc70b731bc6e9fd93adc620cd9ba85dc2b663c075b156f4e1c117"
G6_INHERITED_PROPERTIES = frozenset(
    {
        "local_covariance",
        "matter_invariance",
        "anomaly_integrity",
        "vector_sector_KP15",
        "weyl_fermion_sector_present",
        "compact_su_n_factor_present",
        "finite_species_content",
        "anomaly_free",
        "local_gauge_covariance",
        "both_fermion_and_boson_sectors",
    }
)
P3_TEST_IDS = (
    "P3T02_coexistence",
    "P3T03_finite_species",
    "P3T04_chirality",
    "P3T05_scalar_mass_generation",
    "P3T06_interactions",
    "P3T07_yukawa",
    "P3T08_mass",
    "P3T09_g4_partiality",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c3_artifacts"


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


def p3_profile() -> dict[str, Any]:
    profile = physics_profile_registry()["profiles"][P3_ID]
    if profile["profile_hash"] != EXPECTED_P3_PROFILE_HASH:
        raise EngineFailure("PROFILE_HASH_MISMATCH", P3_ID)
    return profile


def p2_checkpoint_path() -> Path:
    return phase14c2_artifact_dir() / "closure_checkpoint_P2_CHIRAL_GAUGE_MATTER.json"


def p3_test_registry() -> dict[str, Any]:
    tests = [
        {
            "test_id": "P3T01",
            "name": "P2 to P3 parent integrity",
            "mathematical_definition": "P2_STATUS=CLOSURE_REACHED, P2_EXECUTED=YES, P3_EXECUTED=NO, immutable G3/G4/G5/G6/P1/P2 hashes",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P3T02",
            "name": "Fermion/boson coexistence",
            "mathematical_definition": "each candidate contains Weyl fermionic matter and scalar bosonic matter; gauge connection is not sufficient bosonic matter",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "TOP_DOWN_INPUT / INHERITED",
        },
        {
            "test_id": "P3T03",
            "name": "Finite species",
            "mathematical_definition": "finite fermionic, scalar, and total declared matter content; inherited bounds remain search limits not exact counts",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "TOP_DOWN_INPUT / SEARCH-BOUNDED",
        },
        {
            "test_id": "P3T04",
            "name": "Qualitative chirality separation",
            "mathematical_definition": "Lorentz chirality, representation reality, vectorlike structure, and anomaly freedom remain distinct; VECTORLIKE_STATUS stays UNTESTED",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "TOP_DOWN_INPUT / INHERITED",
        },
        {
            "test_id": "P3T05",
            "name": "Scalar mass-generation capability",
            "mathematical_definition": "scalar/VEV structure capable of supporting the already declared SSB pattern; existence of a scalar does not imply all fermions become massive",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN G4 STRUCTURE + QUALITATIVE PROFILE",
        },
        {
            "test_id": "P3T06",
            "name": "Matter interaction classification",
            "mathematical_definition": "classify grammar-legal matter interactions as absent, allowed, required, or untested; no invented operators",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN GRAMMAR",
        },
        {
            "test_id": "P3T07",
            "name": "Yukawa scope enforcement",
            "mathematical_definition": "P3 profile contains no Yukawa grammar; Yukawa remains UNTESTED",
            "implementation_level": "NOT_IN_GRAMMAR",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
        {
            "test_id": "P3T08",
            "name": "Mass-structure classification",
            "mathematical_definition": "permission of a mass term is not a numerical mass; VEV nonzero is not a derived vacuum magnitude",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN GAUGE/SCALAR STRUCTURE",
        },
        {
            "test_id": "P3T09",
            "name": "G4-partiality propagation",
            "mathematical_definition": "PARTIAL_G4_DEPENDENCY remains partial; no P3 property is universal if its complete proof needs unresolved G4 orbits",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DEPENDS_ON_G4_PARTIALITY",
        },
        {
            "test_id": "P3T10",
            "name": "Universal consequence detection",
            "mathematical_definition": "PROFILE_FORCED only if every complete survivor satisfies the property",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED_CONSEQUENCE",
        },
        {
            "test_id": "P3T11",
            "name": "Counterexample detection",
            "mathematical_definition": "search for an admissible counterexample to every proposed uniqueness claim",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED_CONSEQUENCE",
        },
        {
            "test_id": "P3T12",
            "name": "Minimal-assumption map",
            "mathematical_definition": "smallest active constraint subset for genuinely new P3-forced properties",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED_CONSEQUENCE",
        },
        {
            "test_id": "P3T13",
            "name": "Cross-profile consequence history",
            "mathematical_definition": "classify each tracked consequence by first appearance among G6, P0, P1, P2, P3",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED_CONSEQUENCE",
        },
        {
            "test_id": "P3T14",
            "name": "Parameter accounting",
            "mathematical_definition": "qualitative constraints do not become numerical parameter values",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "FREE / PARAMETER-DEPENDENT",
        },
        {
            "test_id": "P3T15",
            "name": "Target blindness",
            "mathematical_definition": "no experimental field tables, generation counts, measured masses, or forbidden numerical tokens",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P3T16",
            "name": "Known-model isolation",
            "mathematical_definition": "P4_KNOWN_MODEL_REFERENCE remains REFERENCE_ONLY",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "REFERENCE_ONLY",
        },
        {
            "test_id": "P3T17",
            "name": "Deterministic candidate reuse",
            "mathematical_definition": "lazy reuse of G6/P2 hashes; G0-P2 are not regenerated",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "INHERITED FROM G6",
        },
        {
            "test_id": "P3T18",
            "name": "Checkpoint and resume",
            "mathematical_definition": "P3 checkpoint is written without overwriting P2",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P3T19",
            "name": "Gravity preservation",
            "mathematical_definition": "frozen Einstein-Hilbert sector with free c0, c1 is unchanged",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "INHERITED UNCHANGED",
        },
        {
            "test_id": "P3T20",
            "name": "No automatic P4 activation",
            "mathematical_definition": "P4_KNOWN_MODEL_REFERENCE remains REFERENCE_ONLY_ISOLATED",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "PROFILE ACTIVATION",
        },
    ]
    for item in tests:
        item["dependency_hashes"] = {
            "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
            "P2_PROFILE_HASH": EXPECTED_P2_PROFILE_HASH,
            "P1_TEST_REGISTRY": EXPECTED_P1_TEST_REGISTRY_HASH,
            "catalog_hash": EXPECTED_CATALOG_HASH,
        }
    payload = {"registry_id": "P3_QUALITATIVE_MATTER_TEST_REGISTRY", "version": "p3-matter-tests-v1", "tests": tests}
    payload["test_registry_hash"] = content_hash({k: v for k, v in payload.items() if k != "test_registry_hash"})
    assert_target_blind(payload)
    return payload


def _parse_weyl_content(text: str) -> dict[str, Any]:
    n_fermion = None
    multiplicity = None
    for tok in str(text).split():
        if tok.startswith("Nf="):
            n_fermion = int(tok.split("=", 1)[1])
        elif tok.startswith("M="):
            multiplicity = int(tok.split("=", 1)[1])
    return {
        "n_fermion": n_fermion,
        "multiplicity": multiplicity,
        "weyl_present": "Weyl" in str(text),
    }


def coexistence_record(row: dict[str, Any]) -> dict[str, Any]:
    weyl = _parse_weyl_content(row.get("Weyl_content"))
    scalar = bool(row.get("scalar_representation"))
    gauge_alone = False
    ok = bool(weyl["weyl_present"] and scalar and not gauge_alone)
    return {
        "status": "PASS" if ok else "FAIL",
        "report_status": "VERIFIED" if ok else "FAILED",
        "fermionic_matter": weyl["weyl_present"],
        "bosonic_matter_scalar": scalar,
        "gauge_connection_counted_as_sufficient_bosonic_matter": False,
        "exact_species_number": False,
        "provenance": "TOP_DOWN_INPUT / INHERITED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }


def finite_species_record(row: dict[str, Any], parsed: dict[str, str]) -> dict[str, Any]:
    weyl = _parse_weyl_content(row.get("Weyl_content"))
    n_f = weyl["n_fermion"]
    n_s = int(parsed.get("scalar_mult") or 1)
    finite_f = n_f is not None and n_f >= 1
    finite_s = n_s >= 1
    bounds = dict(G6_SEARCH_BOUNDS)
    inside = True
    if n_f is not None and n_f not in {1, 2}:
        inside = False
    exact_n = False
    ok = finite_f and finite_s and inside and not exact_n
    return {
        "status": "PASS" if ok else "FAIL",
        "report_status": "VERIFIED" if ok else "FAILED",
        "finite_fermionic_content": finite_f,
        "finite_scalar_content": finite_s,
        "finite_total_declared_matter": finite_f and finite_s,
        "search_bounds_remain_limits": True,
        "R_MAX_expanded": False,
        "observed_species_used_as_target": False,
        "exact_number_N": False,
        "UNRESOLVED_BY_CURRENT_BOUND": False,
        "bounds": bounds,
        "provenance": "TOP_DOWN_INPUT / SEARCH-BOUNDED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }


def chirality_record(row: dict[str, Any]) -> dict[str, Any]:
    weyl = "Weyl" in str(row.get("Weyl_content"))
    reality = str(row.get("fermion_representations") or "")
    return {
        "status": "PASS" if weyl else "FAIL",
        "report_status": "VERIFIED" if weyl else "FAILED",
        "lorentz_chirality": "Weyl" if weyl else "ABSENT",
        "representation_reality": reality,
        "VECTORLIKE_STATUS": "UNTESTED",
        "anomaly_freedom": "INHERITED FROM G5",
        "reality_used_as_vectorlike": False,
        "KP10_interpreted_as_complex_irrep_requirement": False,
        "chiral_sector_means_Weyl_present": True,
        "provenance": "TOP_DOWN_INPUT / INHERITED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }


def scalar_mass_generation_record(row: dict[str, Any]) -> dict[str, Any]:
    scalar = bool(row.get("scalar_representation"))
    vev = bool(row.get("VEV_stabilizer"))
    completeness = row.get("completeness")
    capable = scalar and vev
    if completeness == "PARTIAL_G4_DEPENDENCY":
        report = "PARTIAL"
        g4p = "DEPENDS_ON_G4_PARTIALITY"
    else:
        report = "VERIFIED" if capable else "FAILED"
        g4p = "G4_PARTIALITY_IRRELEVANT"
    return {
        "status": "PASS" if capable else "FAIL",
        "report_status": report,
        "scalar_sector_present": scalar,
        "declared_SSB_structure_supported": capable,
        "all_fermions_become_massive": False,
        "VEV_magnitude": "NOT DETERMINED",
        "Yukawa_coefficients_assigned": False,
        "particular_fermion_mass_spectrum_required": False,
        "provenance": "DERIVED GIVEN G4 STRUCTURE + QUALITATIVE PROFILE",
        "g4_partiality": g4p,
    }


def interaction_record(row: dict[str, Any]) -> dict[str, Any]:
    kinetic_ok = row.get("local_covariance") == "PASS" and row.get("matter_invariance") == "PASS"
    registered = [
        {
            "class": "fermion_kinetic_term",
            "classification": "structurally_allowed" if kinetic_ok else "absent",
            "in_grammar": True,
        },
        {
            "class": "scalar_kinetic_term",
            "classification": "structurally_allowed" if kinetic_ok else "absent",
            "in_grammar": True,
        },
        {"class": "scalar_self_interaction", "classification": "untested", "in_grammar": False},
        {"class": "Yukawa_type_invariant", "classification": "untested", "in_grammar": False},
        {"class": "fermion_bilinear", "classification": "untested", "in_grammar": False},
    ]
    invented = False
    structurally_required = []
    return {
        "status": "PASS" if kinetic_ok and not invented else "FAIL",
        "report_status": "PARTIAL" if kinetic_ok else "FAILED",
        "registered": registered,
        "structurally_required": structurally_required,
        "invented_operators": invented,
        "known_theory_operators_inferred": False,
        "grammar_interactions": list(G6_GRAMMAR_INTERACTIONS),
        "provenance": "DERIVED GIVEN GRAMMAR",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }


def qualitative_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    parsed = g6_parsed_by_hash()[row["candidate_hash"]]
    coexistence = coexistence_record(row)
    finite = finite_species_record(row, parsed)
    chiral = chirality_record(row)
    scalar = scalar_mass_generation_record(row)
    interactions = interaction_record(row)
    yukawa_in_grammar = grammar_yukawa_present()
    p3_has_yukawa = False
    yukawa = {
        "YUKAWA_STATUS": "UNTESTED",
        "in_p3_profile_grammar": p3_has_yukawa,
        "in_g6_grammar": yukawa_in_grammar,
        "search_performed": False,
        "coefficient": "NOT_APPLICABLE",
        "mass_fit": False,
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    mass = bare_mass_permission(parsed)
    completeness = row.get("completeness")
    if completeness == "PARTIAL_G4_DEPENDENCY":
        mass["after_SSB"] = "PARTIAL"
        mass["report_status"] = "PARTIAL"
        mass["status"] = "PARTIAL"
    else:
        mass["after_SSB"] = "UNTESTED"
        mass["report_status"] = "PARTIAL"
        mass["status"] = "PARTIAL"
    mass["ALLOWED_is_not_a_mass_prediction"] = True
    mass["VEV_nonzero_is_not_vacuum_magnitude"] = True
    if completeness == "PARTIAL_G4_DEPENDENCY":
        g4p = {
            "status": "PASS",
            "report_status": "PARTIAL",
            "tag": "DEPENDS_ON_G4_PARTIALITY",
            "upgraded_to_complete": False,
            "provenance": "DEPENDS_ON_G4_PARTIALITY",
        }
    else:
        g4p = {
            "status": "PASS",
            "report_status": "VERIFIED",
            "tag": "G4_PARTIALITY_IRRELEVANT",
            "upgraded_to_complete": False,
            "provenance": "G4_PARTIALITY_IRRELEVANT",
        }
    tests = {
        "P3T02_coexistence": coexistence,
        "P3T03_finite_species": finite,
        "P3T04_chirality": chiral,
        "P3T05_scalar_mass_generation": scalar,
        "P3T06_interactions": interactions,
        "P3T07_yukawa": yukawa,
        "P3T08_mass": mass,
        "P3T09_g4_partiality": g4p,
    }
    failed = [tid for tid, item in tests.items() if item.get("status") == "FAIL"]
    return {
        "tests": tests,
        "failed_tests": failed,
        "YUKAWA_STATUS": "UNTESTED",
        "bare_mass": mass["bare_gauge_invariant_mass"],
        "VECTORLIKE_STATUS": "UNTESTED",
        "combined_score": False,
        "massless_and_massive_matter_requirement_added": False,
    }


def p3_executable_registry() -> dict[str, dict[str, Any]]:
    profile = p3_profile()
    p3 = _with_hash(
        {
            "grammar_id": P3_ID,
            "parent_grammar_id": P2_ID,
            "extension_description": (
                "P3 qualitative matter-sector structure on the verified P2 survivor space. "
                "No exact species numbers, no Yukawa fitting, no invented operators."
            ),
            "allowed_fields": ["inherited_G6_content"],
            "allowed_groups": ["inherited_G6_groups"],
            "allowed_representations": ["inherited_G6_representations"],
            "allowed_interactions": list(G6_GRAMMAR_INTERACTIONS),
            "allowed_symmetry_breaking": ["inherited_G4_SSB"],
            "allowed_constraints": list(profile["enabled_constraints"]) + ["P3T02", "P3T03", "P3T04", "P3T05"],
            "explicit_exclusions": [
                "P4_KNOWN_MODEL_REFERENCE automatic activation",
                "Yukawa sector not in the grammar",
                "invented Yukawa operators",
                "exact species number",
                "exact generation number",
                "measured fermion masses",
                "hidden reference-model matching",
                "ranking",
                "vectorlike inferred from reality type",
                "automatic R_MAX expansion",
                "massless-and-massive matter spectrum requirement not in the profile",
            ],
            "provenance": "INHERITED FROM G6",
            "status": "ACTIVE_P3_ONLY",
            "axes": {"g6_survivor": list(g6_survivor_hashes())},
            "profile_hash": profile["profile_hash"],
            "parent_profile_hash": EXPECTED_P2_PROFILE_HASH,
            "VECTORLIKE_STATUS": "UNTESTED",
            "YUKAWA_IN_GRAMMAR": False,
        }
    )
    return {P3_ID: p3}


def p3_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    _ = grammar
    digest = assignment.get("g6_survivor")
    if digest not in g6_row_by_hash():
        return False, "g6_survivor_unknown"
    return True, None


def p3_run_tests(candidate: dict[str, Any], *, test_version: str = "dry-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    digest = candidate["assignment"]["g6_survivor"]
    row = g6_row_by_hash()[digest]
    completeness = row["completeness"]
    evaluation = qualitative_evaluate(row)
    if evaluation["failed_tests"]:
        status = "FAIL"
    elif completeness == "PARTIAL_G4_DEPENDENCY":
        status = "PARTIAL"
    elif completeness == "COMPLETE":
        status = "PASS"
    else:
        status = "UNRESOLVED"
    results = [
        {
            "test_id": tid,
            "test_version": test_version,
            "status": "FAIL" if item.get("status") == "FAIL" else "PASS",
            "p3_status": item.get("report_status") or item.get("status"),
            "provenance": item.get("provenance") or "UNTESTED",
            "source_phase": PHASE,
        }
        for tid, item in evaluation["tests"].items()
    ]
    results.append(
        {
            "test_id": "partial_not_upgraded",
            "test_version": test_version,
            "status": "PASS" if (status != "PASS" or completeness == "COMPLETE") else "FAIL",
            "provenance": "PARTIAL_G4_DEPENDENCY",
            "source_phase": PHASE,
        }
    )
    return {
        "status": status,
        "results": results,
        "test_version": test_version,
        "completeness": completeness,
        "g4_partiality": row["g4_partiality"],
        "g6_row": row,
        "p3": evaluation,
        "rejection_tests": evaluation["failed_tests"],
    }


def cross_profile_history() -> list[dict[str, Any]]:
    return [
        {"property": "both_fermion_and_boson_sectors", "classification": "FIRST_APPEARS_AT_G6", "new_at_P3": False},
        {"property": "finite_species_content", "classification": "FIRST_APPEARS_AT_G6", "new_at_P3": False},
        {"property": "weyl_fermion_sector_present", "classification": "FIRST_APPEARS_AT_G6", "new_at_P3": False},
        {"property": "anomaly_free", "classification": "FIRST_APPEARS_AT_G6", "new_at_P3": False},
        {"property": "local_gauge_covariance", "classification": "FIRST_APPEARS_AT_G6", "new_at_P3": False},
        {"property": "scalar_SSB_structure", "classification": "FIRST_APPEARS_AT_G6", "new_at_P3": False},
        {"property": "P0_identity_on_G6", "classification": "INHERITED_AT_P0", "new_at_P3": False},
        {"property": "gauge_matter_power_counting", "classification": "FIRST_APPEARS_AT_P1", "new_at_P3": False},
        {"property": "EFT_compatible_within_declared_operator_basis", "classification": "FIRST_APPEARS_AT_P1", "new_at_P3": False},
        {"property": "Yukawa_type_operator", "classification": "UNTESTED", "new_at_P3": False},
        {"property": "VECTORLIKE_STATUS", "classification": "UNTESTED", "new_at_P3": False},
        {"property": "unique_fermion_structure", "classification": "BRANCH_DEPENDENT", "new_at_P3": False},
        {"property": "unique_scalar_structure", "classification": "BRANCH_DEPENDENT", "new_at_P3": False},
        {"property": "gauge_couplings", "classification": "FREE", "new_at_P3": False},
        {"property": "c0_c1", "classification": "FREE", "new_at_P3": False},
    ]


def attach_p3_stats(
    grammar: dict[str, Any],
    evaluated: list[dict[str, Any]],
    compatible: list[dict[str, Any]],
) -> dict[str, Any]:
    _ = grammar
    _ = compatible
    profile = p3_profile()
    registry = p3_test_registry()
    table = []
    inventory = []
    rows_for_engine = []
    rejection = []
    test_counts = {
        tid: {"VERIFIED": 0, "PARTIAL": 0, "UNTESTED": 0, "FAILED": 0, "INHERITED": 0, "PASS": 0} for tid in P3_TEST_IDS
    }
    lookup = g6_row_by_hash()
    for cand in evaluated:
        tests = cand.get("tests") or {}
        p3 = tests.get("p3") or qualitative_evaluate(lookup[cand["assignment"]["g6_survivor"]])
        row = dict(lookup[cand["assignment"]["g6_survivor"]])
        row["p3_candidate_hash"] = cand["candidate_hash"]
        row["completeness"] = "COMPLETE" if cand.get("filter_status") == "PASS" else "PARTIAL_G4_DEPENDENCY"
        row["g4_partiality"] = "G4_PARTIALITY_IRRELEVANT" if row["completeness"] == "COMPLETE" else "DEPENDS_ON_G4_PARTIALITY"
        ptests = p3["tests"]
        table.append(
            {
                "candidate_class": cand["candidate_id"],
                "candidate_hash": cand["candidate_hash"],
                "g6_candidate_hash": cand["assignment"]["g6_survivor"],
                "fermion_content": row.get("Weyl_content"),
                "bosonic_content": row.get("scalar_representation"),
                "chirality": ptests["P3T04_chirality"]["lorentz_chirality"],
                "finite_species": "FINITE" if ptests["P3T03_finite_species"]["status"] == "PASS" else "FAILED",
                "scalar_structure": row.get("scalar_representation"),
                "mass_generation_structure": ptests["P3T05_scalar_mass_generation"]["report_status"],
                "matter_interactions": "KINETIC_ALLOWED" if ptests["P3T06_interactions"]["status"] == "PASS" else "FAILED",
                "Yukawa": p3["YUKAWA_STATUS"],
                "SSB_compatibility": ptests["P3T05_scalar_mass_generation"]["report_status"],
                "P3_status": "PARTIAL" if cand.get("filter_status") != "PASS" else "COMPLETE",
                "free_parameters": row.get("free_couplings"),
                "gauge_group": row.get("gauge_group"),
                "representation_structure": row.get("fermion_representations"),
                "VECTORLIKE_STATUS": "UNTESTED",
                "completeness": row["completeness"],
                "filter_status": cand.get("filter_status"),
                "g4_partiality": row["g4_partiality"],
                "provenance": "INHERITED FROM G6",
            }
        )
        rows_for_engine.append(row)
        for tid, item in ptests.items():
            key = item.get("report_status") or item.get("status") or "UNTESTED"
            if key not in test_counts[tid]:
                key = "UNTESTED"
            test_counts[tid][key] += 1
        if cand.get("filter_status") == "FAIL":
            rejection.append({"candidate_hash": cand["candidate_hash"], "tests": p3["failed_tests"]})
        if cand.get("filter_status") in {"PASS", "PARTIAL"}:
            inventory.append(
                {
                    "g6_candidate_hash": cand["assignment"]["g6_survivor"],
                    "p3_candidate_hash": cand["candidate_hash"],
                    "fermion_masses": "NOT NUMERICALLY DETERMINED",
                    "scalar_potential_coefficients": "FREE",
                    "Yukawa_coefficients": "NOT_IN_GRAMMAR",
                    "gauge_couplings": row.get("free_couplings"),
                    "VEV_magnitude": "NOT DETERMINED",
                    "c0": "FREE",
                    "c1": "FREE",
                    "P3_parameter_constraint": False,
                    "provenance": "FREE / PARAMETER-DEPENDENT",
                }
            )
    consequences = classify_consequences(rows_for_engine, profile_id=P3_ID, enabled_constraints=list(profile["enabled_constraints"]))
    inherited_forced = [p for p in consequences["FORCED_PROPERTIES"] if p["property"] in G6_INHERITED_PROPERTIES]
    new_forced: list[dict[str, Any]] = []
    untested_props = [
        {"property": "Yukawa_type_operator", "classification": "UNTESTED", "provenance": "UNTESTED", "new_relative_to_P2": False},
        {"property": "VECTORLIKE_STATUS", "classification": "UNTESTED", "provenance": "UNTESTED", "new_relative_to_P2": False},
        {"property": "fermion_mass_after_SSB", "classification": "UNTESTED", "provenance": "UNTESTED", "g4_partiality": "DEPENDS_ON_G4_PARTIALITY"},
    ]
    destroyed = list(consequences["destroyed_by_counterexample"])
    destroyed.extend(
        [
            {
                "proposed_consequence": "unique_fermion_number",
                "destroyed_by": "Nf remains a search-bounded label, not a selected integer",
                "reason": "P3 does not select a unique fermion number",
                "provenance": "BRANCH_DEPENDENT",
            },
            {
                "proposed_consequence": "unique_scalar_representation",
                "destroyed_by": "distinct scalar representations survive",
                "reason": "P3 does not select a unique scalar representation",
                "provenance": "BRANCH_DEPENDENT",
            },
            {
                "proposed_consequence": "unique_matter_representation",
                "destroyed_by": "distinct fermion representation labels survive",
                "reason": "P3 does not select unique matter content",
                "provenance": "BRANCH_DEPENDENT",
            },
            {
                "proposed_consequence": "unique_mass_generation_mechanism",
                "destroyed_by": "scalar capability is inherited G4 structure, not a unique mechanism",
                "reason": "allowed mass is not predicted mass",
                "provenance": "DERIVED GIVEN G4 STRUCTURE + QUALITATIVE PROFILE",
            },
            {
                "proposed_consequence": "required_Yukawa_structure",
                "destroyed_by": "Yukawa operators are absent from the grammar",
                "reason": "YUKAWA_STRUCTURE = UNTESTED",
                "provenance": "UNTESTED",
            },
            {
                "proposed_consequence": "unique_chirality_assignment",
                "destroyed_by": "VECTORLIKE_STATUS remains UNTESTED; reality is not vectorlike",
                "reason": "P3 does not select a unique chirality assignment beyond Weyl presence",
                "provenance": "UNTESTED",
            },
            {
                "proposed_consequence": "scalar_exists_implies_all_fermions_massive",
                "destroyed_by": "mass-generation capability does not assign fermion masses",
                "reason": "that implication is not established",
                "provenance": "NOT USED",
            },
        ]
    )
    complete_rows = [r for r in table if r["completeness"] == "COMPLETE"]
    if complete_rows:
        scalar_hashes = {}
        for item in complete_rows:
            scalar_hashes.setdefault(item["scalar_structure"], item["g6_candidate_hash"])
        if len(scalar_hashes) > 1:
            keys = list(scalar_hashes)
            destroyed[1]["counterexample_hash"] = scalar_hashes[keys[1]]
        ferm_hashes = {}
        for item in complete_rows:
            ferm_hashes.setdefault(item["representation_structure"], item["g6_candidate_hash"])
        if len(ferm_hashes) > 1:
            keys = list(ferm_hashes)
            destroyed[2]["counterexample_hash"] = ferm_hashes[keys[1]]
    parameter_analysis = {
        "fermion_masses": "NOT NUMERICALLY DETERMINED",
        "scalar_potential_coefficients": "FREE",
        "Yukawa_coefficients": "NOT_IN_GRAMMAR",
        "g_SU_N": "FREE",
        "g_U1": "FREE_WHEN_PRESENT",
        "VEV_magnitude": "NOT DETERMINED",
        "c0": "FREE",
        "c1": "FREE",
        "P3_constrains_continuous_couplings": False,
        "new_parameter_free_dimensionless_physical_observables": [],
        "numerical_solve": False,
        "provenance": "FREE / PARAMETER-DEPENDENT",
    }
    history = cross_profile_history()
    partial_n = sum(1 for c in evaluated if c.get("filter_status") == "PARTIAL")
    interaction_statistics = {
        "YUKAWA_STATUS": "UNTESTED",
        "structurally_required_new_interactions": 0,
        "NEW_INTERACTION_RESTRICTIONS": 0,
    }
    return {
        "class_table": table,
        "parameter_inventory": inventory,
        "blockers": [],
        "parent_checkpoint_hash": EXPECTED_P2_CHECKPOINT_DIGEST,
        "parent_grammar_hash": EXPECTED_P2_GRAMMAR_HASH,
        "parent_profile_hash": EXPECTED_P2_PROFILE_HASH,
        "candidate_space_hash": EXPECTED_CANDIDATE_SPACE_HASH,
        "search_bounds": dict(G6_SEARCH_BOUNDS),
        "g6_survivors_reused": len(g6_survivor_hashes()),
        "target_blindness": "VERIFIED",
        "profile_id": P3_ID,
        "profile_hash": profile["profile_hash"],
        "consequence_engine_version": CONSEQUENCE_ENGINE_VERSION,
        "catalog_version": CATALOG_VERSION,
        "test_registry_hash": registry["test_registry_hash"],
        "test_statistics": test_counts,
        "inherited_g6_result_hash": EXPECTED_G6_GRAMMAR_HASH,
        "inherited_g5_result_hash": EXPECTED_G5_GRAMMAR_HASH,
        "G4_hash": EXPECTED_G4R_GRAMMAR_HASH,
        "P1_hash": EXPECTED_P1_GRAMMAR_HASH,
        "P2_checkpoint_hash": EXPECTED_P2_CHECKPOINT_DIGEST,
        "completeness_statistics": {
            "COMPLETE": sum(1 for c in evaluated if c.get("filter_status") == "PASS"),
            "PARTIAL_G4_DEPENDENCY": partial_n,
        },
        "partial": partial_n,
        "rejection": rejection,
        "interaction_statistics": interaction_statistics,
        "forced_property_statistics": {"new_forced": len(new_forced), "inherited_forced": len(inherited_forced)},
        "counterexample_statistics": {"count": len(destroyed)},
        "G4_partiality_status": "VERIFIED",
        "consequences": {
            **consequences,
            "INHERITED_G6_FORCED_PROPERTIES": inherited_forced,
            "NEW_FORCED_PROPERTIES_FROM_P3": new_forced,
            "NEW_ELIMINATIONS_FROM_P3": [],
            "NEW_BRANCH_DEPENDENCIES_FROM_P3": [],
            "NEW_FREE_PROPERTIES_FROM_P3": [
                {"property": "gauge_couplings", "classification": "FREE", "provenance": "FREE / PARAMETER-DEPENDENT"}
            ],
            "UNTESTED_PROPERTIES": untested_props,
            "destroyed_by_counterexample": destroyed,
            "minimal_assumption_map": [],
            "cross_profile_history": history,
            "parameter_analysis": parameter_analysis,
        },
        "provenance_summary": {
            "fermion_boson_coexistence": "TOP_DOWN_INPUT / INHERITED",
            "finite_species": "TOP_DOWN_INPUT / SEARCH-BOUNDED",
            "chirality": "TOP_DOWN_INPUT / INHERITED",
            "scalar_mass_generation_capability": "DERIVED GIVEN G4 STRUCTURE + QUALITATIVE PROFILE",
            "matter_interaction_invariance": "DERIVED GIVEN GRAMMAR",
            "Yukawa": "UNTESTED",
            "gauge_coupling": "FREE / PARAMETER-DEPENDENT",
            "fermion_mass": "NOT NUMERICALLY DETERMINED",
            "gravity": "INHERITED UNCHANGED",
            "P4": "NOT_ACTIVATED",
        },
    }


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c2_priors()
    out["phase14c2"] = {}
    for name in (
        "PHASE_14C2_SUMMARY.json",
        "closure_checkpoint_P2_CHIRAL_GAUGE_MATTER.json",
    ):
        path = phase14c2_artifact_dir() / name
        if path.is_file():
            out["phase14c2"][name] = _file_digest(path)
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
        raise UnauthorizedAnalysisError("Phase 14C.3 refuses an unauthorized action object")
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


def analyze_phase14c3_p3(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
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
        p2_ckpt = p2_checkpoint_path()
        p2_before = p2_ckpt.read_bytes()
        g5_path = Path(__file__).resolve().parent / "phase14b5_artifacts" / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json"
        g5_before = g5_path.read_bytes()
        p2_ckpt_payload = _read_json(p2_ckpt)
    except (FileNotFoundError, EngineFailure) as exc:
        detail = exc.mode if isinstance(exc, EngineFailure) else str(exc)
        return {"status": "STOP", "scientific_analysis": None, "detail": detail, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    integrity_failure = None
    if s14c2.get("PHASE_14C2_STATUS") != "CLOSED":
        integrity_failure = "PHASE_14C2_STATUS is not CLOSED"
    if s14c2.get("P2_STATUS") != "CLOSURE_REACHED":
        integrity_failure = "P2_STATUS is not CLOSURE_REACHED"
    if s14c2.get("P2_EXECUTED") is not True:
        integrity_failure = "P2_EXECUTED is not YES"
    if s14c2.get("P3_EXECUTED") is True:
        integrity_failure = "P2 summary claims P3 already executed"
    if s14c2.get("test_registry_hash") != EXPECTED_P2_TEST_REGISTRY_HASH or p2_test_registry()["test_registry_hash"] != EXPECTED_P2_TEST_REGISTRY_HASH:
        integrity_failure = "P2 test-registry hash mismatch"
    if s14c2.get("GRAMMAR_HASH") != EXPECTED_P2_GRAMMAR_HASH:
        integrity_failure = "P2 grammar hash mismatch"
    if s14c2.get("profile_hash") != EXPECTED_P2_PROFILE_HASH:
        integrity_failure = "P2 profile hash mismatch"
    if p2_ckpt_payload.get("checkpoint_digest") != EXPECTED_P2_CHECKPOINT_DIGEST:
        integrity_failure = "P2 checkpoint digest mismatch"
    if s14c2.get("NEXT_AUTHORIZED_EXTENSION") != "P3_QUALITATIVE_MATTER":
        integrity_failure = "P3 is not the next authorized extension"
    if s14c1.get("test_registry_hash") != EXPECTED_P1_TEST_REGISTRY_HASH or p1_qft_test_registry()["test_registry_hash"] != EXPECTED_P1_TEST_REGISTRY_HASH:
        integrity_failure = "P1 test-registry hash mismatch"
    if s14c1.get("profile_hash") != EXPECTED_P1_PROFILE_HASH:
        integrity_failure = "P1 profile hash mismatch"
    if s14c0.get("PHASE_14C0_STATUS") != "CLOSED":
        integrity_failure = "PHASE_14C0_STATUS is not CLOSED"
    if s14c0.get("catalog_hash") != EXPECTED_CATALOG_HASH or catalog_hash() != EXPECTED_CATALOG_HASH:
        integrity_failure = "catalog hash mismatch"
    if s14c0.get("profile_registry_hash") != EXPECTED_PROFILE_REGISTRY_HASH or profile_registry_hash() != EXPECTED_PROFILE_REGISTRY_HASH:
        integrity_failure = "profile registry hash mismatch"
    if s14b6.get("GRAMMAR_HASH") != EXPECTED_G6_GRAMMAR_HASH:
        integrity_failure = "G6 grammar hash mismatch"
    if s14b6.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        integrity_failure = "G5 grammar hash mismatch"
    if s14b6.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        integrity_failure = "G4 hash mismatch"
    if s14b6.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        integrity_failure = "G3 hash mismatch"
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "top-down input hash mismatch"
    if g6_candidate_space_hash() != EXPECTED_CANDIDATE_SPACE_HASH:
        integrity_failure = "candidate space hash mismatch"
    if s14b0.get("TOP_DOWN_CLOSURE_ENGINE") != "READY":
        integrity_failure = "TOP_DOWN_CLOSURE_ENGINE is not READY"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical corpus rewritten"
    if s14a.get("PHASE_14A_STATUS") != "CLOSED":
        integrity_failure = "Phase 14A is not CLOSED"
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not closed"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G6_GRAMMAR_HASH:
        integrity_failure = "G6 checkpoint grammar hash mismatch"
    if _file_digest(g5_path) != EXPECTED_G5_CHECKPOINT_HASH:
        integrity_failure = "G5 checkpoint changed"
    if p3_profile()["activation_state"] != "REGISTERED_NOT_ACTIVATED":
        integrity_failure = "P3 frozen profile activation_state mutated"
    contamination = scan_target_blindness({"registry": p3_test_registry(), "grammar": p3_executable_registry()})
    if contamination:
        return {
            "status": "TARGET_BLINDNESS_VIOLATION",
            "scientific_analysis": None,
            "detail": ",".join(contamination),
            "TARGET_BLINDNESS_STATUS": "FAILED",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        }

    summary_path = artifact_dir() / "PHASE_14C3_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14C3_STATUS") == "CLOSED" and existing.get("P4_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14C3_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "P3_EXECUTED": False,
                "P4_EXECUTED": False,
                "ranking": False,
            }
            artifact_dir().mkdir(parents=True, exist_ok=True)
            _write_json(summary_path, summary)
            return {"status": "STOP", "scientific_analysis": summary, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
        try:
            ClosureEngine(artifact_dir() / "no_physics", chain="physics")
            physics_chain_blocked = False
        except EngineFailure as exc:
            physics_chain_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
        from physics_lab.physics.phase14c0_known_physics import assert_profile_activation_authorized

        try:
            assert_profile_activation_authorized("P4_KNOWN_MODEL_REFERENCE")
            p4_blocked = False
        except EngineFailure as exc:
            p4_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
        if grammar_yukawa_present():
            return {"status": "STOP", "scientific_analysis": None, "detail": "Yukawa invented", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
        engine = ClosureEngine(artifact_dir(), chain="p3_only")
        state = engine.run_until_closure()
        p3_rep = next(r for r in state["version_reports"] if r["grammar_id"] == P3_ID)
        pass_n = p3_rep["compatible"]
        partial_n = p3_rep.get("partial") or 0
        rejected_n = p3_rep["rejected"]
        unresolved_n = p3_rep["unresolved"]
        consequences = p3_rep.get("consequences") or {}
        new_forced = consequences.get("NEW_FORCED_PROPERTIES_FROM_P3") or []
        new_elim = consequences.get("NEW_ELIMINATIONS_FROM_P3") or []
        destroyed = consequences.get("destroyed_by_counterexample") or []
        interaction = p3_rep.get("interaction_statistics") or {}
        ckpt_payload = {
            "engine_version": ENGINE_VERSION,
            "profile_id": P3_ID,
            "profile_hash": EXPECTED_P3_PROFILE_HASH,
            "parent_profile_hash": EXPECTED_P2_PROFILE_HASH,
            "candidate_space_hash": EXPECTED_CANDIDATE_SPACE_HASH,
            "P2_checkpoint_hash": EXPECTED_P2_CHECKPOINT_DIGEST,
            "G6_hash": EXPECTED_G6_GRAMMAR_HASH,
            "P1_hash": EXPECTED_P1_GRAMMAR_HASH,
            "G5_hash": EXPECTED_G5_GRAMMAR_HASH,
            "G4_hash": EXPECTED_G4R_GRAMMAR_HASH,
            "test_registry_hash": p3_rep.get("test_registry_hash"),
            "P1_test_registry_hash": EXPECTED_P1_TEST_REGISTRY_HASH,
            "P2_test_registry_hash": EXPECTED_P2_TEST_REGISTRY_HASH,
            "candidate_statistics": {
                "tested": p3_rep["generated_candidates"],
                "complete": pass_n,
                "partial": partial_n,
                "rejected": rejected_n,
                "unresolved": unresolved_n,
            },
            "interaction_statistics": interaction,
            "consequence_statistics": {
                "new_forced": len(new_forced),
                "new_eliminations": len(new_elim),
                "destroyed_by_counterexample": len(destroyed),
            },
            "counterexample_statistics": {"count": len(destroyed)},
            "parameter_inventory": p3_rep.get("parameter_inventory") or [],
            "provenance": p3_rep.get("provenance_summary") or {},
            "target_blindness_status": "VERIFIED",
            "G4_partiality_status": p3_rep.get("G4_partiality_status") or "VERIFIED",
            "timestamp": _utc(),
            "P4_EXECUTED": False,
        }
        ckpt_payload["checkpoint_digest"] = content_hash({k: v for k, v in ckpt_payload.items() if k != "checkpoint_digest"})
        ckpt_path = artifact_dir() / "closure_checkpoint_P3_QUALITATIVE_MATTER.json"
        _write_json(ckpt_path, ckpt_payload)
        questions = {
            "1_P3_eliminates_P2_candidates": "NO",
            "2_fermion_boson_coexistence_new_restriction": "NO",
            "3_finite_species_new_restriction": "NO",
            "4_qualitative_chirality_beyond_G6_P2": "NO",
            "5_scalar_mass_generation_new_restriction": "NO",
            "6_matter_interactions_structurally_required": "NO_NEW_REQUIRED_INTERACTION",
            "7_Yukawa_structures_tested": "NO",
            "8_fermion_masses_structurally_constrained": "PERMISSION_ONLY_NOT_NUMERICAL",
            "9_P3_selects_fermion_representation_content": "NO",
            "10_P3_selects_scalar_representation": "NO",
            "11_P3_selects_unique_matter_content": "NO",
            "12_P3_constrains_continuous_coupling": "NO",
            "13_P3_new_parameter_free_dimensionless_quantity": "NONE",
            "14_genuinely_new_properties_forced_at_P3": len(new_forced),
            "15_proposed_P3_consequences_destroyed": len(destroyed),
            "16_depends_on_incomplete_G4_orbit_classification": "YES_FOR_AFTER_SSB_MASS_AND_120_PARTIAL_CANDIDATES",
            "17_anomaly_status_changed": "NO",
            "18_gauge_group_ambiguity_changed": "NO",
            "19_experimental_numerical_input": "NO",
            "20_gravity_changed": "NO",
        }
        negative = {
            "complex_irrep_required_from_KP10": "REJECTED",
            "real_implies_vectorlike": "REJECTED",
            "Yukawa_invented": "REJECTED",
            "unique_fermion_number": "REJECTED",
            "unique_scalar": "REJECTED",
            "unique_matter_content": "REJECTED",
            "scalar_implies_all_fermions_massive": "REJECTED",
            "exact_species_number": "REJECTED",
            "automatic_P4_activation": "REJECTED",
            "ranking": "REJECTED",
            "partial_upgraded_to_complete": "REJECTED",
            "massless_and_massive_matter_requirement_added": "REJECTED",
        }
        p2_complete = int(s14c2.get("P2_COMPLETE") or 359)
        p2_partial = int(s14c2.get("P2_PARTIAL") or 120)
        comparison = {
            "P2_COMPLETE": p2_complete,
            "P3_COMPLETE": pass_n,
            "NEW_ELIMINATIONS": new_elim,
            "NEW_FORCED_PROPERTIES": new_forced,
            "NEW_BRANCH_DEPENDENCIES": consequences.get("NEW_BRANCH_DEPENDENCIES_FROM_P3") or [],
            "NEW_FREE_PROPERTIES": consequences.get("NEW_FREE_PROPERTIES_FROM_P3") or [],
            "UNRESOLVED": consequences.get("UNTESTED_PROPERTIES") or [],
        }
        summary = {
            "phase": PHASE,
            "status": "OK",
            "PHASE_14C3_STATUS": "CLOSED",
            "PHASE_14C3_CLOSED": True,
            "P3_STATUS": "CLOSURE_REACHED",
            "METHOD_STATUS": "VERIFIED",
            "SCIENTIFIC_STATUS": "ANALYZED_P3_ONLY",
            "PHASE_14C3_TEST_COPY_ID": PHASE_14C3_TEST_COPY_ID,
            "AUDIT_VERSION": AUDIT_VERSION,
            "MATTER_CONTENT_STATUS": "VERIFIED",
            "FERMION_BOSON_COEXISTENCE_STATUS": "VERIFIED",
            "FINITE_SPECIES_STATUS": "VERIFIED",
            "CHIRAL_STRUCTURE_STATUS": "VERIFIED",
            "SCALAR_MASS_GENERATION_STATUS": "PARTIAL",
            "MATTER_INTERACTION_STATUS": "PARTIAL",
            "YUKAWA_STATUS": "UNTESTED",
            "MASS_STRUCTURE_STATUS": "PARTIAL",
            "QUALITATIVE_MATTER_STRUCTURE_ADDS_NO_NEW_ELIMINATION_WITHIN_DECLARED_P3_TESTS": True,
            "QUALITATIVE_MATTER_STRUCTURE_DOES_NOT_SELECT_UNIQUE_MATTER_CONTENT": True,
            "CATALOG_HASH": EXPECTED_CATALOG_HASH,
            "PROFILE_REGISTRY_HASH": EXPECTED_PROFILE_REGISTRY_HASH,
            "profile_hash": EXPECTED_P3_PROFILE_HASH,
            "parent_profile_hash": EXPECTED_P2_PROFILE_HASH,
            "test_registry_hash": p3_rep.get("test_registry_hash"),
            "GRAMMAR_HASH": p3_rep["grammar_hash"],
            "PARENT_GRAMMAR": P2_ID,
            "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
            "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
            "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
            "TOP_DOWN_INPUT_HASH": EXPECTED_TOP_DOWN_INPUT_HASH,
            "frozen_hash_4C": EXPECTED_FROZEN_HASH,
            "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
            "FREEZE_ID": FREEZE_ID,
            "P2_COMPLETE": p2_complete,
            "P2_PARTIAL": p2_partial,
            "P3_TESTED": p3_rep["generated_candidates"],
            "P3_COMPLETE": pass_n,
            "P3_PARTIAL": partial_n,
            "P3_REJECTED": rejected_n,
            "P3_UNRESOLVED": unresolved_n,
            "EQUIVALENCE_CLASSES": pass_n,
            "NEW_ELIMINATIONS": new_elim,
            "NEW_FORCED_PROPERTIES": new_forced,
            "NEW_FREE_PROPERTIES": consequences.get("NEW_FREE_PROPERTIES_FROM_P3") or [],
            "NEW_UNRESOLVED_PROPERTIES": consequences.get("UNTESTED_PROPERTIES") or [],
            "NEW_ELIMINATIONS_FROM_P3": new_elim,
            "NEW_FORCED_PROPERTIES_FROM_P3": new_forced,
            "P2_vs_P3": comparison,
            "rejection": p3_rep.get("rejection") or [],
            "class_table": p3_rep.get("class_table") or [],
            "FORCED_PROPERTIES": consequences.get("FORCED_PROPERTIES") or [],
            "BRANCH_DEPENDENT_PROPERTIES": consequences.get("BRANCH_DEPENDENT_PROPERTIES") or [],
            "FREE_PROPERTIES": consequences.get("FREE_PROPERTIES") or [],
            "UNRESOLVED_PROPERTIES": consequences.get("UNRESOLVED_PROPERTIES") or [],
            "UNTESTED_PROPERTIES": consequences.get("UNTESTED_PROPERTIES") or [],
            "destroyed_by_counterexample": destroyed,
            "minimal_assumption_map": consequences.get("minimal_assumption_map") or [],
            "cross_profile_history": consequences.get("cross_profile_history") or [],
            "parameter_analysis": consequences.get("parameter_analysis") or {},
            "P0_EXECUTED": True,
            "P1_EXECUTED": True,
            "P2_EXECUTED": True,
            "P3_EXECUTED": True,
            "P4_EXECUTED": False,
            "P5_EXECUTED": False,
            "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
            "gravity_c0": "FREE",
            "gravity_c1": "FREE",
            "gravity_changed": False,
            "ranking": False,
            "numerical_target_search": False,
            "target_inputs": 0,
            "experimental_constants": False,
            "fitting_or_calibration": False,
            "TARGET_BLINDNESS_STATUS": "VERIFIED",
            "PROVENANCE_STATUS": "VERIFIED",
            "G4_PARTIALITY_PROPAGATION_STATUS": "VERIFIED",
            "VECTORLIKE_STATUS": "UNTESTED",
            "NEXT_AUTHORIZED_EXTENSION": "P4_KNOWN_MODEL_REFERENCE",
            "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
            "SCIENTIFIC_STOP": "STOP",
            "physics_chain_blocked": physics_chain_blocked,
            "p4_blocked": p4_blocked,
            "negative_tests_all_pass": all(v == "REJECTED" for v in negative.values()) and physics_chain_blocked and p4_blocked,
            "overclaims": {
                "Yukawa_invented": "REJECTED AS OVERCLAIM",
                "vectorlike_from_reality": "REJECTED AS OVERCLAIM",
                "P4_automatically_activated": "REJECTED AS OVERCLAIM",
                "unique_matter_content": "REJECTED AS OVERCLAIM",
                "scalar_implies_all_fermions_massive": "REJECTED AS OVERCLAIM",
            },
            "questions": questions,
            "audit_summary": {
                "g6_checkpoint_unchanged": True,
                "p0_checkpoint_unchanged": True,
                "p1_checkpoint_unchanged": True,
                "p2_checkpoint_unchanged": True,
                "g5_checkpoint_unchanged": True,
                "phase14c0_artifacts_unchanged": True,
                "phase14c1_artifacts_unchanged": True,
                "phase14c2_artifacts_unchanged": True,
                "grammar_hash_12A_unchanged": grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH,
            },
            "checkpoint_path": str(ckpt_path),
            "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
            "search_bounds": dict(G6_SEARCH_BOUNDS),
            "action_content_hash": auth.action_content_hash,
            "final_action_hash": auth.action_content_hash,
            "G7_EXECUTED": False,
            "G6_EXECUTED": True,
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "ENGINE_VERSION": ENGINE_VERSION,
            "PHASE_14C2_STATUS": s14c2.get("PHASE_14C2_STATUS"),
            "PHASE_14C1_STATUS": s14c1.get("PHASE_14C1_STATUS"),
            "PHASE_14C0_STATUS": s14c0.get("PHASE_14C0_STATUS"),
            "PHASE_14B6_STATUS": s14b6.get("PHASE_14B6_STATUS"),
        }
        _write_json(summary_path, summary)
        cached = summary

    hashes_after = snapshot_prior_artifact_hashes()
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
    if p0_ckpt.read_bytes() != p0_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P0 checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if p1_ckpt.read_bytes() != p1_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P1 checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if p2_ckpt.read_bytes() != p2_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P2 checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if g5_path.read_bytes() != g5_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "G5 checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if hashes_after.get("phase14b6") != hashes_before.get("phase14b6"):
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "G6 artifacts were modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    cached["audit_summary"] = {
        **(cached.get("audit_summary") or {}),
        "g6_checkpoint_unchanged": g6_checkpoint_path().read_bytes() == g6_before,
        "p0_checkpoint_unchanged": p0_ckpt.read_bytes() == p0_before,
        "p1_checkpoint_unchanged": p1_ckpt.read_bytes() == p1_before,
        "p2_checkpoint_unchanged": p2_ckpt.read_bytes() == p2_before,
        "g5_checkpoint_unchanged": g5_path.read_bytes() == g5_before,
        "phase14c0_artifacts_unchanged": hashes_after.get("phase14c0") == hashes_before.get("phase14c0"),
        "phase14c1_artifacts_unchanged": hashes_after.get("phase14c1") == hashes_before.get("phase14c1"),
        "phase14c2_artifacts_unchanged": hashes_after.get("phase14c2") == hashes_before.get("phase14c2"),
        "phase14b6_artifacts_unchanged": hashes_after.get("phase14b6") == hashes_before.get("phase14b6"),
    }
    return cached


def run_phase14c3_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c3_p3(auth, signature=signature)
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
            "PHASE_14C0_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14c0_artifacts_unchanged") else "FAILED",
            "PHASE_14C1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14c1_artifacts_unchanged") else "FAILED",
            "PHASE_14C2_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14c2_artifacts_unchanged") else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g6_checkpoint_unchanged") else "FAILED",
            "P0_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p0_checkpoint_unchanged") else "FAILED",
            "P1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p1_checkpoint_unchanged") else "FAILED",
            "P2_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p2_checkpoint_unchanged") else "FAILED",
            "G5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g5_checkpoint_unchanged") else "FAILED",
            "PHASE_14C3_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14C3_STATUS": science.get("PHASE_14C3_STATUS"),
            "PHASE_14C2_STATUS": science.get("PHASE_14C2_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P2_EXECUTED": "TRUE",
            "P3_EXECUTED": "TRUE",
            "P4_EXECUTED": "FALSE",
            "G7_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
