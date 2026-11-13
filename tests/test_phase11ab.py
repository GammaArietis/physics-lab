"""Phase 11AB: mediation synthesis and PARTIAL triage."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11ab_model import build_phase11ab_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11aa_direct_mediation import artifact_dir as phase11aa_artifact_dir
from physics_lab.physics.phase11ab_mediation_synthesis import (
    NON_IMPLICATIONS,
    PHASE_11AB_TEST_COPY_ID,
    analyze_phase11ab_mediation_synthesis,
    artifact_dir,
    synthesis_identities,
    triage_catalog,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_non_implications():
    assert NON_IMPLICATIONS["synthesis_selects_a_mechanism"] is False
    assert NON_IMPLICATIONS["common_soft_terms_imply_equivalence"] is False
    assert NON_IMPLICATIONS["shared_symbol_implies_shared_origin"] is False
    assert NON_IMPLICATIONS["triage_upgrades_PARTIAL_to_VERIFIED"] is False
    assert NON_IMPLICATIONS["CLASS_C_becomes_VERIFIED"] is False
    assert NON_IMPLICATIONS["CLASS_D_becomes_VERIFIED"] is False
    assert NON_IMPLICATIONS["mixed_mediation_activated"] is False


def test_synthesis_identities():
    ids = synthesis_identities()
    assert ids["F_X_not_F_phi"] is True
    assert ids["F_X_not_F_T"] is True
    assert ids["F_T_not_F_phi"] is True
    assert ids["M_direct_not_messenger_mass"] is True
    assert ids["shared_notation_not_shared_origin"] is True
    assert ids["loop_coefficient_not_PFR"] is True
    assert ids["exclusive_intersection_not_PFR"] is True
    assert ids["status"] == "VERIFIED"


def test_triage_catalog_is_deterministic_and_exclusive():
    a = triage_catalog()
    b = triage_catalog()
    assert a == b
    classes = [item["class"] for item in a]
    assert all(cls in {"A", "B", "C", "D", "E"} for cls in classes)
    assert len(classes) == 17
    assert classes.count("A") == 3
    assert classes.count("B") == 2
    assert classes.count("C") == 3
    assert classes.count("D") == 6
    assert classes.count("E") == 3
    for item in a:
        if item["class"] in {"C", "D"}:
            assert item.get("expected_transition") != "VERIFIED"
            assert item.get("resolution") == "NOT_ACTIVATED"
        if item["class"] == "E":
            assert item.get("expected_transition") != "FAILED"
            assert item.get("resolution") == "LEAVE_OPEN"


def test_default_run_remains_partial():
    sci = build_phase11ab_model().solve().metadata["phase11ab_analysis"]
    assert sci["PHASE_11AB_STATUS"] == "PARTIAL"
    assert sci["MEDIATION_SYNTHESIS_STATUS"] == "VERIFIED"
    assert sci["MEDIATION_EQUIVALENCE_STATUS"] == "NOT_DERIVED"
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"
    assert sci["PARTIAL_TRIAGE_STATUS"] == "VERIFIED"
    assert sci["UNION_CERTIFIED_PFRS"] == 0
    assert sci["PHASE_11AB_STOPPED"] is True
    assert sci["new_physical_mechanism_introduced"] is False
    assert sci["analysis"]["identities"]["F_X_not_F_phi"] is True
    assert len(sci["analysis"]["equivalence_pairs"]) == 10
    assert all(p["outcome"] == "DISTINCT" for p in sci["analysis"]["equivalence_pairs"])


def test_baselines_unaltered():
    before = {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11AA": (phase11aa_artifact_dir() / "PHASE_11AA_DIRECT_MEDIATION.json").read_bytes(),
    }
    grammar_before = grammar_hash()
    sci = build_phase11ab_model().solve().metadata["phase11ab_analysis"]
    after = {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "11AA": (phase11aa_artifact_dir() / "PHASE_11AA_DIRECT_MEDIATION.json").read_bytes(),
    }
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_11AA_UNCHANGED"] is True
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11ab_mediation_synthesis(auth, write_artifacts=False)
    b = analyze_phase11ab_mediation_synthesis(auth, write_artifacts=False)
    assert a["MEDIATION_SELECTION_STATUS"] == b["MEDIATION_SELECTION_STATUS"]
    assert a["analysis"]["triage"] == b["analysis"]["triage"]


def test_both_signatures_remain_partial():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11ab_model(signature=sig).solve().metadata["phase11ab_analysis"]
        assert sci["PHASE_11AB_TEST_COPY_ID"] == PHASE_11AB_TEST_COPY_ID
        assert sci["SCIENTIFIC_STOP"] == "STOP"


def test_artifacts_and_yaml_validator():
    build_phase11ab_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11AB_MEDIATION_SYNTHESIS.json", "PHASE_11AB_SUMMARY.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11ab.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11AB: pre-analysis gate",
        "Phase 11AB: coverage",
        "Phase 11AB: no numerical target comparison",
        "Phase 11AB: banned tokens",
        "Phase 11AB: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11AB PARTIAL" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11ab_mediation_synthesis.py",
        root / "models" / "examples" / "phase11ab_model.py",
        root / "reporting" / "phase11ab_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11aa" + "_direct_mediation",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
