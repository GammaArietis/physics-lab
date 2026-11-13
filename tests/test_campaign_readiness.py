"""Readiness tests for the bounded phase-7 campaign manifest."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    CampaignManifestError,
    audit_campaign_readiness,
    load_campaign_manifest,
    validate_campaign_manifest,
    write_campaign_readiness_report,
)


MANIFEST_PATH = "schemas/examples/campaign_manifest_pilot.json"


def test_pilot_manifest_is_ready_without_execution() -> None:
    manifest = load_campaign_manifest(MANIFEST_PATH)
    audit = audit_campaign_readiness(manifest=manifest)

    assert manifest["status"] == "PILOT_READY"
    assert audit["status"] == "READY_FOR_PILOT"
    assert audit["execution_status"] == "NOT_RUN"
    assert audit["candidate_count"] == 1
    assert all(audit["checks"].values())
    assert all(audit["controls"].values())


def test_readiness_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_campaign_readiness_report(tmp_path / "first.json")
    second = write_campaign_readiness_report(tmp_path / "second.json")

    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )
    serialized = first.read_text(encoding="utf-8")
    assert "/workspace/" not in serialized
    assert "/Users/" not in serialized
    assert "NOT_RUN" in serialized


def test_manifest_rejects_automatic_selection() -> None:
    manifest = copy.deepcopy(load_campaign_manifest(MANIFEST_PATH))
    manifest["selection_policy"]["mode"] = "AUTO_SELECT"

    with pytest.raises(CampaignManifestError, match="automatic selection"):
        validate_campaign_manifest(manifest)


def test_manifest_rejects_external_data_and_empirical_activation() -> None:
    manifest = copy.deepcopy(load_campaign_manifest(MANIFEST_PATH))
    manifest["scope"]["external_data_used"] = True

    with pytest.raises(CampaignManifestError, match="external_data_used"):
        validate_campaign_manifest(manifest)

    manifest = copy.deepcopy(load_campaign_manifest(MANIFEST_PATH))
    manifest["scope"]["empirical_comparison"] = "AUTHORIZED"

    with pytest.raises(CampaignManifestError, match="empirical comparison"):
        validate_campaign_manifest(manifest)


def test_manifest_requires_portable_checkpoint_and_report_paths() -> None:
    manifest = copy.deepcopy(load_campaign_manifest(MANIFEST_PATH))
    manifest["execution"]["checkpoint_path"] = "../outside/checkpoint.json"

    with pytest.raises(CampaignManifestError, match="cannot escape"):
        validate_campaign_manifest(manifest)


def test_manifest_bounds_parallelism_and_failures() -> None:
    manifest = copy.deepcopy(load_campaign_manifest(MANIFEST_PATH))
    manifest["execution"]["parallelism"] = 2

    audit = audit_campaign_readiness(manifest=manifest)
    assert audit["status"] == "NOT_READY"
    assert audit["checks"]["parallelism_bounded"] is False

    manifest = copy.deepcopy(load_campaign_manifest(MANIFEST_PATH))
    manifest["failure_policy"]["max_failures"] = 2
    with pytest.raises(CampaignManifestError, match="bounded by max_candidates"):
        validate_campaign_manifest(manifest)


def test_candidate_reference_mismatch_is_isolated_in_readiness_report() -> None:
    manifest = copy.deepcopy(load_campaign_manifest(MANIFEST_PATH))
    manifest["candidate_refs"][0]["candidate_id"] = "different-candidate-id"

    audit = audit_campaign_readiness(manifest=manifest)
    assert audit["status"] == "NOT_READY"
    assert audit["checks"]["candidate_records_valid"] is False
    assert audit["candidate_audits"][0]["status"] == "FAIL"
