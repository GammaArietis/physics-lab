"""Phase 10C: downstream structural interpretation."""

from __future__ import annotations

import copy
from pathlib import Path

from physics_lab.models.examples.phase10c_model import build_phase10c_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10c_interpretation import (
    EXPECTED_REFERENCE_CATALOG_HASH,
    EXPECTED_SOURCE_CATALOG_HASH,
    PHASE_10C_TEST_COPY_ID,
    analyze_phase10c_interpretation,
    artifact_dir,
    load_reference_catalog,
    load_source_catalog,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_interpretation_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10c_model(signature=sig).solve()
        sci = result.metadata["phase10c_analysis"]
        integ = result.metadata["phase10c_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["PHASE_10C_STATUS"] == "COMPLETE"
        assert sci["PHASE_10C_CLOSED"] is True
        assert sci["PHASE_10C_TEST_COPY_ID"] == PHASE_10C_TEST_COPY_ID
        assert sci["CANDIDATES_INTERPRETED"] == 8
        assert sci["REFERENCE_OBJECTS"] == 7
        assert sci["PAIRWISE_COMPARISONS"] == 56
        assert sci["PARAMETER_FREE_RELATION_COUNT"] == 0
        assert sci["PARAMETER_DEPENDENT_CLASS_COUNT"] == 8
        assert sci["models_generated"] == 0
        assert sci["NO_RANKING_PERFORMED"] is True
        assert sci["CANDIDATE_CATALOG_UNCHANGED"] is True
        assert sci["SOURCE_CATALOG_HASH"] == EXPECTED_SOURCE_CATALOG_HASH
        assert sci["REFERENCE_CATALOG_HASH"] == EXPECTED_REFERENCE_CATALOG_HASH
        ids = [row["class_id"] for row in sci["structural_family_table"]]
        assert ids == [f"MODEL_{i:04d}" for i in range(1, 9)]


def test_10c_cannot_modify_10b_catalogue():
    catalog = phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json"
    before = catalog.read_bytes()
    build_phase10c_model().solve()
    after = catalog.read_bytes()
    assert before == after
    assert catalog.name == "CANDIDATE_CATALOG.json"
    assert artifact_dir() != phase10b1_artifact_dir()
    assert not (artifact_dir() / "CANDIDATE_CATALOG.json").exists()


def test_10c_cannot_modify_generator_configuration():
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase10c_interpretation(auth)
    assert sci["GENERATOR_UNCHANGED"] is True
    assert sci["GRAMMAR_UNCHANGED"] is True
    assert sci["WHITELIST_UNCHANGED"] is True
    assert sci["BLACKLIST_UNCHANGED"] is True
    assert sci["grammar_modified"] is False


def test_known_physics_cannot_affect_candidate_selection():
    source = load_source_catalog()
    ids_before = [item["model_id"] for item in source]
    hashes_before = [item["canonical_hash"] for item in source]
    result = build_phase10c_model().solve()
    sci = result.metadata["phase10c_analysis"]
    ids_after = [item["model_id"] for item in sci["interpretation_catalog"]["interpretation_results"]]
    hashes_after = [item["canonical_hash"] for item in sci["interpretation_catalog"]["interpretation_results"]]
    assert ids_before == ids_after == [f"MODEL_{i:04d}" for i in range(1, 9)]
    assert hashes_before == hashes_after
    assert sci["NO_CANDIDATE_SELECTION_PERFORMED"] is True


def test_no_ranking_field_and_no_numerical_target():
    sci = build_phase10c_model().solve().metadata["phase10c_analysis"]
    blob = sci["interpretation_catalog"]
    banned_keys = {
        "ra" + "nk",
        "sc" + "ore",
        "win" + "ner",
        "best" + "_" + "model",
        "top" + "_" + "model",
        "similarity" + "_" + "score",
    }
    def walk(obj):
        if isinstance(obj, dict):
            for key, val in obj.items():
                assert key not in banned_keys
                walk(val)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
    walk(blob)
    assert sci["numerical_target_search"] is False
    assert sci["NO_TARGET_VALUES_USED"] is True


def test_unsupported_equivalence_and_parameter_dependent_relations_remain():
    sci = build_phase10c_model().solve().metadata["phase10c_analysis"]
    for item in sci["interpretation_catalog"]["interpretation_results"]:
        assert "BASIS_EQUIVALENCE_UNSUPPORTED" in item["unsupported_equivalences"]
        assert item["parameter_audit"]["parameter_status"] == "PARAMETER_DEPENDENT"
        classes = {row["classification"] for row in item["derived_relation_classification"]}
        assert "parameter-dependent" in classes
        assert item["parameter_audit"]["remaining_physical_parameters"]
        assert "c0" in item["parameter_audit"]["remaining_physical_parameters"]
        assert "c1" in item["parameter_audit"]["remaining_physical_parameters"]


def test_no_new_model_generated():
    sci = build_phase10c_model().solve().metadata["phase10c_analysis"]
    assert sci["models_generated"] == 0
    assert len(sci["structural_family_table"]) == 8


def test_reference_update_cannot_alter_candidate_classes():
    source = load_source_catalog()
    refs = load_reference_catalog()
    mutated = copy.deepcopy(refs)
    mutated["einstein_hilbert"]["fingerprint"] = "mutated documentation only"
    auth = authorize_phase5b0_analysis()
    halted = analyze_phase10c_interpretation(
        auth,
        reference_catalog=mutated,
        write_artifacts=False,
    )
    assert halted["status"] == "INTERPRETATION_INVALIDATED"
    ids = [item["model_id"] for item in source]
    hashes = [item["canonical_hash"] for item in source]
    assert ids == [f"MODEL_{i:04d}" for i in range(1, 9)]
    assert all(hashes)


def test_deterministic_comparison():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase10c_interpretation(auth, write_artifacts=False)
    b = analyze_phase10c_interpretation(auth, write_artifacts=False)
    assert a["SOURCE_CATALOG_HASH"] == b["SOURCE_CATALOG_HASH"]
    assert a["REFERENCE_CATALOG_HASH"] == b["REFERENCE_CATALOG_HASH"]
    assert a["interpretation_matrix"] == b["interpretation_matrix"]
    assert a["structural_family_table"] == b["structural_family_table"]


def test_source_catalog_hash_mismatch_invalidates():
    auth = authorize_phase5b0_analysis()
    catalog = copy.deepcopy(load_source_catalog())
    catalog[0] = {**catalog[0], "canonical_hash": "0" * 64}
    out = analyze_phase10c_interpretation(
        auth,
        source_catalog=catalog,
        write_artifacts=False,
    )
    assert out["status"] == "INTERPRETATION_INVALIDATED"
    assert "SOURCE_CATALOG_HASH" in str(out.get("detail"))


def test_reference_hash_mismatch_invalidates():
    auth = authorize_phase5b0_analysis()
    refs = copy.deepcopy(load_reference_catalog())
    refs["maxwell"]["fingerprint"] = "altered reference"
    out = analyze_phase10c_interpretation(
        auth,
        reference_catalog=refs,
        write_artifacts=False,
    )
    assert out["status"] == "INTERPRETATION_INVALIDATED"
    assert "REFERENCE_CATALOG_HASH" in str(out.get("detail"))


def test_artifacts_exist_and_do_not_overwrite_10b():
    build_phase10c_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_10C_INTERPRETATION_CATALOG.json",
        "INTERPRETATION_MATRIX.json",
        "STRUCTURAL_FAMILY_TABLE.json",
        "PARAMETER_AUDIT.json",
        "HUMAN_READABLE_SUMMARIES.json",
        "PHASE_10C_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert not (root / "CANDIDATE_CATALOG.json").exists()
    assert (phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json").is_file()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10c.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10C: pre-analysis gate",
        "Phase 10C: interpretation coverage",
        "Phase 10C: no numerical target comparison",
        "Phase 10C: banned tokens",
        "Phase 10C: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE 10C — DOWNSTREAM STRUCTURAL INTERPRETATION" in text
    assert "PHASE 10C CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "BLIND SEARCH RESULT" in text
    assert "DOWNSTREAM INTERPRETATION" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10c_interpretation.py",
        root / "models" / "examples" / "phase10c_model.py",
        root / "reporting" / "phase10c_report.py",
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
        "best" + "_" + "model",
        "top" + "_" + "candidates",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
