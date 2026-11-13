"""Internal–external coupling: g is INPUT, n is DERIVED, not a charge."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.provenance import Provenance
from physics_lab.models.examples.coupling_model import build_coupling_model
from physics_lab.models.loader import load_model
from physics_lab.physics.coupling import analyze_coupling, gauge_covariance_holds
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_g_is_input_and_gn_tracks_n():
    result = build_coupling_model(g=2.5, n_max=4).solve()
    g = result.parameters.get("g")
    assert g.provenance is Provenance.INPUT
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        assert state.quantum_numbers["J"] == n
        assert abs(float(state.quantum_numbers["interaction_coefficient"]) - 2.5 * n) < 1e-12
        assert state.quantum_numbers["is_charge"] is False
    assert result.metadata["coupling_analysis"]["unique_coupling_prediction"] == "NO"
    assert result.metadata["coupling_analysis"]["fractional_coupling_structure"] == "NONE"
    assert result.metadata["charge_fractions"] == "NOT ASSIGNED"
    assert all(row.charge is None for row in result.mass_charge_table)


def test_g_not_fixed_by_radius():
    a = build_coupling_model(radius=1.0, g=1.0, n_max=2).solve()
    b = build_coupling_model(radius=7.0, g=1.0, n_max=2).solve()
    n1a = next(s for s in a.spectrum.states if int(s.quantum_numbers["n"]) == 1)
    n1b = next(s for s in b.spectrum.states if int(s.quantum_numbers["n"]) == 1)
    assert n1a.quantum_numbers["interaction_coefficient"] == n1b.quantum_numbers["interaction_coefficient"]
    assert a.metadata["coupling_analysis"]["g_from_geometry"]["verdict"] == "NOT PREDICTED"


def test_same_c3_sector_different_coupling():
    result = build_coupling_model(g=1.0, n_max=5).solve()
    ones = [
        s
        for s in result.spectrum.states
        if s.quantum_numbers.get("c3_sector") == 1
    ]
    ns = {int(s.quantum_numbers["n"]) for s in ones}
    assert {1, 4} <= ns or {-2, 1} <= ns
    coeffs = {float(s.quantum_numbers["interaction_coefficient"]) for s in ones}
    assert len(coeffs) >= 2


def test_no_one_third_in_coupling_source():
    src = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "models" / "examples" / "coupling_model.py"
    text = src.read_text(encoding="utf-8")
    assert "g: float = 1.0" in text
    assert "g = 1/3" not in text
    assert "CircleChargeObservable" not in text
    phys = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "physics" / "coupling.py"
    ptext = phys.read_text(encoding="utf-8")
    assert "from physics_lab.physics.constants" not in ptext
    assert "1/137" not in ptext
    assert "alpha = g" not in ptext


def test_gauge_and_yaml():
    assert gauge_covariance_holds(n=1)
    assert gauge_covariance_holds(n=-2)
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "coupling.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    assert by_name["Internal generator J"].status is CheckStatus.PASS
    assert by_name["Interaction term"].status is CheckStatus.PASS
    assert by_name["Coupling coefficient g"].status is CheckStatus.PASS
    assert by_name["Gauge consistency"].status is CheckStatus.PASS
    assert by_name["C3 vs coupling"].status is CheckStatus.PASS
    assert by_name["Coupling experimental firewall"].status is CheckStatus.PASS
    assert by_name["Alpha prediction"].status is CheckStatus.UNTESTED
    assert "INTERNAL-EXTERNAL COUPLING TEST" in report.text
    unused = [row for row in report.audit.rows if row.parameter == "1/3"]
    assert unused and unused[0].origin == "NOT USED"
    analysis = analyze_coupling(n_values=list(range(-5, 6)))
    assert analysis.alpha == "UNTESTED"
    assert analysis.charge_interpretation == "UNTESTED"
