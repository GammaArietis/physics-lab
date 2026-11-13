"""Phase 5B.0: exact global symmetry of the frozen Phase 4C action."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase5b0_model import build_phase5b0_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_exact_so2_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase5b0_model(signature=sig).solve()
        sci = result.metadata["phase5b0_analysis"]
        integ = result.metadata["phase5b0_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert integ["ATOMIC_GATE"] == "VERIFIED"
        assert integ["ACTION_INTEGRITY"] == "VERIFIED"
        assert integ["ANALYSIS_ACTION_HASH"] == integ["FINAL_ACTION_HASH"]
        assert freeze["fingerprint"] == integ["ANALYSIS_ACTION_HASH"]
        assert sci["levels"]["A_H_int"] == "so(2)"
        assert sci["levels"]["B_kinetic"] == "so(3)"
        assert sci["levels"]["C_nonlinear"] == "ABSENT"
        assert sci["levels"]["D_mixing"] == "ABSENT"
        assert sci["levels"]["E_full_frozen_action"] == "so(2)"
        assert sci["SO2_congruent_U1"] is True
        assert sci["dim_V_b"] == 2
        assert sci["case_generic"].startswith("EXACT GLOBAL SO(2)")
        assert sci["case_lam_a_equals_lam_b"] == "PARAMETER-TUNED SYMMETRY"
        assert sci["noether_current"]["on_shell_conservation"] is True
        assert sci["noether_current"]["C"] == 2
        assert sci["noether_current"]["conservation_law_curved"] == "nabla_mu j^mu = 0"
        assert sci["noether_current"]["conservation_law_flat_limit"] == "partial_mu j^mu = 0"
        assert sci["noether_current"]["Q_Noether_identified_as_em"] is False
        assert sci["noether_current"]["existence_basis_independent"] is True
        assert sci["phase_5b0_closed"] is True
        assert sci["noether_breaking_test_copy"]["nabla_mu_j_mu_vanishes"] is False
        assert sci["noether_breaking_test_copy"]["frozen_baseline_modified"] is False
        assert sci["action_modifications_attempted"] is False
        assert sci["gauge_field_introduced"] is False
        assert sci["g_introduced"] is False
        assert sci["Z_A_introduced"] is False
        assert sci["experimental_constants"] is False
        assert sci["gravity_changed"] is False


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase5b0.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 5B.0: pre-analysis gate",
        "Phase 5B.0: full-action symmetry",
        "Phase 5B.0: Noether current",
        "Phase 5B.0: gravity unchanged",
        "Phase 5B.0: no rescue / no gauging",
        "Phase 5B.0: banned tokens",
        "Phase 5B.0: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "ACTION_SERIALIZER_CONTRACT:" in text
    assert "phase4c-action-v1" in text
    assert "PRE_ANALYSIS_GATE:" in text
    assert "ATOMIC_GATE:" in text
    assert "EXACT GLOBAL SO(2)" in text
    assert "Phase 5B.0 is CLOSED." in text
    assert "nabla_mu j^mu = 0" in text
    assert "NOT INTRODUCED" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase5b0_symmetry.py",
        root / "physics" / "phase5b0_gate.py",
        root / "models" / "examples" / "phase5b0_model.py",
        root / "reporting" / "phase5b0_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha_em",
        "electr" + "ic",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics.gauge_internal",
        "6." + "674",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
