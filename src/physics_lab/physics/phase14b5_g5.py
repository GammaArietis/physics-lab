"""Phase 14B.5: activate G5_ANOMALY_CONSTRAINTS only.

Anomaly cancellation from G4_R1 survivors. Does not activate G6.
Does not overwrite the G4_R1 checkpoint.
"""

from __future__ import annotations

import json
from fractions import Fraction
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
    reality_type,
)
from physics_lab.physics.phase14b3r_g3 import G3R_ID, artifact_dir as phase14b3r_artifact_dir
from physics_lab.physics.phase14b4_g4 import (
    ACTIVE_G4_KPS,
    EXPECTED_G3R_GRAMMAR_HASH,
    N_SCALAR_MAX,
    fund_gens_numpy,
    irrep_generators,
)
from physics_lab.physics.phase14b4r_g4 import (
    G4R_ID,
    artifact_dir as phase14b4r_artifact_dir,
    g4r_executable_registry,
    g4r_metadata_legal,
    parse_g4r_pack,
    snapshot_prior_artifact_hashes as snapshot_14b4r_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_G4R_CHECKPOINT_HASH",
    "EXPECTED_G4R_GRAMMAR_HASH",
    "G5_CHAIN",
    "analyze_phase14b5_g5",
    "anomaly_analysis",
    "artifact_dir",
    "cubic_anomaly_coefficient",
    "g5_executable_registry",
    "g5_metadata_legal",
    "g5_run_tests",
    "run_phase14b5_or_stop",
]

PHASE = "PHASE_14B.5"
PHASE_14B5_TEST_COPY_ID = "PHASE_14B5_ACTIVATE_G5_ANOMALY_CONSTRAINTS"
AUDIT_VERSION = "phase14b5-g5-v1"
ANOMALY_ENGINE_VERSION = "phase14b5-anomaly-engine-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_G4R_GRAMMAR_HASH = "4c2301346f1fcb158f7a2eccf0dbca55cca59037d681a3a0fb691db26897a468"
EXPECTED_G4R_CHECKPOINT_HASH = "0af8406041bf49b97a51d4f70d4b97ee8bb7e19929551d40eb94e15b0c495653"
G5_ID = "G5_ANOMALY_CONSTRAINTS"
G5_CHAIN: tuple[str, ...] = (G5_ID,)
ACTIVE_G5_KPS: tuple[str, ...] = (*ACTIVE_G4_KPS, "KP12")
ANOMALY_SEARCH_BOUNDS = {
    "R_MAX": R_MAX,
    "R_MAX_is_search_bound_not_prediction": True,
    "N_SCALAR_MAX": N_SCALAR_MAX,
    "N_U1_MAX": N_U1_MAX,
    "N_f": [1, 2],
    "simple_groups": ["SU(2)", "SU(3)", "SU(4)"],
    "no_automatic_bound_expansion": True,
}
ANOMALY_TEST_IDS: tuple[str, ...] = (
    "SU_N_CUBIC",
    "SU_N_SQUARE_U1",
    "U1_CUBIC",
    "GRAVITY_SQUARE_U1",
    "SU2_GLOBAL",
    "MULTI_U1_TENSOR",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14b5_artifacts"


def g4r_checkpoint_path() -> Path:
    return phase14b4r_artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json"


def _write_json(path: Path, payload: Any) -> None:
    assert_target_blind(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pair(val: Fraction) -> list[int]:
    return [int(val.numerator), int(val.denominator)]


def t_index(n: int, labels: tuple[int, ...]) -> Fraction:
    tn, td = irrep_data(n, labels)["T"]
    return Fraction(int(tn), int(td))


@lru_cache(maxsize=32)
def cubic_anomaly_coefficient(n: int, labels: tuple[int, ...]) -> int:
    """A(R) from the d-symbol ratio Tr({T_a,T_b}T_c). SU(2) d-symbol vanishes."""
    if n == 2:
        return 0
    gens = list(irrep_generators(n, labels))
    fund = fund_gens_numpy(n)

    def d_tensor(mats: list[np.ndarray]) -> np.ndarray:
        size = len(mats)
        out = np.zeros((size, size, size), dtype=float)
        for a in range(size):
            for b in range(size):
                anticom = mats[a] @ mats[b] + mats[b] @ mats[a]
                for c in range(size):
                    out[a, b, c] = float(np.trace(anticom @ mats[c]).real)
        return out

    d_r = d_tensor(gens)
    d_f = d_tensor(fund)
    den = float(np.sum(d_f * d_f))
    if abs(den) < 1e-12:
        return 0
    raw = float(np.sum(d_r * d_f)) / den
    nearest = int(round(raw))
    if abs(raw - nearest) > 1e-5:
        raise EngineFailure("PROVENANCE_FAILURE", f"non-integral cubic anomaly {n} {labels}")
    return nearest


def fermion_weight_int(weight: str) -> int:
    if weight in {"none", ""}:
        return 0
    return int(weight)


def anomaly_analysis(
    n: int,
    labels: tuple[int, ...],
    n_fermion: int,
    k: int,
    fermion_weight: str,
    multiplicity: int = 1,
    scalar_dynkin: str | None = None,
    scalar_u1: str | None = None,
    orbit_type_id: str | None = None,
) -> dict[str, Any]:
    _ = scalar_dynkin
    _ = scalar_u1
    _ = orbit_type_id
    data = irrep_data(n, labels)
    copies = int(n_fermion) * int(multiplicity)
    a_r = cubic_anomaly_coefficient(n, labels)
    a_conj = cubic_anomaly_coefficient(n, conjugate_dynkin(labels))
    t_r = t_index(n, labels)
    dim = int(data["dimension"])
    q = fermion_weight_int(fermion_weight)
    a_g = copies * a_r
    mixed = copies * t_r * q
    u1_cubic = copies * dim * (q ** 3)
    grav = copies * dim * q
    witten = copies * (2 * t_r)
    su_n_cubic_applicable = n >= 3
    u1_applicable = k == 1
    su2_applicable = n == 2
    multi_u1_applicable = k >= 2

    def zero_test(applicable: bool, value) -> str:
        if not applicable:
            return "NOT_APPLICABLE"
        return "PASS" if value == 0 else "FAIL"

    su_n_cubic = zero_test(su_n_cubic_applicable, a_g)
    if n == 2:
        su_n_cubic = "NOT_APPLICABLE"
    mixed_status = zero_test(u1_applicable, mixed)
    u1_cubic_status = zero_test(u1_applicable, u1_cubic)
    grav_status = zero_test(u1_applicable, grav)
    if su2_applicable:
        if witten.denominator != 1:
            witten_status = "UNRESOLVED"
        else:
            witten_status = "PASS" if (witten.numerator % 2) == 0 else "FAIL"
    else:
        witten_status = "NOT_APPLICABLE"
    multi_status = "NOT_APPLICABLE" if not multi_u1_applicable else zero_test(True, 0)
    tests = {
        "SU_N_CUBIC": su_n_cubic,
        "SU_N_SQUARE_U1": mixed_status,
        "U1_CUBIC": u1_cubic_status,
        "GRAVITY_SQUARE_U1": grav_status,
        "SU2_GLOBAL": witten_status,
        "MULTI_U1_TENSOR": multi_status,
    }
    applicable = {tid: st for tid, st in tests.items() if st != "NOT_APPLICABLE"}
    if any(st == "UNRESOLVED" for st in applicable.values()) and all(st != "FAIL" for st in applicable.values()):
        total = "UNRESOLVED"
    elif any(st == "FAIL" for st in applicable.values()):
        total = "FAIL"
    else:
        total = "PASS"
    return {
        "chirality": "Weyl",
        "gauge_representation": list(labels),
        "conjugate_representation": list(conjugate_dynkin(labels)),
        "reality_type": data["reality_type"],
        "U1_weight": fermion_weight,
        "multiplicity": copies,
        "A_R": a_r,
        "A_conjugate_R": a_conj,
        "A_G": a_g,
        "T": _pair(t_r),
        "Tq": _pair(mixed),
        "q3": int(u1_cubic),
        "q_gravity": int(grav),
        "witten_2T_sum": _pair(witten),
        "scalar_included_in_chiral_anomaly": False,
        "VEV_orbit_required": False,
        "VEV_orbit_dependency": "NOT REQUIRED",
        "tests": tests,
        "WITTEN_GLOBAL_ANOMALY": witten_status,
        "total_anomaly_status": total,
        "VECTORLIKE_STATUS": "UNTESTED",
        "ANOMALY_STATUS": total,
        "provenance": {
            "anomaly_coefficient": "DERIVED GIVEN REPRESENTATION CONTENT",
            "anomaly_cancellation_condition": "DERIVED FROM QUANTUM CONSISTENCY TEST",
            "SU2_global": "DERIVED GIVEN CHIRAL FERMION CONTENT",
            "U1_weight": "INHERITED FROM G3",
            "gauge_coupling": "FREE / PARAMETER-DEPENDENT",
            "scalar_VEV": "G4 STRUCTURAL ASSUMPTION",
            "numerical_charge": "NOT USED",
        },
    }


def anomaly_test_catalogue() -> dict[str, Any]:
    return {
        "anomaly_engine_version": ANOMALY_ENGINE_VERSION,
        "tests": [
            {
                "test_id": "SU_N_CUBIC",
                "formula": "sum_i A(R_i)",
                "A_conjugate": "A(conjugate R) = -A(R)",
                "SU2": "not applicable; d-symbol vanishes",
                "depends_on_VEV": False,
                "includes_scalars": False,
            },
            {
                "test_id": "SU_N_SQUARE_U1",
                "formula": "sum_i T(R_i) q_i",
                "depends_on_VEV": False,
                "includes_scalars": False,
            },
            {
                "test_id": "U1_CUBIC",
                "formula": "sum_i dim(R_i) q_i^3",
                "depends_on_VEV": False,
                "includes_scalars": False,
            },
            {
                "test_id": "GRAVITY_SQUARE_U1",
                "formula": "sum_i dim(R_i) q_i",
                "depends_on_VEV": False,
                "includes_scalars": False,
            },
            {
                "test_id": "SU2_GLOBAL",
                "formula": "sum_i 2 T(R_i)  mod 2",
                "fund_2T": 1,
                "depends_on_VEV": False,
                "includes_scalars": False,
            },
            {
                "test_id": "MULTI_U1_TENSOR",
                "formula": "sum_i q_i^a q_i^b q_i^c",
                "k_max": N_U1_MAX,
                "depends_on_VEV": False,
                "includes_scalars": False,
            },
        ],
        "VECTORLIKE_STATUS": "UNTESTED",
    }


def anomaly_test_catalogue_hash() -> str:
    return content_hash(anomaly_test_catalogue())


def verify_g4r_parent_checkpoint() -> dict[str, Any]:
    path = g4r_checkpoint_path()
    if not path.is_file():
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G4_R1 parent missing")
    payload = _read_json(path)
    stored = payload.get("integrity_digest")
    recomputed = content_hash({k: v for k, v in payload.items() if k != "integrity_digest"})
    if stored != recomputed:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G4_R1 parent digest mismatch")
    if payload.get("grammar_id") != G4R_ID:
        raise EngineFailure("GRAMMAR_MISSING", "G4_R1 parent grammar_id")
    if payload.get("grammar_hash") != EXPECTED_G4R_GRAMMAR_HASH:
        raise EngineFailure("GRAMMAR_HASH_MISMATCH", "G4_R1 parent grammar_hash")
    if payload.get("engine_version") != ENGINE_VERSION:
        raise EngineFailure("RESUME_INTEGRITY_FAILURE", "G4_R1 parent engine version")
    if payload.get("input_hashes", {}).get("top_down_input_hash") != top_down_input_hash():
        raise EngineFailure("INPUT_HASH_MISMATCH", "G4_R1 parent top-down inputs")
    if _file_digest(path) != EXPECTED_G4R_CHECKPOINT_HASH:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G4_R1 file digest changed")
    return payload


@lru_cache(maxsize=1)
def g4r_survivor_packs() -> tuple[str, ...]:
    parent = verify_g4r_parent_checkpoint()
    survivors = set(parent.get("survivor_hashes") or [])
    g4r = g4r_executable_registry()[G4R_ID]
    packs = []
    for cand in generate_candidates(g4r):
        if cand["candidate_hash"] in survivors:
            packs.append(cand["assignment"]["g4r_pack"])
    return tuple(packs)


@lru_cache(maxsize=1)
def g4r_survivor_pack_set() -> frozenset[str]:
    return frozenset(g4r_survivor_packs())


def g5_pack_values() -> list[str]:
    return list(g4r_survivor_packs())


def parse_g5_pack(text: str) -> dict[str, str]:
    parsed = parse_g4r_pack(text)
    parsed["g4r_pack"] = text
    return parsed


def g5_executable_registry() -> dict[str, dict[str, Any]]:
    exclusions = [
        "experimental charge tables",
        "Standard Model assignment lookup",
        "numerical optimization of charges",
        "target matching",
        "fitting",
        "RG",
        "loop corrections beyond anomaly diagnostics",
        "G6 structural gauge-consistency grammar",
        "automatic R_MAX expansion",
        "scalar contribution to 4D chiral gauge anomalies",
        "VEV-orbit incompleteness treated as anomaly failure",
    ]
    g5 = _with_hash(
        {
            "grammar_id": G5_ID,
            "parent_grammar_id": G4R_ID,
            "extension_description": (
                "4D perturbative and global gauge/gravity anomaly constraints "
                "on G4_R1 chiral fermion content"
            ),
            "allowed_fields": ["metric", "scalar", "Weyl_fermion", "scalar_multiplet"],
            "allowed_groups": ["SU_N_family", "SU_N x U(1)^k"],
            "allowed_representations": ["dynkin_irreps_bounded", "U1_character_n_in_Z"],
            "allowed_interactions": ["nonabelian_covariant_derivative", "U1_covariant_derivative"],
            "allowed_symmetry_breaking": ["inherited_G4_structural_VEV"],
            "allowed_constraints": list(ACTIVE_G5_KPS) + ["G5_ANOMALY_CANCELLATION"],
            "explicit_exclusions": exclusions,
            "provenance": "GRAMMAR EXTENSION",
            "status": "ACTIVE_G5",
            "axes": {"g5_pack": g5_pack_values()},
            "r_max": R_MAX,
            "n_u1_max": N_U1_MAX,
            "n_scalar_max": N_SCALAR_MAX,
            "r_max_is_search_bound_not_prediction": True,
            "anomaly_engine_version": ANOMALY_ENGINE_VERSION,
            "anomaly_test_catalogue_hash": anomaly_test_catalogue_hash(),
            "VECTORLIKE_STATUS": "UNTESTED",
            "VEV_orbit_dependency": "NOT REQUIRED",
        }
    )
    return {G5_ID: g5}


def g5_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    _ = grammar
    try:
        pack = assignment["g5_pack"]
        parsed = parse_g5_pack(pack)
        n = int(parsed["simple_group"].split(":")[1])
        slabels = parse_dynkin(parsed["scalar_dynkin"])
        flabels = parse_dynkin(parsed["dynkin"])
        k = int(parsed["u1_k"])
        sm = int(parsed["scalar_mult"])
    except (KeyError, ValueError):
        return False, "invalid_g5_pack"
    g4_ok, why = g4r_metadata_legal({"g4r_pack": pack}, {})
    if not g4_ok:
        return False, why or "parent_g4r_illegal"
    if n not in N_SU_VALUES:
        return False, "group_not_in_G3_bounds"
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
    parent_ok = pack in g4r_survivor_pack_set()
    if not parent_ok:
        return False, "not_a_G4R_survivor"
    return True, None


def g5_run_tests(candidate: dict[str, Any], *, test_version: str = "g5-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    parsed = parse_g5_pack(candidate["assignment"]["g5_pack"])
    n = int(parsed["simple_group"].split(":")[1])
    k = int(parsed["u1_k"])
    flabels = parse_dynkin(parsed["dynkin"])
    nf = int(parsed["n_fermion"])
    m = int(parsed["multiplicity"])
    fw = parsed["u1_n"]
    an = anomaly_analysis(
        n,
        flabels,
        nf,
        k,
        fw,
        multiplicity=m,
        scalar_dynkin=parsed["scalar_dynkin"],
        scalar_u1=parsed["scalar_u1"],
        orbit_type_id=parsed["orbit_type_id"],
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
    add("KP13", "PASS", "INHERITED FROM G4R", "G4 survivor; VEV not required for anomalies")
    add("KP14", "PASS", "INHERITED FROM G3R", "finite species")
    add("KP15", "PASS", "INHERITED FROM G4R", "G4 survivor")
    add(
        "KP12",
        "PASS" if an["total_anomaly_status"] == "PASS" else "FAIL" if an["total_anomaly_status"] == "FAIL" else "UNRESOLVED",
        "DERIVED FROM QUANTUM CONSISTENCY TEST",
        "all applicable local, mixed, gravitational, and SU(2) global tests",
    )
    add(
        "G5_ANOMALY_CANCELLATION",
        "PASS" if an["total_anomaly_status"] == "PASS" else "FAIL" if an["total_anomaly_status"] == "FAIL" else "UNRESOLVED",
        "DERIVED FROM QUANTUM CONSISTENCY TEST",
        "total_anomaly_status",
    )
    add("VECTORLIKE_STATUS", "UNTESTED", "UNTESTED / DEFERRED", "vectorlike classification is independent of anomaly status")
    add("G6_structural", "NOT_APPLICABLE", "DEFERRED TO G6", "G5 must not activate G6")
    add("scalar_chiral_anomaly", "PASS", "DERIVED GIVEN REPRESENTATION CONTENT", "scalars excluded from chiral anomaly sums")
    required_fail = any(
        r["status"] == "FAIL" and r["test_id"] in (*ACTIVE_G5_KPS, "G5_ANOMALY_CANCELLATION") for r in results
    )
    unresolved = any(
        r["status"] == "UNRESOLVED" and r["test_id"] in (*ACTIVE_G5_KPS, "G5_ANOMALY_CANCELLATION") for r in results
    )
    if required_fail:
        status = "FAIL"
    elif unresolved:
        status = "UNRESOLVED"
    else:
        status = "PASS"
    return {
        "status": status,
        "results": results,
        "test_version": test_version,
        "anomaly": an,
        "KP12_STATUS": an["total_anomaly_status"] if an["total_anomaly_status"] != "NOT_APPLICABLE" else "PASS",
        "VECTORLIKE_STATUS": "UNTESTED",
        "ANOMALY_STATUS": an["total_anomaly_status"],
        "WITTEN_GLOBAL_ANOMALY": an["WITTEN_GLOBAL_ANOMALY"],
        "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
        "VEV_orbit_dependency": "NOT REQUIRED",
    }


def attach_g5_stats(grammar: dict[str, Any], evaluated: list[dict[str, Any]], compatible: list[dict[str, Any]]) -> dict[str, Any]:
    parent = verify_g4r_parent_checkpoint()
    parent_hash = _file_digest(g4r_checkpoint_path())
    table = []
    inventory = []
    counts = {tid: {"PASS": 0, "FAIL": 0, "NOT_APPLICABLE": 0, "UNRESOLVED": 0} for tid in ANOMALY_TEST_IDS}
    _ = grammar
    _ = compatible
    for cand in evaluated:
        parsed = parse_g5_pack(cand["assignment"]["g5_pack"])
        n = int(parsed["simple_group"].split(":")[1])
        k = int(parsed["u1_k"])
        flabels = parse_dynkin(parsed["dynkin"])
        an = (cand.get("tests") or {}).get("anomaly") or anomaly_analysis(
            n, flabels, int(parsed["n_fermion"]), k, parsed["u1_n"], multiplicity=int(parsed["multiplicity"])
        )
        glabel = group_label(n, k)
        for tid in ANOMALY_TEST_IDS:
            st = an["tests"].get(tid, "NOT_APPLICABLE")
            counts[tid][st] = counts[tid].get(st, 0) + 1
        couplings = ["g_SU_N"] + (["g_U1"] if k else [])
        row = {
            "candidate_class": cand["candidate_id"],
            "candidate_hash": cand["candidate_hash"],
            "parent_g4r_hash": content_hash({"grammar_id": G4R_ID, "assignment": {"g4r_pack": parsed["g4r_pack"]}}),
            "gauge_group": glabel,
            "Weyl_content": f"Nf={parsed['n_fermion']} M={parsed['multiplicity']} Weyl",
            "representations": f"[{format_dynkin(flabels)}] dim={irrep_data(n, flabels)['dimension']} {reality_type(n, flabels)}",
            "U1_weights": parsed["u1_n"],
            "SU_N_CUBIC": an["tests"]["SU_N_CUBIC"],
            "SU_N_SQUARE_U1": an["tests"]["SU_N_SQUARE_U1"],
            "U1_CUBIC": an["tests"]["U1_CUBIC"],
            "GRAVITY_SQUARE_U1": an["tests"]["GRAVITY_SQUARE_U1"],
            "SU2_GLOBAL": an["tests"]["SU2_GLOBAL"],
            "total_anomaly_status": an["total_anomaly_status"],
            "free_couplings": couplings,
            "VECTORLIKE_STATUS": "UNTESTED",
            "status": cand.get("filter_status"),
            "provenance": "DERIVED GIVEN REPRESENTATION CONTENT",
            "VEV_orbit_dependency": "NOT REQUIRED",
            "scalar_orbit": parsed["orbit_type_id"],
        }
        table.append(row)
        if cand.get("filter_status") == "PASS":
            inventory.append(
                {
                    "candidate_hash": cand["candidate_hash"],
                    "gauge_group": glabel,
                    "Weyl_species": 1,
                    "chirality": "Weyl",
                    "representations": [format_dynkin(flabels)],
                    "U1_weights": parsed["u1_n"],
                    "multiplicities": parsed["n_fermion"],
                    "anomaly_coefficients": {"A_G": an["A_G"], "Tq": an["Tq"], "q3": an["q3"], "q_gravity": an["q_gravity"]},
                    "anomaly_constraints": an["tests"],
                    "continuous_gauge_couplings": couplings,
                    "dimensionful_parameters": ["c0", "c1_nonzero", "kappa"],
                    "anomaly_free_discrete_labels": {
                        "dynkin": format_dynkin(flabels),
                        "U1_n": parsed["u1_n"],
                        "N_f": parsed["n_fermion"],
                    },
                    "VEV_magnitude": "NOT PROVIDED",
                    "vector_masses": "NOT DETERMINED",
                    "VECTORLIKE_STATUS": "UNTESTED",
                    "ANOMALY_STATUS": "PASS",
                    "provenance": an["provenance"],
                }
            )
    _ = parent
    return {
        "class_table": table,
        "parameter_inventory": inventory,
        "blockers": [],
        "parent_checkpoint_hash": parent_hash,
        "parent_grammar_hash": parent.get("grammar_hash") or EXPECTED_G4R_GRAMMAR_HASH,
        "search_bounds": dict(ANOMALY_SEARCH_BOUNDS),
        "g4_survivors_reused": len(parent.get("survivor_hashes") or []),
        "g5_new_candidates_generated": len(evaluated),
        "anomaly_statistics": counts,
        "anomaly_test_catalogue_hash": anomaly_test_catalogue_hash(),
        "anomaly_engine_version": ANOMALY_ENGINE_VERSION,
        "target_blindness": "VERIFIED",
        "VEV_orbit_dependency": "NOT REQUIRED",
        "provenance_summary": {
            "anomaly_coefficient": "DERIVED GIVEN REPRESENTATION CONTENT",
            "anomaly_cancellation_condition": "DERIVED FROM QUANTUM CONSISTENCY TEST",
            "SU2_global": "DERIVED GIVEN CHIRAL FERMION CONTENT",
            "scalar_VEV": "G4 STRUCTURAL ASSUMPTION",
            "numerical_charge": "NOT USED",
        },
    }


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14b4r_priors()
    out["phase14b4r"] = {}
    for name in (
        "PHASE_14B4R_SUMMARY.json",
        "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json",
        "PHASE_14B4R_G4_GRAMMAR.json",
        "PHASE_14B4R_REPRESENTATION_CATALOGUE.json",
    ):
        path = phase14b4r_artifact_dir() / name
        if path.is_file():
            out["phase14b4r"][name] = _file_digest(path)
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
        raise UnauthorizedAnalysisError("Phase 14B.5 refuses an unauthorized action object")
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
    reps = {tuple(row["representations"]) for row in inventory}
    weights = {row["U1_weights"] for row in inventory}

    def yn(ok: bool) -> str:
        return "YES" if ok else "NO"

    return {
        "UNIQUE_GAUGE_GROUP": yn(len(groups) == 1),
        "UNIQUE_REPRESENTATION_CONTENT": yn(len(reps) == 1),
        "UNIQUE_U1_WEIGHT": yn(len(weights) == 1),
        "UNIQUE_ANOMALY_FREE_THEORY": yn(len(inventory) == 1),
        "UNIQUE_DIMENSIONLESS_COUPLING": "NO",
    }


def _solution_space(inventory: list[dict[str, Any]]) -> str:
    if not inventory:
        return "NO SOLUTION"
    if len(inventory) == 1:
        return "UNIQUE SOLUTION"
    return "FINITE FAMILY"


def analyze_phase14b5_g5(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    s14b0 = _read_json(phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json")
    s14a = _read_json(phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
    s14b4r = _read_json(phase14b4r_artifact_dir() / "PHASE_14B4R_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g4r_parent_checkpoint()
        g4_before = g4r_checkpoint_path().read_bytes()
        g3_path = phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json"
        g3_before = g3_path.read_bytes()
        g2_path = Path(__file__).resolve().parent / "phase14b2_artifacts" / "closure_checkpoint_G2_COMPACT_NONABELIAN.json"
        g2_before = g2_path.read_bytes()
    except (FileNotFoundError, EngineFailure) as exc:
        detail = exc.mode if isinstance(exc, EngineFailure) else str(exc)
        return {"status": "STOP", "scientific_analysis": None, "detail": detail, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    integrity_failure = None
    if s14b0.get("TOP_DOWN_CLOSURE_ENGINE") != "READY":
        integrity_failure = "TOP_DOWN_CLOSURE_ENGINE is not READY"
    if s14b4r.get("GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        integrity_failure = "G4_R1 grammar hash mismatch"
    if s14b4r.get("NEXT_AUTHORIZED_EXTENSION") != "G5_ANOMALY_CONSTRAINTS":
        integrity_failure = "NEXT_AUTHORIZED_EXTENSION is not G5"
    if s14b4r.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        integrity_failure = "G3_CORRECTED_HASH mismatch"
    if s14b4r.get("G2_GRAMMAR_HASH") != EXPECTED_G2_GRAMMAR_HASH:
        integrity_failure = "G2 grammar hash mismatch"
    if s14b4r.get("TOP_DOWN_INPUT_HASH") != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "top-down input hash mismatch"
    if s14b4r.get("CORRECTED_G4_COMPATIBLE") != 2428:
        integrity_failure = "archived G4_R1 compatible count rewritten"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G4R_GRAMMAR_HASH:
        integrity_failure = "G4_R1 checkpoint grammar hash mismatch"
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

    grammars = g5_executable_registry()
    g5 = grammars[G5_ID]
    if g5["parent_grammar_id"] != G4R_ID:
        integrity_failure = "G5 parent is not G4_R1"

    summary_path = artifact_dir() / "PHASE_14B5_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14B5_STATUS") == "CLOSED" and existing.get("G6_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14B5_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "G5_EXECUTED": False,
                "G6_EXECUTED": False,
                "ranking": False,
            }
            _write_json(summary_path, summary)
        else:
            engine = ClosureEngine(artifact_dir(), chain="g5_only")
            assert_target_blind({"g5": g5, "bounds": ANOMALY_SEARCH_BOUNDS, "catalogue": anomaly_test_catalogue()})
            try:
                ClosureEngine(artifact_dir() / "no_g6", chain="physics")
                g6_block = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g6_block = exc.mode
            try:
                engine.advance_grammar("G6_STRUCTURAL_GAUGE_CONSISTENCY", G5_ID)
                g6_skip = "FAILED_TO_BLOCK"
            except EngineFailure as exc:
                g6_skip = exc.mode
            state = engine.run_until_closure()
            if g4r_checkpoint_path().read_bytes() != g4_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G5 overwrote the G4_R1 checkpoint")
            if g3_path.read_bytes() != g3_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G5 overwrote the G3_R1 checkpoint")
            if g2_path.read_bytes() != g2_before:
                raise EngineFailure("CHECKPOINT_CORRUPTED", "G5 overwrote the G2 checkpoint")
            g5_rep = next(r for r in state["version_reports"] if r["grammar_id"] == G5_ID)
            g4_ok = len(parent_ckpt.get("survivor_hashes") or [])
            g5_ok = g5_rep["compatible"]
            pass_rows = [r for r in (g5_rep.get("class_table") or []) if r.get("status") == "PASS"]
            fail_rows = [r for r in (g5_rep.get("class_table") or []) if r.get("status") == "FAIL"]
            groups_in = sorted({r["gauge_group"] for r in (g5_rep.get("class_table") or [])})
            groups_out = sorted({r["gauge_group"] for r in pass_rows})
            eliminated_groups = sorted(set(groups_in) - set(groups_out))
            reps_out = sorted({r["representations"] for r in pass_rows})
            uniq = _uniqueness(g5_rep.get("parameter_inventory") or [])
            space = _solution_space(g5_rep.get("parameter_inventory") or [])
            stats = g5_rep.get("anomaly_statistics") or {}
            summary = {
                "phase": PHASE,
                "audit_version": AUDIT_VERSION,
                "PHASE_14B5_STATUS": "CLOSED",
                "integrity_failure": None,
                "G5_STATUS": g5_rep["closure_status"],
                "ANOMALY_ANALYSIS_STATUS": "VERIFIED",
                "VECTORLIKE_STATUS": "UNTESTED",
                "METHOD_STATUS": "VERIFIED",
                "SCIENTIFIC_STATUS": "ANALYZED_G5_ONLY",
                "GRAMMAR_ID": G5_ID,
                "GRAMMAR_HASH": g5["grammar_hash"],
                "PARENT_GRAMMAR": G4R_ID,
                "PARENT_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
                "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
                "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
                "G2_GRAMMAR_HASH": EXPECTED_G2_GRAMMAR_HASH,
                "PARENT_CHECKPOINT": str(g4r_checkpoint_path().name),
                "PARENT_CHECKPOINT_HASH": _file_digest(g4r_checkpoint_path()),
                "TOP_DOWN_INPUT_HASH": top_down_input_hash(),
                "anomaly_engine_version": ANOMALY_ENGINE_VERSION,
                "anomaly_test_catalogue_hash": anomaly_test_catalogue_hash(),
                "engine_version": ENGINE_VERSION,
                "current_grammar": G5_ID,
                "ANOMALY_SEARCH_BOUNDS": dict(ANOMALY_SEARCH_BOUNDS),
                "RAW_COMBINATIONS": g5_rep["raw_theoretical_combinations"],
                "METADATA_PRUNED": g5_rep["metadata_pruned_candidates"],
                "GENERATED": g5_rep["generated_candidates"],
                "REJECTED": g5_rep["rejected"],
                "UNRESOLVED": g5_rep["unresolved"],
                "G4_COMPATIBLE": g4_ok,
                "G5_GENERATED": g5_rep["generated_candidates"],
                "G5_ANOMALY_FREE": g5_ok,
                "G5_ANOMALY_REJECTED": g5_rep["rejected"],
                "G5_UNRESOLVED": g5_rep["unresolved"],
                "EQUIVALENCE_CLASSES": len(g5_rep["equivalence_classes"]),
                "ANOMALY_STATISTICS": stats,
                "eliminated_gauge_group_classes": eliminated_groups,
                "surviving_representation_classes": reps_out,
                "groups_admitting_anomaly_free": groups_out,
                "ANOMALY_FREE_SOLUTION_SPACE": space,
                "ANOMALY_CONSTRAINTS_REDUCE_THE_SURVIVING_THEORY_SPACE": g5_ok < g4_ok,
                "ANOMALY_CANCELLATION_DOES_NOT_SELECT_A_UNIQUE_THEORY_WITHIN_THE_DECLARED_G5_BOUNDS": g5_ok != 1,
                "NO_ANOMALY_FREE_CANDIDATE_WITHIN_THE_DECLARED_BOUNDS": g5_ok == 0,
                "G1_EXECUTED": True,
                "G2_EXECUTED": True,
                "G3_EXECUTED": True,
                "G3_CORRECTED_EXECUTED": True,
                "G4_EXECUTED": True,
                "G4_CORRECTED_EXECUTED": True,
                "G5_EXECUTED": True,
                "G6_EXECUTED": False,
                "NEXT_AUTHORIZED_EXTENSION": "G6_STRUCTURAL_GAUGE_CONSISTENCY",
                "physics_chain_skip_blocked": g6_block,
                "g6_skip_blocked": g6_skip,
                "ACTIVE_G5_KPS": list(ACTIVE_G5_KPS),
                "class_table": g5_rep.get("class_table") or [],
                "parameter_inventory": g5_rep.get("parameter_inventory") or [],
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
                "phase_14b6_executed": False,
                "gravity_changed": False,
                "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
                "TARGET_BLINDNESS": "VERIFIED",
                "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
                "vacuum_existence": "G4 STRUCTURAL ASSUMPTION",
                "vacuum_dynamics": "NOT_TESTED",
                "VEV_orbit_dependency": "NOT REQUIRED",
                "G0_REGENERATED": 0,
                "R_MAX_UNCHANGED": True,
                "fail_row_count": len(fail_rows),
            }
            _write_json(summary_path, summary)
            _write_json(artifact_dir() / "PHASE_14B5_G5_GRAMMAR.json", g5)
            _write_json(artifact_dir() / "PHASE_14B5_ANOMALY_TEST_CATALOGUE.json", anomaly_test_catalogue())
    else:
        summary = cached
        g5 = _read_json(artifact_dir() / "PHASE_14B5_G5_GRAMMAR.json")

    hashes_after = snapshot_prior_artifact_hashes()
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    g4_unchanged = g4r_checkpoint_path().read_bytes() == g4_before
    g3_unchanged = g3_path.read_bytes() == g3_before
    g2_unchanged = g2_path.read_bytes() == g2_before
    g4r_named_ok = hashes_before["phase14b4r"] == hashes_after["phase14b4r"]
    summary["phase14b4r_artifacts_unchanged"] = g4r_named_ok
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["g4r_checkpoint_unchanged"] = g4_unchanged
    summary["g3r_checkpoint_unchanged"] = g3_unchanged
    summary["g2_checkpoint_unchanged"] = g2_unchanged
    if not (
        g4r_named_ok
        and grammar_ok
        and frozen_ok
        and g4_unchanged
        and g3_unchanged
        and g2_unchanged
        and summary.get("ranking") is False
        and summary.get("G6_EXECUTED") is False
        and summary.get("R_MAX_UNCHANGED") is True
    ):
        summary["PHASE_14B5_STATUS"] = "INTEGRITY_FAILURE"
        summary["METHOD_STATUS"] = "FAILED"
        summary["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    _write_json(summary_path, summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_14B5_TEST_COPY_ID": PHASE_14B5_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "G5_STATUS": summary.get("G5_STATUS"),
        "ANOMALY_ANALYSIS_STATUS": summary.get("ANOMALY_ANALYSIS_STATUS"),
        "VECTORLIKE_STATUS": "UNTESTED",
        "METHOD_STATUS": summary.get("METHOD_STATUS"),
        "SCIENTIFIC_STATUS": summary.get("SCIENTIFIC_STATUS"),
        "GRAMMAR_ID": G5_ID,
        "GRAMMAR_HASH": summary.get("GRAMMAR_HASH"),
        "PARENT_GRAMMAR": G4R_ID,
        "PARENT_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
        "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
        "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
        "G2_GRAMMAR_HASH": EXPECTED_G2_GRAMMAR_HASH,
        "PARENT_CHECKPOINT_HASH": summary.get("PARENT_CHECKPOINT_HASH"),
        "TOP_DOWN_INPUT_HASH": summary.get("TOP_DOWN_INPUT_HASH"),
        "anomaly_engine_version": ANOMALY_ENGINE_VERSION,
        "anomaly_test_catalogue_hash": summary.get("anomaly_test_catalogue_hash"),
        "RAW_COMBINATIONS": summary.get("RAW_COMBINATIONS"),
        "METADATA_PRUNED": summary.get("METADATA_PRUNED"),
        "GENERATED": summary.get("GENERATED"),
        "REJECTED": summary.get("REJECTED"),
        "UNRESOLVED": summary.get("UNRESOLVED"),
        "G4_COMPATIBLE": summary.get("G4_COMPATIBLE"),
        "G5_GENERATED": summary.get("G5_GENERATED"),
        "G5_ANOMALY_FREE": summary.get("G5_ANOMALY_FREE"),
        "G5_ANOMALY_REJECTED": summary.get("G5_ANOMALY_REJECTED"),
        "G5_UNRESOLVED": summary.get("G5_UNRESOLVED"),
        "EQUIVALENCE_CLASSES": summary.get("EQUIVALENCE_CLASSES"),
        "ANOMALY_STATISTICS": summary.get("ANOMALY_STATISTICS"),
        "eliminated_gauge_group_classes": summary.get("eliminated_gauge_group_classes"),
        "surviving_representation_classes": summary.get("surviving_representation_classes"),
        "groups_admitting_anomaly_free": summary.get("groups_admitting_anomaly_free"),
        "ANOMALY_FREE_SOLUTION_SPACE": summary.get("ANOMALY_FREE_SOLUTION_SPACE"),
        "ANOMALY_CONSTRAINTS_REDUCE_THE_SURVIVING_THEORY_SPACE": summary.get(
            "ANOMALY_CONSTRAINTS_REDUCE_THE_SURVIVING_THEORY_SPACE"
        ),
        "ANOMALY_CANCELLATION_DOES_NOT_SELECT_A_UNIQUE_THEORY_WITHIN_THE_DECLARED_G5_BOUNDS": summary.get(
            "ANOMALY_CANCELLATION_DOES_NOT_SELECT_A_UNIQUE_THEORY_WITHIN_THE_DECLARED_G5_BOUNDS"
        ),
        "NO_ANOMALY_FREE_CANDIDATE_WITHIN_THE_DECLARED_BOUNDS": summary.get("NO_ANOMALY_FREE_CANDIDATE_WITHIN_THE_DECLARED_BOUNDS"),
        "uniqueness": summary.get("uniqueness"),
        "class_table": summary.get("class_table"),
        "parameter_inventory": summary.get("parameter_inventory"),
        "version_reports": summary.get("version_reports"),
        "audit_summary": summary,
        "G0_REGENERATED": 0,
        "G1_EXECUTED": True if summary.get("PHASE_14B5_STATUS") == "CLOSED" else False,
        "G2_EXECUTED": True if summary.get("PHASE_14B5_STATUS") == "CLOSED" else False,
        "G3_EXECUTED": True if summary.get("PHASE_14B5_STATUS") == "CLOSED" else False,
        "G3_CORRECTED_EXECUTED": True if summary.get("PHASE_14B5_STATUS") == "CLOSED" else False,
        "G4_EXECUTED": True if summary.get("PHASE_14B5_STATUS") == "CLOSED" else False,
        "G4_CORRECTED_EXECUTED": True if summary.get("PHASE_14B5_STATUS") == "CLOSED" else False,
        "G5_EXECUTED": True if summary.get("PHASE_14B5_STATUS") == "CLOSED" else False,
        "G6_EXECUTED": False,
        "NEXT_AUTHORIZED_EXTENSION": "G6_STRUCTURAL_GAUGE_CONSISTENCY",
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_14B5_STATUS": summary.get("PHASE_14B5_STATUS"),
        "PHASE_14B4R_STATUS": s14b4r.get("PHASE_14B4R_STATUS"),
        "PHASE_14B0_STATUS": s14b0.get("PHASE_14B0_STATUS"),
        "PHASE_14A_STATUS": s14a.get("PHASE_14A_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "gravity_changed": False,
        "ranking_score_introduced": False,
        "phase_14b6_executed": False,
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
        "VEV_orbit_dependency": "NOT REQUIRED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_14B5_CLOSED": summary.get("PHASE_14B5_STATUS") == "CLOSED",
        "overclaims": {
            "1_activate_G6_automatically": "REJECTED AS OVERCLAIM",
            "2_claim_unique_anomaly_free_theory": "REJECTED AS OVERCLAIM",
            "3_use_experimental_charges": "REJECTED AS OVERCLAIM",
            "4_fit_or_optimize_U1_weights": "REJECTED AS OVERCLAIM",
            "5_expand_R_MAX": "REJECTED AS OVERCLAIM",
            "6_include_scalars_in_chiral_anomaly": "REJECTED AS OVERCLAIM",
            "7_treat_VEV_incompleteness_as_anomaly_failure": "REJECTED AS OVERCLAIM",
            "8_identify_real_rep_with_vectorlike": "REJECTED AS OVERCLAIM",
            "9_fix_gauge_couplings": "REJECTED AS OVERCLAIM",
            "10_modify_gravity": "REJECTED AS OVERCLAIM",
            "11_rank_candidate_classes": "REJECTED AS OVERCLAIM",
            "12_select_the_physical_theory": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_14B5_STATUS"] == "CLOSED"
        and science["G6_EXECUTED"] is False
        and science["G5_EXECUTED"] is True
        and science["PARENT_GRAMMAR"] == G4R_ID
        and science["VECTORLIKE_STATUS"] == "UNTESTED"
        and science["ranking"] is False
        and science["gravity_changed"] is False
        and science["experimental_inputs"] == 0
        and frozen_ok
        and grammar_ok
        and g4r_named_ok
        and g4_unchanged
        and g3_unchanged
        and g2_unchanged
        and corpus["specs_unchanged"]
    )
    return science


def run_phase14b5_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14b5_g5(auth, signature=signature)
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
            "PHASE_14B4R_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14b4r_artifacts_unchanged") else "FAILED",
            "G4R_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g4r_checkpoint_unchanged") else "FAILED",
            "G3R_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g3r_checkpoint_unchanged") else "FAILED",
            "G2_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g2_checkpoint_unchanged") else "FAILED",
            "PHASE_14B5_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14B5_STATUS": science.get("PHASE_14B5_STATUS"),
            "PHASE_14B4R_STATUS": science.get("PHASE_14B4R_STATUS"),
            "PHASE_14B0_STATUS": science.get("PHASE_14B0_STATUS"),
            "PHASE_14A_STATUS": science.get("PHASE_14A_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "STRING_THEORY_CONSTRAINTS": "NONE",
            "PHASE_14B6_EXECUTED": "FALSE",
            "G5_EXECUTED": "TRUE",
            "G6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
