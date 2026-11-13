"""Independent Phase 12B checks: freeze identity, isolation, no 12C."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase12b_search import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_LEGAL_COUNT,
    analyze_phase12b_search,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)


def test_independent_exhaustive_search_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    manifest = artifact_dir() / "PHASE_12B_SEARCH_MANIFEST.json"
    before_manifest = manifest.read_bytes() if manifest.is_file() else None
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase12b_search(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["enumerated_candidates"] == EXPECTED_LEGAL_COUNT
    assert sci["completion_status"] == "EXHAUSTIVE_RUN_COMPLETE"
    assert sci["sampling"] is False
    assert sci["phase_12c_executed"] is False
    assert sci["UNIQUE_ACTION"] == "NO"
    assert sci["GLOBAL_CLOSURE"] == "NO"
    assert sci["PHASE_12B_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in declared_ids
    assert sci["overclaims"]["7_start_phase_12C"] == "REJECTED AS OVERCLAIM"
    assert manifest.is_file()
    if before_manifest is not None:
        assert manifest.read_bytes() == before_manifest
    _ = before_hash


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase12b_search.py",
        root / "models" / "examples" / "phase12b_model.py",
        root / "reporting" / "phase12b_report.py",
        root / "tests" / "phase12b_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "from physics_lab.physics.gauge_internal" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "phase10a_" + "known_physics" not in text
        assert "KNOWN_PHYSICS_CATALOG" not in text
        assert "best_model" not in text
        assert "preferred_model" not in text
        assert "top_model" not in text
