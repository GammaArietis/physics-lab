"""Validator scorecard behaviour."""

from __future__ import annotations

from physics_lab.core.provenance import Provenance
from physics_lab.models.examples.circle_model import build_circle_model
from physics_lab.models.examples.toy_mass_charge import build_toy_mass_charge_model
from physics_lab.reporting.audit import audit_parameters
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_scorecard_has_no_overall_score():
    report = validate(build_circle_model())
    assert "8/10" not in report.text
    assert "overall score" in report.text.lower()
    allowed = {s.value for s in CheckStatus}
    for check in report.checks:
        assert check.status.value in allowed


def test_audit_lists_free_parameters_and_unused_watched_quantities():
    model = build_circle_model()
    result = model.solve()
    audit = audit_parameters(model, result)
    names = {row.parameter: row for row in audit.rows}
    assert names["R"].origin == "INPUT"
    assert names["C"].origin == "INPUT"
    assert names["1/3"].origin == "NOT USED"
    assert names["alpha"].origin == "NOT USED"
    assert audit.free_count >= 3
    assert audit.calibrated_count == 0


def test_calibrated_parameter_is_counted():
    model = build_circle_model(provenances={"kappa": Provenance.CALIBRATED})
    report = validate(model)
    assert report.audit.calibrated_count == 1
    assert any("calibrated" in w.lower() for w in report.result.warnings)


def test_toy_mass_charge_table():
    report = validate(build_toy_mass_charge_model())
    table = report.result.mass_charge_table
    assert len(table) == 3
    assert all(row.mass is not None and row.charge is not None for row in table)


def test_interference_untested_on_circle():
    report = validate(build_circle_model())
    check = report.check("Interference")
    assert check is not None
    assert check.status is CheckStatus.UNTESTED
