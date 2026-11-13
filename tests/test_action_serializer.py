"""ACTION_SERIALIZER_CONTRACT tests for PHASE_4C_ACTION_FREEZE."""

from __future__ import annotations

import copy
import os
import subprocess
import sys
from pathlib import Path

from physics_lab.models.examples.internal_spectrum_model import build_internal_spectrum_model
from physics_lab.models.loader import load_model
from physics_lab.physics.action_serializer import (
    SERIALIZER_SCHEMA,
    SerializationUnresolved,
    canonical_json_bytes,
    canonicalize_action,
    canonicalize_expr,
    fingerprint_canonical_action,
    serialize_action,
)
from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    freeze_is_verified,
    freeze_phase4c_action,
    phase4c_action_document,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _fp(document: dict) -> str:
    return serialize_action(document)["fingerprint"]


def test_1_serialize_twice_identical():
    doc = phase4c_action_document()
    a = serialize_action(doc)
    b = serialize_action(doc)
    assert a["canonical_bytes"] == b["canonical_bytes"]
    assert a["fingerprint"] == b["fingerprint"]
    assert a["fingerprint"] == fingerprint_canonical_action(a["canonical_action"])


def test_2_reorder_source_dictionaries():
    doc = phase4c_action_document()
    shuffled = _reverse_keys(copy.deepcopy(doc))
    shuffled["terms"] = list(reversed(shuffled["terms"]))
    shuffled["parameters"] = list(reversed(shuffled["parameters"]))
    shuffled["fields"] = list(reversed(shuffled["fields"]))
    shuffled["assumptions"] = list(reversed(shuffled["assumptions"]))
    shuffled["approximations"] = list(reversed(shuffled["approximations"]))
    assert _fp(doc) == _fp(shuffled)


def test_3_reorder_additive_terms():
    left = canonicalize_expr({"op": "add", "args": [{"symbol": "A"}, {"symbol": "B"}]})
    right = canonicalize_expr({"op": "add", "args": [{"symbol": "B"}, {"symbol": "A"}]})
    assert left == right
    nested = canonicalize_expr(
        {"op": "add", "args": [{"op": "add", "args": [{"symbol": "C"}, {"symbol": "A"}]}, {"symbol": "B"}]}
    )
    flat = canonicalize_expr(
        {"op": "add", "args": [{"symbol": "B"}, {"symbol": "A"}, {"symbol": "C"}]}
    )
    assert nested == flat
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    other["terms"] = list(reversed(other["terms"]))
    assert _fp(doc) == _fp(other)


def test_4_rename_implementation_variable():
    phi_field = {"id": "Phi", "type": "real_vector", "internal_dimension": 3}
    metric_field = {"id": "metric", "type": "metric", "spacetime_dimension": 4}
    the_field = phi_field
    spacetime_metric = metric_field
    doc = phase4c_action_document()
    rebuilt = copy.deepcopy(doc)
    rebuilt["fields"] = [spacetime_metric, the_field]
    assert _fp(doc) == _fp(rebuilt)


def test_5_change_physical_coefficient_identity():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    for term in other["terms"]:
        if term["id"] == "matter_kinetic":
            term["expression"]["integrand"]["args"][0] = {"symbol": "Z_renamed"}
    assert _fp(doc) != _fp(other)


def test_6_add_a_term():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    other["terms"].append(
        {
            "id": "extra_volume",
            "expression": {
                "op": "integral",
                "coords": "d4x",
                "density": "sqrt_minus_g",
                "integrand": {"symbol": "c0"},
            },
            "coefficients": ["c0"],
            "provenance": ["ASSUMED"],
        }
    )
    assert _fp(doc) != _fp(other)


def test_7_remove_a_term():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    other["terms"] = [t for t in other["terms"] if t["id"] != "matter_phi_sq"]
    assert _fp(doc) != _fp(other)


def test_8_change_a_sign():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    for term in other["terms"]:
        if term["id"] == "gravity_c0":
            term["expression"]["integrand"] = {
                "op": "mul",
                "args": [{"integer": -1}, {"symbol": "c0"}],
            }
    assert _fp(doc) != _fp(other)


def test_9_change_H_int():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    for term in other["terms"]:
        if term["id"] == "matter_H_int":
            matrix = term["expression"]["integrand"]["args"][2]["right"]["operator"]
            matrix["entries"][2][2] = {"symbol": "lam_a"}
    assert _fp(doc) != _fp(other)


def test_10_nonstructural_runtime_value_ignored():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    for param in other["parameters"]:
        if param["id"] == "lam_a":
            param["runtime_value"] = 17
            param["notes_runtime"] = "probe"
            param["value"] = 17
    assert _fp(doc) == _fp(other)


def test_11_structural_value_changes_hash():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    for param in other["parameters"]:
        if param["id"] == "internal_dimension":
            param["value"] = 4
    assert _fp(doc) != _fp(other)


def test_12_independent_executions():
    first = freeze_phase4c_action()["fingerprint"]
    second = freeze_phase4c_action()["fingerprint"]
    assert first == second
    src = Path(__file__).resolve().parents[1] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    code = (
        "from physics_lab.physics.phase4c_action_freeze import freeze_phase4c_action; "
        "print(freeze_phase4c_action()['fingerprint'])"
    )
    proc_a = subprocess.check_output([sys.executable, "-c", code], env=env, text=True).strip()
    proc_b = subprocess.check_output([sys.executable, "-c", code], env=env, text=True).strip()
    assert proc_a == proc_b == first
    assert len(first) == 64


def test_fail_closed_unknown_op_and_float():
    try:
        canonicalize_expr({"op": "guess", "args": []})
        raise AssertionError("unknown op must fail")
    except SerializationUnresolved as exc:
        assert exc.status == "SERIALIZATION_UNRESOLVED"
    try:
        canonicalize_expr({"integer": 0.5})
        raise AssertionError("float must fail")
    except SerializationUnresolved as exc:
        assert exc.status == "SERIALIZATION_UNRESOLVED"
    try:
        canonicalize_action({**phase4c_action_document(), "Noether": True})
        raise AssertionError("analysis keys must fail")
    except SerializationUnresolved as exc:
        assert exc.status == "SERIALIZATION_UNRESOLVED"


def test_scalar_mul_commutes_operators_do_not():
    a = canonicalize_expr(
        {"op": "mul", "args": [{"symbol": "a"}, {"symbol": "b"}, {"field": "Phi"}]}
    )
    b = canonicalize_expr(
        {"op": "mul", "args": [{"symbol": "b"}, {"symbol": "a"}, {"field": "Phi"}]}
    )
    assert a == b
    m1 = {
        "op": "matrix",
        "rows": 2,
        "cols": 2,
        "entries": [[{"integer": 0}, {"integer": 1}], [{"integer": 0}, {"integer": 0}]],
    }
    m2 = {
        "op": "matrix",
        "rows": 2,
        "cols": 2,
        "entries": [[{"integer": 0}, {"integer": 0}], [{"integer": 1}, {"integer": 0}]],
    }
    ab = canonicalize_expr({"op": "mul", "args": [m1, m2]})
    ba = canonicalize_expr({"op": "mul", "args": [m2, m1]})
    assert ab != ba


def test_zero_identity_and_rational_canonical():
    zero = canonicalize_expr(
        {
            "op": "matrix",
            "rows": 2,
            "cols": 2,
            "entries": [[{"integer": 0}, {"integer": 0}], [{"integer": 0}, {"integer": 0}]],
        }
    )
    assert zero == {"op": "zero_matrix", "rows": 2, "cols": 2}
    ident = canonicalize_expr(
        {
            "op": "matrix",
            "rows": 2,
            "cols": 2,
            "entries": [[{"integer": 1}, {"integer": 0}], [{"integer": 0}, {"integer": 1}]],
        }
    )
    assert ident == {"op": "identity_matrix", "dim": 2}
    assert canonicalize_expr({"rational": [2, 4]}) == {"rational": [1, 2]}
    assert canonicalize_expr({"rational": [2, 1]}) == {"integer": 2}


def test_schema_in_hashed_payload_and_freeze_envelope():
    freeze = freeze_phase4c_action()
    assert freeze["serializer_schema"] == SERIALIZER_SCHEMA
    assert freeze["canonical_action"]["serializer_schema"] == SERIALIZER_SCHEMA
    assert freeze["freeze_id"] == FREEZE_ID
    assert freeze_is_verified(freeze)
    blob = canonical_json_bytes(freeze["canonical_action"]).decode("utf-8")
    assert SERIALIZER_SCHEMA in blob
    assert "candidate generator" not in blob
    assert "Noether" not in blob
    assert freeze["basis_convention"]["hashed"] is False
    assert "BASIS_EQUIVALENCE_UNSUPPORTED" in freeze["unsupported_equivalences"]
    assert "basis_convention" not in freeze["canonical_action"]


def test_model_report_and_validator():
    result = build_internal_spectrum_model().solve()
    freeze = result.metadata["action_freeze"]
    assert freeze_is_verified(freeze)
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "internal_spectrum.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Action freeze: verified",
        "Action freeze: determinism",
        "Action freeze: no analysis leakage",
        "Action freeze: banned tokens",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert "ACTION_SERIALIZER_CONTRACT:" in report.text
    assert SERIALIZER_SCHEMA in report.text
    assert "ACTION_CONTENT_HASH:" in report.text
    assert freeze["fingerprint"] in report.text
    assert "SERIALIZER_STATUS:" in report.text
    assert "FREEZE_STATUS:" in report.text
    assert "unsupported_equivalences:" in report.text


def _reverse_keys(obj):
    if isinstance(obj, dict):
        return {k: _reverse_keys(v) for k, v in reversed(list(obj.items()))}
    if isinstance(obj, list):
        return [_reverse_keys(x) for x in obj]
    return obj
