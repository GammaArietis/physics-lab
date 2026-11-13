"""S¹ + C3 exploration: sectors from the C3 action, no charge assignment."""

from __future__ import annotations

from pathlib import Path

import sympy as sp

from physics_lab.geometry.c3_action import C3_ORDER, analyze_c3_on_n, c3_cube_roots
from physics_lab.models.examples.circle_model import build_circle_model
from physics_lab.models.examples.s1_c3_model import build_s1_c3_model
from physics_lab.models.loader import load_model
from physics_lab.reporting.exploration import compare_s1_and_s1_c3, new_properties_from_c3
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_s1_still_derives_integer_n():
    result = build_s1_c3_model(n_max=5).solve()
    ns = [int(s.quantum_numbers["n"]) for s in result.spectrum.states]
    assert ns == list(range(-5, 6))
    assert result.metadata["n_origin"] == "derived from PBC"
    assert result.metadata["k_quantization"].integer_n_derived is True
    assert result.metadata["half_integer_rejected"] is True


def test_c3_phase_depends_on_n():
    result = build_s1_c3_model(n_max=3).solve()
    phases = {int(s.quantum_numbers["n"]): s.quantum_numbers["c3_phase"] for s in result.spectrum.states}
    assert phases[0] == "1"
    assert len({phases[0], phases[1], phases[2]}) == 3


def test_c3_cubed_is_identity():
    result = build_s1_c3_model(n_max=4).solve()
    assert result.metadata["c3_cubed_identity"] is True
    for row in result.metadata["c3_actions"]:
        assert row["cubed_is_identity"] is True


def test_sectors_derived_from_phase_matching_not_inserted():
    result = build_s1_c3_model(n_max=5).solve()
    assert result.metadata["c3_residue_form"] is True
    assert set(result.metadata["c3_sectors"]) >= {0, 1, 2}
    for state in result.spectrum.states:
        n = int(state.quantum_numbers["n"])
        r = state.quantum_numbers["c3_sector"]
        phase = sp.exp(sp.I * n * 2 * sp.pi / C3_ORDER)
        matched = None
        for idx, root in enumerate(c3_cube_roots()):
            if sp.simplify(phase - root) == 0:
                matched = idx
                break
        assert matched == r
        assert (n - r) % 3 == 0


def test_no_charge_assigned():
    result = build_s1_c3_model().solve()
    assert result.metadata["charge_fractions"] == "NOT ASSIGNED"
    assert all(row.charge is None for row in result.mass_charge_table)
    for param in result.parameters:
        assert param.name.lower() not in {"fraction", "charge_fraction", "one_third"}
        assert abs(float(param.value) - 1.0 / 3.0) > 1e-12


def test_source_does_not_search_for_one_third():
    src = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "models" / "examples" / "s1_c3_model.py"
    text = src.read_text(encoding="utf-8")
    assert "def find_one_third" not in text
    assert "charge_fraction =" not in text
    assert "CircleChargeObservable" not in text


def test_mass_mechanism_unchanged():
    result = build_s1_c3_model().solve()
    masses = [row.mass for row in result.mass_charge_table if row.mass is not None]
    assert masses
    assert all(m.provenance.value == "ASSUMED" for m in masses)


def test_hamiltonian_spectrum_matches_s1():
    s1 = build_circle_model(n_max=5, include_charge=False, include_momentum=False).solve()
    both = build_s1_c3_model(n_max=5).solve()
    lam_a = [round(s.eigenvalue.numeric(), 12) for s in s1.spectrum.states]
    lam_b = [round(s.eigenvalue.numeric(), 12) for s in both.spectrum.states]
    assert lam_a == lam_b


def test_validator_and_yaml():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "s1_c3.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    assert by_name["C3 action"].status is CheckStatus.PASS
    assert by_name["C3 cubed identity"].status is CheckStatus.PASS
    assert by_name["C3 sectors"].status is CheckStatus.PASS
    assert by_name["Fractional charge"].status is CheckStatus.UNTESTED
    assert "INTERNAL STRUCTURE EXPLORATION" in report.text
    assert "DERIVED FROM C3 SYMMETRY" in report.text
    assert "1/3" in {row.parameter for row in report.audit.rows}
    unused = [row for row in report.audit.rows if row.parameter == "1/3"]
    assert unused and unused[0].origin == "NOT USED"


def test_compare_lists_c3_additions_without_score():
    a = build_circle_model(n_max=5, include_charge=False)
    b = build_s1_c3_model(n_max=5)
    ra, rb = a.solve(), b.solve()
    text = compare_s1_and_s1_c3(a, ra, b, rb)
    assert "No model is scored" in text
    assert "better" in text.lower()
    props = new_properties_from_c3(ra, rb)
    assert any("C3 action" in p for p in props)
    assert any("unchanged" in p for p in props)


def test_analyze_c3_on_n_matches_formula():
    action = analyze_c3_on_n(4, 1.0)
    assert action.sector == 1
    assert action.cubed_is_identity is True
    assert sp.simplify(action.phase - sp.exp(sp.I * 8 * sp.pi / 3)) == 0
