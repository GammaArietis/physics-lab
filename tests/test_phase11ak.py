"""Phase 11AK: the frozen theory does not supply a UV completion."""

from __future__ import annotations

from physics_lab.core.provenance import Provenance
from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ak_uv_completion import (
    AUDIT_CLOSURE_TARGET,
    EXECUTION_CLOSURE_TARGET,
    UV_FORMULA,
    FrozenAuthorizationError,
    UVCompletionAuthorization,
    run_containment_audit_T12,
    run_phase_11AK_2_execution,
)


def test_wrong_uv_target_is_refused_before_the_scan():
    refused = run_containment_audit_T12("PLANCK_EQUALS_MASS")
    assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
    assert refused["scanned"] is False
    assert refused["T12_activated"] is False


def test_uv_audit_is_not_found_and_the_cutoff_does_not_fix_parameters():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    audit = run_containment_audit_T12(write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert audit["status"] == "OK"
    assert audit["provenance_log"][0]["closure_target"] == AUDIT_CLOSURE_TARGET == "UV_COMPLETION_DERIVED"
    assert audit["provenance_log"][0]["logged_before_logical_execution"] is True
    assert audit["Provenance"] == "NOT_FOUND"
    assert audit["UV_COMPLETION_STATUS"] == "NOT_FOUND"
    assert audit["new_parameter_count"] == 0
    assert audit["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert {row["probe"]: row["Provenance"] for row in audit["probes"]} == {
        "frozen_action": "NOT_FOUND",
        "gravity_4a_4b": "NOT_FOUND",
        "moduli_and_eom": "NOT_FOUND",
    }
    assert audit["probes"][0]["evidence"]["planck_in_freeze"] is False
    assert audit["probes"][0]["evidence"]["c0_FREE"] is True
    assert audit["probes"][1]["evidence"]["newton_G_used_to_fix_c1"] is False
    assert audit["probes"][1]["evidence"]["m_eff2_without_free_parameters"] == "NO"
    assert audit["probes"][2]["evidence"]["moduli_depend_on_planck"] is False
    assert audit["probes"][2]["evidence"]["equations_naming_planck"] == []
    auth = UVCompletionAuthorization()
    assert auth.phase == "PHASE_11AK.2"
    assert auth.gate == "HUMAN-DECLARED NEW PHYSICAL INPUT"
    assert auth.provenance == Provenance.ASSUMED.value
    assert auth.principle == "String-Scale UV Cutoff T12"
    assert auth.formula == UV_FORMULA
    assert auth.theoretical_scope == "STRING_EFFECTIVE_THEORY"
    try:
        auth.formula = "ALTERED"
    except FrozenAuthorizationError:
        pass
    else:
        raise AssertionError("sealed formula accepted a later assignment")
    refused = run_phase_11AK_2_execution(object())
    assert refused["status"] == "STOP"
    assert refused["provenance_log"][2]["closure_target"] == EXECUTION_CLOSURE_TARGET
    out = run_phase_11AK_2_execution(auth, write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert out["status"] == "OK"
    assert out["Provenance"] == "ASSUMED"
    assert out["classification"] == "NEW PHYSICAL INPUT"
    assert out["derived"] is False
    assert out["previous_audit_provenance"] == "NOT_FOUND"
    assert out["frozen_action_modified"] is False
    assert out["new_parameter_count"] == 0
    analysis = out["analysis"]
    assert analysis["action_substitution_sites"] == 0
    assert analysis["orbit_product_common"] is True
    assert analysis["Lambda_UV_is_number"] is False
    assert analysis["M_Planck_remains_free"] is True
    assert analysis["mass_depends_on_cutoff"] is False
    assert analysis["mass_charge_ratio_unchanged"] is True
    assert analysis["mass_charge_ratio_parameter_free"] is False
    assert analysis["charge_fixed_to_number"] is False
    assert analysis["parameters_removed"] == 0
    assert analysis["M_Planck_added_to_frozen_parameter_list"] is False
    assert out["parameter_free_relation"] is False
    assert out["observed"] == "RELATION_NOT_DERIVED"
    assert out["PROGRAM_CLOSURE_STATUS"] == "RELATION_NOT_DERIVED"
    names = [item["entry"] for item in out["provenance_log"]]
    assert names.index("Pre-Execution Closure Criterion") < names.index("UV cutoff on execution copy")
