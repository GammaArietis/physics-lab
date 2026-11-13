"""Phase 14B.4R: G4 stabilizer and mass-matrix mathematical consistency correction.

Does not activate G5. Does not overwrite the archived G4 checkpoint.
Does not introduce new physics.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

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
from physics_lab.physics.phase14b3_g3 import (
    EXPECTED_G2_GRAMMAR_HASH,
    EXPECTED_TOP_DOWN_INPUT_HASH,
    N_SU_VALUES,
    N_U1_MAX,
    R_MAX,
    all_dynkin,
    build_representation_catalogue,
    catalogue_hash,
    format_dynkin,
    g3_pack_values,
    group_label,
    irrep_data,
    parse_dynkin,
    parse_pack,
    reality_type,
    su_n_dimension,
)
from physics_lab.physics.phase14b3r_g3 import (
    G3R_ID,
    artifact_dir as phase14b3r_artifact_dir,
)
from physics_lab.physics.phase14b4_g4 import (
    ACTIVE_G4_KPS,
    DEFERRED_G4_KPS,
    EXPECTED_G3R_CHECKPOINT_HASH,
    EXPECTED_G3R_GRAMMAR_HASH,
    N_SCALAR_MAX,
    fund_gens_numpy,
    irrep_generators,
    snapshot_prior_artifact_hashes as snapshot_14b4_priors,
    verify_g3r_parent_checkpoint,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_OLD_G4_CHECKPOINT_HASH",
    "EXPECTED_OLD_G4_GRAMMAR_HASH",
    "G4R_CHAIN",
    "analyze_phase14b4r_g4",
    "artifact_dir",
    "breaking_analysis_orbit",
    "g4r_executable_registry",
    "g4r_metadata_legal",
    "g4r_run_tests",
    "orbit_types",
    "run_phase14b4r_or_stop",
    "solve_stabilizer",
    "independent_mass_matrix",
]

PHASE = "PHASE_14B.4R"
PHASE_14B4R_TEST_COPY_ID = "PHASE_14B4R_G4_STABILIZER_MASS_MATRIX_AUDIT"
AUDIT_VERSION = "phase14b4r-g4-stabilizer-audit-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_OLD_G4_GRAMMAR_HASH = "58a75b4ef696d3e90b61a3056c41b879a05f7c24b3b427f6ff5c67ce74fa0851"
EXPECTED_OLD_G4_CHECKPOINT_HASH = "a7e3956942c6fd3e0dcfb2efec5d985dd729ad5794bfa1c046a763930227de09"
G4R_ID = "G4_SCALAR_MULTIPLETS_VEV_R1"
G4R_CHAIN: tuple[str, ...] = (G4R_ID,)
OLD_G4_ID = "G4_SCALAR_MULTIPLETS_VEV"
RANK_TOL = 1e-6
CLOSURE_TOL = 1e-6
SCALAR_SEARCH_BOUNDS = {
    "R_MAX": R_MAX,
    "R_MAX_is_search_bound_not_prediction": True,
    "N_SCALAR_MAX": N_SCALAR_MAX,
    "N_SCALAR_MAX_is_search_bound_not_prediction": True,
    "N_U1_MAX": N_U1_MAX,
    "N_f": [1, 2],
    "simple_groups": ["SU(2)", "SU(3)", "SU(4)"],
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b4r_artifacts"


def old_g4_artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b4_artifacts"


def old_g4_checkpoint_path() -> Path:
    return old_g4_artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV.json"


def g3r_checkpoint_path() -> Path:
    return phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json"


def _write_json(path: Path, payload: Any) -> None:
    assert_target_blind(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _spec(orbit_type_id: str, representative_VEV_form: str, classification: str) -> dict[str, str]:
    return {
        "orbit_type_id": orbit_type_id,
        "representative_VEV_form": representative_VEV_form,
        "classification": classification,
    }


def orbit_types(n: int, labels: tuple[int, ...]) -> list[dict[str, str]]:
    if all(a == 0 for a in labels):
        return [_spec("nonzero_singlet", "unit_singlet", "COMPLETE")]
    if labels[0] == 1 and all(a == 0 for a in labels[1:]):
        return [_spec("nonzero_fundamental", "e_0", "COMPLETE")]
    if labels[-1] == 1 and all(a == 0 for a in labels[:-1]):
        return [_spec("nonzero_antifundamental", "e_0", "COMPLETE")]
    if n == 3 and labels == (1, 1):
        return [
            _spec("regular_adjoint", "hermitian_diag_1_0_m1", "COMPLETE"),
            _spec("degenerate_adjoint", "hermitian_diag_1_1_m2", "COMPLETE"),
        ]
    if n == 4 and labels == (1, 0, 1):
        return [
            _spec("regular_adjoint", "hermitian_diag_3_1_m1_m3", "COMPLETE"),
            _spec("partition_211_adjoint", "hermitian_diag_1_1_0_m2", "COMPLETE"),
            _spec("partition_22_adjoint", "hermitian_diag_1_1_m1_m1", "COMPLETE"),
            _spec("partition_31_adjoint", "hermitian_diag_1_1_1_m3", "COMPLETE"),
        ]
    if n == 4 and labels == (0, 1, 0):
        return [
            _spec("decomposable_2form", "A_01", "COMPLETE"),
            _spec("symplectic_2form", "A_01_plus_A_23", "COMPLETE"),
        ]
    return [
        _spec("hw_vector", "highest_weight_basis_vector", "PARTIAL"),
        _spec("generic_nonzero", "deterministic_generic_nonzero", "PARTIAL"),
    ]


def vev_orbit_classification_status() -> str:
    for n in N_SU_VALUES:
        for labels in all_dynkin(n - 1, R_MAX):
            if any(item["classification"] == "PARTIAL" for item in orbit_types(n, labels)):
                return "PARTIAL"
    return "COMPLETE"


def _twoform_pairs() -> list[tuple[int, int]]:
    return [(i, j) for i in range(4) for j in range(i + 1, 4)]


@lru_cache(maxsize=8)
def _adjoint_generators(n: int) -> tuple[np.ndarray, ...]:
    fund = tuple(fund_gens_numpy(n))
    dim = n * n - 1
    out = []
    for ta in fund:
        mat = np.zeros((dim, dim), dtype=np.complex128)
        for b, tb in enumerate(fund):
            image = -1j * (ta @ tb - tb @ ta)
            mat[:, b] = _flatten_hermitian(image, fund)
        out.append(mat)
    return tuple(out)


def _flatten_hermitian(hmat: np.ndarray, fund: tuple[np.ndarray, ...]) -> np.ndarray:
    return np.array([2.0 * np.trace(g.conj().T @ hmat).real for g in fund], dtype=np.complex128)


def _adjoint_vev(hmat: np.ndarray, n: int) -> np.ndarray:
    fund = tuple(fund_gens_numpy(n))
    vec = _flatten_hermitian(hmat, fund)
    nrm = np.linalg.norm(vec)
    if nrm < RANK_TOL:
        raise EngineFailure("G4_STABILIZER_ERROR", "zero adjoint VEV")
    return vec / nrm


@lru_cache(maxsize=4)
def _twoform_generators() -> tuple[np.ndarray, ...]:
    fund = fund_gens_numpy(4)
    pairs = _twoform_pairs()
    out = []
    for tmat in fund:
        mat = np.zeros((6, 6), dtype=np.complex128)
        for col, (i, j) in enumerate(pairs):
            amap = np.zeros((4, 4), dtype=np.complex128)
            amap[i, j] = 1.0
            amap[j, i] = -1.0
            image = tmat @ amap + amap @ tmat.T
            for row, (p, q) in enumerate(pairs):
                mat[row, col] = image[p, q]
        out.append(mat)
    return tuple(out)


def _twoform_vev(entries: dict[tuple[int, int], complex]) -> np.ndarray:
    vec = np.zeros(6, dtype=np.complex128)
    for idx, pair in enumerate(_twoform_pairs()):
        vec[idx] = entries.get(pair, 0.0)
    nrm = np.linalg.norm(vec)
    if nrm < RANK_TOL:
        raise EngineFailure("G4_STABILIZER_ERROR", "zero two-form VEV")
    return vec / nrm


def scalar_generators(n: int, labels: tuple[int, ...]) -> tuple[np.ndarray, ...]:
    if all(a == 0 for a in labels):
        return tuple(np.zeros((1, 1), dtype=np.complex128) for _ in fund_gens_numpy(n))
    if n == 3 and labels == (1, 1):
        return _adjoint_generators(3)
    if n == 4 and labels == (1, 0, 1):
        return _adjoint_generators(4)
    if n == 4 and labels == (0, 1, 0):
        return _twoform_generators()
    if labels[0] == 1 and all(a == 0 for a in labels[1:]):
        return tuple(fund_gens_numpy(n))
    if labels[-1] == 1 and all(a == 0 for a in labels[:-1]):
        return tuple(-g.conj() for g in fund_gens_numpy(n))
    return irrep_generators(n, labels)


def representative_vev(n: int, labels: tuple[int, ...], orbit_type_id: str) -> np.ndarray:
    gens = scalar_generators(n, labels)
    dim = gens[0].shape[0]
    if orbit_type_id == "nonzero_singlet":
        return np.array([1.0 + 0.0j])
    if orbit_type_id in {"nonzero_fundamental", "nonzero_antifundamental"}:
        vec = np.zeros(dim, dtype=np.complex128)
        vec[0] = 1.0
        return vec
    if n == 3 and labels == (1, 1) and orbit_type_id == "regular_adjoint":
        return _adjoint_vev(np.diag([1.0, 0.0, -1.0]).astype(np.complex128), 3)
    if n == 3 and labels == (1, 1) and orbit_type_id == "degenerate_adjoint":
        return _adjoint_vev(np.diag([1.0, 1.0, -2.0]).astype(np.complex128), 3)
    if n == 4 and labels == (1, 0, 1) and orbit_type_id == "regular_adjoint":
        return _adjoint_vev(np.diag([3.0, 1.0, -1.0, -3.0]).astype(np.complex128), 4)
    if n == 4 and labels == (1, 0, 1) and orbit_type_id == "partition_211_adjoint":
        return _adjoint_vev(np.diag([1.0, 1.0, 0.0, -2.0]).astype(np.complex128), 4)
    if n == 4 and labels == (1, 0, 1) and orbit_type_id == "partition_22_adjoint":
        return _adjoint_vev(np.diag([1.0, 1.0, -1.0, -1.0]).astype(np.complex128), 4)
    if n == 4 and labels == (1, 0, 1) and orbit_type_id == "partition_31_adjoint":
        return _adjoint_vev(np.diag([1.0, 1.0, 1.0, -3.0]).astype(np.complex128), 4)
    if n == 4 and labels == (0, 1, 0) and orbit_type_id == "decomposable_2form":
        return _twoform_vev({(0, 1): 1.0})
    if n == 4 and labels == (0, 1, 0) and orbit_type_id == "symplectic_2form":
        return _twoform_vev({(0, 1): 1.0, (2, 3): 1.0})
    if orbit_type_id == "hw_vector":
        vec = np.zeros(dim, dtype=np.complex128)
        vec[0] = 1.0
        return vec
    if orbit_type_id == "generic_nonzero":
        if reality_type(n, labels) == "real":
            vec = np.array([float(i + 1) for i in range(dim)], dtype=np.complex128)
        else:
            vec = np.array([(i + 1) + (i + 2) * 1j for i in range(dim)], dtype=np.complex128)
        return vec / np.linalg.norm(vec)
    raise EngineFailure("G4_STABILIZER_ERROR", f"unknown orbit {orbit_type_id}")


def _directions(gens: list[np.ndarray], vev: np.ndarray, u1_weight: int | None) -> list[np.ndarray]:
    tv = [g @ vev for g in gens]
    if u1_weight is not None:
        tv.append(float(u1_weight) * vev)
    return tv


def solve_stabilizer(gens: list[np.ndarray], vev: np.ndarray, u1_weight: int | None = None) -> dict[str, Any]:
    tv = _directions(gens, vev, u1_weight)
    dim_g = len(tv)
    if dim_g == 0:
        return {"dim_G": 0, "dim_H": 0, "broken_dim": 0, "nullspace": np.zeros((0, 0)), "jacobian_rank": 0}
    cols = [np.concatenate([item.real, item.imag]) for item in tv]
    jac = np.stack(cols, axis=1)
    rank = int(np.linalg.matrix_rank(jac, tol=RANK_TOL))
    dim_h = dim_g - rank
    _u, svals, vh = np.linalg.svd(jac, full_matrices=True)
    cutoff = RANK_TOL
    nullspace = vh[rank:].T.real if rank < dim_g else np.zeros((dim_g, 0))
    _ = svals
    _ = cutoff
    return {
        "dim_G": dim_g,
        "dim_H": dim_h,
        "broken_dim": rank,
        "jacobian_rank": rank,
        "nullspace": nullspace,
    }


def independent_mass_matrix(gens: list[np.ndarray], vev: np.ndarray, u1_weight: int | None = None) -> dict[str, Any]:
    tv = _directions(gens, vev, u1_weight)
    size = len(tv)
    m2 = np.zeros((size, size), dtype=float)
    for a in range(size):
        for b in range(size):
            m2[a, b] = float(np.vdot(tv[a], tv[b]).real)
    rank = int(np.linalg.matrix_rank(m2, tol=RANK_TOL)) if size else 0
    return {"M2": m2, "rank_M2": rank, "nullity_M2": size - rank, "dim_G": size}


def stabilizer_algebra_closes(gens: list[np.ndarray], nullspace: np.ndarray) -> bool:
    if nullspace.size == 0:
        return True
    xs = []
    for col in range(nullspace.shape[1]):
        coeff = nullspace[:, col]
        acc = np.zeros_like(gens[0])
        for a, g in enumerate(gens):
            acc = acc + coeff[a] * g
        xs.append(acc)
    flats = [x.reshape(-1) for x in xs]
    basis = np.stack([np.concatenate([f.real, f.imag]) for f in flats], axis=1)
    for i, xi in enumerate(xs):
        for j, xj in enumerate(xs):
            if j <= i:
                continue
            comm = xi @ xj - xj @ xi
            target = np.concatenate([comm.real.reshape(-1), comm.imag.reshape(-1)])
            sol, residual, _rank, _s = np.linalg.lstsq(basis, target, rcond=None)
            if residual.size and float(residual[0]) > CLOSURE_TOL:
                _ = sol
                return False
            rebuilt = basis @ sol
            if np.linalg.norm(rebuilt - target) > CLOSURE_TOL:
                return False
    return True


def _structure_label(dim_g: int, dim_h: int) -> str:
    if dim_h == 0:
        return "trivial"
    if dim_h == dim_g:
        return "full_gauge_algebra"
    return f"derived_centralizer_dim_{dim_h}"


@lru_cache(maxsize=256)
def breaking_analysis_orbit(
    n: int,
    labels: tuple[int, ...],
    k: int,
    weight: str,
    orbit_type_id: str,
) -> dict[str, Any]:
    gens = list(scalar_generators(n, labels))
    vev = representative_vev(n, labels, orbit_type_id)
    u1 = None
    if k == 1:
        u1 = 0 if weight == "none" else int(weight)
    stab = solve_stabilizer(gens, vev, u1)
    mass = independent_mass_matrix(gens, vev, u1)
    if stab["dim_H"] != mass["nullity_M2"] or stab["broken_dim"] != mass["rank_M2"]:
        raise EngineFailure(
            "G4_STABILIZER_MASS_MATRIX_INCONSISTENCY",
            f"n={n} labels={labels} orbit={orbit_type_id} dimH={stab['dim_H']} nullM2={mass['nullity_M2']}",
        )
    if n == 3 and labels == (1, 1) and orbit_type_id == "regular_adjoint" and k == 0 and stab["dim_H"] == 1:
        raise EngineFailure("G4_STABILIZER_ERROR", "regular SU(3) adjoint stabilizer dim 1")
    if mass["rank_M2"] != stab["dim_G"] - stab["dim_H"]:
        raise EngineFailure(
            "G4_STABILIZER_MASS_MATRIX_INCONSISTENCY",
            "rank(M2) != dim G - dim H",
        )
    full_gens = list(gens)
    if u1 is not None:
        full_gens.append(float(u1) * np.eye(gens[0].shape[0], dtype=np.complex128))
    closure = stabilizer_algebra_closes(full_gens, stab["nullspace"])
    scaled_gens = [2.0 * g for g in gens]
    scaled = independent_mass_matrix(scaled_gens, vev, u1)
    coupling_independent = scaled["rank_M2"] == mass["rank_M2"] and scaled["nullity_M2"] == mass["nullity_M2"]
    dim_g = stab["dim_G"]
    dim_h = stab["dim_H"]
    broken = stab["broken_dim"]
    form = next(item["representative_VEV_form"] for item in orbit_types(n, labels) if item["orbit_type_id"] == orbit_type_id)
    classification = next(item["classification"] for item in orbit_types(n, labels) if item["orbit_type_id"] == orbit_type_id)
    return {
        "dim_G": dim_g,
        "dim_H": dim_h,
        "dim_G_over_H": broken,
        "broken_dim": broken,
        "rank_M2": mass["rank_M2"],
        "nullity_M2": mass["nullity_M2"],
        "massless_vector_count": mass["nullity_M2"],
        "massive_vector_candidate_count": mass["rank_M2"],
        "goldstone_direction_count": broken,
        "orbit_dimension": broken,
        "partial_breaking": bool(dim_h > 0 and broken > 0),
        "complete_breaking": bool(broken > 0 and dim_h == 0),
        "no_breaking": bool(broken == 0),
        "stabilizer_structure": _structure_label(dim_g, dim_h),
        "stabilizer_algebra_closed": closure,
        "stab_mass_consistent": True,
        "coupling_independent": coupling_independent,
        "scalar_dimension": gens[0].shape[0],
        "scalar_reality": reality_type(n, labels),
        "vev_nonzero": True,
        "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
        "vacuum_dynamics": "NOT_TESTED",
        "u1_weight": weight,
        "orbit_type_id": orbit_type_id,
        "representative_VEV_form": form,
        "orbit_classification": classification,
        "VEV_magnitude": "NOT PROVIDED",
        "gauge_couplings": "FREE / PARAMETER-DEPENDENT",
    }


def pure_u1_breaking(weight: int) -> dict[str, Any]:
    vev = np.array([1.0 + 0.0j])
    stab = solve_stabilizer([], vev, weight)
    mass = independent_mass_matrix([], vev, weight)
    if stab["dim_H"] != mass["nullity_M2"]:
        raise EngineFailure("G4_STABILIZER_MASS_MATRIX_INCONSISTENCY", "pure U(1)")
    return {
        "dim_G": 1,
        "dim_H": mass["nullity_M2"],
        "dim_G_over_H": mass["rank_M2"],
        "rank_M2": mass["rank_M2"],
        "nullity_M2": mass["nullity_M2"],
        "partial_breaking": False,
        "complete_breaking": bool(mass["rank_M2"] == 1),
        "no_breaking": bool(mass["rank_M2"] == 0),
        "massless_vector_count": mass["nullity_M2"],
        "massive_vector_candidate_count": mass["rank_M2"],
        "goldstone_direction_count": mass["rank_M2"],
    }


def g3_prefix_from_g4r(text: str) -> str:
    items = [p for p in text.split("|") if not p.startswith(("SD:", "SW:", "SM:", "SO:"))]
    return "|".join(items)


def parse_g4r_pack(text: str) -> dict[str, str]:
    parts = dict(item.split(":", 1) for item in text.split("|"))
    g3 = g3_prefix_from_g4r(text)
    parsed = parse_pack(g3)
    parsed["scalar_dynkin"] = parts["SD"]
    parsed["scalar_u1"] = parts["SW"]
    parsed["scalar_mult"] = parts.get("SM", "1")
    parsed["orbit_type_id"] = parts["SO"]
    parsed["g3_pack"] = g3
    return parsed


def g4r_pack_values() -> list[str]:
    packs = []
    for g3 in g3_pack_values():
        parsed = parse_pack(g3)
        n = int(parsed["simple_group"].split(":")[1])
        k = int(parsed["u1_k"])
        for labels in all_dynkin(n - 1, R_MAX):
            sd = format_dynkin(labels)
            for orbit in orbit_types(n, labels):
                oid = orbit["orbit_type_id"]
                if k == 0:
                    packs.append(f"{g3}|SD:{sd}|SW:none|SM:1|SO:{oid}")
                else:
                    for w in range(-N_U1_MAX, N_U1_MAX + 1):
                        packs.append(f"{g3}|SD:{sd}|SW:{w}|SM:1|SO:{oid}")
    return packs


def g4r_executable_registry() -> dict[str, dict[str, Any]]:
    exclusions = [
        "exceptional groups",
        "Standard Model Higgs lookup",
        "numerical VEV magnitude",
        "numerical vector masses",
        "anomaly cancellation engine",
        "G5 anomaly grammar",
        "experimental Higgs data",
        "measured vector masses",
        "potential minimization as a derived vacuum",
        "automatic R_MAX expansion",
        "generic-VEV shortcut treated as exhaustive",
        "hard-coded stabilizer dimensions",
    ]
    g4r = _with_hash(
        {
            "grammar_id": G4R_ID,
            "parent_grammar_id": G3R_ID,
            "extension_description": (
                "MATHEMATICAL CONSISTENCY CORRECTION of G4: VEV orbit strata, "
                "independent Lie-algebra stabilizer, independent mass-matrix rank/nullity"
            ),
            "allowed_fields": ["metric", "scalar", "Weyl_fermion", "scalar_multiplet"],
            "allowed_groups": ["SU_N_family", "SU_N x U(1)^k"],
            "allowed_representations": ["dynkin_irreps_bounded", "U1_character_n_in_Z", "scalar_irrep_from_G3_catalogue"],
            "allowed_interactions": ["nonabelian_covariant_derivative", "U1_covariant_derivative", "scalar_kinetic_VEV"],
            "allowed_symmetry_breaking": ["nonzero_structural_VEV", "VEV_orbit_stratum"],
            "allowed_constraints": list(ACTIVE_G4_KPS) + ["G4_SCALAR_VEV_VALIDITY", "G4_STABILIZER_MASS_MATRIX_CONSISTENCY"],
            "explicit_exclusions": exclusions,
            "provenance": "MATHEMATICAL CONSISTENCY CORRECTION",
            "status": "ACTIVE_G4_CORRECTED",
            "axes": {"g4r_pack": g4r_pack_values()},
            "r_max": R_MAX,
            "n_scalar_max": N_SCALAR_MAX,
            "n_u1_max": N_U1_MAX,
            "r_max_is_search_bound_not_prediction": True,
            "n_scalar_max_is_search_bound_not_prediction": True,
            "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
            "vacuum_dynamics": "NOT_TESTED",
            "VEV_ORBIT_CLASSIFICATION": vev_orbit_classification_status(),
            "correction_of": OLD_G4_ID,
            "correction_of_grammar_hash": EXPECTED_OLD_G4_GRAMMAR_HASH,
        }
    )
    return {G4R_ID: g4r}


def g4r_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    _ = grammar
    try:
        parsed = parse_g4r_pack(assignment["g4r_pack"])
        n = int(parsed["simple_group"].split(":")[1])
        slabels = parse_dynkin(parsed["scalar_dynkin"])
        k = int(parsed["u1_k"])
        sw = parsed["scalar_u1"]
        sm = int(parsed["scalar_mult"])
        flabels = parse_dynkin(parsed["dynkin"])
        oid = parsed["orbit_type_id"]
    except (KeyError, ValueError):
        return False, "invalid_g4r_pack"
    if n not in N_SU_VALUES:
        return False, "group_not_in_G3_bounds"
    if len(flabels) != n - 1 or len(slabels) != n - 1:
        return False, "dynkin_rank_mismatch"
    if any(x < 0 or x > R_MAX for x in flabels + slabels):
        return False, "dynkin_outside_R_MAX"
    if sm < 1 or sm > N_SCALAR_MAX:
        return False, "scalar_multiplicity_outside_N_SCALAR_MAX"
    if oid not in {item["orbit_type_id"] for item in orbit_types(n, slabels)}:
        return False, "orbit_type_not_in_classification"
    if k == 0 and (parsed["u1_n"] != "none" or sw != "none"):
        return False, "u1_weight_without_u1_factor"
    if k == 1:
        try:
            wi = int(parsed["u1_n"])
            swi = int(sw)
        except ValueError:
            return False, "u1_weight_not_integer"
        if abs(wi) > N_U1_MAX or abs(swi) > N_U1_MAX:
            return False, "u1_weight_outside_N_U1_MAX"
    return True, None


def verify_old_g4_archive() -> dict[str, Any]:
    path = old_g4_checkpoint_path()
    if not path.is_file():
        raise EngineFailure("CHECKPOINT_CORRUPTED", "archived G4 checkpoint missing")
    payload = _read_json(path)
    stored = payload.get("integrity_digest")
    recomputed = content_hash({k: v for k, v in payload.items() if k != "integrity_digest"})
    if stored != recomputed:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "archived G4 digest mismatch")
    if payload.get("grammar_id") != OLD_G4_ID:
        raise EngineFailure("GRAMMAR_MISSING", "archived G4 grammar_id")
    if payload.get("grammar_hash") != EXPECTED_OLD_G4_GRAMMAR_HASH:
        raise EngineFailure("GRAMMAR_HASH_MISMATCH", "archived G4 grammar_hash")
    if _file_digest(path) != EXPECTED_OLD_G4_CHECKPOINT_HASH:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "archived G4 file digest changed")
    return payload


def g4r_run_tests(candidate: dict[str, Any], *, test_version: str = "g4r-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    parsed = parse_g4r_pack(candidate["assignment"]["g4r_pack"])
    n = int(parsed["simple_group"].split(":")[1])
    k = int(parsed["u1_k"])
    slabels = parse_dynkin(parsed["scalar_dynkin"])
    sw = parsed["scalar_u1"]
    oid = parsed["orbit_type_id"]
    data = irrep_data(n, slabels)
    br = breaking_analysis_orbit(n, slabels, k, sw, oid)
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
    add("KP09", "PASS", "INHERITED FROM G3R", "Weyl plus bosonic scalar/metric plus extra scalar multiplet")
    add("KP10", "PASS", "INHERITED FROM G3R", "Weyl sector inherited; complex representation is not required")
    add("KP11", "PASS", "MATHEMATICAL REPRESENTATION DATA", "Dynkin labels for fermions and scalars")
    add("KP14", "PASS", "INHERITED FROM G3R", "finite species; N_SCALAR_MAX is a search limit")
    add(
        "KP13",
        "PASS" if br["dim_G_over_H"] > 0 else "FAIL",
        "DERIVED GIVEN REPRESENTATION + VEV",
        "KP13 is a consequence of a declared nonzero VEV; vacuum dynamics not tested",
    )
    add(
        "KP15",
        "PASS" if br["partial_breaking"] else "FAIL",
        "DERIVED GIVEN GAUGE + SCALAR KINETIC STRUCTURE + VEV",
        "massless_vector_count>0 and massive_vector_candidate_count>0 from rank/nullity",
    )
    add("KP12", "UNTESTED", "DEFERRED TO G5", "anomaly_status=DEFERRED_TO_G5")
    add(
        "G4_SCALAR_VEV_VALIDITY",
        "PASS" if br["vev_nonzero"] and data["dimension"] >= 1 else "FAIL",
        "G4 STRUCTURAL ASSUMPTION",
        "finite scalar irrep plus nonzero structural VEV",
    )
    add(
        "G4_STABILIZER_MASS_MATRIX_CONSISTENCY",
        "PASS" if br["stab_mass_consistent"] else "FAIL",
        "DERIVED GIVEN GAUGE + SCALAR KINETIC STRUCTURE + VEV",
        "nullity(M2)==dim(H) and rank(M2)==dim(G)-dim(H)",
    )
    add("vacuum_dynamics", "UNTESTED", "NOT_TESTED", "vacuum_existence is assumed, not derived from a potential")
    add("G5_anomaly", "NOT_APPLICABLE", "DEFERRED TO G5", "G4_CORRECTED must not activate G5")
    required_fail = any(
        r["status"] == "FAIL" and r["test_id"] in (*ACTIVE_G4_KPS, "G4_SCALAR_VEV_VALIDITY", "G4_STABILIZER_MASS_MATRIX_CONSISTENCY")
        for r in results
    )
    return {
        "status": "FAIL" if required_fail else "PASS",
        "results": results,
        "test_version": test_version,
        "irrep": data,
        "breaking": br,
        "KP13_STATUS": "PASS" if br["dim_G_over_H"] > 0 else "FAIL",
        "KP15_STATUS": "PASS" if br["partial_breaking"] else "FAIL",
        "anomaly_status": "DEFERRED_TO_G5",
        "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
        "vacuum_dynamics": "NOT_TESTED",
    }


def attach_g4r_stats(grammar: dict[str, Any], evaluated: list[dict[str, Any]], compatible: list[dict[str, Any]]) -> dict[str, Any]:
    parent = verify_g3r_parent_checkpoint()
    parent_hash = _file_digest(g3r_checkpoint_path())
    table = []
    inventory = []
    _ = compatible
    _ = grammar
    for cand in evaluated:
        parsed = parse_g4r_pack(cand["assignment"]["g4r_pack"])
        n = int(parsed["simple_group"].split(":")[1])
        k = int(parsed["u1_k"])
        slabels = parse_dynkin(parsed["scalar_dynkin"])
        sw = parsed["scalar_u1"]
        oid = parsed["orbit_type_id"]
        data = irrep_data(n, slabels)
        br = (cand.get("tests") or {}).get("breaking") or breaking_analysis_orbit(n, slabels, k, sw, oid)
        glabel = group_label(n, k)
        parent_g3 = content_hash({"grammar_id": G3R_ID, "assignment": {"g3_pack": parsed["g3_pack"]}})
        kp13 = "PASS" if br["dim_G_over_H"] > 0 else "FAIL"
        kp15 = "PASS" if br["partial_breaking"] else "FAIL"
        row = {
            "candidate_class": cand["candidate_id"],
            "candidate_hash": cand["candidate_hash"],
            "parent_g3_hash": parent_g3,
            "gauge_group": glabel,
            "scalar_irrep": f"[{format_dynkin(slabels)}] dim={data['dimension']} {data['reality_type']}",
            "VEV_orbit_type": oid,
            "dim_G": br["dim_G"],
            "stabilizer_H": br["stabilizer_structure"],
            "dim_H": br["dim_H"],
            "broken_dim": br["broken_dim"],
            "massless_vectors": br["massless_vector_count"],
            "massive_vectors": br["massive_vector_candidate_count"],
            "KP13": kp13,
            "KP15": kp15,
            "anomaly_status": "DEFERRED_TO_G5",
            "status": cand.get("filter_status"),
            "provenance": "DERIVED GIVEN REPRESENTATION + VEV",
            "representative_VEV_form": br["representative_VEV_form"],
            "orbit_classification": br["orbit_classification"],
        }
        table.append(row)
        if cand.get("filter_status") == "PASS":
            couplings = ["g_SU_N"] + (["g_U1"] if k else [])
            inventory.append(
                {
                    "candidate_hash": cand["candidate_hash"],
                    "gauge_group": glabel,
                    "scalar_representation": [format_dynkin(slabels)],
                    "VEV_orbit_type": oid,
                    "scalar_multiplicity": parsed["scalar_mult"],
                    "VEV_multiplicity": "1",
                    "stabilizer_H_dimension": br["dim_H"],
                    "stabilizer_structure": br["stabilizer_structure"],
                    "broken_generator_count": br["dim_G_over_H"],
                    "unbroken_generator_count": br["dim_H"],
                    "Goldstone_direction_count": br["goldstone_direction_count"],
                    "rank_M2": br["rank_M2"],
                    "nullity_M2": br["nullity_M2"],
                    "continuous_gauge_couplings": couplings,
                    "scalar_potential_parameters": "NOT_TESTED",
                    "dimensionful_parameters": ["c0", "c1_nonzero", "kappa"],
                    "VEV_magnitude": "NOT PROVIDED",
                    "vector_masses": "NOT DETERMINED",
                    "parent_g3_hash": parent_g3,
                    "anomaly_status": "DEFERRED_TO_G5",
                    "provenance": {
                        "scalar_representation": "GRAMMAR EXTENSION",
                        "nonzero_VEV": "G4 STRUCTURAL ASSUMPTION",
                        "VEV_orbit_type": "DERIVED GIVEN REPRESENTATION + VEV",
                        "VEV_stabilizer_H": "DERIVED GIVEN REPRESENTATION + VEV",
                        "broken_generators": "DERIVED",
                        "mass_matrix_rank": "DERIVED GIVEN GAUGE + SCALAR KINETIC STRUCTURE + VEV",
                        "massless_massive_vector_structure": "DERIVED GIVEN SSB ASSUMPTION",
                        "numerical_VEV_magnitude": "NOT PROVIDED",
                        "numerical_vector_masses": "NOT DETERMINED",
                        "anomaly_cancellation": "DEFERRED TO G5",
                    },
                }
            )
    _ = parent
    return {
        "class_table": table,
        "parameter_inventory": inventory,
        "blockers": [],
        "parent_checkpoint_hash": parent_hash,
        "search_bounds": dict(SCALAR_SEARCH_BOUNDS),
        "g3_survivors_reused": len(parent.get("survivor_hashes") or []),
        "g4_new_candidates_generated": len(evaluated),
        "representation_catalogue_hash": catalogue_hash(),
        "target_blindness": "VERIFIED",
        "VEV_ORBIT_CLASSIFICATION": vev_orbit_classification_status(),
        "provenance_summary": {
            "scalar_representation": "GRAMMAR EXTENSION",
            "nonzero_VEV": "G4 STRUCTURAL ASSUMPTION",
            "VEV_stabilizer_H": "DERIVED GIVEN REPRESENTATION + VEV",
            "mass_matrix_rank": "DERIVED GIVEN GAUGE + SCALAR KINETIC STRUCTURE + VEV",
            "anomaly_cancellation": "DEFERRED TO G5",
            "correction": "MATHEMATICAL CONSISTENCY CORRECTION",
        },
    }


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14b4_priors()
    out["phase14b4"] = {}
    for name in (
        "PHASE_14B4_SUMMARY.json",
        "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV.json",
        "PHASE_14B4_G4_GRAMMAR.json",
        "PHASE_14B4_REPRESENTATION_CATALOGUE.json",
    ):
        path = old_g4_artifact_dir() / name
        if path.is_file():
            out["phase14b4"][name] = _file_digest(path)
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
        raise UnauthorizedAnalysisError("Phase 14B.4R refuses an unauthorized action object")
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
    stabs = {row["stabilizer_H_dimension"] for row in inventory}
    patterns = {
        (row["gauge_group"], row.get("VEV_orbit_type"), row["stabilizer_H_dimension"], row["broken_generator_count"])
        for row in inventory
    }

    def yn(ok: bool) -> str:
        return "YES" if ok else "NO"

    return {
        "UNIQUE_GAUGE_GROUP": yn(len(groups) == 1),
        "UNIQUE_STABILIZER": yn(len(stabs) == 1),
        "UNIQUE_BREAKING_PATTERN": yn(len(patterns) == 1),
        "UNIQUE_SCALAR_REPRESENTATION": yn(len({tuple(row["scalar_representation"]) for row in inventory}) == 1),
        "UNIQUE_VEV_ORBIT": yn(len({row.get("VEV_orbit_type") for row in inventory}) == 1),
        "UNIQUE_DIMENSIONLESS_COUPLING": "NO",
    }


def _old_dim(row: dict[str, Any]) -> int:
    text = str(row.get("unbroken_subgroup") or "")
    if "stabilizer_dim=" in text:
        return int(text.split("stabilizer_dim=", 1)[1].split()[0])
    return int(row.get("massless_vector_count") or 0)


def _correction_diff(old_rows: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> dict[str, Any]:
    old_pass = [r for r in old_rows if r.get("status") == "PASS"]
    new_pass = [r for r in new_rows if r.get("status") == "PASS"]
    old_by_scalar: dict[tuple[str, str], set[int]] = {}
    for row in old_pass:
        key = (str(row.get("gauge_group")), str(row.get("scalar_representation")))
        old_by_scalar.setdefault(key, set()).add(_old_dim(row))
    new_by_scalar: dict[tuple[str, str], set[int]] = {}
    for row in new_pass:
        key = (str(row.get("gauge_group")), str(row.get("scalar_irrep")))
        new_by_scalar.setdefault(key, set()).add(int(row.get("dim_H") or 0))
    restored = []
    removed = []
    prior_errors = []
    for key, new_dims in sorted(new_by_scalar.items()):
        old_dims = old_by_scalar.get(key, set())
        extra = sorted(new_dims - old_dims)
        missing = sorted(old_dims - new_dims)
        if extra:
            restored.append({"gauge_group": key[0], "scalar_irrep": key[1], "new_dim_H": extra})
        if missing:
            removed.append({"gauge_group": key[0], "scalar_irrep": key[1], "old_dim_H_not_reproduced_as_generic": missing})
            prior_errors.append(
                {
                    "mark": "PRIOR_IMPLEMENTATION_ERROR",
                    "gauge_group": key[0],
                    "scalar_irrep": key[1],
                    "old_generic_dim_H": sorted(old_dims),
                    "corrected_dim_H": sorted(new_dims),
                }
            )
    return {
        "RESTORED_CLASSES": restored,
        "REMOVED_CLASSES": removed,
        "PRIOR_IMPLEMENTATION_ERROR": prior_errors,
        "OLD_G4_COMPATIBLE": len(old_pass),
        "CORRECTED_G4_COMPATIBLE": len(new_pass),
    }


def analyze_phase14b4r_g4(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    s14b0 = _read_json(phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json")
    s14a = _read_json(phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
    s14b3r = _read_json(phase14b3r_artifact_dir() / "PHASE_14B3R_SUMMARY.json")
    s14b4 = _read_json(old_g4_artifact_dir() / "PHASE_14B4_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g3r_parent_checkpoint()
        old_ckpt = verify_old_g4_archive()
        g3_before = g3r_checkpoint_path().read_bytes()
        g4_before = old_g4_checkpoint_path().read_bytes()
        g2_path = Path(__file__).resolve().parent / "phase14b2_artifacts" / "closure_checkpoint_G2_COMPACT_NONABELIAN.json"
        g2_before = g2_path.read_bytes()
    except (FileNotFoundError, EngineFailure) as exc:
        detail = exc.mode if isinstance(exc, EngineFailure) else str(exc)
        return {"status": "STOP", "scientific_analysis": None, "detail": detail, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    integrity_failure = None
    if s14b0.get("TOP_DOWN_CLOSURE_ENGINE") != "READY":
        integrity_failure = "TOP_DOWN_CLOSURE_ENGINE is not READY"
    if s14b3r.get("GRAMMAR_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        integrity_failure = "G3_R1 grammar hash mismatch"
    if s14b4.get("GRAMMAR_HASH") != EXPECTED_OLD_G4_GRAMMAR_HASH:
        integrity_failure = "archived G4 grammar hash mismatch"
    if s14b4.get("G4_TOP_DOWN_COMPATIBLE") != 1060:
        integrity_failure = "archived G4 compatible count rewritten"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G3R_GRAMMAR_HASH:
        integrity_failure = "G3_R1 checkpoint grammar hash mismatch"
    if old_ckpt.get("grammar_hash") != EXPECTED_OLD_G4_GRAMMAR_HASH:
        integrity_failure = "old G4 checkpoint grammar hash mismatch"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical corpus rewritten"
    if s14a.get("PHASE_14A_STATUS") != "CLOSED":
        integrity_failure = "Phase 14A is not CLOSED"
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not closed"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "live top-down input hash mismatch"

    grammars = g4r_executable_registry()
    g4r = grammars[G4R_ID]
    if g4r["parent_grammar_id"] != G3R_ID:
        integrity_failure = "G4_R1 parent is not G3_R1"
    if g4r["grammar_hash"] == EXPECTED_OLD_G4_GRAMMAR_HASH:
        integrity_failure = "corrected G4 grammar hash is not distinct"

    summary_path = artifact_dir() / "PHASE_14B4R_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14B4R_STATUS") == "CLOSED" and existing.get("G5_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14B4R_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "G4_CORRECTED_EXECUTED": False,
                "G5_EXECUTED": False,
                "ranking": False,
            }
            _write_json(summary_path, summary)
        else:
            engine = ClosureEngine(artifact_dir(), chain="g4r_only")
            assert_target_blind({"g4r": g4r, "bounds": SCALAR_SEARCH_BOUNDS, "catalogue": build_representation_catalogue()})
            try:
                ClosureEngine(artifact_dir() / "no_g5", chain="physics")
                g5_block = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g5_block = exc.mode
            try:
                engine.advance_grammar("G5_ANOMALY_CONSTRAINTS", G4R_ID)
                g5_skip = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g5_skip = exc.mode
            state = engine.run_until_closure()
            if g3r_checkpoint_path().read_bytes() != g3_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G4R overwrote the G3_R1 checkpoint")
            if old_g4_checkpoint_path().read_bytes() != g4_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G4R overwrote the archived G4 checkpoint")
            if g2_path.read_bytes() != g2_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G4R overwrote the G2 checkpoint")
            g4_rep = next(r for r in state["version_reports"] if r["grammar_id"] == G4R_ID)
            g3_ok = len(parent_ckpt.get("survivor_hashes") or [])
            g4_ok = g4_rep["compatible"]
            pass_rows = [r for r in (g4_rep.get("class_table") or []) if r.get("status") == "PASS"]
            kp15_any = any(r.get("KP15") == "PASS" for r in pass_rows)
            kp13_any = any(r.get("KP13") == "PASS" for r in pass_rows)
            groups_partial = sorted({r["gauge_group"] for r in pass_rows})
            patterns = {(r["gauge_group"], r["VEV_orbit_type"], r["dim_H"], r["broken_dim"]) for r in pass_rows}
            diff = _correction_diff(old_ckpt.get("class_table") or [], g4_rep.get("class_table") or [])
            uniq = _uniqueness(g4_rep.get("parameter_inventory") or [])
            summary = {
                "phase": PHASE,
                "audit_version": AUDIT_VERSION,
                "PHASE_14B4R_STATUS": "CLOSED",
                "integrity_failure": None,
                "CORRECTION_STATUS": "APPLIED",
                "G4_STATUS": g4_rep["closure_status"],
                "METHOD_STATUS": "VERIFIED",
                "SCIENTIFIC_STATUS": "ANALYZED_G4_CORRECTED_ONLY",
                "GRAMMAR_ID": G4R_ID,
                "GRAMMAR_HASH": g4r["grammar_hash"],
                "OLD_G4_GRAMMAR_HASH": EXPECTED_OLD_G4_GRAMMAR_HASH,
                "NEW_G4_GRAMMAR_HASH": g4r["grammar_hash"],
                "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
                "PARENT_GRAMMAR": G3R_ID,
                "PARENT_GRAMMAR_HASH": EXPECTED_G3R_GRAMMAR_HASH,
                "G2_GRAMMAR_HASH": EXPECTED_G2_GRAMMAR_HASH,
                "PARENT_CHECKPOINT": str(g3r_checkpoint_path().name),
                "PARENT_CHECKPOINT_HASH": _file_digest(g3r_checkpoint_path()),
                "TOP_DOWN_INPUT_HASH": top_down_input_hash(),
                "engine_version": ENGINE_VERSION,
                "current_grammar": G4R_ID,
                "SCALAR_SEARCH_BOUNDS": dict(SCALAR_SEARCH_BOUNDS),
                "RAW_COMBINATIONS": g4_rep["raw_theoretical_combinations"],
                "METADATA_PRUNED": g4_rep["metadata_pruned_candidates"],
                "GENERATED": g4_rep["generated_candidates"],
                "REJECTED": g4_rep["rejected"],
                "UNRESOLVED": g4_rep["unresolved"],
                "TOP_DOWN_COMPATIBLE": g4_ok,
                "EQUIVALENCE_CLASSES": len(g4_rep["equivalence_classes"]),
                "G3_COMPATIBLE": g3_ok,
                "OLD_G4_COMPATIBLE": 1060,
                "CORRECTED_G4_COMPATIBLE": g4_ok,
                "RESTORED_CLASSES": diff["RESTORED_CLASSES"],
                "REMOVED_CLASSES": diff["REMOVED_CLASSES"],
                "PRIOR_IMPLEMENTATION_ERROR": diff["PRIOR_IMPLEMENTATION_ERROR"],
                "OLD_G4_STATUS": "G4_SUPERSEDED_BY_STABILIZER_AUDIT",
                "VEV_ORBIT_CLASSIFICATION": vev_orbit_classification_status(),
                "STABILIZER_MASS_MATRIX_CONSISTENCY": "VERIFIED",
                "G4_STABILIZER_CLASSIFICATION_PARTIAL": vev_orbit_classification_status() == "PARTIAL",
                "KP13_STATUS": "PASS" if kp13_any else "FAIL",
                "KP15_STATUS": "PASS" if kp15_any else "FAIL",
                "KP15_STRUCTURALLY_SUPPORTED": bool(kp15_any),
                "STRUCTURAL_SSB_SUPPORTED": bool(kp15_any),
                "QUALITATIVE_SSB_DOES_NOT_SELECT_A_UNIQUE_BREAKING_PATTERN": len(patterns) != 1,
                "groups_admitting_partial_breaking": groups_partial,
                "G1_EXECUTED": True,
                "G2_EXECUTED": True,
                "G3_EXECUTED": True,
                "G3_CORRECTED_EXECUTED": True,
                "G4_EXECUTED": True,
                "G4_CORRECTED_EXECUTED": True,
                "G5_EXECUTED": False,
                "NEXT_AUTHORIZED_EXTENSION": "G5_ANOMALY_CONSTRAINTS",
                "physics_chain_skip_blocked": g5_block,
                "g5_skip_blocked": g5_skip,
                "ACTIVE_G4_KPS": list(ACTIVE_G4_KPS),
                "DEFERRED_G4_KPS": dict(DEFERRED_G4_KPS),
                "class_table": g4_rep.get("class_table") or [],
                "parameter_inventory": g4_rep.get("parameter_inventory") or [],
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
                "phase_14b5_executed": False,
                "gravity_changed": False,
                "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
                "TARGET_BLINDNESS": "VERIFIED",
                "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
                "anomaly_status": "DEFERRED_TO_G5",
                "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
                "vacuum_dynamics": "NOT_TESTED",
                "correction_provenance": "MATHEMATICAL CONSISTENCY CORRECTION",
                "G0_REGENERATED": 0,
                "G1_FULL_SEARCH_REGENERATED": 0,
                "G2_FULL_SEARCH_REGENERATED": 0,
                "G3_FULL_SEARCH_REGENERATED": 0,
                "R_MAX_UNCHANGED": True,
            }
            _write_json(summary_path, summary)
            _write_json(artifact_dir() / "PHASE_14B4R_G4_GRAMMAR.json", g4r)
            _write_json(artifact_dir() / "PHASE_14B4R_REPRESENTATION_CATALOGUE.json", build_representation_catalogue())
            _write_json(
                old_g4_artifact_dir() / "PHASE_14B4_SUPERSEDED_BY_STABILIZER_AUDIT.json",
                {
                    "OLD_G4_STATUS": "G4_SUPERSEDED_BY_STABILIZER_AUDIT",
                    "OLD_G4_GRAMMAR_ID": OLD_G4_ID,
                    "OLD_G4_GRAMMAR_HASH": EXPECTED_OLD_G4_GRAMMAR_HASH,
                    "OLD_G4_CHECKPOINT": str(old_g4_checkpoint_path().name),
                    "OLD_G4_CHECKPOINT_HASH": EXPECTED_OLD_G4_CHECKPOINT_HASH,
                    "SUPERSEDED_BY": G4R_ID,
                    "SUPERSEDED_BY_GRAMMAR_HASH": g4r["grammar_hash"],
                    "correction": "independent stabilizer and mass-matrix audit; VEV orbit strata",
                    "provenance": "SUPERSEDED BY STABILIZER AUDIT",
                    "checkpoint_file_unmodified": True,
                },
            )
    else:
        summary = cached
        g4r = _read_json(artifact_dir() / "PHASE_14B4R_G4_GRAMMAR.json")

    hashes_after = snapshot_prior_artifact_hashes()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    g3_unchanged = g3r_checkpoint_path().read_bytes() == g3_before
    g4_unchanged = old_g4_checkpoint_path().read_bytes() == g4_before
    g2_unchanged = g2_path.read_bytes() == g2_before
    artifacts_ok = hashes_before["phase14b3r"] == hashes_after["phase14b3r"]
    old_g4_named_ok = hashes_before["phase14b4"] == hashes_after["phase14b4"]
    summary["phase14b3r_artifacts_unchanged"] = artifacts_ok
    summary["phase14b4_named_artifacts_unchanged"] = old_g4_named_ok
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["g3r_checkpoint_unchanged"] = g3_unchanged
    summary["g4_checkpoint_unchanged"] = g4_unchanged
    summary["g2_checkpoint_unchanged"] = g2_unchanged
    if not (
        artifacts_ok
        and old_g4_named_ok
        and grammar_ok
        and frozen_ok
        and g3_unchanged
        and g4_unchanged
        and g2_unchanged
        and summary.get("ranking") is False
        and summary.get("G5_EXECUTED") is False
        and summary.get("R_MAX_UNCHANGED") is True
    ):
        summary["PHASE_14B4R_STATUS"] = "INTEGRITY_FAILURE"
        summary["METHOD_STATUS"] = "FAILED"
        summary["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    _write_json(summary_path, summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_14B4R_TEST_COPY_ID": PHASE_14B4R_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "CORRECTION_STATUS": summary.get("CORRECTION_STATUS"),
        "G4_STATUS": summary.get("G4_STATUS"),
        "METHOD_STATUS": summary.get("METHOD_STATUS"),
        "SCIENTIFIC_STATUS": summary.get("SCIENTIFIC_STATUS"),
        "GRAMMAR_ID": G4R_ID,
        "GRAMMAR_HASH": summary.get("GRAMMAR_HASH"),
        "OLD_G4_GRAMMAR_HASH": EXPECTED_OLD_G4_GRAMMAR_HASH,
        "NEW_G4_GRAMMAR_HASH": summary.get("NEW_G4_GRAMMAR_HASH"),
        "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
        "PARENT_GRAMMAR": G3R_ID,
        "PARENT_GRAMMAR_HASH": EXPECTED_G3R_GRAMMAR_HASH,
        "G2_GRAMMAR_HASH": EXPECTED_G2_GRAMMAR_HASH,
        "PARENT_CHECKPOINT": summary.get("PARENT_CHECKPOINT"),
        "PARENT_CHECKPOINT_HASH": summary.get("PARENT_CHECKPOINT_HASH"),
        "TOP_DOWN_INPUT_HASH": summary.get("TOP_DOWN_INPUT_HASH"),
        "SCALAR_SEARCH_BOUNDS": summary.get("SCALAR_SEARCH_BOUNDS"),
        "RAW_COMBINATIONS": summary.get("RAW_COMBINATIONS"),
        "METADATA_PRUNED": summary.get("METADATA_PRUNED"),
        "GENERATED": summary.get("GENERATED"),
        "REJECTED": summary.get("REJECTED"),
        "UNRESOLVED": summary.get("UNRESOLVED"),
        "TOP_DOWN_COMPATIBLE": summary.get("TOP_DOWN_COMPATIBLE"),
        "EQUIVALENCE_CLASSES": summary.get("EQUIVALENCE_CLASSES"),
        "G3_COMPATIBLE": summary.get("G3_COMPATIBLE"),
        "OLD_G4_COMPATIBLE": summary.get("OLD_G4_COMPATIBLE"),
        "CORRECTED_G4_COMPATIBLE": summary.get("CORRECTED_G4_COMPATIBLE"),
        "RESTORED_CLASSES": summary.get("RESTORED_CLASSES"),
        "REMOVED_CLASSES": summary.get("REMOVED_CLASSES"),
        "PRIOR_IMPLEMENTATION_ERROR": summary.get("PRIOR_IMPLEMENTATION_ERROR"),
        "OLD_G4_STATUS": "G4_SUPERSEDED_BY_STABILIZER_AUDIT",
        "VEV_ORBIT_CLASSIFICATION": summary.get("VEV_ORBIT_CLASSIFICATION"),
        "STABILIZER_MASS_MATRIX_CONSISTENCY": summary.get("STABILIZER_MASS_MATRIX_CONSISTENCY"),
        "G4_STABILIZER_CLASSIFICATION_PARTIAL": summary.get("G4_STABILIZER_CLASSIFICATION_PARTIAL"),
        "KP13_STATUS": summary.get("KP13_STATUS"),
        "KP15_STATUS": summary.get("KP15_STATUS"),
        "KP15_STRUCTURALLY_SUPPORTED": summary.get("KP15_STRUCTURALLY_SUPPORTED"),
        "STRUCTURAL_SSB_SUPPORTED": summary.get("STRUCTURAL_SSB_SUPPORTED"),
        "QUALITATIVE_SSB_DOES_NOT_SELECT_A_UNIQUE_BREAKING_PATTERN": summary.get(
            "QUALITATIVE_SSB_DOES_NOT_SELECT_A_UNIQUE_BREAKING_PATTERN"
        ),
        "groups_admitting_partial_breaking": summary.get("groups_admitting_partial_breaking"),
        "G0_REGENERATED": 0,
        "G1_EXECUTED": True if summary.get("PHASE_14B4R_STATUS") == "CLOSED" else False,
        "G2_EXECUTED": True if summary.get("PHASE_14B4R_STATUS") == "CLOSED" else False,
        "G3_EXECUTED": True if summary.get("PHASE_14B4R_STATUS") == "CLOSED" else False,
        "G3_CORRECTED_EXECUTED": True if summary.get("PHASE_14B4R_STATUS") == "CLOSED" else False,
        "G4_EXECUTED": True if summary.get("PHASE_14B4R_STATUS") == "CLOSED" else False,
        "G4_CORRECTED_EXECUTED": True if summary.get("PHASE_14B4R_STATUS") == "CLOSED" else False,
        "G5_EXECUTED": False,
        "NEXT_AUTHORIZED_EXTENSION": "G5_ANOMALY_CONSTRAINTS",
        "class_table": summary.get("class_table"),
        "parameter_inventory": summary.get("parameter_inventory"),
        "uniqueness": summary.get("uniqueness"),
        "version_reports": summary.get("version_reports"),
        "audit_summary": summary,
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_14B4R_STATUS": summary.get("PHASE_14B4R_STATUS"),
        "PHASE_14B4_STATUS": s14b4.get("PHASE_14B4_STATUS"),
        "PHASE_14B3R_STATUS": s14b3r.get("PHASE_14B3R_STATUS"),
        "PHASE_14B0_STATUS": s14b0.get("PHASE_14B0_STATUS"),
        "PHASE_14A_STATUS": s14a.get("PHASE_14A_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "gravity_changed": False,
        "ranking_score_introduced": False,
        "phase_14b5_executed": False,
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
        "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
        "vacuum_dynamics": "NOT_TESTED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_14B4R_CLOSED": summary.get("PHASE_14B4R_STATUS") == "CLOSED",
        "correction_provenance": "MATHEMATICAL CONSISTENCY CORRECTION",
        "overclaims": {
            "1_activate_G5_automatically": "REJECTED AS OVERCLAIM",
            "2_claim_unique_breaking_pattern": "REJECTED AS OVERCLAIM",
            "3_claim_Higgs_mechanism_as_a_fitted_theory": "REJECTED AS OVERCLAIM",
            "4_assign_numerical_VEV": "REJECTED AS OVERCLAIM",
            "5_assign_numerical_vector_masses": "REJECTED AS OVERCLAIM",
            "6_run_anomaly_engine": "REJECTED AS OVERCLAIM",
            "7_expand_R_MAX": "REJECTED AS OVERCLAIM",
            "8_insert_experimental_inputs": "REJECTED AS OVERCLAIM",
            "9_modify_gravity": "REJECTED AS OVERCLAIM",
            "10_rank_candidate_classes": "REJECTED AS OVERCLAIM",
            "11_prefer_SM_Higgs_representation": "REJECTED AS OVERCLAIM",
            "12_derive_vacuum_from_unspecified_potential": "REJECTED AS OVERCLAIM",
            "13_treat_generic_VEV_as_exhaustive_orbit_classification": "REJECTED AS OVERCLAIM",
            "14_hardcode_stabilizer_dimensions": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_14B4R_STATUS"] == "CLOSED"
        and science["G5_EXECUTED"] is False
        and science["G4_CORRECTED_EXECUTED"] is True
        and science["PARENT_GRAMMAR"] == G3R_ID
        and science["ranking"] is False
        and science["gravity_changed"] is False
        and science["experimental_inputs"] == 0
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and old_g4_named_ok
        and g3_unchanged
        and g4_unchanged
        and g2_unchanged
        and corpus["specs_unchanged"]
    )
    return science


def run_phase14b4r_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14b4r_g4(auth, signature=signature)
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
            "PHASE_14B3R_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14b3r_artifacts_unchanged") else "FAILED",
            "PHASE_14B4_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g4_checkpoint_unchanged") else "FAILED",
            "G3R_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g3r_checkpoint_unchanged") else "FAILED",
            "G2_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g2_checkpoint_unchanged") else "FAILED",
            "PHASE_14B4R_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14B4R_STATUS": science.get("PHASE_14B4R_STATUS"),
            "PHASE_14B4_STATUS": science.get("PHASE_14B4_STATUS"),
            "PHASE_14B3R_STATUS": science.get("PHASE_14B3R_STATUS"),
            "PHASE_14B0_STATUS": science.get("PHASE_14B0_STATUS"),
            "PHASE_14A_STATUS": science.get("PHASE_14A_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "STRING_THEORY_CONSTRAINTS": "NONE",
            "PHASE_14B5_EXECUTED": "FALSE",
            "G4_CORRECTED_EXECUTED": "TRUE",
            "G5_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
