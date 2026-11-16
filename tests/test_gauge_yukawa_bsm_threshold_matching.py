from __future__ import annotations

import stat

import pytest

from physics_lab.search.gauge_yukawa_bsm_threshold_matching import (
    apply_one_loop_bsm_thresholds,
    run_bsm_threshold_matching_campaign,
    vectorlike_threshold_delta_b,
    w15_threshold_events,
)


def _candidate() -> dict:
    return {
        "candidate_id": "test-Q",
        "status": "COMPLETE",
        "final_state": [0.01, 0.02, 0.03, 0.05, 0.01, 0.004, 0.005, 0.001],
        "segments": [
            {"low_scale_gev": 1.0e8, "active_multiplicities": {"Q": 1}},
            {"low_scale_gev": 91.1876, "active_multiplicities": {"Q": 0}},
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


def test_w15_events_and_representation_delta_b_are_recovered() -> None:
    events = w15_threshold_events(_candidate())
    assert events == [{"multiplet": "Q", "multiplicity_decoupled": 1, "mass_gev": 1.0e8, "source_segment_index": 0}]
    delta = vectorlike_threshold_delta_b(events)
    assert delta == pytest.approx({"g1": 1.0 / 7.5, "g2": 2.0, "g3": 4.0 / 3.0})


def test_one_loop_threshold_control_changes_gauge_and_portal_entries() -> None:
    corrected, metadata = apply_one_loop_bsm_thresholds(
        _candidate()["final_state"],
        _candidate(),
        matching_scale_gev=91.1876,
        singlet_mass_gev=1000.0,
    )
    assert corrected == pytest.approx(_candidate()["final_state"])
    assert metadata["canonical_threshold_matching_scales"] is True
    assert metadata["low_scale_endpoint_logs_reapplied"] is False
    assert metadata["higgs_quartic_shift"] == 0.0
    assert metadata["complete_bsm_self_energies_included"] is False
    assert metadata["experimental_data_used"] is False


def test_campaign_retains_mass_grid_and_projects_to_smdr(tmp_path) -> None:
    report = run_bsm_threshold_matching_campaign(
        {"pipeline_version": "test-w15", "scope": {"ir_scale_gev": 91.1876}, "candidate_results": [_candidate()]},
        smdr_root=_fake_smdr(tmp_path),
        singlet_mass_grid_gev=[1000.0, 100000.0],
    )
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["status_counts"] == {"SMDR_COMPLETE": 2}
    assert report["controls"]["all_singlet_mass_hypotheses_retained"] is True
    assert report["selection"]["performed"] is False
