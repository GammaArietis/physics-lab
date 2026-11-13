"""Phase 14A lexicon tests. The bridge renames identifiers and adds no terms."""

from __future__ import annotations

from collections import Counter

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14a_lexicon import ARTIFACT_DIR_NAME, _physics_dir, run_phase_14a
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14a_applies_only_the_four_authorized_mappings() -> None:
    before = _prior()
    result = run_phase_14a(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14A_STATUS"] == "COMPLETE"
    assert result["LEXICON_STATUS"] == "VERIFIED"
    assert result["PARAMETER_IDENTITY_STATUS"] == "HUMAN-AUTHORIZED"
    assert result["ACTION_MATERIALIZATION_STATUS"] == "PARTIAL"
    assert result["NEW_INTEGRAND"] is False
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["NEW_PHYSICAL_CONTENT"] == "NONE"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["SEARCH_EXECUTED"] is False
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["PYTEST_STATUS"] == "GREEN"
    assert len(result["LEXICON"]["entries"]) == 4
    sources = {item["source_identifier"] for item in result["LEXICON"]["entries"]}
    assert sources == {"g_mu_nu", "A_mu", "lambda_a", "lambda_b"}
    assert all(item["provenance"] == "HUMAN-AUTHORIZED REPRESENTATIONAL ASSUMPTION" for item in result["LEXICON"]["entries"])
    counts = Counter(item["mapping_status"] for item in result["ALIGNMENT"]["rows"])
    previous = Counter(item["previous_status"] for item in result["ALIGNMENT"]["rows"])
    assert previous["PARTIAL_MATCH"] == 16
    assert previous["NO_MATCH"] == 64
    assert counts["CERTIFIED_EXACT_MATCH"] == 4
    assert counts["CERTIFIED_EQUIVALENT_MATCH"] == 0
    assert counts["NO_MATCH"] == 64
    exact = [item for item in result["ALIGNMENT"]["rows"] if item["mapping_status"] == "CERTIFIED_EXACT_MATCH"]
    assert {item["selected_value"] for item in exact} == {"metric_plus_internal_Phi"}
    assert all(item["derived_without_assumption"] is False for item in exact)
    assert all(item["mapping_status"] == "NO_MATCH" for item in result["ALIGNMENT"]["rows"] if item["selected_value"] == "function_of_KTK")
    assert all(item["mapping_status"] == "NO_MATCH" for item in result["ALIGNMENT"]["rows"] if item["selected_value"] == "optional_F2_test_extension")
    assert all(item["persisted"] is False for item in result["ALIGNMENT"]["dry_run"])
    assert len(result["dry_run_negatives"]) == 20
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14A_THEORY_IR_LEXICON.json",
        "PHASE_14A_LEXICON_HASH.json",
        "PHASE_14A_SEMANTIC_ALIGNMENT.json",
        "PHASE_14A_ACTION_MATERIALIZATION_DRYRUN.json",
        "PHASE_14A_PARAMETER_IDENTITY.json",
        "PHASE_14A_FRONTIER.json",
        "SEARCH_MANIFEST_14A.json",
    ):
        assert (destination / name).is_file()
