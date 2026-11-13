"""Phase 13: spacetime dimension as a discrete search variable."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase13_model import build_phase13_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import (
    EXPECTED_GRAMMAR_HASH_10B,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
)
from physics_lab.physics.phase12d_derivation import artifact_dir as phase12d_artifact_dir
from physics_lab.physics.phase13_dimension import (
    AUDIT_VERSION,
    DIMENSIONS,
    EXPECTED_12A_GRAMMAR_HASH,
    PHASE_13_TEST_COPY_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_dimensional_search_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_10a = grammar_hash_10a()
    before_12a = grammar_hash_12a()
    before_12d = (phase12d_artifact_dir() / "PHASE_12D_SUMMARY.json").read_bytes()
    before_freeze = (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase13_model(signature=sig).solve()
        sci = result.metadata["phase13_analysis"]
        integ = result.metadata["phase13_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        closure = sci["closure_results"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == before_10a == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
        assert sci["grammar_hash_12A"] == EXPECTED_12A_GRAMMAR_HASH
        assert sci["frozen_hash_4C"] == EXPECTED_FROZEN_HASH
        assert list(sci["dimensions_tested"]) == list(DIMENSIONS)
        assert sci["dimensions_consistent"] == list(DIMENSIONS)
        assert sci["dimensions_inconsistent"] == []
        assert sci["unique_dimension"] == "NO"
        assert sci["NO_UNIQUE_DIMENSION_DETECTED"] is True
        assert sci["NO_REQUIRED_DIMENSION"] is True
        assert sci["minimal_consistent_D"] == 4
        assert closure["MINIMAL_DIMENSION"] == "UNTESTED"
        assert closure["DIMENSION_UNIQUELY_SELECTED"] is False
        assert sci["string_theory_constraints_imported"] is False
        assert sci["ranking"] is False
        assert sci["phase_14_executed"] is False
        assert sci["new_physical_principle"] is False
        assert sci["PHASE_13_STATUS"] == "CLOSED"
        assert sci["PHASE_13_TEST_COPY_ID"] == PHASE_13_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["DIMENSION_SWEEP_EXHAUSTIVE"] is True
        assert sci["STRUCTURAL_BRANCH_SEARCH_EXHAUSTIVE"] is True
        assert sci["FULL_DYNAMIC_DERIVATION_EXHAUSTIVE"] is False
        assert sci["window_limit_reached"] is True
        assert sci["dimensions_with_new_PFR"] == []
        assert sci["PARAMETER_FREE_CLOSURE"] == "NO"
        assert sci["UNIQUE_ACTION"] == "NO"
        internals = [row["internal_vs_extra"] for row in sci["dimension_rows"]]
        assert all(item["identified_H_int_with_extra_spacetime"] is False for item in internals)
        assert all(item["H_int_dimension"] == 3 for item in internals)
        grav4 = next(r for r in sci["dimension_rows"] if r["D"] == 4)["gravity"]
        grav5 = next(r for r in sci["dimension_rows"] if r["D"] == 5)["gravity"]
        assert grav4["D4_local_bulk_is_c0_plus_c1_R"] is True
        assert "L2 = gauss_bonnet = K - 4 Ricci^2 + R^2" in grav5["dynamical_operators"]
        assert sci["overclaims"]["1_assume_D4_or_D10_or_D11_or_D12"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["5_import_M_or_F_theory"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["12_start_phase_14"] == "REJECTED AS OVERCLAIM"
        assert summary["ranking"] is False
        assert len(sci["sweep_table"]) == 13
        assert len(sci["level_b"]["skipped"]) == 0
    after = snapshot_prior_artifact_hashes()
    assert before == after
    assert (phase12d_artifact_dir() / "PHASE_12D_SUMMARY.json").read_bytes() == before_12d
    assert (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes() == before_freeze


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase13_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "PHASE_13_SUMMARY.json",
        "PHASE_13_DIMENSION_SEARCH_MANIFEST.json",
        "PHASE_13_DIMENSION_SWEEP_RESULTS.json",
        "PHASE_13_DIMENSIONAL_OPERATOR_RESULTS.json",
        "PHASE_13_PARAMETER_RESULTS.json",
        "PHASE_13_EFFECTIVE_4D_RESULTS.json",
        "PHASE_13_CLOSURE_RESULTS.json",
        "PHASE_13_INTEGRITY_REPORT.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase12a_artifact_dir()
    assert root != phase12d_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase13.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 13: pre-analysis gate",
        "Phase 13: dimensional-search coverage",
        "Phase 13: no numerical target search",
        "Phase 13: banned tokens",
        "Phase 13: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_13_SUMMARY" in text
    assert "PHASE 13 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "NO_UNIQUE_DIMENSION_DETECTED" in text
    assert "No Phase 14" in text or "no Phase 14" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase13_dimension.py",
        root / "models" / "examples" / "phase13_model.py",
        root / "reporting" / "phase13_report.py",
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
        "preferred_model",
        "top_model",
        "superstring",
        "worldsheet",
        "Calabi" + "-Yau",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
