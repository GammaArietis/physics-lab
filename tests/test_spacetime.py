"""Phase 3: spacetime principles do not select a unique scalar action."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.spacetime_model import build_spacetime_model
from physics_lab.models.loader import load_model
from physics_lab.physics.spacetime import MOSTLY_MINUS, MOSTLY_PLUS, analyze_spacetime
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_unique_action_is_no_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_spacetime_model(signature=sig).solve()
        data = result.metadata["spacetime_analysis"]
        assert data["unique_action"] == "NO"
        assert data["unique_kinetic_structure"] == "NO"
        assert data["canonical_kinetic_term"] == "NOT SELECTED"
        assert data["F_linear_in_X"] == "NOT DERIVED"
        assert data["quantum_unitarity"] == "UNTESTED"
        assert data["interpretation"] == "UNTESTED"
        assert data["signature_audit"]["signature_consistency"] == "PASS"
        assert data["examples"]["L2"]["eom_order"] == 2
        assert data["answers"]["1_lorentz_forces_quadratic"] == "NO"
        l5 = data["examples"]["L5"]
        assert l5["higher_derivative_in_L"] == "YES"
        assert l5["hessian_degenerate"] == "YES"
        assert l5["eom_higher_order"] == "NO"
        assert l5["ostrogradsky_instability"] == "NO"
        assert data["first_derivative_class"]["status"] == "COMPLETE AT FIRST-DERIVATIVE SCALAR LEVEL"
        assert data["phase3_status"]["Phase 3"] == "CLOSED"
        assert data["curved"]["dynamical_gravity"] == "NOT YET TESTED"


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "spacetime.py",
        root / "geometry" / "minkowski.py",
        root / "models" / "examples" / "spacetime_model.py",
        root / "reporting" / "spacetime_report.py",
        root / "tests" / "spacetime_test.py",
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
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "spacetime.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Spacetime: Lorentz scalars / boost",
        "Spacetime: signature contraction X",
        "Spacetime: Hamiltonian kinetic sign",
        "Spacetime: propagator / dispersion",
        "Spacetime: EOM order and Ostrogradsky",
        "Spacetime: locality vs derivative order",
        "Spacetime: general covariance branch",
        "Spacetime: field redefinition",
        "Spacetime: dimensional / no-scale",
        "Spacetime: uniqueness",
        "Spacetime: cross-signature equivalence",
        "Spacetime: mixed-convention trap",
        "Spacetime: Euclidean branch",
        "Spacetime: banned tokens",
        "Spacetime: experimental firewall",
        "Alpha prediction",
    ):
        status = by_name[name].status
        if name == "Alpha prediction":
            assert status is CheckStatus.UNTESTED
        else:
            assert status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "SPACETIME DYNAMICS TEST — PHASE 3" in report.text
    assert "SIGNATURE CONSISTENCY" in report.text
    assert "PHASE 3 STATUS" in report.text
    assert "COMPLETE AT FIRST-DERIVATIVE SCALAR LEVEL" in report.text
    analysis = analyze_spacetime(signature=MOSTLY_PLUS)
    assert analysis["unique_action"] == "NO"
