from __future__ import annotations

import math

from physics_lab.search.gauge_yukawa_vectorlike_extension import (
    action_record,
    gauge_coefficients,
    run_gauge_yukawa_campaign,
)


def _activation() -> dict:
    state = [0.45, 0.65, 0.9, 0.8, 0.25, 0.13, 0.10, 0.02]
    return {
        "campaign_id": "test",
        "uv_scale_gev": 1.0e6,
        "ir_scale_gev": 100.0,
        "candidates": [
            {"candidate_id": "Q", "multiplicities": {"Q": 1}, "yukawa_multiplet": "Q", "initial_state": state},
            {"candidate_id": "zero-control", "multiplicities": {"E": 1}, "yukawa_multiplet": "E", "initial_state": [0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.1, 0.02]},
        ],
    }


def test_vectorlike_pair_has_explicit_action_and_anomaly_control() -> None:
    action = action_record({"Q": 1}, "Q")
    assert action["new_fields"][1]["vectorlike_pair"] is True
    assert action["new_fields"][1]["gauge_anomaly_cancelled_pairwise"] is True


def test_gauge_coefficients_are_derived_from_representation_data() -> None:
    coefficients = gauge_coefficients({"Q": 1})
    assert math.isclose(coefficients["g1"], 41.0 / 10.0 + 2.0 / 15.0)
    assert math.isclose(coefficients["g2"], -19.0 / 6.0 + 2.0)
    assert math.isclose(coefficients["g3"], -7.0 + 4.0 / 3.0)


def test_campaign_keeps_zero_gauge_surface_and_no_selection() -> None:
    report = run_gauge_yukawa_campaign(_activation())
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["candidate_count"] == 2
    assert report["scan"]["status_counts"]["ZERO_PROTECTED"] == 1
    assert report["controls"]["no_exact_zero_gauge_rescue_claimed"] is True
    assert report["selection"]["performed"] is False

