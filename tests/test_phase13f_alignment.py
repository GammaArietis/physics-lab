"""Phase 13F alignment tests. The automatic path stops when a map is uncertified."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase13f_alignment import ARTIFACT_DIR_NAME, _physics_dir, run_phase_13f
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase13f_stops_when_alignment_is_uncertified() -> None:
    before = _prior()
    result = run_phase_13f(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_13F_STATUS"] == "COMPLETE"
    assert result["SEMANTIC_ALIGNMENT_STATUS"] == "BLOCKED"
    assert result["NEW_COMPOSITION_SEMANTICS_REQUIRED"] is True
    assert result["NEW_PHYSICAL_CONTENT"] == "NONE"
    assert result["CURRENT_AUTOMATIC_PATH_EXHAUSTED"] is True
    assert result["AUTOMATIC_PATH_TERMINATED"] is True
    assert result["EXISTING_COMPOSITION_SEMANTICS"] == "ABSENT"
    assert result["ACTION_ASSEMBLY_DRYRUN_STATUS"] == "UNRESOLVED"
    assert result["SEARCH_EXECUTED"] is False
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    rows = result["ALIGNMENT"]["rows"]
    assert rows
    assert not any(item["mapping_status"] == "CERTIFIED_EXACT_MATCH" for item in rows)
    assert not any(item["mapping_status"] == "CERTIFIED_EQUIVALENT_MATCH" for item in rows)
    identities = { (item["left"], item["right"]): item["status"] for item in result["ALIGNMENT"]["identities"] }
    assert identities[("lambda_a", "lam_a")] == "PARAMETER_IDENTITY_UNCERTIFIED"
    assert identities[("lambda_b", "lam_b")] == "PARAMETER_IDENTITY_UNCERTIFIED"
    assert all(item["persisted"] is False and item["included_terms"] == [] for item in result["ALIGNMENT"]["dry_run"])
    assert len(result["dry_run_negatives"]) == 22
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    assert not (_physics_dir() / "phase13g_alignment_artifacts").exists()
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_13F_AXIS_ACTION_ALIGNMENT.json",
        "PHASE_13F_PARAMETER_IDENTITY_ALIGNMENT.json",
        "PHASE_13F_ACTION_ASSEMBLY_DRYRUN.json",
        "PHASE_13F_COMPOSITION_SEMANTICS.json",
        "PHASE_13F_FRONTIER.json",
        "SEARCH_MANIFEST_13F.json",
    ):
        assert (destination / name).is_file()
