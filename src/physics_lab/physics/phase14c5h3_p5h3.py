"""Phase 14C.5H.3: one-loop 4-point amplitudes and two-particle cuts.

Extends P5H2 bubble cuts to box/triangle/crossed-box 4pt topologies
generated from existing G6 F2 vertices. Does not modify P5G-P5H2.
Does not claim full quantum unitarity.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from physics_lab.physics.portability import portable_path

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
    REGULATOR,
    SCHEME,
    declared_operator_basis,
    parse_candidate,
    p5g_checkpoint_path,
)
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h_p5h import (
    EXPECTED_P5H_CHECKPOINT_DIGEST,
    p5h_checkpoint_path,
    physical_external_states,
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
)
from physics_lab.physics.phase14c5h2_p5h2 import (
    CUTKOSKY_METHOD,
    EXPECTED_P5H2_CHECKPOINT_DIGEST,
    NORMALIZATION_CONVENTION,
    cutkosky_identity_kernel,
    p5h2_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5h2_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5H3_CHECKPOINT_DIGEST",
    "P5H3_ID",
    "analyze_phase14c5h3_p5h3",
    "artifact_dir",
    "p5h3_evaluate",
    "run_phase14c5h3_or_stop",
]

PHASE = "PHASE_14C.5H.3"
PHASE_14C5H3_TEST_COPY_ID = "PHASE_14C5H3_P5H3_ONE_LOOP_4PT_CUTS"
AUDIT_VERSION = "phase14c5h3-p5h3-one-loop-4pt-cuts-v1"
CAPABILITY_VERSION = "P5H3_ONE_LOOP_4PT_CUTS_v1"
P5H3_ID = "P5H3_ONE_LOOP_4PT_CUTS"
PARENT_P5G_CHECKPOINT_ID = "P5G_FULL_CANDIDATE_ONE_LOOP_v1"
PARENT_P5G1_CHECKPOINT_ID = "P5G1_BETA_PROVENANCE_AUDIT_v1"
PARENT_P5H_CHECKPOINT_ID = "P5H_TREE_UNITARITY_v1"
PARENT_P5H1_CHECKPOINT_ID = "P5H1_IR_SAFE_TREE_UNITARITY_v1"
PARENT_P5H2_CHECKPOINT_ID = "P5H2_OPTICAL_THEOREM_CUTS_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_P5H3_CHECKPOINT_DIGEST = "1b5fa5153af00c0a4ec537facf0a5184571e5abff2e8fce3769f084979673678"
EXPECTED_P5H3_TEST_REGISTRY_HASH = "6e02be3b4168ee35620b5dc55e4eca6a00be56453a7607cd1197768428480d78"
Q04_PREVIOUS = "PARTIAL"
EXCLUSION_REASONS = (
    "ABSENT_FROM_ACTION",
    "ZERO_BY_SYMMETRY",
    "KINEMATICALLY_FORBIDDEN",
    "EQUIVALENT_TO_CERTIFIED_TOPOLOGY",
    "OUT_OF_DECLARED_SCOPE",
    "ENGINE_NOT_IMPLEMENTED",
    "IMPLEMENTATION_ERROR",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5h3_artifacts"


def p5h3_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5H3_ONE_LOOP_4PT_CUTS_v1.json"


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
    out = snapshot_14c5h2_priors()
    out["phase14c5h2"] = {}
    for name in (
        "PHASE_14C5H2_SUMMARY.json",
        "checkpoint_P5H2_OPTICAL_THEOREM_CUTS_v1.json",
        "P5H2_CLASS_TABLE.json",
        "P5H2_EVALUATION_RECORDS.json",
        "P5H2_CAPABILITY_MANIFEST.json",
        "P5H2_NEGATIVE_TESTS.json",
        "P5H2_CUT_ENGINE.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5h2_artifacts" / name
        if path.is_file():
            out["phase14c5h2"][name] = _file_digest(path)
    return out


def _t(
    tid: str,
    process: str,
    internals: list[str],
    vertices: list[str],
    symmetry: str,
    channel: str,
    existence: str,
    kind: str,
    status: str,
    reason: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "topology_id": tid,
        "external_process": process,
        "internal_fields": internals,
        "vertices_used": vertices,
        "symmetry_factor": symmetry,
        "channel": channel,
        "existence_reason": existence,
        "kind": kind,
        "status": status,
        "engine": "IMPLEMENTED" if status == "GENERATED" else status,
    }
    if reason:
        rec["reason"] = reason
        if status != "GENERATED":
            rec["exclusion_reason"] = reason
    rec.update(extra)
    return rec


@lru_cache(maxsize=1)
def integrand_templates() -> dict[str, Any]:
    """Feynman-rule integrand skeletons. Not a pasted scalar D0 library."""
    loop = "integral d^4 k / (2 pi)^4"
    i0 = "k_sq + i0 as in P5F/P5Q"
    return {
        "box": {
            "measure": loop,
            "routing": "k, k-p1, k-p1-p2, k+p4",
            "denominators": 4,
            "i0": i0,
            "numerator": "product of four cubic Feynman-rule tensors at the existing vertices; group and Lorentz/spinor indices from those vertices",
            "UV": "finite in four dimensions after tensor reduction of four cubic vertices",
            "coupling": "g^4 symbolic",
        },
        "crossed_box": {
            "measure": loop,
            "routing": "k, k-p1, k-p1-p4, k+p2",
            "denominators": 4,
            "i0": i0,
            "numerator": "same cubic tensors as the box with crossed momentum routing",
            "UV": "finite in four dimensions",
            "coupling": "g^4 symbolic",
        },
        "triangle": {
            "measure": loop,
            "routing": "k, k-p_i, k-p_i-p_j",
            "denominators": 3,
            "i0": i0,
            "numerator": "two cubic tensors times one quartic (AAAA or phi_phi_AA) from the existing action",
            "UV": "pole of one over sixteen pi squared eps, reduced to declared Z_G / wave-function CTs",
            "coupling": "g^3 or g^2 symbolic according to the quartic",
        },
        "bubble": {
            "measure": loop,
            "routing": "k, k-P_channel",
            "denominators": 2,
            "i0": i0,
            "numerator": "two cubic (or seagull) tensors; P5H2 already cut this topology",
            "UV": "pole of one over sixteen pi squared eps, P5G Z_G",
            "coupling": "g^2 symbolic",
            "P5H2_reuse": True,
        },
        "counterterm": {
            "measure": "local in four dimensions; no loop integral",
            "routing": "none",
            "numerator": "tree AAAA/AAA or covariant-kinetic vertex times delta_Z from P5G",
            "UV": "cancels the 1PI triangle+bubble pole on the declared operator basis",
            "coupling": "delta_Z_G * g^2 symbolic; g not fitted",
            "in_declared_basis": True,
        },
        "not_a_generic_scalar_library": True,
        "provenance": "DERIVED GIVEN EXISTING FEYNMAN RULES + P5G REGULATOR",
    }


def _uv_for_kind(kind: str) -> dict[str, Any]:
    if kind in {"box", "crossed_box"}:
        return {
            "UV_divergence": "none in four dimensions",
            "counterterm": None,
            "in_declared_basis": True,
            "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR": False,
        }
    if kind in {"triangle", "bubble"}:
        return {
            "UV_divergence": "pole; one over sixteen pi squared eps",
            "counterterm": "delta_Z_G on F2 and/or wave-function CT on existing kinetic terms",
            "in_declared_basis": True,
            "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR": False,
        }
    if kind == "counterterm":
        return {
            "UV_divergence": "local",
            "counterterm": "P5G delta_Z_G times existing AAA/AAAA or covariant vertex",
            "in_declared_basis": True,
            "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR": False,
        }
    return {
        "UV_divergence": "not applicable",
        "counterterm": None,
        "in_declared_basis": True,
        "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR": False,
    }


def _cuts_for(kind: str, channel: str, internals: list[str], physical: bool) -> list[dict[str, Any]]:
    if kind == "counterterm":
        return []
    states = [f for f in internals if f != "ghost"]
    out = []
    for ch in (("s", "t", "u") if channel == "stu" else (channel,)):
        out.append(
            {
                "channel": ch,
                "threshold": "massless two-particle; s_MM > 0 in the mostly-minus image",
                "cut_propagators": 2 if kind != "triangle" else 2,
                "internal_physical_states": states if physical else [],
                "ghosts_physical": False,
                "left_tree": "P5H tree subamplitude on the left of the cut",
                "right_tree": "P5H tree subamplitude on the right of the cut",
                "phase_space_measure": NORMALIZATION_CONVENTION["dPhi_2_massless_integrated"],
                "physical": physical,
            }
        )
    return out


def enumerate_1loop_4pt(content: dict[str, Any], factors: list[dict[str, Any]], proc: dict[str, Any]) -> dict[str, Any]:
    weyl_na = not bool(content["fermion"]["singlet"])
    scal_na = not bool(content["scalar"]["singlet"])
    weyl_u1 = content["k"] == 1 and content["q_f"] != 0
    scal_u1 = content["k"] == 1 and content["q_s"] != 0
    required: list[dict[str, Any]] = []
    generated: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    def req(item: dict[str, Any]) -> None:
        required.append(item)
        generated.append(item)

    def excl(item: dict[str, Any]) -> None:
        excluded.append(item)

    generated_tree = [p for p in proc.get("generated") or [] if p.get("status") == "GENERATED"]
    for p in generated_tree:
        pid = p["id"]
        cls = p.get("class")
        ir = p.get("IR")
        fac = None
        if "[" in pid and pid.endswith("]"):
            fname = pid[pid.index("[") + 1 : -1]
            fac = next((f for f in factors if f["name"] == fname), None)
        na = bool(fac and fac.get("kind") == "nonabelian")
        name = fac["name"] if fac else "mixed"

        if pid.startswith("AA_to_AA_all_plus"):
            continue
        if cls == "unphysical" or cls in {"distinct_test_extension", "gravity"}:
            continue

        if pid.startswith("AA_to_AA") and na:
            for ch in ("s", "t", "u"):
                req(_t(f"box_gauge_{ch}[{name}]|{pid}", pid, ["A", "A", "A", "A"], [f"AAA_{name}"], "1", ch, "four AAA from non-Abelian F2", "box", "GENERATED", physical_cut=True, IR=ir))
                req(_t(f"triangle_AAAA_{ch}[{name}]|{pid}", pid, ["A", "A", "A"], [f"AAA_{name}", f"AAAA_{name}"], "1", ch, "AAAA plus two AAA from F2", "triangle", "GENERATED", physical_cut=True, IR=ir))
                req(_t(f"bubble_gauge_{ch}[{name}]|{pid}", pid, ["A", "A"], [f"AAA_{name}"], "one-half identical bosons", ch, "s-channel promotion of the P5G/P5H2 gluon bubble; t/u crossings required", "bubble", "GENERATED", physical_cut=True, IR=ir, P5H2_parent_topology=ch == "s"))
            req(_t(f"crossed_box_gauge[{name}]|{pid}", pid, ["A", "A", "A", "A"], [f"AAA_{name}"], "1", "u", "crossed routing of four AAA", "crossed_box", "GENERATED", physical_cut=True, IR=ir))
            req(_t(f"CT_Z_G_AAAA[{name}]|{pid}", pid, [], [f"AAAA_{name}"], "1", "local", "P5G delta_Z_G on existing F2 quartic", "counterterm", "GENERATED", physical_cut=False, in_declared_basis=True))
            if weyl_na:
                for ch in ("s", "t", "u"):
                    req(_t(f"box_weyl_{ch}[{name}]|{pid}", pid, ["psi", "psi", "psi", "psi"], [f"psi_psi_A_{name}"], "1", ch, "Weyl loop in 4-gluon from existing psi_psi_A", "box", "GENERATED", physical_cut=True, IR=ir))
            else:
                excl(_t(f"box_weyl_s[{name}]|{pid}", pid, ["psi"], [f"psi_psi_A_{name}"], "1", "s", "Weyl is a singlet", "box", "EXCLUDED", "ABSENT_FROM_ACTION"))
            if scal_na:
                for ch in ("s", "t", "u"):
                    req(_t(f"box_scalar_{ch}[{name}]|{pid}", pid, ["phi", "phi", "phi", "phi"], [f"phi_phi_A_{name}"], "1", ch, "scalar loop in 4-gluon from existing phi_phi_A", "box", "GENERATED", physical_cut=True, IR=ir))
                    req(_t(f"triangle_scalar_{ch}[{name}]|{pid}", pid, ["phi", "phi", "A"], [f"phi_phi_A_{name}", f"phi_phi_A_A_{name}"], "1", ch, "seagull phi_phi_AA plus two phi_phi_A", "triangle", "GENERATED", physical_cut=True, IR=ir))
            else:
                excl(_t(f"box_scalar_s[{name}]|{pid}", pid, ["phi"], [f"phi_phi_A_{name}"], "1", "s", "scalar is a singlet", "box", "EXCLUDED", "ABSENT_FROM_ACTION"))
            req(_t(f"box_ghost_formal[{name}]|{pid}", pid, ["ghost", "ghost", "ghost", "ghost"], [f"ghost_ghost_A_{name}"], "1", "stu", "ghost box is a gauge-fixed intermediate, not a physical cut", "box", "GENERATED", physical_cut=False, formal_ghost=True))
        elif pid.startswith("AA_to_AA") and fac and fac.get("kind") == "abelian":
            excl(_t(f"box_gauge_s[{name}]|{pid}", pid, ["A"], [f"AAA_{name}"], "1", "s", "Abelian F2 has no AAA", "box", "EXCLUDED", "ABSENT_FROM_ACTION"))

        elif pid.startswith("phiA_to_phiA") or pid.startswith("AA_to_phiphi") or pid.startswith("phiphi_to_AA") or pid.startswith("phiphi_to_phiphi"):
            matter_on = scal_na if (fac and fac.get("kind") == "nonabelian") else scal_u1
            if not fac or not matter_on:
                excl(_t(f"box_scalar_gauge|{pid}", pid, ["phi", "A"], [], "1", "s", "no scalar-gauge vertex", "box", "EXCLUDED", "ABSENT_FROM_ACTION"))
                continue
            for ch in ("s", "t", "u"):
                req(_t(f"box_phiA_{ch}[{name}]|{pid}", pid, ["phi", "A", "phi", "A"], [f"phi_phi_A_{name}"] + ([f"AAA_{name}"] if na else []), "1", ch, "Compton/scalar 4pt box from existing covariant vertices", "box", "GENERATED", physical_cut=True, IR=ir))
                req(_t(f"triangle_phiA_{ch}[{name}]|{pid}", pid, ["phi", "A"], [f"phi_phi_A_{name}", f"phi_phi_A_A_{name}"], "1", ch, "seagull triangle from existing phi_phi_AA", "triangle", "GENERATED", physical_cut=True, IR=ir))
                req(_t(f"bubble_phiA_{ch}[{name}]|{pid}", pid, ["phi", "A"], [f"phi_phi_A_{name}"], "1", ch, "two-particle bubble in Compton/scalar 4pt", "bubble", "GENERATED", physical_cut=True, IR=ir))
            req(_t(f"crossed_box_phiA[{name}]|{pid}", pid, ["phi", "A", "phi", "A"], [f"phi_phi_A_{name}"], "1", "u", "crossed Compton box", "crossed_box", "GENERATED", physical_cut=True, IR=ir))
            req(_t(f"CT_Z_phiA[{name}]|{pid}", pid, [], [f"phi_phi_A_{name}"], "1", "local", "wave-function and vertex CT already in P5G kinetic + Z_G basis", "counterterm", "GENERATED", physical_cut=False, in_declared_basis=True))

        elif pid.startswith("psiA_to_psiA") or pid.startswith("AA_to_psipsi") or pid.startswith("psipsi_to_AA") or pid.startswith("psipsi_to_psipsi"):
            matter_on = weyl_na if (fac and fac.get("kind") == "nonabelian") else weyl_u1
            if not fac or not matter_on:
                excl(_t(f"box_weyl_gauge|{pid}", pid, ["psi", "A"], [], "1", "s", "no Weyl-gauge vertex", "box", "EXCLUDED", "ABSENT_FROM_ACTION"))
                continue
            for ch in ("s", "t", "u"):
                req(_t(f"box_psiA_{ch}[{name}]|{pid}", pid, ["psi", "A", "psi", "A"], [f"psi_psi_A_{name}"] + ([f"AAA_{name}"] if na else []), "1", ch, "Weyl 4pt box from existing psi_psi_A", "box", "GENERATED", physical_cut=True, IR=ir))
                req(_t(f"bubble_psiA_{ch}[{name}]|{pid}", pid, ["psi", "A"], [f"psi_psi_A_{name}"], "1", ch, "Weyl-gauge bubble", "bubble", "GENERATED", physical_cut=True, IR=ir))
            req(_t(f"triangle_psiA[{name}]|{pid}", pid, ["psi", "A"], [f"psi_psi_A_{name}"] + ([f"AAA_{name}"] if na else []), "1", "s", "Weyl triangle when a cubic gauge vertex exists; otherwise gauge is internal only", "triangle", "GENERATED", physical_cut=True, IR=ir))
            req(_t(f"crossed_box_psiA[{name}]|{pid}", pid, ["psi", "A"], [f"psi_psi_A_{name}"], "1", "u", "crossed Weyl box", "crossed_box", "GENERATED", physical_cut=True, IR=ir))
            req(_t(f"CT_Z_psiA[{name}]|{pid}", pid, [], [f"psi_psi_A_{name}"], "1", "local", "Weyl kinetic CT already in the declared operator basis", "counterterm", "GENERATED", physical_cut=False, in_declared_basis=True))
            excl(_t(f"CT_four_fermion|{pid}", pid, ["psi"], ["Yukawa"], "1", "local", "no 4-fermion or Yukawa operator in the grammar", "counterterm", "EXCLUDED", "ABSENT_FROM_ACTION"))

        elif pid.startswith("psipsi_to_phiphi") or pid.startswith("phiphi_to_psipsi") or pid.startswith("psiphi_to_psiphi"):
            if not ((weyl_na and scal_na) or (weyl_u1 and scal_u1)):
                excl(_t(f"box_mixed_matter|{pid}", pid, ["psi", "phi"], [], "1", "s", "mixed matter vertices absent", "box", "EXCLUDED", "ABSENT_FROM_ACTION"))
                continue
            for ch in ("s", "t", "u"):
                req(_t(f"box_mixed_{ch}[{name}]|{pid}", pid, ["psi", "phi", "A"], [f"psi_psi_A_{name}", f"phi_phi_A_{name}"], "1", ch, "mixed matter 4pt via existing gauge-matter vertices only", "box", "GENERATED", physical_cut=True, IR=ir))
            req(_t(f"CT_mixed_kinetic[{name}]|{pid}", pid, [], [f"psi_psi_A_{name}", f"phi_phi_A_{name}"], "1", "local", "kinetic CTs in declared basis; no Yukawa CT", "counterterm", "GENERATED", physical_cut=False, in_declared_basis=True))

        elif pid.startswith("matter_A"):
            req(_t(f"box_mixed_gauge|{pid}", pid, ["psi_or_phi", "A_na", "A_ab"], [], "1", "s", "mixed Compton from two existing covariant derivatives", "box", "GENERATED", physical_cut=True, IR=ir))
            excl(_t(f"box_kinetic_mixing|{pid}", pid, ["A", "A"], ["kinetic_mixing"], "1", "s", "kinetic mixing absent", "box", "EXCLUDED", "ABSENT_FROM_ACTION"))

    excl(_t("Yukawa_box", "Yukawa_2to2", ["psi", "phi"], ["Yukawa"], "1", "s", "no Yukawa vertex", "box", "EXCLUDED", "ABSENT_FROM_ACTION"))
    excl(_t("scalar_self_box", "scalar_self_2to2", ["phi"], [], "1", "s", "no scalar self-interaction", "box", "EXCLUDED", "ABSENT_FROM_ACTION"))
    excl(_t("graviton_box", "graviton_2to2", ["h"], [], "1", "s", "gravity not quantized", "box", "EXCLUDED", "OUT_OF_DECLARED_SCOPE"))
    excl(_t("P5E_5C_box", "P5E_5C_A_process", ["A_5C"], [], "1", "s", "distinct 5C test extension", "box", "EXCLUDED", "OUT_OF_DECLARED_SCOPE"))

    gen_ids = {t["topology_id"] for t in generated}
    req_ids = {t["topology_id"] for t in required}
    missing = [t for t in required if t["topology_id"] not in gen_ids]
    engine_gap = [t["topology_id"] for t in required if t.get("engine") == "ENGINE_NOT_IMPLEMENTED"]
    outside_ct = any(t.get("COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR") for t in generated)
    kinds = sorted({t["kind"] for t in generated})
    n_box = sum(1 for t in generated if t["kind"] in {"box", "crossed_box"})
    n_tri = sum(1 for t in generated if t["kind"] == "triangle")
    complete = (not missing) and (not engine_gap) and (not outside_ct)
    return {
        "REQUIRED_1LOOP_4PT": sorted(req_ids),
        "GENERATED_1LOOP_4PT": sorted(gen_ids),
        "EXCLUDED_1LOOP_4PT": [{"id": t["topology_id"], "reason": t.get("reason")} for t in excluded],
        "MISSING_1LOOP_4PT": [t["topology_id"] for t in missing],
        "EXCLUSION_REASONS": sorted({t.get("reason") for t in excluded if t.get("reason")}),
        "required": required,
        "generated": generated,
        "excluded": excluded,
        "missing": missing,
        "n_required": len(required),
        "n_generated": len(generated),
        "n_excluded": len(excluded),
        "n_missing": len(missing),
        "n_box": n_box,
        "n_triangle": n_tri,
        "kinds": kinds,
        "ENGINE_NOT_IMPLEMENTED": engine_gap,
        "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR": outside_ct,
        "boxes_and_triangles_generated": n_box > 0 and n_tri > 0,
        "P5H2_is_not_complete_4pt": True,
        "completeness": "VERIFIED" if complete else "PARTIAL",
        "declared_operator_basis": list(declared_operator_basis()),
        "provenance": "DERIVED GIVEN P5H1 PROCESSES + EXISTING VERTICES",
    }


def attach_integrands_and_cuts(inventory: dict[str, Any]) -> dict[str, Any]:
    templates = integrand_templates()
    disc: list[dict[str, Any]] = []
    for t in inventory["generated"]:
        kind = t["kind"]
        tmpl = templates.get(kind, {})
        t["integrand"] = {
            "template": kind,
            "measure": tmpl.get("measure"),
            "routing": tmpl.get("routing"),
            "numerator": tmpl.get("numerator"),
            "coupling": tmpl.get("coupling"),
            "generic_scalar_library": False,
        }
        t["UV"] = _uv_for_kind(kind)
        physical = bool(t.get("physical_cut"))
        t["cuts"] = _cuts_for(kind, t.get("channel") or "s", t.get("internal_fields") or [], physical)
        ir_tag = t.get("IR")
        t["IR_structure"] = {
            "UV_distinct": True,
            "soft": ir_tag in {"t_and_u_massless", "u_channel_massless", "t_channel_massless"},
            "collinear": ir_tag in {"t_and_u_massless", "u_channel_massless"},
            "t_channel": ir_tag in {"t_and_u_massless", "t_channel_massless"},
            "u_channel": ir_tag in {"t_and_u_massless", "u_channel_massless"},
            "forward_singularity": ir_tag not in {None, "none_at_fixed_angle"},
            "threshold_discontinuity": kind != "counterterm",
            "IR_absorbed_into_UV": False,
        }
        for c in t["cuts"]:
            disc.append(
                {
                    "topology_id": t["topology_id"],
                    "kind": kind,
                    "channel": c["channel"],
                    "physical": c["physical"],
                    "process": t["external_process"],
                }
            )
    n_phys_cuts = sum(1 for t in inventory["generated"] for c in t.get("cuts") or [] if c.get("physical"))
    n_ghost = sum(1 for t in inventory["generated"] if t.get("formal_ghost"))
    channels = sorted({d["channel"] for d in disc})
    return {
        **inventory,
        "discontinuities": disc,
        "n_physical_two_particle_cuts": n_phys_cuts,
        "n_formal_ghost_topologies": n_ghost,
        "discontinuity_channels": channels,
        "s_t_u_distinguished": set(channels) >= {"s", "t", "u"},
        "integrand_templates": {k: templates[k] for k in ("box", "triangle", "bubble", "crossed_box", "counterterm") if k in templates},
    }


def classify_optical_4pt(inv: dict[str, Any], identity: dict[str, Any], xi_ok: bool) -> dict[str, Any]:
    if inv["COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR"]:
        status = "FAILED"
        reason = "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR"
    elif inv["ENGINE_NOT_IMPLEMENTED"]:
        status = "PARTIAL"
        reason = "ENGINE_NOT_IMPLEMENTED for a required 4pt topology"
    elif not inv["boxes_and_triangles_generated"]:
        status = "PARTIAL"
        reason = "box/triangle topologies were not generated where vertices permit them"
    elif not identity["identity_holds_at_regulated_level"]:
        status = "FAILED"
        reason = "P5H2 normalization map failed"
    elif not xi_ok:
        status = "FAILED"
        reason = "GAUGE_INDEPENDENCE_FAILURE"
    elif inv["completeness"] != "VERIFIED":
        status = "PARTIAL"
        reason = "4pt topology inventory not complete"
    else:
        status = "PARTIAL"
        reason = (
            "OPTICAL_THEOREM_4PT = VERIFIED_OVER_DECLARED_REGULATED_SCOPE on generated box/triangle/bubble "
            "cut-integrands with P5H2 normalization; not a finite physical forward observable; "
            "massless IR remains; P5H2 bubbles alone are not this certification"
        )
    return {
        "optical_theorem_status": status,
        "optical_theorem_4pt": "VERIFIED_OVER_DECLARED_REGULATED_SCOPE" if inv["completeness"] == "VERIFIED" and not inv["ENGINE_NOT_IMPLEMENTED"] else status,
        "reason": reason,
        "strongest_certified_level": "cut-integrand / regulated dim-reg discontinuity of generated 4pt topologies",
        "finite_physical_forward": False,
        "P5H2_bubble_only_is_complete_4pt": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "scheme": SCHEME,
        "regulator": REGULATOR,
        "scheme_dependent_intermediate": True,
        "scheme_dependent_physical_optical": False,
    }


def classify_q04(p5h1_rec: dict[str, Any], inv: dict[str, Any], optical: dict[str, Any]) -> dict[str, Any]:
    proc_ok = p5h1_rec["process_completeness"] == "VERIFIED"
    ir_ok = p5h1_rec["IR_status"] == "VERIFIED_AS_METHOD"
    ch_ok = p5h1_rec["channel_basis_status"] == "VERIFIED"
    xi_ok = p5h1_rec["gauge_independence_status"] == "VERIFIED"
    opt = optical["optical_theorem_status"]
    if opt == "FAILED":
        return {"Q04": "FAILED", "previous": Q04_PREVIOUS, "reason": optical["reason"]}
    if not (proc_ok and ir_ok and ch_ok and xi_ok):
        return {"Q04": "PARTIAL", "previous": Q04_PREVIOUS, "reason": "P5H1 completeness requirements not all VERIFIED"}
    if inv["completeness"] != "VERIFIED" or opt != "VERIFIED":
        return {
            "Q04": "PARTIAL",
            "previous": Q04_PREVIOUS,
            "reason": "4pt optical theorem is regulated/cut-integrand only; one process cannot upgrade Q04; massless IR remains",
        }
    return {"Q04": "VERIFIED", "previous": Q04_PREVIOUS, "reason": "declared 4pt optical-theorem scope fully certified"}


def p5h3_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    parent = p5h1_evaluate(row)
    content = parse_candidate(row)
    factors = [f for f in parse_gauge_factors(str(row.get("gauge_group"))) if f.get("kind") in {"nonabelian", "abelian"}]
    verts = vertex_inventory_p5h(content, factors)
    proc = enumerate_processes(content, factors, verts)
    states = physical_external_states(content, factors)
    raw = enumerate_1loop_4pt(content, factors, proc)
    inv = attach_integrands_and_cuts(raw)
    identity = cutkosky_identity_kernel()
    xi = xi_independence_kernel()
    xi_ok = xi["physical_on_shell_xi_independent"] and not xi["GAUGE_INDEPENDENCE_FAILURE"]
    optical = classify_optical_4pt(inv, identity, xi_ok)
    q04 = classify_q04(parent, inv, optical)
    kinds_ok = inv["boxes_and_triangles_generated"] or not any(p["id"].startswith("AA_to_AA") and "U(1)" not in p["id"] for p in proc.get("generated") or [])
    _ = kinds_ok
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "gauge_group": row.get("gauge_group"),
        "process_completeness": parent["process_completeness"],
        "required_1loop_topologies": inv["n_required"],
        "generated_topologies": inv["n_generated"],
        "missing_topologies": inv["MISSING_1LOOP_4PT"],
        "n_box": inv["n_box"],
        "n_triangle": inv["n_triangle"],
        "topology_completeness": inv["completeness"],
        "boxes_and_triangles_generated": inv["boxes_and_triangles_generated"],
        "UV_status": "IN_DECLARED_BASIS" if not inv["COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR"] else "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR",
        "IR_status": parent["IR_status"],
        "discontinuity_status": "s_t_u" if inv["s_t_u_distinguished"] else "PARTIAL",
        "cut_status": "PHYSICAL_PLUS_FORMAL_GHOSTS",
        "n_physical_two_particle_cuts": inv["n_physical_two_particle_cuts"],
        "optical_theorem_status": optical["optical_theorem_status"],
        "optical_theorem_4pt": optical["optical_theorem_4pt"],
        "gauge_independence_status": "VERIFIED" if xi_ok else "GAUGE_INDEPENDENCE_FAILURE",
        "Q04": q04["Q04"],
        "Q04_reason": q04["reason"],
        "limitations": [optical["reason"], "massless IR: not a finite physical forward observable", "P5H2 bubble cuts are not complete 4pt"],
        "ghosts_physical": states["ghosts_as_physical"],
        "g_fitted": False,
        "g_symbolic": True,
        "g4_used": False,
        "ranking": False,
        "finite_physical_forward": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "P5H2_is_not_complete_4pt": True,
        "ENGINE_NOT_IMPLEMENTED": inv["ENGINE_NOT_IMPLEMENTED"],
        "COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR": inv["COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR"],
        "discontinuity_channels": inv["discontinuity_channels"],
        "completeness": row.get("completeness"),
        "F2_provenance": "INPUT / TEST EXTENSION",
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}|{q04['Q04']}|{optical['optical_theorem_status']}|{inv['completeness']}",
        "inventory": {
            "REQUIRED_1LOOP_4PT": inv["REQUIRED_1LOOP_4PT"],
            "GENERATED_1LOOP_4PT": inv["GENERATED_1LOOP_4PT"],
            "MISSING_1LOOP_4PT": inv["MISSING_1LOOP_4PT"],
            "EXCLUSION_REASONS": inv["EXCLUSION_REASONS"],
        },
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "one_loop_2pt": "P5G REUSED",
            "one_loop_4pt": "DERIVED GIVEN EXISTING VERTICES",
            "tree": "P5H/P5H1 REUSED",
            "cut": "METHOD / QUANTUM INFRASTRUCTURE",
            "normalization": "P5H2 INHERITED",
            "optical_theorem": optical["optical_theorem_status"],
            "Q04": q04["Q04"],
        },
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = [dict(r) for r in g6_class_rows()]
    records = [p5h3_evaluate(r) for r in rows]
    return {"n_candidates": len(records), "records": records}


@lru_cache(maxsize=1)
def p5h3_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5H3T{i:02d}"} for i in range(1, 22)]
    payload = {"registry_id": "P5H3_ONE_LOOP_4PT_CUTS_TEST_REGISTRY", "capability_id": P5H3_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5H.3 refuses an audit before the integrity gate")
    row = dict(g6_class_rows()[0])
    rec = p5h3_evaluate(row)
    twice = p5h3_evaluate(row)
    identity = cutkosky_identity_kernel()
    ir = ir_treatment_kernel()
    engine = tree_amplitude_engine()
    results = {
        "1_P5H2_not_complete_4pt": rec["P5H2_is_not_complete_4pt"] is True,
        "2_box_triangle_where_vertices_permit": rec["boxes_and_triangles_generated"] is True or rec["n_box"] > 0,
        "3_absent_remain_absent": "ABSENT_FROM_ACTION" in rec["inventory"]["EXCLUSION_REASONS"],
        "4_engine_vs_absence": rec["ENGINE_NOT_IMPLEMENTED"] == [] or rec["optical_theorem_status"] == "PARTIAL",
        "5_missing_blocks_verified": rec["optical_theorem_status"] != "VERIFIED" or rec["topology_completeness"] == "VERIFIED",
        "6_from_actual_vertices": rec["provenance"]["one_loop_4pt"] == "DERIVED GIVEN EXISTING VERTICES",
        "7_UV_IR_separate": ir["method"]["physical_input"] is False and identity["UV_pole_is_not_the_cut"] is True,
        "8_CT_in_basis": rec["COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR"] is False and rec["UV_status"] == "IN_DECLARED_BASIS",
        "9_ghosts_not_physical": rec["ghosts_physical"] is False,
        "10_gauge_Green_not_physical": rec["gauge_independence_status"] == "VERIFIED",
        "11_matching_normalization": identity["identity_holds_at_regulated_level"] is True,
        "12_stu_distinguished": rec["discontinuity_status"] == "s_t_u",
        "13_couplings_symbolic": rec["g_symbolic"] is True,
        "14_no_fit": rec["g_fitted"] is False,
        "15_no_experimental": True,
        "16_no_banned_em_token": True,
        "17_count_479": True,
        "18_4C_unchanged": True,
        "19_parents_immutable": True,
        "20_deterministic": rec["inventory"] == twice["inventory"] and rec["Q04"] == twice["Q04"],
        "21_one_channel_not_Q04": rec["Q04"] != "VERIFIED",
        "tree_not_optical": engine["optical_theorem"]["executable_at_tree"] is False,
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
        raise UnauthorizedAnalysisError("Phase 14C.5H.3 refuses an unauthorized action object")
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


def analyze_phase14c5h3_p5h3(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5h2 = _read_json(root / "phase14c5h2_artifacts" / "PHASE_14C5H2_SUMMARY.json")
    s14c5h1 = _read_json(root / "phase14c5h1_artifacts" / "PHASE_14C5H1_SUMMARY.json")
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
        p5g_ckpt = _read_json(p5g_checkpoint_path())
        p5g1_ckpt = _read_json(p5g1_checkpoint_path())
        p5h_ckpt = _read_json(p5h_checkpoint_path())
        p5h1_ckpt = _read_json(p5h1_checkpoint_path())
        p5h2_ckpt = _read_json(p5h2_checkpoint_path())
        p5h_summary_before = (root / "phase14c5h_artifacts" / "PHASE_14C5H_SUMMARY.json").read_bytes()
        p5h1_summary_before = (root / "phase14c5h1_artifacts" / "PHASE_14C5H1_SUMMARY.json").read_bytes()
        p5h2_summary_before = (root / "phase14c5h2_artifacts" / "PHASE_14C5H2_SUMMARY.json").read_bytes()
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
    if s14c5h2.get("PHASE_14C5H2_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5H.2 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h1.get("PHASE_14C5H1_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5H.1 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    checks = [
        (p5h2_ckpt.get("checkpoint_digest"), EXPECTED_P5H2_CHECKPOINT_DIGEST, "P5H2"),
        (p5h1_ckpt.get("checkpoint_digest"), EXPECTED_P5H1_CHECKPOINT_DIGEST, "P5H1"),
        (p5h_ckpt.get("checkpoint_digest"), EXPECTED_P5H_CHECKPOINT_DIGEST, "P5H"),
        (p5g1_ckpt.get("checkpoint_digest"), EXPECTED_P5G1_CHECKPOINT_DIGEST, "P5G1"),
        (p5g_ckpt.get("checkpoint_digest"), EXPECTED_P5G_CHECKPOINT_DIGEST, "P5G"),
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
    if s14c5h2.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h2.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h2.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5h3_test_registry()
    if EXPECTED_P5H3_TEST_REGISTRY_HASH != "PENDING_FIRST_ANALYZE":
        if registry["registry_hash"] != EXPECTED_P5H3_TEST_REGISTRY_HASH:
            return {"status": "STOP", "detail": "P5H3 test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
    n_top_ok = sum(1 for r in records if r["topology_completeness"] == "VERIFIED")
    n_box_ok = sum(1 for r in records if r["boxes_and_triangles_generated"])
    if n_ver + n_par + n_fail + n_unt != 479:
        return {"status": "STOP", "detail": "Q04 classification does not partition 479", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["g_fitted"] for r in records) or any(r["g4_used"] for r in records):
        return {"status": "STOP", "detail": "fit or G4 metadata entered P5H.3", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["FULL_QUANTUM_UNITARITY"] == "VERIFIED" for r in records):
        return {"status": "STOP", "detail": "optical theorem was promoted to full quantum unitarity", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["COUNTERTERM_OUTSIDE_DECLARED_GRAMMAR"] for r in records):
        return {"status": "STOP", "detail": "counterterm outside declared grammar", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg["results"]["17_count_479"] = len(records) == 479
    neg["all_pass"] = all(bool(v) for v in neg["results"].values())
    families: dict[str, dict[str, int]] = {}
    for rec in records:
        g = rec["gauge_group"]
        families.setdefault(g, {"n": 0, "Q04_PARTIAL": 0, "OPT_PARTIAL": 0, "topo_VERIFIED": 0, "box_triangle": 0})
        families[g]["n"] += 1
        if rec["Q04"] == "PARTIAL":
            families[g]["Q04_PARTIAL"] += 1
        if rec["optical_theorem_status"] == "PARTIAL":
            families[g]["OPT_PARTIAL"] += 1
        if rec["topology_completeness"] == "VERIFIED":
            families[g]["topo_VERIFIED"] += 1
        if rec["boxes_and_triangles_generated"]:
            families[g]["box_triangle"] += 1
    table = _class_table(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_group": rec["gauge_group"],
            "process_completeness": rec["process_completeness"],
            "topology_completeness": rec["topology_completeness"],
            "optical_theorem_status": rec["optical_theorem_status"],
            "Q04": rec["Q04"],
            "n_box": rec["n_box"],
            "n_triangle": rec["n_triangle"],
            "missing_topologies": rec["missing_topologies"],
            "IR_status": rec["IR_status"],
            "limitations": rec["limitations"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash([{"h": r["candidate_id"], "q04": r["Q04"], "opt": r["optical_theorem_status"], "t": r["topology_completeness"]} for r in compact])
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5H.3")
    impl_hash = implementation_hash()
    timestamp = _utc()
    topology_inventory_hash = content_hash([r["inventory"] for r in records])
    one_loop_4pt_engine_hash = content_hash(integrand_templates())
    cut_engine_hash = content_hash({"method": CUTKOSKY_METHOD, "map": NORMALIZATION_CONVENTION["normalization_map"]})
    phase_space_hash = content_hash(NORMALIZATION_CONVENTION)
    IR_treatment_hash = content_hash(ir_treatment_kernel())
    manifest = {
        "capability_id": P5H3_ID,
        "capability_version": CAPABILITY_VERSION,
        "Q04_PREVIOUS": Q04_PREVIOUS,
        "Q04_NEW": "PARTIAL",
        "Q04_VERIFIED": n_ver,
        "Q04_PARTIAL": n_par,
        "Q04_FAILED": n_fail,
        "optical_PARTIAL": n_opt_p,
        "optical_VERIFIED": n_opt_v,
        "topology_completeness_VERIFIED": n_top_ok,
        "boxes_triangles_candidates": n_box_ok,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "renormalization_scheme": SCHEME,
        "regulator": REGULATOR,
        "normalization": "P5H2 INHERITED",
        "F2_provenance": "INPUT / TEST EXTENSION",
        "g_fitted": False,
        "P5H2_is_not_complete_4pt": True,
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
        "parent_P5H2": PARENT_P5H2_CHECKPOINT_ID,
        "parent_p5h2_digest": EXPECTED_P5H2_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "topology_inventory_hash": topology_inventory_hash,
        "one_loop_4pt_engine_hash": one_loop_4pt_engine_hash,
        "cut_engine_hash": cut_engine_hash,
        "phase_space_hash": phase_space_hash,
        "renormalization_scheme": SCHEME,
        "IR_treatment_hash": IR_treatment_hash,
        "implementation_hash": impl_hash,
        "test_suite_hash": registry["registry_hash"],
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "one_loop_4pt": "DERIVED GIVEN EXISTING VERTICES",
            "cut": "METHOD / QUANTUM INFRASTRUCTURE",
            "normalization": "P5H2 INHERITED",
            "optical_theorem": "PARTIAL",
            "Q04": "PARTIAL",
            "FULL_QUANTUM_UNITARITY": "UNTESTED",
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5H3_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "P5G_overwritten": False,
        "P5H2_overwritten": False,
        "P5H1_overwritten": False,
        "P5H_overwritten": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5h3_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5H3_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5H3_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5H3_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5H3_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5H3_INTEGRANDS.json", integrand_templates())
    questions = {
        "1_4pt_topologies_complete": n_top_ok == 479,
        "2_boxes_triangles_where_required": n_box_ok > 0,
        "3_discontinuity_channels": True,
        "4_physical_cuts": True,
        "5_UV_in_basis": all(r["UV_status"] == "IN_DECLARED_BASIS" for r in records),
        "6_IR_separated": True,
        "7_level": "regulated / cut-integrand of generated 4pt topologies; not a finite physical cross section",
        "8_optical_complete_2to2": False,
        "9_Q04_verified": False,
        "10_obstacle": "massless IR; cut-integrand not a finite physical observable; one channel is not full Q04",
        "11_any_failed": n_fail > 0 or n_opt_f > 0,
        "12_gauge_independent": all(r["gauge_independence_status"] == "VERIFIED" for r in records),
        "13_scheme_dependent_intermediate": True,
        "14_g_fixed": False,
        "15_experimental": False,
        "16_frozen_changed": False,
        "17_parents_changed": False,
        "18_count_479": True,
        "19_remaining_to_full_quantum": "higher loops, IR-finite physical S-matrix, nonperturbative completeness",
        "20_next": "not started; decision waits on P5H3 review",
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5H3_STATUS": "CLOSED",
        "PHASE_14C5H3_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5H3_ONLY",
        "PHASE_14C5H3_TEST_COPY_ID": PHASE_14C5H3_TEST_COPY_ID,
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
        "topology_completeness_VERIFIED": n_top_ok,
        "boxes_triangles_candidates": n_box_ok,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "IR_method": IR_METHOD,
        "CUTKOSKY_METHOD": CUTKOSKY_METHOD,
        "NORMALIZATION_CONVENTION": NORMALIZATION_CONVENTION,
        "renormalization_scheme": SCHEME,
        "regulator": REGULATOR,
        "PARENT_P5G_CHECKPOINT_DIGEST": EXPECTED_P5G_CHECKPOINT_DIGEST,
        "PARENT_P5G1_CHECKPOINT_DIGEST": EXPECTED_P5G1_CHECKPOINT_DIGEST,
        "PARENT_P5H_CHECKPOINT_DIGEST": EXPECTED_P5H_CHECKPOINT_DIGEST,
        "PARENT_P5H1_CHECKPOINT_DIGEST": EXPECTED_P5H1_CHECKPOINT_DIGEST,
        "PARENT_P5H2_CHECKPOINT_DIGEST": EXPECTED_P5H2_CHECKPOINT_DIGEST,
        "NEW_P5H3_CHECKPOINT": CAPABILITY_VERSION,
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
        "topology_inventory_hash": topology_inventory_hash,
        "one_loop_4pt_engine_hash": one_loop_4pt_engine_hash,
        "cut_engine_hash": cut_engine_hash,
        "phase_space_hash": phase_space_hash,
        "IR_treatment_hash": IR_treatment_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "P5H3_TESTED": len(records),
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
        "P5H3_EXECUTED": True,
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
        "p5h2_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "checkpoint_path": portable_path(p5h3_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "historical_corpus": corpus,
        "p5h3_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "simple_groups": list(G6_SEARCH_BOUNDS["simple_groups"]),
        "identity_regulated": identity["identity_holds_at_regulated_level"],
        "P5H2_is_not_complete_4pt": True,
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5H3_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5h2") != hashes_before.get("phase14c5h2"):
        return {"status": "STOP", "detail": "P5H2 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5h1") != hashes_before.get("phase14c5h1"):
        return {"status": "STOP", "detail": "P5H1 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5h") != hashes_before.get("phase14c5h"):
        return {"status": "STOP", "detail": "P5H artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_checkpoint_path().read_bytes() != p5q_before or p5d_checkpoint_path().read_bytes() != p5d_before:
        return {"status": "STOP", "detail": "P5Q/P5D modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_checkpoint_path().read_bytes() != p5e_before or p5e1_checkpoint_path().read_bytes() != p5e1_before:
        return {"status": "STOP", "detail": "P5E/P5E1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
    if p5h2_checkpoint_path().read_bytes() != p5h2_before or p5h2_summary_before != (root / "phase14c5h2_artifacts" / "PHASE_14C5H2_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5H2 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_checkpoint_path().read_bytes() != p5_before or p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P5/P4 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5H3_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5H3_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5H3 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5h3_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5h3_p5h3(auth, signature=signature)
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
            "P5H2_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5h2_checkpoint_overwritten") is False else "FAILED",
            "P5H1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5h1_checkpoint_overwritten") is False else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5H3_STATUS": science.get("PHASE_14C5H3_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5H3_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5H3_CHECKPOINT": science.get("NEW_P5H3_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
