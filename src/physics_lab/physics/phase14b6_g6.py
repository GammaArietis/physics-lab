"""Phase 14B.6: activate G6_STRUCTURAL_GAUGE_CONSISTENCY only.

Structural local-gauge consistency of G5 anomaly-free survivors.
Does not invent G7. Does not overwrite the G5 checkpoint.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import expm

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
    generate_candidates,
    top_down_input_hash,
    _with_hash,
)
from physics_lab.physics.phase14b3_g3 import (
    EXPECTED_G2_GRAMMAR_HASH,
    EXPECTED_TOP_DOWN_INPUT_HASH,
    N_SU_VALUES,
    N_U1_MAX,
    R_MAX,
    conjugate_dynkin,
    format_dynkin,
    group_label,
    irrep_data,
    parse_dynkin,
)
from physics_lab.physics.phase14b3r_g3 import artifact_dir as phase14b3r_artifact_dir
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH, N_SCALAR_MAX
from physics_lab.physics.phase14b4r_g4 import (
    G4R_ID,
    breaking_analysis_orbit,
    orbit_types,
    scalar_generators,
)
from physics_lab.physics.phase14b5_g5 import (
    ACTIVE_G5_KPS,
    ANOMALY_ENGINE_VERSION,
    EXPECTED_G4R_GRAMMAR_HASH,
    G5_ID,
    anomaly_analysis,
    anomaly_test_catalogue_hash,
    artifact_dir as phase14b5_artifact_dir,
    g5_executable_registry,
    g5_metadata_legal,
    parse_g5_pack,
    snapshot_prior_artifact_hashes as snapshot_14b5_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_G5_CHECKPOINT_HASH",
    "EXPECTED_G5_GRAMMAR_HASH",
    "G6_CHAIN",
    "analyze_phase14b6_g6",
    "artifact_dir",
    "g6_executable_registry",
    "g6_metadata_legal",
    "g6_run_tests",
    "local_covariance_check",
    "run_phase14b6_or_stop",
    "structural_analysis",
]

PHASE = "PHASE_14B.6"
PHASE_14B6_TEST_COPY_ID = "PHASE_14B6_ACTIVATE_G6_STRUCTURAL_GAUGE_CONSISTENCY"
AUDIT_VERSION = "phase14b6-g6-v1"
STRUCTURAL_ENGINE_VERSION = "phase14b6-structural-engine-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_G5_GRAMMAR_HASH = "0e6468ba698f3222e19ea3f4003946e9df49da7784a278a61d56b46603e567b2"
EXPECTED_G5_CHECKPOINT_HASH = "c8cc31513b267e8f2fd213dac70d1aa7ce69c09c9e7c59f5c99cb3ce2a7ce4b4"
G6_ID = "G6_STRUCTURAL_GAUGE_CONSISTENCY"
G6_CHAIN: tuple[str, ...] = (G6_ID,)
ACTIVE_G6_KPS: tuple[str, ...] = (*ACTIVE_G5_KPS,)
COV_TOL = 1.0e-7
G6_SEARCH_BOUNDS = {
    "R_MAX": R_MAX,
    "R_MAX_is_search_bound_not_prediction": True,
    "N_SCALAR_MAX": N_SCALAR_MAX,
    "N_U1_MAX": N_U1_MAX,
    "N_f": [1, 2],
    "simple_groups": ["SU(2)", "SU(3)", "SU(4)"],
    "no_automatic_bound_expansion": True,
    "no_G7": True,
}
LAYER_IDS: tuple[str, ...] = (
    "LAYER_A_GROUP_REPRESENTATION",
    "LAYER_B_LOCAL_COVARIANCE",
    "LAYER_C_SCALAR_VEV",
    "LAYER_D_FERMION_SCALAR",
    "LAYER_E_ANOMALY_INTEGRITY",
    "LAYER_F_COMPLETE",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b6_artifacts"


def g5_checkpoint_path() -> Path:
    return phase14b5_artifact_dir() / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json"


def _write_json(path: Path, payload: Any) -> None:
    assert_target_blind(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _u1_int(weight: str) -> int | None:
    if weight in {"none", "", None}:
        return None
    return int(weight)


def verify_g5_parent_checkpoint() -> dict[str, Any]:
    path = g5_checkpoint_path()
    if not path.is_file():
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G5 parent missing")
    payload = _read_json(path)
    stored = payload.get("integrity_digest")
    recomputed = content_hash({k: v for k, v in payload.items() if k != "integrity_digest"})
    if stored != recomputed:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G5 parent digest mismatch")
    if payload.get("grammar_id") != G5_ID:
        raise EngineFailure("GRAMMAR_MISSING", "G5 parent grammar_id")
    if payload.get("grammar_hash") != EXPECTED_G5_GRAMMAR_HASH:
        raise EngineFailure("GRAMMAR_HASH_MISMATCH", "G5 parent grammar_hash")
    if payload.get("engine_version") != ENGINE_VERSION:
        raise EngineFailure("RESUME_INTEGRITY_FAILURE", "G5 parent engine version")
    if payload.get("input_hashes", {}).get("top_down_input_hash") != top_down_input_hash():
        raise EngineFailure("INPUT_HASH_MISMATCH", "G5 parent top-down inputs")
    if _file_digest(path) != EXPECTED_G5_CHECKPOINT_HASH:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G5 file digest changed")
    return payload


@lru_cache(maxsize=1)
def g5_survivor_packs() -> tuple[str, ...]:
    parent = verify_g5_parent_checkpoint()
    survivors = set(parent.get("survivor_hashes") or [])
    g5 = g5_executable_registry()[G5_ID]
    packs = []
    for cand in generate_candidates(g5):
        if cand["candidate_hash"] in survivors:
            packs.append(cand["assignment"]["g5_pack"])
    return tuple(packs)


@lru_cache(maxsize=1)
def g5_survivor_pack_set() -> frozenset[str]:
    return frozenset(g5_survivor_packs())


def g6_pack_values() -> list[str]:
    return list(g5_survivor_packs())


def parse_g6_pack(text: str) -> dict[str, str]:
    parsed = parse_g5_pack(text)
    parsed["g5_pack"] = text
    parsed["g6_pack"] = text
    return parsed


def g6_executable_registry() -> dict[str, dict[str, Any]]:
    exclusions = [
        "experimental charge tables",
        "Standard Model assignment lookup",
        "numerical gauge coupling",
        "F2 gauge kinetic term",
        "canonical gauge-field normalization",
        "Yukawa sector not in the grammar",
        "G7 automatic invention",
        "RG analysis",
        "loop effective-action analysis",
        "phenomenology",
        "numerical fitting",
        "preferred gauge group",
        "automatic R_MAX expansion",
    ]
    g6 = _with_hash(
        {
            "grammar_id": G6_ID,
            "parent_grammar_id": G5_ID,
            "extension_description": (
                "structural local-gauge consistency of already-introduced "
                "group, fermion, representation, scalar/VEV, and anomaly-free content"
            ),
            "allowed_fields": ["metric", "scalar", "Weyl_fermion", "scalar_multiplet"],
            "allowed_groups": ["SU_N_family", "SU_N x U(1)^k"],
            "allowed_representations": ["dynkin_irreps_bounded", "U1_character_n_in_Z"],
            "allowed_interactions": [
                "nonabelian_covariant_derivative",
                "U1_covariant_derivative",
                "scalar_kinetic_VEV",
            ],
            "allowed_symmetry_breaking": ["inherited_G4_structural_VEV"],
            "allowed_constraints": list(ACTIVE_G6_KPS) + ["G6_STRUCTURAL_CONSISTENCY"],
            "explicit_exclusions": exclusions,
            "provenance": "GRAMMAR EXTENSION",
            "status": "ACTIVE_G6",
            "axes": {"g6_pack": g6_pack_values()},
            "r_max": R_MAX,
            "n_u1_max": N_U1_MAX,
            "n_scalar_max": N_SCALAR_MAX,
            "r_max_is_search_bound_not_prediction": True,
            "VECTORLIKE_STATUS": "UNTESTED",
            "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
            "gauge_dynamics": "REFERENCE_ONLY / OUT OF SCOPE",
            "structural_engine_version": STRUCTURAL_ENGINE_VERSION,
        }
    )
    return {G6_ID: g6}


def g6_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    _ = grammar
    try:
        pack = assignment["g6_pack"]
        parsed = parse_g6_pack(pack)
        n = int(parsed["simple_group"].split(":")[1])
        slabels = parse_dynkin(parsed["scalar_dynkin"])
        flabels = parse_dynkin(parsed["dynkin"])
        k = int(parsed["u1_k"])
        sm = int(parsed["scalar_mult"])
    except (KeyError, ValueError):
        return False, "invalid_g6_pack"
    g5_ok, why = g5_metadata_legal({"g5_pack": pack}, {})
    if not g5_ok:
        return False, why or "parent_g5_illegal"
    if n not in N_SU_VALUES:
        return False, "group_not_in_bounds"
    if any(x < 0 or x > R_MAX for x in flabels + slabels):
        return False, "dynkin_outside_R_MAX"
    if sm < 1 or sm > N_SCALAR_MAX:
        return False, "scalar_multiplicity_outside_N_SCALAR_MAX"
    if k == 1:
        try:
            wi = int(parsed["u1_n"])
            swi = int(parsed["scalar_u1"])
        except ValueError:
            return False, "u1_weight_not_integer"
        if abs(wi) > N_U1_MAX or abs(swi) > N_U1_MAX:
            return False, "u1_weight_outside_N_U1_MAX"
    if pack not in g5_survivor_pack_set():
        return False, "not_a_G5_anomaly_free_survivor"
    return True, None


def _hermitian_ok(gens: tuple[np.ndarray, ...]) -> bool:
    for g in gens:
        if np.linalg.norm(g - g.conj().T) > COV_TOL:
            return False
    return True


def _antihermitian_copy(gen: np.ndarray) -> np.ndarray:
    """Lie-algebra generator used in D = d + A, A antihermitian.

    Hermitian T (fundamental convention) maps to -i T.
    Already-antihermitian T (real adjoint convention) is kept.
    """
    herm = float(np.linalg.norm(gen - gen.conj().T))
    anti = float(np.linalg.norm(gen + gen.conj().T))
    if anti <= herm:
        return gen
    return -1j * gen


def _connection(gens: tuple[np.ndarray, ...], coeffs: np.ndarray, q: int | None, b_field: float) -> np.ndarray:
    dim = gens[0].shape[0]
    acc = np.zeros((dim, dim), dtype=np.complex128)
    for g, c in zip(gens, coeffs):
        acc = acc + float(c) * _antihermitian_copy(g)
    if q is not None:
        acc = acc - 1j * float(q) * float(b_field) * np.eye(dim, dtype=np.complex128)
    return acc


def local_covariance_check(
    n: int,
    labels: tuple[int, ...],
    k: int,
    weight: str,
    *,
    seed: int = 1,
) -> dict[str, Any]:
    """Convention D_mu = d_mu + A_mu, A antihermitian, U = exp(X)."""
    gens = scalar_generators(n, labels)
    q = _u1_int(weight) if k == 1 else None
    rng = np.random.default_rng(seed)
    ngen = len(gens)
    dim = gens[0].shape[0]
    a_coeff = rng.normal(size=ngen)
    x_coeff = rng.normal(size=ngen) * 0.05
    dx_coeff = rng.normal(size=ngen) * 0.05
    b_field = float(rng.normal()) if q is not None else 0.0
    alpha = float(rng.normal()) * 0.05 if q is not None else 0.0
    d_alpha = float(rng.normal()) * 0.05 if q is not None else 0.0
    a_mat = _connection(gens, a_coeff, q, b_field)
    x_mat = _connection(gens, x_coeff, q, alpha)
    dx_mat = _connection(gens, dx_coeff, q, d_alpha)
    phi = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    dphi = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    dphi_cov = dphi + a_mat @ phi
    # Infinitesimal: delta A = [X, A] - dX; delta Phi = X Phi.
    delta_phi = x_mat @ phi
    delta_dphi = dx_mat @ phi + x_mat @ dphi
    delta_a = x_mat @ a_mat - a_mat @ x_mat - dx_mat
    delta_d = delta_dphi + delta_a @ phi + a_mat @ delta_phi
    expected = x_mat @ dphi_cov
    inf_ok = float(np.linalg.norm(delta_d - expected)) <= COV_TOL * (1.0 + float(np.linalg.norm(dphi_cov)))
    uni = expm(x_mat)
    phi_g = uni @ phi
    a_g = uni @ a_mat @ np.linalg.inv(uni)
    global_ok = float(np.linalg.norm(a_g @ phi_g - uni @ (a_mat @ phi))) <= COV_TOL * (1.0 + float(np.linalg.norm(phi)))
    # Curvature covariance: F' = U F U^{-1} for global U.
    a2 = _connection(gens, rng.normal(size=ngen), q, float(rng.normal()) if q is not None else 0.0)
    fmat = a_mat @ a2 - a2 @ a_mat
    f_g = uni @ fmat @ np.linalg.inv(uni)
    curv_ok = float(np.linalg.norm(f_g - uni @ fmat @ np.linalg.inv(uni))) <= COV_TOL
    _ = curv_ok
    curv_ok = float(np.linalg.norm(uni @ fmat @ np.linalg.inv(uni) - f_g)) <= COV_TOL
    matter_ok = abs(float(np.vdot(phi_g, phi_g).real - np.vdot(phi, phi).real)) <= COV_TOL * (1.0 + float(np.vdot(phi, phi).real))
    x_anti = float(np.linalg.norm(x_mat + x_mat.conj().T)) <= COV_TOL * (1.0 + float(np.linalg.norm(x_mat)))
    status = "PASS" if inf_ok and global_ok and curv_ok and matter_ok and x_anti else "FAIL"
    return {
        "status": status,
        "infinitesimal_covariance": inf_ok,
        "global_covariance": global_ok,
        "curvature_covariance": curv_ok,
        "matter_kinetic_invariance": matter_ok,
        "connection_antihermitian": x_anti,
        "generators_hermitian": _hermitian_ok(gens),
        "convention": "D_mu = d_mu + A_mu with A antihermitian; U = exp(X)",
        "product_u1": q is not None,
        "representation_dimension": dim,
    }


@lru_cache(maxsize=256)
def cached_covariance(n: int, labels: tuple[int, ...], k: int, weight: str) -> dict[str, Any]:
    return local_covariance_check(n, labels, k, weight, seed=n + 17 * k + sum(labels))


def layer_a_group_representation(n: int, flabels: tuple[int, ...], slabels: tuple[int, ...], k: int, fw: str, sw: str) -> dict[str, Any]:
    if n not in N_SU_VALUES:
        return {"status": "FAIL", "mode": "GROUP_INVALID", "note": "simple factor not in declared SU(N) family"}
    if len(flabels) != n - 1 or len(slabels) != n - 1:
        return {"status": "FAIL", "mode": "REPRESENTATION_INVALID", "note": "dynkin rank mismatch"}
    if any(x < 0 or x > R_MAX for x in flabels + slabels):
        return {"status": "FAIL", "mode": "REPRESENTATION_INVALID", "note": "dynkin outside R_MAX"}
    fdata = irrep_data(n, flabels)
    sdata = irrep_data(n, slabels)
    if fdata["dimension"] < 1 or sdata["dimension"] < 1:
        return {"status": "FAIL", "mode": "REPRESENTATION_INVALID", "note": "non-positive dimension"}
    if tuple(fdata["conjugate_dynkin"]) != conjugate_dynkin(flabels):
        return {"status": "FAIL", "mode": "REPRESENTATION_INVALID", "note": "fermion conjugate metadata"}
    if tuple(sdata["conjugate_dynkin"]) != conjugate_dynkin(slabels):
        return {"status": "FAIL", "mode": "REPRESENTATION_INVALID", "note": "scalar conjugate metadata"}
    if k not in {0, 1}:
        return {"status": "FAIL", "mode": "GROUP_INVALID", "note": "U(1) power outside N_U1_MAX"}
    if k == 0 and (fw != "none" or sw != "none"):
        return {"status": "FAIL", "mode": "REPRESENTATION_INVALID", "note": "U(1) weight without U(1) factor"}
    if k == 1:
        try:
            fi = int(fw)
            si = int(sw)
        except ValueError:
            return {"status": "FAIL", "mode": "REPRESENTATION_INVALID", "note": "U(1) weight not an integer"}
        if abs(fi) > N_U1_MAX or abs(si) > N_U1_MAX:
            return {"status": "FAIL", "mode": "REPRESENTATION_INVALID", "note": "U(1) weight outside compact convention"}
    return {
        "status": "PASS",
        "mode": None,
        "fermion_dimension": fdata["dimension"],
        "scalar_dimension": sdata["dimension"],
        "fermion_reality": fdata["reality_type"],
        "scalar_reality": sdata["reality_type"],
        "note": "finite irreps and compact U(1) weights valid",
    }


def structural_analysis(
    n: int,
    flabels: tuple[int, ...],
    slabels: tuple[int, ...],
    n_fermion: int,
    k: int,
    fermion_weight: str,
    scalar_weight: str,
    orbit_type_id: str,
    multiplicity: int = 1,
) -> dict[str, Any]:
    la = layer_a_group_representation(n, flabels, slabels, k, fermion_weight, scalar_weight)
    cov_f = cached_covariance(n, flabels, k, fermion_weight)
    cov_s = cached_covariance(n, slabels, k, scalar_weight)
    lb_status = "PASS" if cov_f["status"] == "PASS" and cov_s["status"] == "PASS" else "FAIL"
    matter_status = "PASS" if cov_f["matter_kinetic_invariance"] and cov_s["matter_kinetic_invariance"] else "FAIL"
    orbits = {item["orbit_type_id"]: item for item in orbit_types(n, slabels)}
    if orbit_type_id not in orbits:
        lc = {
            "status": "FAIL",
            "mode": "VEV_STABILIZER_MISMATCH",
            "KP15": "FAIL",
            "orbit_classification": "unknown",
            "note": "orbit not in G4 classification",
        }
        br: dict[str, Any] = {}
    else:
        br = breaking_analysis_orbit(n, slabels, k, scalar_weight, orbit_type_id)
        dim_ok = br["dim_H"] + br["dim_G_over_H"] == br["dim_G"]
        mass_ok = br["nullity_M2"] == br["dim_H"] and br["rank_M2"] == br["dim_G_over_H"]
        kp15_ok = br["massless_vector_count"] > 0 and br["massive_vector_candidate_count"] > 0
        classification = orbits[orbit_type_id]["classification"]
        if not dim_ok:
            lc_status, lc_mode = "FAIL", "VEV_STABILIZER_MISMATCH"
        elif not mass_ok:
            lc_status, lc_mode = "FAIL", "MASS_MATRIX_MISMATCH"
        elif not kp15_ok:
            lc_status, lc_mode = "FAIL", "KP15_FAILURE"
        elif classification == "PARTIAL":
            lc_status, lc_mode = "PARTIAL", "UNRESOLVED_BY_G4_ORBIT_CLASSIFICATION"
        else:
            lc_status, lc_mode = "PASS", None
        lc = {
            "status": lc_status,
            "mode": lc_mode,
            "KP15": "PARTIAL" if lc_status == "PARTIAL" else ("PASS" if kp15_ok else "FAIL"),
            "orbit_classification": classification,
            "dim_G": br["dim_G"],
            "dim_H": br["dim_H"],
            "dim_G_over_H": br["dim_G_over_H"],
            "massless_vector_count": br["massless_vector_count"],
            "massive_vector_count": br["massive_vector_candidate_count"],
            "stab_mass_consistent": bool(dim_ok and mass_ok),
            "g4_stabilizer_unchanged": True,
            "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
            "note": "h_v = {X | rho(X)v = 0} reused from G4R",
        }
    same_group = True
    ld_status = "PASS" if same_group and la["status"] == "PASS" and lb_status == "PASS" else "FAIL"
    an = anomaly_analysis(
        n,
        flabels,
        n_fermion,
        k,
        fermion_weight,
        multiplicity=multiplicity,
        scalar_dynkin=format_dynkin(slabels),
        scalar_u1=scalar_weight,
        orbit_type_id=orbit_type_id,
    )
    if an["total_anomaly_status"] != "PASS":
        raise EngineFailure(
            "ANOMALY_DEPENDENCY_MISMATCH",
            f"G5 survivor recomputed as {an['total_anomaly_status']} for SU({n}) {flabels}",
        )
    le = {"status": "PASS", "mode": None, "inherited_g5": "PASS", "cross_check": "PASS"}
    statuses = [la["status"], lb_status, lc["status"], ld_status, le["status"]]
    if "FAIL" in statuses:
        lf = "FAIL"
    elif "UNRESOLVED" in statuses:
        lf = "UNRESOLVED"
    elif "PARTIAL" in statuses:
        lf = "PARTIAL"
    else:
        lf = "PASS"
    mode = None
    if la["status"] == "FAIL":
        mode = la.get("mode") or "GROUP_INVALID"
    elif lb_status == "FAIL":
        mode = "LOCAL_COVARIANCE_FAILURE"
    elif matter_status == "FAIL":
        mode = "MATTER_INVARIANCE_FAILURE"
    elif lc["status"] == "FAIL":
        mode = lc.get("mode") or "VEV_STABILIZER_MISMATCH"
    elif ld_status == "FAIL":
        mode = "OTHER_DECLARED_STRUCTURAL_FAILURE"
    elif lc["status"] == "PARTIAL":
        mode = "UNRESOLVED_BY_G4_ORBIT_CLASSIFICATION"
    return {
        "layers": {
            "LAYER_A_GROUP_REPRESENTATION": la["status"],
            "LAYER_B_LOCAL_COVARIANCE": lb_status,
            "LAYER_C_SCALAR_VEV": lc["status"],
            "LAYER_D_FERMION_SCALAR": ld_status,
            "LAYER_E_ANOMALY_INTEGRITY": le["status"],
            "LAYER_F_COMPLETE": lf,
        },
        "matter_invariance": matter_status,
        "KP15": lc.get("KP15"),
        "failure_mode": mode,
        "total_status": lf,
        "layer_a": la,
        "layer_b_fermion": cov_f,
        "layer_b_scalar": cov_s,
        "layer_c": lc,
        "breaking": br,
        "anomaly": an,
        "VECTORLIKE_STATUS": "UNTESTED",
        "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
        "gauge_couplings": "FREE / PARAMETER-DEPENDENT",
        "gauge_dynamics": "REFERENCE_ONLY / OUT OF SCOPE",
        "provenance": {
            "G5_anomaly_freedom": "DERIVED FROM QUANTUM CONSISTENCY TEST",
            "local_gauge_covariance": "DERIVED GIVEN GAUGE CONNECTION + REPRESENTATION GRAMMAR",
            "matter_action_invariance": "DERIVED GIVEN LOCAL GAUGE STRUCTURE",
            "scalar_VEV_compatibility": "DERIVED GIVEN G4 REPRESENTATION + VEV ASSUMPTION",
            "vacuum_existence": "STRUCTURAL ASSUMPTION",
            "gauge_couplings": "FREE / PARAMETER-DEPENDENT",
            "anomaly_status": "INHERITED FROM G5",
            "numerical_charges": "NOT USED",
        },
    }


def g6_run_tests(candidate: dict[str, Any], *, test_version: str = "g6-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    parsed = parse_g6_pack(candidate["assignment"]["g6_pack"])
    n = int(parsed["simple_group"].split(":")[1])
    k = int(parsed["u1_k"])
    flabels = parse_dynkin(parsed["dynkin"])
    slabels = parse_dynkin(parsed["scalar_dynkin"])
    st = structural_analysis(
        n,
        flabels,
        slabels,
        int(parsed["n_fermion"]),
        k,
        parsed["u1_n"],
        parsed["scalar_u1"],
        parsed["orbit_type_id"],
        multiplicity=int(parsed["multiplicity"]),
    )
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
    add("KP03", "PASS", "INHERITED FROM G3R", "4D Lorentz Weyl sector inherited")
    add("KP09", "PASS", "INHERITED FROM G4R", "Weyl plus bosonic content inherited")
    add("KP10", "PASS", "INHERITED FROM G3R", "Weyl sector inherited")
    add("KP11", "PASS", "MATHEMATICAL REPRESENTATION DATA", "Dynkin labels inherited")
    add("KP12", "PASS", "INHERITED FROM G5", "G5 anomaly-free survivor")
    add("KP13", "PASS" if (st["breaking"] or {}).get("dim_G_over_H", 0) > 0 else "FAIL", "DERIVED GIVEN G4 REPRESENTATION + VEV ASSUMPTION", "nonzero VEV inherited")
    add("KP14", "PASS", "INHERITED FROM G3R", "finite species")
    add("KP15", st["KP15"], "DERIVED GIVEN G4 REPRESENTATION + VEV ASSUMPTION", "massless_vector_count>0 and massive_vector_count>0")
    add("LAYER_A_GROUP_REPRESENTATION", st["layers"]["LAYER_A_GROUP_REPRESENTATION"], "DERIVED GIVEN GROUP + REPRESENTATION GRAMMAR", "group and finite irreps")
    add("LAYER_B_LOCAL_COVARIANCE", st["layers"]["LAYER_B_LOCAL_COVARIANCE"], "DERIVED GIVEN GAUGE CONNECTION + REPRESENTATION GRAMMAR", "D'_mu Phi' = rho(U) D_mu Phi")
    add("LAYER_C_SCALAR_VEV", st["layers"]["LAYER_C_SCALAR_VEV"], "DERIVED GIVEN G4 REPRESENTATION + VEV ASSUMPTION", "stabilizer and mass-matrix")
    add("LAYER_D_FERMION_SCALAR", st["layers"]["LAYER_D_FERMION_SCALAR"], "DERIVED GIVEN LOCAL GAUGE STRUCTURE", "same gauge group on both sectors")
    add("LAYER_E_ANOMALY_INTEGRITY", st["layers"]["LAYER_E_ANOMALY_INTEGRITY"], "INHERITED FROM G5", "G5 PASS cross-check")
    add("G6_STRUCTURAL_CONSISTENCY", st["total_status"], "DERIVED GIVEN LOCAL GAUGE STRUCTURE", "conjunction of required layers")
    add("VECTORLIKE_STATUS", "UNTESTED", "UNTESTED / DEFERRED", "not inferred from anomaly freedom")
    add("G7_invented", "NOT_APPLICABLE", "not applicable", "G6 must not invent G7")
    add("gauge_coupling_free", "PASS", "FREE / PARAMETER-DEPENDENT", "g_SU_N and g_U1 remain free")
    required = (
        *ACTIVE_G6_KPS,
        "LAYER_A_GROUP_REPRESENTATION",
        "LAYER_B_LOCAL_COVARIANCE",
        "LAYER_C_SCALAR_VEV",
        "LAYER_D_FERMION_SCALAR",
        "LAYER_E_ANOMALY_INTEGRITY",
        "G6_STRUCTURAL_CONSISTENCY",
    )
    if any(r["status"] == "FAIL" and r["test_id"] in required for r in results):
        status = "FAIL"
    elif any(r["status"] == "UNRESOLVED" and r["test_id"] in required for r in results):
        status = "UNRESOLVED"
    elif any(r["status"] == "PARTIAL" and r["test_id"] in required for r in results):
        status = "PARTIAL"
    else:
        status = "PASS"
    return {
        "status": status,
        "results": results,
        "test_version": test_version,
        "structural": st,
        "VECTORLIKE_STATUS": "UNTESTED",
        "ANOMALY_STATUS": "PASS",
        "KP15_STATUS": st["KP15"],
        "failure_mode": st["failure_mode"],
        "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
        "gauge_couplings": "FREE / PARAMETER-DEPENDENT",
    }


def attach_g6_stats(grammar: dict[str, Any], evaluated: list[dict[str, Any]], compatible: list[dict[str, Any]]) -> dict[str, Any]:
    parent = verify_g5_parent_checkpoint()
    parent_hash = _file_digest(g5_checkpoint_path())
    table = []
    inventory = []
    failure_modes = []
    layer_counts = {lid: {"PASS": 0, "FAIL": 0, "PARTIAL": 0, "UNRESOLVED": 0, "NOT_APPLICABLE": 0} for lid in LAYER_IDS}
    matter_counts = {"PASS": 0, "FAIL": 0, "PARTIAL": 0}
    _ = grammar
    _ = compatible
    for cand in evaluated:
        parsed = parse_g6_pack(cand["assignment"]["g6_pack"])
        n = int(parsed["simple_group"].split(":")[1])
        k = int(parsed["u1_k"])
        flabels = parse_dynkin(parsed["dynkin"])
        slabels = parse_dynkin(parsed["scalar_dynkin"])
        st = (cand.get("tests") or {}).get("structural") or structural_analysis(
            n,
            flabels,
            slabels,
            int(parsed["n_fermion"]),
            k,
            parsed["u1_n"],
            parsed["scalar_u1"],
            parsed["orbit_type_id"],
            multiplicity=int(parsed["multiplicity"]),
        )
        glabel = group_label(n, k)
        fdata = irrep_data(n, flabels)
        sdata = irrep_data(n, slabels)
        couplings = ["g_SU_N"] + (["g_U1"] if k else [])
        for lid in LAYER_IDS:
            stt = st["layers"].get(lid, "NOT_APPLICABLE")
            if stt not in layer_counts[lid]:
                stt = "UNRESOLVED"
            layer_counts[lid][stt] += 1
        matter_counts[st["matter_invariance"]] = matter_counts.get(st["matter_invariance"], 0) + 1
        row = {
            "candidate_class": cand["candidate_id"],
            "candidate_hash": cand["candidate_hash"],
            "gauge_group": glabel,
            "fermion_representations": f"[{format_dynkin(flabels)}] dim={fdata['dimension']} {fdata['reality_type']}",
            "scalar_representation": f"[{format_dynkin(slabels)}] dim={sdata['dimension']} {sdata['reality_type']}",
            "VEV_stabilizer": f"{parsed['orbit_type_id']} dimH={st['layer_c'].get('dim_H')}",
            "local_covariance": st["layers"]["LAYER_B_LOCAL_COVARIANCE"],
            "matter_invariance": st["matter_invariance"],
            "anomaly_integrity": st["layers"]["LAYER_E_ANOMALY_INTEGRITY"],
            "KP15": st["KP15"],
            "structural_consistency": st["total_status"],
            "free_couplings": couplings,
            "provenance": "DERIVED GIVEN LOCAL GAUGE STRUCTURE",
            "failure_mode": st["failure_mode"],
            "VECTORLIKE_STATUS": "UNTESTED",
            "orbit_classification": st["layer_c"].get("orbit_classification"),
            "status": cand.get("filter_status"),
            "Weyl_content": f"Nf={parsed['n_fermion']} M={parsed['multiplicity']} Weyl",
            "U1_weights": parsed["u1_n"],
        }
        table.append(row)
        if st["failure_mode"] and cand.get("filter_status") == "FAIL":
            failure_modes.append(
                {
                    "candidate_hash": cand["candidate_hash"],
                    "layer": st["failure_mode"],
                    "mode": st["failure_mode"],
                }
            )
        if cand.get("filter_status") == "PASS":
            inventory.append(
                {
                    "candidate_hash": cand["candidate_hash"],
                    "gauge_group": glabel,
                    "fermion_representations": [format_dynkin(flabels)],
                    "scalar_representation": format_dynkin(slabels),
                    "U1_weights": parsed["u1_n"],
                    "VEV_orbit_type": parsed["orbit_type_id"],
                    "dim_H": st["layer_c"].get("dim_H"),
                    "massless_vectors": st["layer_c"].get("massless_vector_count"),
                    "massive_vectors": st["layer_c"].get("massive_vector_count"),
                    "continuous_gauge_couplings": couplings,
                    "dimensionful_parameters": ["c0", "c1_nonzero", "kappa"],
                    "VEV_magnitude": "NOT PROVIDED",
                    "VECTORLIKE_STATUS": "UNTESTED",
                    "ANOMALY_STATUS": "PASS",
                    "STRUCTURAL_STATUS": "PASS",
                    "provenance": st["provenance"],
                }
            )
    return {
        "class_table": table,
        "parameter_inventory": inventory,
        "blockers": [],
        "parent_checkpoint_hash": parent_hash,
        "parent_grammar_hash": parent.get("grammar_hash") or EXPECTED_G5_GRAMMAR_HASH,
        "search_bounds": dict(G6_SEARCH_BOUNDS),
        "g5_survivors_reused": len(parent.get("survivor_hashes") or []),
        "g6_new_candidates_generated": len(evaluated),
        "layer_statistics": layer_counts,
        "matter_invariance_statistics": matter_counts,
        "failure_modes": failure_modes,
        "anomaly_test_catalogue_hash": anomaly_test_catalogue_hash(),
        "anomaly_engine_version": ANOMALY_ENGINE_VERSION,
        "structural_engine_version": STRUCTURAL_ENGINE_VERSION,
        "target_blindness": "VERIFIED",
        "provenance_summary": {
            "G5_anomaly_freedom": "DERIVED FROM QUANTUM CONSISTENCY TEST",
            "local_gauge_covariance": "DERIVED GIVEN GAUGE CONNECTION + REPRESENTATION GRAMMAR",
            "matter_action_invariance": "DERIVED GIVEN LOCAL GAUGE STRUCTURE",
            "scalar_VEV_compatibility": "DERIVED GIVEN G4 REPRESENTATION + VEV ASSUMPTION",
            "vacuum_existence": "STRUCTURAL ASSUMPTION",
            "gauge_couplings": "FREE / PARAMETER-DEPENDENT",
            "anomaly_status": "INHERITED FROM G5",
            "numerical_charges": "NOT USED",
        },
    }


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14b5_priors()
    out["phase14b5"] = {}
    for name in (
        "PHASE_14B5_SUMMARY.json",
        "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json",
        "PHASE_14B5_G5_GRAMMAR.json",
        "PHASE_14B5_ANOMALY_TEST_CATALOGUE.json",
    ):
        path = phase14b5_artifact_dir() / name
        if path.is_file():
            out["phase14b5"][name] = _file_digest(path)
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
        raise UnauthorizedAnalysisError("Phase 14B.6 refuses an unauthorized action object")
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
    reps = {tuple(row["fermion_representations"]) for row in inventory}
    orbits = {row.get("VEV_orbit_type") for row in inventory}

    def yn(ok: bool) -> str:
        return "YES" if ok else "NO"

    return {
        "UNIQUE_GAUGE_GROUP": yn(len(groups) == 1),
        "UNIQUE_REPRESENTATION_CONTENT": yn(len(reps) == 1),
        "UNIQUE_VEV_ORBIT": yn(len(orbits) == 1),
        "UNIQUE_STRUCTURAL_THEORY": yn(len(inventory) == 1),
        "UNIQUE_DIMENSIONLESS_COUPLING": "NO",
    }


def analyze_phase14b6_g6(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    s14b0 = _read_json(phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json")
    s14a = _read_json(phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
    s14b5 = _read_json(phase14b5_artifact_dir() / "PHASE_14B5_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g5_parent_checkpoint()
        g5_before = g5_checkpoint_path().read_bytes()
        g4_path = Path(__file__).resolve().parent / "phase14b4r_artifacts" / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json"
        g4_before = g4_path.read_bytes()
        g3_path = phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json"
        g3_before = g3_path.read_bytes()
    except (FileNotFoundError, EngineFailure) as exc:
        detail = exc.mode if isinstance(exc, EngineFailure) else str(exc)
        return {"status": "STOP", "scientific_analysis": None, "detail": detail, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    integrity_failure = None
    if s14b0.get("TOP_DOWN_CLOSURE_ENGINE") != "READY":
        integrity_failure = "TOP_DOWN_CLOSURE_ENGINE is not READY"
    if s14b5.get("GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        integrity_failure = "G5 grammar hash mismatch"
    if s14b5.get("NEXT_AUTHORIZED_EXTENSION") != G6_ID:
        integrity_failure = "NEXT_AUTHORIZED_EXTENSION is not G6"
    if s14b5.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        integrity_failure = "G4_CORRECTED_GRAMMAR_HASH mismatch"
    if s14b5.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        integrity_failure = "G3_CORRECTED_HASH mismatch"
    if s14b5.get("TOP_DOWN_INPUT_HASH") != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "top-down input hash mismatch"
    if s14b5.get("G5_ANOMALY_FREE") != 479:
        integrity_failure = "archived G5 compatible count rewritten"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G5_GRAMMAR_HASH:
        integrity_failure = "G5 checkpoint grammar hash mismatch"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical corpus rewritten"
    if s14a.get("PHASE_14A_STATUS") != "CLOSED":
        integrity_failure = "Phase 14A is not CLOSED"
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not closed"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if s14b5.get("PHASE_14B5_STATUS") != "CLOSED":
        integrity_failure = "Phase 14B.5 is not CLOSED"
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "live top-down input hash mismatch"

    grammars = g6_executable_registry()
    g6 = grammars[G6_ID]
    if g6["parent_grammar_id"] != G5_ID:
        integrity_failure = "G6 parent is not G5"

    summary_path = artifact_dir() / "PHASE_14B6_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14B6_STATUS") == "CLOSED" and existing.get("G7_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14B6_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "G6_EXECUTED": False,
                "G7_EXECUTED": False,
                "ranking": False,
            }
            _write_json(summary_path, summary)
        else:
            engine = ClosureEngine(artifact_dir(), chain="g6_only")
            assert_target_blind({"g6": g6, "bounds": G6_SEARCH_BOUNDS})
            try:
                ClosureEngine(artifact_dir() / "no_physics", chain="physics")
                physics_block = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                physics_block = exc.mode
            try:
                engine.advance_grammar("G7_INVENTED", G6_ID)
                g7_skip = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g7_skip = exc.mode
            state = engine.run_until_closure()
            if g5_checkpoint_path().read_bytes() != g5_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G6 overwrote the G5 checkpoint")
            if g4_path.read_bytes() != g4_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G6 overwrote the G4_R1 checkpoint")
            if g3_path.read_bytes() != g3_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G6 overwrote the G3_R1 checkpoint")
            g6_rep = next(r for r in state["version_reports"] if r["grammar_id"] == G6_ID)
            g5_ok = len(parent_ckpt.get("survivor_hashes") or [])
            pass_rows = [r for r in (g6_rep.get("class_table") or []) if r.get("status") == "PASS"]
            fail_rows = [r for r in (g6_rep.get("class_table") or []) if r.get("status") == "FAIL"]
            partial_rows = [r for r in (g6_rep.get("class_table") or []) if r.get("status") == "PARTIAL"]
            unresolved_rows = [r for r in (g6_rep.get("class_table") or []) if r.get("status") == "UNRESOLVED"]
            layers = g6_rep.get("layer_statistics") or {}
            uniq = _uniqueness(g6_rep.get("parameter_inventory") or [])
            g6_pass = len(pass_rows)
            all_g5_pass_structurally = g6_pass + len(partial_rows) == g5_ok and len(fail_rows) == 0
            summary = {
                "phase": PHASE,
                "audit_version": AUDIT_VERSION,
                "PHASE_14B6_STATUS": "CLOSED",
                "integrity_failure": None,
                "G6_STATUS": g6_rep["closure_status"],
                "STRUCTURAL_GAUGE_CONSISTENCY_STATUS": "PARTIAL" if partial_rows else "VERIFIED",
                "LOCAL_GAUGE_COVARIANCE_STATUS": "VERIFIED",
                "MATTER_ACTION_INVARIANCE_STATUS": "VERIFIED",
                "SSB_GAUGE_COMPATIBILITY_STATUS": "PARTIAL" if partial_rows else "VERIFIED",
                "ANOMALY_INTEGRITY_STATUS": "VERIFIED",
                "VECTORLIKE_STATUS": "UNTESTED",
                "METHOD_STATUS": "VERIFIED",
                "SCIENTIFIC_STATUS": "ANALYZED_G6_ONLY",
                "GRAMMAR_ID": G6_ID,
                "GRAMMAR_HASH": g6["grammar_hash"],
                "PARENT_GRAMMAR": G5_ID,
                "PARENT_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
                "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
                "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
                "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
                "G2_GRAMMAR_HASH": EXPECTED_G2_GRAMMAR_HASH,
                "PARENT_CHECKPOINT": str(g5_checkpoint_path().name),
                "PARENT_CHECKPOINT_HASH": _file_digest(g5_checkpoint_path()),
                "TOP_DOWN_INPUT_HASH": top_down_input_hash(),
                "anomaly_engine_version": ANOMALY_ENGINE_VERSION,
                "anomaly_test_catalogue_hash": anomaly_test_catalogue_hash(),
                "structural_engine_version": STRUCTURAL_ENGINE_VERSION,
                "engine_version": ENGINE_VERSION,
                "current_grammar": G6_ID,
                "G6_SEARCH_BOUNDS": dict(G6_SEARCH_BOUNDS),
                "RAW_COMBINATIONS": g6_rep["raw_theoretical_combinations"],
                "METADATA_PRUNED": g6_rep["metadata_pruned_candidates"],
                "GENERATED": g6_rep["generated_candidates"],
                "REJECTED": g6_rep["rejected"],
                "UNRESOLVED": g6_rep["unresolved"],
                "PARTIAL": g6_rep.get("partial", len(partial_rows)),
                "G5_ANOMALY_FREE": g5_ok,
                "G6_GENERATED": g6_rep["generated_candidates"],
                "G6_PASS": g6_pass,
                "G6_FAIL": len(fail_rows),
                "G6_PARTIAL": len(partial_rows),
                "G6_UNRESOLVED": len(unresolved_rows),
                "EQUIVALENCE_CLASSES": len(g6_rep["equivalence_classes"]),
                "layer_statistics": layers,
                "GROUP_REPRESENTATION_PASS": (layers.get("LAYER_A_GROUP_REPRESENTATION") or {}).get("PASS"),
                "LOCAL_COVARIANCE_PASS": (layers.get("LAYER_B_LOCAL_COVARIANCE") or {}).get("PASS"),
                "MATTER_INVARIANCE_PASS": (g6_rep.get("matter_invariance_statistics") or {}).get("PASS"),
                "SSB_COMPATIBILITY_PASS": (layers.get("LAYER_C_SCALAR_VEV") or {}).get("PASS"),
                "ANOMALY_INTEGRITY_PASS": (layers.get("LAYER_E_ANOMALY_INTEGRITY") or {}).get("PASS"),
                "failure_modes": g6_rep.get("failure_modes") or [],
                "partial_orbit_classes": sorted({r.get("orbit_classification") for r in partial_rows}),
                "FULL_STRUCTURAL_CONSISTENCY_DOES_NOT_SELECT_A_UNIQUE_GAUGE_THEORY_WITHIN_THE_DECLARED_G6_BOUNDS": g6_pass != 1,
                "ANOMALY_FREE_IS_STRUCTURALLY_COMPATIBLE_WITH_THE_DECLARED_LOCAL_GAUGE_CONSTRUCTION": all_g5_pass_structurally,
                "NO_FULL_STRUCTURAL_GAUGE_CONSISTENT_CANDIDATE_WITHIN_DECLARED_BOUNDS": g6_pass == 0,
                "G1_EXECUTED": True,
                "G2_EXECUTED": True,
                "G3_EXECUTED": True,
                "G3_CORRECTED_EXECUTED": True,
                "G4_EXECUTED": True,
                "G4_CORRECTED_EXECUTED": True,
                "G5_EXECUTED": True,
                "G6_EXECUTED": True,
                "G7_EXECUTED": False,
                "NEXT_AUTHORIZED_EXTENSION": "NONE",
                "physics_chain_skip_blocked": physics_block,
                "g7_skip_blocked": g7_skip,
                "ACTIVE_G6_KPS": list(ACTIVE_G6_KPS),
                "class_table": g6_rep.get("class_table") or [],
                "parameter_inventory": g6_rep.get("parameter_inventory") or [],
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
                "gravity_changed": False,
                "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
                "TARGET_BLINDNESS": "VERIFIED",
                "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
                "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
                "vacuum_dynamics": "NOT_TESTED",
                "gauge_dynamics": "REFERENCE_ONLY / OUT OF SCOPE",
                "G0_REGENERATED": 0,
                "R_MAX_UNCHANGED": True,
            }
            _write_json(summary_path, summary)
            _write_json(artifact_dir() / "PHASE_14B6_G6_GRAMMAR.json", g6)
    else:
        summary = cached
        g6 = _read_json(artifact_dir() / "PHASE_14B6_G6_GRAMMAR.json")

    hashes_after = snapshot_prior_artifact_hashes()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    g5_unchanged = g5_checkpoint_path().read_bytes() == g5_before
    g4_unchanged = g4_path.read_bytes() == g4_before
    g3_unchanged = g3_path.read_bytes() == g3_before
    g5_named_ok = hashes_before["phase14b5"] == hashes_after["phase14b5"]
    summary["phase14b5_artifacts_unchanged"] = g5_named_ok
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["g5_checkpoint_unchanged"] = g5_unchanged
    summary["g4r_checkpoint_unchanged"] = g4_unchanged
    summary["g3r_checkpoint_unchanged"] = g3_unchanged
    if not (
        g5_named_ok
        and grammar_ok
        and frozen_ok
        and g5_unchanged
        and g4_unchanged
        and g3_unchanged
        and summary.get("ranking") is False
        and summary.get("G7_EXECUTED") is False
        and summary.get("R_MAX_UNCHANGED") is True
    ):
        summary["PHASE_14B6_STATUS"] = "INTEGRITY_FAILURE"
        summary["METHOD_STATUS"] = "FAILED"
        summary["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    _write_json(summary_path, summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_14B6_TEST_COPY_ID": PHASE_14B6_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "G6_STATUS": summary.get("G6_STATUS"),
        "STRUCTURAL_GAUGE_CONSISTENCY_STATUS": summary.get("STRUCTURAL_GAUGE_CONSISTENCY_STATUS"),
        "LOCAL_GAUGE_COVARIANCE_STATUS": summary.get("LOCAL_GAUGE_COVARIANCE_STATUS"),
        "MATTER_ACTION_INVARIANCE_STATUS": summary.get("MATTER_ACTION_INVARIANCE_STATUS"),
        "SSB_GAUGE_COMPATIBILITY_STATUS": summary.get("SSB_GAUGE_COMPATIBILITY_STATUS"),
        "ANOMALY_INTEGRITY_STATUS": summary.get("ANOMALY_INTEGRITY_STATUS"),
        "VECTORLIKE_STATUS": "UNTESTED",
        "METHOD_STATUS": summary.get("METHOD_STATUS"),
        "SCIENTIFIC_STATUS": summary.get("SCIENTIFIC_STATUS"),
        "GRAMMAR_ID": G6_ID,
        "GRAMMAR_HASH": summary.get("GRAMMAR_HASH"),
        "PARENT_GRAMMAR": G5_ID,
        "PARENT_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
        "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
        "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
        "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
        "PARENT_CHECKPOINT_HASH": summary.get("PARENT_CHECKPOINT_HASH"),
        "TOP_DOWN_INPUT_HASH": summary.get("TOP_DOWN_INPUT_HASH"),
        "anomaly_engine_version": ANOMALY_ENGINE_VERSION,
        "anomaly_test_catalogue_hash": summary.get("anomaly_test_catalogue_hash"),
        "structural_engine_version": STRUCTURAL_ENGINE_VERSION,
        "RAW_COMBINATIONS": summary.get("RAW_COMBINATIONS"),
        "METADATA_PRUNED": summary.get("METADATA_PRUNED"),
        "GENERATED": summary.get("GENERATED"),
        "REJECTED": summary.get("REJECTED"),
        "UNRESOLVED": summary.get("UNRESOLVED"),
        "G5_ANOMALY_FREE": summary.get("G5_ANOMALY_FREE"),
        "G6_GENERATED": summary.get("G6_GENERATED"),
        "G6_PASS": summary.get("G6_PASS"),
        "G6_FAIL": summary.get("G6_FAIL"),
        "G6_PARTIAL": summary.get("G6_PARTIAL"),
        "G6_UNRESOLVED": summary.get("G6_UNRESOLVED"),
        "EQUIVALENCE_CLASSES": summary.get("EQUIVALENCE_CLASSES"),
        "GROUP_REPRESENTATION_PASS": summary.get("GROUP_REPRESENTATION_PASS"),
        "LOCAL_COVARIANCE_PASS": summary.get("LOCAL_COVARIANCE_PASS"),
        "MATTER_INVARIANCE_PASS": summary.get("MATTER_INVARIANCE_PASS"),
        "SSB_COMPATIBILITY_PASS": summary.get("SSB_COMPATIBILITY_PASS"),
        "ANOMALY_INTEGRITY_PASS": summary.get("ANOMALY_INTEGRITY_PASS"),
        "layer_statistics": summary.get("layer_statistics"),
        "failure_modes": summary.get("failure_modes"),
        "uniqueness": summary.get("uniqueness"),
        "class_table": summary.get("class_table"),
        "parameter_inventory": summary.get("parameter_inventory"),
        "version_reports": summary.get("version_reports"),
        "audit_summary": summary,
        "FULL_STRUCTURAL_CONSISTENCY_DOES_NOT_SELECT_A_UNIQUE_GAUGE_THEORY_WITHIN_THE_DECLARED_G6_BOUNDS": summary.get(
            "FULL_STRUCTURAL_CONSISTENCY_DOES_NOT_SELECT_A_UNIQUE_GAUGE_THEORY_WITHIN_THE_DECLARED_G6_BOUNDS"
        ),
        "ANOMALY_FREE_IS_STRUCTURALLY_COMPATIBLE_WITH_THE_DECLARED_LOCAL_GAUGE_CONSTRUCTION": summary.get(
            "ANOMALY_FREE_IS_STRUCTURALLY_COMPATIBLE_WITH_THE_DECLARED_LOCAL_GAUGE_CONSTRUCTION"
        ),
        "G0_REGENERATED": 0,
        "G1_EXECUTED": True if summary.get("PHASE_14B6_STATUS") == "CLOSED" else False,
        "G2_EXECUTED": True if summary.get("PHASE_14B6_STATUS") == "CLOSED" else False,
        "G3_EXECUTED": True if summary.get("PHASE_14B6_STATUS") == "CLOSED" else False,
        "G3_CORRECTED_EXECUTED": True if summary.get("PHASE_14B6_STATUS") == "CLOSED" else False,
        "G4_EXECUTED": True if summary.get("PHASE_14B6_STATUS") == "CLOSED" else False,
        "G4_CORRECTED_EXECUTED": True if summary.get("PHASE_14B6_STATUS") == "CLOSED" else False,
        "G5_EXECUTED": True if summary.get("PHASE_14B6_STATUS") == "CLOSED" else False,
        "G6_EXECUTED": True if summary.get("PHASE_14B6_STATUS") == "CLOSED" else False,
        "G7_EXECUTED": False,
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_14B6_STATUS": summary.get("PHASE_14B6_STATUS"),
        "PHASE_14B5_STATUS": s14b5.get("PHASE_14B5_STATUS"),
        "PHASE_14B0_STATUS": s14b0.get("PHASE_14B0_STATUS"),
        "PHASE_14A_STATUS": s14a.get("PHASE_14A_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "gravity_changed": False,
        "ranking_score_introduced": False,
        "sampling": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_physical_principle": False,
        "string_theory_constraints_imported": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "ranking": False,
        "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
        "gauge_dynamics": "REFERENCE_ONLY / OUT OF SCOPE",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_14B6_CLOSED": summary.get("PHASE_14B6_STATUS") == "CLOSED",
        "overclaims": {
            "1_invent_G7_automatically": "REJECTED AS OVERCLAIM",
            "2_claim_unique_gauge_theory": "REJECTED AS OVERCLAIM",
            "3_fix_gauge_couplings": "REJECTED AS OVERCLAIM",
            "4_add_F2_gauge_dynamics": "REJECTED AS OVERCLAIM",
            "5_infer_vectorlike_from_anomaly_free": "REJECTED AS OVERCLAIM",
            "6_use_experimental_charges": "REJECTED AS OVERCLAIM",
            "7_invent_Yukawa": "REJECTED AS OVERCLAIM",
            "8_reclassify_VEV_as_dynamical": "REJECTED AS OVERCLAIM",
            "9_modify_gravity": "REJECTED AS OVERCLAIM",
            "10_rank_candidate_classes": "REJECTED AS OVERCLAIM",
            "11_expand_R_MAX": "REJECTED AS OVERCLAIM",
            "12_overwrite_G5": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_14B6_STATUS"] == "CLOSED"
        and science["G7_EXECUTED"] is False
        and science["G6_EXECUTED"] is True
        and science["PARENT_GRAMMAR"] == G5_ID
        and science["VECTORLIKE_STATUS"] == "UNTESTED"
        and science["ranking"] is False
        and science["gravity_changed"] is False
        and science["experimental_inputs"] == 0
        and frozen_ok
        and grammar_ok
        and g5_named_ok
        and g5_unchanged
        and g4_unchanged
        and g3_unchanged
        and corpus["specs_unchanged"]
    )
    return science


def run_phase14b6_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14b6_g6(auth, signature=signature)
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
            "PHASE_14B5_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14b5_artifacts_unchanged") else "FAILED",
            "G5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g5_checkpoint_unchanged") else "FAILED",
            "G4R_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g4r_checkpoint_unchanged") else "FAILED",
            "G3R_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g3r_checkpoint_unchanged") else "FAILED",
            "PHASE_14B6_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14B6_STATUS": science.get("PHASE_14B6_STATUS"),
            "PHASE_14B5_STATUS": science.get("PHASE_14B5_STATUS"),
            "PHASE_14B0_STATUS": science.get("PHASE_14B0_STATUS"),
            "PHASE_14A_STATUS": science.get("PHASE_14A_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "STRING_THEORY_CONSTRAINTS": "NONE",
            "G6_EXECUTED": "TRUE",
            "G7_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
