"""Provenance firewall: inserted values cannot become DERIVED."""

from __future__ import annotations

import pytest

from physics_lab.core.parameter import Parameter
from physics_lab.core.provenance import (
    DerivationContext,
    ExperimentalLeakError,
    Provenance,
    ProvenanceError,
    combine_provenance,
)
from physics_lab.models.examples.circle_model import build_circle_model
from physics_lab.physics.charge import inspect_charge_fractions


def test_input_cannot_be_created_as_derived():
    with pytest.raises(ProvenanceError):
        Parameter(name="R", value=1.0, provenance=Provenance.DERIVED)


def test_input_cannot_be_reclassified_as_derived():
    p = Parameter(name="R", value=1.0, provenance=Provenance.INPUT)
    with pytest.raises(ProvenanceError):
        p.reclassify(Provenance.DERIVED)


def test_experimental_blocked_during_derivation():
    exp = Parameter(name="alpha_inverse", value=137.036, provenance=Provenance.EXPERIMENTAL)
    with DerivationContext("test"):
        with pytest.raises(ExperimentalLeakError):
            _ = exp.numeric


def test_experimental_readable_outside_derivation():
    exp = Parameter(name="alpha_inverse", value=137.036, provenance=Provenance.EXPERIMENTAL)
    assert exp.numeric == pytest.approx(137.036)


def test_combine_provenance_rejects_experimental():
    with pytest.raises(ExperimentalLeakError):
        combine_provenance(Provenance.INPUT, Provenance.EXPERIMENTAL)


def test_assumed_cannot_be_reclassified_as_derived():
    p = Parameter(name="C", value=1.0, provenance=Provenance.ASSUMED)
    with pytest.raises(ProvenanceError):
        p.reclassify(Provenance.DERIVED)


def test_calibrated_cannot_be_reclassified_as_derived():
    p = Parameter(name="kappa", value=1.0, provenance=Provenance.CALIBRATED)
    with pytest.raises(ProvenanceError):
        p.reclassify(Provenance.DERIVED)
    assert "NOT a prediction" in (p.warning_if_not_prediction() or "")
    from physics_lab.core.result import Quantity

    qty = Quantity(name="alpha", value=137.0, provenance=Provenance.CALIBRATED)
    assert qty.is_prediction() is False


def test_experimental_value_attribute_blocked_during_derivation():
    exp = Parameter(name="alpha_inverse", value=137.036, provenance=Provenance.EXPERIMENTAL)
    with DerivationContext("test"):
        with pytest.raises(ExperimentalLeakError):
            _ = exp.value
        with pytest.raises(ExperimentalLeakError):
            _ = exp.numeric


def test_yaml_rejects_derived_label_on_inserted_parameter(tmp_path):
    from physics_lab.core.provenance import ProvenanceError
    from physics_lab.models.loader import build_from_config

    with pytest.raises(ProvenanceError):
        build_from_config(
            {
                "name": "circle_model",
                "parameters": {"R": {"value": 1.0, "provenance": "DERIVED"}},
            }
        )


def test_circle_rejects_experimental_parameter():
    from physics_lab.core.model import Model

    model = build_circle_model()
    model.parameters.add(
        Parameter(name="alpha_inverse", value=137.036, provenance=Provenance.EXPERIMENTAL)
    )
    with pytest.raises(ExperimentalLeakError):
        model.solve()


def test_inserted_one_third_is_not_a_prediction():
    model = build_circle_model(
        extra_parameters=[
            Parameter(name="charge_fraction", value=1.0 / 3.0, provenance=Provenance.INPUT)
        ]
    )
    result = model.solve()
    charges = [row.charge.numeric() for row in result.mass_charge_table if row.charge]
    report = inspect_charge_fractions(charges, result.parameters)
    assert report.inserted_one_third is True
    assert report.status == "NOT A PREDICTION"


def test_constants_module_is_experimental_only():
    from physics_lab.physics import constants

    assert constants.ALPHA_INVERSE.provenance is Provenance.EXPERIMENTAL
    assert constants.ALPHA.provenance is Provenance.EXPERIMENTAL


def test_circle_model_source_does_not_import_experimental_constants():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "physics_lab"
        / "models"
        / "examples"
        / "circle_model.py"
    ).read_text(encoding="utf-8")
    assert "physics_lab.physics.constants" not in source
    assert "ALPHA_INVERSE" not in source
    assert "137.036" not in source
