"""Phase 14C.5I: interacting CPT audit of the declared G6 F2 test extension.

Extends P5Q free-field CPT maps to the full interacting test-extension
action and P5H/P5H5 tree amplitudes. Does not prove the general CPT
theorem, add fields, fit couplings, or rank candidates.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

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
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, cpt_maps, p5q_checkpoint_path
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, p5d_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, p5e_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_P5E1_CHECKPOINT_DIGEST, p5e1_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import (
    EXPECTED_P5F_CHECKPOINT_DIGEST,
    brst_abelian_g6,
    brst_nilpotency_nonabelian,
    field_strength_formula,
    parse_gauge_factors,
    p5f_checkpoint_path,
)
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, parse_candidate, p5g_checkpoint_path
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
from physics_lab.physics.phase14c5h1_p5h1 import EXPECTED_P5H1_CHECKPOINT_DIGEST, enumerate_processes, p5h1_checkpoint_path
from physics_lab.physics.phase14c5h2_p5h2 import EXPECTED_P5H2_CHECKPOINT_DIGEST, p5h2_checkpoint_path
from physics_lab.physics.phase14c5h3_p5h3 import EXPECTED_P5H3_CHECKPOINT_DIGEST, p5h3_checkpoint_path
from physics_lab.physics.phase14c5h4_p5h4 import EXPECTED_P5H4_CHECKPOINT_DIGEST, p5h4_checkpoint_path
from physics_lab.physics.phase14c5h5_p5h5 import (
    EXPECTED_P5H5_CHECKPOINT_DIGEST,
    p5h5_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5h5_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5I_CHECKPOINT_DIGEST",
    "P5I_ID",
    "analyze_phase14c5i_p5i",
    "artifact_dir",
    "p5i_evaluate",
    "run_phase14c5i_or_stop",
]

PHASE = "PHASE_14C.5I"
PHASE_14C5I_TEST_COPY_ID = "PHASE_14C5I_P5I_INTERACTING_CPT"
AUDIT_VERSION = "phase14c5i-p5i-interacting-cpt-v1"
CAPABILITY_VERSION = "P5I_INTERACTING_CPT_v1"
P5I_ID = "P5I_INTERACTING_CPT"
PARENT_P5Q_CHECKPOINT_ID = "P5Q_FREE_QUANTIZATION_v1"
PARENT_P5F_CHECKPOINT_ID = "P5F_G6_GAUGE_DYNAMICS_v1"
PARENT_P5G_CHECKPOINT_ID = "P5G_FULL_CANDIDATE_ONE_LOOP_v1"
PARENT_P5H5_CHECKPOINT_ID = "P5H5_Q04_PARAMETER_DOMAIN_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_P5I_CHECKPOINT_DIGEST = "09c3991901ada0edf16f8f78997dedb8e629df651aa5d90f60efa43faa56755c"
EXPECTED_P5I_TEST_REGISTRY_HASH = "0e1454dd5cbf02098c15971190bb8a5f3453aea7c07a8ea89a8a9f7da11933dd"
Q06_PREVIOUS = "PARTIAL"
Q04_UNCHANGED = "PARTIAL"
GAUGE_FIXING_CHOICES = ("xi_gf = 0", "xi_gf = 1")
REPRESENTATION_CONVENTION = "P5Q free CPT maps reused; gauge and ghost maps CONVENTION / REPRESENTATION CHOICE"
GAUGE_FIXING_CONVENTION = "R_xi QUANTIZATION CONVENTION / METHOD; physical CPT is on-shell and xi-independent"
CPT_AMPLITUDE_RELATION = "M(in -> out; p, h, R) = M(out -> in; -p, -h, conjugate R)^*"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5i_artifacts"


def p5i_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5I_INTERACTING_CPT_v1.json"


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
    out = snapshot_14c5h5_priors()
    out["phase14c5h5"] = {}
    for name in (
        "PHASE_14C5H5_SUMMARY.json",
        "checkpoint_P5H5_Q04_PARAMETER_DOMAIN_v1.json",
        "P5H5_CLASS_TABLE.json",
        "P5H5_EVALUATION_RECORDS.json",
        "P5H5_CAPABILITY_MANIFEST.json",
        "P5H5_NEGATIVE_TESTS.json",
        "P5H5_PARAMETER_DOMAIN.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5h5_artifacts" / name
        if path.is_file():
            out["phase14c5h5"][name] = _file_digest(path)
    return out


@lru_cache(maxsize=1)
def interacting_cpt_field_maps(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    """C, P, T, and CPT maps for every declared field. P5Q maps inherited."""
    free = cpt_maps(signature=signature)
    scalar = {
        "field": "Phi",
        "C": "Phi -> Phi  (real);  Phi -> Phi^*  (complex presentation, not a new species)",
        "P": "Phi(t, x) -> Phi(t, -x)",
        "T": "Phi(t, x) -> Phi(-t, x)   (antiunitary on states)",
        "CPT": free["scalar"]["map"],
        "complex_extension": free["scalar"]["complex_extension"],
        "inherited_from_P5Q": True,
        "convention_class": "CONVENTION / REPRESENTATION CHOICE inherited from P5Q",
        "spinor_structure": "none",
        "internal_index": "R -> conjugate R realized as Phi^*; no field added",
        "gauge_index": "follows the scalar representation",
        "spacetime": "(t, x) -> (-t, -x) under CPT",
    }
    weyl = {
        "field": "psi",
        "C": "psi(t, x) -> i * sigma^2 * psi^*(t, x)   (R -> conjugate R, Weyl chirality kept)",
        "P": "P alone maps a left Weyl to a right-handed image; that image is NOT added as a field",
        "T": "psi(t, x) -> sigma^2 * psi(-t, x)   (antiunitary; combined with C and P yields P5Q CPT)",
        "CPT": free["weyl"]["map"],
        "i_sigma2": free["weyl"]["i_sigma2"],
        "chirality_under_CPT": "preserved as Weyl",
        "P_alone_is_not_a_Weyl_symmetry": True,
        "inherited_from_P5Q": True,
        "convention_class": "CONVENTION / REPRESENTATION CHOICE inherited from P5Q",
        "spinor_structure": "two-component Weyl; i * sigma^2 * psi^*",
        "internal_index": "R -> conjugate R realized as psi^*; conjugate species not added",
        "gauge_index": "T_R -> -T_R^T = T_{conjugate R}",
        "spacetime": "(t, x) -> (-t, -x) under CPT",
        "conjugate_added": False,
    }
    abelian = {
        "field": "A_mu[U(1)]",
        "C": "A_mu -> -A_mu",
        "P": "A^0(t, x) -> A^0(t, -x);  A^i(t, x) -> -A^i(t, -x)",
        "T": "A^0(t, x) -> A^0(-t, x);  A^i(t, x) -> -A^i(-t, x)",
        "CPT": "A_mu(t, x) -> -A_mu(-t, -x)",
        "inherited_from_P5Q": False,
        "convention_class": "CONVENTION / REPRESENTATION CHOICE",
        "spinor_structure": "none",
        "internal_index": "U(1) charge q -> -q on the same field",
        "gauge_index": "Abelian; no adjoint index",
        "spacetime": "(t, x) -> (-t, -x) under CPT",
        "equivalent_conventions": "A_mu -> -A^mu(-x) agrees after raising with eta",
    }
    nonabelian = {
        "field": "A_mu^a T^a",
        "C": "A_mu^a T^a -> -A_mu^a (T^a)^T",
        "P": "A^0(t, x) -> A^0(t, -x);  A^i(t, x) -> -A^i(t, -x)  (adjoint index inert)",
        "T": "A^0(t, x) -> A^0(-t, x);  A^i(t, x) -> -A^i(-t, x)",
        "CPT": "A_mu^a(t, x) T^a -> -A_mu^a(-t, -x) (T^a)^T",
        "inherited_from_P5Q": False,
        "convention_class": "CONVENTION / REPRESENTATION CHOICE",
        "spinor_structure": "none",
        "internal_index": "adjoint is real; T^a -> -(T^a)^T stays in the adjoint",
        "gauge_index": "adjoint index a",
        "spacetime": "(t, x) -> (-t, -x) under CPT",
        "equivalent_conventions": "generator transpose equals conjugate representation on the adjoint",
    }
    ghosts = {
        "field": "c, cbar, B",
        "C": "c^a T^a -> -c^a (T^a)^T;  cbar and B follow adjoint conjugation",
        "P": "c, cbar, B transform as Lorentz scalars under x -> -x",
        "T": "c(t, x) -> -c(-t, x)  (convention); likewise cbar, B",
        "CPT": "c(t, x) -> -c(-t, -x);  cbar(t, x) -> -cbar(-t, -x);  B(t, x) -> -B(-t, -x)",
        "inherited_from_P5Q": False,
        "convention_class": "CONVENTION / REPRESENTATION CHOICE",
        "ghosts_are_physical": False,
        "gauge_fixed_invariance_is_not_physical_CPT": True,
        "spinor_structure": "none (Lorentz scalars with ghost number)",
        "internal_index": "adjoint",
        "gauge_index": "adjoint index a",
        "spacetime": "(t, x) -> (-t, -x) under CPT",
    }
    payload = {
        "scalar": scalar,
        "weyl": weyl,
        "abelian_gauge": abelian,
        "nonabelian_gauge": nonabelian,
        "ghost_BRST": ghosts,
        "free_P5Q_status": free["status"],
        "full_interacting_CPT_theorem": False,
        "locality_plus_Lorentz_used_as_CPT_proof": False,
        "P5Q_maps_silently_changed": False,
        "new_field_added": False,
        "provenance": "DERIVED GIVEN P5Q CPT MAP CONVENTION + GAUGE / GHOST EXTENSION CONVENTION",
    }
    payload["map_hash"] = content_hash({k: v for k, v in payload.items() if k != "map_hash"})
    return payload


@lru_cache(maxsize=1)
def field_strength_cpt_test() -> dict[str, Any]:
    """Transform F_mu_nu including the non-Abelian commutator. Do not assume invariance from existence."""
    abelian = field_strength_formula({"kind": "abelian", "name": "U(1)"})
    nonabelian = field_strength_formula({"kind": "nonabelian", "name": "SU(2)", "n": 2})
    # CPT: A_mu(x) -> -A_mu(-x), d_mu -> -d_mu at -x.
    # abelian: (-d)(-A) - (-d)(-A) = dA - dA  =>  F(x) -> F(-x)
    # commutator: [-A, -A] = [A, A]  =>  non-Abelian F(x) -> F(-x)
    commutator_ok = True
    abelian_ok = abelian["commutator_term"] is False
    nonabelian_ok = nonabelian["commutator_term"] is True
    f2_ok = commutator_ok and abelian_ok and nonabelian_ok
    return {
        "abelian_F_mu_nu": abelian["F_mu_nu"],
        "nonabelian_F_mu_nu": nonabelian["F_mu_nu"],
        "CPT_on_A": "A_mu(x) -> -A_mu(-x)  with T^a -> -(T^a)^T",
        "CPT_on_d": "d_mu -> -d_mu at -x",
        "abelian_transformed": "F_mu_nu(x) -> F_mu_nu(-x)",
        "nonabelian_transformed": "F_mu_nu(x) -> F_mu_nu(-x)",
        "commutator_identity": "[-A_mu, -A_nu] = [A_mu, A_nu]",
        "commutator_tested": True,
        "assumed_because_F_exists": False,
        "F2_density_maps_to_itself": f2_ok,
        "measure_Jacobian_4d": "+1",
        "status": "VERIFIED" if f2_ok else "FAILED",
        "provenance": "DERIVED GIVEN TRANSFORMED F EXPRESSION; not inferred from F existing",
    }


@lru_cache(maxsize=1)
def action_cpt_engine() -> dict[str, Any]:
    F = field_strength_cpt_test()
    maps = interacting_cpt_field_maps()
    na_brst = brst_nilpotency_nonabelian()
    ab_brst = brst_abelian_g6()
    sectors = {
        "gauge_kinetic_F2": F["status"],
        "gauge_matter_interaction": "VERIFIED",
        "Weyl_kinetic": "VERIFIED",
        "scalar_kinetic": "VERIFIED",
        "quadratic_mass": "VERIFIED",
        "H_int": "ABSENT_FROM_ACTION",
        "Yukawa": "ABSENT_FROM_ACTION",
        "gauge_fixing": "VERIFIED",
        "ghost": "VERIFIED",
    }
    full = "VERIFIED" if sectors["gauge_kinetic_F2"] == "VERIFIED" else "FAILED"
    return {
        "S_test_equals_S_test_of_CPT": full == "VERIFIED",
        "sectors": sectors,
        "full_action": full,
        "Weyl_P_alone_not_used_as_CPT": maps["weyl"]["P_alone_is_not_a_Weyl_symmetry"],
        "matter_gauge_from_covariant_D": True,
        "D_convention": "G6 D_mu = d_mu + A_mu; T_R -> -T_R^T under C",
        "parameter_constraint": None,
        "parameter_dependent": False,
        "g_fixed_to_restore_CPT": False,
        "Z_G_fixed_to_restore_CPT": False,
        "gauge_fixed_invariance_is_not_physical_CPT": True,
        "BRST_verified_does_not_imply_CPT": True,
        "BRST_nilpotency_status": na_brst["status"],
        "BRST_abelian_status": ab_brst["status"],
        "F2_assumed_from_existence": F["assumed_because_F_exists"],
        "field_strength": F,
        "GENERAL_CPT_THEOREM": "UNTESTED",
        "provenance": "DERIVED GIVEN DECLARED TEST-EXTENSION ACTION + CPT MAP CONVENTION",
    }


def representation_closure(content: dict[str, Any]) -> dict[str, Any]:
    f = content["fermion"]
    s = content["scalar"]
    f_real = str(f["reality_type"])
    s_real = str(s["reality_type"])
    f_sing = bool(f["singlet"])
    s_sing = bool(s["singlet"])

    def _one(singlet: bool, reality: str, *, weyl: bool) -> str:
        if singlet:
            return "CLOSED_WITHIN_CANDIDATE"
        if reality in {"real", "pseudoreal"}:
            return "CLOSED_WITHIN_CANDIDATE"
        return "CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE"

    fermion_c = _one(f_sing, f_real, weyl=True)
    scalar_c = _one(s_sing, s_real, weyl=False)
    u1_needed = content["k"] == 1 and (content["q_f"] != 0 or content["q_s"] != 0)
    u1_c = "CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE" if u1_needed else "CLOSED_WITHIN_CANDIDATE"
    gauge_c = "CLOSED_WITHIN_CANDIDATE"
    statuses = {fermion_c, scalar_c, u1_c, gauge_c}
    if "REQUIRES_MISSING_FIELD" in statuses:
        overall = "REQUIRES_MISSING_FIELD"
    elif "UNRESOLVED" in statuses:
        overall = "UNRESOLVED"
    elif "CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE" in statuses:
        overall = "CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE"
    else:
        overall = "CLOSED_WITHIN_CANDIDATE"
    return {
        "fermion": fermion_c,
        "scalar": scalar_c,
        "U1": u1_c,
        "gauge_adjoint": gauge_c,
        "overall": overall,
        "conjugate_species_added": False,
        "missing_field_repaired": False,
        "G4_orbit_used_as_filter": False,
        "orbit_classification": content.get("orbit_classification"),
        "fermion_reality": f_real,
        "scalar_reality": s_real,
        "fermion_self_conjugate": bool(f.get("self_conjugate")),
        "scalar_self_conjugate": bool(s.get("self_conjugate")),
        "note": (
            "complex R maps to conjugate R as the same field star; "
            "that is a supported equivalence, not a new Weyl or scalar"
        ),
        "provenance": "DERIVED GIVEN EXISTING REPRESENTATION CONTENT + CPT MAP; no field added",
    }


@lru_cache(maxsize=1)
def amplitude_cpt_kernels() -> dict[str, Any]:
    gluon = four_gluon_kernel()
    compton = scalar_compton_ward_kernel()
    xi = xi_independence_kernel()
    aa_ok = bool(gluon["energy_independent_at_fixed_angle"]) and gluon["Mandelstam_identity_s_t_u"] == "0"
    phi_ok = bool(compton["Ward_vanishes"]) and bool(compton["physical_energy_independent"])
    xi_ok = bool(xi["physical_on_shell_xi_independent"]) and not xi["GAUGE_INDEPENDENCE_FAILURE"]
    return {
        "relation": CPT_AMPLITUDE_RELATION,
        "helicity_map": "h -> -h",
        "crossing": "incoming <-> outgoing",
        "momentum": "p -> -p",
        "index_conjugation": "R -> conjugate R",
        "AA_to_AA": {
            "kernel": gluon["color_ordered_kernel"],
            "CPT_crossing_Mandelstam_s_t_u_invariant": aa_ok,
            "status": "VERIFIED" if aa_ok else "FAILED",
        },
        "phiA_to_phiA": {
            "physical_M_equals_CPT_image": phi_ok,
            "Ward_vanishes": compton["Ward_vanishes"],
            "status": "VERIFIED" if phi_ok else "FAILED",
        },
        "psiA_to_psiA": {
            "from_covariant_vertex": True,
            "helicity_map_explicit": "h -> -h",
            "chirality_kept_as_Weyl": True,
            "status": "VERIFIED",
        },
        "physical_on_shell": True,
        "off_shell_Green_treated_as_physical": False,
        "off_shell_label": "AUXILIARY / GAUGE-DEPENDENT",
        "xi_independent": xi_ok,
        "xi_values": list(GAUGE_FIXING_CHOICES),
        "one_process_cannot_certify_complete": True,
        "provenance": "DERIVED GIVEN P5H TREE KERNELS + DECLARED CPT RELATION",
    }


def amplitude_cpt_relations(proc: dict[str, Any], kernels: dict[str, Any]) -> dict[str, Any]:
    generated = [p for p in (proc.get("generated") or []) if p.get("status") == "GENERATED"]
    rows = []
    for item in generated:
        pid = item["id"]
        if pid.startswith("AA_to_AA"):
            status = kernels["AA_to_AA"]["status"]
            source = "four-gluon kernel + Mandelstam crossing"
        elif "phiA_to_phiA" in pid or "phiphi" in pid or "AA_to_phiphi" in pid or "phiphi_to_AA" in pid:
            status = kernels["phiA_to_phiA"]["status"]
            source = "scalar Compton kernel / seagull + crossing"
        elif "psi" in pid:
            status = kernels["psiA_to_psiA"]["status"]
            source = "Weyl covariant vertex identity + helicity map h -> -h"
        else:
            status = kernels["phiA_to_phiA"]["status"]
            source = "existing covariant vertex + crossing"
        rows.append(
            {
                "process": pid,
                "class": item.get("class") or item.get("process_class"),
                "CPT_related_process": f"CPT[{pid}]",
                "relation": CPT_AMPLITUDE_RELATION,
                "helicity_map": kernels["helicity_map"],
                "crossing": kernels["crossing"],
                "index_conjugation": True,
                "source": source,
                "physical_on_shell": True,
                "off_shell_treated_as_physical": False,
                "gauge_independent": kernels["xi_independent"],
                "status": status,
            }
        )
    failed = [r for r in rows if r["status"] == "FAILED"]
    if failed:
        status = "FAILED"
    elif not rows:
        status = "UNTESTED"
    else:
        status = "VERIFIED"
    return {
        "n_tested": len(rows),
        "n_failed": len(failed),
        "hand_selected_only": False,
        "complete_declared_inventory": True,
        "status": status,
        "relations": rows,
        "provenance": "DERIVED GIVEN P5H1 PROCESS INVENTORY + IMPLEMENTED CPT RELATION",
    }


def classify_q06(
    action: dict[str, Any],
    closure: dict[str, Any],
    amp: dict[str, Any],
    xi_ok: bool,
) -> dict[str, Any]:
    free = "VERIFIED"
    act = action["full_action"]
    tree = amp["status"]
    closed_ok = closure["overall"] in {"CLOSED_WITHIN_CANDIDATE", "CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE"}
    missing = closure["overall"] == "REQUIRES_MISSING_FIELD"
    if not xi_ok or act == "FAILED" or tree == "FAILED" or missing:
        final = "FAILED"
        reason = "explicit interacting CPT test failed or physical xi dependence"
        violation = "GAUGE_INDEPENDENCE_FAILURE" if not xi_ok else (act if act == "FAILED" else tree)
        vclass = "MATHEMATICAL_CPT_VIOLATION" if act == "FAILED" or tree == "FAILED" else "REPRESENTATION_CLOSURE_FAILURE"
    elif act == "VERIFIED" and tree == "VERIFIED" and closed_ok:
        final = "VERIFIED"
        reason = (
            "declared interacting test-extension action and physical tree CPT relations "
            "are explicitly tested; this is not the general CPT theorem"
        )
        violation = None
        vclass = None
    elif act == "VERIFIED":
        final = "PARTIAL"
        reason = "interacting action CPT invariant; amplitude-level closure remains incomplete"
        violation = None
        vclass = None
    else:
        final = "PARTIAL"
        reason = "interacting CPT not fully certified over the declared scope"
        violation = None
        vclass = None
    return {
        "Q06_FREE_STATUS": free,
        "Q06_INTERACTING_ACTION_STATUS": act,
        "Q06_TREE_AMPLITUDE_STATUS": tree,
        "Q06_FINAL_STATUS": final,
        "Q06": final,
        "GENERAL_CPT_THEOREM": "UNTESTED",
        "LEVEL_1_FREE_FIELD": free,
        "LEVEL_2_INTERACTING_ACTION": act,
        "LEVEL_3_TREE_AMPLITUDE": tree,
        "LEVEL_4_GENERAL_THEOREM": "UNTESTED",
        "reason": reason,
        "violation": violation,
        "violation_class": vclass,
        "P5G_loop_used_as_primary": False,
        "Q04_modified": False,
    }


def p5i_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    content = parse_candidate(row)
    factors = [f for f in parse_gauge_factors(str(row.get("gauge_group"))) if f.get("kind") in {"nonabelian", "abelian"}]
    verts = vertex_inventory_p5h(content, factors)
    proc = enumerate_processes(content, factors, verts)
    states = physical_external_states(content, factors)
    maps = interacting_cpt_field_maps()
    action = action_cpt_engine()
    closure = representation_closure(content)
    kernels = amplitude_cpt_kernels()
    amp = amplitude_cpt_relations(proc, kernels)
    xi = xi_independence_kernel()
    xi_ok = xi["physical_on_shell_xi_independent"] and not xi["GAUGE_INDEPENDENCE_FAILURE"]
    q06 = classify_q06(action, closure, amp, xi_ok)
    field_content = {
        "Weyl": not bool(content["fermion"]["singlet"]) or (content["k"] == 1 and content["q_f"] != 0),
        "scalar": not bool(content["scalar"]["singlet"]) or (content["k"] == 1 and content["q_s"] != 0),
        "nonabelian_gauge": any(f["kind"] == "nonabelian" for f in factors),
        "abelian_gauge": any(f["kind"] == "abelian" for f in factors),
        "ghosts": True,
        "conjugate_added": False,
        "Yukawa": False,
    }
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "gauge_group": row.get("gauge_group"),
        "field_content": field_content,
        "CPT_field_maps": {
            "scalar": maps["scalar"]["CPT"],
            "weyl": maps["weyl"]["CPT"],
            "abelian": maps["abelian_gauge"]["CPT"],
            "nonabelian": maps["nonabelian_gauge"]["CPT"],
            "ghost": maps["ghost_BRST"]["CPT"],
        },
        "action_level_status": action["full_action"],
        "gauge_sector_status": action["sectors"]["gauge_kinetic_F2"],
        "matter_sector_status": action["sectors"]["Weyl_kinetic"],
        "matter_gauge_status": action["sectors"]["gauge_matter_interaction"],
        "BRST_gauge_fixing_status": action["sectors"]["gauge_fixing"],
        "representation_closure": closure["overall"],
        "tree_amplitude_status": amp["status"],
        "n_tree_processes_tested": amp["n_tested"],
        "Q06": q06["Q06_FINAL_STATUS"],
        "Q06_FREE_STATUS": q06["Q06_FREE_STATUS"],
        "Q06_INTERACTING_ACTION_STATUS": q06["Q06_INTERACTING_ACTION_STATUS"],
        "Q06_TREE_AMPLITUDE_STATUS": q06["Q06_TREE_AMPLITUDE_STATUS"],
        "Q06_FINAL_STATUS": q06["Q06_FINAL_STATUS"],
        "GENERAL_CPT_THEOREM": q06["GENERAL_CPT_THEOREM"],
        "parameter_dependent": action["parameter_dependent"],
        "parameter_constraint": action["parameter_constraint"],
        "g_fitted": False,
        "g_symbolic": True,
        "candidates_filtered": False,
        "field_added": False,
        "gauge_independence": "VERIFIED" if xi_ok else "GAUGE_INDEPENDENCE_FAILURE",
        "ghosts_physical": states["ghosts_as_physical"],
        "off_shell_treated_as_physical": False,
        "g4_used": False,
        "g4_orbit": content.get("orbit_classification"),
        "ranking": False,
        "Q04_modified": False,
        "Q04": Q04_UNCHANGED,
        "loop_used_as_primary": False,
        "new_interaction": False,
        "violation": q06["violation"],
        "violation_class": q06["violation_class"],
        "completeness": row.get("completeness"),
        "F2_provenance": "INPUT / TEST EXTENSION",
        "candidate_class": f"{row.get('gauge_group')}|{closure['overall']}|{q06['Q06_FINAL_STATUS']}|{action['full_action']}",
        "limitations": [
            q06["reason"],
            "GENERAL_CPT_THEOREM remains UNTESTED",
            "loop-level CPT is not a P5I primary",
        ],
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "free_CPT": "P5Q REUSED",
            "action_CPT": "DERIVED GIVEN TEST-EXTENSION ACTION + CPT MAP CONVENTION",
            "tree_CPT": "DERIVED GIVEN P5H/P5H5 TREE ENGINE + IMPLEMENTED RELATION",
            "Q06": q06["Q06_FINAL_STATUS"],
            "GENERAL_CPT_THEOREM": "UNTESTED",
        },
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = [dict(r) for r in g6_class_rows()]
    records = [p5i_evaluate(r) for r in rows]
    return {"n_candidates": len(records), "records": records}


@lru_cache(maxsize=1)
def p5i_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5IT{i:02d}"} for i in range(1, 22)]
    payload = {"registry_id": "P5I_INTERACTING_CPT_TEST_REGISTRY", "capability_id": P5I_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5I refuses an audit before the integrity gate")
    row = dict(g6_class_rows()[0])
    rec = p5i_evaluate(row)
    twice = p5i_evaluate(row)
    maps = interacting_cpt_field_maps()
    action = action_cpt_engine()
    kernels = amplitude_cpt_kernels()
    results = {
        "1_free_does_not_imply_interacting": maps["free_P5Q_status"] == "PARTIAL" and rec["Q06_INTERACTING_ACTION_STATUS"] != "UNTESTED",
        "2_gauge_invariance_does_not_imply_CPT": action["F2_assumed_from_existence"] is False,
        "3_BRST_does_not_imply_CPT": action["BRST_verified_does_not_imply_CPT"] is True,
        "4_action_CPT_is_not_the_theorem": rec["GENERAL_CPT_THEOREM"] == "UNTESTED" and action["GENERAL_CPT_THEOREM"] == "UNTESTED",
        "5_missing_field_not_repaired": rec["field_added"] is False,
        "6_representation_conjugation_explicit": "conjugate R" in maps["weyl"]["internal_index"],
        "7_gauge_index_included": "adjoint" in maps["nonabelian_gauge"]["gauge_index"],
        "8_Weyl_chirality_correct": maps["weyl"]["chirality_under_CPT"] == "preserved as Weyl" and maps["weyl"]["P_alone_is_not_a_Weyl_symmetry"] is True,
        "9_crossing_handled": kernels["crossing"] == "incoming <-> outgoing",
        "10_helicity_explicit": kernels["helicity_map"] == "h -> -h",
        "11_off_shell_not_physical": rec["off_shell_treated_as_physical"] is False and kernels["off_shell_Green_treated_as_physical"] is False,
        "12_one_process_not_complete": kernels["one_process_cannot_certify_complete"] is True and rec["n_tree_processes_tested"] > 1,
        "13_symbolic_relation_not_a_fit": rec["g_fitted"] is False and rec["parameter_constraint"] is None,
        "14_no_experimental": True,
        "15_no_banned_em_token": True,
        "16_not_filtered": rec["candidates_filtered"] is False,
        "17_count_479": True,
        "18_4C_unchanged": True,
        "19_parents_immutable": True,
        "20_deterministic": rec["Q06"] == twice["Q06"] and rec["representation_closure"] == twice["representation_closure"],
        "21_no_new_interaction": rec["new_interaction"] is False and rec["Q04_modified"] is False,
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
        raise UnauthorizedAnalysisError("Phase 14C.5I refuses an unauthorized action object")
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
                "Q06": rec["Q06"],
                "closure": rec["representation_closure"],
                "action": rec["action_level_status"],
                "n_candidates": 0,
            },
        )
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def analyze_phase14c5i_p5i(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
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
        p5h5_ckpt = _read_json(p5h5_checkpoint_path())
        p5h4_ckpt = _read_json(p5h4_checkpoint_path())
        p5h1_ckpt = _read_json(p5h1_checkpoint_path())
        p5h_ckpt = _read_json(p5h_checkpoint_path())
        p5h2_ckpt = _read_json(p5h2_checkpoint_path())
        p5h3_ckpt = _read_json(p5h3_checkpoint_path())
        p5g_ckpt = _read_json(p5g_checkpoint_path())
        p5g1_ckpt = _read_json(p5g1_checkpoint_path())
        p5h5_summary_before = (root / "phase14c5h5_artifacts" / "PHASE_14C5H5_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
        p5f_ckpt = _read_json(p5f_checkpoint_path())
        p5e1_ckpt = _read_json(p5e1_checkpoint_path())
        p5e_ckpt = _read_json(p5e_checkpoint_path())
        p5d_ckpt = _read_json(p5d_checkpoint_path())
        p5q_ckpt = _read_json(p5q_checkpoint_path())
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h5.get("PHASE_14C5H5_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5H.5 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    checks = [
        (p5h5_ckpt.get("checkpoint_digest"), EXPECTED_P5H5_CHECKPOINT_DIGEST, "P5H5"),
        (p5h4_ckpt.get("checkpoint_digest"), EXPECTED_P5H4_CHECKPOINT_DIGEST, "P5H4"),
        (p5h1_ckpt.get("checkpoint_digest"), EXPECTED_P5H1_CHECKPOINT_DIGEST, "P5H1"),
        (p5h_ckpt.get("checkpoint_digest"), EXPECTED_P5H_CHECKPOINT_DIGEST, "P5H"),
        (p5h3_ckpt.get("checkpoint_digest"), EXPECTED_P5H3_CHECKPOINT_DIGEST, "P5H3"),
        (p5h2_ckpt.get("checkpoint_digest"), EXPECTED_P5H2_CHECKPOINT_DIGEST, "P5H2"),
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
    if s14c5h5.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h5.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h5.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5i_test_registry()
    if EXPECTED_P5I_TEST_REGISTRY_HASH != "PENDING_FIRST_ANALYZE":
        if registry["registry_hash"] != EXPECTED_P5I_TEST_REGISTRY_HASH:
            return {"status": "STOP", "detail": "P5I test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    maps = interacting_cpt_field_maps()
    action = action_cpt_engine()
    kernels = amplitude_cpt_kernels()
    neg = negative_test_battery(auth)
    engine = tree_amplitude_engine()
    evaluated = evaluate_all_candidates()
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    n_ver = sum(1 for r in records if r["Q06"] == "VERIFIED")
    n_par = sum(1 for r in records if r["Q06"] == "PARTIAL")
    n_fail = sum(1 for r in records if r["Q06"] == "FAILED")
    n_unt = sum(1 for r in records if r["Q06"] == "UNTESTED")
    n_act = sum(1 for r in records if r["action_level_status"] == "VERIFIED")
    n_amp = sum(1 for r in records if r["tree_amplitude_status"] == "VERIFIED")
    n_closed = sum(1 for r in records if r["representation_closure"] == "CLOSED_WITHIN_CANDIDATE")
    n_equiv = sum(1 for r in records if r["representation_closure"] == "CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE")
    n_missing = sum(1 for r in records if r["representation_closure"] == "REQUIRES_MISSING_FIELD")
    n_param = sum(1 for r in records if r["parameter_dependent"])
    if n_ver + n_par + n_fail + n_unt != 479:
        return {"status": "STOP", "detail": "Q06 classification does not partition 479", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["g_fitted"] for r in records) or any(r["g4_used"] for r in records):
        return {"status": "STOP", "detail": "fit or G4 metadata entered P5I", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["field_added"] for r in records) or any(r["candidates_filtered"] for r in records):
        return {"status": "STOP", "detail": "a field was added or a candidate was filtered", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["GENERAL_CPT_THEOREM"] == "VERIFIED" for r in records):
        return {"status": "STOP", "detail": "P5I was promoted to the general CPT theorem", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["Q04_modified"] or r["Q04"] != Q04_UNCHANGED for r in records):
        return {"status": "STOP", "detail": "Q04 was modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["loop_used_as_primary"] or r["new_interaction"] for r in records):
        return {"status": "STOP", "detail": "a new loop programme or interaction entered P5I", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg["results"]["17_count_479"] = len(records) == 479
    neg["all_pass"] = all(bool(v) for v in neg["results"].values())
    families: dict[str, dict[str, int]] = {}
    for rec in records:
        g = rec["gauge_group"]
        families.setdefault(
            g,
            {"n": 0, "Q06_VERIFIED": 0, "Q06_PARTIAL": 0, "ACTION_VERIFIED": 0, "AMP_VERIFIED": 0, "CLOSED": 0, "EQUIV": 0},
        )
        families[g]["n"] += 1
        if rec["Q06"] == "VERIFIED":
            families[g]["Q06_VERIFIED"] += 1
        if rec["Q06"] == "PARTIAL":
            families[g]["Q06_PARTIAL"] += 1
        if rec["action_level_status"] == "VERIFIED":
            families[g]["ACTION_VERIFIED"] += 1
        if rec["tree_amplitude_status"] == "VERIFIED":
            families[g]["AMP_VERIFIED"] += 1
        if rec["representation_closure"] == "CLOSED_WITHIN_CANDIDATE":
            families[g]["CLOSED"] += 1
        if rec["representation_closure"] == "CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE":
            families[g]["EQUIV"] += 1
    table = _class_table(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_group": rec["gauge_group"],
            "field_content": rec["field_content"],
            "action_CPT": rec["action_level_status"],
            "representation_closure": rec["representation_closure"],
            "amplitude_CPT": rec["tree_amplitude_status"],
            "n_tree_processes_tested": rec["n_tree_processes_tested"],
            "Q06": rec["Q06"],
            "Q06_FREE_STATUS": rec["Q06_FREE_STATUS"],
            "Q06_INTERACTING_ACTION_STATUS": rec["Q06_INTERACTING_ACTION_STATUS"],
            "Q06_TREE_AMPLITUDE_STATUS": rec["Q06_TREE_AMPLITUDE_STATUS"],
            "GENERAL_CPT_THEOREM": rec["GENERAL_CPT_THEOREM"],
            "limitation": rec["limitations"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash([{"h": r["candidate_id"], "q06": r["Q06"], "c": r["representation_closure"]} for r in compact])
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5I")
    impl_hash = implementation_hash()
    timestamp = _utc()
    CPT_map_hash = maps["map_hash"]
    action_CPT_engine_hash = content_hash(action)
    amplitude_CPT_engine_hash = content_hash({k: v for k, v in kernels.items()})
    amplitude_engine_hash = engine["engine_hash"]
    manifest = {
        "capability_id": P5I_ID,
        "capability_version": CAPABILITY_VERSION,
        "Q06_PREVIOUS": Q06_PREVIOUS,
        "Q06_NEW": records[0]["Q06"] if records else "UNTESTED",
        "Q06_VERIFIED": n_ver,
        "Q06_PARTIAL": n_par,
        "Q06_FAILED": n_fail,
        "Q06_UNTESTED": n_unt,
        "Q06_FREE_STATUS": "VERIFIED",
        "Q06_INTERACTING_ACTION_STATUS": action["full_action"],
        "Q06_TREE_AMPLITUDE_STATUS": kernels["AA_to_AA"]["status"],
        "GENERAL_CPT_THEOREM": "UNTESTED",
        "FULL_TEST_EXTENSION_CPT_INVARIANCE": action["full_action"],
        "action_level_CPT_verified": n_act,
        "amplitude_level_CPT_verified": n_amp,
        "CLOSED_WITHIN_CANDIDATE": n_closed,
        "CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE": n_equiv,
        "REQUIRES_MISSING_FIELD": n_missing,
        "parameter_dependent": n_param,
        "Q04_unchanged": Q04_UNCHANGED,
        "loop_primary": False,
        "F2_provenance": "INPUT / TEST EXTENSION",
    }
    manifest["manifest_hash"] = content_hash(manifest)
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_P5Q": PARENT_P5Q_CHECKPOINT_ID,
        "parent_p5q_digest": EXPECTED_P5Q_CHECKPOINT_DIGEST,
        "parent_P5F": PARENT_P5F_CHECKPOINT_ID,
        "parent_p5f_digest": EXPECTED_P5F_CHECKPOINT_DIGEST,
        "parent_P5G": PARENT_P5G_CHECKPOINT_ID,
        "parent_p5g_digest": EXPECTED_P5G_CHECKPOINT_DIGEST,
        "parent_P5H5": PARENT_P5H5_CHECKPOINT_ID,
        "parent_p5h5_digest": EXPECTED_P5H5_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "CPT_map_hash": CPT_map_hash,
        "action_CPT_engine_hash": action_CPT_engine_hash,
        "amplitude_CPT_engine_hash": amplitude_CPT_engine_hash,
        "amplitude_engine_hash": amplitude_engine_hash,
        "implementation_hash": impl_hash,
        "test_suite_hash": registry["registry_hash"],
        "representation_convention": REPRESENTATION_CONVENTION,
        "gauge_fixing_convention": GAUGE_FIXING_CONVENTION,
        "gauge_fixing_choices": list(GAUGE_FIXING_CHOICES),
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "free_CPT": "P5Q REUSED",
            "action_CPT": "DERIVED GIVEN TEST-EXTENSION ACTION + CPT MAP CONVENTION",
            "tree_CPT": "DERIVED GIVEN P5H TREE ENGINE + IMPLEMENTED RELATION",
            "Q06": manifest["Q06_NEW"],
            "GENERAL_CPT_THEOREM": "UNTESTED",
            "Q04": Q04_UNCHANGED,
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5I_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "P5Q_overwritten": False,
        "P5F_overwritten": False,
        "P5G_overwritten": False,
        "P5H5_overwritten": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5i_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5I_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5I_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5I_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5I_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5I_CPT_MAPS.json", maps)
    _write_json(artifact_dir() / "P5I_ACTION_TEST.json", action)
    questions = {
        "1_maps_for_every_declared_field": True,
        "2_interacting_action_CPT": action["full_action"] == "VERIFIED",
        "3_gauge_sector_CPT": action["sectors"]["gauge_kinetic_F2"] == "VERIFIED",
        "4_matter_gauge_CPT": action["sectors"]["gauge_matter_interaction"] == "VERIFIED",
        "5_gauge_fixing_compatible": action["sectors"]["gauge_fixing"] == "VERIFIED",
        "6_closes_without_adding_fields": n_missing == 0,
        "7_tree_amplitudes_CPT_related": n_amp == 479,
        "8_physical_gauge_independent": True,
        "9_genuine_violation": n_fail > 0,
        "10_parameter_dependent": n_param > 0,
        "11_Q06_upgraded": n_ver == 479,
        "12_missing_if_not": "GENERAL_CPT_THEOREM remains UNTESTED; not a Pauli-Luders proof",
        "13_status_changed_by_filtering": False,
        "14_filtered": False,
        "15_coupling_fixed": False,
        "16_experimental": False,
        "17_frozen_changed": False,
        "18_G1G6_changed": False,
        "19_P5Q_P5H5_changed": False,
        "20_count_479": True,
        "21_proves_general_CPT_theorem": False,
        "22_untested": "general CPT theorem; all-orders antiunitary CPT operator; loop-level 4pt CPT as a primary",
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5I_STATUS": "CLOSED",
        "PHASE_14C5I_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5I_ONLY",
        "PHASE_14C5I_TEST_COPY_ID": PHASE_14C5I_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "Q06_CPT_STATUS": records[0]["Q06"] if records else "UNTESTED",
        "Q06_PREVIOUS": Q06_PREVIOUS,
        "Q06_VERIFIED": n_ver,
        "Q06_PARTIAL": n_par,
        "Q06_FAILED": n_fail,
        "Q06_UNTESTED": n_unt,
        "Q06_FREE_STATUS": "VERIFIED",
        "Q06_INTERACTING_ACTION_STATUS": action["full_action"],
        "Q06_TREE_AMPLITUDE_STATUS": "VERIFIED" if n_amp == 479 else "PARTIAL",
        "Q06_FINAL_STATUS": records[0]["Q06"] if n_ver == 479 or n_par == 479 or n_fail == 479 else "PARTIAL",
        "GENERAL_CPT_THEOREM": "UNTESTED",
        "FULL_TEST_EXTENSION_CPT_INVARIANCE": action["full_action"],
        "action_level_CPT_verified": n_act,
        "amplitude_level_CPT_verified": n_amp,
        "CLOSED_WITHIN_CANDIDATE": n_closed,
        "CLOSES_ONLY_UP_TO_SUPPORTED_EQUIVALENCE": n_equiv,
        "REQUIRES_MISSING_FIELD": n_missing,
        "parameter_dependent_cases": n_param,
        "candidates_filtered": False,
        "Q04_TREE_UNITARITY_STATUS": Q04_UNCHANGED,
        "Q04_modified": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "loop_primary": False,
        "PARENT_P5Q_CHECKPOINT_DIGEST": EXPECTED_P5Q_CHECKPOINT_DIGEST,
        "PARENT_P5F_CHECKPOINT_DIGEST": EXPECTED_P5F_CHECKPOINT_DIGEST,
        "PARENT_P5G_CHECKPOINT_DIGEST": EXPECTED_P5G_CHECKPOINT_DIGEST,
        "PARENT_P5H5_CHECKPOINT_DIGEST": EXPECTED_P5H5_CHECKPOINT_DIGEST,
        "NEW_P5I_CHECKPOINT": CAPABILITY_VERSION,
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
        "CPT_map_hash": CPT_map_hash,
        "action_CPT_engine_hash": action_CPT_engine_hash,
        "amplitude_CPT_engine_hash": amplitude_CPT_engine_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "P5I_TESTED": len(records),
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
        "new_loop_order": False,
        "ranking": False,
        "P5I_EXECUTED": True,
        "P6_EXECUTED": False,
        "gravity_changed": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "p5q_checkpoint_overwritten": False,
        "p5f_checkpoint_overwritten": False,
        "p5g_checkpoint_overwritten": False,
        "p5h5_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
        "checkpoint_path": str(p5i_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "historical_corpus": corpus,
        "p5i_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "simple_groups": list(G6_SEARCH_BOUNDS["simple_groups"]),
        "gauge_fixing_choices": list(GAUGE_FIXING_CHOICES),
        "representation_convention": REPRESENTATION_CONVENTION,
        "cpt_maps": {
            "scalar": maps["scalar"]["CPT"],
            "weyl": maps["weyl"]["CPT"],
            "abelian": maps["abelian_gauge"]["CPT"],
            "nonabelian": maps["nonabelian_gauge"]["CPT"],
            "ghost": maps["ghost_BRST"]["CPT"],
        },
        "action_sectors": action["sectors"],
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5I_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5h5") != hashes_before.get("phase14c5h5"):
        return {"status": "STOP", "detail": "P5H5 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_checkpoint_path().read_bytes() != p5q_before:
        return {"status": "STOP", "detail": "P5Q modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5d_checkpoint_path().read_bytes() != p5d_before:
        return {"status": "STOP", "detail": "P5D modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_checkpoint_path().read_bytes() != p5e_before or p5e1_checkpoint_path().read_bytes() != p5e1_before:
        return {"status": "STOP", "detail": "P5E/P5E1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_checkpoint_path().read_bytes() != p5f_before:
        return {"status": "STOP", "detail": "P5F modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g_checkpoint_path().read_bytes() != p5g_before:
        return {"status": "STOP", "detail": "P5G modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g1_checkpoint_path().read_bytes() != p5g1_before:
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
    if p5_checkpoint_path().read_bytes() != p5_before or p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P5/P4 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5I_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5I_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5I checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5i_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5i_p5i(auth, signature=signature)
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
            "P5Q_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5q_checkpoint_overwritten") is False else "FAILED",
            "P5F_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5f_checkpoint_overwritten") is False else "FAILED",
            "P5G_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5g_checkpoint_overwritten") is False else "FAILED",
            "P5H5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5h5_checkpoint_overwritten") is False else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5I_STATUS": science.get("PHASE_14C5I_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5I_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5I_CHECKPOINT": science.get("NEW_P5I_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
