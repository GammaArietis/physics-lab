"""Phase 11AH.1: frozen equations do not force F proportional to Phi."""

from __future__ import annotations

from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ah_t06_containment import CLOSURE_TARGET, run_containment_audit_T06


def test_wrong_target_is_refused_before_the_scan():
    refused = run_containment_audit_T06("F_EQUALS_PHI")
    assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
    assert refused["scanned"] is False
    assert refused["T06_activated"] is False
    assert refused["provenance_log"][0]["accepted"] is False


def test_t06_audit_does_not_derive_proportionality():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    gate = phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json"
    gate_before = gate.read_bytes()
    out = run_containment_audit_T06(write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert gate.read_bytes() == gate_before
    assert out["status"] == "OK"
    assert out["topic"] == "T06: F proportional to Phi"
    assert out["provenance_log"][0]["rule"] == "Target-Blind rule"
    assert out["provenance_log"][0]["closure_target"] == CLOSURE_TARGET == "PROPORTIONALITY_DERIVED"
    assert out["provenance_log"][0]["logged_before_logical_execution"] is True
    assert out["closure_target_used_as_filter"] is False
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["new_parameter_count"] == 0
    assert out["frozen_action_modified"] is False
    assert out["definitions_modified"] is False
    assert out["T06_activated"] is False
    assert out["Provenance"] == "NOT_FOUND"
    assert out["PROPORTIONALITY_STATUS"] == "NOT_FOUND"
    assert {row["probe"]: row["Provenance"] for row in out["probes"]} == {
        "eom_4d": "NOT_FOUND",
        "z2_moduli": "NOT_FOUND",
        "bianchi_identity": "NOT_FOUND",
        "field_definitions": "NOT_FOUND",
    }
    eom = out["probes"][0]["evidence"]
    assert eom["equations_linking_F_and_Phi"] == []
    assert eom["gauge_equation_present"] is True
    moduli = out["probes"][1]["evidence"]
    assert moduli["symmetry"] == "Z_2"
    assert moduli["surviving_class"] == [[-1, -1], [1, 1]]
    assert moduli["class_mentions_F"] is False
    bianchi = out["probes"][2]["evidence"]
    assert bianchi["bianchi_holds_identically"] is True
    assert bianchi["new_parameter_relation"] is False
    assert bianchi["constrains_lambda"] is False
    fields = out["probes"][3]["evidence"]
    assert fields["F_definition"] == "F_mu_nu = d_mu mathcalA_nu - d_nu mathcalA_mu"
    assert fields["F_X_not_F_phi"] is True
    assert fields["proportion_forced_by_definitions"] is False
    assert fields["lam_a_provenance"] == "INPUT"
    assert "Phi" in fields["frozen_field_ids"]
