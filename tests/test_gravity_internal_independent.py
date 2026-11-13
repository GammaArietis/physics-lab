"""Independent Phase 4B checks: slots, conservation, and examples."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.gravity_internal import (
    MOSTLY_MINUS,
    MOSTLY_PLUS,
    action_matches_closed_form,
    conservation_identity_1p1,
    example_branch,
    field_redefinition_invariants,
    m_eff2_from_quadratic,
    metric_eom_from_variations,
    volume_inverse_metric_variation,
)
from physics_lab.physics.spacetime import canonical_prefactor


def test_independent_volume_and_T_variation():
    assert volume_inverse_metric_variation(MOSTLY_PLUS) is True
    assert volume_inverse_metric_variation(MOSTLY_MINUS) is True
    assert action_matches_closed_form(MOSTLY_PLUS) is True
    assert action_matches_closed_form(MOSTLY_MINUS) is True


def test_independent_conservation_both_signatures():
    assert conservation_identity_1p1(MOSTLY_PLUS) is True
    assert conservation_identity_1p1(MOSTLY_MINUS) is True


def test_independent_m_eff2_signature_adaptation():
    k2 = -1
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        m2 = m_eff2_from_quadratic(canonical_prefactor(sig), k2, sig)
        assert m2 == 1
    m0 = m_eff2_from_quadratic(canonical_prefactor(MOSTLY_PLUS), 0, MOSTLY_PLUS)
    assert m0 == 0


def test_independent_examples_T_not_forced():
    a = example_branch(MOSTLY_PLUS, massive=False)
    b = example_branch(MOSTLY_PLUS, massive=True)
    assert a["m_eff2"] == 0
    assert b["m_eff2"] == 1
    assert a["T00_wave_zero"] is False
    assert b["T00_wave_zero"] is False
    assert a["parameters_input"] is True
    assert b["parameters_input"] is True


def test_independent_field_redefinition():
    data = field_redefinition_invariants(MOSTLY_PLUS)
    assert data["m_eff2_invariant"] is True
    assert data["T_invariant"] is True
    assert data["canonical_is_unique_dynamics"] is False


def test_independent_metric_eom_coefficient():
    eom = metric_eom_from_variations()
    assert eom["equation"] == "c1 G_{mu nu} - (c0/2) g_{mu nu} = (1/2) T_{mu nu}"
    assert eom["equivalent"] == "2 c1 G_{mu nu} - c0 g_{mu nu} = T_{mu nu}"
    assert eom["not_inserted_einstein"] is True


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "gravity_internal.py",
        root / "models" / "examples" / "gravity_internal_model.py",
        root / "reporting" / "gravity_internal_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "1/" + "3" not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
        assert "6." + "674" not in text
