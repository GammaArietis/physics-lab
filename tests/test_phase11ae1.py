"""Phase 11AE.1: containment audit; no activated vacuum principle."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11ae1_model import build_phase11ae1_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11ae_vacuum_selection import artifact_dir as phase11ae_artifact_dir
from physics_lab.physics.phase11ae_vacuum_selection import is_exact_mathematical_statement
from physics_lab.physics.phase11ae1_containment import (
    CLOSURE_TARGETS,
    EXTERNAL_REFERENCE_ONLY,
    NON_IMPLICATIONS,
    PHASE_11AE1_TEST_COPY_ID,
    PRE_EXECUTION_CLOSURE_TARGET,
    analyze_phase11ae1_containment,
    artifact_dir,
    containment_identities,
    refuse_principle_activation,
    run_containment_audit,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_non_implications():
    assert NON_IMPLICATIONS["stationary_point_is_selected_vacuum"] is False
    assert NON_IMPLICATIONS["local_minimum_is_global_minimum"] is False
    assert NON_IMPLICATIONS["potential_existence_is_global_minimum_principle"] is False
    assert NON_IMPLICATIONS["sugra_potential_existence_is_vacuum_selection"] is False
    assert NON_IMPLICATIONS["modulus_existence_is_stabilization"] is False
    assert NON_IMPLICATIONS["external_lowest_energy_is_operational"] is False
    assert NON_IMPLICATIONS["containment_activates_vacuum_selection"] is False


def test_external_lowest_energy_is_reference_only():
    for phrase in EXTERNAL_REFERENCE_ONLY:
        assert is_exact_mathematical_statement(phrase) is False


def test_containment_identities_do_not_derive_argmin():
    ident = containment_identities()
    assert ident["status"] == "VERIFIED"
    assert ident["functional_complete"] is False
    assert ident["argmin_present"] is False
    assert ident["vacuum_identified_with_argmin"] is False
    assert ident["derivation_succeeded"] is False
    assert ident["first_missing_kind"] == "NEW_ASSUMPTION"
    assert ident["p11_stationarity_is_not_selection"] is True
    assert ident["p11_principle"] == "NOT_FOUND"
    assert ident["z11_no_stabilization"] is True


def test_activation_attempt_is_refused():
    refused = refuse_principle_activation("global minimum")
    assert refused["activated"] is False
    assert refused["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    auth = authorize_phase5b0_analysis()
    out = analyze_phase11ae1_containment(
        auth,
        write_artifacts=False,
        injected_statement="global minimum",
    )
    assert out["status"] == "STOP"
    assert out["PHASE_11AE1_STOPPED"] is True
    assert out["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"


def test_default_run_is_not_contained():
    sci = build_phase11ae1_model().solve().metadata["phase11ae1_analysis"]
    assert sci["PHASE_11AE1_STATUS"] == "COMPLETE"
    assert sci["CONTAINMENT_STATUS"] == "REQUIRES_NEW_ASSUMPTION"
    assert sci["CONTAINMENT_RECORD"] == "NOT_CONTAINED"
    assert sci["GLOBAL_MINIMIZATION_STATUS"] == "ABSENT"
    assert sci["LOCAL_VS_GLOBAL_STATUS"] == "NOT_ESTABLISHED"
    assert sci["MINIMUM_EXISTENCE_STATUS"] == "NOT_ESTABLISHED"
    assert sci["PFR_STATUS"] == "NOT_FOUND"
    assert sci["PARAMETER_REDUCTION_STATUS"] == "NONE"
    assert sci["NEW_PHYSICAL_INPUT_STATUS"] is False
    assert sci["NEW_ASSUMPTION_STATUS"] is False
    assert sci["principle_activated"] is False
    assert sci["PHASE_11AE1_STOPPED"] is True
    assert sci["NEW_PARAMETER_COUNT"] == 0
    assert sci["REDUCED_PARAMETER_COUNT"] == 0


def test_baselines_unaltered():
    before = {
        "11P": (phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json").read_bytes(),
        "11AE": (phase11ae_artifact_dir() / "PHASE_11AE_VACUUM_SELECTION.json").read_bytes(),
    }
    grammar_before = grammar_hash()
    sci = build_phase11ae1_model().solve().metadata["phase11ae1_analysis"]
    after = {
        "11P": (phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json").read_bytes(),
        "11AE": (phase11ae_artifact_dir() / "PHASE_11AE_VACUUM_SELECTION.json").read_bytes(),
    }
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PHASE_11P_UNCHANGED"] is True
    assert sci["PHASE_11AE_UNCHANGED"] is True
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_deterministic_rerun():
    auth = authorize_phase5b0_analysis()
    a = analyze_phase11ae1_containment(auth, write_artifacts=False)
    b = analyze_phase11ae1_containment(auth, write_artifacts=False)
    assert a["CONTAINMENT_STATUS"] == b["CONTAINMENT_STATUS"] == "REQUIRES_NEW_ASSUMPTION"


def test_both_signatures_remain_not_contained():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        sci = build_phase11ae1_model(signature=sig).solve().metadata["phase11ae1_analysis"]
        assert sci["PHASE_11AE1_TEST_COPY_ID"] == PHASE_11AE1_TEST_COPY_ID
        assert sci["SCIENTIFIC_STOP"] == "STOP"
        assert sci["CONTAINMENT_RECORD"] == "NOT_CONTAINED"


def test_artifacts_and_yaml_validator():
    build_phase11ae1_model().solve()
    root = artifact_dir()
    for name in ("PHASE_11AE1_CONTAINMENT.json", "PHASE_11AE1_SUMMARY.json"):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11ae1.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11AE.1: pre-analysis gate",
        "Phase 11AE.1: coverage",
        "Phase 11AE.1: no numerical target comparison",
        "Phase 11AE.1: banned tokens",
        "Phase 11AE.1: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "PHASE 11AE1 COMPLETE" in report.text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11ae1_containment.py",
        root / "models" / "examples" / "phase11ae1_model.py",
        root / "reporting" / "phase11ae1_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "analyze_phase11p" + "_vacuum_selection",
        "analyze_phase11ae" + "_vacuum_selection",
        "best" + "_" + "model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


class TestPhase11AE1ContainmentAudit:
    def test_closure_is_required_before_any_scan(self):
        assert PRE_EXECUTION_CLOSURE_TARGET is None
        refused = run_containment_audit()
        assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
        assert refused["scanned"] is False
        assert refused["new_parameter_count"] == 0
        assert refused["principle_activated"] is False
        entry = refused["provenance_log"][0]
        assert entry["rule"] == "Target-Blind rule"
        assert entry["logged_before_logical_execution"] is True
        assert entry["post_hoc_validation"] is False
        assert entry["accepted"] is False

    def test_unknown_target_is_refused(self):
        refused = run_containment_audit("LOWEST_ENERGY")
        assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
        assert refused["scanned"] is False

    def test_constant_declaration_is_accepted(self, monkeypatch):
        monkeypatch.setattr(
            "physics_lab.physics.phase11ae1_containment.PRE_EXECUTION_CLOSURE_TARGET",
            "DEGENERATE_CLASS",
        )
        out = run_containment_audit()
        assert out["status"] == "OK"
        assert out["closure_target"] == "DEGENERATE_CLASS"
        assert out["provenance_log"][0]["rule"] == "Target-Blind rule"
        assert out["provenance_log"][0]["accepted"] is True

    def test_conflicting_declaration_is_refused(self, monkeypatch):
        monkeypatch.setattr(
            "physics_lab.physics.phase11ae1_containment.PRE_EXECUTION_CLOSURE_TARGET",
            "SINGLE_VACUUM",
        )
        refused = run_containment_audit("DOMAIN_REDUCTION")
        assert refused["status"] == "CLOSURE_CRITERION_REFUSED"
        assert refused["scanned"] is False

    def test_target_blind_scan_does_not_depend_on_the_declared_objective(self):
        reports = [run_containment_audit(target) for target in CLOSURE_TARGETS]
        provenances = []
        for report in reports:
            assert report["status"] == "OK"
            assert report["scanned"] is True
            assert report["closure_target_used_as_filter"] is False
            assert report["action_content_hash"] == EXPECTED_FROZEN_HASH
            assert report["catalog_class_count"] == 8
            assert report["equivalence_component_count"] == 4
            assert report["new_parameter_count"] == 0
            assert report["principle_activated"] is False
            assert report["Provenance"] == "NOT_FOUND"
            assert report["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
            provenances.append(
                {row["probe"]: row["Provenance"] for row in report["provenance_log"] if "probe" in row}
            )
        assert provenances[0] == provenances[1] == provenances[2]
        assert provenances[0] == {
            "native_minimization_functional": "NOT_FOUND",
            "admissible_space_V_adm": "NOT_FOUND",
            "global_minimization_from_4d_eom_or_bianchi": "NOT_FOUND",
        }
        evidence = reports[0]["probes"][0]["evidence"]
        assert evidence["quadratic_potential_is_minimization_functional"] is False
        assert evidence["identity_principle"] == "NOT_FOUND"
        bianchi = reports[0]["probes"][2]["evidence"]
        assert bianchi["bianchi_is_geometric_identity"] is True
        assert bianchi["bianchi_is_minimization_procedure"] is False
        assert bianchi["eom_minimization_rows"] == 0

    def test_provenance_log_is_written_without_touching_parents(self):
        catalog = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "physics" / "phase10b1_artifacts" / "CANDIDATE_CATALOG.json"
        before = catalog.read_bytes()
        out = run_containment_audit("SINGLE_VACUUM", write_artifacts=True)
        assert catalog.read_bytes() == before
        log_path = artifact_dir() / "PHASE_11AE1_PROVENANCE_LOG.json"
        assert log_path.is_file()
        assert out["Provenance"] == "NOT_FOUND"
