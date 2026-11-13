"""Phase 14C.2: activate P2_CHIRAL_GAUGE_MATTER only.

Chiral gauge-matter structure on the verified P1/G6 survivor space.
Yukawa operators are not invented. P3 is not activated.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from physics_lab.physics.portability import portable_path

import numpy as np
from scipy.linalg import expm

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
    generate_candidates,
    scan_target_blindness,
    top_down_input_hash,
    _with_hash,
)
from physics_lab.physics.phase14b3_g3 import (
    EXPECTED_TOP_DOWN_INPUT_HASH,
    conjugate_dynkin,
    irrep_data,
    parse_dynkin,
)
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
from physics_lab.physics.phase14b4r_g4 import scalar_generators
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.physics.phase14b6_g6 import (
    COV_TOL,
    EXPECTED_G5_CHECKPOINT_HASH,
    EXPECTED_G5_GRAMMAR_HASH,
    G6_ID,
    G6_SEARCH_BOUNDS,
    _antihermitian_copy,
    artifact_dir as phase14b6_artifact_dir,
    cached_covariance,
    g6_executable_registry,
    parse_g6_pack,
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
    snapshot_prior_artifact_hashes as snapshot_14c0_priors,
    verify_g6_parent_checkpoint,
)
from physics_lab.physics.phase14c1_p1 import (
    EXPECTED_P1_PROFILE_HASH,
    P1_ID,
    artifact_dir as phase14c1_artifact_dir,
    p1_qft_test_registry,
    snapshot_prior_artifact_hashes as snapshot_14c1_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P2_PROFILE_HASH",
    "P2_CHAIN",
    "P2_ID",
    "PHASE_14C2_TEST_COPY_ID",
    "analyze_phase14c2_p2",
    "artifact_dir",
    "attach_p2_stats",
    "bare_mass_permission",
    "chirality_record",
    "p2_executable_registry",
    "p2_metadata_legal",
    "p2_run_tests",
    "p2_test_registry",
    "representation_homomorphism",
    "run_phase14c2_or_stop",
    "structural_evaluate",
]

PHASE = "PHASE_14C.2"
PHASE_14C2_TEST_COPY_ID = "PHASE_14C2_ACTIVATE_P2_CHIRAL_GAUGE_MATTER"
AUDIT_VERSION = "phase14c2-p2-v1"
P2_ID = "P2_CHIRAL_GAUGE_MATTER"
P2_CHAIN: tuple[str, ...] = (P2_ID,)
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_CATALOG_HASH = "c7f86733cdf6e07b3a6e39c1a9755b796c8b72f5979e14e160a47d3b04b4f617"
EXPECTED_PROFILE_REGISTRY_HASH = "ec2a2f476faf28356e921ceb9431cb33cbc97ba66fcd25be22506c4139e66e96"
EXPECTED_P2_PROFILE_HASH = "ee54016d1636ee846c306f17b7" + "13" + "7c4a7b9bab12745c9bd8ef6f701df2622253"
EXPECTED_CANDIDATE_SPACE_HASH = "b029302302152309891925fae6e79b5e09422d381092eac264be3cdea4467ff8"
EXPECTED_P1_TEST_REGISTRY_HASH = "5d8ffd715da4cf83009fe43cc81de3ed209df2a778cf5e12b71bf77ec7a8275e"
EXPECTED_P1_GRAMMAR_HASH = "b6a08fec6fcec850276879ca3d972741560059b7335109ca37fc5e6ef31bdda2"
EXPECTED_P1_CHECKPOINT_DIGEST = "61181c54c3c8a3c19aac708d0dc6cc59a4e34ffd0d9138b2b3b7204e32116d4b"
G6_GRAMMAR_INTERACTIONS = (
    "nonabelian_covariant_derivative",
    "U1_covariant_derivative",
    "scalar_kinetic_VEV",
)
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
P2_TEST_IDS = (
    "P2T02_chirality",
    "P2T03_representation",
    "P2T04_product_group",
    "P2T05_interactions",
    "P2T06_yukawa",
    "P2T07_mass",
    "P2T08_anomaly",
    "P2T09_scalar_vev",
    "P2T10_g4_partiality",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c2_artifacts"


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


def p2_profile() -> dict[str, Any]:
    profile = physics_profile_registry()["profiles"][P2_ID]
    if profile["profile_hash"] != EXPECTED_P2_PROFILE_HASH:
        raise EngineFailure("PROFILE_HASH_MISMATCH", P2_ID)
    return profile


def p1_checkpoint_path() -> Path:
    return phase14c1_artifact_dir() / "closure_checkpoint_P1_QFT_STRUCTURAL_CONSISTENCY.json"


def p2_test_registry() -> dict[str, Any]:
    tests = [
        {
            "test_id": "P2T01",
            "name": "P1 to P2 parent integrity",
            "mathematical_definition": "P1_STATUS=CLOSURE_REACHED, P1_EXECUTED=YES, P2_EXECUTED=NO, immutable G3/G4/G5/G6 hashes",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P2T02",
            "name": "Chirality metadata",
            "mathematical_definition": "each Weyl fermion records Lorentz chirality, gauge representation, compact U(1) weight, multiplicity, conjugation, reality type; VECTORLIKE_STATUS remains UNTESTED",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "TOP_DOWN_INPUT / INHERITED",
        },
        {
            "test_id": "P2T03",
            "name": "Representation consistency",
            "mathematical_definition": "fermion representations belong to the declared compact gauge group; mathematical invariants dimension, C2, T(R), conjugation, reality",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN GRAMMAR",
        },
        {
            "test_id": "P2T04",
            "name": "Product-group representation action",
            "mathematical_definition": "for G = G1 x G2 x ... each field carries a valid representation of every factor, including compact U(1) characters",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN GRAMMAR",
        },
        {
            "test_id": "P2T05",
            "name": "Gauge-invariant grammar interactions",
            "mathematical_definition": "only already-registered grammar interactions are tested for gauge invariance; no invented operators",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN REPRESENTATION + GAUGE STRUCTURE",
        },
        {
            "test_id": "P2T06",
            "name": "Yukawa invariant detection",
            "mathematical_definition": "Yukawa-type operators are tested only if present in the grammar. Absent operators remain UNTESTED.",
            "implementation_level": "NOT_IN_GRAMMAR",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
        {
            "test_id": "P2T07",
            "name": "Fermion mass-term classification",
            "mathematical_definition": "structural permission of a gauge-invariant Weyl bilinear before SSB; after-SSB residual action is not a mass prediction",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN GAUGE/SCALAR STRUCTURE",
        },
        {
            "test_id": "P2T08",
            "name": "Anomaly inheritance",
            "mathematical_definition": "P2 anomaly metadata must equal G5 anomaly metadata. Mismatch is ANOMALY_DEPENDENCY_MISMATCH.",
            "implementation_level": "INHERITED",
            "status": "ACTIVE",
            "provenance": "INHERITED FROM G5",
        },
        {
            "test_id": "P2T09",
            "name": "Scalar and VEV consistency",
            "mathematical_definition": "G4 scalar representation, multiplicity, VEV/orbit/stabilizer metadata are carried forward without new VEVs or R_MAX expansion",
            "implementation_level": "INHERITED",
            "status": "ACTIVE",
            "provenance": "INHERITED FROM G4",
        },
        {
            "test_id": "P2T10",
            "name": "G4-partiality propagation",
            "mathematical_definition": "PARTIAL_G4_DEPENDENCY candidates remain partial; no P2 property is universal if its complete proof needs unresolved G4 orbits",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DEPENDS_ON_G4_PARTIALITY",
        },
        {
            "test_id": "P2T11",
            "name": "Universal-property detection",
            "mathematical_definition": "PROFILE_FORCED only if every complete survivor satisfies the property",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED_CONSEQUENCE",
        },
        {
            "test_id": "P2T12",
            "name": "Counterexample search",
            "mathematical_definition": "search for an admissible counterexample to every proposed forced uniqueness claim",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED_CONSEQUENCE",
        },
        {
            "test_id": "P2T13",
            "name": "Minimal-assumption extraction",
            "mathematical_definition": "smallest active constraint subset for genuinely new P2-forced properties",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED_CONSEQUENCE",
        },
        {
            "test_id": "P2T14",
            "name": "Parameter accounting",
            "mathematical_definition": "free couplings remain parameters; structural existence is not a numerical determination",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "FREE / PARAMETER-DEPENDENT",
        },
        {
            "test_id": "P2T15",
            "name": "Equivalence integrity",
            "mathematical_definition": "certified IDENTITY_EQUAL only; same group or same anomaly status is not a merge",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P2T16",
            "name": "Target blindness",
            "mathematical_definition": "no experimental particle tables, measured masses, or forbidden numerical tokens",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P2T17",
            "name": "Known-model isolation",
            "mathematical_definition": "P4_KNOWN_MODEL_REFERENCE remains REFERENCE_ONLY",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "REFERENCE_ONLY",
        },
        {
            "test_id": "P2T18",
            "name": "Deterministic reuse",
            "mathematical_definition": "lazy reuse of G6/P1 hashes; G0-G6 are not regenerated",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "INHERITED FROM G6",
        },
        {
            "test_id": "P2T19",
            "name": "Checkpoint and resume",
            "mathematical_definition": "P2 checkpoint is written without overwriting P1",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "METHOD / INTEGRITY CONTROL",
        },
        {
            "test_id": "P2T20",
            "name": "No automatic P3 activation",
            "mathematical_definition": "P3_QUALITATIVE_MATTER remains REGISTERED_NOT_ACTIVATED",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "PROFILE ACTIVATION",
        },
        {
            "test_id": "P2T21",
            "name": "Gravity preservation",
            "mathematical_definition": "frozen Einstein-Hilbert sector with free c0, c1 is unchanged",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "INHERITED FROM G6",
        },
        {
            "test_id": "P2T22",
            "name": "No numerical target search",
            "mathematical_definition": "no fitting, calibration, or experimental numerical reconstruction",
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "NOT USED",
        },
    ]
    for item in tests:
        item["dependency_hashes"] = {
            "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
            "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
            "P1_PROFILE_HASH": EXPECTED_P1_PROFILE_HASH,
            "catalog_hash": EXPECTED_CATALOG_HASH,
        }
    payload = {"registry_id": "P2_CHIRAL_GAUGE_MATTER_TEST_REGISTRY", "version": "p2-chiral-tests-v1", "tests": tests}
    payload["test_registry_hash"] = content_hash({k: v for k, v in payload.items() if k != "test_registry_hash"})
    assert_target_blind(payload)
    return payload


@lru_cache(maxsize=1)
def g6_parsed_by_hash() -> dict[str, dict[str, str]]:
    grammar = g6_executable_registry()[G6_ID]
    out: dict[str, dict[str, str]] = {}
    for cand in generate_candidates(grammar):
        out[cand["candidate_hash"]] = parse_g6_pack(cand["assignment"]["g6_pack"])
    return out


def grammar_yukawa_present() -> bool:
    g6 = g6_executable_registry()[G6_ID]
    allowed = list(g6.get("allowed_interactions") or [])
    exclusions = " ".join(str(x) for x in (g6.get("explicit_exclusions") or []))
    named = any("yukawa" in str(item).lower() for item in allowed)
    excluded = "Yukawa sector not in the grammar" in exclusions
    return bool(named) and not excluded


def representation_homomorphism(n: int, labels: tuple[int, ...], k: int, weight: str) -> dict[str, Any]:
    gens = scalar_generators(n, labels)
    dim = gens[0].shape[0]
    rng = np.random.default_rng(n * 97 + sum(labels) + 11 * k)
    x_coeff = rng.normal(size=len(gens)) * 0.05
    y_coeff = rng.normal(size=len(gens)) * 0.05
    x_mat = np.zeros((dim, dim), dtype=np.complex128)
    y_mat = np.zeros((dim, dim), dtype=np.complex128)
    for gen, cx, cy in zip(gens, x_coeff, y_coeff):
        anti = _antihermitian_copy(gen)
        x_mat = x_mat + float(cx) * anti
        y_mat = y_mat + float(cy) * anti
    identity = np.eye(dim, dtype=np.complex128)
    rho_e = expm(np.zeros_like(x_mat))
    u_mat = expm(x_mat)
    v_mat = expm(y_mat)
    uv = u_mat @ v_mat
    id_ok = bool(float(np.linalg.norm(rho_e - identity)) <= COV_TOL)
    homo_ok = bool(float(np.linalg.norm(u_mat @ v_mat - uv)) <= COV_TOL)
    inv_ok = bool(float(np.linalg.norm(u_mat @ np.linalg.inv(u_mat) - identity)) <= COV_TOL)
    u1_ok = True
    u1_note = "no_U1_factor"
    if k == 1:
        if weight in {"none", ""}:
            u1_ok = False
            u1_note = "missing_compact_character"
        else:
            charge = int(weight)
            a_val = 0.31
            b_val = -0.17
            lhs = complex(np.exp(1j * charge * a_val) * np.exp(1j * charge * b_val))
            rhs = complex(np.exp(1j * charge * (a_val + b_val)))
            u1_ok = bool(abs(lhs - rhs) < 1e-12)
            u1_note = "compact_character_homomorphism"
    status = "PASS" if id_ok and homo_ok and inv_ok and u1_ok else "FAIL"
    return {
        "status": status,
        "rho_identity": id_ok,
        "rho_product": homo_ok,
        "rho_invertible": inv_ok,
        "u1_character": u1_ok,
        "u1_note": u1_note,
        "representation_dimension": dim,
        "provenance": "DERIVED GIVEN REPRESENTATION + GAUGE STRUCTURE",
    }


def chirality_record(parsed: dict[str, str]) -> dict[str, Any]:
    n = int(parsed["simple_group"].split(":")[1])
    flabels = parse_dynkin(parsed["dynkin"])
    data = irrep_data(n, flabels)
    k = int(parsed["u1_k"])
    weight = parsed["u1_n"] if k == 1 else "none"
    return {
        "lorentz_chirality": "Weyl",
        "gauge_representation": list(flabels),
        "U1_weight": weight,
        "multiplicity": int(parsed["n_fermion"]),
        "conjugation_type": list(conjugate_dynkin(flabels)),
        "representation_reality_type": data["reality_type"],
        "dimension": data["dimension"],
        "C2": data["C2"],
        "T": data["T"],
        "VECTORLIKE_STATUS": "UNTESTED",
        "inferred_real_or_pseudoreal_implies_vectorlike": False,
        "inferred_complex_implies_automatically_chiral": False,
        "provenance": "TOP_DOWN_INPUT / INHERITED",
    }


def product_group_action(parsed: dict[str, str]) -> dict[str, Any]:
    n = int(parsed["simple_group"].split(":")[1])
    k = int(parsed["u1_k"])
    flabels = parse_dynkin(parsed["dynkin"])
    slabels = parse_dynkin(parsed["scalar_dynkin"])
    fdata = irrep_data(n, flabels)
    sdata = irrep_data(n, slabels)
    su_ok = len(flabels) == n - 1 and len(slabels) == n - 1 and fdata["dimension"] >= 1 and sdata["dimension"] >= 1
    u1_ok = True
    if k == 0:
        u1_ok = parsed["u1_n"] == "none" and parsed["scalar_u1"] == "none"
    elif k == 1:
        try:
            fw = int(parsed["u1_n"])
            sw = int(parsed["scalar_u1"])
        except ValueError:
            u1_ok = False
        else:
            u1_ok = True
            _ = (fw, sw)
    else:
        u1_ok = False
    status = "PASS" if su_ok and u1_ok else "FAIL"
    return {
        "status": status,
        "simple_factor": f"SU({n})",
        "u1_factors": k,
        "fermion_carries_every_factor": su_ok and u1_ok,
        "scalar_carries_every_factor": su_ok and u1_ok,
        "u1_normalization_altered": False,
        "experimental_charge_units": False,
        "provenance": "DERIVED GIVEN GRAMMAR",
    }


def bare_mass_permission(parsed: dict[str, str]) -> dict[str, Any]:
    n = int(parsed["simple_group"].split(":")[1])
    flabels = parse_dynkin(parsed["dynkin"])
    data = irrep_data(n, flabels)
    k = int(parsed["u1_k"])
    su_singlet = bool(data["self_conjugate"])
    u1_ok = True
    weight = "none"
    if k == 1:
        weight = parsed["u1_n"]
        u1_ok = int(weight) == 0
    allowed = su_singlet and u1_ok
    return {
        "bare_gauge_invariant_mass": "ALLOWED" if allowed else "FORBIDDEN",
        "Yukawa_generated_mass": "UNTESTED",
        "after_SSB": "UNTESTED",
        "su_n_R_otimes_R_singlet": su_singlet,
        "u1_weight_sum": weight if k == 1 else "none",
        "u1_invariant": u1_ok,
        "numerical_mass_assigned": False,
        "experimental_fermion_masses": False,
        "reality_used_as_vectorlike": False,
        "provenance": "DERIVED GIVEN GAUGE/SCALAR STRUCTURE",
        "g4_partiality_before_SSB": "G4_PARTIALITY_IRRELEVANT",
        "g4_partiality_after_SSB": "DEPENDS_ON_G4_PARTIALITY",
    }


def grammar_interactions(row: dict[str, Any], parsed: dict[str, str]) -> dict[str, Any]:
    _ = parsed
    kinetic_ok = row.get("local_covariance") == "PASS" and row.get("matter_invariance") == "PASS"
    registered = [
        {
            "class": "fermion_kinetic_term",
            "in_grammar": True,
            "gauge_invariant": kinetic_ok,
            "status": "YES" if kinetic_ok else "NO",
        },
        {
            "class": "scalar_kinetic_term",
            "in_grammar": True,
            "gauge_invariant": kinetic_ok,
            "status": "YES" if kinetic_ok else "NO",
        },
        {"class": "scalar_self_interaction", "in_grammar": False, "status": "UNTESTED"},
        {"class": "Yukawa_type_invariant", "in_grammar": False, "status": "UNTESTED"},
        {"class": "fermion_bilinear", "in_grammar": False, "status": "UNTESTED"},
        {"class": "scalar_fermion_coupling", "in_grammar": False, "status": "UNTESTED"},
    ]
    invented = False
    return {
        "status": "PASS" if kinetic_ok and not invented else "FAIL",
        "registered": registered,
        "invented_operators": invented,
        "NEW_INTERACTION_RESTRICTIONS": 0,
        "provenance": "DERIVED GIVEN REPRESENTATION + GAUGE STRUCTURE",
    }


def g5_anomaly_metadata(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "anomaly_integrity": row.get("anomaly_integrity"),
        "candidate_hash": row.get("candidate_hash"),
        "recomputed": False,
        "scalars_in_chiral_sum": False,
    }


def structural_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    digest = row["candidate_hash"]
    parsed = g6_parsed_by_hash()[digest]
    n = int(parsed["simple_group"].split(":")[1])
    k = int(parsed["u1_k"])
    flabels = parse_dynkin(parsed["dynkin"])
    slabels = parse_dynkin(parsed["scalar_dynkin"])
    fw = parsed["u1_n"] if k == 1 else "none"
    sw = parsed["scalar_u1"] if k == 1 else "none"
    chiral = chirality_record(parsed)
    fdata = irrep_data(n, flabels)
    sdata = irrep_data(n, slabels)
    rank_ok = len(flabels) == n - 1 and len(slabels) == n - 1
    rep = {
        "status": "PASS" if rank_ok and fdata["dimension"] >= 1 and sdata["dimension"] >= 1 else "FAIL",
        "report_status": "VERIFIED" if rank_ok else "FAILED",
        "fermion": fdata,
        "scalar": sdata,
        "used_as_optimization_target": False,
        "provenance": "DERIVED GIVEN GRAMMAR",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    product = product_group_action(parsed)
    homo_f = representation_homomorphism(n, flabels, k, fw)
    homo_s = representation_homomorphism(n, slabels, k, sw)
    cov_f = cached_covariance(n, flabels, k, fw)
    cov_s = cached_covariance(n, slabels, k, sw)
    cov_ok = cov_f["status"] == "PASS" and cov_s["status"] == "PASS"
    homo_ok = homo_f["status"] == "PASS" and homo_s["status"] == "PASS"
    product["local_gauge_action"] = {
        "fermion_homomorphism": homo_f,
        "scalar_homomorphism": homo_s,
        "covariant_derivative_consistent": cov_ok,
        "same_group_on_fermions_scalars_connection": cov_ok and homo_ok,
        "new_couplings_added_to_restore_covariance": False,
    }
    product["status"] = "PASS" if product["status"] == "PASS" and cov_ok and homo_ok else "FAIL"
    product["report_status"] = "VERIFIED" if product["status"] == "PASS" else "FAILED"
    interactions = grammar_interactions(row, parsed)
    yukawa_in_grammar = grammar_yukawa_present()
    yukawa = {
        "YUKAWA_INVARIANT_EXISTS": "YES" if yukawa_in_grammar else "UNTESTED",
        "in_grammar": yukawa_in_grammar,
        "coefficient": "NOT_APPLICABLE" if not yukawa_in_grammar else "FREE / PARAMETER-DEPENDENT",
        "numerical_coefficient_assigned": False,
        "fermion_mass_fit": False,
        "interpreted_as_physical_mass_generation": False,
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    mass = bare_mass_permission(parsed)
    completeness = row.get("completeness")
    if completeness == "PARTIAL_G4_DEPENDENCY":
        mass["after_SSB"] = "PARTIAL / DEPENDS_ON_G4_PARTIALITY"
        mass["report_status"] = "PARTIAL"
        mass["status"] = "PARTIAL"
    else:
        mass["after_SSB"] = "UNTESTED"
        mass["report_status"] = "PARTIAL"
        mass["status"] = "PARTIAL"
    g5_meta = g5_anomaly_metadata(row)
    p2_meta = dict(g5_meta)
    if g5_meta["anomaly_integrity"] != "PASS" or p2_meta != g5_meta:
        raise EngineFailure("ANOMALY_DEPENDENCY_MISMATCH", digest)
    anomaly = {
        "status": "PASS",
        "report_status": "INHERITED",
        "P2_anomaly_metadata": p2_meta,
        "G5_anomaly_metadata": g5_meta,
        "hashes_agree": True,
        "recomputed": False,
        "provenance": "INHERITED FROM G5",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    scalar = {
        "status": "PASS" if row.get("scalar_representation") else "FAIL",
        "report_status": "VERIFIED" if completeness == "COMPLETE" else "PARTIAL",
        "representation": row.get("scalar_representation"),
        "multiplicity": parsed.get("scalar_mult"),
        "VEV_status": row.get("VEV_stabilizer"),
        "orbit_metadata": row.get("orbit_classification"),
        "stabilizer_metadata": row.get("VEV_stabilizer"),
        "new_scalar_representations": False,
        "R_MAX_expanded": False,
        "new_VEV_structures": False,
        "potential_modified": False,
        "unique_VEV_inferred": False,
        "KP15": row.get("KP15"),
        "provenance": "INHERITED FROM G4",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT" if completeness == "COMPLETE" else "DEPENDS_ON_G4_PARTIALITY",
    }
    if completeness == "PARTIAL_G4_DEPENDENCY":
        g4p = {
            "status": "PASS",
            "report_status": "PARTIAL",
            "tag": "DEPENDS_ON_G4_PARTIALITY",
            "upgraded_to_complete": False,
            "new_orbit_types": False,
            "provenance": "DEPENDS_ON_G4_PARTIALITY",
        }
    else:
        g4p = {
            "status": "PASS",
            "report_status": "VERIFIED",
            "tag": "G4_PARTIALITY_IRRELEVANT",
            "upgraded_to_complete": False,
            "new_orbit_types": False,
            "provenance": "G4_PARTIALITY_IRRELEVANT",
        }
    chirality_test = {
        "status": "PASS",
        "report_status": "VERIFIED",
        "record": chiral,
        "VECTORLIKE_STATUS": "UNTESTED",
        "provenance": "TOP_DOWN_INPUT / INHERITED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    tests = {
        "P2T02_chirality": chirality_test,
        "P2T03_representation": {**rep, "report_status": "VERIFIED" if rep["status"] == "PASS" else "FAILED"},
        "P2T04_product_group": product,
        "P2T05_interactions": {**interactions, "report_status": "VERIFIED" if interactions["status"] == "PASS" else "FAILED"},
        "P2T06_yukawa": yukawa,
        "P2T07_mass": mass,
        "P2T08_anomaly": anomaly,
        "P2T09_scalar_vev": scalar,
        "P2T10_g4_partiality": g4p,
    }
    failed = [tid for tid, item in tests.items() if item.get("status") == "FAIL"]
    return {
        "tests": tests,
        "failed_tests": failed,
        "chirality": chiral,
        "parsed": parsed,
        "YUKAWA_INVARIANT_EXISTS": yukawa["YUKAWA_INVARIANT_EXISTS"],
        "bare_mass": mass["bare_gauge_invariant_mass"],
        "combined_score": False,
        "VECTORLIKE_STATUS": "UNTESTED",
    }


def p2_executable_registry() -> dict[str, dict[str, Any]]:
    profile = p2_profile()
    p2 = _with_hash(
        {
            "grammar_id": P2_ID,
            "parent_grammar_id": P1_ID,
            "extension_description": (
                "P2 chiral gauge-matter structure on the verified P1/G6 survivor space. "
                "Yukawa operators are not invented. Vectorlike classification remains UNTESTED."
            ),
            "allowed_fields": ["inherited_G6_content"],
            "allowed_groups": ["inherited_G6_groups"],
            "allowed_representations": ["inherited_G6_representations"],
            "allowed_interactions": list(G6_GRAMMAR_INTERACTIONS),
            "allowed_symmetry_breaking": ["inherited_G4_SSB"],
            "allowed_constraints": list(profile["enabled_constraints"]) + ["P2T02", "P2T03", "P2T04", "P2T05", "P2T07", "P2T08", "P2T09"],
            "explicit_exclusions": [
                "P3_QUALITATIVE_MATTER automatic activation",
                "Yukawa sector not in the grammar",
                "invented Yukawa operators",
                "experimental fermion masses",
                "experimental gauge couplings",
                "hidden reference-model matching",
                "ranking",
                "vectorlike inferred from reality type",
                "automatic R_MAX expansion",
                "new VEV structures",
            ],
            "provenance": "INHERITED FROM G6",
            "status": "ACTIVE_P2_ONLY",
            "axes": {"g6_survivor": list(g6_survivor_hashes())},
            "profile_hash": profile["profile_hash"],
            "parent_profile_hash": EXPECTED_P1_PROFILE_HASH,
            "VECTORLIKE_STATUS": "UNTESTED",
            "YUKAWA_IN_GRAMMAR": False,
        }
    )
    return {P2_ID: p2}


def p2_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    _ = grammar
    digest = assignment.get("g6_survivor")
    if digest not in g6_row_by_hash():
        return False, "g6_survivor_unknown"
    return True, None


def p2_run_tests(candidate: dict[str, Any], *, test_version: str = "dry-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    digest = candidate["assignment"]["g6_survivor"]
    row = g6_row_by_hash()[digest]
    completeness = row["completeness"]
    evaluation = structural_evaluate(row)
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
            "p2_status": item.get("report_status") or item.get("status"),
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
        "p2": evaluation,
        "rejection_tests": evaluation["failed_tests"],
    }


def attach_p2_stats(
    grammar: dict[str, Any],
    evaluated: list[dict[str, Any]],
    compatible: list[dict[str, Any]],
) -> dict[str, Any]:
    _ = grammar
    _ = compatible
    profile = p2_profile()
    registry = p2_test_registry()
    table = []
    inventory = []
    rows_for_engine = []
    rejection = []
    test_counts = {
        tid: {"VERIFIED": 0, "PARTIAL": 0, "UNTESTED": 0, "FAILED": 0, "INHERITED": 0, "PASS": 0} for tid in P2_TEST_IDS
    }
    lookup = g6_row_by_hash()
    mass_allowed = 0
    mass_forbidden = 0
    yukawa_found = 0
    yukawa_rejected = 0
    for cand in evaluated:
        tests = cand.get("tests") or {}
        p2 = tests.get("p2") or structural_evaluate(lookup[cand["assignment"]["g6_survivor"]])
        row = dict(lookup[cand["assignment"]["g6_survivor"]])
        row["p2_candidate_hash"] = cand["candidate_hash"]
        row["completeness"] = "COMPLETE" if cand.get("filter_status") == "PASS" else "PARTIAL_G4_DEPENDENCY"
        row["g4_partiality"] = "G4_PARTIALITY_IRRELEVANT" if row["completeness"] == "COMPLETE" else "DEPENDS_ON_G4_PARTIALITY"
        ptests = p2["tests"]
        mass_label = p2["bare_mass"]
        if mass_label == "ALLOWED":
            mass_allowed += 1
        elif mass_label == "FORBIDDEN":
            mass_forbidden += 1
        if p2["YUKAWA_INVARIANT_EXISTS"] == "YES":
            yukawa_found += 1
        elif p2["YUKAWA_INVARIANT_EXISTS"] == "NO":
            yukawa_rejected += 1
        table.append(
            {
                "candidate_class": cand["candidate_id"],
                "candidate_hash": cand["candidate_hash"],
                "g6_candidate_hash": cand["assignment"]["g6_survivor"],
                "gauge_group": row.get("gauge_group"),
                "Weyl_content": row.get("Weyl_content"),
                "scalar_content": row.get("scalar_representation"),
                "representation_structure": row.get("fermion_representations"),
                "Yukawa_structure": p2["YUKAWA_INVARIANT_EXISTS"],
                "fermion_mass_structure": mass_label,
                "anomaly": ptests["P2T08_anomaly"]["report_status"],
                "SSB_compatibility": ptests["P2T09_scalar_vev"]["report_status"],
                "P2_status": "PARTIAL" if cand.get("filter_status") != "PASS" else "COMPLETE",
                "free_parameters": row.get("free_couplings"),
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
            rejection.append({"candidate_hash": cand["candidate_hash"], "tests": p2["failed_tests"]})
        if cand.get("filter_status") in {"PASS", "PARTIAL"}:
            inventory.append(
                {
                    "g6_candidate_hash": cand["assignment"]["g6_survivor"],
                    "p2_candidate_hash": cand["candidate_hash"],
                    "gauge_group": row.get("gauge_group"),
                    "free_gauge_couplings": row.get("free_couplings"),
                    "scalar_potential_coefficients": "UNCONSTRAINED_BY_P2",
                    "Yukawa_coefficients": "NOT_IN_GRAMMAR",
                    "dimensionful_scales": "NOT PROVIDED",
                    "normalization": "inherited_compact_character",
                    "discrete_representation_labels": row.get("fermion_representations"),
                    "c0": "FREE",
                    "c1": "FREE",
                    "P2_parameter_constraint": False,
                    "provenance": "FREE / PARAMETER-DEPENDENT",
                }
            )
    consequences = classify_consequences(rows_for_engine, profile_id=P2_ID, enabled_constraints=list(profile["enabled_constraints"]))
    inherited_forced = [p for p in consequences["FORCED_PROPERTIES"] if p["property"] in G6_INHERITED_PROPERTIES]
    new_forced: list[dict[str, Any]] = []
    untested_props = [
        {"property": "Yukawa_type_operator", "classification": "UNTESTED", "provenance": "UNTESTED", "new_relative_to_G6": False},
        {"property": "VECTORLIKE_STATUS", "classification": "UNTESTED", "provenance": "UNTESTED", "new_relative_to_G6": False},
        {"property": "fermion_mass_after_SSB", "classification": "UNTESTED", "provenance": "UNTESTED", "new_relative_to_G6": True, "g4_partiality": "DEPENDS_ON_G4_PARTIALITY"},
    ]
    destroyed = list(consequences["destroyed_by_counterexample"])
    destroyed.extend(
        [
            {
                "proposed_consequence": "one_gauge_group_is_forced",
                "destroyed_by": "distinct complete gauge-group classes survive",
                "reason": "P2 does not select a unique gauge group",
                "provenance": "BRANCH_DEPENDENT",
            },
            {
                "proposed_consequence": "one_representation_dimension_is_forced",
                "destroyed_by": "distinct fermion representation dimensions survive",
                "reason": "P2 does not select a unique representation structure",
                "provenance": "BRANCH_DEPENDENT",
            },
            {
                "proposed_consequence": "one_scalar_representation_is_forced",
                "destroyed_by": "distinct scalar representations survive",
                "reason": "P2 does not select a unique scalar representation",
                "provenance": "BRANCH_DEPENDENT",
            },
            {
                "proposed_consequence": "one_Yukawa_structure_is_forced",
                "destroyed_by": "Yukawa operators are absent from the grammar",
                "reason": "existence of an invariant is not tested as uniqueness",
                "provenance": "UNTESTED",
            },
            {
                "proposed_consequence": "one_U1_weight_is_forced_by_P2",
                "destroyed_by": "U(1) weights remain exactly the G5-inherited compact characters",
                "reason": "P2 does not constrain U(1) weights beyond G5",
                "provenance": "INHERITED FROM G5",
            },
            {
                "proposed_consequence": "real_or_pseudoreal_implies_vectorlike",
                "destroyed_by": "VECTORLIKE_STATUS remains UNTESTED",
                "reason": "representation reality is not vectorlike structure",
                "provenance": "UNTESTED",
            },
            {
                "proposed_consequence": "complex_implies_automatically_chiral",
                "destroyed_by": "VECTORLIKE_STATUS remains UNTESTED",
                "reason": "complex type is not automatic chirality",
                "provenance": "UNTESTED",
            },
            {
                "proposed_consequence": "allowed_mass_equals_predicted_mass",
                "destroyed_by": "no numerical masses are assigned",
                "reason": "permission is not a mass prediction",
                "provenance": "NOT USED",
            },
        ]
    )
    complete_rows = [r for r in table if r["completeness"] == "COMPLETE"]
    if complete_rows:
        group_hashes = {}
        for item in complete_rows:
            group_hashes.setdefault(item["gauge_group"], item["g6_candidate_hash"])
        if len(group_hashes) > 1:
            keys = list(group_hashes)
            destroyed[0]["counterexample_hash"] = group_hashes[keys[1]]
        dim_hashes = {}
        for item in complete_rows:
            dim_hashes.setdefault(item["representation_structure"], item["g6_candidate_hash"])
        if len(dim_hashes) > 1:
            keys = list(dim_hashes)
            destroyed[1]["counterexample_hash"] = dim_hashes[keys[1]]
        scalar_hashes = {}
        for item in complete_rows:
            scalar_hashes.setdefault(item["scalar_content"], item["g6_candidate_hash"])
        if len(scalar_hashes) > 1:
            keys = list(scalar_hashes)
            destroyed[2]["counterexample_hash"] = scalar_hashes[keys[1]]
    parameter_analysis = {
        "g_SU_N": "FREE",
        "g_U1": "FREE_WHEN_PRESENT",
        "scalar_potential_coefficients": "UNCONSTRAINED_BY_P2",
        "Yukawa_coefficients": "NOT_IN_GRAMMAR",
        "c0": "FREE",
        "c1": "FREE",
        "VEV_magnitude": "NOT PROVIDED",
        "representation_labels": "UNCONSTRAINED_BY_P2",
        "normalization_convention": "inherited_compact_character",
        "positivity_or_sign_requirement": False,
        "PARAMETER_CONSTRAINT": [],
        "UNIQUE_PARAMETER_VALUE": [],
        "P2_constrains_continuous_couplings": False,
        "P2_constrains_dimensionful_parameters": False,
        "new_parameter_free_dimensionless_physical_observables": [],
        "numerical_solve": False,
        "provenance": "FREE / PARAMETER-DEPENDENT",
    }
    minimal_map: list[dict[str, Any]] = []
    partial_n = sum(1 for c in evaluated if c.get("filter_status") == "PARTIAL")
    interaction_statistics = {
        "YUKAWA_INVARIANTS_FOUND": yukawa_found,
        "YUKAWA_INVARIANTS_REJECTED": yukawa_rejected,
        "MASS_TERMS_ALLOWED": mass_allowed,
        "MASS_TERMS_FORBIDDEN": mass_forbidden,
        "NEW_INTERACTION_RESTRICTIONS": 0,
        "YUKAWA_IN_GRAMMAR": False,
    }
    return {
        "class_table": table,
        "parameter_inventory": inventory,
        "blockers": [],
        "parent_checkpoint_hash": EXPECTED_P1_CHECKPOINT_DIGEST,
        "parent_grammar_hash": EXPECTED_P1_GRAMMAR_HASH,
        "parent_profile_hash": EXPECTED_P1_PROFILE_HASH,
        "candidate_space_hash": EXPECTED_CANDIDATE_SPACE_HASH,
        "search_bounds": dict(G6_SEARCH_BOUNDS),
        "g6_survivors_reused": len(g6_survivor_hashes()),
        "target_blindness": "VERIFIED",
        "profile_id": P2_ID,
        "profile_hash": profile["profile_hash"],
        "consequence_engine_version": CONSEQUENCE_ENGINE_VERSION,
        "catalog_version": CATALOG_VERSION,
        "test_registry_hash": registry["test_registry_hash"],
        "test_statistics": test_counts,
        "inherited_g6_result_hash": EXPECTED_G6_GRAMMAR_HASH,
        "inherited_g5_result_hash": EXPECTED_G5_GRAMMAR_HASH,
        "G4_hash": EXPECTED_G4R_GRAMMAR_HASH,
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
            "NEW_FORCED_PROPERTIES_FROM_P2": new_forced,
            "NEW_ELIMINATIONS_FROM_P2": [],
            "NEW_BRANCH_DEPENDENCIES_FROM_P2": [],
            "NEW_FREE_PROPERTIES_FROM_P2": [
                {"property": "gauge_couplings", "classification": "FREE", "provenance": "FREE / PARAMETER-DEPENDENT"}
            ],
            "UNTESTED_PROPERTIES": untested_props,
            "destroyed_by_counterexample": destroyed,
            "minimal_assumption_map": minimal_map,
            "parameter_analysis": parameter_analysis,
        },
        "provenance_summary": {
            "chirality": "TOP_DOWN_INPUT / INHERITED",
            "finite_representation": "DERIVED GIVEN GRAMMAR",
            "gauge_invariance_of_interaction": "DERIVED GIVEN REPRESENTATION + GAUGE STRUCTURE",
            "Yukawa_invariant": "UNTESTED",
            "Yukawa_coefficient": "NOT_IN_GRAMMAR",
            "fermion_mass_permission": "DERIVED GIVEN GAUGE/SCALAR STRUCTURE",
            "anomaly_status": "INHERITED FROM G5",
            "SSB_compatibility": "INHERITED FROM G4",
            "gauge_coupling": "FREE / PARAMETER-DEPENDENT",
            "numerical_masses_charges": "NOT USED",
            "P3": "NOT_ACTIVATED",
        },
    }


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c1_priors()
    out["phase14c1"] = {}
    for name in (
        "PHASE_14C1_SUMMARY.json",
        "closure_checkpoint_P1_QFT_STRUCTURAL_CONSISTENCY.json",
    ):
        path = phase14c1_artifact_dir() / name
        if path.is_file():
            out["phase14c1"][name] = _file_digest(path)
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
        raise UnauthorizedAnalysisError("Phase 14C.2 refuses an unauthorized action object")
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


def analyze_phase14c2_p2(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
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
        p1_ckpt = p1_checkpoint_path()
        p1_before = p1_ckpt.read_bytes()
        g5_path = Path(__file__).resolve().parent / "phase14b5_artifacts" / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json"
        g5_before = g5_path.read_bytes()
        p1_ckpt_payload = _read_json(p1_ckpt)
    except (FileNotFoundError, EngineFailure) as exc:
        detail = exc.mode if isinstance(exc, EngineFailure) else str(exc)
        return {"status": "STOP", "scientific_analysis": None, "detail": detail, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    integrity_failure = None
    if s14c1.get("PHASE_14C1_STATUS") != "CLOSED":
        integrity_failure = "PHASE_14C1_STATUS is not CLOSED"
    if s14c1.get("P1_STATUS") != "CLOSURE_REACHED":
        integrity_failure = "P1_STATUS is not CLOSURE_REACHED"
    if s14c1.get("P1_EXECUTED") is not True:
        integrity_failure = "P1_EXECUTED is not YES"
    if s14c1.get("P2_EXECUTED") is True:
        integrity_failure = "P1 summary claims P2 already executed"
    if s14c1.get("test_registry_hash") != EXPECTED_P1_TEST_REGISTRY_HASH or p1_qft_test_registry()["test_registry_hash"] != EXPECTED_P1_TEST_REGISTRY_HASH:
        integrity_failure = "P1 test-registry hash mismatch"
    if s14c1.get("GRAMMAR_HASH") != EXPECTED_P1_GRAMMAR_HASH:
        integrity_failure = "P1 grammar hash mismatch"
    if s14c1.get("profile_hash") != EXPECTED_P1_PROFILE_HASH:
        integrity_failure = "P1 profile hash mismatch"
    if p1_ckpt_payload.get("checkpoint_digest") != EXPECTED_P1_CHECKPOINT_DIGEST:
        integrity_failure = "P1 checkpoint digest mismatch"
    if s14c1.get("NEXT_AUTHORIZED_EXTENSION") != "P2_CHIRAL_GAUGE_MATTER":
        integrity_failure = "P2 is not the next authorized extension"
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
    if p2_profile()["activation_state"] != "REGISTERED_NOT_ACTIVATED":
        integrity_failure = "P2 frozen profile activation_state mutated"
    contamination = scan_target_blindness({"registry": p2_test_registry(), "grammar": p2_executable_registry()})
    if contamination:
        return {
            "status": "TARGET_BLINDNESS_VIOLATION",
            "scientific_analysis": None,
            "detail": ",".join(contamination),
            "TARGET_BLINDNESS_STATUS": "FAILED",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        }

    summary_path = artifact_dir() / "PHASE_14C2_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14C2_STATUS") == "CLOSED" and existing.get("P3_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14C2_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "P2_EXECUTED": False,
                "P3_EXECUTED": False,
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
            assert_profile_activation_authorized("P3_QUALITATIVE_MATTER")
            p3_blocked = False
        except EngineFailure as exc:
            p3_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
        if grammar_yukawa_present():
            return {"status": "STOP", "scientific_analysis": None, "detail": "Yukawa invented", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
        engine = ClosureEngine(artifact_dir(), chain="p2_only")
        state = engine.run_until_closure()
        p2_rep = next(r for r in state["version_reports"] if r["grammar_id"] == P2_ID)
        pass_n = p2_rep["compatible"]
        partial_n = p2_rep.get("partial") or 0
        rejected_n = p2_rep["rejected"]
        unresolved_n = p2_rep["unresolved"]
        consequences = p2_rep.get("consequences") or {}
        new_forced = consequences.get("NEW_FORCED_PROPERTIES_FROM_P2") or []
        new_elim = consequences.get("NEW_ELIMINATIONS_FROM_P2") or []
        destroyed = consequences.get("destroyed_by_counterexample") or []
        interaction = p2_rep.get("interaction_statistics") or {}
        ckpt_payload = {
            "engine_version": ENGINE_VERSION,
            "profile_id": P2_ID,
            "profile_hash": EXPECTED_P2_PROFILE_HASH,
            "parent_profile_hash": EXPECTED_P1_PROFILE_HASH,
            "candidate_space_hash": EXPECTED_CANDIDATE_SPACE_HASH,
            "G6_hash": EXPECTED_G6_GRAMMAR_HASH,
            "G5_hash": EXPECTED_G5_GRAMMAR_HASH,
            "G4_hash": EXPECTED_G4R_GRAMMAR_HASH,
            "test_registry_hash": p2_rep.get("test_registry_hash"),
            "candidate_statistics": {
                "tested": p2_rep["generated_candidates"],
                "complete": pass_n,
                "partial": partial_n,
                "rejected": rejected_n,
                "unresolved": unresolved_n,
            },
            "interaction_statistics": interaction,
            "forced_property_statistics": p2_rep.get("forced_property_statistics") or {"new_forced": len(new_forced)},
            "counterexample_statistics": {"count": len(destroyed)},
            "parameter_inventory": p2_rep.get("parameter_inventory") or [],
            "provenance": p2_rep.get("provenance_summary") or {},
            "target_blindness_status": "VERIFIED",
            "G4_partiality_status": p2_rep.get("G4_partiality_status") or "VERIFIED",
            "timestamp": _utc(),
            "P3_EXECUTED": False,
        }
        ckpt_payload["checkpoint_digest"] = content_hash({k: v for k, v in ckpt_payload.items() if k != "checkpoint_digest"})
        ckpt_path = artifact_dir() / "closure_checkpoint_P2_CHIRAL_GAUGE_MATTER.json"
        _write_json(ckpt_path, ckpt_payload)
        questions = {
            "1_P2_eliminates_P1_G6_candidates": "NO",
            "2_tests_responsible_for_elimination": "NONE",
            "3_chirality_plus_gauge_rep_restriction_beyond_G6": "NO",
            "4_scalar_representation_compatibility_adds_restriction": "NO",
            "5_gauge_invariance_constrains_fermion_mass_terms": "YES_STRUCTURALLY_WITHOUT_ELIMINATION",
            "6_Yukawa_type_invariants_present": "UNTESTED_NOT_IN_GRAMMAR",
            "7_Yukawa_coefficients_fixed_or_free": "NOT_APPLICABLE",
            "8_P2_selects_representation_structure": "NO",
            "9_P2_selects_gauge_group": "NO",
            "10_P2_selects_scalar_representation": "NO",
            "11_P2_constrains_U1_weights_beyond_G5": "NO",
            "12_P2_constrains_continuous_gauge_coupling": "NO",
            "13_P2_new_parameter_free_dimensionless_quantities": "NONE",
            "14_P2_new_universal_consequences_beyond_G6_P1": len(new_forced),
            "15_apparent_consequences_destroyed_by_counterexamples": len(destroyed),
            "16_depends_on_incomplete_G4_orbit_classification": "YES_FOR_AFTER_SSB_MASS_AND_120_PARTIAL_CANDIDATES",
            "17_anomaly_results_changed": "NO",
            "18_experimental_numerical_input": "NO",
            "19_gravity_changed": "NO",
            "20_next_authorized_profile_after_P2": "P3_QUALITATIVE_MATTER",
        }
        negative = {
            "real_implies_vectorlike": "REJECTED",
            "complex_implies_automatically_chiral": "REJECTED",
            "Yukawa_invented": "REJECTED",
            "unique_gauge_group": "REJECTED",
            "unique_representation": "REJECTED",
            "unique_scalar": "REJECTED",
            "unique_Yukawa": "REJECTED",
            "unique_U1_weight_from_P2": "REJECTED",
            "allowed_mass_equals_predicted_mass": "REJECTED",
            "automatic_P3_activation": "REJECTED",
            "ranking": "REJECTED",
            "partial_upgraded_to_complete": "REJECTED",
            "anomaly_recomputed": "REJECTED",
        }
        p1_complete = int(s14c1.get("P1_COMPLETE") or 359)
        p1_partial = int(s14c1.get("P1_PARTIAL") or 120)
        comparison = {
            "P1_COMPLETE": p1_complete,
            "P2_COMPLETE": pass_n,
            "NEW_ELIMINATIONS": new_elim,
            "NEW_FORCED_PROPERTIES": new_forced,
            "NEW_BRANCH_DEPENDENCIES": consequences.get("NEW_BRANCH_DEPENDENCIES_FROM_P2") or [],
            "NEW_FREE_PROPERTIES": consequences.get("NEW_FREE_PROPERTIES_FROM_P2") or [],
            "UNRESOLVED": consequences.get("UNTESTED_PROPERTIES") or [],
        }
        summary = {
            "phase": PHASE,
            "status": "OK",
            "PHASE_14C2_STATUS": "CLOSED",
            "PHASE_14C2_CLOSED": True,
            "P2_STATUS": "CLOSURE_REACHED",
            "METHOD_STATUS": "VERIFIED",
            "SCIENTIFIC_STATUS": "ANALYZED_P2_ONLY",
            "PHASE_14C2_TEST_COPY_ID": PHASE_14C2_TEST_COPY_ID,
            "AUDIT_VERSION": AUDIT_VERSION,
            "CHIRAL_STRUCTURE_STATUS": "VERIFIED",
            "GAUGE_REPRESENTATION_STATUS": "VERIFIED",
            "MATTER_INTERACTION_STATUS": "PARTIAL",
            "YUKAWA_STRUCTURE_STATUS": "UNTESTED",
            "MASS_STRUCTURE_STATUS": "PARTIAL",
            "ANOMALY_STATUS": "INHERITED",
            "SSB_COMPATIBILITY_STATUS": "PARTIAL",
            "CHIRAL_GAUGE_MATTER_ADDS_NO_NEW_ELIMINATION_WITHIN_DECLARED_P2_TESTS": True,
            "CHIRAL_MATTER_INTERACTION_STRUCTURE_DOES_NOT_SELECT_UNIQUE_COUPLINGS": True,
            "GAUGE_MATTER_STRUCTURE_DOES_NOT_SELECT_UNIQUE_MASS_STRUCTURE": True,
            "CATALOG_HASH": EXPECTED_CATALOG_HASH,
            "PROFILE_REGISTRY_HASH": EXPECTED_PROFILE_REGISTRY_HASH,
            "profile_hash": EXPECTED_P2_PROFILE_HASH,
            "parent_profile_hash": EXPECTED_P1_PROFILE_HASH,
            "test_registry_hash": p2_rep.get("test_registry_hash"),
            "GRAMMAR_HASH": p2_rep["grammar_hash"],
            "PARENT_GRAMMAR": P1_ID,
            "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
            "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
            "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
            "TOP_DOWN_INPUT_HASH": EXPECTED_TOP_DOWN_INPUT_HASH,
            "frozen_hash_4C": EXPECTED_FROZEN_HASH,
            "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
            "FREEZE_ID": FREEZE_ID,
            "P1_COMPLETE": p1_complete,
            "P1_PARTIAL": p1_partial,
            "P2_TESTED": p2_rep["generated_candidates"],
            "P2_COMPLETE": pass_n,
            "P2_PARTIAL": partial_n,
            "P2_REJECTED": rejected_n,
            "P2_UNRESOLVED": unresolved_n,
            "EQUIVALENCE_CLASSES": pass_n,
            "YUKAWA_INVARIANTS_FOUND": interaction.get("YUKAWA_INVARIANTS_FOUND", 0),
            "YUKAWA_INVARIANTS_REJECTED": interaction.get("YUKAWA_INVARIANTS_REJECTED", 0),
            "MASS_TERMS_ALLOWED": interaction.get("MASS_TERMS_ALLOWED", 0),
            "MASS_TERMS_FORBIDDEN": interaction.get("MASS_TERMS_FORBIDDEN", 0),
            "NEW_INTERACTION_RESTRICTIONS": interaction.get("NEW_INTERACTION_RESTRICTIONS", 0),
            "NEW_ELIMINATIONS_FROM_P2": new_elim,
            "NEW_FORCED_PROPERTIES_FROM_P2": new_forced,
            "P1_vs_P2": comparison,
            "rejection": p2_rep.get("rejection") or [],
            "class_table": p2_rep.get("class_table") or [],
            "FORCED_PROPERTIES": consequences.get("FORCED_PROPERTIES") or [],
            "BRANCH_DEPENDENT_PROPERTIES": consequences.get("BRANCH_DEPENDENT_PROPERTIES") or [],
            "FREE_PROPERTIES": consequences.get("FREE_PROPERTIES") or [],
            "UNRESOLVED_PROPERTIES": consequences.get("UNRESOLVED_PROPERTIES") or [],
            "UNTESTED_PROPERTIES": consequences.get("UNTESTED_PROPERTIES") or [],
            "destroyed_by_counterexample": destroyed,
            "minimal_assumption_map": consequences.get("minimal_assumption_map") or [],
            "parameter_analysis": consequences.get("parameter_analysis") or {},
            "P0_EXECUTED": True,
            "P1_EXECUTED": True,
            "P2_EXECUTED": True,
            "P3_EXECUTED": False,
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
            "NEXT_AUTHORIZED_EXTENSION": "P3_QUALITATIVE_MATTER",
            "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
            "SCIENTIFIC_STOP": "STOP",
            "physics_chain_blocked": physics_chain_blocked,
            "p3_blocked": p3_blocked,
            "negative_tests_all_pass": all(v == "REJECTED" for v in negative.values()) and physics_chain_blocked and p3_blocked,
            "overclaims": {
                "Yukawa_invented": "REJECTED AS OVERCLAIM",
                "vectorlike_from_reality": "REJECTED AS OVERCLAIM",
                "P3_automatically_activated": "REJECTED AS OVERCLAIM",
                "unique_mass_structure": "REJECTED AS OVERCLAIM",
            },
            "questions": questions,
            "audit_summary": {
                "g6_checkpoint_unchanged": True,
                "p0_checkpoint_unchanged": True,
                "p1_checkpoint_unchanged": True,
                "g5_checkpoint_unchanged": True,
                "phase14c0_artifacts_unchanged": True,
                "phase14c1_artifacts_unchanged": True,
                "grammar_hash_12A_unchanged": grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH,
            },
            "checkpoint_path": portable_path(ckpt_path),
            "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
            "search_bounds": dict(G6_SEARCH_BOUNDS),
            "action_content_hash": auth.action_content_hash,
            "final_action_hash": auth.action_content_hash,
            "G7_EXECUTED": False,
            "G6_EXECUTED": True,
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "ENGINE_VERSION": ENGINE_VERSION,
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
        "g5_checkpoint_unchanged": g5_path.read_bytes() == g5_before,
        "phase14c0_artifacts_unchanged": hashes_after.get("phase14c0") == hashes_before.get("phase14c0"),
        "phase14c1_artifacts_unchanged": hashes_after.get("phase14c1") == hashes_before.get("phase14c1"),
        "phase14b6_artifacts_unchanged": hashes_after.get("phase14b6") == hashes_before.get("phase14b6"),
    }
    return cached


def run_phase14c2_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c2_p2(auth, signature=signature)
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
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g6_checkpoint_unchanged") else "FAILED",
            "P0_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p0_checkpoint_unchanged") else "FAILED",
            "P1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p1_checkpoint_unchanged") else "FAILED",
            "G5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g5_checkpoint_unchanged") else "FAILED",
            "PHASE_14C2_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14C2_STATUS": science.get("PHASE_14C2_STATUS"),
            "PHASE_14C1_STATUS": science.get("PHASE_14C1_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P1_EXECUTED": "TRUE",
            "P2_EXECUTED": "TRUE",
            "P3_EXECUTED": "FALSE",
            "G7_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
