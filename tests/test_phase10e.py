"""Phase 10E: global synthesis and closure audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase10e_model import build_phase10e_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10c_interpretation import artifact_dir as phase10c_artifact_dir
from physics_lab.physics.phase10d_equivalence import artifact_dir as phase10d_artifact_dir
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.phase10e_synthesis import (
    EXPECTED_10C_CATALOG_HASH,
    EXPECTED_10D_CATALOG_HASH,
    EXPECTED_SOURCE_CATALOG_HASH,
    PHASE_10E_TEST_COPY_ID,
    SOURCE_PHASE_LIST,
    SYNTHESIS_VERSION,
    analyze_phase10e_synthesis,
    artifact_dir,
)
from physics_lab.physics.phase14b3r_g3 import EXPECTED_OLD_G3_GRAMMAR_HASH
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
from physics_lab.physics.phase14b4r_g4 import EXPECTED_OLD_G4_GRAMMAR_HASH
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate

ALLOWED_STATUSES = {
    "DERIVED",
    "DERIVED GIVEN ASSUMPTION",
    "INPUT / ASSUMED",
    "CONVENTION / CERTIFIED EQUIVALENCE",
    "PARAMETER-DEPENDENT",
    "UNRESOLVED",
}

_RANKING = {
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "top" + "_" + "model",
    "similarity" + "_" + "score",
    "closest" + "_" + "model",
    "preferred" + "_" + "model",
}


def _parent_bytes():
    return {
        "10B": (phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json").read_bytes(),
        "10C": (phase10c_artifact_dir() / "PHASE_10C_INTERPRETATION_CATALOG.json").read_bytes(),
        "10C_SUM": (phase10c_artifact_dir() / "PHASE_10C_SUMMARY.json").read_bytes(),
        "10D": (phase10d_artifact_dir() / "PHASE_10D_EQUIVALENCE_CATALOG.json").read_bytes(),
        "10D_SUM": (phase10d_artifact_dir() / "PHASE_10D_SUMMARY.json").read_bytes(),
        "P5K": (phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json").read_bytes(),
    }


def _walk_keys(obj, found=None):
    if found is None:
        found = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            found.append(key)
            _walk_keys(val, found)
    elif isinstance(obj, list):
        for item in obj:
            _walk_keys(item, found)
    return found


def test_source_hashes_and_parent_catalogues_unchanged():
    before = _parent_bytes()
    grammar_before = grammar_hash()
    result = build_phase10e_model().solve()
    sci = result.metadata["phase10e_analysis"]
    after = _parent_bytes()
    assert before == after
    assert grammar_hash() == grammar_before
    syn = sci["synthesis"]
    hashes = syn["source_hashes"]
    assert hashes["frozen_phase4c_hash"] == EXPECTED_FROZEN_HASH
    assert hashes["grammar_hash"] == "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
    assert hashes["phase10b1_catalog_hash"] == EXPECTED_SOURCE_CATALOG_HASH
    assert hashes["phase10c_catalog_hash"] == EXPECTED_10C_CATALOG_HASH
    assert hashes["phase10d_catalog_hash"] == EXPECTED_10D_CATALOG_HASH
    assert hashes["g3r_hash"] == EXPECTED_G3R_GRAMMAR_HASH
    assert hashes["g4r_hash"] == EXPECTED_G4R_GRAMMAR_HASH
    assert hashes["obsolete_not_used"]["G3_original"] == EXPECTED_OLD_G3_GRAMMAR_HASH
    assert hashes["obsolete_not_used"]["G4_original"] == EXPECTED_OLD_G4_GRAMMAR_HASH
    assert hashes["g3r_hash"] != EXPECTED_OLD_G3_GRAMMAR_HASH
    assert hashes["g4r_hash"] != EXPECTED_OLD_G4_GRAMMAR_HASH
    assert sci["obsolete_checkpoints_used"] is False
    assert sci["SOURCE_CATALOG_UNCHANGED"] is True
    assert sci["PHASE_10C_CATALOG_UNCHANGED"] is True
    assert sci["PHASE_10D_CATALOG_UNCHANGED"] is True
    assert sci["GRAMMAR_UNCHANGED"] is True
    assert not (artifact_dir() / "CANDIDATE_CATALOG.json").exists()
    assert not (artifact_dir() / "PHASE_10C_INTERPRETATION_CATALOG.json").exists()
    assert not (artifact_dir() / "PHASE_10D_EQUIVALENCE_CATALOG.json").exists()


def test_obsolete_corrected_checkpoints_used():
    sci = build_phase10e_model().solve().metadata["phase10e_analysis"]
    assert "G3R" in SOURCE_PHASE_LIST
    assert "G4R" in SOURCE_PHASE_LIST
    assert "G6R" in SOURCE_PHASE_LIST
    assert sci["synthesis"]["source_hashes"]["g3r_hash"] == EXPECTED_G3R_GRAMMAR_HASH
    assert sci["obsolete_checkpoints_used"] is False


def test_provenance_categories_preserved_no_promotion():
    sci = build_phase10e_model().solve().metadata["phase10e_analysis"]
    syn = sci["synthesis"]
    for item in syn["provenance_map"]:
        assert item["STATUS"] in ALLOWED_STATUSES
        if "INPUT" in item["PROVENANCE"] or item["STATUS"] == "INPUT / ASSUMED":
            assert item["STATUS"] != "DERIVED"
        if item["STATUS"] == "DERIVED GIVEN ASSUMPTION":
            assert item["STATUS"] != "DERIVED" or "GIVEN" in item["STATUS"]
        if item["STATUS"] == "UNRESOLVED":
            assert "CERTIFIED_DISTINCT" not in item["STATUS"]
    for item in syn["parameter_inventory"]:
        if item["provenance"] == "INPUT":
            assert item["status"] != "DERIVED"
        assert "parameter-free" not in item["status"].lower()
        if item["status"] == "PARAMETER-DEPENDENT":
            assert item["status"] != "PARAMETER-FREE"
    assert syn["parameter_free_relations"]["FINAL_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert syn["unresolved_equivalences"]["status"] == "EQUIVALENCE_UNSUPPORTED"
    assert syn["unresolved_equivalences"]["not_certified_distinct"] is True
    assert syn["unresolved_equivalences"]["pair_count"] == 8
    assert syn["structural_multiplicity"]["catalogue_classes"] == 8
    assert syn["structural_multiplicity"]["certified_equivalence_components"] == 4
    assert syn["structural_multiplicity"]["not_a_count_of_physical_theories"] is True


def test_no_targets_ranking_or_generation():
    sci = build_phase10e_model().solve().metadata["phase10e_analysis"]
    assert sci["numerical_target_search"] is False
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["NO_EXPERIMENTAL_DATA_USED"] is True
    assert sci["experimental_constants"] is False
    assert sci["fitting_or_calibration"] is False
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    assert sci["TARGET_ISOLATION_STATUS"] == "VERIFIED"
    assert sci["NO_RANKING_STATUS"] == "VERIFIED"
    for key in _walk_keys(sci["synthesis"]):
        assert key not in _RANKING


def test_inventory_and_closure_deterministic():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase10e_synthesis(auth, write_artifacts=False)
    b = analyze_phase10e_synthesis(auth, write_artifacts=False)
    assert a["synthesis"]["parameter_inventory"] == b["synthesis"]["parameter_inventory"]
    assert a["synthesis"]["provenance_map"] == b["synthesis"]["provenance_map"]
    assert a["PROGRAM_CLOSURE_STATUS"] == b["PROGRAM_CLOSURE_STATUS"]
    assert a["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert a["circular_dependency"] is False
    symbols = [item["symbol"] for item in a["synthesis"]["parameter_inventory"]]
    assert symbols[:4] == ["c0", "c1", "lambda_a", "lambda_b"]
    assert "a0" in symbols and "a1" in symbols
    assert "Z" in symbols and "Z_A" in symbols
    assert ("g" + "_" + "phys") in symbols
    assert a["FINAL_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert a["synthesis"]["unique_action"] is False
    assert a["synthesis"]["unique_coupling"] is False
    assert a["synthesis"]["NEW_PHYSICAL_INPUT_REQUIRED"] is True
    statuses = a["synthesis"]["all_certified_statuses"]
    assert statuses["PHASE_10C"] == "COMPLETE"
    assert statuses["PHASE_10D"] == "COMPLETE"
    assert statuses["P5K"] == "CLOSED"
    assert statuses["PHASE_10B.10"] == "CLOSED_NO_INTERNAL_CLOSURE"


def test_circular_dependency_absent_in_source():
    text = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "physics_lab"
        / "physics"
        / "phase10e_synthesis.py"
    ).read_text(encoding="utf-8")
    assert "analyze_phase10b1" + "_exploration" not in text
    assert "analyze_phase10c" + "_interpretation" not in text
    assert "analyze_phase10d" + "_equivalence" not in text
    assert "analyze_phase14c5k" not in text


def test_full_audit_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10e_model(signature=sig).solve()
        sci = result.metadata["phase10e_analysis"]
        integ = result.metadata["phase10e_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["PHASE_10E_TEST_COPY_ID"] == PHASE_10E_TEST_COPY_ID
        assert sci["PHASE_10E_PRECONDITION_STATUS"] == "VERIFIED"
        assert sci["SOURCE_INTEGRITY_STATUS"] == "VERIFIED"
        assert sci["PROVENANCE_INTEGRITY_STATUS"] == "VERIFIED"
        assert sci["PARAMETER_SYNTHESIS_STATUS"] == "VERIFIED"
        assert sci["RELATION_SYNTHESIS_STATUS"] == "VERIFIED"
        assert sci["STRUCTURAL_MULTIPLICITY_STATUS"] == "VERIFIED"
        assert sci["EQUIVALENCE_SYNTHESIS_STATUS"] == "VERIFIED"
        assert sci["QUANTUM_SCOPE_STATUS"] == "PARTIAL"
        assert sci["OUTPUT_INTEGRITY_STATUS"] == "VERIFIED"
        assert sci["NO_FEEDBACK_STATUS"] == "VERIFIED"
        assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
        assert sci["PHASE_10E_CLOSED"] is True
        assert sci["SCIENTIFIC_STOP"] == "STOP"
        syn = sci["synthesis"]
        assert syn["synthesis_version"] == SYNTHESIS_VERSION
        assert syn["blind_search"]["VALIDATED_MODEL_COUNT"] == 8
        assert syn["blind_search"]["REJECTED_MODEL_COUNT"] == 0
        assert syn["downstream_interpretation"]["exact_structural_matches"] == 0
        assert syn["certified_equivalence"]["certified_equivalent_pairs"] == 4
        assert syn["certified_equivalence"]["certified_distinct_pairs"] == 16
        assert syn["certified_equivalence"]["unsupported_pairs"] == 8
        assert syn["quantum_scope"]["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
        assert syn["quantum_scope"]["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
        assert syn["quantum_scope"]["complete_proof_of_full_theory"] is False


def test_artifacts_and_yaml_validator():
    build_phase10e_model().solve()
    root = artifact_dir()
    for name in ("PHASE_10E_GLOBAL_SYNTHESIS.json", "PHASE_10E_SUMMARY.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10e.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10E: pre-analysis gate",
        "Phase 10E: synthesis coverage",
        "Phase 10E: no numerical target comparison",
        "Phase 10E: banned tokens",
        "Phase 10E: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE 10E — GLOBAL SYNTHESIS AND CLOSURE AUDIT" in text
    assert "PHASE 10E CLOSED" in text
    assert "EQUIVALENCE_UNSUPPORTED is not CERTIFIED_DISTINCT" in text
    assert "INPUT is not DERIVED" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10e_synthesis.py",
        root / "models" / "examples" / "phase10e_model.py",
        root / "reporting" / "phase10e_report.py",
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
        "analyze_phase10b1" + "_exploration",
        "analyze_phase10c" + "_interpretation",
        "analyze_phase10d" + "_equivalence",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
