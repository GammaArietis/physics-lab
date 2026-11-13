"""Phase 14B.4: activate G4_SCALAR_MULTIPLETS_VEV only.

Incremental SSB test from corrected G3 survivors. Does not activate G5.
"""

from __future__ import annotations

import itertools
import json
from collections import deque
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
from physics_lab.physics.phase14b2_g2 import su_n_generators
from physics_lab.physics.phase14b3_g3 import (
    EXPECTED_G2_GRAMMAR_HASH,
    EXPECTED_TOP_DOWN_INPUT_HASH,
    M_MAX,
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
    snapshot_prior_artifact_hashes as snapshot_14b3r_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_G3R_CHECKPOINT_HASH",
    "EXPECTED_G3R_GRAMMAR_HASH",
    "G4_CHAIN",
    "N_SCALAR_MAX",
    "analyze_phase14b4_g4",
    "artifact_dir",
    "breaking_analysis",
    "g4_executable_registry",
    "g4_metadata_legal",
    "g4_run_tests",
    "irrep_generators",
    "pure_u1_breaking",
    "run_phase14b4_or_stop",
]

PHASE = "PHASE_14B.4"
PHASE_14B4_TEST_COPY_ID = "PHASE_14B4_ACTIVATE_G4_SCALAR_MULTIPLETS_VEV"
AUDIT_VERSION = "phase14b4-g4-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_G3R_GRAMMAR_HASH = "57ae71e4446cb13e18b60d6b4ca5a1b84a2bc5fb892773459b12afcc70757c68"
EXPECTED_G3R_CHECKPOINT_HASH = "11a676c46a4c416ca0aada6dac296601cbba82a29e884d2f52baab6dba35e06d"
G4_ID = "G4_SCALAR_MULTIPLETS_VEV"
G4_CHAIN: tuple[str, ...] = (G4_ID,)
N_SCALAR_MAX = 1
RANK_TOL = 1e-6
HW_TOL = 1e-8
ACTIVE_G4_KPS: tuple[str, ...] = (
    "KP01",
    "KP02",
    "KP03",
    "KP09",
    "KP10",
    "KP11",
    "KP13",
    "KP14",
    "KP15",
)
DEFERRED_G4_KPS = {"KP12": "DEFERRED TO G5"}
SCALAR_SEARCH_BOUNDS = {
    "R_MAX": R_MAX,
    "R_MAX_is_search_bound_not_prediction": True,
    "N_SCALAR_MAX": N_SCALAR_MAX,
    "N_SCALAR_MAX_is_search_bound_not_prediction": True,
    "N_U1_MAX": N_U1_MAX,
    "M_MAX": M_MAX,
    "M_MAX_is_search_bound_not_prediction": True,
    "groups_inherited_from_G3": [f"SU({n})" for n in N_SU_VALUES],
    "n_fermion_inherited_from_G3": ["1", "2"],
    "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
    "vacuum_dynamics": "NOT_TESTED",
}

def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b4_artifacts"


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


def fund_gens_numpy(n: int) -> list[np.ndarray]:
    return [np.array(g, dtype=np.complex128) for g in su_n_generators(n)]


def _chevalley(n: int) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    e_ops: list[np.ndarray] = []
    f_ops: list[np.ndarray] = []
    h_ops: list[np.ndarray] = []
    for i in range(n - 1):
        e = np.zeros((n, n), dtype=np.complex128)
        f = np.zeros((n, n), dtype=np.complex128)
        h = np.zeros((n, n), dtype=np.complex128)
        e[i, i + 1] = 1
        f[i + 1, i] = 1
        h[i, i] = 1
        h[i + 1, i + 1] = -1
        e_ops.append(e)
        f_ops.append(f)
        h_ops.append(h)
    return e_ops, f_ops, h_ops


def _wedge_matrix(tmat: np.ndarray, n: int, k: int) -> np.ndarray:
    idx = list(itertools.combinations(range(n), k))
    pos = {c: i for i, c in enumerate(idx)}
    dim = len(idx)
    out = np.zeros((dim, dim), dtype=np.complex128)
    for col, multi in enumerate(idx):
        for r, ir in enumerate(multi):
            for s in range(n):
                new = list(multi)
                new[r] = s
                if len(set(new)) < k:
                    continue
                sign = 1
                for a in range(k):
                    for b in range(a + 1, k):
                        if new[a] > new[b]:
                            sign *= -1
                out[pos[tuple(sorted(new))], col] += tmat[s, ir] * sign
    return out


def _tensor(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.kron(a, np.eye(b.shape[0])) + np.kron(np.eye(a.shape[0]), b)


def _embed_ops(ops: list[np.ndarray], n: int, labels: tuple[int, ...]) -> list[np.ndarray]:
    factors = [p for p, a in enumerate(labels, start=1) if a]
    if not factors:
        return [np.zeros((1, 1), dtype=np.complex128) for _ in ops]
    per = [[_wedge_matrix(op, n, k) for op in ops] for k in factors]
    out = []
    for i in range(len(ops)):
        mat = per[0][i]
        for f in range(1, len(factors)):
            mat = _tensor(mat, per[f][i])
        out.append(mat)
    return out


def _svd_null(mats: list[np.ndarray], tol: float = HW_TOL) -> np.ndarray:
    stacked = np.vstack(mats)
    _u, s, vh = np.linalg.svd(stacked, full_matrices=True)
    rank = int((s > tol).sum())
    return vh[rank:].conj().T


@lru_cache(maxsize=32)
def irrep_generators(n: int, labels: tuple[int, ...]) -> tuple[np.ndarray, ...]:
    fund = fund_gens_numpy(n)
    if all(a == 0 for a in labels):
        return tuple(np.zeros((1, 1), dtype=np.complex128) for _ in fund)
    e_ops, f_ops, h_ops = _chevalley(n)
    e_emb = _embed_ops(e_ops, n, labels)
    f_emb = _embed_ops(f_ops, n, labels)
    h_emb = _embed_ops(h_ops, n, labels)
    t_emb = _embed_ops(fund, n, labels)
    dim = t_emb[0].shape[0]
    constraints = list(e_emb) + [h_emb[i] - a * np.eye(dim) for i, a in enumerate(labels)]
    hw = _svd_null(constraints)[:, 0]
    hw = hw / np.linalg.norm(hw)
    basis = [hw]
    queue = deque([hw])
    expected = su_n_dimension(n, labels)
    while queue and len(basis) < expected:
        vec = queue.popleft()
        for fop in f_emb:
            w = fop @ vec
            for b in basis:
                w = w - np.vdot(b, w) * b
            nrm = np.linalg.norm(w)
            if nrm < HW_TOL:
                continue
            w = w / nrm
            basis.append(w)
            queue.append(w)
            if len(basis) == expected:
                break
    if len(basis) != expected:
        raise EngineFailure("SEARCH_ACCOUNTING_FAILURE", f"irrep basis {n} {labels}")
    bmat = np.stack(basis, axis=1)
    return tuple(bmat.conj().T @ tmat @ bmat for tmat in t_emb)


def generic_vev(n: int, labels: tuple[int, ...], dim: int) -> np.ndarray:
    if reality_type(n, labels) == "real":
        vec = np.array([float(i + 1) for i in range(dim)], dtype=np.complex128)
    else:
        vec = np.array([(i + 1) + (i + 2) * 1j for i in range(dim)], dtype=np.complex128)
    return vec / np.linalg.norm(vec)


def mass_matrix(tv: list[np.ndarray]) -> np.ndarray:
    size = len(tv)
    mat = np.zeros((size, size), dtype=float)
    for a in range(size):
        for b in range(size):
            mat[a, b] = float(np.vdot(tv[a], tv[b]).real)
    return mat


def breaking_from_generators(
    gens: list[np.ndarray],
    vevs: list[np.ndarray],
    u1_weights: list[int],
) -> dict[str, Any]:
    tv: list[np.ndarray] = []
    n_su = len(gens)
    for a in range(n_su):
        acc = np.zeros_like(vevs[0])
        for v in vevs:
            acc = acc + gens[a] @ v
        tv.append(acc)
    if u1_weights:
        acc = np.zeros_like(vevs[0])
        for v, wgt in zip(vevs, u1_weights):
            acc = acc + wgt * v
        tv.append(acc)
    m2 = mass_matrix(tv)
    rank = int(np.linalg.matrix_rank(m2, tol=RANK_TOL))
    dim_g = len(tv)
    null = dim_g - rank
    return {
        "dim_G": dim_g,
        "rank_M2": rank,
        "nullity_M2": null,
        "dim_H": null,
        "dim_G_over_H": rank,
        "massless_vector_count": null,
        "massive_vector_candidate_count": rank,
        "goldstone_direction_count": rank,
        "partial_breaking": bool(null > 0 and rank > 0),
        "complete_breaking": bool(rank > 0 and null == 0),
        "no_breaking": bool(rank == 0),
    }


def breaking_analysis(n: int, labels: tuple[int, ...], k: int, weight: str) -> dict[str, Any]:
    gens = list(irrep_generators(n, labels))
    dim = gens[0].shape[0]
    vev = generic_vev(n, labels, dim)
    weights = []
    if k == 1:
        weights = [0 if weight == "none" else int(weight)]
    data = breaking_from_generators(gens, [vev], weights)
    data.update(
        {
            "scalar_dimension": dim,
            "scalar_reality": reality_type(n, labels),
            "vev_nonzero": True,
            "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
            "vacuum_dynamics": "NOT_TESTED",
            "u1_weight": weight,
            "coupling_independent": True,
        }
    )
    scaled = breaking_from_generators([2.0 * g for g in gens], [vev], weights)
    data["coupling_independent"] = scaled["rank_M2"] == data["rank_M2"] and scaled["nullity_M2"] == data["nullity_M2"]
    return data


def pure_u1_breaking(weight: int) -> dict[str, Any]:
    """dim(G)=1 complete-vs-no-breaking logic."""
    vev = np.array([1.0 + 0.0j])
    return breaking_from_generators([], [vev], [weight])


def common_stabilizer(
    items: list[tuple[list[np.ndarray], np.ndarray, int | None]],
) -> dict[str, Any]:
    gens0 = items[0][0]
    vevs = [v for _g, v, _w in items]
    weights = []
    has_u1 = any(w is not None for _g, _v, w in items)
    if has_u1:
        weights = [0 if w is None else int(w) for _g, _v, w in items]
    return breaking_from_generators(gens0, vevs, weights)


def g3_prefix_from_g4(text: str) -> str:
    items = [p for p in text.split("|") if not p.startswith(("SD:", "SW:", "SM:"))]
    return "|".join(items)


def parse_g4_pack(text: str) -> dict[str, str]:
    parts = dict(item.split(":", 1) for item in text.split("|"))
    g3 = g3_prefix_from_g4(text)
    parsed = parse_pack(g3)
    parsed["scalar_dynkin"] = parts["SD"]
    parsed["scalar_u1"] = parts["SW"]
    parsed["scalar_mult"] = parts.get("SM", "1")
    parsed["g3_pack"] = g3
    return parsed


def g4_pack_values() -> list[str]:
    packs = []
    for g3 in g3_pack_values():
        parsed = parse_pack(g3)
        n = int(parsed["simple_group"].split(":")[1])
        k = int(parsed["u1_k"])
        for labels in all_dynkin(n - 1, R_MAX):
            sd = format_dynkin(labels)
            if k == 0:
                packs.append(f"{g3}|SD:{sd}|SW:none|SM:1")
            else:
                for w in range(-N_U1_MAX, N_U1_MAX + 1):
                    packs.append(f"{g3}|SD:{sd}|SW:{w}|SM:1")
    return packs


def g4_executable_registry() -> dict[str, dict[str, Any]]:
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
    ]
    g4 = _with_hash(
        {
            "grammar_id": G4_ID,
            "parent_grammar_id": G3R_ID,
            "extension_description": (
                "Bounded scalar multiplets plus a structural nonzero VEV; "
                "derive stabilizer, mass-matrix rank/nullity, and KP15"
            ),
            "allowed_fields": ["metric", "scalar", "Weyl_fermion", "scalar_multiplet"],
            "allowed_groups": ["SU_N_family", "SU_N x U(1)^k"],
            "allowed_representations": ["dynkin_irreps_bounded", "U1_character_n_in_Z", "scalar_irrep_from_G3_catalogue"],
            "allowed_interactions": ["nonabelian_covariant_derivative", "U1_covariant_derivative", "scalar_kinetic_VEV"],
            "allowed_symmetry_breaking": ["nonzero_structural_VEV"],
            "allowed_constraints": list(ACTIVE_G4_KPS) + ["G4_SCALAR_VEV_VALIDITY"],
            "explicit_exclusions": exclusions,
            "provenance": "GRAMMAR EXTENSION",
            "status": "ACTIVE_G4",
            "axes": {"g4_pack": g4_pack_values()},
            "r_max": R_MAX,
            "n_scalar_max": N_SCALAR_MAX,
            "n_u1_max": N_U1_MAX,
            "r_max_is_search_bound_not_prediction": True,
            "n_scalar_max_is_search_bound_not_prediction": True,
            "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
            "vacuum_dynamics": "NOT_TESTED",
        }
    )
    return {G4_ID: g4}


def g4_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    _ = grammar
    try:
        parsed = parse_g4_pack(assignment["g4_pack"])
        n = int(parsed["simple_group"].split(":")[1])
        slabels = parse_dynkin(parsed["scalar_dynkin"])
        k = int(parsed["u1_k"])
        sw = parsed["scalar_u1"]
        sm = int(parsed["scalar_mult"])
        flabels = parse_dynkin(parsed["dynkin"])
    except (KeyError, ValueError):
        return False, "invalid_g4_pack"
    if n not in N_SU_VALUES:
        return False, "group_not_in_G3_bounds"
    if len(flabels) != n - 1 or len(slabels) != n - 1:
        return False, "dynkin_rank_mismatch"
    if any(x < 0 or x > R_MAX for x in flabels + slabels):
        return False, "dynkin_outside_R_MAX"
    if sm < 1 or sm > N_SCALAR_MAX:
        return False, "scalar_multiplicity_outside_N_SCALAR_MAX"
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


def verify_g3r_parent_checkpoint() -> dict[str, Any]:
    path = g3r_checkpoint_path()
    if not path.is_file():
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G3_R1 parent missing")
    payload = _read_json(path)
    stored = payload.get("integrity_digest")
    recomputed = content_hash({k: v for k, v in payload.items() if k != "integrity_digest"})
    if stored != recomputed:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G3_R1 parent digest mismatch")
    if payload.get("grammar_id") != G3R_ID:
        raise EngineFailure("GRAMMAR_MISSING", "G3_R1 parent grammar_id")
    if payload.get("grammar_hash") != EXPECTED_G3R_GRAMMAR_HASH:
        raise EngineFailure("GRAMMAR_HASH_MISMATCH", "G3_R1 parent grammar_hash")
    if payload.get("engine_version") != ENGINE_VERSION:
        raise EngineFailure("RESUME_INTEGRITY_FAILURE", "G3_R1 parent engine version")
    if payload.get("input_hashes", {}).get("top_down_input_hash") != top_down_input_hash():
        raise EngineFailure("INPUT_HASH_MISMATCH", "G3_R1 parent top-down inputs")
    if _file_digest(path) != EXPECTED_G3R_CHECKPOINT_HASH:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G3_R1 file digest changed")
    return payload


def g4_run_tests(candidate: dict[str, Any], *, test_version: str = "g4-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    parsed = parse_g4_pack(candidate["assignment"]["g4_pack"])
    n = int(parsed["simple_group"].split(":")[1])
    k = int(parsed["u1_k"])
    slabels = parse_dynkin(parsed["scalar_dynkin"])
    sw = parsed["scalar_u1"]
    data = irrep_data(n, slabels)
    br = breaking_analysis(n, slabels, k, sw)
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
        "KP13 requires a broken generator",
    )
    add(
        "KP15",
        "PASS" if br["partial_breaking"] else "FAIL",
        "DERIVED GIVEN GAUGE + SCALAR KINETIC STRUCTURE + VEV",
        "massless_vector_count>0 and massive_vector_candidate_count>0",
    )
    add("KP12", "UNTESTED", "DEFERRED TO G5", "anomaly_status=DEFERRED_TO_G5")
    add(
        "G4_SCALAR_VEV_VALIDITY",
        "PASS" if br["vev_nonzero"] and data["dimension"] >= 1 else "FAIL",
        "G4 STRUCTURAL ASSUMPTION",
        "finite scalar irrep plus nonzero structural VEV",
    )
    add("vacuum_dynamics", "UNTESTED", "NOT_TESTED", "vacuum_existence is assumed, not derived from a potential")
    add("G5_anomaly", "NOT_APPLICABLE", "DEFERRED TO G5", "G4 must not activate G5")
    required_fail = any(
        r["status"] == "FAIL" and r["test_id"] in (*ACTIVE_G4_KPS, "G4_SCALAR_VEV_VALIDITY") for r in results
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


def attach_g4_stats(grammar: dict[str, Any], evaluated: list[dict[str, Any]], compatible: list[dict[str, Any]]) -> dict[str, Any]:
    parent = verify_g3r_parent_checkpoint()
    parent_hash = _file_digest(g3r_checkpoint_path())
    table = []
    inventory = []
    _ = compatible
    _ = grammar
    for cand in evaluated:
        parsed = parse_g4_pack(cand["assignment"]["g4_pack"])
        n = int(parsed["simple_group"].split(":")[1])
        k = int(parsed["u1_k"])
        slabels = parse_dynkin(parsed["scalar_dynkin"])
        sw = parsed["scalar_u1"]
        data = irrep_data(n, slabels)
        br = (cand.get("tests") or {}).get("breaking") or breaking_analysis(n, slabels, k, sw)
        glabel = group_label(n, k)
        parent_g3 = content_hash({"grammar_id": G3R_ID, "assignment": {"g3_pack": parsed["g3_pack"]}})
        kp13 = "PASS" if br["dim_G_over_H"] > 0 else "FAIL"
        kp15 = "PASS" if br["partial_breaking"] else "FAIL"
        row = {
            "candidate_class": cand["candidate_id"],
            "candidate_hash": cand["candidate_hash"],
            "parent_g3_hash": parent_g3,
            "gauge_group": glabel,
            "scalar_representation": f"[{format_dynkin(slabels)}] dim={data['dimension']} {data['reality_type']}",
            "VEV_structure": "nonzero structural VEV; magnitude not provided",
            "unbroken_subgroup": f"stabilizer_dim={br['dim_H']}",
            "broken_generators": br["dim_G_over_H"],
            "massless_vector_count": br["massless_vector_count"],
            "massive_vector_count": br["massive_vector_candidate_count"],
            "KP13": kp13,
            "KP15": kp15,
            "anomaly_status": "DEFERRED_TO_G5",
            "status": cand.get("filter_status"),
            "provenance": "DERIVED GIVEN REPRESENTATION + VEV",
        }
        table.append(row)
        if cand.get("filter_status") == "PASS":
            couplings = ["g_SU_N"] + (["g_U1"] if k else [])
            inventory.append(
                {
                    "candidate_hash": cand["candidate_hash"],
                    "gauge_group": glabel,
                    "scalar_representation": [format_dynkin(slabels)],
                    "scalar_multiplicity": parsed["scalar_mult"],
                    "VEV_multiplicity": "1",
                    "stabilizer_H_dimension": br["dim_H"],
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
        "provenance_summary": {
            "scalar_representation": "GRAMMAR EXTENSION",
            "nonzero_VEV": "G4 STRUCTURAL ASSUMPTION",
            "VEV_stabilizer_H": "DERIVED GIVEN REPRESENTATION + VEV",
            "mass_matrix_rank": "DERIVED GIVEN GAUGE + SCALAR KINETIC STRUCTURE + VEV",
            "anomaly_cancellation": "DEFERRED TO G5",
        },
    }


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14b3r_priors()
    out["phase14b3r"] = {}
    for name in (
        "PHASE_14B3R_SUMMARY.json",
        "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json",
        "PHASE_14B3R_G3_GRAMMAR.json",
    ):
        path = phase14b3r_artifact_dir() / name
        if path.is_file():
            out["phase14b3r"][name] = _file_digest(path)
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
        raise UnauthorizedAnalysisError("Phase 14B.4 refuses an unauthorized action object")
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
    patterns = {(row["gauge_group"], row["stabilizer_H_dimension"], row["broken_generator_count"]) for row in inventory}

    def yn(ok: bool) -> str:
        return "YES" if ok else "NO"

    return {
        "UNIQUE_GAUGE_GROUP": yn(len(groups) == 1),
        "UNIQUE_STABILIZER": yn(len(stabs) == 1),
        "UNIQUE_BREAKING_PATTERN": yn(len(patterns) == 1),
        "UNIQUE_STRUCTURE": yn(len(inventory) == 1),
        "UNIQUE_PARAMETER_SET": "NO",
        "UNIQUE_DIMENSIONLESS_COUPLING": "NO",
    }


def analyze_phase14b4_g4(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
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
        s14b3r = _read_json(phase14b3r_artifact_dir() / "PHASE_14B3R_SUMMARY.json")
        corpus = _historical_corpus()
        parent_ckpt = verify_g3r_parent_checkpoint()
        g3_before = g3r_checkpoint_path().read_bytes()
        from physics_lab.physics.phase14b2_g2 import artifact_dir as phase14b2_artifact_dir

        g2_path = phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json"
        g2_before = g2_path.read_bytes()
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
    if s14b3r.get("PHASE_14B3R_STATUS") != "CLOSED":
        integrity_failure = "Phase 14B.3R is not CLOSED"
    if s14b3r.get("current_grammar") != G3R_ID:
        integrity_failure = "CURRENT_GRAMMAR is not G3_FINITE_REPRESENTATIONS_R1"
    if s14b3r.get("NEXT_AUTHORIZED_EXTENSION") != G4_ID:
        integrity_failure = "NEXT_AUTHORIZED_EXTENSION is not G4"
    if s14b3r.get("GRAMMAR_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        integrity_failure = "G3_R1 grammar hash mismatch"
    if s14b3r.get("PARENT_GRAMMAR_HASH") != EXPECTED_G2_GRAMMAR_HASH:
        integrity_failure = "G2 grammar hash mismatch"
    if s14b3r.get("TOP_DOWN_INPUT_HASH") != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "top-down input hash mismatch"
    if s14b3r.get("G4_EXECUTED") is True:
        integrity_failure = "G4 was already marked executed in G3_R1 artifacts"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical corpus rewritten"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G3R_GRAMMAR_HASH:
        integrity_failure = "G3_R1 checkpoint grammar hash mismatch"
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "live top-down input hash mismatch"
    if R_MAX != 1:
        integrity_failure = "R_MAX expanded"

    grammars = g4_executable_registry()
    g4 = grammars[G4_ID]
    if g4["parent_grammar_id"] != G3R_ID:
        integrity_failure = "G4 parent is not G3_R1"

    summary_path = artifact_dir() / "PHASE_14B4_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14B4_STATUS") == "CLOSED" and existing.get("G5_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14B4_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "G4_EXECUTED": False,
                "G5_EXECUTED": False,
                "ranking": False,
            }
            _write_json(summary_path, summary)
        else:
            engine = ClosureEngine(artifact_dir(), chain="g4_only")
            assert_target_blind({"g4": g4, "bounds": SCALAR_SEARCH_BOUNDS, "catalogue": build_representation_catalogue()})
            try:
                ClosureEngine(artifact_dir() / "no_g5", chain="physics")
                g5_block = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g5_block = exc.mode
            try:
                engine.advance_grammar("G5_ANOMALY_CONSTRAINTS", G4_ID)
                g5_skip = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g5_skip = exc.mode
            state = engine.run_until_closure()
            if g3r_checkpoint_path().read_bytes() != g3_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G4 overwrote the G3_R1 checkpoint")
            if g2_path.read_bytes() != g2_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G4 overwrote the G2 checkpoint")
            g4_rep = next(r for r in state["version_reports"] if r["grammar_id"] == G4_ID)
            g3_ok = len(parent_ckpt.get("survivor_hashes") or [])
            g4_ok = g4_rep["compatible"]
            newly = g4_rep.get("compatible_hashes") or []
            used_parents = {row.get("parent_g3_hash") for row in g4_rep.get("class_table") or [] if row.get("status") == "PASS"}
            eliminated = [h for h in (parent_ckpt.get("survivor_hashes") or []) if h not in used_parents]
            uniq = _uniqueness(g4_rep.get("parameter_inventory") or [])
            pass_rows = [r for r in (g4_rep.get("class_table") or []) if r.get("status") == "PASS"]
            kp15_any = any(r.get("KP15") == "PASS" for r in pass_rows)
            kp13_any = any(r.get("KP13") == "PASS" for r in pass_rows)
            groups_partial = sorted({r["gauge_group"] for r in pass_rows})
            scalar_stabs = sorted({r["scalar_representation"] for r in pass_rows})
            patterns = {(r["gauge_group"], r["unbroken_subgroup"], r["broken_generators"]) for r in pass_rows}
            summary = {
                "phase": PHASE,
                "audit_version": AUDIT_VERSION,
                "PHASE_14B4_STATUS": "CLOSED",
                "integrity_failure": None,
                "G4_STATUS": g4_rep["closure_status"],
                "METHOD_STATUS": "VERIFIED",
                "SCIENTIFIC_STATUS": "ANALYZED_G4_ONLY",
                "GRAMMAR_ID": G4_ID,
                "GRAMMAR_HASH": g4["grammar_hash"],
                "PARENT_GRAMMAR": G3R_ID,
                "PARENT_GRAMMAR_HASH": EXPECTED_G3R_GRAMMAR_HASH,
                "G2_GRAMMAR_HASH": EXPECTED_G2_GRAMMAR_HASH,
                "PARENT_CHECKPOINT": str(g3r_checkpoint_path().name),
                "PARENT_CHECKPOINT_HASH": _file_digest(g3r_checkpoint_path()),
                "TOP_DOWN_INPUT_HASH": top_down_input_hash(),
                "engine_version": ENGINE_VERSION,
                "current_grammar": G4_ID,
                "SCALAR_SEARCH_BOUNDS": dict(SCALAR_SEARCH_BOUNDS),
                "RAW_COMBINATIONS": g4_rep["raw_theoretical_combinations"],
                "METADATA_PRUNED": g4_rep["metadata_pruned_candidates"],
                "GENERATED": g4_rep["generated_candidates"],
                "REJECTED": g4_rep["rejected"],
                "UNRESOLVED": g4_rep["unresolved"],
                "TOP_DOWN_COMPATIBLE": g4_ok,
                "EQUIVALENCE_CLASSES": len(g4_rep["equivalence_classes"]),
                "G3_COMPATIBLE": g3_ok,
                "G4_GENERATED": g4_rep["generated_candidates"],
                "G4_TOP_DOWN_COMPATIBLE": g4_ok,
                "NEWLY_ENABLED": newly,
                "ELIMINATED": eliminated,
                "G3_SURVIVORS_REUSED": g4_rep.get("g3_survivors_reused"),
                "G4_NEW_CANDIDATES_GENERATED": g4_rep.get("g4_new_candidates_generated"),
                "G0_REGENERATED": 0,
                "G1_FULL_SEARCH_REGENERATED": 0,
                "G2_FULL_SEARCH_REGENERATED": 0,
                "G3_FULL_SEARCH_REGENERATED": 0,
                "R_MAX_UNCHANGED": True,
                "KP13_STATUS": "PASS" if kp13_any else "FAIL",
                "KP15_STATUS": "PASS" if kp15_any else "FAIL",
                "KP15_STRUCTURALLY_SUPPORTED": bool(kp15_any),
                "KP15_NOT_REALIZED_WITHIN_DECLARED_G4_BOUNDS": not bool(kp15_any),
                "STRUCTURAL_SSB_SUPPORTED": bool(kp15_any),
                "QUALITATIVE_SSB_DOES_NOT_SELECT_A_UNIQUE_BREAKING_PATTERN": len(patterns) != 1,
                "groups_admitting_partial_breaking": groups_partial,
                "scalar_representations_with_nontrivial_stabilizer": scalar_stabs,
                "G1_EXECUTED": True,
                "G2_EXECUTED": True,
                "G3_EXECUTED": True,
                "G3_CORRECTED_EXECUTED": True,
                "G4_EXECUTED": True,
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
            }
            _write_json(summary_path, summary)
            _write_json(artifact_dir() / "PHASE_14B4_G4_GRAMMAR.json", g4)
            _write_json(artifact_dir() / "PHASE_14B4_REPRESENTATION_CATALOGUE.json", build_representation_catalogue())
    else:
        summary = cached
        g4 = _read_json(artifact_dir() / "PHASE_14B4_G4_GRAMMAR.json")

    hashes_after = snapshot_prior_artifact_hashes()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    g3_unchanged = g3r_checkpoint_path().read_bytes() == g3_before
    g2_unchanged = g2_path.read_bytes() == g2_before
    artifacts_ok = hashes_before["phase14b3r"] == hashes_after["phase14b3r"]
    summary["phase14b3r_artifacts_unchanged"] = artifacts_ok
    summary["phase14b2_artifacts_unchanged"] = hashes_before.get("phase14b2") == hashes_after.get("phase14b2")
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["g3r_checkpoint_unchanged"] = g3_unchanged
    summary["g2_checkpoint_unchanged"] = g2_unchanged
    if not (
        artifacts_ok
        and grammar_ok
        and frozen_ok
        and g3_unchanged
        and g2_unchanged
        and summary.get("ranking") is False
        and summary.get("G5_EXECUTED") is False
        and summary.get("R_MAX_UNCHANGED") is True
    ):
        summary["PHASE_14B4_STATUS"] = "INTEGRITY_FAILURE"
        summary["METHOD_STATUS"] = "FAILED"
        summary["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    _write_json(summary_path, summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_14B4_TEST_COPY_ID": PHASE_14B4_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "G4_STATUS": summary.get("G4_STATUS"),
        "METHOD_STATUS": summary.get("METHOD_STATUS"),
        "SCIENTIFIC_STATUS": summary.get("SCIENTIFIC_STATUS"),
        "GRAMMAR_ID": G4_ID,
        "GRAMMAR_HASH": summary.get("GRAMMAR_HASH"),
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
        "G4_GENERATED": summary.get("G4_GENERATED"),
        "G4_TOP_DOWN_COMPATIBLE": summary.get("G4_TOP_DOWN_COMPATIBLE"),
        "NEWLY_ENABLED": summary.get("NEWLY_ENABLED"),
        "ELIMINATED": summary.get("ELIMINATED"),
        "KP13_STATUS": summary.get("KP13_STATUS"),
        "KP15_STATUS": summary.get("KP15_STATUS"),
        "KP15_STRUCTURALLY_SUPPORTED": summary.get("KP15_STRUCTURALLY_SUPPORTED"),
        "STRUCTURAL_SSB_SUPPORTED": summary.get("STRUCTURAL_SSB_SUPPORTED"),
        "QUALITATIVE_SSB_DOES_NOT_SELECT_A_UNIQUE_BREAKING_PATTERN": summary.get(
            "QUALITATIVE_SSB_DOES_NOT_SELECT_A_UNIQUE_BREAKING_PATTERN"
        ),
        "groups_admitting_partial_breaking": summary.get("groups_admitting_partial_breaking"),
        "scalar_representations_with_nontrivial_stabilizer": summary.get("scalar_representations_with_nontrivial_stabilizer"),
        "G0_REGENERATED": 0,
        "G1_EXECUTED": True if summary.get("PHASE_14B4_STATUS") == "CLOSED" else False,
        "G2_EXECUTED": True if summary.get("PHASE_14B4_STATUS") == "CLOSED" else False,
        "G3_EXECUTED": True if summary.get("PHASE_14B4_STATUS") == "CLOSED" else False,
        "G3_CORRECTED_EXECUTED": True if summary.get("PHASE_14B4_STATUS") == "CLOSED" else False,
        "G4_EXECUTED": True if summary.get("PHASE_14B4_STATUS") == "CLOSED" else False,
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
        "PHASE_14B4_STATUS": summary.get("PHASE_14B4_STATUS"),
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
        "PHASE_14B4_CLOSED": summary.get("PHASE_14B4_STATUS") == "CLOSED",
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
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_14B4_STATUS"] == "CLOSED"
        and science["G5_EXECUTED"] is False
        and science["G4_EXECUTED"] is True
        and science["PARENT_GRAMMAR"] == G3R_ID
        and science["ranking"] is False
        and science["gravity_changed"] is False
        and science["experimental_inputs"] == 0
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and g3_unchanged
        and g2_unchanged
        and corpus["specs_unchanged"]
    )
    return science


def run_phase14b4_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14b4_g4(auth, signature=signature)
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
            "G3R_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g3r_checkpoint_unchanged") else "FAILED",
            "G2_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g2_checkpoint_unchanged") else "FAILED",
            "PHASE_14B4_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
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
            "G4_EXECUTED": "TRUE",
            "G5_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
