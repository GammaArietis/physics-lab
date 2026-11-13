"""Phase 10B.1: exhaustive blind structural exploration."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase10b1_model import build_phase10b1_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b1_exploration import PHASE_10B1_TEST_COPY_ID, artifact_dir
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_exhaustive_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10b1_model(signature=sig).solve()
        sci = result.metadata["phase10b1_analysis"]
        integ = result.metadata["phase10b1_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["search_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert summary["TOTAL_GENERATED"] == 8
        assert summary["enumerated_count"] == 8
        assert summary["unique_generated_specs"] == 8
        assert summary["duplicate_generation_count"] == 0
        assert summary["exhaustive_coverage"] == "VERIFIED"
        assert summary["target_blindness"] == "VERIFIED"
        assert summary["reproducibility"] == "VERIFIED"
        assert summary["frozen_integrity"] == "VERIFIED"
        assert sci["PHASE_10B1_STATUS"] == "CLOSED"
        assert sci["PHASE_10B1_CLOSED"] is True
        assert sci["PHASE_10B1_TEST_COPY_ID"] == PHASE_10B1_TEST_COPY_ID
        assert sci["ranking_score_introduced"] is False
        assert sci["known_physics_comparison_executed"] is False
        assert sci["phase_10c_executed"] is False
        assert sci["NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"] is True
        assert len(sci["candidate_catalog"]) == 8
        ids = [item["model_id"] for item in sci["candidate_catalog"]]
        assert ids == [f"MODEL_{i:04d}" for i in range(1, 9)]
        assert sci["search_manifest"]["generation_mode"] == "EXHAUSTIVE"
        assert sci["search_manifest"]["random_seed"] is None
        assert sci["search_manifest"]["expected_candidate_count"] == 8


def test_artifacts_exist_and_manifest_is_exhaustive():
    build_phase10b1_model().solve()
    root = artifact_dir()
    for name in (
        "SEARCH_MANIFEST.json",
        "CANDIDATE_CATALOG.json",
        "VALIDATION_RESULTS.json",
        "CANONICALIZATION_RESULTS.json",
        "DEDUPLICATION_RESULTS.json",
        "DERIVED_RELATIONS.json",
        "PARAMETER_INVENTORY.json",
        "REJECTION_LOG.json",
        "SEARCH_SUMMARY.json",
    ):
        assert (root / name).is_file(), name


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10b1.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10B.1: pre-analysis gate",
        "Phase 10B.1: exhaustive coverage",
        "Phase 10B.1: no numerical target search",
        "Phase 10B.1: banned tokens",
        "Phase 10B.1: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE 10B.1 SUMMARY" in text
    assert "PHASE 10B.1 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b1_exploration.py",
        root / "models" / "examples" / "phase10b1_model.py",
        root / "reporting" / "phase10b1_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
        "phase10a_" + "known_physics",
        "best_model",
        "top_candidates",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
