"""Phase 13E materialization audit. No action is assembled."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase13e_materialization import ARTIFACT_DIR_NAME, _physics_dir, run_phase_13e
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase13e_audits_existing_action_records() -> None:
    before = _prior()
    result = run_phase_13e(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_13E_STATUS"] == "COMPLETE"
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["MATERIALIZATION_RULE_STATUS"] == "ABSENT"
    assert result["ACTION_MATERIALIZATION_STATUS"] == "PARTIAL"
    assert result["FIELD_CONTENT_MATERIALIZATION_STATUS"] == "UNRESOLVED"
    assert result["GAUGE_MATERIALIZATION_STATUS"] == "UNRESOLVED"
    assert result["INTERNAL_OPERATOR_MATERIALIZATION_STATUS"] == "UNRESOLVED"
    assert result["PARAMETER_IDENTITY_STATUS"] == "PARTIAL"
    assert result["COMPOSITION_SEMANTICS_STATUS"] == "ABSENT"
    assert result["NEW_INTEGRAND_REQUIRED"] is False
    assert result["NEW_PHYSICAL_CONTENT"] == "NONE"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["AUDIT"]["parent"]["action_hash"] == FROZEN_4C_HASH
    assert {item["id"] for item in result["AUDIT"]["parent"]["fields"]} == {"Phi", "metric"}
    coefficients = set(result["AUDIT"]["parent"]["coefficients"])
    assert {"c0", "c1", "Z", "kappa", "c_H", "lam_a", "lam_b"} <= coefficients
    assert all(item["ACTION_MATERIALIZATION"] == "PARTIAL" for item in result["AUDIT"]["per_theory"])
    assert all(item["critical_outcome"] == "MATERIALIZATION_RULE_MISSING" for item in result["AUDIT"]["per_theory"])
    assert result["AUDIT"]["composition"]["proposal"]["implemented"] is False
    assert len(result["dry_run_negatives"]) == 18
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_13E_ACTION_COMPONENT_INVENTORY.json",
        "PHASE_13E_AXIS_ACTION_MAPPING.json",
        "PHASE_13E_MATERIALIZATION_AUDIT.json",
        "PHASE_13E_PARAMETER_IDENTITY_AUDIT.json",
        "PHASE_13E_COMPOSITION_SEMANTICS.json",
        "PHASE_13E_FRONTIER.json",
        "SEARCH_MANIFEST_13E.json",
    ):
        assert (destination / name).is_file()
