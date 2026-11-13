"""Phase 14D activates the thirty-two authorized bindings and materializes test actions."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14d_materialization import (
    ARTIFACT_DIR_NAME,
    AUTHORIZATION_ID,
    AUTHORIZATION_PROVENANCE,
    _physics_dir,
    run_phase_14d,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14d_materializes_authorized_bindings_only() -> None:
    before = _prior()
    result = run_phase_14d(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14D_STATUS"] == "COMPLETE"
    assert result["AUTHORIZATION_STATUS"] == "VERIFIED"
    assert result["AUTHORIZATION_ID"] == AUTHORIZATION_ID
    assert result["ACTIVATED_BINDING_COUNT"] == 32
    assert result["NOT_READY_BINDING_COUNT"] == 4
    assert result["ACTION_TEMPLATE_STATUS"] == "VERIFIED"
    assert result["ACTION_MATERIALIZATION_STATUS"] == "PARTIAL"
    assert result["COMPLETE_ACTION_COUNT"] == 4
    assert result["PARTIAL_ACTION_COUNT"] == 0
    assert result["UNRESOLVED_ACTION_COUNT"] == 4
    assert result["NEW_INTEGRAND"] is False
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["NEW_FIELD_COUNT"] == 0
    assert result["NEW_PHYSICAL_CONTENT"] == "NONE"
    assert result["PARAMETER_IDENTITY_STATUS"] == "HUMAN-AUTHORIZED"
    assert result["GAUGE_BINDING_STATUS"] == "PARTIAL"
    assert result["OPERATOR_BINDING_STATUS"] == "VERIFIED"
    assert result["OPERATOR_EXPRESSION_MATCH"] == "VERIFIED"
    assert result["GRAVITY_BINDING_STATUS"] == "VERIFIED"
    assert result["MATTER_BINDING_STATUS"] == "VERIFIED"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["EOM_EXECUTED"] is False
    assert result["SEARCH_EXECUTED"] is False
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["REPRODUCIBILITY_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
    assert result["LEXICON_HASH"] == "12ca8091fd7177191124bc842f0575dc5a5f353709b26d0ebb059934a9301fba"
    assert all(item["classification"] == AUTHORIZATION_PROVENANCE for item in result["ACTIVATED"])
    assert all(item["physical_relation"] == "NOT_DERIVED" and item["provenance_relabelled"] is False for item in result["ACTIVATED"])
    assert {item["selected_value"] for item in result["ACTIVATED"]} == {
        "volume_plus_ricci",
        "commutant_symmetric_K",
        "function_of_KTK",
        "connection_without_autonomous_F2",
        "optional_F2_test_extension",
        "matter_kinetic+matter_phi_sq",
    }
    assert all(item["activation"] == "NOT_ACTIVATED" and item["field_fabricated"] is False for item in result["INACTIVE"])
    actions = result["MATERIALIZATION"]["actions"]
    complete = [item for item in actions if item["status"] == "COMPLETE"]
    unresolved = [item for item in actions if item["status"] == "UNRESOLVED"]
    assert len(complete) == 4
    assert len(unresolved) == 4
    assert all(item["slot_checks"]["FIELD_CONTENT_SLOT"] is True for item in complete)
    assert all(all(item["slot_checks"].values()) for item in complete)
    assert all(item["materialized_action_hash"] != FROZEN_4C_HASH for item in complete)
    assert all(item["included_terms"] for item in complete)
    assert all(item["fields"] == ["Phi", "metric"] or set(item["fields"]) == {"Phi", "metric"} for item in complete)
    assert all("mathcalA_mu" not in item["fields"] for item in actions)
    assert all("Z_A" not in item["output_parameters"] for item in actions)
    assert all(item["included_terms"] == [] and item["fields"] == [] for item in unresolved)
    assert all(item["persisted_as_frozen_replacement"] is False for item in actions)
    assert result["operator_test"]["merged_with_lexicon"] is False
    assert result["operator_test"]["phase10d_status"] == "PHASE_10D_OPERATOR_FAMILY"
    gravity = [item for item in result["ACTIVATED"] if item["selected_value"] == "volume_plus_ricci"]
    assert all(item["source_provenance"] == "INPUT" and item["target_provenance"] == "ASSUMED" for item in gravity)
    assert len(result["dry_run_negatives"]) == 18
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14D_AUTHORIZATION_RECORD.json",
        "PHASE_14D_ACTIVATED_BINDINGS.json",
        "PHASE_14D_MATERIALIZED_ACTIONS.json",
        "PHASE_14D_ACTION_HASHES.json",
        "PHASE_14D_PARAMETER_AUDIT.json",
        "PHASE_14D_FRONTIER.json",
        "SEARCH_MANIFEST_14D.json",
    ):
        assert (destination / name).is_file()
