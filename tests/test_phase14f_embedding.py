"""Phase 14F embeds stored gauge expressions and leaves prior actions unchanged."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14f_embedding import ARTIFACT_DIR_NAME, D_MU, F2_CONTENTS, LINEAR, QUADRATIC, _physics_dir, run_phase_14f
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14f_embeds_authorized_component_expressions() -> None:
    before = _prior()
    result = run_phase_14f(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14F_STATUS"] == "COMPLETE"
    assert result["COMPONENT_EMBEDDING_STATUS"] == "VERIFIED"
    assert result["ACTION_MATERIALIZATION_V2_STATUS"] == "COMPLETE"
    assert result["FIELD_CLOSURE_STATUS"] == "VERIFIED"
    assert result["PARAMETER_CLOSURE_STATUS"] == "VERIFIED"
    assert result["GAUGE_COMPONENT_STATUS"] == "VERIFIED"
    assert result["F2_COMPONENT_STATUS"] == "VERIFIED"
    assert result["F2_FIELD_DEPENDENCY_STATUS"] == "UNDECLARED"
    assert result["INTERNAL_OPERATOR_STATUS"] == "VERIFIED"
    assert result["GRAVITY_COMPONENT_STATUS"] == "VERIFIED"
    assert result["COMPLETE_ACTION_COUNT"] == 4
    assert result["PARTIAL_ACTION_COUNT"] == 0
    assert result["UNRESOLVED_ACTION_COUNT"] == 0
    assert result["NEW_INTEGRAND_COUNT"] == 0
    assert result["NEW_FIELD_COUNT"] == 0
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["NEW_PHYSICAL_CONTENT"] == "NONE"
    assert result["EOM_EXECUTED"] is False
    assert result["SEARCH_EXECUTED"] is False
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["REPRODUCIBILITY_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["NUMBER_OF_CORRECTED_ACTIONS"] == 4
    assert result["NUMBER_OF_ACTIONS_WITH_EXPLICIT_GAUGE_FIELD"] == 4
    assert result["NUMBER_OF_ACTIONS_WITH_EXPLICIT_F2"] == 2
    assert result["NUMBER_OF_ACTIONS_WITH_COMPLETE_FIELD_CLOSURE"] == 4
    assert result["NUMBER_OF_ACTIONS_STILL_PARTIAL"] == 0
    assert result["NUMBER_OF_ACTIONS_STILL_UNRESOLVED"] == 0
    assert result["DISCREPANCY_STATUS"] == "RESOLVED_BY_COMPONENT_EMBEDDING"
    assert result["bundle"]["composition_mode_kinetic"] == "REPLACEMENT"
    assert result["bundle"]["composition_mode_f2"] == "ADDITION"
    actions = result["EMBEDDING"]["actions"]
    assert len(actions) == 4
    assert all({D_MU, LINEAR, QUADRATIC} <= {piece["expression"] for piece in item["embedded_terms"]} for item in actions)
    assert all("Z" in item["actual_parameters"] for item in actions)
    assert all(item["replaced_terms"] == ["matter_kinetic"] and item["duplicated_terms"] == [] for item in actions)
    assert all("mathcalA_mu" in item["actual_fields"] for item in actions)
    assert all(item["materialized_action_v2_hash"] != item["old_14d_hash"] for item in actions)
    assert all(item["gravity_registry_provenance"] == "INPUT" and item["gravity_term_provenance"] == "ASSUMED" for item in actions)
    assert all(item["operator_diagonal"] == ["lam_a", "lam_b", "lam_b"] for item in actions)
    assert all(item["phase10d_merged_with_lexicon"] is False for item in actions)
    f2 = [item for item in actions if item["f2_present_in_expression"] is True]
    plain = [item for item in actions if item["f2_present_in_expression"] is False]
    assert len(f2) == 2 and len(plain) == 2
    assert all(F2_CONTENTS in [piece["expression"] for piece in item["embedded_terms"]] for item in f2)
    assert all("Z_A" in item["actual_parameters"] and "F_mu_nu" in item["actual_fields"] for item in f2)
    assert all("Z_A" not in item["actual_parameters"] and item["f2_status"] == "ABSENT" for item in plain)
    assert all(item["f2_a_mu_dependency"] == "UNDECLARED" for item in actions)
    assert len(result["dry_run_negatives"]) == 20
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14F_COMPONENT_EMBEDDING.json",
        "PHASE_14F_MATERIALIZED_ACTIONS_V2.json",
        "PHASE_14F_FIELD_CLOSURE.json",
        "PHASE_14F_PARAMETER_CLOSURE.json",
        "PHASE_14F_F2_DEPENDENCY.json",
        "PHASE_14F_OPERATOR_EMBEDDING.json",
        "PHASE_14F_GRAVITY_EMBEDDING.json",
        "PHASE_14F_FRONTIER.json",
        "SEARCH_MANIFEST_14F.json",
    ):
        assert (destination / name).is_file()
