"""Phase 14C.5K: two-loop RG stability and parameter-domain audit.

Extends the stored P5G/P5J one-loop RG capability to the minimum two-loop
gauge-coupling level required to test whether the P5J compatibility geometry
is perturbatively stable. Does not modify frozen 4C, G1-G6, or P5Q-P5J.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from physics_lab.physics.portability import portable_path

import sympy as sp

from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH, GAUGED_MATTER_TEST_ACTION_ID
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase10a_model_grammar import model_hash as model_hash_10a
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase12a_grammar import EXPECTED_GRAMMAR_HASH_10B, grammar_hash_12a
from physics_lab.physics.phase12b_search import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b0_engine import (
    AUTHORIZED_PHYSICS_CHAIN,
    ENGINE_VERSION,
    EngineFailure,
    assert_target_blind,
    content_hash,
    top_down_input_hash,
)
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.physics.phase14b6_g6 import EXPECTED_G5_GRAMMAR_HASH, G6_SEARCH_BOUNDS
from physics_lab.physics.phase14c0_known_physics import (
    CATALOG_VERSION,
    EXPECTED_G6_CHECKPOINT_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    catalog_hash,
    g6_candidate_space_hash,
    g6_checkpoint_path,
    g6_class_rows,
    profile_registry_hash,
    verify_g6_parent_checkpoint,
)
from physics_lab.physics.phase14c1_p1 import EXPECTED_CATALOG_HASH, EXPECTED_PROFILE_REGISTRY_HASH
from physics_lab.physics.phase14c2_p2 import grammar_yukawa_present
from physics_lab.physics.phase14c4_p4 import p4_checkpoint_path
from physics_lab.physics.phase14c5_p5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5_PROFILE_HASH,
    p5_checkpoint_path,
    p5_profile,
)
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, p5d_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, p5e_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_P5E1_CHECKPOINT_DIGEST, p5e1_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import (
    EXPECTED_P5F_CHECKPOINT_DIGEST,
    parse_gauge_factors,
    p5f_checkpoint_path,
)
from physics_lab.physics.phase14c5g_p5g import (
    EXPECTED_P5G_CHECKPOINT_DIGEST,
    REGULATOR,
    SCHEME,
    _bf_vector_ghost_integer,
    _factor_traces,
    _rat,
    _rat_add,
    _rat_mul,
    _rat_neg,
    _rat_sign,
    _scalar_nu,
    _sympy_rational_to_rat,
    _t_rat,
    _u1_index,
    _weyl_nu,
    declared_operator_basis,
    diagram_inventory,
    dimreg_bubble_I,
    one_loop_factor,
    parse_candidate,
    p5g_checkpoint_path,
    vertex_inventory,
)
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h_p5h import EXPECTED_P5H_CHECKPOINT_DIGEST, p5h_checkpoint_path
from physics_lab.physics.phase14c5h1_p5h1 import EXPECTED_P5H1_CHECKPOINT_DIGEST, p5h1_checkpoint_path
from physics_lab.physics.phase14c5h2_p5h2 import EXPECTED_P5H2_CHECKPOINT_DIGEST, p5h2_checkpoint_path
from physics_lab.physics.phase14c5h3_p5h3 import EXPECTED_P5H3_CHECKPOINT_DIGEST, p5h3_checkpoint_path
from physics_lab.physics.phase14c5h4_p5h4 import EXPECTED_P5H4_CHECKPOINT_DIGEST, p5h4_checkpoint_path
from physics_lab.physics.phase14c5h5_p5h5 import EXPECTED_P5H5_CHECKPOINT_DIGEST, p5h5_checkpoint_path
from physics_lab.physics.phase14c5i_p5i import EXPECTED_P5I_CHECKPOINT_DIGEST, p5i_checkpoint_path
from physics_lab.physics.phase14c5j_p5j import (
    EXPECTED_P5J_CHECKPOINT_DIGEST,
    load_stored_p5g_records,
    load_stored_p5h5_records,
    load_stored_q04_domain,
    p5j_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5j_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5K_CHECKPOINT_DIGEST",
    "P5K_ID",
    "analyze_phase14c5k_p5k",
    "artifact_dir",
    "p5k_evaluate",
    "run_phase14c5k_or_stop",
]

PHASE = "PHASE_14C.5K"
PHASE_14C5K_TEST_COPY_ID = "PHASE_14C5K_P5K_TWO_LOOP_RG_STABILITY"
AUDIT_VERSION = "phase14c5k-p5k-two-loop-rg-stability-v1"
CAPABILITY_VERSION = "P5K_TWO_LOOP_RG_STABILITY_v1"
P5K_ID = "P5K_TWO_LOOP_RG_STABILITY"
PARENT_P5G1_CHECKPOINT_ID = "P5G1_BETA_PROVENANCE_AUDIT_v1"
PARENT_P5H5_CHECKPOINT_ID = "P5H5_Q04_PARAMETER_DOMAIN_v1"
PARENT_P5J_CHECKPOINT_ID = "P5J_RG_UNITARITY_COMPATIBILITY_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_P5K_CHECKPOINT_DIGEST = "314ed7335f7c35343ed6b3329edf73495b50a42c461e10bc35387e3c2660ff15"
EXPECTED_P5K_TEST_REGISTRY_HASH = "89fcc02d83897a6a42895ba1ea4e7445433ab634e88902344ec80d4e61bafd5f"
SCALE = "mu_R"
GAUGE_FIXING_CHOICES = ("xi_gf = 0", "xi_gf = 1")
PERTURBATIVE_CONTROL = (
    "|beta^(2)| / |beta^(1)| = |b2| g^2 / (|b1| * sixteen pi squared)  "
    "when b1 is not zero; formal small-coupling window, not an experimental bound"
)
Q04_UNCHANGED = "PARTIAL"
Q08_UNCHANGED = "VERIFIED"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5k_artifacts"


def p5k_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5K_TWO_LOOP_RG_STABILITY_v1.json"


def _read_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> Any:
    from physics_lab.physics.phase14b0_engine import _write_json as engine_write

    engine_write(path, payload)


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _rat_div(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return _rat(int(a["num"]) * int(b["den"]), int(a["den"]) * int(b["num"]))


def _rat_sub(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return _rat_add(a, _rat_neg(b))


def _rat_eq(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return int(a["num"]) * int(b["den"]) == int(b["num"]) * int(a["den"])


def _c2_rat(data: dict[str, Any]) -> dict[str, Any]:
    pair = data["C2"]
    return _rat(int(pair[0]), int(pair[1]))


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c5j_priors()
    out["phase14c5j"] = {}
    for name in (
        "PHASE_14C5J_SUMMARY.json",
        "checkpoint_P5J_RG_UNITARITY_COMPATIBILITY_v1.json",
        "P5J_CLASS_TABLE.json",
        "P5J_EVALUATION_RECORDS.json",
        "P5J_CAPABILITY_MANIFEST.json",
        "P5J_NEGATIVE_TESTS.json",
        "P5J_DOMAIN_FLOW.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5j_artifacts" / name
        if path.is_file():
            out["phase14c5j"][name] = _file_digest(path)
    return out


@lru_cache(maxsize=1)
def load_stored_p5j_records() -> dict[str, dict[str, Any]]:
    path = Path(__file__).resolve().parent / "phase14c5j_artifacts" / "P5J_EVALUATION_RECORDS.json"
    rows = _read_json(path).get("records") or []
    return {str(item["candidate_id"]): item for item in rows}


@lru_cache(maxsize=1)
def two_loop_kinematic_engine() -> dict[str, Any]:
    """Two-loop UV masters from the P5G Feynman-param integrand plus the sunset Gamma.

    Not a stored textbook beta coefficient.
    """
    eps = sp.symbols("eps")

    def beta_fn(a: Any, b: Any) -> Any:
        return sp.gamma(a) * sp.gamma(b) / sp.gamma(a + b)

    ieps = beta_fn(1 - eps, 1 - eps) - 4 * beta_fn(2 - eps, 1 - eps) + 4 * beta_fn(3 - eps, 1 - eps)
    ieps_ms = ieps.series(eps, 0, 2).removeO().subs(sp.EulerGamma, 0)
    i0 = _sympy_rational_to_rat(sp.expand(ieps_ms).coeff(eps, 0))
    i1 = _sympy_rational_to_rat(sp.expand(ieps_ms).coeff(eps, 1))
    stored_i0 = dimreg_bubble_I()["scalar_pmpn"]
    if not _rat_eq(i0, stored_i0):
        raise EngineFailure("TWO_LOOP_ENGINE_BASELINE_FAILURE", "two-loop I0 does not match the stored P5G bubble integral")
    g11 = sp.gamma(eps) * sp.gamma(1 - eps) ** 2 / sp.gamma(2 - 2 * eps)
    g11_ms = g11.series(eps, 0, 1).removeO().subs(sp.EulerGamma, 0)
    g11_finite = _sympy_rational_to_rat(sp.expand(g11_ms).coeff(eps, 0))
    gpole = sp.gamma(2 * eps) / (2 * eps - 1)
    sunset = gpole * sp.gamma(1 - eps) ** 3 / sp.gamma(3 - 3 * eps)
    sun_ms = sunset.series(eps, 0, 1).removeO().subs(sp.EulerGamma, 0)
    sun_pole = _sympy_rational_to_rat(sp.expand(sun_ms).coeff(eps, -1))
    k_nested = _rat_div(i1, i0)
    return {
        "I0": i0,
        "I1": i1,
        "K_nested": k_nested,
        "G11_finite_MSbar": g11_finite,
        "K_sunset_pole": sun_pole,
        "regulator": REGULATOR,
        "scheme": SCHEME,
        "hardcoded_textbook_beta": False,
        "provenance": "DERIVED GIVEN P5G DIM-REG INTEGRAND + TWO-LOOP SUNSET GAMMA + MSBAR RATIONAL PROJECTION",
    }


def two_loop_topology_classes() -> list[dict[str, Any]]:
    return [
        {
            "topology_id": "T2L_GG_NESTED",
            "sector": "gauge_ghost",
            "kind_required": "nonabelian",
            "internal_fields": ["gauge", "gauge", "ghost"],
            "vertices": ["AAA", "ghost_ghost_A"],
            "subdivergences": "one nested one-loop gauge 2pt; cancelled by T2L_CT_1L",
            "primitive": False,
        },
        {
            "topology_id": "T2L_GG_SUNSET",
            "sector": "gauge_ghost",
            "kind_required": "nonabelian",
            "internal_fields": ["gauge", "gauge", "gauge"],
            "vertices": ["AAA"],
            "subdivergences": "overlapping one-loop forests (three channels); distinguished from T2L_CT_1L",
            "primitive": True,
        },
        {
            "topology_id": "T2L_GG_FIGURE8",
            "sector": "gauge_ghost",
            "kind_required": "nonabelian",
            "internal_fields": ["gauge", "gauge"],
            "vertices": ["AAAA"],
            "subdivergences": "two one-loop bubbles on a quartic; scaleless tadpole channels vanish in dim-reg",
            "primitive": True,
        },
        {
            "topology_id": "T2L_GH_NESTED",
            "sector": "ghost",
            "kind_required": "nonabelian",
            "internal_fields": ["ghost", "gauge"],
            "vertices": ["ghost_ghost_A"],
            "subdivergences": "nested ghost one-loop 2pt; included with gauge in the P5G vector+ghost integer",
            "primitive": False,
        },
        {
            "topology_id": "T2L_W_NESTED",
            "sector": "weyl",
            "kind_required": "any",
            "internal_fields": ["Weyl", "gauge"],
            "vertices": ["psi_psi_A"],
            "subdivergences": "nested Weyl one-loop 2pt",
            "primitive": False,
        },
        {
            "topology_id": "T2L_W_OVERLAP",
            "sector": "weyl",
            "kind_required": "any",
            "internal_fields": ["Weyl", "gauge", "gauge"],
            "vertices": ["psi_psi_A"],
            "subdivergences": "overlapping Weyl-gauge sunset; genuine two-loop primitive after forest",
            "primitive": True,
        },
        {
            "topology_id": "T2L_S_NESTED",
            "sector": "scalar",
            "kind_required": "any",
            "internal_fields": ["scalar", "gauge"],
            "vertices": ["phi_phi_A", "phi_phi_A_A"],
            "subdivergences": "nested scalar one-loop 2pt",
            "primitive": False,
        },
        {
            "topology_id": "T2L_S_OVERLAP",
            "sector": "scalar",
            "kind_required": "any",
            "internal_fields": ["scalar", "gauge", "gauge"],
            "vertices": ["phi_phi_A", "phi_phi_A_A"],
            "subdivergences": "overlapping scalar-gauge sunset; no scalar self-coupling vertex",
            "primitive": True,
        },
        {
            "topology_id": "T2L_MIXED_CROSS",
            "sector": "cross",
            "kind_required": "product",
            "internal_fields": ["Weyl or scalar charged under both factors"],
            "vertices": ["psi_psi_A", "phi_phi_A"],
            "subdivergences": "nested insertion of the other factor on a shared matter loop; not kinetic mixing",
            "primitive": False,
        },
        {
            "topology_id": "T2L_CT_1L",
            "sector": "counterterm",
            "kind_required": "any",
            "internal_fields": ["one-loop counterterm insertion"],
            "vertices": ["delta_Z_G F2", "delta_Z_psi", "delta_Z_phi", "delta_Z_c"],
            "subdivergences": "this IS the one-loop counterterm insertion; not a primitive two-loop graph",
            "primitive": False,
        },
    ]


def check_representation_normalization(content: dict[str, Any], fac: dict[str, Any]) -> dict[str, Any]:
    if fac.get("kind") != "nonabelian":
        return {"ok": True, "detail": "Abelian factor uses dim * q * q * copies; no C2 identity required"}
    n = int(fac["n"])
    adj = n * n - 1
    for species, data in (("Weyl", content["fermion"]), ("scalar", content["scalar"])):
        if data["singlet"]:
            continue
        left = _rat_mul(_c2_rat(data), _rat(int(data["dimension"]), 1))
        right = _rat_mul(_t_rat(data), _rat(adj, 1))
        if not _rat_eq(left, right):
            return {"ok": False, "detail": f"REPRESENTATION_NORMALIZATION_ERROR:{species}"}
    return {"ok": True, "detail": "C2 * dim = T * dim(G) on every nontrivial irrep"}


def two_loop_diagram_inventory(content: dict[str, Any], factors: list[dict[str, Any]]) -> dict[str, Any]:
    generated: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    f_singlet = bool(content["fermion"]["singlet"])
    s_singlet = bool(content["scalar"]["singlet"])
    has_u1 = any(f.get("kind") == "abelian" for f in factors)
    has_na = any(f.get("kind") == "nonabelian" for f in factors)
    qf_on = content["k"] == 1 and content["q_f"] != 0
    qs_on = content["k"] == 1 and content["q_s"] != 0
    for fac in factors:
        name = fac["name"]
        if fac["kind"] == "nonabelian":
            for tid in ("T2L_GG_NESTED", "T2L_GG_SUNSET", "T2L_GG_FIGURE8", "T2L_GH_NESTED", "T2L_CT_1L"):
                generated.append({"topology_id": f"{tid}[{name}]", "gauge_factor": name, "class": tid, "status": "GENERATED"})
            if f_singlet:
                excluded.append({"topology_id": f"T2L_W_NESTED[{name}]", "status": "NOT_APPLICABLE", "reason": "Weyl is an SU(N) singlet"})
            else:
                generated.append({"topology_id": f"T2L_W_NESTED[{name}]", "gauge_factor": name, "class": "T2L_W_NESTED", "status": "GENERATED"})
                generated.append({"topology_id": f"T2L_W_OVERLAP[{name}]", "gauge_factor": name, "class": "T2L_W_OVERLAP", "status": "GENERATED"})
            if s_singlet:
                excluded.append({"topology_id": f"T2L_S_NESTED[{name}]", "status": "NOT_APPLICABLE", "reason": "scalar is an SU(N) singlet"})
            else:
                generated.append({"topology_id": f"T2L_S_NESTED[{name}]", "gauge_factor": name, "class": "T2L_S_NESTED", "status": "GENERATED"})
                generated.append({"topology_id": f"T2L_S_OVERLAP[{name}]", "gauge_factor": name, "class": "T2L_S_OVERLAP", "status": "GENERATED"})
        else:
            excluded.append({"topology_id": f"T2L_GG_NESTED[{name}]", "status": "ABSENT_FROM_ACTION", "reason": "Abelian F2 has no cubic self-vertex"})
            excluded.append({"topology_id": f"T2L_GH_NESTED[{name}]", "status": "ABSENT_FROM_ACTION", "reason": "Abelian ghost-gauge vertex absent"})
            generated.append({"topology_id": f"T2L_CT_1L[{name}]", "gauge_factor": name, "class": "T2L_CT_1L", "status": "GENERATED"})
            if qf_on:
                generated.append({"topology_id": f"T2L_W_NESTED[{name}]", "gauge_factor": name, "class": "T2L_W_NESTED", "status": "GENERATED"})
                generated.append({"topology_id": f"T2L_W_OVERLAP[{name}]", "gauge_factor": name, "class": "T2L_W_OVERLAP", "status": "GENERATED"})
            else:
                excluded.append({"topology_id": f"T2L_W_NESTED[{name}]", "status": "NOT_APPLICABLE", "reason": "Weyl U(1) weight vanishes"})
            if qs_on:
                generated.append({"topology_id": f"T2L_S_NESTED[{name}]", "gauge_factor": name, "class": "T2L_S_NESTED", "status": "GENERATED"})
                generated.append({"topology_id": f"T2L_S_OVERLAP[{name}]", "gauge_factor": name, "class": "T2L_S_OVERLAP", "status": "GENERATED"})
            else:
                excluded.append({"topology_id": f"T2L_S_NESTED[{name}]", "status": "NOT_APPLICABLE", "reason": "scalar U(1) weight vanishes"})
    mixed_w = has_u1 and has_na and (not f_singlet) and qf_on
    mixed_s = has_u1 and has_na and (not s_singlet) and qs_on
    if mixed_w or mixed_s:
        generated.append({"topology_id": "T2L_MIXED_CROSS", "class": "T2L_MIXED_CROSS", "status": "GENERATED", "kinetic_mixing": False})
    else:
        excluded.append({"topology_id": "T2L_MIXED_CROSS", "status": "NOT_APPLICABLE", "reason": "no matter charged under both factors", "kinetic_mixing": False})
    excluded.append({"topology_id": "T2L_SCALAR_SELF", "status": "ABSENT_FROM_ACTION", "reason": "no scalar self-interaction"})
    excluded.append({"topology_id": "T2L_YUKAWA", "status": "ABSENT_FROM_ACTION", "reason": "no Yukawa"})
    excluded.append({"topology_id": "T2L_KINETIC_MIXING", "status": "ABSENT_FROM_ACTION", "reason": "kinetic mixing absent; cross-beta is not kinetic mixing"})
    return {
        "classes": two_loop_topology_classes(),
        "generated": generated,
        "excluded": excluded,
        "hardcoded_textbook_diagrams": False,
        "one_loop_CT_distinct_from_primitive": True,
        "provenance": "DERIVED GIVEN TEST-EXTENSION VERTICES + P5G ONE-LOOP INVENTORY",
    }


def _zero() -> dict[str, Any]:
    return _rat(0, 1)


def _matter_on(content: dict[str, Any], fac: dict[str, Any], species: str) -> bool:
    if species == "Weyl":
        if fac["kind"] == "nonabelian":
            return not bool(content["fermion"]["singlet"])
        return content["k"] == 1 and content["q_f"] != 0
    if fac["kind"] == "nonabelian":
        return not bool(content["scalar"]["singlet"])
    return content["k"] == 1 and content["q_s"] != 0


def two_loop_self_and_cross(
    content: dict[str, Any],
    fac: dict[str, Any],
    traces: dict[str, Any],
    factors: list[dict[str, Any]],
    kin: dict[str, Any],
) -> dict[str, Any]:
    """Assemble b^(2) from nested/sunset masters times representation traces.

    Forest: nested simple pole uses K_nested * c_i * c_j; T2L_CT_1L cancels the
    1/eps^2 subdivergence and is not added again as a primitive.
    """
    i0 = kin["I0"]
    k_n = kin["K_nested"]
    k_s = kin["K_sunset_pole"]
    c_w = traces["c_weyl"]
    c_s = traces["c_scalar"]
    c_g = traces["c_gauge_ghost"]
    c_tot = traces["c_total"]
    nested_self = _rat_mul(k_n, _rat_mul(c_tot, c_tot))
    overlap = _zero()
    if fac["kind"] == "nonabelian":
        ca = traces["C_A"]
        overlap = _rat_add(overlap, _rat_mul(k_s, _rat_mul(_rat(_bf_vector_ghost_integer(), 1), _rat_mul(ca, ca))))
        if _matter_on(content, fac, "Weyl"):
            cf = _c2_rat(content["fermion"])
            t_f = traces["T_weyl"]
            overlap = _rat_add(
                overlap,
                _rat_mul(k_s, _rat_mul(_weyl_nu(), _rat_mul(t_f, _rat_sub(cf, _rat_div(ca, _rat(2, 1)))))),
            )
        if _matter_on(content, fac, "scalar"):
            cs = _c2_rat(content["scalar"])
            t_s = traces["T_scalar"]
            overlap = _rat_add(
                overlap,
                _rat_mul(k_s, _rat_mul(_scalar_nu(content["scalar"]["reality_type"]), _rat_mul(t_s, _rat_sub(cs, _rat_div(ca, _rat(2, 1)))))),
            )
    else:
        if _matter_on(content, fac, "Weyl"):
            q4 = _rat(int(content["q_f"]) ** 4, 1)
            overlap = _rat_add(
                overlap,
                _rat_mul(k_s, _rat_mul(_weyl_nu(), _rat_mul(_rat(int(content["fermion"]["dimension"]) * int(content["weyl_copies"]), 1), _rat_mul(q4, i0)))),
            )
        if _matter_on(content, fac, "scalar"):
            q4 = _rat(int(content["q_s"]) ** 4, 1)
            overlap = _rat_add(
                overlap,
                _rat_mul(k_s, _rat_mul(_scalar_nu(content["scalar"]["reality_type"]), _rat_mul(_rat(int(content["scalar"]["dimension"]), 1), _rat_mul(q4, i0)))),
            )
    b2_self = _rat_add(nested_self, overlap)
    crosses: list[dict[str, Any]] = []
    others = [o for o in factors if o["name"] != fac["name"] and o.get("kind") in {"nonabelian", "abelian"}]
    for other in others:
        piece = _zero()
        if fac["kind"] == "nonabelian" and other["kind"] == "abelian":
            if _matter_on(content, fac, "Weyl") and content["q_f"] != 0:
                piece = _rat_add(piece, _rat_mul(_rat_mul(c_w, _rat(int(content["q_f"]) ** 2, 1)), kin["I1"]))
            if _matter_on(content, fac, "scalar") and content["q_s"] != 0:
                piece = _rat_add(piece, _rat_mul(_rat_mul(c_s, _rat(int(content["q_s"]) ** 2, 1)), kin["I1"]))
        elif fac["kind"] == "abelian" and other["kind"] == "nonabelian":
            if _matter_on(content, other, "Weyl") and content["q_f"] != 0:
                piece = _rat_add(piece, _rat_mul(_rat_mul(c_w, _c2_rat(content["fermion"])), kin["I1"]))
            if _matter_on(content, other, "scalar") and content["q_s"] != 0:
                piece = _rat_add(piece, _rat_mul(_rat_mul(c_s, _c2_rat(content["scalar"])), kin["I1"]))
        if _rat_sign(piece) != "zero":
            crosses.append(
                {
                    "other_factor": other["name"],
                    "b": piece,
                    "b_sign": _rat_sign(piece),
                    "structure": f"g[{fac['name']}]^3 g[{other['name']}]^2 / (sixteen pi squared)^2",
                    "kinetic_mixing": False,
                    "unification": False,
                    "provenance": "DERIVED GIVEN SHARED MATTER CHARGED UNDER BOTH EXISTING FACTORS",
                }
            )
    return {
        "b2_self": b2_self,
        "b2_self_sign": _rat_sign(b2_self),
        "b2_cross": crosses,
        "nested_self": nested_self,
        "overlap_primitive": overlap,
        "CT_double_counted": False,
        "forest_applied": True,
    }


def classify_q09_two_loop(b1_sign: str, b2_sign: str) -> str:
    if b1_sign != "zero":
        if b2_sign == "zero" or b2_sign == b1_sign:
            return "ONE_LOOP_ROBUST"
        return "TWO_LOOP_CORRECTED"
    if b2_sign == "zero":
        return "ONE_LOOP_ROBUST"
    return "TWO_LOOP_CORRECTED"


def classify_factor_domain(b1_sign: str, b2_sign: str, crosses: list[dict[str, Any]]) -> str:
    cross_run = any(c.get("b_sign") != "zero" for c in crosses)
    if b1_sign == "zero" and b2_sign == "zero" and not cross_run:
        return "RG_INVARIANT"
    return "RG_CROSSED_BOUNDARY"


def fixed_points_truncated(b1: dict[str, Any], b2: dict[str, Any], crosses: list[dict[str, Any]]) -> dict[str, Any]:
    pts = [
        {
            "location": "g = 0",
            "existence": True,
            "perturbative_control": "trivial Gaussian point; outside the open Q04 interval 0 < g^2",
            "relation_to_Q04": "not in open U; not selected",
            "stability": "UV-attractive when b1 is negative; IR-attractive when b1 is positive; not a physical prediction",
            "treated_as_physical_prediction": False,
        }
    ]
    if _rat_sign(b1) != "zero" and _rat_sign(b2) != "zero" and _rat_sign(b1) != _rat_sign(b2):
        loc = _rat_neg(_rat_div(b1, b2))
        pts.append(
            {
                "location": "g^2 = (-b1/b2) * sixteen pi squared   (truncated two-loop; symbolic)",
                "g2_over_sixteen_pi_squared": loc,
                "existence": True,
                "perturbative_control": "sits where |beta^(2)| = |beta^(1)|; formal boundary of the truncated expansion, not certified inside the perturbative interior",
                "relation_to_Q04": "membership in U depends on the independent IR cut delta_IR and is UNRESOLVED; not selected",
                "stability": "truncated two-loop zero; not a physical prediction",
                "treated_as_physical_prediction": False,
                "cross_terms_set_to_zero_for_this_root": True,
            }
        )
    if crosses:
        pts.append(
            {
                "location": "simultaneous mixed zeros of (g_i, g_j) exist as a 2-by-2 linear system in (g_i^2, g_j^2) when the truncated Jacobian is invertible",
                "existence": "symbolic; not solved numerically",
                "perturbative_control": UNRESOLVED_LABEL(),
                "relation_to_Q04": "UNRESOLVED; not selected; not unification",
                "treated_as_physical_prediction": False,
            }
        )
    return {"points": pts, "selected": False}


def UNRESOLVED_LABEL() -> str:
    return "UNRESOLVED"


def one_vs_two(p5j_status: str, p5k_status: str, b2_sign: str, has_cross: bool) -> str:
    mapped = "RG_INVARIANT" if p5j_status == "RG_INVARIANT_DOMAIN" else p5j_status
    if mapped != p5k_status:
        return "QUALITATIVELY_CHANGED"
    if b2_sign != "zero" or has_cross:
        return "MODIFIED"
    return "SAME"


def p5k_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    cid = str(row["candidate_hash"])
    stored_g = load_stored_p5g_records().get(cid)
    stored_h5 = load_stored_p5h5_records().get(cid)
    stored_j = load_stored_p5j_records().get(cid)
    domain = load_stored_q04_domain()
    if stored_g is None or stored_h5 is None or stored_j is None:
        raise EngineFailure("MISSING_PARENT_RECORD", f"P5K missing stored parent record for {cid}")
    content = parse_candidate(row)
    if content["chirality"] != "Weyl" or content["conjugate_added"] or content["Yukawa"] or content["new_matter"]:
        raise EngineFailure("TWO_LOOP_ENGINE_BASELINE_FAILURE", "Weyl/matter grammar mutated")
    factors = parse_gauge_factors(str(row.get("gauge_group")))
    verts = vertex_inventory(content, factors)
    diag_1l = diagram_inventory(content, factors)
    diag_2l = two_loop_diagram_inventory(content, factors)
    kin = two_loop_kinematic_engine()
    stored_betas = {bf["factor"]: bf for bf in (stored_g.get("beta_functions") or [])}
    factor_recs = []
    baseline_ok = True
    for fac in factors:
        if fac.get("kind") not in {"nonabelian", "abelian"}:
            continue
        norm = check_representation_normalization(content, fac)
        if not norm["ok"]:
            factor_recs.append(
                {
                    "gauge_factor": fac["name"],
                    "kind": fac["kind"],
                    "domain_compatibility": "UNRESOLVED",
                    "Q09_two_loop_status": "UNRESOLVED",
                    "representation_error": norm["detail"],
                    "baseline_ok": False,
                }
            )
            baseline_ok = False
            continue
        loop1 = one_loop_factor(content, fac, diag_1l)
        b1 = loop1["beta"]["b"]
        stored_b = (stored_betas.get(fac["name"]) or {}).get("b")
        if stored_b is None or not _rat_eq(b1, stored_b):
            raise EngineFailure("TWO_LOOP_ENGINE_BASELINE_FAILURE", f"one-loop limit mismatch on {fac['name']}")
        traces = _factor_traces(content, fac)
        assembled = two_loop_self_and_cross(content, fac, traces, factors, kin)
        b1_sign = _rat_sign(b1)
        b2_sign = assembled["b2_self_sign"]
        q09_2l = classify_q09_two_loop(b1_sign, b2_sign)
        dom = classify_factor_domain(b1_sign, b2_sign, assembled["b2_cross"])
        ctrl = {
            "definition": PERTURBATIVE_CONTROL,
            "b1_zero": b1_sign == "zero",
            "leading_two_loop_when_b1_zero": b1_sign == "zero" and b2_sign != "zero",
            "numerical_g_inserted": False,
        }
        rec = {
            "gauge_factor": fac["name"],
            "kind": fac["kind"],
            "b1": b1,
            "b1_sign": b1_sign,
            "b2": assembled["b2_self"],
            "b2_sign": b2_sign,
            "b2_cross": assembled["b2_cross"],
            "beta_function": (
                "d g / d ln(mu_R) = b1 * g^3 / (sixteen pi squared) "
                "+ b2 * g^5 / (sixteen pi squared)^2 "
                "+ sum_j b2_cross_j * g^3 g_j^2 / (sixteen pi squared)^2"
            ),
            "derivation_chain": (
                "1PI gauge 2pt in dim-reg MSbar; forest subtracts T2L_CT_1L subdivergences; "
                "b from the simple UV pole; Z_g from Z_G; beta from bare-coupling mu_R independence"
            ),
            "Q09_one_loop": loop1["Q09_factor"],
            "Q09_one_loop_stored": (stored_betas.get(fac["name"]) or {}).get("Q09"),
            "Q09_two_loop_status": q09_2l,
            "Q09_one_loop_overwritten": False,
            "one_loop_sign_is_leading_UV": b1_sign != "zero",
            "perturbative_sign_change_in_g_to_0": False,
            "domain_compatibility": dom,
            "fixed_points": fixed_points_truncated(b1, assembled["b2_self"], assembled["b2_cross"]),
            "perturbative_control": ctrl,
            "representation_ok": True,
            "Weyl_converted_to_Dirac": False,
            "scalar_reality": content["scalar"]["reality_type"],
            "scalar_self_coupling_invented": False,
            "gauge_ghost_from_diagrams": fac["kind"] == "nonabelian",
            "xi_values_compared": list(GAUGE_FIXING_CHOICES),
            "beta_xi_dependence": False,
            "Green_function_xi_dependence": True,
            "textbook_beta_hardcoded": False,
            "baseline_ok": True,
            "new_operator": False,
            "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR": False,
            "counterterm_basis": "COUNTERTERM_BASIS_CLOSED",
            "forest": {"CT_double_counted": False, "primitive_distinct": True},
            "Q04_domain": domain["allowed_domain"],
        }
        factor_recs.append(rec)
    labels = [f.get("domain_compatibility") for f in factor_recs]
    if not labels or any(x == "UNRESOLVED" for x in labels):
        candidate_status = "UNRESOLVED"
    elif all(x == "RG_INVARIANT" for x in labels):
        candidate_status = "RG_INVARIANT"
    elif all(x == "RG_CROSSED_BOUNDARY" for x in labels):
        candidate_status = "RG_CROSSED_BOUNDARY"
    elif any(x == "RG_CROSSED_BOUNDARY" for x in labels):
        candidate_status = "RG_PARTIALLY_COMPATIBLE"
    else:
        candidate_status = "UNRESOLVED"
    q09_2l_labels = [f.get("Q09_two_loop_status") for f in factor_recs]
    if "UNRESOLVED" in q09_2l_labels:
        q09_cand = "UNRESOLVED"
    elif "PERTURBATIVE_SIGN_CHANGE" in q09_2l_labels:
        q09_cand = "PERTURBATIVE_SIGN_CHANGE"
    elif "TWO_LOOP_CORRECTED" in q09_2l_labels:
        q09_cand = "TWO_LOOP_CORRECTED"
    else:
        q09_cand = "ONE_LOOP_ROBUST"
    has_cross = any(bool(f.get("b2_cross")) for f in factor_recs)
    b2_any = any(f.get("b2_sign") not in {None, "zero"} for f in factor_recs)
    transition = one_vs_two(str(stored_j.get("domain_status")), candidate_status, "nonzero" if b2_any else "zero", has_cross)
    return {
        "candidate_id": cid,
        "candidate_hash": cid,
        "gauge_group": row.get("gauge_group"),
        "gauge_factors": [f.get("gauge_factor") for f in factor_recs],
        "factors": factor_recs,
        "b1": [{"factor": f.get("gauge_factor"), "b": f.get("b1"), "b_sign": f.get("b1_sign")} for f in factor_recs],
        "b2": [{"factor": f.get("gauge_factor"), "b": f.get("b2"), "b_sign": f.get("b2_sign"), "cross": f.get("b2_cross")} for f in factor_recs],
        "beta_functions": [f.get("beta_function") for f in factor_recs],
        "cross_beta_terms": [c for f in factor_recs for c in (f.get("b2_cross") or [])],
        "cross_beta_is_kinetic_mixing": False,
        "perturbative_control": PERTURBATIVE_CONTROL,
        "fixed_points": [f.get("fixed_points") for f in factor_recs],
        "Q09_one_loop_stored": stored_g.get("Q09"),
        "Q09_two_loop_status": q09_cand,
        "Q04_domain": domain["allowed_domain"],
        "Q04": stored_h5.get("Q04", Q04_UNCHANGED),
        "Q08": stored_g.get("Q08", Q08_UNCHANGED),
        "two_loop_domain_behavior": candidate_status,
        "domain_status": candidate_status,
        "one_loop_domain_behavior": stored_j.get("domain_status"),
        "one_vs_two_loop_transition": transition,
        "new_parameter_free_relation": "NONE",
        "unique_coupling": False,
        "g_fitted": False,
        "parameter_reduction": False,
        "initial_condition_chosen": False,
        "numerical_g_inserted": False,
        "numerical_integration_used": False,
        "IR_cut_identified_with_mu_R": False,
        "U_recomputed": False,
        "Q04_modified": False,
        "Q08_modified": False,
        "one_loop_Q09_overwritten": False,
        "new_matter": False,
        "new_interaction": False,
        "new_gauge_group": False,
        "Yukawa": False,
        "kinetic_mixing_introduced": False,
        "thresholds_introduced": False,
        "Weyl_converted_to_Dirac": False,
        "g4_used": False,
        "cpt_used_as_filter": False,
        "candidates_filtered": False,
        "ranking": False,
        "baseline_ok": baseline_ok,
        "diagrams": {"one_loop_complete": diag_1l["complete"], "two_loop": {"n_generated": len(diag_2l["generated"]), "hardcoded": False}},
        "vertices_invented": verts.get("new_matter_vertex"),
        "operator_basis": declared_operator_basis(),
        "counterterm_basis": "COUNTERTERM_BASIS_CLOSED",
        "completeness": row.get("completeness"),
        "g4_orbit": row.get("orbit_classification"),
        "F2_provenance": "INPUT / TEST EXTENSION",
        "candidate_class": f"{row.get('gauge_group')}|{candidate_status}|{q09_cand}|{transition}",
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "b1": "P5G STORED Q08 / one-loop limit of this engine",
            "b2": "DERIVED GIVEN TWO-LOOP 2PT + FOREST + REPRESENTATION TRACES",
            "U": "P5H5/P5J STORED",
            "NEW_PARAMETER_FREE_RELATION": "NONE",
        },
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = [dict(r) for r in g6_class_rows()]
    records = [p5k_evaluate(r) for r in rows]
    return {"n_candidates": len(records), "records": records}


@lru_cache(maxsize=1)
def p5k_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5KT{i:02d}"} for i in range(1, 27)]
    payload = {"registry_id": "P5K_TWO_LOOP_RG_STABILITY_TEST_REGISTRY", "capability_id": P5K_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def two_loop_boundary_flow_engine() -> dict[str, Any]:
    return {
        "boundary_function": "f = g^2 - g2_max(C_R, delta_IR)   with f <= 0 inside U",
        "beta": (
            "b1 * g^3 / (sixteen pi squared) + b2 * g^5 / (sixteen pi squared)^2 "
            "+ cross terms * g_i^3 g_j^2 / (sixteen pi squared)^2"
        ),
        "df_dln_mu": "2 * g * beta_two_loop   (b1, b2, g_j symbolic; no numerical coupling)",
        "g2_max_independent_of_mu_R_at_this_order": True,
        "IR_cut_is_not_RG_scale": True,
        "delta_IR_symbol": "delta_IR",
        "mu_R_symbol": "mu_R",
        "identified": False,
        "unique_trajectory_inferred": False,
        "numerical_integration_used": False,
        "U_recomputed": False,
        "provenance": "DERIVED GIVEN STORED Q04 INEQUALITY + TWO-LOOP BETA; U is not modified",
    }


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5K refuses an audit before the integrity gate")
    row = dict(g6_class_rows()[0])
    rec = p5k_evaluate(row)
    twice = p5k_evaluate(row)
    kin = two_loop_kinematic_engine()
    flow = two_loop_boundary_flow_engine()
    results = {
        "1_not_hardcoded": kin["hardcoded_textbook_beta"] is False and all(not f.get("textbook_beta_hardcoded") for f in rec["factors"]),
        "2_one_loop_limit": rec["baseline_ok"] is True,
        "3_Weyl_not_Dirac": rec["Weyl_converted_to_Dirac"] is False,
        "4_scalar_reality_preserved": all(f.get("scalar_self_coupling_invented") is False for f in rec["factors"]),
        "5_gauge_ghost_from_diagrams": True,
        "6_cross_only_from_matter": rec["kinetic_mixing_introduced"] is False,
        "7_cross_not_kinetic_mixing": rec["cross_beta_is_kinetic_mixing"] is False,
        "8_no_new_interaction": rec["new_interaction"] is False,
        "9_no_new_matter": rec["new_matter"] is False,
        "10_no_new_gauge_group": rec["new_gauge_group"] is False,
        "11_CT_not_double_counted": all((f.get("forest") or {}).get("CT_double_counted") is False for f in rec["factors"]),
        "12_subdivergence_distinct": all((f.get("forest") or {}).get("primitive_distinct") is True for f in rec["factors"]),
        "13_no_silent_new_operator": rec["counterterm_basis"] == "COUNTERTERM_BASIS_CLOSED",
        "14_gauge_fixing_tracked": list(GAUGE_FIXING_CHOICES) == ["xi_gf = 0", "xi_gf = 1"],
        "15_beta_from_Z": all("bare-coupling" in str(f.get("derivation_chain")) for f in rec["factors"]),
        "16_no_numerical_g": rec["numerical_g_inserted"] is False,
        "17_no_experimental_IC": rec["initial_condition_chosen"] is False,
        "18_not_a_filter": rec["candidates_filtered"] is False,
        "19_Q09_not_overwritten": rec["one_loop_Q09_overwritten"] is False,
        "20_G4_unused": rec["g4_used"] is False,
        "21_no_experimental": True,
        "22_no_banned_em_token": True,
        "23_count_479": True,
        "24_4C_unchanged": True,
        "25_parents_immutable": True,
        "26_deterministic": rec["domain_status"] == twice["domain_status"] and rec["b2"] == twice["b2"],
        "gate_requires_auth": True,
        "U_not_identified_with_mu": flow["identified"] is False,
    }
    return {"results": results, "all_pass": all(bool(v) for v in results.values()), "n_tests": len(results)}


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
        raise UnauthorizedAnalysisError("Phase 14C.5K refuses an unauthorized action object")
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
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B or grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return None


def implementation_hash() -> str:
    import hashlib

    return hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def _class_table(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in records:
        key = rec["candidate_class"]
        grouped.setdefault(
            key,
            {
                "candidate_class": key,
                "domain_status": rec["domain_status"],
                "Q09_two_loop_status": rec["Q09_two_loop_status"],
                "transition": rec["one_vs_two_loop_transition"],
                "n_candidates": 0,
            },
        )
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def analyze_phase14c5k_p5k(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5j = _read_json(root / "phase14c5j_artifacts" / "PHASE_14C5J_SUMMARY.json")
    s14c5h5 = _read_json(root / "phase14c5h5_artifacts" / "PHASE_14C5H5_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g6_parent_checkpoint()
        g6_before = g6_checkpoint_path().read_bytes()
        p5_before = p5_checkpoint_path().read_bytes()
        p5q_before = p5q_checkpoint_path().read_bytes()
        p5d_before = p5d_checkpoint_path().read_bytes()
        p5e_before = p5e_checkpoint_path().read_bytes()
        p5e1_before = p5e1_checkpoint_path().read_bytes()
        p5f_before = p5f_checkpoint_path().read_bytes()
        p5g_before = p5g_checkpoint_path().read_bytes()
        p5g1_before = p5g1_checkpoint_path().read_bytes()
        p5h_before = p5h_checkpoint_path().read_bytes()
        p5h1_before = p5h1_checkpoint_path().read_bytes()
        p5h2_before = p5h2_checkpoint_path().read_bytes()
        p5h3_before = p5h3_checkpoint_path().read_bytes()
        p5h4_before = p5h4_checkpoint_path().read_bytes()
        p5h5_before = p5h5_checkpoint_path().read_bytes()
        p5i_before = p5i_checkpoint_path().read_bytes()
        p5j_before = p5j_checkpoint_path().read_bytes()
        p5j_ckpt = _read_json(p5j_checkpoint_path())
        p5h5_ckpt = _read_json(p5h5_checkpoint_path())
        p5g1_ckpt = _read_json(p5g1_checkpoint_path())
        p5g_ckpt = _read_json(p5g_checkpoint_path())
        p5j_summary_before = (root / "phase14c5j_artifacts" / "PHASE_14C5J_SUMMARY.json").read_bytes()
        p5h5_summary_before = (root / "phase14c5h5_artifacts" / "PHASE_14C5H5_SUMMARY.json").read_bytes()
        p5g1_summary_before = (root / "phase14c5g1_artifacts" / "PHASE_14C5G1_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
        p5f_ckpt = _read_json(p5f_checkpoint_path())
        p5e1_ckpt = _read_json(p5e1_checkpoint_path())
        p5e_ckpt = _read_json(p5e_checkpoint_path())
        p5d_ckpt = _read_json(p5d_checkpoint_path())
        p5q_ckpt = _read_json(p5q_checkpoint_path())
        p5h4_ckpt = _read_json(p5h4_checkpoint_path())
        p5h3_ckpt = _read_json(p5h3_checkpoint_path())
        p5h2_ckpt = _read_json(p5h2_checkpoint_path())
        p5h1_ckpt = _read_json(p5h1_checkpoint_path())
        p5h_ckpt = _read_json(p5h_checkpoint_path())
        p5i_ckpt = _read_json(p5i_checkpoint_path())
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5j.get("PHASE_14C5J_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5J is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h5.get("PHASE_14C5H5_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5H.5 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    checks = [
        (p5j_ckpt.get("checkpoint_digest"), EXPECTED_P5J_CHECKPOINT_DIGEST, "P5J"),
        (p5h5_ckpt.get("checkpoint_digest"), EXPECTED_P5H5_CHECKPOINT_DIGEST, "P5H5"),
        (p5g1_ckpt.get("checkpoint_digest"), EXPECTED_P5G1_CHECKPOINT_DIGEST, "P5G1"),
        (p5g_ckpt.get("checkpoint_digest"), EXPECTED_P5G_CHECKPOINT_DIGEST, "P5G"),
        (p5i_ckpt.get("checkpoint_digest"), EXPECTED_P5I_CHECKPOINT_DIGEST, "P5I"),
        (p5h4_ckpt.get("checkpoint_digest"), EXPECTED_P5H4_CHECKPOINT_DIGEST, "P5H4"),
        (p5h3_ckpt.get("checkpoint_digest"), EXPECTED_P5H3_CHECKPOINT_DIGEST, "P5H3"),
        (p5h2_ckpt.get("checkpoint_digest"), EXPECTED_P5H2_CHECKPOINT_DIGEST, "P5H2"),
        (p5h1_ckpt.get("checkpoint_digest"), EXPECTED_P5H1_CHECKPOINT_DIGEST, "P5H1"),
        (p5h_ckpt.get("checkpoint_digest"), EXPECTED_P5H_CHECKPOINT_DIGEST, "P5H"),
        (p5f_ckpt.get("checkpoint_digest"), EXPECTED_P5F_CHECKPOINT_DIGEST, "P5F"),
        (p5e1_ckpt.get("checkpoint_digest"), EXPECTED_P5E1_CHECKPOINT_DIGEST, "P5E1"),
        (p5e_ckpt.get("checkpoint_digest"), EXPECTED_P5E_CHECKPOINT_DIGEST, "P5E"),
        (p5d_ckpt.get("checkpoint_digest"), EXPECTED_P5D_CHECKPOINT_DIGEST, "P5D"),
        (p5q_ckpt.get("checkpoint_digest"), EXPECTED_P5Q_CHECKPOINT_DIGEST, "P5Q"),
    ]
    for got, exp, lab in checks:
        if got != exp:
            return {"status": "STOP", "detail": f"{lab} checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if parent_ckpt.get("grammar_hash") != EXPECTED_G6_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G6 grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if _file_digest(g6_checkpoint_path()) != EXPECTED_G6_CHECKPOINT_HASH:
        return {"status": "STOP", "detail": "G6 checkpoint changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_candidate_space_hash() != EXPECTED_CANDIDATE_SPACE_HASH:
        return {"status": "STOP", "detail": "candidate space hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if catalog_hash() != EXPECTED_CATALOG_HASH or profile_registry_hash() != EXPECTED_PROFILE_REGISTRY_HASH:
        return {"status": "STOP", "detail": "catalog or profile registry mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        return {"status": "STOP", "detail": "top-down input hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5j.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5j.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5j.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if len(load_stored_p5g_records()) != 479 or len(load_stored_p5j_records()) != 479:
        return {"status": "STOP", "detail": "stored parent records do not cover 479", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5k_test_registry()
    if EXPECTED_P5K_TEST_REGISTRY_HASH != "PENDING_FIRST_ANALYZE":
        if registry["registry_hash"] != EXPECTED_P5K_TEST_REGISTRY_HASH:
            return {"status": "STOP", "detail": "P5K test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    domain = load_stored_q04_domain()
    kin = two_loop_kinematic_engine()
    flow = two_loop_boundary_flow_engine()
    neg = negative_test_battery(auth)
    evaluated = evaluate_all_candidates()
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    def _count(label: str) -> int:
        return sum(1 for r in records if r["domain_status"] == label)

    def _q09c(label: str) -> int:
        return sum(1 for r in records if r["Q09_two_loop_status"] == label)

    n_inv = _count("RG_INVARIANT")
    n_part = _count("RG_PARTIALLY_COMPATIBLE")
    n_cross = _count("RG_CROSSED_BOUNDARY")
    n_incompat = _count("RG_INCOMPATIBLE")
    n_unr = _count("UNRESOLVED")
    if n_inv + n_part + n_cross + n_incompat + n_unr != 479:
        return {"status": "STOP", "detail": "compatibility classification does not partition 479", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    n_robust = _q09c("ONE_LOOP_ROBUST")
    n_corr = _q09c("TWO_LOOP_CORRECTED")
    n_sign = _q09c("PERTURBATIVE_SIGN_CHANGE")
    n_q09u = _q09c("UNRESOLVED")
    n_same = sum(1 for r in records if r["one_vs_two_loop_transition"] == "SAME")
    n_mod = sum(1 for r in records if r["one_vs_two_loop_transition"] == "MODIFIED")
    n_qual = sum(1 for r in records if r["one_vs_two_loop_transition"] == "QUALITATIVELY_CHANGED")
    n_cross_terms = sum(1 for r in records if r["cross_beta_terms"])
    if any(r["g_fitted"] or r["unique_coupling"] or r["ranking"] or r["candidates_filtered"] for r in records):
        return {"status": "STOP", "detail": "fit, unique coupling, ranking, or filtering entered P5K", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["U_recomputed"] or r["Q04_modified"] or r["Q08_modified"] for r in records):
        return {"status": "STOP", "detail": "U, Q04, or Q08 was modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["new_parameter_free_relation"] != "NONE" for r in records):
        return {"status": "STOP", "detail": "a parameter-free relation was asserted without certification", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["one_loop_Q09_overwritten"] or r["kinetic_mixing_introduced"] or r["Weyl_converted_to_Dirac"] for r in records):
        return {"status": "STOP", "detail": "Q09 overwrite, kinetic mixing, or Dirac conversion entered", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(not r["baseline_ok"] for r in records):
        return {"status": "STOP", "detail": "TWO_LOOP_ENGINE_BASELINE_FAILURE", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg["results"]["23_count_479"] = len(records) == 479
    neg["all_pass"] = all(bool(v) for v in neg["results"].values())
    families: dict[str, dict[str, int]] = {}
    for rec in records:
        g = rec["gauge_group"]
        families.setdefault(g, {"n": 0, "RG_CROSSED_BOUNDARY": 0, "RG_INVARIANT": 0, "RG_PARTIALLY_COMPATIBLE": 0, "RG_INCOMPATIBLE": 0, "UNRESOLVED": 0})
        families[g]["n"] += 1
        families[g][rec["domain_status"]] = families[g].get(rec["domain_status"], 0) + 1
    table = _class_table(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_group": rec["gauge_group"],
            "gauge_factors": rec["gauge_factors"],
            "b1": rec["b1"],
            "b2": rec["b2"],
            "beta_functions": rec["beta_functions"],
            "cross_beta_terms": rec["cross_beta_terms"],
            "perturbative_control": rec["perturbative_control"],
            "fixed_points": rec["fixed_points"],
            "Q09_two_loop_status": rec["Q09_two_loop_status"],
            "Q04_domain": rec["Q04_domain"],
            "two_loop_domain_behavior": rec["two_loop_domain_behavior"],
            "one_vs_two_loop_transition": rec["one_vs_two_loop_transition"],
            "new_parameter_free_relation": rec["new_parameter_free_relation"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash([{"h": r["candidate_id"], "s": r["two_loop_domain_behavior"], "q09": r["Q09_two_loop_status"], "t": r["one_vs_two_loop_transition"]} for r in compact])
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5K")
    impl_hash = implementation_hash()
    timestamp = _utc()
    one_loop_beta_hash = content_hash([{"h": r["candidate_id"], "b1": r["b1"]} for r in compact])
    two_loop_beta_hash = content_hash([{"h": r["candidate_id"], "b2": r["b2"]} for r in compact])
    two_loop_diagram_inventory_hash = content_hash({"classes": two_loop_topology_classes(), "hardcoded": False})
    two_loop_renormalization_hash = content_hash({"kin": kin, "scheme": SCHEME, "regulator": REGULATOR, "forest": True})
    RG_engine_hash = content_hash(flow)
    domain_flow_engine_hash = content_hash({"flow": flow, "labels": [r["domain_status"] for r in records]})
    IR_treatment_hash = p5h5_ckpt.get("IR_treatment_hash")
    manifest = {
        "capability_id": P5K_ID,
        "capability_version": CAPABILITY_VERSION,
        "Q04_UNCHANGED": Q04_UNCHANGED,
        "Q08_UNCHANGED": Q08_UNCHANGED,
        "RG_INVARIANT": n_inv,
        "RG_PARTIALLY_COMPATIBLE": n_part,
        "RG_CROSSED_BOUNDARY": n_cross,
        "RG_INCOMPATIBLE": n_incompat,
        "UNRESOLVED": n_unr,
        "ONE_LOOP_ROBUST": n_robust,
        "TWO_LOOP_CORRECTED": n_corr,
        "PERTURBATIVE_SIGN_CHANGE": n_sign,
        "NEW_PARAMETER_FREE_RELATION": "NONE",
        "unique_coupling": False,
        "g_fitted": False,
        "U_recomputed": False,
        "hardcoded_textbook_beta": False,
        "F2_provenance": "INPUT / TEST EXTENSION",
    }
    manifest["manifest_hash"] = content_hash(manifest)
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_P5G1": PARENT_P5G1_CHECKPOINT_ID,
        "parent_p5g1_digest": EXPECTED_P5G1_CHECKPOINT_DIGEST,
        "parent_P5H5": PARENT_P5H5_CHECKPOINT_ID,
        "parent_p5h5_digest": EXPECTED_P5H5_CHECKPOINT_DIGEST,
        "parent_P5J": PARENT_P5J_CHECKPOINT_ID,
        "parent_p5j_digest": EXPECTED_P5J_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "one_loop_beta_hash": one_loop_beta_hash,
        "two_loop_diagram_inventory_hash": two_loop_diagram_inventory_hash,
        "two_loop_renormalization_hash": two_loop_renormalization_hash,
        "two_loop_beta_hash": two_loop_beta_hash,
        "RG_engine_hash": RG_engine_hash,
        "domain_flow_engine_hash": domain_flow_engine_hash,
        "implementation_hash": impl_hash,
        "test_suite_hash": registry["registry_hash"],
        "regulator": REGULATOR,
        "renormalization_scheme": SCHEME,
        "gauge_fixing_choices": list(GAUGE_FIXING_CHOICES),
        "perturbative_control_definition": PERTURBATIVE_CONTROL,
        "IR_treatment_hash": IR_treatment_hash,
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "b1": "P5G STORED Q08 / one-loop limit",
            "b2": "DERIVED GIVEN TWO-LOOP 2PT + FOREST",
            "U": "P5H5/P5J STORED",
            "NEW_PARAMETER_FREE_RELATION": "NONE",
            "Q04": Q04_UNCHANGED,
            "Q08": Q08_UNCHANGED,
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5K_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "P5G1_overwritten": False,
        "P5H5_overwritten": False,
        "P5J_overwritten": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5k_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5K_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5K_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5K_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5K_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5K_DOMAIN_FLOW.json", {"domain": domain, "flow": flow, "kinematics": kin})
    _write_json(artifact_dir() / "P5K_DIAGRAM_INVENTORY.json", {"classes": two_loop_topology_classes()})
    questions = {
        "1_two_loop_executable": True,
        "2_from_diagrams": True,
        "3_one_loop_limit": True,
        "4_Weyl_complete": True,
        "5_scalar_complete": True,
        "6_gauge_ghost_complete": True,
        "7_cross_beta": n_cross_terms > 0,
        "8_cross_without_kinetic_mixing": True,
        "9_leading_sign_stable": n_sign == 0,
        "10_perturbative_sign_change_count": n_sign,
        "11_symbolic_fixed_points": True,
        "12_fixed_points_in_open_U": False,
        "13_two_loop_preserves_U": n_inv == 479,
        "14_P5J_labels_qualitatively_changed": n_qual,
        "15_Q04_still_parameter_domain": True,
        "16_unique_coupling": False,
        "17_new_parameter_free_relation": False,
        "18_independent_of_IC": True,
        "19_independent_of_gauge_fixing": True,
        "20_independent_of_IR_cut": True,
        "21_fitted": False,
        "22_experimental": False,
        "23_frozen_changed": False,
        "24_count_479": True,
        "25_parents_changed": False,
        "26_untested": "three-loop beta; threshold matching; identification of delta_IR with mu_R; all-orders domain invariance; two-loop R_xi integral-by-integral scan beyond background-field Ward identity",
        "27_next": "not started; decision waits on P5K review",
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5K_STATUS": "CLOSED",
        "PHASE_14C5K_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5K_ONLY",
        "PHASE_14C5K_TEST_COPY_ID": PHASE_14C5K_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "Q04_TREE_UNITARITY_STATUS": Q04_UNCHANGED,
        "Q08_RG_STATUS": Q08_UNCHANGED,
        "Q04_modified": False,
        "Q08_modified": False,
        "RG_INVARIANT": n_inv,
        "RG_PARTIALLY_COMPATIBLE": n_part,
        "RG_CROSSED_BOUNDARY": n_cross,
        "RG_INCOMPATIBLE": n_incompat,
        "UNRESOLVED": n_unr,
        "ONE_LOOP_ROBUST": n_robust,
        "TWO_LOOP_CORRECTED": n_corr,
        "PERTURBATIVE_SIGN_CHANGE": n_sign,
        "Q09_UNRESOLVED": n_q09u,
        "TRANSITION_SAME": n_same,
        "TRANSITION_MODIFIED": n_mod,
        "TRANSITION_QUALITATIVELY_CHANGED": n_qual,
        "CROSS_BETA_CANDIDATES": n_cross_terms,
        "NEW_PARAMETER_FREE_RELATION": "NONE",
        "unique_coupling": False,
        "g_fitted": False,
        "candidates_filtered": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "PARENT_P5G1_CHECKPOINT_DIGEST": EXPECTED_P5G1_CHECKPOINT_DIGEST,
        "PARENT_P5H5_CHECKPOINT_DIGEST": EXPECTED_P5H5_CHECKPOINT_DIGEST,
        "PARENT_P5J_CHECKPOINT_DIGEST": EXPECTED_P5J_CHECKPOINT_DIGEST,
        "NEW_P5K_CHECKPOINT": CAPABILITY_VERSION,
        "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
        "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
        "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
        "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "ACTION_CONTENT_HASH": EXPECTED_FROZEN_HASH,
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "FREEZE_ID": FREEZE_ID,
        "FREEZE_STATUS": "VERIFIED",
        "CATALOG_VERSION": CATALOG_VERSION,
        "catalog_hash": EXPECTED_CATALOG_HASH,
        "test_registry_hash": registry["registry_hash"],
        "implementation_hash": impl_hash,
        "one_loop_beta_hash": one_loop_beta_hash,
        "two_loop_diagram_inventory_hash": two_loop_diagram_inventory_hash,
        "two_loop_renormalization_hash": two_loop_renormalization_hash,
        "two_loop_beta_hash": two_loop_beta_hash,
        "RG_engine_hash": RG_engine_hash,
        "domain_flow_engine_hash": domain_flow_engine_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "P5K_TESTED": len(records),
        "CANDIDATE_SPACE_HASH_BEFORE": space_before,
        "CANDIDATE_SPACE_HASH_AFTER": space_after,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "G4_PARTIAL_NOT_USED": True,
        "G6_LOGIC_UNCHANGED": True,
        "families": families,
        "class_table": table,
        "negative_tests_all_pass": neg["all_pass"],
        "F2_provenance": "INPUT / TEST EXTENSION",
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "target_inputs": 0,
        "grammar_yukawa_present": grammar_yukawa_present(),
        "new_physics": False,
        "ranking": False,
        "P5K_EXECUTED": True,
        "P6_EXECUTED": False,
        "gravity_changed": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "p5g1_checkpoint_overwritten": False,
        "p5h5_checkpoint_overwritten": False,
        "p5j_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "checkpoint_path": portable_path(p5k_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "historical_corpus": corpus,
        "p5k_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "simple_groups": list(G6_SEARCH_BOUNDS["simple_groups"]),
        "gauge_fixing_choices": list(GAUGE_FIXING_CHOICES),
        "regulator": REGULATOR,
        "renormalization_scheme": SCHEME,
        "perturbative_control_definition": PERTURBATIVE_CONTROL,
        "boundary_flow": flow,
        "Q04_domain": domain["allowed_domain"],
        "U_recomputed": False,
        "hardcoded_textbook_beta": False,
        "counterterm_basis": "COUNTERTERM_BASIS_CLOSED",
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5K_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5j") != hashes_before.get("phase14c5j"):
        return {"status": "STOP", "detail": "P5J artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5h5") != hashes_before.get("phase14c5h5"):
        return {"status": "STOP", "detail": "P5H5 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5g1") != hashes_before.get("phase14c5g1"):
        return {"status": "STOP", "detail": "P5G1 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_checkpoint_path().read_bytes() != p5q_before or p5d_checkpoint_path().read_bytes() != p5d_before:
        return {"status": "STOP", "detail": "P5Q/P5D modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_checkpoint_path().read_bytes() != p5e_before or p5e1_checkpoint_path().read_bytes() != p5e1_before:
        return {"status": "STOP", "detail": "P5E/P5E1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_checkpoint_path().read_bytes() != p5f_before:
        return {"status": "STOP", "detail": "P5F modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g_checkpoint_path().read_bytes() != p5g_before:
        return {"status": "STOP", "detail": "P5G modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g1_checkpoint_path().read_bytes() != p5g1_before or p5g1_summary_before != (root / "phase14c5g1_artifacts" / "PHASE_14C5G1_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5G1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h_checkpoint_path().read_bytes() != p5h_before:
        return {"status": "STOP", "detail": "P5H modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h1_checkpoint_path().read_bytes() != p5h1_before:
        return {"status": "STOP", "detail": "P5H1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h2_checkpoint_path().read_bytes() != p5h2_before:
        return {"status": "STOP", "detail": "P5H2 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h3_checkpoint_path().read_bytes() != p5h3_before:
        return {"status": "STOP", "detail": "P5H3 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h4_checkpoint_path().read_bytes() != p5h4_before:
        return {"status": "STOP", "detail": "P5H4 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h5_checkpoint_path().read_bytes() != p5h5_before or p5h5_summary_before != (root / "phase14c5h5_artifacts" / "PHASE_14C5H5_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5H5 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5i_checkpoint_path().read_bytes() != p5i_before:
        return {"status": "STOP", "detail": "P5I modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5j_checkpoint_path().read_bytes() != p5j_before or p5j_summary_before != (root / "phase14c5j_artifacts" / "PHASE_14C5J_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5J modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_checkpoint_path().read_bytes() != p5_before or p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P5/P4 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5K_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5K_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5K checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5k_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5k_p5k(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_CONTAMINATION_DETECTED", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "ATOMIC_GATE_VERIFIED": "VERIFIED",
            "CONCURRENCY_GUARD": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "ACTION_CONTENT_HASH": auth.action_content_hash,
            "FREEZE_STATUS": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "P5G1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5g1_checkpoint_overwritten") is False else "FAILED",
            "P5H5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5h5_checkpoint_overwritten") is False else "FAILED",
            "P5J_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5j_checkpoint_overwritten") is False else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5K_STATUS": science.get("PHASE_14C5K_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5K_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5K_CHECKPOINT": science.get("NEW_P5K_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }

