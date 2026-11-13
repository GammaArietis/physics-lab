"""Phase 4A: dynamical metric does not uniquely select Einstein-Hilbert."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.dynamical_metric_model import build_dynamical_metric_model
from physics_lab.models.loader import load_model
from physics_lab.physics.dynamical_metric import MOSTLY_MINUS, MOSTLY_PLUS, analyze_dynamical_metric
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_unique_action_no_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_dynamical_metric_model(signature=sig).solve()
        data = result.metadata["dynamical_metric_analysis"]
        assert data["unique_action"] == "NO"
        assert data["unique_coefficients"] == "NO"
        assert data["unique_equations"] == "NO"
        assert data["unique_physical_theory"] == "NO"
        assert "DERIVED UNDER ASSUMPTIONS" in data["einstein_hilbert"]
        assert data["cosmological_term"] == "FREE"
        assert data["G"] == "FREE"
        assert data["Lambda"] == "FREE"
        assert data["c0_c1_determined"] == "NO"
        assert data["quantum_unitarity"] == "UNTESTED"
        assert data["full_dof_count"] == "UNTESTED"
        assert data["interpretation"] == "UNTESTED"
        assert data["gauss_bonnet_kernel"] is True
        assert data["lovelock_audit"]["computer_proved_lovelock"] is False
        assert data["lovelock_audit"]["d4"]["k2_check"] is True
        assert data["lovelock_audit"]["gb_d5_local"] is True
        assert data["equation_order"]["linear_EOM"] == 2
        assert data["equation_order"]["quadratic_EOM"] == 4
        assert data["answers"]["1_unique_from_cov_loc_metric"] == "NO"
        assert data["answers"]["6_G_Lambda"] == (
            "NO. newton_coupling and cosmo_scale are not determined. "
            "Reparametrizations are CONVENTION / DEFINITION."
        )


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "dynamical_metric.py",
        root / "physics" / "lovelock.py",
        root / "geometry" / "lorentzian_manifold.py",
        root / "models" / "examples" / "dynamical_metric_model.py",
        root / "reporting" / "dynamical_metric_report.py",
        root / "tests" / "dynamical_metric_test.py",
    ]
    banned = (
        "1/3",
        "2/3",
        "1/137",
        "137.036",
        "alpha",
        "charge",
        "electric",
        "mass",
        "from physics_lab.physics.constants",
        "6." + "674",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "dynamical_metric.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Dynamical metric: uniqueness",
        "Dynamical metric: gauss_bonnet",
        "Dynamical metric: Lovelock audit",
        "Dynamical metric: EOM order",
        "Dynamical metric: Bianchi identity",
        "Dynamical metric: diffeomorphism / charts",
        "Dynamical metric: signature consistency",
        "Dynamical metric: dimensions / provenance",
        "Dynamical metric: banned tokens",
        "Dynamical metric: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "PHASE 4A — DYNAMICAL METRIC TEST" in report.text
    assert "PHASE 4A — GENERAL METRIC DYNAMICS AUDIT" in report.text
    analysis = analyze_dynamical_metric(signature=MOSTLY_PLUS)
    assert analysis["unique_action"] == "NO"
    assert "DERIVED UNDER ASSUMPTIONS" in analysis["einstein_hilbert"]
