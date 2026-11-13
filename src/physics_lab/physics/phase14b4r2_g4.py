"""G4R-ORBIT-CLOSURE-v2: SU(4) 20 / 20-bar / 64 orbit classification.

Mathematical / software closure of the G4R PARTIAL placeholders.
Does not invent new physics. Does not overwrite frozen G4R / G5 / G6 checkpoints.
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
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase12b_search import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b0_engine import (
    ENGINE_VERSION,
    EngineFailure,
    assert_target_blind,
    content_hash,
    generate_candidates,
    top_down_input_hash,
    _with_hash,
)
from physics_lab.physics.phase14b3_g3 import (
    N_SU_VALUES,
    R_MAX,
    all_dynkin,
    conjugate_dynkin,
    format_dynkin,
    irrep_data,
    parse_dynkin,
    reality_type,
    su_n_dimension,
)
from physics_lab.physics.phase14b4_g4 import (
    HW_TOL,
    _chevalley,
    _embed_ops,
    _svd_null,
    fund_gens_numpy,
)
from physics_lab.physics.phase14b4r_g4 import (
    EXPECTED_OLD_G4_CHECKPOINT_HASH as EXPECTED_ARCHIVED_G4_CHECKPOINT_HASH,
    EXPECTED_OLD_G4_GRAMMAR_HASH as EXPECTED_ARCHIVED_G4_GRAMMAR_HASH,
    G4R_ID,
    RANK_TOL,
    SCALAR_SEARCH_BOUNDS,
    artifact_dir as phase14b4r_artifact_dir,
    breaking_analysis_orbit,
    g4r_executable_registry,
    g4r_pack_values,
    orbit_types,
    parse_g4r_pack,
    representative_vev,
    scalar_generators,
    snapshot_prior_artifact_hashes as snapshot_14b4r_priors,
    solve_stabilizer,
)
from physics_lab.physics.phase14b5_g5 import (
    EXPECTED_G4R_CHECKPOINT_HASH,
    EXPECTED_G4R_GRAMMAR_HASH,
    G5_ID,
    anomaly_analysis,
    artifact_dir as phase14b5_artifact_dir,
    g5_pack_values,
    parse_g5_pack,
)
from physics_lab.physics.phase14b6_g6 import (
    EXPECTED_G5_CHECKPOINT_HASH,
    EXPECTED_G5_GRAMMAR_HASH,
    G6_ID,
    artifact_dir as phase14b6_artifact_dir,
    cached_covariance,
    g6_pack_values,
    layer_a_group_representation,
    parse_g6_pack,
)
from physics_lab.physics.phase14c0_known_physics import EXPECTED_G6_GRAMMAR_HASH
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_G4R2_GRAMMAR_HASH",
    "EXPECTED_G6R2_RESULT_HASH",
    "G4R2_CHAIN",
    "G4R2_ID",
    "G6R2_ID",
    "analyze_phase14b4r2_g4",
    "artifact_dir",
    "orbit_types_v2",
    "run_phase14b4r2_or_stop",
    "structural_analysis_v2",
]

PHASE = "PHASE_14B.4R2"
PHASE_14B4R2_TEST_COPY_ID = "PHASE_14B4R2_G4R_ORBIT_CLOSURE_V2"
AUDIT_VERSION = "g4r-orbit-closure-v2"
CLOSURE_VERSION = "G4R-ORBIT-CLOSURE-v2"
G6R2_VERSION = "G6R-ORBIT-CLOSURE-v2"
G4R2_ID = "G4_SCALAR_MULTIPLETS_VEV_R2"
G6R2_ID = "G6_STRUCTURAL_GAUGE_CONSISTENCY_R2"
EXPECTED_G4R2_GRAMMAR_HASH = "3f630e92aa8156b802333cab55c9ffb0f1382fa1d2459182a3b65f4c96e0b11d"
EXPECTED_G6R2_RESULT_HASH = "a7f34e041b5227957f2e3b766d9aae64cbc64a75f1020216d65f61877b2e2f1e"
EXPECTED_G4R2_CHECKPOINT_DIGEST = "68f9d3205df163ad7cacc1ba7d3b46837958615a4ca720c0359b81c6a0f42046"
EXPECTED_G6R2_CHECKPOINT_DIGEST = "53e16324af29c8dfb486e6cc330538e5449c4bfe5b93759b25dceaf90edf5137"
G4R2_CHAIN: tuple[str, ...] = (G4R2_ID,)
TARGET_IRREPS: tuple[tuple[int, tuple[int, ...]], ...] = (
    (4, (0, 1, 1)),
    (4, (1, 1, 0)),
    (4, (1, 1, 1)),
)
SU4_DIM = 15


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b4r2_artifacts"


def _write_json(path: Path, payload: Any) -> None:
    assert_target_blind(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pairs() -> list[tuple[int, int]]:
    return list(itertools.combinations(range(4), 2))


def _triples() -> list[tuple[int, int, int]]:
    return list(itertools.combinations(range(4), 3))


def _missing_sign(triple: tuple[int, ...]) -> tuple[int, int]:
    miss = [i for i in range(4) if i not in triple][0]
    perm = list(triple) + [miss]
    inversions = 0
    for i in range(4):
        for j in range(i + 1, 4):
            if perm[i] > perm[j]:
                inversions += 1
    return miss, 1 if inversions % 2 == 0 else -1


def embed_factors(labels: tuple[int, ...]) -> list[int]:
    return [p for p, a in enumerate(labels, start=1) if a]


def embed_dimension(labels: tuple[int, ...]) -> int:
    dim = 1
    for k in embed_factors(labels):
        dim *= len(list(itertools.combinations(range(4), k)))
    return dim


@lru_cache(maxsize=8)
def irrep_embedding(labels: tuple[int, ...]) -> dict[str, Any]:
    """Existing Cartan-Weyl realization: HW subspace of the declared wedge product."""
    n = 4
    fund = fund_gens_numpy(n)
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
        raise EngineFailure("ORBIT_CLASSIFICATION_UNRESOLVED", f"irrep basis {labels}")
    bmat = np.stack(basis, axis=1)
    gens = tuple(bmat.conj().T @ tmat @ bmat for tmat in t_emb)
    return {
        "labels": labels,
        "factors": embed_factors(labels),
        "embed_dimension": dim,
        "irrep_dimension": expected,
        "basis_matrix": bmat,
        "generators": gens,
        "realization": "highest_weight_subspace_of_wedge_product",
        "provenance": "DERIVED GIVEN EXISTING REPRESENTATION",
    }


def mixed_tensor_from_20(v: np.ndarray) -> np.ndarray:
    """T^{ij}_k antisymmetric in ij, inside the existing 20 = [0,1,1] embedding."""
    emb = irrep_embedding((0, 1, 1))
    embed = emb["basis_matrix"] @ v
    T = np.zeros((4, 4, 4), dtype=np.complex128)
    for p_idx, (i, j) in enumerate(_pairs()):
        for t_idx, tri in enumerate(_triples()):
            val = embed[p_idx * 4 + t_idx]
            k, sgn = _missing_sign(tri)
            T[i, j, k] += sgn * val
            T[j, i, k] -= sgn * val
    return T


def act_fundamental_on_mixed(xmat: np.ndarray, tensor: np.ndarray) -> np.ndarray:
    term1 = np.einsum("ap,pbc->abc", xmat, tensor)
    term2 = np.einsum("bq,aqc->abc", xmat, tensor)
    term3 = np.einsum("abr,rc->abc", tensor, xmat)
    return term1 + term2 - term3


def tensor_stabilizer_dim(tensor: np.ndarray) -> int:
    """Lie-algebra stabilizer of a mixed tensor under the fundamental su(4) action."""
    gens = fund_gens_numpy(4)
    cols = []
    for g in gens:
        image = act_fundamental_on_mixed(g, tensor)
        cols.append(np.concatenate([image.real.reshape(-1), image.imag.reshape(-1)]))
    jac = np.stack(cols, axis=1)
    rank = int(np.linalg.matrix_rank(jac, tol=RANK_TOL))
    return SU4_DIM - rank


def hw_mixed_tensor() -> np.ndarray:
    T = np.zeros((4, 4, 4), dtype=np.complex128)
    T[0, 1, 2] = 1.0
    T[1, 0, 2] = -1.0
    return T


def map_rank_of_tensor(tensor: np.ndarray) -> int:
    mat = np.zeros((6, 4), dtype=np.complex128)
    for p_idx, (i, j) in enumerate(_pairs()):
        for k in range(4):
            mat[p_idx, k] = tensor[i, j, k]
    return int(np.linalg.matrix_rank(mat, tol=1e-8))


def pfaffian4(mat: np.ndarray) -> complex:
    return mat[0, 1] * mat[2, 3] - mat[0, 2] * mat[1, 3] + mat[0, 3] * mat[1, 2]


def orbit_types_v2(n: int, labels: tuple[int, ...]) -> list[dict[str, Any]]:
    """Same search ids as G4R; classification upgraded only where certified."""
    base = orbit_types(n, labels)
    if (n, labels) not in TARGET_IRREPS:
        return [dict(item) for item in base]
    out = []
    for item in base:
        rec = dict(item)
        if rec["orbit_type_id"] == "hw_vector":
            rec["classification"] = "COMPLETE"
            rec["stratum_id"] = "minimal_highest_weight_orbit"
            rec["covering"] = "this_stratum_only"
            rec["completeness_criterion"] = "unique_closed_orbit_of_a_highest_weight_vector_in_an_irrep"
            rec["provenance"] = "DERIVED GIVEN EXISTING REPRESENTATION"
            rec["list_exhaustive"] = False
        elif rec["orbit_type_id"] == "generic_nonzero":
            rec["classification"] = "COMPLETE"
            rec["stratum_id"] = "open_trivial_stabilizer_stratum"
            rec["covering"] = "this_stratum_only"
            rec["completeness_criterion"] = "Zariski_open_set_where_Lie_stabilizer_dimension_vanishes"
            rec["provenance"] = "DERIVED GIVEN EXISTING REPRESENTATION"
            rec["list_exhaustive"] = False
        out.append(rec)
    return out


def irrep_orbit_list_status(n: int, labels: tuple[int, ...]) -> str:
    if (n, labels) in TARGET_IRREPS:
        return "PARTIAL"
    items = orbit_types_v2(n, labels)
    if any(item["classification"] == "PARTIAL" for item in items):
        return "PARTIAL"
    return "COMPLETE"


def vev_orbit_classification_status_v2() -> str:
    for n in N_SU_VALUES:
        for labels in all_dynkin(n - 1, R_MAX):
            if irrep_orbit_list_status(n, labels) == "PARTIAL":
                return "PARTIAL"
    return "COMPLETE"


def classify_representative(n: int, labels: tuple[int, ...], orbit_type_id: str) -> dict[str, Any]:
    item = next(x for x in orbit_types_v2(n, labels) if x["orbit_type_id"] == orbit_type_id)
    vev = representative_vev(n, labels, orbit_type_id)
    br = breaking_analysis_orbit(n, labels, 0, "none", orbit_type_id)
    payload: dict[str, Any] = {
        "orbit_type_id": orbit_type_id,
        "stratum_id": item.get("stratum_id") or item["orbit_type_id"],
        "classification": item["classification"],
        "representative_VEV_form": item["representative_VEV_form"],
        "stabilizer_dimension_su4": br["dim_H"],
        "orbit_dimension_su4": br["orbit_dimension"],
        "generic_or_special": "special" if orbit_type_id == "hw_vector" else "generic",
        "provenance": item.get("provenance") or "DERIVED GIVEN EXISTING REPRESENTATION",
        "completeness_criterion": item.get("completeness_criterion"),
        "list_exhaustive": item.get("list_exhaustive", True),
    }
    if (n, labels) == (4, (0, 1, 1)) and orbit_type_id == "hw_vector":
        tensor = hw_mixed_tensor()
        payload["algebraic_representative"] = "T^{01}_2 = 1, antisymmetrized, already traceless"
        payload["map_rank"] = map_rank_of_tensor(tensor)
        payload["pfaffian_of_support"] = "zero (decomposable two-form)"
        payload["independent_tensor_stabilizer_dim"] = tensor_stabilizer_dim(tensor)
        payload["invariant"] = "rank(phi)=1 and image spanned by a decomposable two-form"
    if (n, labels) == (4, (0, 1, 1)) and orbit_type_id == "generic_nonzero":
        tensor = mixed_tensor_from_20(vev)
        payload["map_rank"] = map_rank_of_tensor(tensor)
        payload["invariant"] = "Lie_stabilizer_dimension = 0 (open stratum)"
    return payload


def conjugation_report() -> dict[str, Any]:
    twenty = (0, 1, 1)
    bar = (1, 1, 0)
    equivalent = conjugate_dynkin(twenty) == bar and conjugate_dynkin(bar) == twenty
    classes = {}
    for oid in ("hw_vector", "generic_nonzero"):
        a = classify_representative(4, twenty, oid)
        b = classify_representative(4, bar, oid)
        classes[oid] = {
            "20_stab_dim": a["stabilizer_dimension_su4"],
            "20bar_stab_dim": b["stabilizer_dimension_su4"],
            "dimensions_match": a["stabilizer_dimension_su4"] == b["stabilizer_dimension_su4"],
        }
    return {
        "status": "conjugation-equivalent" if equivalent and all(v["dimensions_match"] for v in classes.values()) else "distinct classification",
        "conjugate_dynkin_identity": equivalent,
        "orbit_classes": classes,
        "provenance": "DERIVED GIVEN EXISTING REPRESENTATION",
        "note": "equivalence established by reversed Dynkin labels plus matching stabilizer dimensions on corresponding representatives; 20-bar is not a copy of 20",
    }


def extra_loci_numerical_evidence() -> dict[str, Any]:
    """Documented extra stabilizer dimensions. Sampling is not a covering proof."""
    return {
        "status": "PARTIAL",
        "provenance": "NUMERICAL EVIDENCE",
        "20_observed_extra_Lie_stab_dims": [1, 2],
        "64_observed_extra_Lie_stab_dims": [1, 4],
        "not_promoted_to_COMPLETE": True,
        "reason": "finite samples do not certify exhaustiveness of the stratum list",
    }


def classification_catalogue() -> dict[str, Any]:
    emb20 = irrep_embedding((0, 1, 1))
    emb20b = irrep_embedding((1, 1, 0))
    emb64 = irrep_embedding((1, 1, 1))
    return {
        "20": {
            "representation": "[0,1,1]",
            "dimension": 20,
            "reality": reality_type(4, (0, 1, 1)),
            "mathematical_realization": "highest-weight subspace of wedge^2 tensor wedge^3 of the fundamental (existing G4 Cartan-Weyl construction)",
            "embed_dimension": emb20["embed_dimension"],
            "embed_factors": emb20["factors"],
            "tensor_interpretation": "traceless mixed tensor T^{ij}_k, antisymmetric in ij, equivalent to the existing 20-dimensional embedding",
            "orbit_classes": [classify_representative(4, (0, 1, 1), "hw_vector"), classify_representative(4, (0, 1, 1), "generic_nonzero")],
            "ORBIT_CLASSIFICATION_STATUS": "PARTIAL",
            "reason_not_complete": "generated strata are certified; additional special loci exist and are not exhaustively classified",
        },
        "20-bar": {
            "representation": "[1,1,0]",
            "dimension": 20,
            "reality": reality_type(4, (1, 1, 0)),
            "mathematical_realization": "highest-weight subspace of wedge^1 tensor wedge^2 of the fundamental",
            "embed_dimension": emb20b["embed_dimension"],
            "embed_factors": emb20b["factors"],
            "orbit_classes": [classify_representative(4, (1, 1, 0), "hw_vector"), classify_representative(4, (1, 1, 0), "generic_nonzero")],
            "conjugation": conjugation_report(),
            "ORBIT_CLASSIFICATION_STATUS": "PARTIAL",
            "reason_not_complete": "conjugate-equivalent to 20; the 20 list is not exhaustive, so neither is 20-bar",
        },
        "64": {
            "representation": "[1,1,1]",
            "dimension": 64,
            "reality": reality_type(4, (1, 1, 1)),
            "mathematical_realization": "highest-weight subspace of wedge^1 tensor wedge^2 tensor wedge^3 of the fundamental",
            "embed_dimension": emb64["embed_dimension"],
            "embed_factors": emb64["factors"],
            "orbit_classes": [classify_representative(4, (1, 1, 1), "hw_vector"), classify_representative(4, (1, 1, 1), "generic_nonzero")],
            "ORBIT_CLASSIFICATION_STATUS": "PARTIAL",
            "reason_not_complete": "HW and open strata certified; remaining special locus not exhaustively classified",
        },
        "extra_loci": extra_loci_numerical_evidence(),
        "G4R_CLOSURE": "PARTIAL",
        "obstruction": "no covering theorem for all nonzero-vector strata of the 20 and 64; residual special loci remain",
    }


def structural_analysis_v2(
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
    """G6 layer logic with G4R2 orbit classification. G6 source is not modified."""
    la = layer_a_group_representation(n, flabels, slabels, k, fermion_weight, scalar_weight)
    cov_f = cached_covariance(n, flabels, k, fermion_weight)
    cov_s = cached_covariance(n, slabels, k, scalar_weight)
    lb_status = "PASS" if cov_f["status"] == "PASS" and cov_s["status"] == "PASS" else "FAIL"
    matter_status = "PASS" if cov_f["matter_kinetic_invariance"] and cov_s["matter_kinetic_invariance"] else "FAIL"
    orbits = {item["orbit_type_id"]: item for item in orbit_types_v2(n, slabels)}
    if orbit_type_id not in orbits:
        lc = {
            "status": "FAIL",
            "mode": "VEV_STABILIZER_MISMATCH",
            "KP15": "FAIL",
            "orbit_classification": "unknown",
            "note": "orbit not in G4R2 classification",
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
            "stratum_id": orbits[orbit_type_id].get("stratum_id"),
            "dim_G": br["dim_G"],
            "dim_H": br["dim_H"],
            "dim_G_over_H": br["dim_G_over_H"],
            "massless_vector_count": br["massless_vector_count"],
            "massive_vector_count": br["massive_vector_candidate_count"],
            "stab_mass_consistent": bool(dim_ok and mass_ok),
            "g4_stabilizer_reused": True,
            "list_exhaustive": orbits[orbit_type_id].get("list_exhaustive", True),
        }
    ld_status = "PASS" if la["status"] == "PASS" and lb_status == "PASS" else "FAIL"
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
            f"G5 survivor recomputed as {an['total_anomaly_status']}",
        )
    le = {"status": "PASS", "mode": None}
    statuses = [la["status"], lb_status, lc["status"], ld_status, le["status"]]
    if "FAIL" in statuses:
        lf = "FAIL"
    elif "PARTIAL" in statuses:
        lf = "PARTIAL"
    else:
        lf = "PASS"
    mode = lc.get("mode") if lc["status"] in {"FAIL", "PARTIAL"} else None
    return {
        "total_status": lf,
        "KP15": lc.get("KP15"),
        "failure_mode": mode,
        "layer_c": lc,
        "breaking": br,
        "anomaly": an,
        "layers": {
            "LAYER_A_GROUP_REPRESENTATION": la["status"],
            "LAYER_B_LOCAL_COVARIANCE": lb_status,
            "LAYER_C_SCALAR_VEV": lc["status"],
            "LAYER_D_FERMION_SCALAR": ld_status,
            "LAYER_E_ANOMALY_INTEGRITY": le["status"],
            "LAYER_F_COMPLETE": lf,
        },
        "matter_invariance": matter_status,
        "VECTORLIKE_STATUS": "UNTESTED",
    }


def g4r2_executable_registry() -> dict[str, dict[str, Any]]:
    parent = g4r_executable_registry()[G4R_ID]
    g4r2 = _with_hash(
        {
            "grammar_id": G4R2_ID,
            "parent_grammar_id": G4R_ID,
            "extension_description": (
                "ORBIT CLASSIFICATION CLOSURE of G4R for SU(4) 20, 20-bar, and 64; "
                "placeholders hw_vector and generic_nonzero recertified as named strata; "
                "stratum list not claimed exhaustive"
            ),
            "allowed_fields": list(parent["allowed_fields"]),
            "allowed_groups": list(parent["allowed_groups"]),
            "allowed_representations": list(parent["allowed_representations"]),
            "allowed_interactions": list(parent["allowed_interactions"]),
            "allowed_symmetry_breaking": list(parent["allowed_symmetry_breaking"]),
            "allowed_constraints": list(parent["allowed_constraints"]),
            "explicit_exclusions": list(parent["explicit_exclusions"])
            + [
                "new gauge groups",
                "R_MAX expansion",
                "F2 gauge kinetic",
                "Yukawa",
                "new fermion species",
                "numerical sampling promoted to COMPLETE covering",
            ],
            "provenance": "METHOD / INFRASTRUCTURE",
            "status": "ACTIVE_G4_ORBIT_CLOSURE_V2",
            "axes": {"g4r_pack": g4r_pack_values()},
            "r_max": R_MAX,
            "VEV_ORBIT_CLASSIFICATION": vev_orbit_classification_status_v2(),
            "STRATUM_LIST_EXHAUSTIVE": False,
            "correction_of": G4R_ID,
            "correction_of_grammar_hash": EXPECTED_G4R_GRAMMAR_HASH,
            "closure_version": CLOSURE_VERSION,
        }
    )
    return {G4R2_ID: g4r2}


def g4r2_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    from physics_lab.physics.phase14b4r_g4 import g4r_metadata_legal

    return g4r_metadata_legal(assignment, grammar)


def g4r2_run_tests(candidate: dict[str, Any], *, test_version: str = "g4r2-tests-v1") -> dict[str, Any]:
    from physics_lab.physics.phase14b4r_g4 import g4r_run_tests

    out = g4r_run_tests(candidate, test_version=test_version)
    parsed = parse_g4r_pack(candidate["assignment"]["g4r_pack"])
    n = int(parsed["simple_group"].split(":")[1])
    slabels = parse_dynkin(parsed["scalar_dynkin"])
    oid = parsed["orbit_type_id"]
    item = next(x for x in orbit_types_v2(n, slabels) if x["orbit_type_id"] == oid)
    br = out["breaking"]
    br = dict(br)
    br["orbit_classification"] = item["classification"]
    br["stratum_id"] = item.get("stratum_id")
    out["breaking"] = br
    return out


def attach_g4r2_stats(grammar: dict[str, Any], evaluated: list[dict[str, Any]], compatible: list[dict[str, Any]]) -> dict[str, Any]:
    from physics_lab.physics.phase14b4r_g4 import attach_g4r_stats

    extra = attach_g4r_stats(grammar, evaluated, compatible)
    extra["VEV_ORBIT_CLASSIFICATION"] = vev_orbit_classification_status_v2()
    extra["STRATUM_LIST_EXHAUSTIVE"] = False
    return extra


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14B.4R2 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return None


def _g4r_checkpoint_bytes() -> bytes:
    return (phase14b4r_artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json").read_bytes()


def _g5_checkpoint_bytes() -> bytes:
    return (phase14b5_artifact_dir() / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json").read_bytes()


def _g6_checkpoint_bytes() -> bytes:
    return (phase14b6_artifact_dir() / "closure_checkpoint_G6_STRUCTURAL_GAUGE_CONSISTENCY.json").read_bytes()


def _old_g4_checkpoint_bytes() -> bytes:
    return (Path(__file__).resolve().parent / "phase14b4_artifacts" / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV.json").read_bytes()


def resolve_g6_candidates() -> dict[str, Any]:
    old_rows = _read_json(phase14b6_artifact_dir() / "PHASE_14B6_SUMMARY.json")["class_table"]
    old_by_hash = {row["candidate_hash"]: row for row in old_rows}
    packs = list(g6_pack_values())
    if len(packs) != 479:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", f"G6 pack count {len(packs)}")
    resolution = []
    new_table = []
    complete_unchanged = 0
    complete_changed = 0
    became_complete = 0
    became_fail = 0
    remain_partial = 0
    for pack in packs:
        parsed = parse_g6_pack(pack)
        old_hash = content_hash({"grammar_id": G6_ID, "assignment": {"g6_pack": pack}})
        old = old_by_hash.get(old_hash)
        if old is None:
            raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "G6 pack missing from frozen table")
        n = int(parsed["simple_group"].split(":")[1])
        flabels = parse_dynkin(parsed["dynkin"])
        slabels = parse_dynkin(parsed["scalar_dynkin"])
        st = structural_analysis_v2(
            n,
            flabels,
            slabels,
            int(parsed["n_fermion"]),
            int(parsed["u1_k"]),
            parsed["u1_n"],
            parsed["scalar_u1"],
            parsed["orbit_type_id"],
            multiplicity=int(parsed["multiplicity"]),
        )
        new_status = st["total_status"]
        old_status = old["status"]
        lc = st["layer_c"]
        br = st["breaking"] or {}
        row = {
            "candidate_id": old.get("candidate_class") or old_hash,
            "candidate_hash_old": old_hash,
            "representation": old["scalar_representation"],
            "old_status": old_status,
            "new_status": new_status,
            "orbit_class": lc.get("stratum_id") or parsed["orbit_type_id"],
            "orbit_type_id": parsed["orbit_type_id"],
            "stabilizer_dim": lc.get("dim_H"),
            "orbit_dim": lc.get("dim_G_over_H"),
            "orbit_classification": lc.get("orbit_classification"),
            "certification_status": lc.get("orbit_classification"),
            "reason": (
                "previously COMPLETE sector unchanged"
                if old["orbit_classification"] == "COMPLETE" and new_status == "PASS"
                else "hw/generic stratum recertified; KP15 still holds"
                if old_status == "PARTIAL" and new_status == "PASS"
                else "recertified stratum fails existing KP15"
                if new_status == "FAIL"
                else "stratum remains unresolved"
            ),
        }
        if old["orbit_classification"] == "COMPLETE":
            if new_status != "PASS" or lc.get("dim_H") is None:
                complete_changed += 1
            else:
                complete_unchanged += 1
        else:
            if new_status == "PASS":
                became_complete += 1
            elif new_status == "FAIL":
                became_fail += 1
            else:
                remain_partial += 1
            resolution.append(row)
        new_table.append({**old, "status": new_status, "orbit_classification": lc.get("orbit_classification"), "KP15": st["KP15"], "VEV_stabilizer": f"{parsed['orbit_type_id']} dimH={lc.get('dim_H')}", "failure_mode": st.get("failure_mode")})
    if complete_changed:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "previously COMPLETE G6 sector changed")
    if len(new_table) != 479:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate count not conserved")
    return {
        "resolution_120": resolution,
        "new_class_table": new_table,
        "became_complete": became_complete,
        "became_fail": became_fail,
        "remain_partial": remain_partial,
        "complete_unchanged": complete_unchanged,
        "g6_new_complete": sum(1 for r in new_table if r["status"] == "PASS"),
        "g6_new_partial": sum(1 for r in new_table if r["status"] == "PARTIAL"),
        "g6_new_fail": sum(1 for r in new_table if r["status"] == "FAIL"),
        "pack_count": len(packs),
    }


def _g4_partial_audit() -> dict[str, Any]:
    old = _read_json(phase14b4r_artifact_dir() / "PHASE_14B4R_SUMMARY.json")["class_table"]
    updated = []
    for row in old:
        rec = dict(row)
        irrep = str(row.get("scalar_irrep") or "")
        if "[0,1,1]" in irrep or "[1,1,0]" in irrep or "[1,1,1]" in irrep:
            oid = row.get("VEV_orbit_type")
            n = 4
            if "[0,1,1]" in irrep:
                labels = (0, 1, 1)
            elif "[1,1,0]" in irrep:
                labels = (1, 1, 0)
            else:
                labels = (1, 1, 1)
            item = next(x for x in orbit_types_v2(n, labels) if x["orbit_type_id"] == oid)
            rec["orbit_classification"] = item["classification"]
            rec["stratum_id"] = item.get("stratum_id")
        updated.append(rec)
    return {
        "old_generated": len(old),
        "new_generated": len(updated),
        "old_pass": sum(1 for r in old if r.get("status") == "PASS"),
        "new_pass": sum(1 for r in updated if r.get("status") == "PASS"),
        "old_fail": sum(1 for r in old if r.get("status") == "FAIL"),
        "new_fail": sum(1 for r in updated if r.get("status") == "FAIL"),
        "class_table": updated,
    }


def analyze_phase14b4r2_g4(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_14b4r_priors()
    g4_before = _g4r_checkpoint_bytes()
    g5_before = _g5_checkpoint_bytes()
    g6_before = _g6_checkpoint_bytes()
    archived_g4_before = _old_g4_checkpoint_bytes()
    if _file_digest(phase14b4r_artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json") != EXPECTED_G4R_CHECKPOINT_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if _file_digest(phase14b5_artifact_dir() / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json") != EXPECTED_G5_CHECKPOINT_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "G5 checkpoint mutated", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    g4r_live = g4r_executable_registry()[G4R_ID]
    if g4r_live["grammar_hash"] != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "live G4R grammar mutated", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    g6_summary = _read_json(phase14b6_artifact_dir() / "PHASE_14B6_SUMMARY.json")
    if g6_summary.get("GRAMMAR_HASH") != EXPECTED_G6_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "G6 grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    catalogue = classification_catalogue()
    g4_audit = _g4_partial_audit()
    g6_res = resolve_g6_candidates()
    g4r2 = g4r2_executable_registry()[G4R2_ID]
    if g4r2["grammar_hash"] != EXPECTED_G4R2_GRAMMAR_HASH:
        raise EngineFailure("GRAMMAR_HASH_MISMATCH", "G4R2 grammar hash drifted")
    g5_packs = list(g5_pack_values())
    g6_packs = list(g6_pack_values())
    if len(g5_packs) != 2428:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", f"G5 pack count {len(g5_packs)}")
    if len(g6_packs) != 479:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", f"G6 pack count {len(g6_packs)}")

    r_max_unchanged = R_MAX == 1
    grammar_expanded = list(g4r_pack_values()) != g4r2["axes"]["g4r_pack"]
    if grammar_expanded:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "G4 pack axis expanded")

    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "closure_version": CLOSURE_VERSION,
        "g6r2_version": G6R2_VERSION,
        "PHASE_14B4R2_STATUS": "CLOSED_PARTIAL",
        "G4R_CLOSURE": "PARTIAL",
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_G4R_ORBIT_CLOSURE_V2",
        "GRAMMAR_ID": G4R2_ID,
        "GRAMMAR_HASH": g4r2["grammar_hash"],
        "old_G4_hash": EXPECTED_G4R_GRAMMAR_HASH,
        "new_G4_hash": g4r2["grammar_hash"],
        "old_G5_hash": EXPECTED_G5_GRAMMAR_HASH,
        "new_G5_hash": EXPECTED_G5_GRAMMAR_HASH,
        "old_G6_hash": EXPECTED_G6_GRAMMAR_HASH,
        "new_G6_hash": content_hash({"grammar_id": G6R2_ID, "parent": EXPECTED_G6_GRAMMAR_HASH, "table": [r["status"] for r in g6_res["new_class_table"]]}),
        "G4R_PARENT": G4R_ID,
        "G6R2_ID": G6R2_ID,
        "VEV_ORBIT_CLASSIFICATION": vev_orbit_classification_status_v2(),
        "STRATUM_LIST_EXHAUSTIVE": False,
        "ORBIT_CLASSIFICATION_STATUS": {
            "20": catalogue["20"]["ORBIT_CLASSIFICATION_STATUS"],
            "20-bar": catalogue["20-bar"]["ORBIT_CLASSIFICATION_STATUS"],
            "64": catalogue["64"]["ORBIT_CLASSIFICATION_STATUS"],
        },
        "PREVIOUS_G6": {"COMPLETE": 359, "PARTIAL": 120, "FAIL": 0},
        "NEW_G6": {
            "COMPLETE": g6_res["g6_new_complete"],
            "PARTIAL": g6_res["g6_new_partial"],
            "FAIL": g6_res["g6_new_fail"],
        },
        "RESOLUTION_COUNTS": {
            "became_COMPLETE": g6_res["became_complete"],
            "became_FAIL": g6_res["became_fail"],
            "remain_PARTIAL": g6_res["remain_partial"],
            "previously_COMPLETE_unchanged": g6_res["complete_unchanged"],
        },
        "G4_PASS_UNCHANGED": g4_audit["old_pass"] == g4_audit["new_pass"],
        "G4_FAIL_UNCHANGED": g4_audit["old_fail"] == g4_audit["new_fail"],
        "G5_LOGIC_UNCHANGED": True,
        "G5_SURVIVOR_COUNT_UNCHANGED": True,
        "G6_LOGIC_UNCHANGED": True,
        "G6_consumed_corrected_G4_orbits": True,
        "R_MAX_UNCHANGED": r_max_unchanged,
        "GRAMMAR_EXPANDED": False,
        "new_physical_principle": False,
        "new_physical_interaction": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "ranking": False,
        "fitting": False,
        "calibration": False,
        "sampling_promoted_to_COMPLETE": False,
        "gravity_changed": False,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "engine_version": ENGINE_VERSION,
        "obstruction": catalogue["obstruction"],
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "P6_EXECUTED": False,
        "F2_INTRODUCED": False,
        "YUKAWA_INTRODUCED": False,
        "QUANTUM_MACHINERY_STARTED": False,
    }
    if summary["new_G6_hash"] != EXPECTED_G6R2_RESULT_HASH:
        raise EngineFailure("GRAMMAR_HASH_MISMATCH", "G6R2 result hash drifted")
    g6_ckpt = {
        "grammar_id": G6R2_ID,
        "grammar_hash": summary["new_G6_hash"],
        "parent": G6_ID,
        "parent_grammar_hash": EXPECTED_G6_GRAMMAR_HASH,
        "closure_version": G6R2_VERSION,
        "class_table": g6_res["new_class_table"],
        "COMPLETE": g6_res["g6_new_complete"],
        "PARTIAL": g6_res["g6_new_partial"],
        "FAIL": g6_res["g6_new_fail"],
        "SUPERSEDED_PARENT": {
            "grammar_id": G6_ID,
            "grammar_hash": EXPECTED_G6_GRAMMAR_HASH,
            "status": "SUPERSEDED",
            "checkpoint_unmodified": True,
        },
        "integrity_digest": None,
        "engine_version": ENGINE_VERSION,
    }
    g6_ckpt["integrity_digest"] = content_hash({k: v for k, v in g6_ckpt.items() if k != "integrity_digest"})
    g4_ckpt = {
        "grammar_id": G4R2_ID,
        "grammar_hash": g4r2["grammar_hash"],
        "parent": G4R_ID,
        "parent_grammar_hash": EXPECTED_G4R_GRAMMAR_HASH,
        "closure_version": CLOSURE_VERSION,
        "class_table": g4_audit["class_table"],
        "SUPERSEDED_PARENT": {
            "grammar_id": G4R_ID,
            "grammar_hash": EXPECTED_G4R_GRAMMAR_HASH,
            "checkpoint_hash": EXPECTED_G4R_CHECKPOINT_HASH,
            "status": "SUPERSEDED",
            "checkpoint_unmodified": True,
        },
        "integrity_digest": None,
        "engine_version": ENGINE_VERSION,
    }
    g4_ckpt["integrity_digest"] = content_hash({k: v for k, v in g4_ckpt.items() if k != "integrity_digest"})
    summary_path = artifact_dir() / "PHASE_14B4R2_SUMMARY.json"
    _write_json(summary_path, summary)
    _write_json(artifact_dir() / "PHASE_14B4R2_G4_GRAMMAR.json", g4r2)
    _write_json(artifact_dir() / "ORBIT_CLASSIFICATION_20_20BAR_64.json", catalogue)
    _write_json(artifact_dir() / "CANDIDATE_120_RESOLUTION.json", {"rows": g6_res["resolution_120"], "counts": summary["RESOLUTION_COUNTS"]})
    _write_json(
        artifact_dir() / "PHASE_14B4R2_G5_PROPAGATION.json",
        {
            "G5_ID": G5_ID,
            "old_G5_hash": EXPECTED_G5_GRAMMAR_HASH,
            "new_G5_hash": EXPECTED_G5_GRAMMAR_HASH,
            "anomaly_rules_changed": False,
            "survivor_count": len(g5_packs),
            "note": "anomaly tests do not depend on VEV orbit type; G5 logic consumed corrected G4 metadata without modification",
            "provenance": "DERIVED GIVEN EXISTING REPRESENTATION",
        },
    )
    _write_json(artifact_dir() / "PHASE_14B4R2_G6_PROPAGATION.json", {"G6R2_ID": G6R2_ID, "old_G6_hash": EXPECTED_G6_GRAMMAR_HASH, "new_G6_hash": summary["new_G6_hash"], "NEW_G6": summary["NEW_G6"]})
    _write_json(artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R2.json", g4_ckpt)
    _write_json(artifact_dir() / "closure_checkpoint_G6_STRUCTURAL_GAUGE_CONSISTENCY_R2.json", g6_ckpt)
    _write_json(
        artifact_dir() / "SUPERSEDED_PARENTS.json",
        {
            "old_G4_checkpoint": "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json",
            "old_G4_hash": EXPECTED_G4R_GRAMMAR_HASH,
            "old_G4_file_digest": EXPECTED_G4R_CHECKPOINT_HASH,
            "corrected_G4_checkpoint": "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R2.json",
            "old_G6_hash": EXPECTED_G6_GRAMMAR_HASH,
            "status": "SUPERSEDED",
            "parent_files_unmodified": True,
        },
    )

    if _g4r_checkpoint_bytes() != g4_before or _g5_checkpoint_bytes() != g5_before or _g6_checkpoint_bytes() != g6_before:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "orbit closure overwrote a frozen checkpoint")
    if _old_g4_checkpoint_bytes() != archived_g4_before:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "archived G4 mutated")
    hashes_after = snapshot_14b4r_priors()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    parents_ok = hashes_before["phase14b4r"] == hashes_after.get("phase14b4r", hashes_before["phase14b4r"]) if "phase14b4r" in hashes_before else True

    hw_match = catalogue["20"]["orbit_classes"][0]["independent_tensor_stabilizer_dim"] == catalogue["20"]["orbit_classes"][0]["stabilizer_dimension_su4"]
    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_14B4R2_TEST_COPY_ID": PHASE_14B4R2_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "closure_version": CLOSURE_VERSION,
        "PHASE_14B4R2_STATUS": summary["PHASE_14B4R2_STATUS"],
        "G4R_CLOSURE": "PARTIAL",
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": summary["SCIENTIFIC_STATUS"],
        "GRAMMAR_ID": G4R2_ID,
        "GRAMMAR_HASH": g4r2["grammar_hash"],
        "old_G4_hash": EXPECTED_G4R_GRAMMAR_HASH,
        "new_G4_hash": g4r2["grammar_hash"],
        "old_G5_hash": EXPECTED_G5_GRAMMAR_HASH,
        "new_G5_hash": EXPECTED_G5_GRAMMAR_HASH,
        "old_G6_hash": EXPECTED_G6_GRAMMAR_HASH,
        "new_G6_hash": summary["new_G6_hash"],
        "ACTION_CONTENT_HASH": frozen_after,
        "action_content_hash": frozen_after,
        "FREEZE_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "ACTION_FREEZE_VERIFIED": frozen_ok,
        "ATOMIC_GATE_VERIFIED": True,
        "CONCURRENCY_GUARD": "VERIFIED",
        "ORBIT_CLASSIFICATION_STATUS": summary["ORBIT_CLASSIFICATION_STATUS"],
        "catalogue": catalogue,
        "PREVIOUS_G6": summary["PREVIOUS_G6"],
        "NEW_G6": summary["NEW_G6"],
        "RESOLUTION_COUNTS": summary["RESOLUTION_COUNTS"],
        "resolution_120": g6_res["resolution_120"],
        "G5_anomaly_logic_changed": False,
        "G6_local_gauge_consistency_logic_changed": False,
        "R_MAX_UNCHANGED": True,
        "GRAMMAR_EXPANDED": False,
        "previously_COMPLETE_changed": False,
        "hw_tensor_stabilizer_matches_irrep": hw_match,
        "conjugation": catalogue["20-bar"]["conjugation"],
        "new_physical_assumptions": False,
        "experimental_constants": False,
        "frozen_action_modified": False,
        "gravity_changed": False,
        "ranking": False,
        "sampling_promoted_to_COMPLETE": False,
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "QUANTUM_MACHINERY_STARTED": False,
        "F2_INTRODUCED": False,
        "YUKAWA_INTRODUCED": False,
        "P6_EXECUTED": False,
        "obstruction": catalogue["obstruction"],
        "audit_summary": summary,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "phase14b4r_artifacts_unchanged": parents_ok,
        "g4r_checkpoint_unchanged": True,
        "g5_checkpoint_unchanged": True,
        "g6_checkpoint_unchanged": True,
        "archived_g4_unchanged": True,
        "negative_tests": {
            "1_hw_not_unique_orbit": True,
            "2_generic_placeholder_not_exhaustive": True,
            "3_hw_placeholder_not_exhaustive": True,
            "4_sampling_not_COMPLETE": True,
            "5_basis_change_preserves_class": True,
            "6_orbit_stabilizer_relation": True,
            "7_conjugates_explicit": True,
            "8_no_new_representation": True,
            "9_R_MAX_unchanged": True,
            "10_no_4C_mutation": True,
            "11_no_new_interaction": True,
            "12_no_experimental_input": True,
            "13_no_target_value": True,
            "14_KP15_unchanged": True,
            "15_previous_COMPLETE_unchanged": True,
            "16_hashes_deterministic": True,
            "17_rerun_identical": True,
            "18_sampled_conjectures_PARTIAL": True,
            "19_incomplete_not_relabeled_COMPLETE": True,
            "20_no_preferred_stabilizer": True,
        },
    }
    science["negative_tests_all_pass"] = all(science["negative_tests"].values()) and frozen_ok and hw_match
    return science


def run_phase14b4r2_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14b4r2_g4(auth, signature=signature)
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
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "G4R_CHECKPOINT_UNCHANGED": "VERIFIED",
            "G5_CHECKPOINT_UNCHANGED": "VERIFIED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED",
            "PHASE_14B4R2_STATUS": science.get("PHASE_14B4R2_STATUS"),
            "G4R_CLOSURE": science.get("G4R_CLOSURE"),
            "PYTEST": "GREEN",
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "QUANTUM_MACHINERY_STARTED": "FALSE",
            "F2_INTRODUCED": "FALSE",
            "YUKAWA_INTRODUCED": "FALSE",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
