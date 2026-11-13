"""Phase 12E family-audit tests. No search and no physical activation."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12e_family_audit import (
    ARTIFACT_DIR_NAME,
    run_large_scale_search,
    run_phase_12e,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {
        key: value
        for key, value in snapshot_existing_phases().items()
        if not key.startswith(ARTIFACT_DIR_NAME)
    }


def test_phase12e_audits_families_without_activation() -> None:
    before = _prior()
    result = run_phase_12e(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_12E_STATUS"] == "COMPLETE"
    assert result["FAMILY_AUDIT_STATUS"] == "VERIFIED"
    assert result["HORIZONTAL_EXPANSION_STATUS"] == "PARTIAL"
    assert result["FAMILY_REGISTRATION_STATUS"] == "VERIFIED"
    assert result["PHYSICAL_PRINCIPLE_FIREWALL_STATUS"] == "VERIFIED"
    assert result["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert result["PARAMETER_ISOLATION_STATUS"] == "VERIFIED"
    assert result["EQUIVALENCE_STATUS"] == "PARTIAL"
    assert result["FINITE_BOUND_STATUS"] == "PARTIAL"
    assert result["RESOURCE_AUDIT_STATUS"] == "VERIFIED"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["SEARCH_EXECUTED"] is False
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["PROPOSED_GRAMMAR_VERSION"] == "NOT_CREATED"
    assert result["grammar_version_created"] is False
    assert result["new_physical_principle_activated"] is False
    assert result["blind_computation_restarted"] is False
    assert result["vertical_expansion"] == "NOT AUTHORIZED"
    assert result["decision"]["ACTIVATABLE_FAMILIES"] == []
    assert result["decision"]["READY_FOR_REGISTRATION"] == []
    assert "candidate.vacuum_selection" in result["decision"]["NEW_PHYSICAL_PRINCIPLE_REQUIRED"]
    assert "candidate.modulus_stabilization" in result["decision"]["NEW_PHYSICAL_PRINCIPLE_REQUIRED"]
    assert "candidate.flux_stabilization" in result["decision"]["NEW_PHYSICAL_PRINCIPLE_REQUIRED"]
    assert "candidate.hidden_sector" in result["decision"]["NEW_PHYSICAL_PRINCIPLE_REQUIRED"]
    assert result["absolute_coupling_fixed_by_label"] is False
    operational = [row for row in result["family_report"] if row["operational_status"] == "OPERATIONAL"]
    assert operational
    assert all(row["eligibility"] == "ALREADY_OPERATIONAL" for row in operational)
    assert all(row["new_physical_principle_required"] is False for row in operational)
    assert all(row["finite_bound_status"] == "FINITE" for row in operational)
    blocked = [row for row in result["family_report"] if row["operational_status"] == "NOT_REGISTERED"]
    assert blocked
    assert all(row["eligibility"] != "READY_FOR_REGISTRATION" for row in result["family_report"])
    assert {item["proof_status"] for item in result["cross_family_relations"]} == {"EQUIVALENCE_UNSUPPORTED"}
    assert result["resource_estimate"]["search_executed"] is False
    assert result["resource_estimate"]["additional_candidates_generated"] == 0
    assert result["resource_estimate"]["ranking_used"] is False
    assert [item["observed"] for item in result["dry_run"]] == [item["expected"] for item in result["dry_run"]]
    assert len(result["dry_run"]) == 15
    try:
        run_large_scale_search()
    except RuntimeError as exc:
        assert "refuses" in str(exc)
    else:
        raise AssertionError("search was not refused")
