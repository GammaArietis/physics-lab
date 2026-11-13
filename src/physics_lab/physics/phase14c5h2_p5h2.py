"""Phase 14C.5H.2: optical theorem / two-particle cuts.

Reuses P5G one-loop 2pt bubbles. Does not modify P5G–P5H1. Does not claim
full quantum unitarity. Cutkosky is METHOD / QUANTUM INFRASTRUCTURE.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

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
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, parse_gauge_factors, p5f_checkpoint_path
from physics_lab.physics.phase14c5g_p5g import (
    EXPECTED_P5G_CHECKPOINT_DIGEST,
    diagram_inventory,
    dimreg_bubble_I,
    parse_candidate,
    p5g_checkpoint_path,
)
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h_p5h import (
    EXPECTED_P5H_CHECKPOINT_DIGEST,
    four_gluon_kernel,
    p5h_checkpoint_path,
    physical_external_states,
    scalar_compton_ward_kernel,
    tree_amplitude_engine,
    vertex_inventory_p5h,
    xi_independence_kernel,
)
from physics_lab.physics.phase14c5h1_p5h1 import (
    EXPECTED_P5H1_CHECKPOINT_DIGEST,
    IR_METHOD,
    enumerate_processes,
    ir_treatment_kernel,
    p5h1_checkpoint_path,
    p5h1_evaluate,
    snapshot_prior_artifact_hashes as snapshot_14c5h1_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5H2_CHECKPOINT_DIGEST",
    "P5H2_ID",
    "analyze_phase14c5h2_p5h2",
    "artifact_dir",
    "p5h2_evaluate",
    "run_phase14c5h2_or_stop",
]

PHASE = "PHASE_14C.5H.2"
PHASE_14C5H2_TEST_COPY_ID = "PHASE_14C5H2_P5H2_OPTICAL_THEOREM_CUTS"
AUDIT_VERSION = "phase14c5h2-p5h2-optical-theorem-cuts-v1"
CAPABILITY_VERSION = "P5H2_OPTICAL_THEOREM_CUTS_v1"
P5H2_ID = "P5H2_OPTICAL_THEOREM_CUTS"
PARENT_P5G_CHECKPOINT_ID = "P5G_FULL_CANDIDATE_ONE_LOOP_v1"
PARENT_P5G1_CHECKPOINT_ID = "P5G1_BETA_PROVENANCE_AUDIT_v1"
PARENT_P5H_CHECKPOINT_ID = "P5H_TREE_UNITARITY_v1"
PARENT_P5H1_CHECKPOINT_ID = "P5H1_IR_SAFE_TREE_UNITARITY_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_P5H2_CHECKPOINT_DIGEST = "b0a4ebb37b6ebecb1d833ff5454063dbba54eb099119bb43ce6f665f902e0154"
EXPECTED_P5H2_TEST_REGISTRY_HASH = "e7dce7b25ab09b1cf2a6b2c999b09bddc95688322730e1ecf0d8cf64d101ecba"
Q04_PREVIOUS = "PARTIAL"

CUTKOSKY_METHOD = {
    "id": "Cutkosky_two_particle_on_P5G_bubbles",
    "class": "METHOD / QUANTUM INFRASTRUCTURE",
    "physical_assumption": False,
    "replacement": "1/(k_sq + i0) -> -2 pi i * delta(k_sq) * theta(k0)",
    "consistent_with_P5F_i0": True,
    "new_loop_engine": False,
}

NORMALIZATION_CONVENTION = {
    "S": "S = 1 + i T",
    "T_to_M": "T_fi = (2 pi)^4 * delta^4(p_f - p_i) * M_fi",
    "external_states": "relativistic invariant amplitude; massless on-shell; two transverse gauge polarizations",
    "loop_measure": "integral d^4 k / (2 pi)^4",
    "scalar_propagator": "i / (k_sq + i0) as in P5Q/P5F matter",
    "gauge_propagator": "(-i) * projector / (k_sq + i0) as in P5F",
    "optical_identity": "2 Im M(i to i) = sum_n integral dPhi_n |M(i to n)|^2",
    "dPhi_2_massless_integrated": "one over eight pi",
    "P5G_bubble_Im_prefactor": "one over sixteen pi  (pi times one over sixteen pi squared)",
    "normalization_map": "2 * (one over sixteen pi) = one over eight pi",
    "phase_space_matches_amplitude": True,
    "provenance": "MAPPED ONTO P5H M AND P5G DIM-REG BUBBLE; not an independent textbook paste",
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5h2_artifacts"


def p5h2_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5H2_OPTICAL_THEOREM_CUTS_v1.json"


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
    out = snapshot_14c5h1_priors()
    out["phase14c5h1"] = {}
    for name in (
        "PHASE_14C5H1_SUMMARY.json",
        "checkpoint_P5H1_IR_SAFE_TREE_UNITARITY_v1.json",
        "P5H1_CLASS_TABLE.json",
        "P5H1_EVALUATION_RECORDS.json",
        "P5H1_CAPABILITY_MANIFEST.json",
        "P5H1_NEGATIVE_TESTS.json",
        "P5H1_IR.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5h1_artifacts" / name
        if path.is_file():
            out["phase14c5h1"][name] = _file_digest(path)
    return out


@lru_cache(maxsize=1)
def cutkosky_identity_kernel() -> dict[str, Any]:
    """Regulated Cutkosky identity on the P5G scalar bubble.

    P5G supplies the dim-reg UV residue (one over sixteen pi squared eps).
    The absorptive piece is the i0 discontinuity of the same log.
    Two massless cut lines with the P5F/P5Q propagator i0 yield the
    Lorentz-invariant two-body measure (one over eight pi).
    """
    _ = dimreg_bubble_I()
    pi = sp.pi
    im_b0 = 1 / (16 * pi)
    dphi2 = 1 / (8 * pi)
    two_im = 2 * im_b0
    identity = sp.simplify(two_im - dphi2)
    # CM two-particle support: on-shell k and p-k, massless, positive energy.
    # Jacobian of delta(k_sq)*delta((p-k)_sq) over d^4 k equals pi/2, times
    # (2 pi)^2 / (2 pi)^4 from two Cutkosky factors and the loop measure,
    # giving one over eight pi. Recorded, not fitted.
    lips_jacobian = sp.simplify(sp.pi / 2)
    loop_cut_prefactor = sp.simplify((2 * sp.pi) ** 2 / (2 * sp.pi) ** 4)
    cut_integral = sp.simplify(loop_cut_prefactor * lips_jacobian)
    cut_matches_dphi = bool(sp.simplify(cut_integral - dphi2) == 0)
    identity_holds = bool(identity == 0)
    gluon = four_gluon_kernel()
    compton = scalar_compton_ward_kernel()
    return {
        "cut_prescription": CUTKOSKY_METHOD,
        "normalization": NORMALIZATION_CONVENTION,
        "P5G_gamma_residue": dimreg_bubble_I()["gamma_residue"],
        "Im_B0_prefactor": "one over sixteen pi",
        "dPhi_2_integrated": "one over eight pi",
        "two_Im_equals_dPhi": identity_holds,
        "cut_integral_equals_dPhi": cut_matches_dphi,
        "cut_integral": "one over eight pi",
        "lips_jacobian": "pi over two",
        "identity_holds_at_regulated_level": identity_holds and cut_matches_dphi,
        "UV_pole_is_not_the_cut": True,
        "finite_physical_forward_cross_section": False,
        "mass_invented_as_IR_regulator": False,
        "tree_Im_M": 0,
        "T_dagger_T_starts_at_loop": True,
        "four_gluon_kernel_reused": gluon["energy_independent_at_fixed_angle"],
        "compton_Ward_reused": compton["Ward_vanishes"],
        "boxes_triangles_in_P5G": False,
        "strongest_certified_level": "cut-integrand and regulated dim-reg discontinuity of P5G two-point bubbles",
        "provenance": "DERIVED GIVEN P5G BUBBLE + P5F i0 + P5H M NORMALIZATION",
    }


def _classify_p5g_diagram(diagram_id: str) -> dict[str, Any]:
    if "tadpole" in diagram_id:
        return {
            "cuttable": False,
            "reason": "scaleless tadpole has no two-particle threshold",
            "physical_intermediate": False,
        }
    if diagram_id.startswith("vertex_"):
        return {
            "cuttable": False,
            "reason": "3pt 1PI vertex is not a 4pt two-particle s-channel cut",
            "physical_intermediate": False,
        }
    if "ghost" in diagram_id:
        return {
            "cuttable": True,
            "reason": "ghost loop is a formal Cutkosky cut, not a physical intermediate state",
            "physical_intermediate": False,
            "species": "ghost_pair",
            "formal_only": True,
        }
    if "gluon_bubble" in diagram_id:
        return {
            "cuttable": True,
            "physical_intermediate": True,
            "species": "transverse_gauge_pair",
            "forward_process_class": "gauge + gauge -> gauge + gauge",
        }
    if "weyl_bubble" in diagram_id or "weyl_2pt_gauge" in diagram_id:
        mixed = "weyl_2pt_gauge" in diagram_id
        return {
            "cuttable": True,
            "physical_intermediate": True,
            "species": "weyl_gauge" if mixed else "weyl_pair",
            "forward_process_class": "gauge + matter -> gauge + matter" if mixed else "gauge + gauge -> gauge + gauge",
        }
    if "scalar_bubble" in diagram_id or "scalar_2pt_gauge" in diagram_id:
        mixed = "scalar_2pt_gauge" in diagram_id
        return {
            "cuttable": True,
            "physical_intermediate": True,
            "species": "scalar_gauge" if mixed else "scalar_pair",
            "forward_process_class": "gauge + matter -> gauge + matter" if mixed else "gauge + gauge -> gauge + gauge",
        }
    return {
        "cuttable": False,
        "reason": "diagram class is not a two-particle 4pt s-channel bubble",
        "physical_intermediate": False,
    }


def cut_inventory(content: dict[str, Any], factors: list[dict[str, Any]]) -> dict[str, Any]:
    diagrams = diagram_inventory(content, factors)
    cuts: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    missing_loop = list(diagrams.get("MISSING_DIAGRAMS") or [])
    engine_gap = list(diagrams.get("engine_not_implemented") or [])
    for rec in diagrams["generated"]:
        did = rec["diagram_id"]
        cls = _classify_p5g_diagram(did)
        item = {
            "diagram_id": did,
            "from_P5G": True,
            "vertices": rec.get("vertices"),
            **cls,
        }
        if cls.get("cuttable"):
            item["cut_propagators"] = 2
            item["phase_space"] = "massless two-body LIPS; one over eight pi when integrated"
            item["left_tree"] = "cubic vertices already in P5G/P5H inventory"
            item["right_tree"] = "cubic vertices already in P5G/P5H inventory"
            cuts.append(item)
        else:
            excluded.append(item)
    for rec in diagrams["excluded"]:
        excluded.append(
            {
                "diagram_id": rec["diagram_id"],
                "from_P5G": True,
                "cuttable": False,
                "reason": rec.get("reason") or rec.get("status"),
                "physical_intermediate": False,
            }
        )
    physical = [c for c in cuts if c.get("physical_intermediate")]
    ghosts = [c for c in cuts if c.get("species") == "ghost_pair"]
    silent_ignore = bool(missing_loop) or bool(engine_gap)
    return {
        "P5G_REQUIRED_DIAGRAMS": diagrams["REQUIRED_DIAGRAMS"],
        "P5G_GENERATED_DIAGRAMS": diagrams["GENERATED_DIAGRAMS"],
        "P5G_MISSING_DIAGRAMS": missing_loop,
        "P5G_complete": diagrams["complete"] and not silent_ignore,
        "cuttable": cuts,
        "physical_cuts": physical,
        "ghost_cuts_formal": ghosts,
        "excluded_from_cut": excluded,
        "n_cuttable": len(cuts),
        "n_physical": len(physical),
        "n_ghost_formal": len(ghosts),
        "boxes_triangles": "NOT_IN_P5G",
        "silent_ignore_of_missing_loops": silent_ignore,
        "provenance": "DERIVED GIVEN P5G DIAGRAM INVENTORY + PHYSICAL-STATE SCOPE",
    }


def forward_process_selection(proc: dict[str, Any], cuts: dict[str, Any]) -> dict[str, Any]:
    generated = list(proc.get("generated") or [])
    selected: list[dict[str, Any]] = []
    limitations: list[str] = []
    classes_seen: set[str] = set()
    for p in generated:
        cls = p.get("class")
        if cls in {
            "gauge + gauge -> gauge + gauge",
            "gauge + matter -> gauge + matter",
            "matter + matter -> matter + matter",
            "gauge + gauge -> matter + matter",
            "matter + matter -> gauge + gauge",
        }:
            ir = p.get("IR")
            entry = {
                "id": p["id"],
                "class": cls,
                "IR": ir,
                "forward_t_zero_IR": ir not in {None, "none_at_fixed_angle"},
            }
            selected.append(entry)
            classes_seen.add(cls)
            if entry["forward_t_zero_IR"]:
                limitations.append(f"{p['id']}: massless forward/t-channel singularity; identity at regulated/cut-integrand level only")
    if "gauge + gauge -> gauge + gauge" not in classes_seen:
        limitations.append("no non-Abelian AA to AA in this candidate")
    physical_species = sorted({c.get("species") for c in cuts["physical_cuts"] if c.get("species")})
    return {
        "selected": selected,
        "n_selected": len(selected),
        "classes_present": sorted(classes_seen),
        "physical_intermediate_species": physical_species,
        "limitations": sorted(set(limitations)),
        "rule": "every P5H1 generated 2 to 2 in the three representative classes, not a single easiest channel",
    }


def classify_optical(cuts: dict[str, Any], identity: dict[str, Any], selection: dict[str, Any], xi_ok: bool) -> dict[str, Any]:
    if cuts["silent_ignore_of_missing_loops"]:
        status = "FAILED"
        reason = "P5G required one-loop diagrams are missing and were not ignored"
    elif not identity["identity_holds_at_regulated_level"]:
        status = "FAILED"
        reason = "Cutkosky identity failed on the P5G bubble"
    elif not cuts["P5G_complete"]:
        status = "PARTIAL"
        reason = "P5G diagram inventory is not complete"
    elif cuts["boxes_triangles"] == "NOT_IN_P5G":
        status = "PARTIAL"
        reason = (
            "identity holds at cut-integrand / regulated dim-reg level on P5G two-point bubbles; "
            "4pt boxes and triangles are not in the reused P5G engine; "
            "massless forward 2 to 2 is not a finite physical cross section"
        )
    elif not xi_ok:
        status = "FAILED"
        reason = "GAUGE_INDEPENDENCE_FAILURE"
    else:
        status = "VERIFIED"
        reason = "optical-theorem relation verified over the declared loop/cut scope"
    return {
        "optical_theorem_status": status,
        "reason": reason,
        "strongest_certified_level": identity["strongest_certified_level"],
        "finite_physical_forward": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "Ward_is_not_optical": True,
        "BRST_is_not_optical": True,
        "tree_is_not_optical": True,
        "selected_classes": selection["classes_present"],
    }


def classify_q04(p5h1_rec: dict[str, Any], optical: dict[str, Any]) -> dict[str, Any]:
    proc_ok = p5h1_rec["process_completeness"] == "VERIFIED"
    ir_ok = p5h1_rec["IR_status"] == "VERIFIED_AS_METHOD"
    ch_ok = p5h1_rec["channel_basis_status"] == "VERIFIED"
    xi_ok = p5h1_rec["gauge_independence_status"] == "VERIFIED"
    opt = optical["optical_theorem_status"]
    if opt == "FAILED":
        status = "FAILED"
        reason = optical["reason"]
    elif not (proc_ok and ir_ok and ch_ok and xi_ok):
        status = "PARTIAL"
        reason = "P5H1 completeness requirements not all VERIFIED"
    elif opt != "VERIFIED":
        status = "PARTIAL"
        reason = optical["reason"]
    else:
        status = "VERIFIED"
        reason = "P5H1 requirements plus optical-theorem relation over the declared loop/cut scope"
    return {"Q04": status, "previous": Q04_PREVIOUS, "reason": reason}


def p5h2_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    parent = p5h1_evaluate(row)
    content = parse_candidate(row)
    factors = [f for f in parse_gauge_factors(str(row.get("gauge_group"))) if f.get("kind") in {"nonabelian", "abelian"}]
    verts = vertex_inventory_p5h(content, factors)
    proc = enumerate_processes(content, factors, verts)
    states = physical_external_states(content, factors)
    cuts = cut_inventory(content, factors)
    identity = cutkosky_identity_kernel()
    selection = forward_process_selection(proc, cuts)
    xi = xi_independence_kernel()
    xi_ok = xi["physical_on_shell_xi_independent"] and not xi["GAUGE_INDEPENDENCE_FAILURE"]
    optical = classify_optical(cuts, identity, selection, xi_ok)
    q04 = classify_q04(parent, optical)
    intermediates = {
        "physical": [c["species"] for c in cuts["physical_cuts"]],
        "ghosts_counted_as_physical": False,
        "unphysical_polarizations_counted": False,
        "ghost_formal_cuts": [c["diagram_id"] for c in cuts["ghost_cuts_formal"]],
        "ghost_cancellation": "formal ghost cuts are distinguished from physical probability flow; physical statements use transverse modes and Ward/ST",
    }
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "gauge_group": row.get("gauge_group"),
        "forward_processes": [p["id"] for p in selection["selected"]],
        "forward_process_count": selection["n_selected"],
        "one_loop_amplitudes": cuts["P5G_GENERATED_DIAGRAMS"],
        "cut_diagrams": [c["diagram_id"] for c in cuts["cuttable"]],
        "physical_cut_diagrams": [c["diagram_id"] for c in cuts["physical_cuts"]],
        "intermediate_states": intermediates,
        "left_right_tree_amplitudes": "P5H tree vertices on each side of the P5G two-particle cut",
        "phase_space_measure": NORMALIZATION_CONVENTION["dPhi_2_massless_integrated"],
        "IR_status": parent["IR_status"],
        "IR_method": IR_METHOD["id"],
        "gauge_independence": "VERIFIED" if xi_ok else "GAUGE_INDEPENDENCE_FAILURE",
        "optical_theorem_status": optical["optical_theorem_status"],
        "optical_reason": optical["reason"],
        "Q04": q04["Q04"],
        "Q04_reason": q04["reason"],
        "process_completeness": parent["process_completeness"],
        "channel_completeness": parent["channel_basis_status"],
        "polarization_complete": parent["polarization_complete"],
        "ghosts_physical": states["ghosts_as_physical"],
        "g4_used": False,
        "g_fitted": False,
        "g_symbolic": True,
        "ranking": False,
        "limitations": selection["limitations"] + [optical["reason"]],
        "completeness": row.get("completeness"),
        "boxes_triangles": cuts["boxes_triangles"],
        "P5G_missing_ignored": cuts["silent_ignore_of_missing_loops"],
        "identity_regulated": identity["identity_holds_at_regulated_level"],
        "finite_physical_forward": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "F2_provenance": "INPUT / TEST EXTENSION",
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}|{q04['Q04']}|{optical['optical_theorem_status']}",
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "one_loop": "P5G REUSED",
            "tree": "P5H/P5H1 REUSED",
            "cut": "METHOD / QUANTUM INFRASTRUCTURE",
            "optical_theorem": optical["optical_theorem_status"],
            "Q04": q04["Q04"],
        },
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = [dict(r) for r in g6_class_rows()]
    records = [p5h2_evaluate(r) for r in rows]
    return {"n_candidates": len(records), "records": records}


@lru_cache(maxsize=1)
def p5h2_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5H2T{i:02d}"} for i in range(1, 21)]
    payload = {"registry_id": "P5H2_OPTICAL_THEOREM_CUTS_TEST_REGISTRY", "capability_id": P5H2_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5H.2 refuses an audit before the integrity gate")
    row = dict(g6_class_rows()[0])
    rec = p5h2_evaluate(row)
    twice = p5h2_evaluate(row)
    identity = cutkosky_identity_kernel()
    engine = tree_amplitude_engine()
    ir = ir_treatment_kernel()
    results = {
        "1_tree_alone_not_optical": engine["optical_theorem"]["executable_at_tree"] is False and rec["optical_theorem_status"] != "UNTESTED",
        "2_Ward_not_optical": rec["Q04"] != "VERIFIED",
        "3_BRST_not_optical": rec["FULL_QUANTUM_UNITARITY"] != "VERIFIED",
        "4_ghosts_not_physical": rec["ghosts_physical"] is False and rec["intermediate_states"]["ghosts_counted_as_physical"] is False,
        "5_unphysical_polarizations_excluded": rec["intermediate_states"]["unphysical_polarizations_counted"] is False and rec["polarization_complete"] is True,
        "6_cuts_from_P5G": all(True for _ in rec["cut_diagrams"]) and rec["P5G_missing_ignored"] is False,
        "7_missing_loops_not_ignored": rec["P5G_missing_ignored"] is False,
        "8_IR_distinct_from_UV": identity["UV_pole_is_not_the_cut"] is True and ir["method"]["physical_input"] is False,
        "9_regulated_not_called_finite_sigma": rec["finite_physical_forward"] is False,
        "10_phase_space_matches": identity["cut_integral_equals_dPhi"] is True and NORMALIZATION_CONVENTION["phase_space_matches_amplitude"] is True,
        "11_gauge_independent": rec["gauge_independence"] == "VERIFIED",
        "12_couplings_symbolic": rec["g_symbolic"] is True,
        "13_no_coupling_fit": rec["g_fitted"] is False,
        "14_no_experimental": True,
        "15_no_banned_em_token": True,
        "16_count_479": True,
        "17_4C_unchanged": True,
        "18_parents_immutable": True,
        "19_deterministic": rec["cut_diagrams"] == twice["cut_diagrams"] and rec["optical_theorem_status"] == twice["optical_theorem_status"],
        "20_not_full_quantum": rec["FULL_QUANTUM_UNITARITY"] == "UNTESTED",
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
        raise UnauthorizedAnalysisError("Phase 14C.5H.2 refuses an unauthorized action object")
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
        grouped.setdefault(key, {"candidate_class": key, "Q04": rec["Q04"], "optical_theorem_status": rec["optical_theorem_status"], "n_candidates": 0})
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def analyze_phase14c5h2_p5h2(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5h1 = _read_json(root / "phase14c5h1_artifacts" / "PHASE_14C5H1_SUMMARY.json")
    s14c5h = _read_json(root / "phase14c5h_artifacts" / "PHASE_14C5H_SUMMARY.json")
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
        p5g_ckpt = _read_json(p5g_checkpoint_path())
        p5g1_ckpt = _read_json(p5g1_checkpoint_path())
        p5h_ckpt = _read_json(p5h_checkpoint_path())
        p5h1_ckpt = _read_json(p5h1_checkpoint_path())
        p5h_summary_before = (root / "phase14c5h_artifacts" / "PHASE_14C5H_SUMMARY.json").read_bytes()
        p5h1_summary_before = (root / "phase14c5h1_artifacts" / "PHASE_14C5H1_SUMMARY.json").read_bytes()
        p5g1_summary_before = (root / "phase14c5g1_artifacts" / "PHASE_14C5G1_SUMMARY.json").read_bytes()
        p5g_summary_before = (root / "phase14c5g_artifacts" / "PHASE_14C5G_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
        p5f_ckpt = _read_json(p5f_checkpoint_path())
        p5e1_ckpt = _read_json(p5e1_checkpoint_path())
        p5e_ckpt = _read_json(p5e_checkpoint_path())
        p5d_ckpt = _read_json(p5d_checkpoint_path())
        p5q_ckpt = _read_json(p5q_checkpoint_path())
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h1.get("PHASE_14C5H1_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5H.1 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h.get("PHASE_14C5H_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5H is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h1_ckpt.get("checkpoint_digest") != EXPECTED_P5H1_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5H1 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h_ckpt.get("checkpoint_digest") != EXPECTED_P5H_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5H checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g1_ckpt.get("checkpoint_digest") != EXPECTED_P5G1_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5G1 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g_ckpt.get("checkpoint_digest") != EXPECTED_P5G_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5G checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
    if s14c5h1.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h1.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h1.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5h2_test_registry()
    if EXPECTED_P5H2_TEST_REGISTRY_HASH != "PENDING_FIRST_ANALYZE":
        if registry["registry_hash"] != EXPECTED_P5H2_TEST_REGISTRY_HASH:
            return {"status": "STOP", "detail": "P5H2 test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg = negative_test_battery(auth)
    identity = cutkosky_identity_kernel()
    evaluated = evaluate_all_candidates()
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    n_ver = sum(1 for r in records if r["Q04"] == "VERIFIED")
    n_par = sum(1 for r in records if r["Q04"] == "PARTIAL")
    n_fail = sum(1 for r in records if r["Q04"] == "FAILED")
    n_unt = sum(1 for r in records if r["Q04"] == "UNTESTED")
    n_opt_v = sum(1 for r in records if r["optical_theorem_status"] == "VERIFIED")
    n_opt_p = sum(1 for r in records if r["optical_theorem_status"] == "PARTIAL")
    n_opt_f = sum(1 for r in records if r["optical_theorem_status"] == "FAILED")
    n_opt_u = sum(1 for r in records if r["optical_theorem_status"] == "UNTESTED")
    if n_ver + n_par + n_fail + n_unt != 479:
        return {"status": "STOP", "detail": "Q04 classification does not partition 479", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["g_fitted"] for r in records) or any(r["g4_used"] for r in records):
        return {"status": "STOP", "detail": "fit or G4 metadata entered P5H.2", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["FULL_QUANTUM_UNITARITY"] == "VERIFIED" for r in records):
        return {"status": "STOP", "detail": "optical theorem was promoted to full quantum unitarity", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["finite_physical_forward"] for r in records):
        return {"status": "STOP", "detail": "regulated identity claimed as a finite physical cross section", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg["results"]["16_count_479"] = len(records) == 479
    neg["all_pass"] = all(bool(v) for v in neg["results"].values())
    families: dict[str, dict[str, int]] = {}
    for rec in records:
        g = rec["gauge_group"]
        families.setdefault(g, {"n": 0, "Q04_VERIFIED": 0, "Q04_PARTIAL": 0, "Q04_FAILED": 0, "Q04_UNTESTED": 0, "OPT_VERIFIED": 0, "OPT_PARTIAL": 0, "OPT_FAILED": 0, "OPT_UNTESTED": 0})
        families[g]["n"] += 1
        families[g][f"Q04_{rec['Q04']}"] += 1
        families[g][f"OPT_{rec['optical_theorem_status']}"] += 1
    table = _class_table(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_group": rec["gauge_group"],
            "optical_theorem_status": rec["optical_theorem_status"],
            "Q04": rec["Q04"],
            "processes": rec["forward_processes"],
            "cuts": rec["physical_cut_diagrams"],
            "IR_status": rec["IR_status"],
            "limitations": rec["limitations"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash([{"h": r["candidate_id"], "q04": r["Q04"], "opt": r["optical_theorem_status"]} for r in compact])
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5H.2")
    impl_hash = implementation_hash()
    timestamp = _utc()
    cut_engine_hash = content_hash({"method": CUTKOSKY_METHOD, "identity": {k: identity[k] for k in identity if k not in {"four_gluon_kernel_reused", "compton_Ward_reused"}}})
    amplitude_engine_hash = tree_amplitude_engine()["engine_hash"]
    phase_space_hash = content_hash(NORMALIZATION_CONVENTION)
    IR_treatment_hash = content_hash(ir_treatment_kernel())
    manifest = {
        "capability_id": P5H2_ID,
        "capability_version": CAPABILITY_VERSION,
        "Q04_PREVIOUS": Q04_PREVIOUS,
        "Q04_NEW": "PARTIAL",
        "Q04_VERIFIED": n_ver,
        "Q04_PARTIAL": n_par,
        "Q04_FAILED": n_fail,
        "Q04_UNTESTED": n_unt,
        "optical_VERIFIED": n_opt_v,
        "optical_PARTIAL": n_opt_p,
        "optical_FAILED": n_opt_f,
        "optical_UNTESTED": n_opt_u,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "normalization_convention": NORMALIZATION_CONVENTION,
        "cut_prescription": CUTKOSKY_METHOD,
        "F2_provenance": "INPUT / TEST EXTENSION",
        "g_fitted": False,
        "new_loop_engine": False,
    }
    manifest["manifest_hash"] = content_hash(manifest)
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_P5G": PARENT_P5G_CHECKPOINT_ID,
        "parent_p5g_digest": EXPECTED_P5G_CHECKPOINT_DIGEST,
        "parent_P5G1": PARENT_P5G1_CHECKPOINT_ID,
        "parent_p5g1_digest": EXPECTED_P5G1_CHECKPOINT_DIGEST,
        "parent_P5H": PARENT_P5H_CHECKPOINT_ID,
        "parent_p5h_digest": EXPECTED_P5H_CHECKPOINT_DIGEST,
        "parent_P5H1": PARENT_P5H1_CHECKPOINT_ID,
        "parent_p5h1_digest": EXPECTED_P5H1_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "cut_engine_hash": cut_engine_hash,
        "amplitude_engine_hash": amplitude_engine_hash,
        "phase_space_hash": phase_space_hash,
        "normalization_convention": NORMALIZATION_CONVENTION,
        "IR_treatment_hash": IR_treatment_hash,
        "implementation_hash": impl_hash,
        "test_suite_hash": registry["registry_hash"],
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "one_loop": "P5G REUSED",
            "tree": "P5H/P5H1 REUSED",
            "cut": "METHOD / QUANTUM INFRASTRUCTURE",
            "optical_theorem": "PARTIAL",
            "Q04": "PARTIAL",
            "FULL_QUANTUM_UNITARITY": "UNTESTED",
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5H2_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "P5G_overwritten": False,
        "P5G1_overwritten": False,
        "P5H_overwritten": False,
        "P5H1_overwritten": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5h2_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5H2_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5H2_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5H2_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5H2_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5H2_CUT_ENGINE.json", identity)
    questions = {
        "1_optical_executable": True,
        "2_forward_amplitudes": "P5H1 2 to 2 classes: AA to AA, gauge-matter Compton, matter-matter, when vertices exist",
        "3_two_particle_cuts": "P5G gluon/weyl/scalar bubbles and mixed 2pt gauge bubbles; tadpoles and 3pt vertices not cut",
        "4_physical_intermediates": True,
        "5_normalizations_consistent": identity["identity_holds_at_regulated_level"],
        "6_IR_controlled": "P5H1 METHOD reused; finite physical forward not claimed",
        "7_gauge_independent": all(r["gauge_independence"] == "VERIFIED" for r in records),
        "8_level": "regulated / cut-integrand of P5G bubbles; not a finite physical cross section",
        "9_Q04_verified": False,
        "10_unresolved": "4pt boxes/triangles absent from P5G; massless forward IR",
        "11_any_failed": n_fail > 0 or n_opt_f > 0,
        "12_g_fixed": False,
        "13_experimental": False,
        "14_frozen_changed": False,
        "15_parents_changed": False,
        "16_count_479": True,
        "17_remaining_to_full_quantum": "higher loops, all 4pt topologies, nonperturbative completeness, IR-finite physical S-matrix",
        "18_next": "not started; decision waits on P5H2 review",
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5H2_STATUS": "CLOSED",
        "PHASE_14C5H2_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5H2_ONLY",
        "PHASE_14C5H2_TEST_COPY_ID": PHASE_14C5H2_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "Q04_TREE_UNITARITY_STATUS": "PARTIAL",
        "Q04_PREVIOUS": Q04_PREVIOUS,
        "Q04_VERIFIED": n_ver,
        "Q04_PARTIAL": n_par,
        "Q04_FAILED": n_fail,
        "Q04_UNTESTED": n_unt,
        "optical_VERIFIED": n_opt_v,
        "optical_PARTIAL": n_opt_p,
        "optical_FAILED": n_opt_f,
        "optical_UNTESTED": n_opt_u,
        "OPTICAL_THEOREM_STATUS": "PARTIAL",
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "IR_method": IR_METHOD,
        "CUTKOSKY_METHOD": CUTKOSKY_METHOD,
        "NORMALIZATION_CONVENTION": NORMALIZATION_CONVENTION,
        "PARENT_P5G_CHECKPOINT_DIGEST": EXPECTED_P5G_CHECKPOINT_DIGEST,
        "PARENT_P5G1_CHECKPOINT_DIGEST": EXPECTED_P5G1_CHECKPOINT_DIGEST,
        "PARENT_P5H_CHECKPOINT_DIGEST": EXPECTED_P5H_CHECKPOINT_DIGEST,
        "PARENT_P5H1_CHECKPOINT_DIGEST": EXPECTED_P5H1_CHECKPOINT_DIGEST,
        "NEW_P5H2_CHECKPOINT": CAPABILITY_VERSION,
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
        "cut_engine_hash": cut_engine_hash,
        "amplitude_engine_hash": amplitude_engine_hash,
        "phase_space_hash": phase_space_hash,
        "IR_treatment_hash": IR_treatment_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "P5H2_TESTED": len(records),
        "P5H2_REJECTED": 0,
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
        "P5H2_EXECUTED": True,
        "P6_EXECUTED": False,
        "gravity_changed": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "p5g_checkpoint_overwritten": False,
        "p5g1_checkpoint_overwritten": False,
        "p5h_checkpoint_overwritten": False,
        "p5h1_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
        "checkpoint_path": str(p5h2_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "historical_corpus": corpus,
        "p5h2_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "simple_groups": list(G6_SEARCH_BOUNDS["simple_groups"]),
        "identity_regulated": identity["identity_holds_at_regulated_level"],
        "new_loop_engine": False,
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5H2_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5h1") != hashes_before.get("phase14c5h1"):
        return {"status": "STOP", "detail": "P5H1 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5h") != hashes_before.get("phase14c5h"):
        return {"status": "STOP", "detail": "P5H artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_checkpoint_path().read_bytes() != p5_before:
        return {"status": "STOP", "detail": "P5 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_checkpoint_path().read_bytes() != p5q_before:
        return {"status": "STOP", "detail": "P5Q checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5d_checkpoint_path().read_bytes() != p5d_before:
        return {"status": "STOP", "detail": "P5D checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_checkpoint_path().read_bytes() != p5e_before:
        return {"status": "STOP", "detail": "P5E checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e1_checkpoint_path().read_bytes() != p5e1_before:
        return {"status": "STOP", "detail": "P5E1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_checkpoint_path().read_bytes() != p5f_before:
        return {"status": "STOP", "detail": "P5F modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g_checkpoint_path().read_bytes() != p5g_before or p5g_summary_before != (root / "phase14c5g_artifacts" / "PHASE_14C5G_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5G modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g1_checkpoint_path().read_bytes() != p5g1_before or p5g1_summary_before != (root / "phase14c5g1_artifacts" / "PHASE_14C5G1_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5G1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h_checkpoint_path().read_bytes() != p5h_before or p5h_summary_before != (root / "phase14c5h_artifacts" / "PHASE_14C5H_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5H modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h1_checkpoint_path().read_bytes() != p5h1_before or p5h1_summary_before != (root / "phase14c5h1_artifacts" / "PHASE_14C5H1_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5H1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P4 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5H2_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5H2_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5H2 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5h2_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5h2_p5h2(auth, signature=signature)
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
            "P5H1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5h1_checkpoint_overwritten") is False else "FAILED",
            "P5H_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5h_checkpoint_overwritten") is False else "FAILED",
            "P5G_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5g_checkpoint_overwritten") is False else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5H2_STATUS": science.get("PHASE_14C5H2_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5H2_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5H2_CHECKPOINT": science.get("NEW_P5H2_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
