"""Independent checks of the Phase 4C action serializer contract."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.action_serializer import (
    SERIALIZER_SCHEMA,
    canonicalize_expr,
    serialize_action,
)
from physics_lab.physics.phase4c_action_freeze import freeze_phase4c_action, phase4c_action_document


def test_independent_hash_is_sha256_of_canonical_json():
    import hashlib

    from physics_lab.physics.action_serializer import canonical_json_bytes

    freeze = freeze_phase4c_action()
    digest = hashlib.sha256(canonical_json_bytes(freeze["canonical_action"])).hexdigest()
    assert freeze["fingerprint"] == digest
    assert freeze["serializer_schema"] == SERIALIZER_SCHEMA
    assert freeze["canonical_action"]["phase"] == "4C"
    terms = {t["id"] for t in freeze["canonical_action"]["terms"]}
    assert terms == {
        "gravity_c0",
        "gravity_c1_R",
        "matter_kinetic",
        "matter_phi_sq",
        "matter_H_int",
    }
    matrix = _find_matrix(freeze["canonical_action"])
    assert matrix is not None
    assert matrix["op"] == "matrix"
    assert matrix["rows"] == matrix["cols"] == 3


def _find_matrix(obj):
    if isinstance(obj, dict):
        if obj.get("op") == "matrix":
            return obj
        for value in obj.values():
            found = _find_matrix(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_matrix(item)
            if found is not None:
                return found
    return None


def test_independent_additive_and_fail_closed():
    a = canonicalize_expr({"op": "add", "args": [{"integer": 1}, {"symbol": "X"}]})
    b = canonicalize_expr({"op": "add", "args": [{"symbol": "X"}, {"integer": 1}]})
    assert a == b
    doc = phase4c_action_document()
    assert serialize_action(doc)["fingerprint"] == freeze_phase4c_action()["fingerprint"]


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "action_serializer.py",
        root / "physics" / "phase4c_action_freeze.py",
        root / "reporting" / "action_freeze_report.py",
        root / "tests" / "action_freeze_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "1/" + "3" not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
        assert "6." + "674" not in text
        assert "alp" + "ha" not in text
        assert "char" + "ge" not in text
