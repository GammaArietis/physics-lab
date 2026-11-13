"""Tests for explicit pilot activation and isolated execution."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from physics_lab.registry import (
    CampaignActivationError,
    load_campaign_manifest,
    load_campaign_activation,
    run_pilot_campaign,
    validate_campaign_activation,
    write_completed_activation,
)


ACTIVATION_PATH = "schemas/examples/campaign_activation_pilot.json"


def test_activation_record_requires_explicit_human_authorization() -> None:
    activation = load_campaign_activation(ACTIVATION_PATH)

    assert activation["authorization"]["status"] == "AUTHORIZED"
    assert activation["authorization"]["human_confirmation"] is True
    assert activation["authorization"]["selection_mode"] == "NO_AUTO_SELECTION"
    assert activation["execution_status"] == "NOT_RUN"


def test_activation_rejects_missing_human_confirmation() -> None:
    activation = copy.deepcopy(load_campaign_activation(ACTIVATION_PATH))
    activation["authorization"]["human_confirmation"] = False

    with pytest.raises(CampaignActivationError, match="human_confirmation"):
        validate_campaign_activation(activation)


def test_pilot_executes_one_candidate_without_selection_or_external_data(tmp_path) -> None:
    manifest = load_campaign_manifest("schemas/examples/campaign_manifest_pilot.json")
    manifest["candidate_refs"][0]["record_path"] = "candidate.json"
    manifest["execution"]["checkpoint_path"] = "checkpoint.json"
    manifest["execution"]["report_directory"] = "reports"
    (tmp_path / "candidate.json").write_text(
        Path("schemas/examples/theory_candidate_circle_reference.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    activation = load_campaign_activation(ACTIVATION_PATH)
    activation["manifest_path"] = "manifest.json"
    activation["checkpoint_path"] = "checkpoint.json"

    report = run_pilot_campaign(activation=activation, repository_root=tmp_path)

    assert report["execution_status"] == "COMPLETE"
    assert report["candidate_count"] == 1
    assert report["candidate_results"][0]["status"] == "PASS"
    assert report["candidate_results"][0]["record_unchanged"] is True
    assert all(report["controls"].values())
    assert report["selection"]["performed"] is False
    assert report["selection"]["ranking_performed"] is False


def test_completed_activation_is_persisted_without_changing_authorization(tmp_path) -> None:
    activation = load_campaign_activation(ACTIVATION_PATH)
    report = {
        "execution_status": "COMPLETE",
        "report_path": "docs/validation/campaign_reports/circle-reference-pilot/campaign_report.json",
    }
    output = write_completed_activation(
        tmp_path / "activation.json",
        activation,
        report,
        completed_at="2026-11-13T20:30:00+01:00",
    )
    saved = json.loads(output.read_text(encoding="utf-8"))

    assert saved["authorization"]["status"] == "AUTHORIZED"
    assert saved["execution_status"] == "COMPLETE"
    assert saved["completed_at"] == "2026-11-13T20:30:00+01:00"
