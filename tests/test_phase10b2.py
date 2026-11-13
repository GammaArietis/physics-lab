"""Phase 10B.2: blind mathematical derivation of the 8 enumerated structures."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase10b2_model import build_phase10b2_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b2_derivation import (
    PHASE_10B2_TEST_COPY_ID,
    artifact_dir,
    snapshot_phase10b1_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_derivation_both_signatures():
    before = snapshot_phase10b1_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10b2_model(signature=sig).solve()
        sci = result.metadata["phase10b2_analysis"]
        integ = result.metadata["phase10b2_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["derivation_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert summary["candidates_analyzed"] == 8
        assert summary["new_assumptions_introduced"] == 0
        assert summary["new_free_parameters_introduced"] == 0
        assert summary["experimental_inputs_used"] == 0
        assert summary["target_inputs_used"] == 0
        assert summary["ranking_performed"] is False
        assert summary["known_physics_comparison"] is False
        assert summary["reproducibility"] == "VERIFIED"
        assert summary["phase10b1_artifacts_unchanged"] is True
        assert sci["PHASE_10B2_STATUS"] == "CLOSED"
        assert sci["PHASE_10B2_CLOSED"] is True
        assert sci["PHASE_10B2_TEST_COPY_ID"] == PHASE_10B2_TEST_COPY_ID
        assert sci["ranking_score_introduced"] is False
        assert sci["known_physics_comparison_executed"] is False
        assert sci["phase_10c_executed"] is False
        assert sci["NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"] is True
        assert len(sci["candidate_records"]) == 8
        ids = [item["model_id"] for item in sci["candidate_records"]]
        assert ids == [f"MODEL_{i:04d}" for i in range(1, 9)]
        for item in sci["candidate_records"]:
            assert item["parameter_free_test"]["classification"] == "NO_PARAMETER_FREE_RELATIONS_FOUND"
            assert item["new_assumptions_introduced"] == 0
    after = snapshot_phase10b1_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_10b1():
    before = snapshot_phase10b1_hashes()
    build_phase10b2_model().solve()
    after = snapshot_phase10b1_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "DERIVATION_CATALOG.json",
        "EOM_RESULTS.json",
        "SYMMETRY_RESULTS.json",
        "SPECTRUM_RESULTS.json",
        "CONSERVATION_RESULTS.json",
        "PARAMETER_RELATIONS.json",
        "PARAMETER_FREE_RELATIONS.json",
        "ASSUMPTION_USAGE.json",
        "UNTESTED_DERIVATIONS.json",
        "DERIVATION_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert not (root / "SEARCH_MANIFEST.json").exists()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10b2.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10B.2: pre-analysis gate",
        "Phase 10B.2: derivation coverage",
        "Phase 10B.2: no numerical target search",
        "Phase 10B.2: banned tokens",
        "Phase 10B.2: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE 10B.2 SUMMARY" in text
    assert "PHASE 10B.2 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b2_derivation.py",
        root / "models" / "examples" / "phase10b2_model.py",
        root / "reporting" / "phase10b2_report.py",
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
        "preferred_model",
        "model_score",
        "strongest_model",
        "closest_model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
