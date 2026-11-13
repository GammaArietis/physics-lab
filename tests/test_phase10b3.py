"""Phase 10B.3: structural consistency and equivalence audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase10b3_model import build_phase10b3_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b2_derivation import artifact_dir as phase10b2_artifact_dir
from physics_lab.physics.phase10b3_audit import (
    PHASE_10B3_TEST_COPY_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_audit_both_signatures():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10b3_model(signature=sig).solve()
        sci = result.metadata["phase10b3_analysis"]
        integ = result.metadata["phase10b3_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert summary["syntactic_candidates"] == 8
        assert summary["TOTAL_GENERATED"] == 8
        assert summary["new_physical_assumptions"] == 0
        assert summary["grammar_changes"] == 0
        assert summary["ranking"] is False
        assert summary["candidates_repaired"] is False
        assert summary["models_merged"] is False
        assert sci["PHASE_10B3_STATUS"] == "CLOSED"
        assert sci["PHASE_10B3_CLOSED"] is True
        assert sci["PHASE_10B3_TEST_COPY_ID"] == PHASE_10B3_TEST_COPY_ID
        assert sci["ranking_score_introduced"] is False
        assert sci["known_physics_comparison_executed"] is False
        assert sci["phase_10c_executed"] is False
        assert sci["NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"] is True
        assert len(sci["candidate_classification_audit"]) == 8
        ids = [item["model_id"] for item in sci["candidate_classification_audit"]]
        assert ids == [f"MODEL_{i:04d}" for i in range(1, 9)]
        op = sci["operator_equivalence_audit"]
        assert op["parameter_reparameterization"] == "TRUE"
        assert op["model_equivalence"] == "UNSUPPORTED"
        assert op["models_merged"] is False
        f2 = sci["field_content_audit"]["F2_A_mu_requirement"]["status"]
        assert f2 in {"REQUIRED_BY_GRAMMAR", "NOT_REQUIRED_BY_GRAMMAR", "UNCHECKED"}
        for model_id in ("MODEL_0007", "MODEL_0008"):
            row = sci["field_content_audit"][model_id]
            assert row["A_mu_in_field_content"] is False
            assert row["structural_coherence"] == "UNRESOLVED"
            assert row["A_mu_added"] is False
            assert row["F2_removed"] is False
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase10b3_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "STRUCTURAL_CONSISTENCY_AUDIT.json",
        "DEPENDENCY_AUDIT.json",
        "FIELD_CONTENT_AUDIT.json",
        "OPERATOR_EQUIVALENCE_AUDIT.json",
        "CANDIDATE_CLASSIFICATION_AUDIT.json",
        "PROVENANCE_AUDIT.json",
        "PHASE_10B3_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert root != phase10b2_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10b3.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10B.3: pre-analysis gate",
        "Phase 10B.3: audit coverage",
        "Phase 10B.3: no numerical target search",
        "Phase 10B.3: banned tokens",
        "Phase 10B.3: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE 10B.3 SUMMARY" in text
    assert "PHASE 10B.3 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b3_audit.py",
        root / "models" / "examples" / "phase10b3_model.py",
        root / "reporting" / "phase10b3_report.py",
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
        "most_physical",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
