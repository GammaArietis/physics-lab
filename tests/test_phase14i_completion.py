"""Phase 14I completes the authorized test action and leaves the freeze unchanged."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14i_completion import (
    ARTIFACT_DIR_NAME,
    CURRENT_FORMULA,
    KINETIC_DENSITY,
    PROVENANCE,
    _physics_dir,
    run_phase_14i,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14i_completes_the_authorized_test_action() -> None:
    before = _prior()
    result = run_phase_14i(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14I_STATUS"] == "COMPLETE"
    assert result["AUTHORIZATION_STATUS"] == PROVENANCE
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["FROZEN_ACTION_MODIFIED"] is False
    assert result["ACTION_FREEZE_VERIFIED"] is True
    assert result["ACTION_DERIVATION_READY"] is True
    assert result["F2_A_MU_DEPENDENCY"] == "DECLARED"
    assert result["PHASE_14I_EOM_STATUS"] == "READY_FOR_NEXT_PHASE"
    assert result["FULL_ACTION_SYMMETRY_STATUS"] == "PENDING_REVERIFICATION"
    assert result["FREEZE_STATUS"] == "VERIFIED"
    assert result["ACTION_COMPLETION_STATUS"] == "VERIFIED"
    assert result["F2_DEPENDENCY_STATUS"] == "VERIFIED"
    assert result["PROVENANCE_STATUS"] == "VERIFIED"
    assert result["NO_GRAVITY_CHANGE"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["EOM_EXECUTED"] is False
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["ACTION_HASH_BEFORE"] != result["ACTION_HASH_AFTER"]
    assert result["CURRENT_DEFINITION"] == "REUSED FROM PHASE_5B.0"
    assert result["CURRENT_RELATION_TO_GAUGED_ACTION"] == "DERIVED GIVEN HUMAN-AUTHORIZED ACTION COMPLETION"
    expansion = result["completion"]["expansion"]
    assert expansion["status"] == "EXACT"
    assert expansion["match"] is True
    assert expansion["current_formula"] == CURRENT_FORMULA
    assert expansion["current_coefficient"] == 2
    assert expansion["k_antisymmetric"] is True
    actions = result["completion"]["actions"]
    assert len(actions) == 4
    assert all(item["kinetic_density"] == KINETIC_DENSITY for item in actions)
    assert all(item["provenance"] == PROVENANCE for item in actions)
    assert all(item["derived_independently"] is False for item in actions)
    assert all(item["strict_provenance"] == "NOT_DERIVED_FROM_THE_FROZEN_ACTION" for item in actions)
    assert all(item["frozen_promoted"] is False for item in actions)
    f2 = [item for item in actions if item["f2_term"] != "ABSENT"]
    plain = [item for item in actions if item["f2_term"] == "ABSENT"]
    assert len(f2) == 2 and len(plain) == 2
    assert all(item["f2_a_mu_dependency"] == "DECLARED" and "Z_A" in item["parameters"] and "F_mu_nu" in item["fields"] for item in f2)
    assert all("Z_A" not in item["parameters"] and "F_mu_nu" not in item["fields"] for item in plain)
    assert len(result["dry_run_negatives"]) == 15
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14I_ACTION_COMPLETION.json",
        "PHASE_14I_EXPANSION.json",
        "PHASE_14I_CURRENT.json",
        "PHASE_14I_F2_COMPLETION.json",
        "PHASE_14I_PROVENANCE.json",
        "PHASE_14I_FIELD_PARAMETER.json",
        "PHASE_14I_FRONTIER.json",
        "SEARCH_MANIFEST_14I.json",
    ):
        assert (destination / name).is_file()
