"""Phase 11A: new physical input gate."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11a_input_model import build_phase11a_input_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11a_strategy import artifact_dir as phase11a_strategy_artifact_dir
from physics_lab.physics.phase11a_input_gate import (
    EXPECTED_10E_SYNTHESIS_HASH,
    PHASE_11A_INPUT_TEST_COPY_ID,
    REQUIRED_INPUT_FIELDS,
    analyze_phase11a_input_gate,
    artifact_dir,
    audit_human_declared_input,
    input_hash,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _probe(**overrides):
    base = {
        "input_id": "AUDIT_PROBE_NOT_SELECTED",
        "title": "Independent Cauchy-slice spin-structure declaration",
        "mathematical_statement": (
            "A compact oriented Cauchy hypersurface carries a declared spin "
            "structure class that is not determined by the frozen volume-plus-Ricci "
            "family or the internal operator H_int."
        ),
        "physical_scope": ["boundary structure"],
        "motivation": "Independent geometric completion not present in Phases 1-10E.",
        "affected_previous_phases": ["none of the certified 1-10E derivations"],
        "new_objects": [
            {
                "object_id": "spin_structure_class",
                "kind": "new geometric assumption",
                "mathematical_definition": "declared spin structure on a Cauchy slice",
                "dimension": "discrete label",
                "symmetry": "Diff on the slice",
                "locality": "hypersurface",
                "covariance": "spatial",
                "derivative_order": 0,
                "parameter_status": "INPUT",
                "dependencies": [],
            }
        ],
        "new_assumptions": ["spin structure is independently declared"],
        "parameter_implications": {
            "new_parameters": [{"name": "spin_label", "dimension": "discrete label"}],
            "constrained_parameters": [],
            "relations": [],
            "silently_fixes_existing": False,
        },
        "intended_domain": "declared Cauchy slices only",
        "provenance": "NEW_PHYSICAL_INPUT",
        "declaration_timestamp": "test-only-not-selected",
        "what_is_new": "an independent spin-structure class on Cauchy slices",
        "what_was_already_known": "gravity family, H_int, optional F2 TEST EXTENSION, 8 catalogue classes",
        "what_is_assumed": "the spin-structure class is an input, not a derived object",
    }
    base.update(overrides)
    return base


def _parent_bytes():
    return {
        "10E": (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_bytes(),
        "10E_SUM": (phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json").read_bytes(),
        "STRAT": (phase11a_strategy_artifact_dir() / "PHASE_11A_SUMMARY.json").read_bytes(),
    }


def test_no_input_blocks():
    result = build_phase11a_input_model().solve()
    sci = result.metadata["phase11a_input_analysis"]
    assert sci["HUMAN_INPUT_PRESENT"] is False
    assert sci["NEW_PHYSICAL_INPUT_STATUS"] == "MISSING"
    assert sci["PHASE_11A_STATUS"] == "BLOCKED"
    assert sci["INPUT_FREEZE_STATUS"] == "NOT_CREATED"
    assert not (artifact_dir() / "PHASE_11A_INPUT_FREEZE.json").exists()
    assert sci["machine_chose_principle"] is False
    assert sci["principles_generated"] == 0


def test_post_hoc_rejected():
    auth = authorize_phase5b0_analysis()
    declared = _probe(desired_consequence="unique coupling")
    sci = analyze_phase11a_input_gate(auth, declared_input=declared, write_artifacts=False)
    assert sci["gate"]["audit"]["POST_HOC_INPUT"] is True
    assert sci["gate"]["audit"]["rejection"] == "POST_HOC_INPUT"
    assert sci["PHASE_11A_STATUS"] == "FAILED"


def test_target_dependent_rejected():
    auth = authorize_phase5b0_analysis()
    declared = _probe(experimental_target_used_for_input_selection=True)
    sci = analyze_phase11a_input_gate(auth, declared_input=declared, write_artifacts=False)
    assert sci["TARGET_INDEPENDENCE_STATUS"] == "FAILED"
    assert sci["gate"]["audit"]["rejection"] == "NEW_INPUT_REJECTED_TARGET_DEPENDENT"
    asserted = _probe(motivation="selected to match measured masses")
    sci2 = analyze_phase11a_input_gate(auth, declared_input=asserted, write_artifacts=False)
    assert sci2["TARGET_INDEPENDENCE_STATUS"] == "FAILED"


def test_already_present_and_reformulation_rejected():
    auth = authorize_phase5b0_analysis()
    present = _probe(
        mathematical_statement="Lorentzian spacetime with Diff covariance in the stated gravity family",
        what_is_new="Lorentzian spacetime with Diff covariance in the stated gravity family",
        title="restated gravity",
    )
    sci = analyze_phase11a_input_gate(auth, declared_input=present, write_artifacts=False)
    assert sci["NOVELTY_AUDIT_STATUS"] == "ALREADY_PRESENT"
    assert sci["PHASE_11A_STATUS"] == "FAILED"
    reform = _probe(
        mathematical_statement="a0 = lambda_a and a1 = lambda_b - lambda_a for commutant_symmetric_K",
        what_is_new="reparameterization of lambda coefficients",
        title="operator reparameterization",
    )
    sci2 = analyze_phase11a_input_gate(auth, declared_input=reform, write_artifacts=False)
    assert sci2["NOVELTY_AUDIT_STATUS"] == "REDUNDANT_REFORMULATION"
    assert sci2["gate"]["audit"]["equivalence_outcome"] == "CERTIFIED_REFORMULATION"


def test_unsupported_equivalence_is_not_new():
    auth = authorize_phase5b0_analysis()
    declared = _probe(
        mathematical_statement="EQUIVALENCE_UNSUPPORTED is new physics for field-content listing",
        what_is_new="field-content listing is new physics",
        title="unsupported as new",
    )
    sci = analyze_phase11a_input_gate(auth, declared_input=declared, write_artifacts=False)
    assert sci["NOVELTY_AUDIT_STATUS"] != "GENUINELY_NEW"
    assert sci["PHASE_11A_STATUS"] != "READY_FOR_CONSEQUENCE_PHASE"


def test_parents_immutable_and_10e_preserved():
    before = _parent_bytes()
    grammar_before = grammar_hash()
    result = build_phase11a_input_model().solve()
    sci = result.metadata["phase11a_input_analysis"]
    after = _parent_bytes()
    assert before == after
    assert grammar_hash() == grammar_before
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["FINAL_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["UNIQUE_ACTION"] is False
    assert sci["UNIQUE_COUPLING"] is False
    assert sci["NEW_PHYSICAL_INPUT_REQUIRED"] is True
    assert sci["PHASE_10E_UNCHANGED"] is True
    assert sci["LEGACY_STRATEGY_11A_UNCHANGED"] is True
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["gate"]["PRE_NEW_INPUT_BASELINE"]["phase10e_synthesis_hash"] == EXPECTED_10E_SYNTHESIS_HASH


def test_input_hash_deterministic_and_versioned():
    a = _probe()
    b = _probe()
    assert input_hash(a) == input_hash(b)
    changed = _probe(mathematical_statement=a["mathematical_statement"] + " with a distinct extra clause")
    assert input_hash(a) != input_hash(changed)
    auth = authorize_phase5b0_analysis()
    sci_a = analyze_phase11a_input_gate(auth, declared_input=a, write_artifacts=False)
    sci_b = analyze_phase11a_input_gate(auth, declared_input=b, write_artifacts=False)
    assert sci_a["gate"]["audit"]["input_hash"] == sci_b["gate"]["audit"]["input_hash"]
    sci_c = analyze_phase11a_input_gate(auth, declared_input=changed, write_artifacts=False)
    assert sci_c["gate"]["audit"]["input_hash"] != sci_a["gate"]["audit"]["input_hash"]
    assert sci_a["NOVELTY_AUDIT_STATUS"] == "GENUINELY_NEW"
    assert sci_a["PHASE_11A_STATUS"] == "READY_FOR_CONSEQUENCE_PHASE"
    assert sci_a["INPUT_FREEZE_STATUS"] == "VERIFIED"
    assert not (artifact_dir() / "PHASE_11A_INPUT_FREEZE.json").exists()


def test_silent_fix_and_no_search_or_ranking():
    auth = authorize_phase5b0_analysis()
    declared = _probe(
        parameter_implications={
            "new_parameters": [],
            "constrained_parameters": ["c0"],
            "relations": [],
            "silently_fixes_existing": True,
        }
    )
    sci = analyze_phase11a_input_gate(auth, declared_input=declared, write_artifacts=False)
    assert sci["PARAMETER_AUDIT_STATUS"] == "FAILED"
    assert sci["PHASE_11A_STATUS"] == "FAILED"
    default = build_phase11a_input_model().solve().metadata["phase11a_input_analysis"]
    assert default["models_generated"] == 0
    assert default["principles_generated"] == 0
    assert default["NO_RANKING_PERFORMED"] is True
    assert default["machine_chose_principle"] is False


def test_provenance_relabel_and_incompatible_rejected():
    auth = authorize_phase5b0_analysis()
    derived = _probe(provenance="DERIVED")
    sci = analyze_phase11a_input_gate(auth, declared_input=derived, write_artifacts=False)
    assert sci["PROVENANCE_STATUS"] == "FAILED"
    assert sci["PHASE_11A_STATUS"] == "FAILED"
    frozen = _probe(mutates_frozen_action=True)
    sci2 = analyze_phase11a_input_gate(auth, declared_input=frozen, write_artifacts=False)
    assert sci2["COMPATIBILITY_STATUS"] == "INCOMPATIBLE"
    assert sci2["PHASE_11A_STATUS"] == "FAILED"


def test_no_machine_generated_principle_in_source():
    text = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "physics_lab"
        / "physics"
        / "phase11a_input_gate.py"
    ).read_text(encoding="utf-8")
    assert "generate_principle" not in text
    assert "principle_generation" not in text
    assert "analyze_phase10e_synthesis" not in text
    assert "analyze_phase11a_strategy" not in text
    for field in REQUIRED_INPUT_FIELDS:
        assert field in text


def test_full_audit_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11a_input_model(signature=sig).solve()
        sci = result.metadata["phase11a_input_analysis"]
        integ = result.metadata["phase11a_input_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["PHASE_11A_INPUT_TEST_COPY_ID"] == PHASE_11A_INPUT_TEST_COPY_ID
        assert sci["PHASE_11A_PRECONDITION_STATUS"] == "VERIFIED"
        assert sci["PHASE_11A_STATUS"] == "BLOCKED"
        assert sci["SCIENTIFIC_STOP"] == "STOP"
        assert sci["COMPATIBILITY_STATUS"] == "UNTESTED"


def test_artifacts_and_yaml_validator():
    build_phase11a_input_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_11A_INPUT_GATE.json",
        "PHASE_11A_INPUT_GATE_SUMMARY.json",
        "PRE_NEW_INPUT_BASELINE.json",
    ):
        assert (root / name).is_file(), name
    assert not (root / "PHASE_11A_INPUT_FREEZE.json").exists()
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11a_input.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11A input gate: pre-analysis gate",
        "Phase 11A input gate: coverage",
        "Phase 11A input gate: no numerical target comparison",
        "Phase 11A input gate: banned tokens",
        "Phase 11A input gate: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE 11A — NEW PHYSICAL INPUT GATE" in text
    assert "PHASE 11A INPUT GATE BLOCKED" in text
    assert "The machine did not invent a principle." in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11a_input_gate.py",
        root / "models" / "examples" / "phase11a_input_model.py",
        root / "reporting" / "phase11a_input_report.py",
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
        "analyze_phase10e_synthesis",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


def test_audit_helper_matches_analyze():
    import json

    synthesis = json.loads(
        (phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json").read_text(encoding="utf-8")
    )
    out = audit_human_declared_input(None, synthesis)
    assert out["HUMAN_INPUT_PRESENT"] is False
    assert out["NEW_PHYSICAL_INPUT_STATUS"] == "MISSING"
