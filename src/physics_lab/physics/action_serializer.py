"""ACTION_SERIALIZER_CONTRACT: deterministic identity of a frozen action.

This module does not decide physical equivalence, add terms, or modify
gravity.  It converts an already-defined action document into canonical
JSON and a SHA-256 fingerprint.  Unknown forms fail closed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

__all__ = [
    "SERIALIZER_SCHEMA",
    "SERIALIZATION_UNRESOLVED",
    "SerializationUnresolved",
    "canonical_json_bytes",
    "canonicalize_action",
    "fingerprint_canonical_action",
    "serialize_action",
]


SERIALIZER_SCHEMA = "phase4c-action-v1"
SERIALIZATION_UNRESOLVED = "SERIALIZATION_UNRESOLVED"
CONTRACT_NAME = "ACTION_SERIALIZER_CONTRACT"

_TOP_LEVEL_KEYS = (
    "serializer_schema",
    "phase",
    "action_type",
    "spacetime",
    "fields",
    "internal_space",
    "parameters",
    "terms",
    "assumptions",
    "approximations",
)

_ALLOWED_PROVENANCE = frozenset(
    {
        "INPUT",
        "ASSUMED",
        "CONVENTION",
        "PARAMETER-DEPENDENT",
        "CALIBRATED",
        "EXPERIMENTAL",
        "DERIVED",
        "METHOD / INTEGRITY CONTROL",
    }
)

_EXPR_OPS = frozenset(
    {
        "add",
        "mul",
        "pow",
        "derivative",
        "contraction",
        "matrix",
        "inner_product",
        "trace",
        "operator_application",
        "integral",
        "metric_contraction",
        "identity_matrix",
        "zero_matrix",
        "neg",
    }
)

_IGNORED_PARAM_KEYS = frozenset({"runtime_value", "notes_runtime"})

_UNSUPPORTED = (
    "BASIS_EQUIVALENCE_UNSUPPORTED",
    "GENERAL_OPERATOR_REORDERING_UNSUPPORTED",
    "ALGEBRAIC_SIMPLIFICATION_UNSUPPORTED",
)


class SerializationUnresolved(Exception):
    """Fail-closed: the serializer will not guess an encoding."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"{SERIALIZATION_UNRESOLVED}: {detail}")
        self.status = SERIALIZATION_UNRESOLVED
        self.detail = detail


def canonical_json_bytes(obj: Any) -> bytes:
    """UTF-8 JSON with sorted keys and no extra whitespace."""
    try:
        text = json.dumps(
            obj,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise SerializationUnresolved(f"JSON encoding failed: {exc}") from exc
    return text.encode("utf-8")


def _canon_key(obj: Any) -> str:
    return canonical_json_bytes(obj).decode("utf-8")


def _require_dict(obj: Any, label: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise SerializationUnresolved(f"{label} must be an object")
    for key in obj:
        if not isinstance(key, str):
            raise SerializationUnresolved(f"{label} has a non-string key")
    return obj


def _require_list(obj: Any, label: str) -> list[Any]:
    if not isinstance(obj, list):
        raise SerializationUnresolved(f"{label} must be an array")
    return obj


def _check_provenance(value: Any, label: str) -> str | list[str]:
    if isinstance(value, list):
        out = []
        for item in value:
            if item not in _ALLOWED_PROVENANCE:
                raise SerializationUnresolved(f"{label}: unknown provenance {item!r}")
            out.append(item)
        return sorted(out)
    if value not in _ALLOWED_PROVENANCE:
        raise SerializationUnresolved(f"{label}: unknown provenance {value!r}")
    return value


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a) or 1


def canon_rational(p: Any, q: Any) -> dict[str, Any]:
    if type(p) is not int or type(q) is not int:
        raise SerializationUnresolved("rational parts must be integers")
    if q == 0:
        raise SerializationUnresolved("rational denominator is zero")
    if q < 0:
        p, q = -p, -q
    g = _gcd(p, q)
    p //= g
    q //= g
    if q == 1:
        return {"integer": p}
    return {"rational": [p, q]}


def _is_commuting_scalar(expr: dict[str, Any]) -> bool:
    if "integer" in expr or "rational" in expr or "symbol" in expr:
        return True
    if "real_constant" in expr or "field" in expr:
        return True
    op = expr.get("op")
    if op in {"add", "mul", "pow", "neg", "inner_product", "trace", "integral"}:
        return True
    if op in {"matrix", "operator_application", "identity_matrix", "zero_matrix"}:
        return False
    if op in {"derivative", "contraction", "metric_contraction"}:
        return True
    return False


def canonicalize_expr(expr: Any) -> dict[str, Any]:
    node = _require_dict(expr, "expression")
    if "op" in node:
        return _canonicalize_op(node)
    if "integer" in node:
        if set(node) != {"integer"}:
            raise SerializationUnresolved("integer node has extra keys")
        if type(node["integer"]) is not int:
            raise SerializationUnresolved("integer value must be an int")
        return {"integer": node["integer"]}
    if "rational" in node:
        if set(node) != {"rational"}:
            raise SerializationUnresolved("rational node has extra keys")
        pair = node["rational"]
        if not isinstance(pair, list) or len(pair) != 2:
            raise SerializationUnresolved("rational must be [p, q]")
        return canon_rational(pair[0], pair[1])
    if "symbol" in node:
        if set(node) != {"symbol"}:
            raise SerializationUnresolved("symbol node has extra keys")
        name = node["symbol"]
        if not isinstance(name, str) or not name:
            raise SerializationUnresolved("symbol name must be a nonempty string")
        return {"symbol": name}
    if "field" in node:
        if set(node) != {"field"}:
            raise SerializationUnresolved("field node has extra keys")
        name = node["field"]
        if not isinstance(name, str) or not name:
            raise SerializationUnresolved("field id must be a nonempty string")
        return {"field": name}
    if "real_constant" in node:
        if set(node) != {"real_constant"}:
            raise SerializationUnresolved("real_constant node has extra keys")
        name = node["real_constant"]
        if not isinstance(name, str) or not name:
            raise SerializationUnresolved("real_constant must be a named constant")
        return {"real_constant": name}
    raise SerializationUnresolved("expression is not a recognized node")


def _canonicalize_op(node: dict[str, Any]) -> dict[str, Any]:
    op = node["op"]
    if op not in _EXPR_OPS:
        raise SerializationUnresolved(f"unsupported op {op!r}")
    if op == "add":
        raw = _require_list(node.get("args"), "add.args")
        flat: list[dict[str, Any]] = []
        for item in raw:
            canon = canonicalize_expr(item)
            if canon.get("op") == "add":
                flat.extend(canon["args"])
            elif canon != {"integer": 0}:
                flat.append(canon)
        if not flat:
            return {"integer": 0}
        flat.sort(key=_canon_key)
        combined: list[dict[str, Any]] = []
        counts: list[int] = []
        for item in flat:
            if combined and item == combined[-1]:
                counts[-1] += 1
            else:
                combined.append(item)
                counts.append(1)
        out_args: list[dict[str, Any]] = []
        for item, n in zip(combined, counts):
            if n == 1:
                out_args.append(item)
            else:
                out_args.append(
                    canonicalize_expr({"op": "mul", "args": [{"integer": n}, item]})
                )
        if len(out_args) == 1:
            return out_args[0]
        return {"op": "add", "args": out_args}
    if op == "mul":
        raw = _require_list(node.get("args"), "mul.args")
        scalars: list[dict[str, Any]] = []
        others: list[dict[str, Any]] = []
        for item in raw:
            canon = canonicalize_expr(item)
            if canon.get("op") == "mul":
                parts = canon["args"]
            elif canon == {"integer": 1}:
                parts = []
            elif canon == {"integer": 0}:
                return {"integer": 0}
            else:
                parts = [canon]
            for part in parts:
                if _is_commuting_scalar(part):
                    scalars.append(part)
                else:
                    others.append(part)
        scalars.sort(key=_canon_key)
        args = scalars + others
        if not args:
            return {"integer": 1}
        if len(args) == 1:
            return args[0]
        return {"op": "mul", "args": args}
    if op == "neg":
        return canonicalize_expr(
            {"op": "mul", "args": [{"integer": -1}, node.get("arg")]}
        )
    if op == "pow":
        return {
            "op": "pow",
            "base": canonicalize_expr(node.get("base")),
            "exp": canonicalize_expr(node.get("exp")),
        }
    if op == "derivative":
        field = node.get("field")
        index = node.get("index")
        if not isinstance(field, str) or not field:
            raise SerializationUnresolved("derivative.field must be a field id")
        if not isinstance(index, str) or not index:
            raise SerializationUnresolved("derivative.index must be a string")
        return {"op": "derivative", "field": field, "index": index}
    if op == "inner_product":
        return {
            "op": "inner_product",
            "left": canonicalize_expr(node.get("left")),
            "right": canonicalize_expr(node.get("right")),
        }
    if op == "trace":
        return {"op": "trace", "arg": canonicalize_expr(node.get("arg"))}
    if op == "operator_application":
        return {
            "op": "operator_application",
            "operator": canonicalize_expr(node.get("operator")),
            "operand": canonicalize_expr(node.get("operand")),
        }
    if op == "contraction":
        return {
            "op": "contraction",
            "left": canonicalize_expr(node.get("left")),
            "right": canonicalize_expr(node.get("right")),
            "indices": _require_list(node.get("indices"), "contraction.indices"),
        }
    if op == "metric_contraction":
        indices = _require_list(node.get("indices"), "metric_contraction.indices")
        for idx in indices:
            if not isinstance(idx, str):
                raise SerializationUnresolved("metric_contraction indices must be strings")
        return {
            "op": "metric_contraction",
            "metric": canonicalize_expr(node.get("metric")),
            "indices": list(indices),
            "operand": canonicalize_expr(node.get("operand")),
        }
    if op == "integral":
        coords = node.get("coords")
        density = node.get("density")
        if not isinstance(coords, str) or not coords:
            raise SerializationUnresolved("integral.coords must be a string")
        if not isinstance(density, str) or not density:
            raise SerializationUnresolved("integral.density must be a string")
        return {
            "op": "integral",
            "coords": coords,
            "density": density,
            "integrand": canonicalize_expr(node.get("integrand")),
        }
    if op == "identity_matrix":
        dim = node.get("dim")
        if type(dim) is not int or dim <= 0:
            raise SerializationUnresolved("identity_matrix.dim must be a positive int")
        return {"op": "identity_matrix", "dim": dim}
    if op == "zero_matrix":
        rows = node.get("rows")
        cols = node.get("cols")
        if type(rows) is not int or type(cols) is not int or rows <= 0 or cols <= 0:
            raise SerializationUnresolved("zero_matrix dimensions must be positive ints")
        return {"op": "zero_matrix", "rows": rows, "cols": cols}
    if op == "matrix":
        rows = node.get("rows")
        cols = node.get("cols")
        entries = _require_list(node.get("entries"), "matrix.entries")
        if type(rows) is not int or type(cols) is not int or rows <= 0 or cols <= 0:
            raise SerializationUnresolved("matrix dimensions must be positive ints")
        if len(entries) != rows:
            raise SerializationUnresolved("matrix.entries row count mismatch")
        canon_rows = []
        for row in entries:
            line = _require_list(row, "matrix row")
            if len(line) != cols:
                raise SerializationUnresolved("matrix.entries column count mismatch")
            canon_rows.append([canonicalize_expr(cell) for cell in line])
        special = _zero_or_identity_matrix(rows, cols, canon_rows)
        if special is not None:
            return special
        return {"op": "matrix", "rows": rows, "cols": cols, "entries": canon_rows}
    raise SerializationUnresolved(f"unhandled op {op!r}")


def _zero_or_identity_matrix(
    rows: int, cols: int, canon_rows: list[list[dict[str, Any]]]
) -> dict[str, Any] | None:
    """Declared 0 / 1 matrix forms only. No diagonalization."""
    zero = {"integer": 0}
    one = {"integer": 1}
    is_zero = True
    is_id = rows == cols
    for i, row in enumerate(canon_rows):
        for j, cell in enumerate(row):
            if cell != zero:
                is_zero = False
            if cell != (one if i == j else zero):
                is_id = False
    if is_zero:
        return {"op": "zero_matrix", "rows": rows, "cols": cols}
    if is_id:
        return {"op": "identity_matrix", "dim": rows}
    return None


def _canon_parameter(item: Any) -> dict[str, Any]:
    rec = _require_dict(item, "parameter")
    extra = set(rec) - {
        "id",
        "role",
        "provenance",
        "symbolic",
        "value_is_structural",
        "value",
        *_IGNORED_PARAM_KEYS,
    }
    if extra:
        raise SerializationUnresolved(f"parameter extra keys {sorted(extra)}")
    pid = rec.get("id")
    if not isinstance(pid, str) or not pid:
        raise SerializationUnresolved("parameter.id must be a nonempty string")
    symbolic = rec.get("symbolic")
    if not isinstance(symbolic, bool):
        raise SerializationUnresolved(f"parameter {pid}: symbolic must be boolean")
    structural = rec.get("value_is_structural", False)
    if not isinstance(structural, bool):
        raise SerializationUnresolved(f"parameter {pid}: value_is_structural must be boolean")
    out: dict[str, Any] = {
        "id": pid,
        "provenance": _check_provenance(rec.get("provenance"), f"parameter {pid}"),
        "role": rec.get("role"),
        "symbolic": symbolic,
        "value_is_structural": structural,
    }
    if not isinstance(out["role"], str) or not out["role"]:
        raise SerializationUnresolved(f"parameter {pid}: role required")
    if structural:
        if "value" not in rec:
            raise SerializationUnresolved(f"parameter {pid}: structural value missing")
        out["value"] = _canon_structural_value(rec["value"], pid)
    return out


def _canon_structural_value(value: Any, pid: str) -> Any:
    if isinstance(value, bool) or type(value) is int:
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return canonicalize_expr(value)
    raise SerializationUnresolved(f"parameter {pid}: structural value is not canonical")


def _canon_field(item: Any) -> dict[str, Any]:
    rec = _require_dict(item, "field")
    fid = rec.get("id")
    ftype = rec.get("type")
    if not isinstance(fid, str) or not fid:
        raise SerializationUnresolved("field.id must be a nonempty string")
    if not isinstance(ftype, str) or not ftype:
        raise SerializationUnresolved(f"field {fid}: type required")
    out: dict[str, Any] = {"id": fid, "type": ftype}
    if "internal_dimension" in rec:
        dim = rec["internal_dimension"]
        if type(dim) is not int or dim <= 0:
            raise SerializationUnresolved(f"field {fid}: internal_dimension invalid")
        out["internal_dimension"] = dim
    if "spacetime_dimension" in rec:
        dim = rec["spacetime_dimension"]
        if type(dim) is not int or dim <= 0:
            raise SerializationUnresolved(f"field {fid}: spacetime_dimension invalid")
        out["spacetime_dimension"] = dim
    extra = set(rec) - {
        "id",
        "type",
        "internal_dimension",
        "spacetime_dimension",
    }
    if extra:
        raise SerializationUnresolved(f"field {fid}: extra keys {sorted(extra)}")
    return out


def _canon_term(item: Any) -> dict[str, Any]:
    rec = _require_dict(item, "term")
    tid = rec.get("id")
    if not isinstance(tid, str) or not tid:
        raise SerializationUnresolved("term.id must be a nonempty string")
    extra = set(rec) - {"id", "expression", "coefficients", "provenance"}
    if extra:
        raise SerializationUnresolved(f"term {tid}: extra keys {sorted(extra)}")
    coeffs = _require_list(rec.get("coefficients"), f"term {tid} coefficients")
    for c in coeffs:
        if not isinstance(c, str):
            raise SerializationUnresolved(f"term {tid}: coefficient ids must be strings")
    return {
        "id": tid,
        "expression": canonicalize_expr(rec.get("expression")),
        "coefficients": sorted(coeffs),
        "provenance": _check_provenance(rec.get("provenance"), f"term {tid}"),
    }


def _canon_assumption(item: Any) -> dict[str, Any]:
    rec = _require_dict(item, "assumption")
    aid = rec.get("id")
    if not isinstance(aid, str) or not aid:
        raise SerializationUnresolved("assumption.id must be a nonempty string")
    out: dict[str, Any] = {
        "id": aid,
        "value": rec.get("value"),
        "provenance": _check_provenance(rec.get("provenance"), f"assumption {aid}"),
    }
    if isinstance(out["value"], float):
        raise SerializationUnresolved(f"assumption {aid}: floating-point values are forbidden")
    if type(out["value"]) not in (bool, int, str) and out["value"] is not None:
        if isinstance(out["value"], dict):
            out["value"] = canonicalize_expr(out["value"])
        else:
            raise SerializationUnresolved(f"assumption {aid}: value is not canonical")
    extra = set(rec) - {"id", "value", "provenance"}
    if extra:
        raise SerializationUnresolved(f"assumption {aid}: extra keys {sorted(extra)}")
    return out


def _strip_ignored(rec: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in rec.items() if k not in _IGNORED_PARAM_KEYS}


def canonicalize_action(document: dict[str, Any]) -> dict[str, Any]:
    """Return the hashed payload.  Extra top-level keys fail closed."""
    doc = _require_dict(document, "canonical_action")
    extra = set(doc) - set(_TOP_LEVEL_KEYS)
    if extra:
        raise SerializationUnresolved(f"action has extra keys {sorted(extra)}")
    missing = [k for k in _TOP_LEVEL_KEYS if k not in doc]
    if missing:
        raise SerializationUnresolved(f"action missing keys {missing}")
    schema = doc["serializer_schema"]
    if schema != SERIALIZER_SCHEMA:
        raise SerializationUnresolved(
            f"serializer_schema {schema!r} is not {SERIALIZER_SCHEMA}"
        )
    spacetime = _require_dict(doc["spacetime"], "spacetime")
    extra_st = set(spacetime) - {"dimension", "signature_class", "volume_element"}
    if extra_st:
        raise SerializationUnresolved(f"spacetime extra keys {sorted(extra_st)}")
    if type(spacetime.get("dimension")) is not int or spacetime["dimension"] <= 0:
        raise SerializationUnresolved("spacetime.dimension must be a positive int")
    if not isinstance(spacetime.get("signature_class"), str):
        raise SerializationUnresolved("spacetime.signature_class must be a string")
    if not isinstance(spacetime.get("volume_element"), str):
        raise SerializationUnresolved("spacetime.volume_element must be a string")
    internal = _require_dict(doc["internal_space"], "internal_space")
    extra_in = set(internal) - {"type", "dimension", "status"}
    if extra_in:
        raise SerializationUnresolved(f"internal_space extra keys {sorted(extra_in)}")
    if type(internal.get("dimension")) is not int or internal["dimension"] <= 0:
        raise SerializationUnresolved("internal_space.dimension must be a positive int")
    if not isinstance(internal.get("type"), str) or not internal["type"]:
        raise SerializationUnresolved("internal_space.type must be a nonempty string")
    _check_provenance(internal.get("status"), "internal_space.status")
    fields = [_canon_field(item) for item in _require_list(doc["fields"], "fields")]
    params = [
        _canon_parameter(_strip_ignored(item) if isinstance(item, dict) else item)
        for item in _require_list(doc["parameters"], "parameters")
    ]
    terms = [_canon_term(item) for item in _require_list(doc["terms"], "terms")]
    assumptions = [
        _canon_assumption(item) for item in _require_list(doc["assumptions"], "assumptions")
    ]
    approximations = _require_list(doc["approximations"], "approximations")
    canon_approx = []
    for item in approximations:
        rec = _require_dict(item, "approximation")
        extra = set(rec) - {"id", "statement", "provenance"}
        if extra:
            raise SerializationUnresolved(f"approximation extra keys {sorted(extra)}")
        aid = rec.get("id")
        if not isinstance(aid, str) or not aid:
            raise SerializationUnresolved("approximation.id required")
        statement = rec.get("statement")
        if not isinstance(statement, str) or not statement:
            raise SerializationUnresolved(f"approximation {aid}: statement required")
        canon_approx.append(
            {
                "id": aid,
                "statement": statement,
                "provenance": _check_provenance(rec.get("provenance"), f"approximation {aid}"),
            }
        )
    fields.sort(key=_canon_key)
    params.sort(key=_canon_key)
    terms.sort(key=_canon_key)
    assumptions.sort(key=_canon_key)
    canon_approx.sort(key=_canon_key)
    if not isinstance(doc["phase"], str) or not isinstance(doc["action_type"], str):
        raise SerializationUnresolved("phase and action_type must be strings")
    return {
        "action_type": doc["action_type"],
        "approximations": canon_approx,
        "assumptions": assumptions,
        "fields": fields,
        "internal_space": {
            "dimension": internal.get("dimension"),
            "status": internal.get("status"),
            "type": internal.get("type"),
        },
        "parameters": params,
        "phase": doc["phase"],
        "serializer_schema": schema,
        "spacetime": {
            "dimension": spacetime.get("dimension"),
            "signature_class": spacetime.get("signature_class"),
            "volume_element": spacetime.get("volume_element"),
        },
        "terms": terms,
    }


def fingerprint_canonical_action(canonical_action: dict[str, Any]) -> str:
    digest = hashlib.sha256(canonical_json_bytes(canonical_action)).hexdigest()
    return digest


def serialize_action(document: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize, hash, and return the freeze envelope."""
    canonical = canonicalize_action(document)
    digest = fingerprint_canonical_action(canonical)
    return {
        "canonical_action": canonical,
        "canonical_bytes": canonical_json_bytes(canonical),
        "fingerprint": digest,
        "freeze_id": document.get("freeze_id", ""),
        "serializer_schema": SERIALIZER_SCHEMA,
        "serializer_status": "VERIFIED",
        "unsupported_equivalences": list(_UNSUPPORTED),
    }
