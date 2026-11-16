from __future__ import annotations

import json
import os
import stat

from physics_lab.search.gauge_yukawa_smdr_matching import (
    run_smdr_matching_campaign,
    w15_state_to_smdr_input,
)


def _candidate(status: str = "COMPLETE") -> dict:
    return {
        "candidate_id": "test-Q",
        "status": status,
        "final_state": [0.01, 0.02, 0.03, 0.05, 0.01, 0.004, 0.005, 0.001],
        "segments": [
            {
                "high_scale_gev": 1.0e16,
                "low_scale_gev": 1.0e8,
                "active_multiplicities": {"Q": 1},
            },
            {
                "high_scale_gev": 1.0e8,
                "low_scale_gev": 91.1876,
                "active_multiplicities": {"Q": 0},
            },
        ],
    }


def _fake_smdr(tmp_path):
    root = tmp_path / "SMDR"
    root.mkdir()
    executable = root / "calc_all"
    executable.write_text(
        "#!/bin/sh\n"
        "cat <<'EOF'\n"
        "SMDR (Standard Model in Dimensional Regularization) v1.3\n"
        "Mt = 172.4; Gammat = 1.3;\n"
        "Mh = 125.2; Gammah = 0.003;\n"
        "MZ = 91.1; GammaZ = 2.4;\n"
        "MW = 80.3; GammaW = 2.0;\n"
        "alpha = 1/137.03599918; GFermi = 1.16637820 10^-5;\n"
        "EOF\n"
    )
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    return root


def test_w15_mapping_is_explicit_and_does_not_hide_bsm_sector() -> None:
    text, metadata = w15_state_to_smdr_input(
        _candidate()["final_state"],
        scale_gev=91.1876,
        candidate=_candidate(),
    )
    assert "SMDR_gp_in = 0.007745966692414834" in text
    assert "SMDR_lambda_in = 0.004" in text
    assert metadata["new_sector_omitted_from_pure_smdr"] is True
    assert metadata["external_bsm_sector"] == ["yS", "lambda_s", "lambda_hs"]
    assert metadata["thresholds"]["thresholds_applied_before_smdr"] is True
    assert "SMDR_Mt_pole" not in text


def test_campaign_runs_target_blind_projection_without_selection(tmp_path) -> None:
    report = run_smdr_matching_campaign(
        {
            "pipeline_version": "test-w15",
            "scope": {"ir_scale_gev": 91.1876},
            "candidate_results": [_candidate()],
        },
        smdr_root=_fake_smdr(tmp_path),
    )
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["status_counts"] == {"SMDR_COMPLETE": 1}
    assert report["candidate_results"][0]["backend"]["parsed"]["w_pole_gev"] == 80.3
    assert report["controls"]["no_experimental_comparison"] is True
    assert report["selection"]["performed"] is False
    assert report["candidate_results"][0]["mapping"]["new_sector_omitted_from_pure_smdr"] is True


def test_backend_failure_is_recorded_per_candidate(tmp_path) -> None:
    report = run_smdr_matching_campaign(
        {
            "pipeline_version": "test-w15",
            "scope": {"ir_scale_gev": 91.1876},
            "candidate_results": [_candidate()],
        },
        smdr_root=tmp_path / "missing-SMDR",
    )
    result = report["candidate_results"][0]
    assert result["status"] == "BACKEND_FAILURE"
    assert report["execution_status"] == "COMPLETE"
    assert report["controls"]["all_selected_candidates_retained"] is True
