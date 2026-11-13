"""Phase 4B: dynamical gravity plus internal scalar."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.gravity_internal_model import build_gravity_internal_model
from physics_lab.models.loader import load_model
from physics_lab.physics.gravity_internal import MOSTLY_MINUS, MOSTLY_PLUS, analyze_gravity_internal
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_common_origin_no_unique_relation_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_gravity_internal_model(signature=sig).solve()
        data = result.metadata["gravity_internal_analysis"]
        assert data["common_origin"] == "YES"
        assert data["unique_relation"] == "NO"
        assert data["c0"] == "INPUT / FREE"
        assert data["c1"] == "INPUT / FREE"
        assert data["c1_from_internal"] == "NO"
        assert data["m_eff2_without_free_parameters"] == "NO"
        assert data["chi_status"] == "INTERNAL DEGREE OF FREEDOM"
        assert data["chi_not"] == "extra dimension"
        assert data["newton_G_used_to_fix_c1"] is False
        assert data["case_A_class"] == "massless linearized mode"
        assert data["case_B_class"] == "massive linearized mode"
        assert data["case_A_massless_T_nonzero"] is True
        assert data["case_B_massive_T_nonzero"] is True
        assert data["conservation_1p1_check"] is True
        assert data["T_action_matches_closed_form"] is True
        assert data["field_redefinition_m_eff2_invariant"] is True
        assert data["field_redefinition_T_invariant"] is True
        assert data["canonical_unique_dynamics"] == "NO"
        assert data["quantum_unitarity"] == "UNTESTED"
        assert data["inertial_equals_gravitational"] == "UNTESTED / NOT CLAIMED"
        assert "no new parameter-free relation" in data["conclusion"]
        assert data["answers"]["5_c1_from_internal"].startswith("NO")
        assert data["answers"]["9_parameter_free_relation"].startswith("NO")


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "gravity_internal.py",
        root / "models" / "examples" / "gravity_internal_model.py",
        root / "reporting" / "gravity_internal_report.py",
    ]
    banned = (
        "1/" + "3",
        "2/" + "3",
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha",
        "char" + "ge",
        "electr" + "ic",
        "from physics_lab.physics." + "constants",
        "6." + "674",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "gravity_internal.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Gravity+internal: chi variation",
        "Gravity+internal: metric variation",
        "Gravity+internal: stress-energy",
        "Gravity+internal: covariant conservation",
        "Gravity+internal: background",
        "Gravity+internal: quadratic expansion",
        "Gravity+internal: m_eff2 / dispersion",
        "Gravity+internal: weak-field sourcing",
        "Gravity+internal: field normalization",
        "Gravity+internal: uniqueness / common origin",
        "Gravity+internal: banned tokens",
        "Gravity+internal: experimental firewall",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "PHASE 4B — DYNAMICAL GRAVITY + INTERNAL SECTOR" in report.text
    analysis = analyze_gravity_internal(signature=MOSTLY_PLUS)
    assert analysis["unique_relation"] == "NO"
    assert analysis["common_origin"] == "YES"
