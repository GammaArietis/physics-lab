from __future__ import annotations

from physics_lab.search.w11_ir_eft_rescue import _run_one_loop_coupling, run_ir_eft_rescue_campaign


def test_zero_gauge_coupling_is_protected_by_multiplicative_flow() -> None:
    result = _run_one_loop_coupling(0.0, 41.0 / 10.0, 246.21965, 2.0)
    assert result["status"] == "ZERO_PROTECTED"
    assert result["output"] == 0.0


def test_nonzero_coupling_runs_without_additive_seed() -> None:
    result = _run_one_loop_coupling(0.02, 41.0 / 10.0, 246.21965, 2.0)
    assert result["status"] == "COMPLETE"
    assert result["output"] > 0.0


def test_campaign_records_non_eligible_case(tmp_path) -> None:
    import gzip
    import json

    archive = tmp_path / "archive.json.gz"
    with gzip.open(archive, "wt", encoding="utf-8") as handle:
        json.dump({"cases": [{"case_id": "bad", "status": "BOUND_REACHED", "error": "bound"}]}, handle)
    report = run_ir_eft_rescue_campaign(archive_path=archive)
    assert report["scan"]["status_counts"] == {"NOT_ELIGIBLE": 1}
    assert report["scan"]["known_eft_rescue_count"] == 0
