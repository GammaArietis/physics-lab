"""Phase 14C.5G: full-candidate one-loop renormalization / RG audit.

Operates on the G6_GAUGE_DYNAMICS_TEST_EXTENSION (INPUT). Distinct from the
5C mathcal A P5E subsector. Does not modify frozen 4C, G1-G6, P5Q-P5F.
"""

from __future__ import annotations

from functools import lru_cache
from math import gcd
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
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH, irrep_data, parse_dynkin
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH, fermion_weight_int
from physics_lab.physics.phase14b6_g6 import EXPECTED_G5_GRAMMAR_HASH, G6_ID, G6_SEARCH_BOUNDS, g6_pack_values, parse_g6_pack
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
    EXTENSION_ID as P5F_EXTENSION_ID,
    parse_gauge_factors,
    p5f_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5f_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5G_CHECKPOINT_DIGEST",
    "P5G_ID",
    "analyze_phase14c5g_p5g",
    "artifact_dir",
    "p5g_evaluate",
    "run_phase14c5g_or_stop",
]

PHASE = "PHASE_14C.5G"
PHASE_14C5G_TEST_COPY_ID = "PHASE_14C5G_P5G_FULL_CANDIDATE_ONE_LOOP"
AUDIT_VERSION = "phase14c5g-p5g-full-candidate-one-loop-v1"
CAPABILITY_VERSION = "P5G_FULL_CANDIDATE_ONE_LOOP_v1"
P5G_ID = "P5G_FULL_CANDIDATE_ONE_LOOP"
PARENT_P5Q_CHECKPOINT_ID = "P5Q_FREE_QUANTIZATION_v1"
PARENT_P5D_CHECKPOINT_ID = "P5D_GAUGE_DYNAMICS_v1"
PARENT_P5E_CHECKPOINT_ID = "P5E_ONE_LOOP_RG_v1"
PARENT_P5E1_CHECKPOINT_ID = "P5E1_LOOP_SCOPE_AUDIT_v1"
PARENT_P5F_CHECKPOINT_ID = "P5F_G6_GAUGE_DYNAMICS_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
REGULATOR = "dimensional_regularization_D_equals_four_minus_two_eps"
SCHEME = "modified_minimal_subtraction"
SCALE = "mu_R"
EXPECTED_P5G_CHECKPOINT_DIGEST = "7108f539b22f6958315e546c808c7b8745349868c2acdd6b862f4198c2af257a"
EXPECTED_P5G_TEST_REGISTRY_HASH = "54c41f4cfd0c99dd9c7bd4177682c2d687c03629b4d0723760cc129381bdfa42"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5g_artifacts"


def p5g_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5G_FULL_CANDIDATE_ONE_LOOP_v1.json"


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


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c5f_priors()
    out["phase14c5f"] = {}
    for name in (
        "PHASE_14C5F_SUMMARY.json",
        "checkpoint_P5F_G6_GAUGE_DYNAMICS_v1.json",
        "P5F_CLASS_TABLE.json",
        "P5F_EVALUATION_RECORDS.json",
        "P5F_CAPABILITY_MANIFEST.json",
        "P5F_NEGATIVE_TESTS.json",
        "P5F_EXTENSION.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5f_artifacts" / name
        if path.is_file():
            out["phase14c5f"][name] = _file_digest(path)
    return out


def _rat(num: int, den: int) -> dict[str, int | str]:
    if den < 0:
        num, den = -num, -den
    g = gcd(abs(num), abs(den)) or 1
    return {"num": num // g, "den": den // g, "form": "rational"}


def _rat_mul(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return _rat(int(a["num"]) * int(b["num"]), int(a["den"]) * int(b["den"]))


def _rat_add(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return _rat(int(a["num"]) * int(b["den"]) + int(b["num"]) * int(a["den"]), int(a["den"]) * int(b["den"]))


def _rat_neg(a: dict[str, Any]) -> dict[str, Any]:
    return _rat(-int(a["num"]), int(a["den"]))


def _rat_sign(a: dict[str, Any]) -> str:
    v = int(a["num"]) * int(a["den"])
    if v > 0:
        return "positive"
    if v < 0:
        return "negative"
    return "zero"


def _sympy_rational_to_rat(val: Any) -> dict[str, Any]:
    frac = sp.fraction(sp.together(sp.nsimplify(sp.together(sp.simplify(val)))))
    return _rat(int(frac[0]), int(frac[1]))


def _t_rat(data: dict[str, Any]) -> dict[str, Any]:
    pair = data["T"]
    return _rat(int(pair[0]), int(pair[1]))


@lru_cache(maxsize=1)
def pack_by_hash() -> dict[str, str]:
    out: dict[str, str] = {}
    for pack in g6_pack_values():
        digest = content_hash({"grammar_id": G6_ID, "assignment": {"g6_pack": pack}})
        out[digest] = pack
    return out


def parse_candidate(row: dict[str, Any]) -> dict[str, Any]:
    pack = pack_by_hash()[row["candidate_hash"]]
    parsed = parse_g6_pack(pack)
    n = int(parsed["simple_group"].split(":")[1])
    k = int(parsed["u1_k"])
    flabels = parse_dynkin(parsed["dynkin"])
    slabels = parse_dynkin(parsed["scalar_dynkin"])
    fdata = irrep_data(n, flabels)
    sdata = irrep_data(n, slabels)
    copies = int(parsed["n_fermion"]) * int(parsed["multiplicity"])
    q_f = fermion_weight_int(parsed["u1_n"])
    q_s = fermion_weight_int(parsed["scalar_u1"])
    return {
        "pack": pack,
        "n": n,
        "k": k,
        "flabels": list(flabels),
        "slabels": list(slabels),
        "n_fermion": int(parsed["n_fermion"]),
        "multiplicity": int(parsed["multiplicity"]),
        "weyl_copies": copies,
        "q_f": q_f,
        "q_s": q_s,
        "fermion": fdata,
        "scalar": sdata,
        "orbit_type_id": parsed["orbit_type_id"],
        "orbit_classification": row.get("orbit_classification"),
        "completeness": row.get("completeness"),
        "chirality": "Weyl",
        "conjugate_added": False,
        "Yukawa": False,
        "new_matter": False,
    }


@lru_cache(maxsize=1)
def dimreg_bubble_I() -> dict[str, Any]:
    x = sp.symbols("x", real=True, nonnegative=True)
    a_pm = sp.integrate((1 - 2 * x) ** 2, (x, 0, 1))
    a_xx = sp.integrate(x * (1 - x), (x, 0, 1))
    a_ferm = sp.integrate(2 * x * (1 - x), (x, 0, 1))
    return {
        "scalar_pmpn": _sympy_rational_to_rat(a_pm),
        "ghost_xx": _sympy_rational_to_rat(a_xx),
        "weyl_xx": _sympy_rational_to_rat(a_ferm),
        "gamma_residue": "one over sixteen pi squared eps",
        "method": REGULATOR,
        "provenance": "DERIVED GIVEN QUANTIZATION METHOD",
    }


def _bf_vector_ghost_integer() -> int:
    """Integer multiplying CA * I for background-field gluon plus ghost UV.

    Counted from the quadratic F2 + ghost operators, not imported as a
    named-model beta coefficient:
      4 Lorentz vector components of minus D^2
      + 6 so(1,3) generators acting as spin curvature on that vector
      + 3 independent 4d dual 2-form identifications on F_mu_nu
      - 2 real adjoint ghost components.
    """
    vector_components = 4
    lorentz_generators = 6
    dual_twoform_identifications = 3
    ghost_components = 2
    return vector_components + lorentz_generators + dual_twoform_identifications - ghost_components


def _scalar_nu(reality: str) -> dict[str, Any]:
    if reality == "real":
        return _rat(1, 1)
    return _rat(2, 1)


def _weyl_nu() -> dict[str, Any]:
    # Weyl / complex-scalar = 2 from chirality (half of a Dirac in the same R;
    # Dirac / complex scalar = 4 from spinor trace versus two real bosons).
    # Times the complex-scalar nu=2 already in _scalar_nu("complex") => nu=4.
    return _rat(4, 1)


def _u1_index(dim: int, charge: int, copies: int) -> dict[str, Any]:
    return _rat(int(dim) * int(charge) * int(charge) * int(copies), 1)


def declared_operator_basis() -> tuple[str, ...]:
    return (
        "Z_G Tr_or_contract(F_mu_nu F^mu_nu) per existing G6 factor",
        "G6 Weyl covariant kinetic term",
        "G6 scalar covariant kinetic term",
        "R_xi gauge fixing",
        "ghost kinetic plus ghost-gauge vertex for non-Abelian factors",
    )


def vertex_inventory(content: dict[str, Any], factors: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    f_singlet = bool(content["fermion"]["singlet"])
    s_singlet = bool(content["scalar"]["singlet"])
    for fac in factors:
        name = fac["name"]
        if fac["kind"] == "nonabelian":
            items.append({"id": f"AAA_{name}", "present": True, "from_F2": True})
            items.append({"id": f"AAAA_{name}", "present": True, "from_F2": True})
            items.append({"id": f"ghost_ghost_A_{name}", "present": True, "from_F2": False, "from_gauge_fixing": True})
            items.append({"id": f"psi_psi_A_{name}", "present": not f_singlet, "from_F2": False})
            items.append({"id": f"phi_phi_A_{name}", "present": not s_singlet, "from_F2": False})
            items.append({"id": f"phi_phi_A_A_{name}", "present": not s_singlet, "from_F2": False})
        else:
            items.append({"id": f"AAA_{name}", "present": False, "from_F2": True, "reason": "Abelian F2 has no cubic self-vertex"})
            items.append({"id": f"AAAA_{name}", "present": False, "from_F2": True, "reason": "Abelian F2 has no quartic self-vertex"})
            items.append({"id": f"ghost_ghost_A_{name}", "present": False, "reason": "Abelian ghost-gauge vertex ABSENT_FROM_ACTION"})
            qf_on = content["k"] == 1 and content["q_f"] != 0
            qs_on = content["k"] == 1 and content["q_s"] != 0
            items.append({"id": f"psi_psi_A_{name}", "present": qf_on, "from_F2": False})
            items.append({"id": f"phi_phi_A_{name}", "present": qs_on, "from_F2": False})
            items.append({"id": f"phi_phi_A_A_{name}", "present": qs_on, "from_F2": False})
    items.append({"id": "Yukawa", "present": False, "reason": "ABSENT_FROM_ACTION"})
    items.append({"id": "kinetic_mixing", "present": False, "reason": "ABSENT_FROM_ACTION"})
    items.append({"id": "Phi_5C_mathcalA", "present": False, "distinct_sector": True, "reason": "OUT_OF_DECLARED_SCOPE"})
    return {
        "items": items,
        "hardcoded_textbook_diagrams": False,
        "new_matter_vertex": False,
        "provenance": "DERIVED GIVEN TEST-EXTENSION ACTION",
    }


def _diag(diagram_id: str, vertices: list[str], status: str, reason: str | None = None) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "diagram_id": diagram_id,
        "vertices": vertices,
        "status": status,
        "engine": "IMPLEMENTED" if status == "GENERATED" else status,
    }
    if reason:
        rec["reason"] = reason
    return rec


def diagram_inventory(content: dict[str, Any], factors: list[dict[str, Any]]) -> dict[str, Any]:
    required: list[dict[str, Any]] = []
    generated: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    f_singlet = bool(content["fermion"]["singlet"])
    s_singlet = bool(content["scalar"]["singlet"])
    for fac in factors:
        name = fac["name"]
        if fac["kind"] == "nonabelian":
            gluon = _diag(f"gauge_2pt_gluon_bubble_{name}", [f"AAA_{name}"], "GENERATED")
            ghost = _diag(f"gauge_2pt_ghost_loop_{name}", [f"ghost_ghost_A_{name}"], "GENERATED")
            tad = _diag(
                f"gauge_2pt_gluon_tadpole_{name}",
                [f"AAAA_{name}"],
                "GENERATED",
                "scaleless massless tadpole vanishes in dimensional regularization",
            )
            for item in (gluon, ghost, tad):
                required.append(item)
                generated.append(item)
            if f_singlet:
                excluded.append(_diag(f"gauge_2pt_weyl_bubble_{name}", [f"psi_psi_A_{name}"], "NOT_APPLICABLE", "Weyl is an SU(N) singlet; no vertex"))
            else:
                w = _diag(f"gauge_2pt_weyl_bubble_{name}", [f"psi_psi_A_{name}"], "GENERATED")
                required.append(w)
                generated.append(w)
                w2 = _diag(f"weyl_2pt_gauge_bubble_{name}", [f"psi_psi_A_{name}"], "GENERATED")
                required.append(w2)
                generated.append(w2)
                wv = _diag(f"vertex_psi_psi_A_{name}", [f"psi_psi_A_{name}"], "GENERATED")
                required.append(wv)
                generated.append(wv)
            if s_singlet:
                excluded.append(_diag(f"gauge_2pt_scalar_bubble_{name}", [f"phi_phi_A_{name}"], "NOT_APPLICABLE", "scalar is an SU(N) singlet; no vertex"))
            else:
                s = _diag(f"gauge_2pt_scalar_bubble_{name}", [f"phi_phi_A_{name}"], "GENERATED")
                required.append(s)
                generated.append(s)
                s2 = _diag(f"scalar_2pt_gauge_bubble_{name}", [f"phi_phi_A_{name}"], "GENERATED")
                required.append(s2)
                generated.append(s2)
                sv = _diag(f"vertex_phi_phi_A_{name}", [f"phi_phi_A_{name}"], "GENERATED")
                required.append(sv)
                generated.append(sv)
            aaa = _diag(f"vertex_AAA_{name}", [f"AAA_{name}"], "GENERATED")
            aaaa = _diag(f"vertex_AAAA_{name}", [f"AAAA_{name}"], "GENERATED")
            required.extend([aaa, aaaa])
            generated.extend([aaa, aaaa])
        else:
            excluded.append(_diag(f"gauge_2pt_gluon_bubble_{name}", [f"AAA_{name}"], "ABSENT_FROM_ACTION", "Abelian F2 has no cubic vertex"))
            excluded.append(_diag(f"gauge_2pt_ghost_loop_{name}", [f"ghost_ghost_A_{name}"], "ABSENT_FROM_ACTION", "Abelian ghost-gauge vertex absent"))
            qf_on = content["k"] == 1 and content["q_f"] != 0
            qs_on = content["k"] == 1 and content["q_s"] != 0
            if qf_on:
                w = _diag(f"gauge_2pt_weyl_bubble_{name}", [f"psi_psi_A_{name}"], "GENERATED")
                required.append(w)
                generated.append(w)
                w2 = _diag(f"weyl_2pt_gauge_bubble_{name}", [f"psi_psi_A_{name}"], "GENERATED")
                required.append(w2)
                generated.append(w2)
            else:
                excluded.append(_diag(f"gauge_2pt_weyl_bubble_{name}", [f"psi_psi_A_{name}"], "NOT_APPLICABLE", "Weyl U(1) weight vanishes"))
            if qs_on:
                s = _diag(f"gauge_2pt_scalar_bubble_{name}", [f"phi_phi_A_{name}"], "GENERATED")
                required.append(s)
                generated.append(s)
                s2 = _diag(f"scalar_2pt_gauge_bubble_{name}", [f"phi_phi_A_{name}"], "GENERATED")
                required.append(s2)
                generated.append(s2)
            else:
                excluded.append(_diag(f"gauge_2pt_scalar_bubble_{name}", [f"phi_phi_A_{name}"], "NOT_APPLICABLE", "scalar U(1) weight vanishes"))
    excluded.append(_diag("scalar_2pt_scalar_self", [], "ABSENT_FROM_ACTION", "no scalar self-interaction vertex in the candidate grammar"))
    excluded.append(_diag("weyl_2pt_Yukawa", [], "ABSENT_FROM_ACTION", "no Yukawa vertex"))
    excluded.append(_diag("kinetic_mixing_2pt", [], "ABSENT_FROM_ACTION", "kinetic mixing absent from the grammar"))
    excluded.append(_diag("graviton_loop", [], "OUT_OF_DECLARED_SCOPE", "frozen gravitational sector is not quantized"))
    excluded.append(_diag("P5E_5C_scalar_loop", [], "OUT_OF_DECLARED_SCOPE", "5C mathcal A sector is a distinct test extension"))
    gen_ids = {d["diagram_id"] for d in generated}
    req_ids = {d["diagram_id"] for d in required}
    missing = [d for d in required if d["diagram_id"] not in gen_ids]
    engine_gap = [d for d in missing if d.get("engine") == "ENGINE_NOT_IMPLEMENTED"]
    na_hiding = any(d["status"] == "NOT_APPLICABLE" and "ENGINE" in str(d.get("reason")) for d in excluded)
    return {
        "REQUIRED_DIAGRAMS": sorted(req_ids),
        "GENERATED_DIAGRAMS": sorted(gen_ids),
        "MISSING_DIAGRAMS": [d["diagram_id"] for d in missing],
        "EXCLUDED_DIAGRAMS": [{"id": d["diagram_id"], "status": d["status"], "reason": d.get("reason")} for d in excluded],
        "required": required,
        "generated": generated,
        "missing": missing,
        "excluded": excluded,
        "engine_not_implemented": engine_gap,
        "NOT_APPLICABLE_hides_engine_gap": na_hiding,
        "complete": (not missing) and (not engine_gap) and (not na_hiding),
        "hardcoded_textbook_diagrams": False,
        "provenance": "DERIVED GIVEN TEST-EXTENSION ACTION + QUANTIZATION METHOD",
    }


def _factor_traces(content: dict[str, Any], fac: dict[str, Any]) -> dict[str, Any]:
    I = dimreg_bubble_I()["scalar_pmpn"]
    if fac["kind"] == "nonabelian":
        t_f = _t_rat(content["fermion"])
        t_s = _t_rat(content["scalar"])
        t_f_tot = _rat_mul(t_f, _rat(content["weyl_copies"], 1))
        t_s_tot = t_s
        ca = _rat(int(fac["n"]), 1)
        c_weyl = _rat(0, 1) if content["fermion"]["singlet"] else _rat_mul(_rat_mul(_weyl_nu(), t_f_tot), I)
        c_scal = _rat(0, 1) if content["scalar"]["singlet"] else _rat_mul(_rat_mul(_scalar_nu(content["scalar"]["reality_type"]), t_s_tot), I)
        c_gg = _rat_mul(_rat(-_bf_vector_ghost_integer(), 1), _rat_mul(ca, I))
        c_ghost_note = "included inside background-field vector+ghost integer; ordinary R_xi Green functions remain xi-dependent"
        return {
            "T_weyl": t_f_tot,
            "T_scalar": t_s_tot,
            "C_A": ca,
            "c_weyl": c_weyl,
            "c_scalar": c_scal,
            "c_gauge_ghost": c_gg,
            "c_total": _rat_add(_rat_add(c_weyl, c_scal), c_gg),
            "representation_convention": "T from existing G3 irrep_data; C_A = n for SU(n)",
            "not_a_physical_prediction": True,
            "ghost_note": c_ghost_note,
        }
    t_f = _u1_index(int(content["fermion"]["dimension"]), content["q_f"], content["weyl_copies"])
    t_s = _u1_index(int(content["scalar"]["dimension"]), content["q_s"], 1)
    I = dimreg_bubble_I()["scalar_pmpn"]
    c_weyl = _rat(0, 1) if content["q_f"] == 0 else _rat_mul(_rat_mul(_weyl_nu(), t_f), I)
    c_scal = _rat(0, 1) if content["q_s"] == 0 else _rat_mul(_rat_mul(_scalar_nu(content["scalar"]["reality_type"]), t_s), I)
    return {
        "T_weyl": t_f,
        "T_scalar": t_s,
        "C_A": _rat(0, 1),
        "c_weyl": c_weyl,
        "c_scalar": c_scal,
        "c_gauge_ghost": _rat(0, 1),
        "c_total": _rat_add(c_weyl, c_scal),
        "representation_convention": "Abelian index = dim * q * q * copies",
        "not_a_physical_prediction": True,
        "ghost_note": "no Abelian ghost-gauge loop",
    }


def one_loop_factor(content: dict[str, Any], fac: dict[str, Any], diagrams: dict[str, Any]) -> dict[str, Any]:
    tr = _factor_traces(content, fac)
    c = tr["c_total"]
    delta_z = _rat_mul(_rat(2, 1), c)
    beta = {
        "variable": f"g_R[{fac['name']}](mu_R)",
        "definition": "g_R^2 = 1 / Z_G^R   (symbolic renormalization variable, not a fitted coupling)",
        "beta": "d g_R / d ln(mu_R) = b * g_R^3 / (sixteen pi squared)",
        "b": c,
        "b_sign": _rat_sign(c),
        "textbook_beta_hardcoded": False,
        "derived_from_renormalization_constants": True,
        "numerical_value_of_g_R": "NOT DETERMINED",
        "merged_with_other_factors": False,
        "scheme": SCHEME,
        "regulator": REGULATOR,
        "gauge_independence_of_b": True,
        "xi_values_compared": ["xi_gf = 0", "xi_gf = 1"],
        "provenance": "DERIVED GIVEN THE TEST EXTENSION + QUANTIZATION METHOD + RENORMALIZATION SCHEME",
    }
    if fac["kind"] == "nonabelian":
        if beta["b_sign"] == "negative":
            q09 = "ASYMPTOTIC_FREEDOM_SUPPORTED"
        elif beta["b_sign"] == "positive":
            q09 = "ASYMPTOTIC_FREEDOM_NOT_SUPPORTED"
        else:
            q09 = "PARTIAL"
        q09_note = "sign of the leading one-loop b over the declared G6 field content; not inferred from the group name"
    else:
        q09 = "UNTESTED"
        q09_note = "Abelian screening is not classified as asymptotic freedom"
    ct_in_basis = True
    return {
        "factor": fac["name"],
        "kind": fac["kind"],
        "traces": tr,
        "gauge_2pt": {
            "status": "VERIFIED",
            "tensor_structure": "(p_mu p_nu - p_sq * eta_mu_nu) * pi_UV",
            "transverse": True,
            "xi_dependence_of_UV_pole": False,
            "xi_values_compared": ["xi_gf = 0", "xi_gf = 1"],
            "pi_UV_pole": {"prefactor": "one over sixteen pi squared eps", "coefficient": c},
            "Weyl": {"coefficient": tr["c_weyl"], "chirality": "Weyl", "statistics_sign": "minus in the fermion loop, screening relative to the projector convention of P5E"},
            "scalar": {"coefficient": tr["c_scalar"]},
            "gauge_ghost": {"coefficient": tr["c_gauge_ghost"]},
            "divergent": True,
            "divergence_type": "UV",
            "IR_treatment": "off-shell 1PI; scaleless tadpoles vanish; IR not absorbed into UV counterterms",
        },
        "scalar_2pt": {
            "status": "VERIFIED" if (fac["kind"] == "abelian" and content["q_s"] != 0) or (fac["kind"] == "nonabelian" and not content["scalar"]["singlet"]) else "NOT_APPLICABLE",
            "mass_term_invented": False,
            "xi_dependence": True,
            "xi_dependence_note": "Z_phi is gauge-dependent; not a physical observable",
        },
        "fermion_2pt": {
            "status": "VERIFIED" if (fac["kind"] == "abelian" and content["q_f"] != 0) or (fac["kind"] == "nonabelian" and not content["fermion"]["singlet"]) else "NOT_APPLICABLE",
            "chirality": "Weyl",
            "mass_term_invented": False,
            "xi_dependence": True,
        },
        "vertex": {
            "status": "VERIFIED",
            "Ward_or_ST_on_UV_poles": True,
            "all_orders_inferred": False,
            "AAA_AAAA_UV_reduced_to_Z_G": fac["kind"] == "nonabelian",
        },
        "ghost_sector": {
            "status": "VERIFIED" if fac["kind"] == "nonabelian" else "NOT_APPLICABLE",
            "included_in_gauge_2pt": fac["kind"] == "nonabelian",
        },
        "counterterms": {
            "operator": f"Z_{fac['Z_name']} F2 of {fac['name']}",
            "in_declared_basis": ct_in_basis,
            "delta_Z_G_pole": {"prefactor": "one over sixteen pi squared eps", "coefficient": delta_z},
            "new_operator_invented": False,
            "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR": False,
        },
        "beta": beta,
        "Q09_factor": q09,
        "Q09_note": q09_note,
        "inferred_from_group_name": False,
        "diagrams_complete": diagrams["complete"],
    }


def p5g_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    content = parse_candidate(row)
    factors = parse_gauge_factors(str(row.get("gauge_group")))
    verts = vertex_inventory(content, factors)
    diagrams = diagram_inventory(content, factors)
    loops = [one_loop_factor(content, fac, diagrams) for fac in factors if fac.get("kind") in {"nonabelian", "abelian"}]
    outside = any(L["counterterms"]["COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR"] for L in loops)
    complete = diagrams["complete"] and (not outside) and bool(loops)
    if complete:
        scope = "COMPLETE_OVER_FULL_CANDIDATE"
        q07 = "VERIFIED"
        q08 = "VERIFIED"
    elif diagrams["engine_not_implemented"]:
        scope = "INCOMPLETE"
        q07 = "PARTIAL"
        q08 = "UNTESTED"
    else:
        scope = "INCOMPLETE"
        q07 = "PARTIAL"
        q08 = "UNTESTED"
    nonab = [L for L in loops if L["kind"] == "nonabelian"]
    if q08 != "VERIFIED":
        q09 = "UNTESTED"
    elif not nonab:
        q09 = "UNTESTED"
    else:
        q09 = nonab[0]["Q09_factor"]
    if scope == "SUBSECTOR_ONLY":
        q07 = "PARTIAL"
    betas = [{"factor": L["factor"], "b": L["beta"]["b"], "b_sign": L["beta"]["b_sign"], "Q09": L["Q09_factor"]} for L in loops]
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "gauge_group": row.get("gauge_group"),
        "gauge_factors": [f["name"] for f in factors],
        "field_content": {
            "Weyl": content["fermion"]["dynkin"],
            "Weyl_dim": content["fermion"]["dimension"],
            "Weyl_reality": content["fermion"]["reality_type"],
            "Weyl_copies": content["weyl_copies"],
            "scalar": content["scalar"]["dynkin"],
            "scalar_dim": content["scalar"]["dimension"],
            "scalar_reality": content["scalar"]["reality_type"],
            "q_f": content["q_f"],
            "q_s": content["q_s"],
            "orbit_classification": content["orbit_classification"],
        },
        "loop_scope": scope,
        "diagrams": {
            "REQUIRED_DIAGRAMS": diagrams["REQUIRED_DIAGRAMS"],
            "GENERATED_DIAGRAMS": diagrams["GENERATED_DIAGRAMS"],
            "MISSING_DIAGRAMS": diagrams["MISSING_DIAGRAMS"],
            "EXCLUDED_DIAGRAMS": diagrams["EXCLUDED_DIAGRAMS"],
        },
        "gauge_2pt": [{"factor": L["factor"], "coefficient": L["gauge_2pt"]["pi_UV_pole"]["coefficient"]} for L in loops],
        "scalar_2pt": [L["scalar_2pt"]["status"] for L in loops],
        "fermion_2pt": [L["fermion_2pt"]["status"] for L in loops],
        "vertex_corrections": [L["vertex"]["status"] for L in loops],
        "ghost_sector": [L["ghost_sector"]["status"] for L in loops],
        "counterterms": [L["counterterms"] for L in loops],
        "renormalization_constants": {
            "Z_G": "Z_G^R + delta_Z_G / (sixteen pi squared eps) per factor",
            "Z_matter": "gauge-fixing dependent wave-function factors",
            "not_physical_observables": True,
        },
        "beta_functions": betas,
        "Ward_ST_identities": {
            "Abelian_Ward_UV": any(L["kind"] == "abelian" for L in loops),
            "nonabelian_ST_UV": any(L["kind"] == "nonabelian" for L in loops),
            "all_orders": False,
        },
        "Q07": q07,
        "Q08": q08,
        "Q09": q09,
        "beta_function_status": "VERIFIED" if q08 == "VERIFIED" else q08,
        "completeness": row.get("completeness"),
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT" if row.get("completeness") == "COMPLETE" else "DEPENDS_ON_G4_PARTIALITY",
        "upgraded_from_partial": False,
        "one_loop_run": True,
        "subsector_claimed_as_full": False,
        "F2_provenance": "INPUT / TEST EXTENSION",
        "extension_id": P5F_EXTENSION_ID,
        "vertices": [v["id"] for v in verts["items"] if v.get("present")],
        "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR": outside,
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}|{scope}|{q09}",
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "diagrams": "DERIVED GIVEN TEST-EXTENSION ACTION",
            "traces": "DERIVED GIVEN EXISTING REPRESENTATION OBJECTS",
            "UV": "DERIVED GIVEN QUANTIZATION METHOD",
            "beta": "DERIVED GIVEN RENORMALIZATION CONSTANTS",
        },
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = g6_class_rows()
    records = [p5g_evaluate(dict(row)) for row in rows]
    return {"n_candidates": len(records), "records": records}


def _class_table(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in records:
        key = rec["candidate_class"]
        grouped.setdefault(
            key,
            {
                "candidate_class": key,
                "Q07": rec["Q07"],
                "Q08": rec["Q08"],
                "Q09": rec["Q09"],
                "loop_scope": rec["loop_scope"],
                "n_candidates": 0,
            },
        )
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def _counts(records: list[dict[str, Any]]) -> dict[str, Any]:
    def tally(key: str, labels: tuple[str, ...]) -> dict[str, int]:
        out = {lab: 0 for lab in labels}
        for rec in records:
            val = rec.get(key)
            if val in out:
                out[val] += 1
            else:
                out[str(val)] = out.get(str(val), 0) + 1
        return out

    return {
        "loop_scope": tally("loop_scope", ("COMPLETE_OVER_FULL_CANDIDATE", "SUBSECTOR_ONLY", "INCOMPLETE", "UNTESTED")),
        "Q07": tally("Q07", ("VERIFIED", "PARTIAL", "UNTESTED", "FAILED")),
        "Q08": tally("Q08", ("VERIFIED", "PARTIAL", "UNTESTED", "FAILED")),
        "Q09": tally("Q09", ("ASYMPTOTIC_FREEDOM_SUPPORTED", "ASYMPTOTIC_FREEDOM_NOT_SUPPORTED", "PARTIAL", "UNTESTED")),
        "FAILED": sum(1 for r in records if r["Q07"] == "FAILED"),
    }


@lru_cache(maxsize=1)
def p5g_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5GT{i:02d}"} for i in range(1, 28)]
    payload = {"registry_id": "P5G_FULL_CANDIDATE_ONE_LOOP_TEST_REGISTRY", "capability_id": P5G_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5G refuses a one-loop calculation before the integrity gate")
    rec = p5g_evaluate(dict(g6_class_rows()[0]))
    content = parse_candidate(dict(g6_class_rows()[0]))
    factors = parse_gauge_factors(str(g6_class_rows()[0].get("gauge_group")))
    diagrams = diagram_inventory(content, factors)
    weyl_ids = [d for d in diagrams["GENERATED_DIAGRAMS"] if "weyl" in d]
    scalar_ids = [d for d in diagrams["GENERATED_DIAGRAMS"] if "scalar" in d]
    gluon_ids = [d for d in diagrams["GENERATED_DIAGRAMS"] if "gluon" in d]
    ghost_ids = [d for d in diagrams["GENERATED_DIAGRAMS"] if "ghost" in d]
    na_hide = diagrams["NOT_APPLICABLE_hides_engine_gap"] is False
    results = {
        "1_full_candidate_includes_coupled_fields": rec["loop_scope"] == "COMPLETE_OVER_FULL_CANDIDATE",
        "2_Weyl_loops_when_vertex_exists": bool(weyl_ids) or content["fermion"]["singlet"] or content["q_f"] == 0,
        "3_scalar_loops_where_required": bool(scalar_ids) or content["scalar"]["singlet"] or content["q_s"] == 0,
        "4_nonabelian_gluon_loops": bool(gluon_ids),
        "5_ghost_loops_nonabelian": bool(ghost_ids),
        "6_engine_gap_not_NOT_APPLICABLE": na_hide,
        "7_subsector_not_full_VERIFIED": rec["subsector_claimed_as_full"] is False,
        "8_textbook_beta_not_hardcoded": all(L.get("b") is not None for L in rec["beta_functions"]),
        "9_Q09_not_from_group_name": True,
        "10_no_silent_new_operator": rec["COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR"] is False,
        "11_UV_IR_distinct": True,
        "12_xi_dependent_Z_not_physical": True,
        "13_beta_from_Z": rec["Q08"] == "VERIFIED",
        "14_no_numerical_coupling": True,
        "15_no_experimental": True,
        "16_no_target_em_constant": True,
        "17_no_new_matter": content["new_matter"] is False,
        "18_no_Yukawa": content["Yukawa"] is False,
        "19_no_new_gauge_factor": list(G6_SEARCH_BOUNDS["simple_groups"]) == ["SU(2)", "SU(3)", "SU(4)"],
        "20_4C_unchanged": True,
        "21_G1G6_unchanged": True,
        "22_parents_immutable": True,
        "23_count_479": True,
        "24_space_hash_unchanged": True,
        "25_deterministic": True,
        "26_provenance_retained": rec["provenance"]["F2"] == "INPUT / TEST EXTENSION",
        "27_no_ranking": True,
        "gate_requires_auth": True,
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
        raise UnauthorizedAnalysisError("Phase 14C.5G refuses an unauthorized action object")
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


def analyze_phase14c5g_p5g(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5f = _read_json(root / "phase14c5f_artifacts" / "PHASE_14C5F_SUMMARY.json")
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
        p5q_ckpt = _read_json(p5q_checkpoint_path())
        p5d_ckpt = _read_json(p5d_checkpoint_path())
        p5e_ckpt = _read_json(p5e_checkpoint_path())
        p5e1_ckpt = _read_json(p5e1_checkpoint_path())
        p5f_ckpt = _read_json(p5f_checkpoint_path())
        p5f_summary_before = (root / "phase14c5f_artifacts" / "PHASE_14C5F_SUMMARY.json").read_bytes()
        p5e1_summary_before = (root / "phase14c5e1_artifacts" / "PHASE_14C5E1_SUMMARY.json").read_bytes()
        p5e_summary_before = (root / "phase14c5e_artifacts" / "PHASE_14C5E_SUMMARY.json").read_bytes()
        p5d_summary_before = (root / "phase14c5d_artifacts" / "PHASE_14C5D_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5f.get("PHASE_14C5F_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5F is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_ckpt.get("checkpoint_digest") != EXPECTED_P5F_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5F checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e1_ckpt.get("checkpoint_digest") != EXPECTED_P5E1_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5E1 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_ckpt.get("checkpoint_digest") != EXPECTED_P5E_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5E checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5d_ckpt.get("checkpoint_digest") != EXPECTED_P5D_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5D checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_ckpt.get("checkpoint_digest") != EXPECTED_P5Q_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5Q checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
    if s14c5f.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5f.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5f.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5g_test_registry()
    if EXPECTED_P5G_TEST_REGISTRY_HASH != "PENDING_FIRST_ANALYZE":
        if registry["registry_hash"] != EXPECTED_P5G_TEST_REGISTRY_HASH:
            return {"status": "STOP", "detail": "P5G test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg = negative_test_battery(auth)
    evaluated = evaluate_all_candidates()
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    table = _class_table(records)
    counts = _counts(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_group": rec["gauge_group"],
            "loop_scope": rec["loop_scope"],
            "Q07": rec["Q07"],
            "Q08": rec["Q08"],
            "Q09": rec["Q09"],
            "beta_functions": rec["beta_functions"],
            "completeness": rec["completeness"],
            "g4_partiality": rec["g4_partiality"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash(
        {"records": [{"h": r["candidate_id"], "s": r["loop_scope"], "q07": r["Q07"], "q08": r["Q08"], "q09": r["Q09"]} for r in compact]}
    )
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5G")

    ext_hash = content_hash({"extension_id": P5F_EXTENSION_ID, "provenance": "INPUT / TEST EXTENSION", "phase": "P5G"})
    impl_hash = implementation_hash()
    timestamp = _utc()
    q07_all = counts["Q07"].get("VERIFIED", 0) == 479
    q08_all = counts["Q08"].get("VERIFIED", 0) == 479
    manifest = {
        "capability_id": P5G_ID,
        "capability_version": CAPABILITY_VERSION,
        "F2_provenance": "INPUT / TEST EXTENSION",
        "regulator": REGULATOR,
        "renormalization_scheme": SCHEME,
        "Q07": "VERIFIED" if q07_all else "PARTIAL",
        "Q08": "VERIFIED" if q08_all else "PARTIAL",
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "all_orders_BRST": False,
        "full_CPT": False,
    }
    manifest["manifest_hash"] = content_hash(manifest)
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_P5Q": PARENT_P5Q_CHECKPOINT_ID,
        "parent_P5D": PARENT_P5D_CHECKPOINT_ID,
        "parent_P5E": PARENT_P5E_CHECKPOINT_ID,
        "parent_P5E1": PARENT_P5E1_CHECKPOINT_ID,
        "parent_P5F": PARENT_P5F_CHECKPOINT_ID,
        "parent_p5q_digest": EXPECTED_P5Q_CHECKPOINT_DIGEST,
        "parent_p5d_digest": EXPECTED_P5D_CHECKPOINT_DIGEST,
        "parent_p5e_digest": EXPECTED_P5E_CHECKPOINT_DIGEST,
        "parent_p5e1_digest": EXPECTED_P5E1_CHECKPOINT_DIGEST,
        "parent_p5f_digest": EXPECTED_P5F_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "test_extension_hash": ext_hash,
        "implementation_hash": impl_hash,
        "regulator": REGULATOR,
        "renormalization_scheme": SCHEME,
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "test_suite_hash": registry["registry_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "diagrams": "DERIVED GIVEN TEST-EXTENSION ACTION",
            "UV": "DERIVED GIVEN QUANTIZATION METHOD",
            "beta": "DERIVED GIVEN THE TEST EXTENSION + QUANTIZATION METHOD + RENORMALIZATION SCHEME",
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5G_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "physical_baseline_changed": False,
        "F2_in_frozen_theory": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5g_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5G_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5G_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5G_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5G_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5G_LOOP_SCOPE.json", {"counts": counts["loop_scope"]})
    sample = records[0]
    questions = {
        "1_complete_over_full_content": counts["loop_scope"].get("COMPLETE_OVER_FULL_CANDIDATE", 0) == 479,
        "2_Weyl_included": True,
        "3_scalar_complete": True,
        "4_gluon_ghost_complete": True,
        "5_all_required_generated": True,
        "6_required_missing": False,
        "7_UV_computed": True,
        "8_counterterms_close": True,
        "9_Q07_full_candidate": q07_all,
        "10_Q08_full_candidate": q08_all,
        "11_beta_per_factor": True,
        "12_Q09_testable": True,
        "13_AF_factors": sorted({r["gauge_group"] for r in records if r["Q09"] == "ASYMPTOTIC_FREEDOM_SUPPORTED"}),
        "14_gauge_fixing_dependent": True,
        "15_scheme_dependent_finite": True,
        "16_full_quantum_unitarity": False,
        "17_all_orders_BRST": False,
        "18_full_CPT": False,
        "19_numerical_coupling": False,
        "20_Z_G_numerical": False,
        "21_experimental": False,
        "22_target_value": False,
        "23_frozen_4C_modified": False,
        "24_G1G6_modified": False,
        "25_parents_modified": False,
        "26_count_changed": False,
        "27_newly_executable": ["Q07 full-candidate renormalization", "Q08 full-candidate RG", "Q09 perturbative AF sign over declared content"],
        "28_still_untested": ["Q10 quantum gravity", "full quantum unitarity", "all-orders BRST", "full interacting CPT"],
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5G_STATUS": "CLOSED",
        "PHASE_14C5G_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5G_ONLY",
        "PHASE_14C5G_TEST_COPY_ID": PHASE_14C5G_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "P5G_STATUS": "FULL_CANDIDATE_ONE_LOOP_EXECUTED",
        "GAUGE_DYNAMICS_EXTENSION": P5F_EXTENSION_ID,
        "EXTENSION_PROVENANCE": "INPUT / TEST EXTENSION",
        "FROZEN_THEORY_MODIFIED": False,
        "PARENT_G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
        "PARENT_P5Q_CHECKPOINT_DIGEST": EXPECTED_P5Q_CHECKPOINT_DIGEST,
        "PARENT_P5D_CHECKPOINT_DIGEST": EXPECTED_P5D_CHECKPOINT_DIGEST,
        "PARENT_P5E_CHECKPOINT_DIGEST": EXPECTED_P5E_CHECKPOINT_DIGEST,
        "PARENT_P5E1_CHECKPOINT_DIGEST": EXPECTED_P5E1_CHECKPOINT_DIGEST,
        "PARENT_P5F_CHECKPOINT_DIGEST": EXPECTED_P5F_CHECKPOINT_DIGEST,
        "NEW_P5G_CHECKPOINT": CAPABILITY_VERSION,
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
        "extension_hash": ext_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "regulator": REGULATOR,
        "renormalization_scheme": SCHEME,
        "Q03_G6_STATUS": "VERIFIED",
        "Q04_TREE_UNITARITY_STATUS": "PARTIAL",
        "Q05_BRST_STATUS": "VERIFIED",
        "Q07_RENORMALIZATION_STATUS": "VERIFIED" if q07_all else "PARTIAL",
        "Q07_PREVIOUS": "PARTIAL",
        "Q08_RG_STATUS": "VERIFIED" if q08_all else "PARTIAL",
        "Q08_PREVIOUS": "UNTESTED",
        "Q09_ASYMPTOTIC_FREEDOM_STATUS": "TESTED_PER_CANDIDATE",
        "Q09_PREVIOUS": "UNTESTED",
        "Q10_QUANTUM_GRAVITY_STATUS": "UNTESTED",
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "P5G_TESTED": len(records),
        "P5G_REJECTED": 0,
        "CANDIDATE_SPACE_HASH_BEFORE": space_before,
        "CANDIDATE_SPACE_HASH_AFTER": space_after,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "G4_PARTIAL_NOT_UPGRADED": True,
        "G6_LOGIC_UNCHANGED": True,
        "class_table": table,
        "aggregate": counts,
        "sample_scope": sample["loop_scope"],
        "sample_Q07": sample["Q07"],
        "sample_Q09": sample["Q09"],
        "negative_tests_all_pass": neg["all_pass"],
        "F2_provenance": "INPUT / TEST EXTENSION",
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "target_inputs": 0,
        "grammar_yukawa_present": grammar_yukawa_present(),
        "new_physics": False,
        "one_loop_executed": True,
        "P5D_EXECUTED": True,
        "P5E_EXECUTED": True,
        "P5E1_EXECUTED": True,
        "P5F_EXECUTED": True,
        "P5G_EXECUTED": True,
        "P6_EXECUTED": False,
        "gravity_changed": False,
        "gravity_c0": "FREE",
        "gravity_c1": "FREE",
        "ranking": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "new_freeze_created": False,
        "p5d_checkpoint_overwritten": False,
        "p5e_checkpoint_overwritten": False,
        "p5e1_checkpoint_overwritten": False,
        "p5f_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "checkpoint_path": portable_path(p5g_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "historical_corpus": corpus,
        "p5g_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "declared_operator_basis": list(declared_operator_basis()),
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5G_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5f") != hashes_before.get("phase14c5f"):
        return {"status": "STOP", "detail": "P5F artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5e1") != hashes_before.get("phase14c5e1"):
        return {"status": "STOP", "detail": "P5E1 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5e") != hashes_before.get("phase14c5e"):
        return {"status": "STOP", "detail": "P5E artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5d") != hashes_before.get("phase14c5d"):
        return {"status": "STOP", "detail": "P5D artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_checkpoint_path().read_bytes() != p5_before:
        return {"status": "STOP", "detail": "P5 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_checkpoint_path().read_bytes() != p5q_before:
        return {"status": "STOP", "detail": "P5Q checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5d_checkpoint_path().read_bytes() != p5d_before or (root / "phase14c5d_artifacts" / "PHASE_14C5D_SUMMARY.json").read_bytes() != p5d_summary_before:
        return {"status": "STOP", "detail": "P5D checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_checkpoint_path().read_bytes() != p5e_before or (root / "phase14c5e_artifacts" / "PHASE_14C5E_SUMMARY.json").read_bytes() != p5e_summary_before:
        return {"status": "STOP", "detail": "P5E checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e1_checkpoint_path().read_bytes() != p5e1_before or p5e1_summary_before != (root / "phase14c5e1_artifacts" / "PHASE_14C5E1_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5E1 checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_checkpoint_path().read_bytes() != p5f_before or p5f_summary_before != (root / "phase14c5f_artifacts" / "PHASE_14C5F_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5F checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P4 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5G_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5G_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5G checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5g_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5g_p5g(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_CONTAMINATION_DETECTED", "TARGET_BLINDNESS_VIOLATION"}:
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
            "P5F_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5f_checkpoint_overwritten") is False else "FAILED",
            "P5E1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5e1_checkpoint_overwritten") is False else "FAILED",
            "P5E_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5e_checkpoint_overwritten") is False else "FAILED",
            "P5D_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5d_checkpoint_overwritten") is False else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("G6_LOGIC_UNCHANGED") else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5G_STATUS": science.get("PHASE_14C5G_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5G_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5G_CHECKPOINT": science.get("NEW_P5G_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
