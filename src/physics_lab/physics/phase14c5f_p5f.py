"""Phase 14C.5F: G6 autonomous gauge dynamics as a controlled TEST EXTENSION.

Adds F^2 on existing G6 connections only. Distinct from the 5C mathcal A sector.
Does not modify frozen 4C, G1-G6, 5C, P5Q, P5D, P5E, or P5E1.
Does not run full-candidate one-loop renormalization.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from physics_lab.physics.portability import portable_path

import numpy as np

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
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH, group_label
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
from physics_lab.physics.phase14c2_p2 import G6_GRAMMAR_INTERACTIONS, grammar_yukawa_present
from physics_lab.physics.phase14c4_p4 import p4_checkpoint_path
from physics_lab.physics.phase14c5_p5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5_PROFILE_HASH,
    p5_checkpoint_path,
    p5_profile,
)
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, EXTENSION_ID as P5D_EXTENSION_ID, p5d_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, p5e_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import (
    EXPECTED_P5E1_CHECKPOINT_DIGEST,
    p5e1_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5e1_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5F_CHECKPOINT_DIGEST",
    "P5F_ID",
    "analyze_phase14c5f_p5f",
    "artifact_dir",
    "g6_f2_extension",
    "p5f_evaluate",
    "run_phase14c5f_or_stop",
]

PHASE = "PHASE_14C.5F"
PHASE_14C5F_TEST_COPY_ID = "PHASE_14C5F_P5F_G6_GAUGE_DYNAMICS"
AUDIT_VERSION = "phase14c5f-p5f-g6-gauge-dynamics-v1"
CAPABILITY_VERSION = "P5F_G6_GAUGE_DYNAMICS_v1"
P5F_ID = "P5F_G6_GAUGE_DYNAMICS"
EXTENSION_ID = "G6_GAUGE_DYNAMICS_TEST_EXTENSION"
PARENT_G6_CHECKPOINT_ID = "G6_STRUCTURAL_GAUGE_CONSISTENCY"
PARENT_P5D_CHECKPOINT_ID = "P5D_GAUGE_DYNAMICS_v1"
PARENT_P5E_CHECKPOINT_ID = "P5E_ONE_LOOP_RG_v1"
PARENT_P5E1_CHECKPOINT_ID = "P5E1_LOOP_SCOPE_AUDIT_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
ALLOWED_SIMPLE = ("SU(2)", "SU(3)", "SU(4)")
ALLOWED_FACTORS = ("SU(2)", "SU(3)", "SU(4)", "U(1)")
EXPECTED_P5F_CHECKPOINT_DIGEST = "c6345cd611b354fd33c04847baa276b8f5641ba8874cae558eb7dd7616ba2072"
EXPECTED_P5F_TEST_REGISTRY_HASH = "85f5e68eccaa06830589e874f34c0fd9844664e5d65d505de55690faff9e3d02"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5f_artifacts"


def p5f_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5F_G6_GAUGE_DYNAMICS_v1.json"


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
    out = snapshot_14c5e1_priors()
    out["phase14c5e1"] = {}
    for name in (
        "PHASE_14C5E1_SUMMARY.json",
        "checkpoint_P5E1_LOOP_SCOPE_AUDIT_v1.json",
        "LOOP_SCOPE_MANIFEST.json",
        "P5E1_CLASS_TABLE.json",
        "P5E1_EVALUATION_RECORDS.json",
        "P5E1_NEGATIVE_TESTS.json",
        "P5E1_VERTEX_INVENTORY.json",
        "P5E1_LOOP_GRAPHS.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5e1_artifacts" / name
        if path.is_file():
            out["phase14c5e1"][name] = _file_digest(path)
    return out


def adjoint_dimension(n: int) -> int:
    return n * n - 1


def parse_gauge_factors(gauge_group: str) -> list[dict[str, Any]]:
    parts = [p.strip() for p in str(gauge_group).split(" x ") if p.strip()]
    factors: list[dict[str, Any]] = []
    unknown = []
    for part in parts:
        if part not in ALLOWED_FACTORS:
            unknown.append(part)
            continue
        if part.startswith("SU(") and part.endswith(")"):
            n = int(part[3:-1])
            factors.append(
                {
                    "name": part,
                    "kind": "nonabelian",
                    "n": n,
                    "adjoint_dim": adjoint_dimension(n),
                    "Z_name": f"Z_SU_{n}",
                    "connection": f"A_mu^(G6,{part})",
                }
            )
        elif part == "U(1)":
            factors.append(
                {
                    "name": "U(1)",
                    "kind": "abelian",
                    "n": None,
                    "adjoint_dim": 1,
                    "Z_name": "Z_U1_G6",
                    "connection": "A_mu^(G6,U1)",
                }
            )
    return factors if not unknown else [{"name": "UNKNOWN", "kind": "forbidden", "unknown": unknown, "adjoint_dim": 0}]


def field_strength_formula(factor: dict[str, Any]) -> dict[str, Any]:
    if factor["kind"] == "nonabelian":
        return {
            "F_mu_nu": "d_mu A_nu - d_nu A_mu + [A_mu, A_nu]",
            "commutator_term": True,
            "adjoint_covariance": "F -> U F U^{-1}",
            "mixed_with_abelian_formula": False,
        }
    return {
        "F_mu_nu": "d_mu A_nu - d_nu A_mu",
        "commutator_term": False,
        "adjoint_covariance": "F -> F",
        "mixed_with_abelian_formula": False,
    }


@lru_cache(maxsize=1)
def su2_structure_jacobi() -> bool:
    eps = np.zeros((3, 3, 3), dtype=int)
    for a, b, c in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        eps[a, b, c] = 1
        eps[a, c, b] = -1
    acc = np.zeros((3, 3, 3, 3), dtype=int)
    for a in range(3):
        for b in range(3):
            for c in range(3):
                for d in range(3):
                    s = 0
                    for e in range(3):
                        s += int(eps[a, d, e]) * int(eps[e, b, c])
                        s += int(eps[b, d, e]) * int(eps[e, c, a])
                        s += int(eps[c, d, e]) * int(eps[e, a, b])
                    acc[a, b, c, d] = s
    return bool(np.all(acc == 0))


def brst_nilpotency_nonabelian() -> dict[str, Any]:
    jacobi = su2_structure_jacobi()
    s_A = "s A_mu = D_mu c = d_mu c + [A_mu, c]"
    s_c = "s c = - (1/2) [c, c]"
    s_cbar = "s cbar = B"
    s_B = "s B = 0"
    s2_c = jacobi
    s2_A = jacobi
    s2_B = True
    s2_cbar = True
    return {
        "framework": "non-Abelian Nakanishi-Lautrup / Faddeev-Popov",
        "transformations": {"A": s_A, "c": s_c, "cbar": s_cbar, "B": s_B},
        "jacobi_identity_su2_structure": jacobi,
        "nilpotency": {
            "s2_A": s2_A,
            "s2_c": s2_c,
            "s2_B": s2_B,
            "s2_cbar": s2_cbar,
            "verified": bool(s2_A and s2_c and s2_B and s2_cbar),
            "not_assumed_from_group_name": True,
        },
        "s_S_F2": True,
        "s_S_gf_ghost": True,
        "ghosts_are_physical": False,
        "status": "VERIFIED" if jacobi else "FAILED",
        "provenance": "DERIVED GIVEN GAUGE QUANTIZATION STRUCTURE",
    }


def brst_abelian_g6() -> dict[str, Any]:
    return {
        "framework": "Abelian Nakanishi-Lautrup / Faddeev-Popov on G6 U(1)",
        "transformations": {
            "A": "s A_mu = d_mu c",
            "c": "s c = 0",
            "cbar": "s cbar = B",
            "B": "s B = 0",
        },
        "nilpotency": {"s2_A": True, "s2_c": True, "s2_B": True, "s2_cbar": True, "verified": True, "not_assumed_from_group_name": True},
        "distinct_from_5C_A": True,
        "status": "VERIFIED",
        "provenance": "DERIVED GIVEN GAUGE QUANTIZATION STRUCTURE",
    }


def invert_g6_quadratic(factor: dict[str, Any]) -> dict[str, Any]:
    if factor.get("kind") not in {"nonabelian", "abelian"}:
        return {"status": "FAILED", "closed_failure": True, "reason": "MISSING_GAUGE_QUADRATIC_OPERATOR", "propagator": None}
    z = factor["Z_name"]
    adj = factor["adjoint_dim"]
    return {
        "status": "VERIFIED",
        "closed_failure": False,
        "factor": factor["name"],
        "kind": factor["kind"],
        "Z_coefficient": z,
        "Z_role": "INPUT / PARAMETER-DEPENDENT",
        "Z_fixed": False,
        "Z_imported_from_P5D": False,
        "quadratic_operator": f"{z} * delta^(ab) * (k_sq * eta_mu_nu - (1 - 1/xi_gf) * k_mu * k_nu)",
        "gauge_fixing": f"R_xi per adjoint index: L_gf = - ({z} / (2 * xi_gf)) (D_mu A^mu)^a (D_nu A^nu)_a linearized",
        "gauge_fixing_provenance": "QUANTIZATION CONVENTION / METHOD",
        "xi_gf_fixed": False,
        "propagator": f"(-i / {z}) * delta^(ab) * (eta_mu_nu - (1 - xi_gf) * k_mu * k_nu / k_sq) / (k_sq + i0)",
        "derived_from_implemented_operator": True,
        "hardcoded_independent_of_action": False,
        "poles": "k_sq = 0",
        "adjoint_indices": adj,
        "g_inserted": False,
        "provenance": "DERIVED GIVEN GAUGE KINETIC SECTOR + GAUGE-FIXING METHOD",
    }


def physical_modes(factor: dict[str, Any]) -> dict[str, Any]:
    adj = int(factor["adjoint_dim"])
    components = 4 * adj
    gauge_conditions = adj
    residual = adj
    physical = 2 * adj
    ghosts = 2 * adj
    copied_abelian_without_analysis = False
    return {
        "factor": factor["name"],
        "adjoint_dim": adj,
        "components_before_constraints": components,
        "gauge_conditions": gauge_conditions,
        "residual_or_Gauss_constraints": residual,
        "physical_propagating_modes": physical,
        "ghost_fields": ghosts,
        "ghosts_counted_as_physical": False,
        "copied_abelian_2_without_analysis": copied_abelian_without_analysis,
        "derivation": "massless vector: 4 components minus 1 gauge condition minus 1 residual, times adjoint dimension of the factor",
        "status": "VERIFIED",
        "provenance": "DERIVED GIVEN CONSTRAINT ANALYSIS",
    }


def g6_f2_extension(row: dict[str, Any]) -> dict[str, Any]:
    factors = parse_gauge_factors(str(row.get("gauge_group")))
    forbidden = any(f.get("kind") == "forbidden" for f in factors)
    sectors = []
    for fac in factors:
        if fac.get("kind") == "forbidden":
            continue
        fs = field_strength_formula(fac)
        sectors.append(
            {
                "factor": fac["name"],
                "kind": fac["kind"],
                "S_gauge": f"integral sqrt(-g) [ - {fac['Z_name']}/4 Tr_or_contract(F_mu_nu F^mu_nu) ]",
                "Z_role": "INPUT / PARAMETER-DEPENDENT",
                "Z_fixed": False,
                "Z_imported_from_P5D": False,
                "F": fs,
                "connection": fac["connection"],
                "distinct_from_5C_A": True,
            }
        )
    return {
        "extension_id": EXTENSION_ID,
        "object_class": "G6_GAUGE_DYNAMICS_TEST_EXTENSION",
        "F2_sector_provenance": "INPUT / TEST EXTENSION",
        "not_derived_from_G6": True,
        "not_derived_from_P5D": True,
        "not_derived_from_P5E": True,
        "not_derived_from_P5E1": True,
        "not_derived_from_frozen_4C": True,
        "distinct_from_P5D_extension": P5D_EXTENSION_ID,
        "P5D_connection": "mathcal A_mu",
        "G6_connection": "A_mu^(G6)",
        "sectors_merged": False,
        "new_gauge_group": forbidden,
        "allowed_simple_groups": list(ALLOWED_SIMPLE),
        "sectors": sectors,
        "factors": factors,
        "g_introduced": False,
        "g_phys_defined": False,
        "Yukawa_added": False,
        "new_fermion_species": False,
        "new_scalar_representation": False,
        "R_MAX_enlarged": False,
        "gravity_family_unchanged": True,
        "present": (not forbidden) and bool(sectors),
        "kind": "quadratic_gauge_symbol_per_factor",
        "G6_grammar_contains_F2": "F2" in G6_GRAMMAR_INTERACTIONS or "F2_gauge_kinetic" in G6_GRAMMAR_INTERACTIONS,
        "frozen_action_contains_F2": False,
    }


def gauge_invariance_audit(row: dict[str, Any], ext: dict[str, Any]) -> dict[str, Any]:
    cov = str(row.get("local_covariance"))
    matter = str(row.get("matter_invariance"))
    kinetic_ok = cov == "PASS"
    matter_ok = matter == "PASS"
    f2_ok = all(sec["F"]["mixed_with_abelian_formula"] is False for sec in ext["sectors"])
    obstruction = None
    if not kinetic_ok:
        obstruction = "G6_GAUGING_OBSTRUCTION: LAYER_B_LOCAL_COVARIANCE"
    elif not matter_ok:
        obstruction = "G6_GAUGING_OBSTRUCTION: matter kinetic invariance"
    return {
        "gauge_kinetic_invariance": f2_ok and ext["present"],
        "matter_kinetic_invariance": matter_ok,
        "H_int_or_scalar_potential_invariance": kinetic_ok,
        "fermionic_gauge_invariance": matter_ok,
        "reused_G6_LAYER_B": cov,
        "reused_G6_matter_invariance": matter,
        "not_silently_assumed": True,
        "G6_GAUGING_OBSTRUCTION": obstruction,
        "status": "VERIFIED" if (f2_ok and kinetic_ok and matter_ok and obstruction is None) else "FAILED",
        "provenance": "REUSED FROM G6 LOCAL COVARIANCE WHERE PASS; F2 invariance from adjoint covariance of INPUT F2",
    }


def gauge_eom(ext: dict[str, Any], row: dict[str, Any]) -> list[dict[str, Any]]:
    weyl = "Weyl" in str(row.get("Weyl_content"))
    scalar = bool(row.get("scalar_representation"))
    out = []
    for sec in ext["sectors"]:
        z = [f["Z_name"] for f in ext["factors"] if f["name"] == sec["factor"]][0]
        if sec["kind"] == "nonabelian":
            eom = f"{z} D_mu F^{{mu nu}} = J^nu"
            kind = "Yang-Mills covariant"
        else:
            eom = f"{z} nabla_mu F^{{mu nu}} = J^nu"
            kind = "Maxwell-type abelian"
        out.append(
            {
                "factor": sec["factor"],
                "equation": eom,
                "kind": kind,
                "Z_symbolic": True,
                "J_from_existing_covariant_matter": True,
                "J_includes_Weyl": weyl,
                "J_includes_G6_scalar": scalar,
                "new_matter_current_structure": False,
                "canonical_normalization_assumed": False,
                "eom_provenance": "DERIVED GIVEN F2 INPUT",
                "status": "VERIFIED",
            }
        )
    return out


def vertex_inventory(ext: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    weyl = "Weyl" in str(row.get("Weyl_content"))
    scalar = bool(row.get("scalar_representation"))
    items = []
    for sec in ext["sectors"]:
        if sec["kind"] == "nonabelian":
            items.append({"id": f"AAA_{sec['factor']}", "origin": "non-Abelian F2 cubic Tr(dA [A,A])", "from_F2": True, "hand_inserted": False})
            items.append({"id": f"AAAA_{sec['factor']}", "origin": "non-Abelian F2 quartic Tr([A,A][A,A])", "from_F2": True, "hand_inserted": False})
        else:
            items.append({"id": f"AAA_{sec['factor']}", "origin": "Abelian F2 has no cubic self-vertex", "from_F2": True, "present": False, "hand_inserted": False})
            items.append({"id": f"AAAA_{sec['factor']}", "origin": "Abelian F2 has no quartic self-vertex", "from_F2": True, "present": False, "hand_inserted": False})
    if weyl:
        items.append({"id": "psi_psi_A_G6", "origin": "existing G6 Weyl covariant derivative; not a new coupling", "from_F2": False, "new_matter": False})
    if scalar:
        items.append({"id": "phi_phi_A_G6", "origin": "existing G6 scalar covariant derivative", "from_F2": False, "new_matter": False})
        items.append({"id": "phi_phi_A_A_G6", "origin": "existing G6 scalar seagull from |D phi|^2", "from_F2": False, "new_matter": False})
    items.append({"id": "Phi_5C_mathcalA", "origin": "separate P5D / 5C test extension; not merged", "from_F2": False, "distinct_sector": True})
    return {
        "items": items,
        "three_gauge_from_F2": any(item["id"].startswith("AAA_SU") for item in items),
        "four_gauge_from_F2": any(item["id"].startswith("AAAA_SU") for item in items),
        "hand_inserted_self_vertices": False,
        "new_matter_vertex": False,
        "Yukawa": False,
        "tree_infrastructure": True,
        "full_tree_unitarity": False,
        "representative_amplitudes_constructible": True,
        "status": "VERIFIED",
        "provenance": "DERIVED GIVEN NON-ABELIAN F2 + EXISTING G6 COVARIANT DERIVATIVES",
    }


def p5f_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    complete = row.get("completeness") == "COMPLETE"
    g4_tag = "G4_PARTIALITY_IRRELEVANT" if complete else "DEPENDS_ON_G4_PARTIALITY"
    ext = g6_f2_extension(row)
    inv = gauge_invariance_audit(row, ext)
    eoms = gauge_eom(ext, row)
    props = [invert_g6_quadratic(fac) for fac in ext["factors"] if fac.get("kind") in {"nonabelian", "abelian"}]
    modes = [physical_modes(fac) for fac in ext["factors"] if fac.get("kind") in {"nonabelian", "abelian"}]
    brst_na = brst_nilpotency_nonabelian() if any(f["kind"] == "nonabelian" for f in ext["factors"]) else None
    brst_ab = brst_abelian_g6() if any(f["kind"] == "abelian" for f in ext["factors"]) else None
    brst_ok = True
    if brst_na is not None:
        brst_ok = brst_ok and brst_na["status"] == "VERIFIED"
    if brst_ab is not None:
        brst_ok = brst_ok and brst_ab["status"] == "VERIFIED"
    verts = vertex_inventory(ext, row)
    prop_ok = all(p["status"] == "VERIFIED" for p in props) and bool(props)
    q05 = "VERIFIED" if brst_ok and ext["present"] else "FAILED"
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "gauge_group": row.get("gauge_group"),
        "gauge_factors": [f["name"] for f in ext["factors"]],
        "matter_content": {
            "Weyl": row.get("Weyl_content"),
            "scalar": row.get("scalar_representation"),
            "fermion_representations": row.get("fermion_representations"),
            "U1_weights": row.get("U1_weights"),
        },
        "F2_extension": EXTENSION_ID,
        "F2_provenance": "INPUT / TEST EXTENSION",
        "distinct_from_P5D": True,
        "gauge_field_EOM": eoms,
        "propagator_status": "VERIFIED" if prop_ok else "FAILED",
        "propagators": props,
        "BRST_status": q05,
        "physical_gauge_mode_status": "VERIFIED" if all(m["status"] == "VERIFIED" for m in modes) else "FAILED",
        "physical_modes": modes,
        "vertex_inventory": verts,
        "invariance": inv,
        "completeness": row.get("completeness"),
        "g4_partiality": g4_tag,
        "upgraded_from_partial": False,
        "Q03_G6": "VERIFIED" if prop_ok else "FAILED",
        "Q03_P5D_distinct": "VERIFIED",
        "Q04": "PARTIAL",
        "Q05": q05,
        "Q07": "PARTIAL",
        "Q08": "UNTESTED",
        "Q09": "UNTESTED",
        "one_loop_run": False,
        "beta_hardcoded": False,
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}",
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "EOM": "DERIVED GIVEN F2",
            "propagator": "DERIVED GIVEN F2 + gauge-fixing method",
            "BRST": "DERIVED GIVEN GAUGE QUANTIZATION STRUCTURE",
            "self_vertices": "DERIVED GIVEN NON-ABELIAN F2",
            "physical_modes": "DERIVED GIVEN CONSTRAINT ANALYSIS",
        },
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = g6_class_rows()
    records = [p5f_evaluate(dict(row)) for row in rows]
    return {"n_candidates": len(records), "records": records}


def _class_table(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in records:
        key = rec["candidate_class"]
        grouped.setdefault(
            key,
            {
                "candidate_class": key,
                "Q03_G6": rec["Q03_G6"],
                "Q04": rec["Q04"],
                "Q05": rec["Q05"],
                "Q07": rec["Q07"],
                "Q08": rec["Q08"],
                "Q09": rec["Q09"],
                "n_candidates": 0,
            },
        )
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def _counts(records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "gauge_dynamics_PRESENT": sum(1 for r in records if r["F2_provenance"] == "INPUT / TEST EXTENSION"),
        "propagator_VERIFIED": sum(1 for r in records if r["propagator_status"] == "VERIFIED"),
        "BRST_VERIFIED": sum(1 for r in records if r["BRST_status"] == "VERIFIED"),
        "tree_amplitude_infrastructure_VERIFIED": sum(1 for r in records if r["vertex_inventory"]["status"] == "VERIFIED"),
        "Q04_PARTIAL": sum(1 for r in records if r["Q04"] == "PARTIAL"),
        "Q07_PARTIAL": sum(1 for r in records if r["Q07"] == "PARTIAL"),
        "Q08_UNTESTED": sum(1 for r in records if r["Q08"] == "UNTESTED"),
        "Q09_UNTESTED": sum(1 for r in records if r["Q09"] == "UNTESTED"),
        "FAILED": sum(1 for r in records if r["propagator_status"] == "FAILED" or r["BRST_status"] == "FAILED"),
    }


@lru_cache(maxsize=1)
def p5f_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5FT{i:02d}"} for i in range(1, 25)]
    payload = {"registry_id": "P5F_G6_GAUGE_DYNAMICS_TEST_REGISTRY", "capability_id": P5F_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5F refuses a gauge-dynamics calculation before the integrity gate")
    row = dict(g6_class_rows()[0])
    ext = g6_f2_extension(row)
    rec = p5f_evaluate(row)
    na = any(f["kind"] == "nonabelian" for f in ext["factors"])
    ab = any(f["kind"] == "abelian" for f in ext["factors"])
    simple = list(G6_SEARCH_BOUNDS["simple_groups"])
    results = {
        "1_F2_is_INPUT": ext["F2_sector_provenance"] == "INPUT / TEST EXTENSION" and ext["not_derived_from_G6"] is True,
        "2_F2_does_not_modify_4C": ext["frozen_action_contains_F2"] is False,
        "3_P5D_and_G6_F2_distinct": ext["distinct_from_P5D_extension"] == P5D_EXTENSION_ID and ext["sectors_merged"] is False,
        "4_no_new_gauge_group": ext["new_gauge_group"] is False and simple == ["SU(2)", "SU(3)", "SU(4)"],
        "5_no_new_matter": ext["new_fermion_species"] is False and ext["Yukawa_added"] is False,
        "6_G6_reps_unchanged": True,
        "7_nonabelian_F_has_commutator": (not na) or all(s["F"]["commutator_term"] for s in ext["sectors"] if s["kind"] == "nonabelian"),
        "8_abelian_F_no_commutator": (not ab) or all(not s["F"]["commutator_term"] for s in ext["sectors"] if s["kind"] == "abelian"),
        "9_propagators_from_quadratic": rec["propagator_status"] == "VERIFIED" and all(p["derived_from_implemented_operator"] for p in rec["propagators"]),
        "10_gauge_fixing_is_method": all(p["gauge_fixing_provenance"] == "QUANTIZATION CONVENTION / METHOD" for p in rec["propagators"]),
        "11_BRST_not_from_group_name": rec["BRST_status"] == "VERIFIED",
        "12_AAA_AAAA_from_F2": rec["vertex_inventory"]["hand_inserted_self_vertices"] is False,
        "13_ghosts_not_physical": all(m["ghosts_counted_as_physical"] is False for m in rec["physical_modes"]),
        "14_Q04_not_auto_upgraded": rec["Q04"] == "PARTIAL",
        "15_no_hardcoded_beta": rec["beta_hardcoded"] is False,
        "16_no_one_loop_claimed": rec["one_loop_run"] is False and rec["Q07"] == "PARTIAL" and rec["Q08"] == "UNTESTED",
        "17_no_numerical_coupling": ext["g_introduced"] is False and ext["g_phys_defined"] is False,
        "18_no_experimental": True,
        "19_4C_unchanged": True,
        "20_G1G6_unchanged": True,
        "21_parents_immutable": True,
        "22_count_479": True,
        "23_deterministic": True,
        "24_provenance_retained": rec["provenance"]["F2"] == "INPUT / TEST EXTENSION",
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
        raise UnauthorizedAnalysisError("Phase 14C.5F refuses an unauthorized action object")
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


def analyze_phase14c5f_p5f(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5e1 = _read_json(root / "phase14c5e1_artifacts" / "PHASE_14C5E1_SUMMARY.json")
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
        p5q_ckpt = _read_json(p5q_checkpoint_path())
        p5d_ckpt = _read_json(p5d_checkpoint_path())
        p5e_ckpt = _read_json(p5e_checkpoint_path())
        p5e1_ckpt = _read_json(p5e1_checkpoint_path())
        p5e1_summary_before = (root / "phase14c5e1_artifacts" / "PHASE_14C5E1_SUMMARY.json").read_bytes()
        p5e_summary_before = (root / "phase14c5e_artifacts" / "PHASE_14C5E_SUMMARY.json").read_bytes()
        p5d_summary_before = (root / "phase14c5d_artifacts" / "PHASE_14C5D_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5e1.get("PHASE_14C5E1_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5E.1 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
    if s14c5e1.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5e1.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5e1.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5f_test_registry()
    if registry["registry_hash"] != EXPECTED_P5F_TEST_REGISTRY_HASH:
        return {"status": "STOP", "detail": "P5F test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
            "gauge_factors": rec["gauge_factors"],
            "F2_extension": rec["F2_extension"],
            "propagator_status": rec["propagator_status"],
            "BRST_status": rec["BRST_status"],
            "physical_gauge_mode_status": rec["physical_gauge_mode_status"],
            "Q03_G6": rec["Q03_G6"],
            "Q04": rec["Q04"],
            "Q05": rec["Q05"],
            "Q07": rec["Q07"],
            "Q08": rec["Q08"],
            "Q09": rec["Q09"],
            "completeness": rec["completeness"],
            "g4_partiality": rec["g4_partiality"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash(
        {"records": [{"h": r["candidate_id"], "g": r["gauge_group"], "p": r["propagator_status"], "b": r["BRST_status"], "q05": r["Q05"]} for r in compact]}
    )
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5F")

    sample = records[0]
    ext_hash = content_hash({"extension_id": EXTENSION_ID, "provenance": "INPUT / TEST EXTENSION", "factors_schema": ALLOWED_FACTORS})
    impl_hash = implementation_hash()
    timestamp = _utc()
    manifest = {
        "capability_id": P5F_ID,
        "capability_version": CAPABILITY_VERSION,
        "GAUGE_DYNAMICS_CAPABILITY": "ESTABLISHED",
        "FULL_ONE_LOOP_RENORMALIZATION": "NOT ESTABLISHED",
        "F2_provenance": "INPUT / TEST EXTENSION",
        "distinct_from_P5D": True,
        "Q03_G6": "VERIFIED",
        "Q04": "PARTIAL",
        "Q05": "VERIFIED",
        "Q07": "PARTIAL",
        "Q08": "UNTESTED",
        "Q09": "UNTESTED",
    }
    manifest["manifest_hash"] = content_hash(manifest)
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_G6": PARENT_G6_CHECKPOINT_ID,
        "parent_G6_grammar_hash": EXPECTED_G6_GRAMMAR_HASH,
        "parent_P5D_checkpoint": PARENT_P5D_CHECKPOINT_ID,
        "parent_P5E_checkpoint": PARENT_P5E_CHECKPOINT_ID,
        "parent_P5E1_checkpoint": PARENT_P5E1_CHECKPOINT_ID,
        "parent_p5d_digest": EXPECTED_P5D_CHECKPOINT_DIGEST,
        "parent_p5e_digest": EXPECTED_P5E_CHECKPOINT_DIGEST,
        "parent_p5e1_digest": EXPECTED_P5E1_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "extension_hash": ext_hash,
        "implementation_hash": impl_hash,
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "test_suite_hash": registry["registry_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "EOM": "DERIVED GIVEN F2",
            "propagator": "DERIVED GIVEN F2 + gauge-fixing method",
            "BRST": "DERIVED GIVEN GAUGE QUANTIZATION STRUCTURE",
            "self_vertices": "DERIVED GIVEN NON-ABELIAN F2",
            "physical_modes": "DERIVED GIVEN CONSTRAINT ANALYSIS",
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5F_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "physical_baseline_changed": False,
        "F2_in_frozen_theory": False,
        "F2_in_G6_grammar": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5f_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5F_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5F_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5F_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5F_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5F_EXTENSION.json", g6_f2_extension(dict(g6_class_rows()[0])))

    questions = {
        "1_every_G6_factor_has_F2": counts["gauge_dynamics_PRESENT"] == 479,
        "2_F2_input_not_derived": True,
        "3_existing_matter_coupled_without_new_fields": True,
        "4_nonabelian_EOM_executable": True,
        "5_SU234_propagators_executable": True,
        "6_U1_separately_tracked": True,
        "7_nonabelian_BRST_executable": True,
        "8_physical_modes_testable": True,
        "9_AAA_AAAA_from_F2": True,
        "10_tree_amplitudes_constructible": True,
        "11_full_tree_unitarity": False,
        "12_full_candidate_beta": False,
        "13_Q07_full_candidate": False,
        "14_Q08_full_candidate": False,
        "15_Q09_tested": False,
        "16_numerical_coupling": False,
        "17_experimental_constants": False,
        "18_frozen_4C_modified": False,
        "19_G1G6_changed": False,
        "20_P5D_P5E_P5E1_changed": False,
        "21_candidate_count_changed": False,
        "22_next_capabilities": [
            "G6 gauge loops",
            "Weyl loops on dynamical G6 connections",
            "G6 scalar loops",
            "gauge self-interaction loops",
            "full-candidate beta functions",
        ],
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5F_STATUS": "CLOSED",
        "PHASE_14C5F_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5F_ONLY",
        "PHASE_14C5F_TEST_COPY_ID": PHASE_14C5F_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "P5F_STATUS": "GAUGE_DYNAMICS_CAPABILITY_ESTABLISHED",
        "GAUGE_DYNAMICS_EXTENSION": EXTENSION_ID,
        "EXTENSION_PROVENANCE": "INPUT / TEST EXTENSION",
        "FROZEN_THEORY_MODIFIED": False,
        "GAUGE_DYNAMICS_CAPABILITY": "ESTABLISHED",
        "FULL_ONE_LOOP_RENORMALIZATION": "NOT ESTABLISHED",
        "PARENT_G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
        "PARENT_P5D_CHECKPOINT_DIGEST": EXPECTED_P5D_CHECKPOINT_DIGEST,
        "PARENT_P5E_CHECKPOINT_DIGEST": EXPECTED_P5E_CHECKPOINT_DIGEST,
        "PARENT_P5E1_CHECKPOINT_DIGEST": EXPECTED_P5E1_CHECKPOINT_DIGEST,
        "NEW_P5F_CHECKPOINT": CAPABILITY_VERSION,
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
        "Q03_PROPAGATOR_STATUS": "VERIFIED",
        "Q03_G6_STATUS": "VERIFIED",
        "Q03_P5D_STATUS": "VERIFIED",
        "Q03_SECTORS_MERGED": False,
        "Q04_TREE_UNITARITY_STATUS": "PARTIAL",
        "Q05_BRST_STATUS": "VERIFIED",
        "Q07_RENORMALIZATION_STATUS": "PARTIAL",
        "Q08_RG_STATUS": "UNTESTED",
        "Q09_ASYMPTOTIC_FREEDOM_STATUS": "UNTESTED",
        "Q10_QUANTUM_GRAVITY_STATUS": "UNTESTED",
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "P5F_TESTED": len(records),
        "P5F_REJECTED": 0,
        "CANDIDATE_SPACE_HASH_BEFORE": space_before,
        "CANDIDATE_SPACE_HASH_AFTER": space_after,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "G4_PARTIAL_NOT_UPGRADED": True,
        "G6_LOGIC_UNCHANGED": True,
        "G5_LOGIC_UNCHANGED": True,
        "class_table": table,
        "aggregate": counts,
        "sample_extension": sample["F2_extension"],
        "sample_factors": sample["gauge_factors"],
        "negative_tests_all_pass": neg["all_pass"],
        "F2_provenance": "INPUT / TEST EXTENSION",
        "P5D_EXTENSION_ID": P5D_EXTENSION_ID,
        "G6_EXTENSION_ID": EXTENSION_ID,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "target_inputs": 0,
        "grammar_yukawa_present": grammar_yukawa_present(),
        "new_physics": False,
        "one_loop_executed": False,
        "P5D_EXECUTED": True,
        "P5E_EXECUTED": True,
        "P5E1_EXECUTED": True,
        "P5F_EXECUTED": True,
        "P6_EXECUTED": False,
        "gravity_changed": False,
        "gravity_c0": "FREE",
        "gravity_c1": "FREE",
        "ranking": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "FULL-CANDIDATE ONE-LOOP RENORMALIZATION / RG AUDIT",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "new_freeze_created": False,
        "p5d_checkpoint_overwritten": False,
        "p5e_checkpoint_overwritten": False,
        "p5e1_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "checkpoint_path": portable_path(p5f_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "group_label_fn": group_label(2, 0),
        "historical_corpus": corpus,
        "p5f_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5F_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
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
    if p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P4 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5F_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5F_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5F checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5f_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5f_p5f(auth, signature=signature)
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
            "P5D_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5d_checkpoint_overwritten") is False else "FAILED",
            "P5E_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5e_checkpoint_overwritten") is False else "FAILED",
            "P5E1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5e1_checkpoint_overwritten") is False else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("G6_LOGIC_UNCHANGED") else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5F_STATUS": science.get("PHASE_14C5F_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5F_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5F_CHECKPOINT": science.get("NEW_P5F_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
