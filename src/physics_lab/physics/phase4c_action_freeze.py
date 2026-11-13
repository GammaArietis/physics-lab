"""PHASE_4C_ACTION_FREEZE: frozen identity of the existing Phase 4C action.

Does not add, remove, or rewrite terms.  Does not include analysis results,
gauge fields, or experimental constants.  Gravity remains the 4A/4B family.
"""

from __future__ import annotations

import copy
import json
import os
import secrets
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from physics_lab.physics.action_serializer import (
    SERIALIZER_SCHEMA,
    SerializationUnresolved,
    canonical_json_bytes,
    fingerprint_canonical_action,
    serialize_action,
)
from physics_lab.physics.internal_spectrum import internal_dimension

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

__all__ = [
    "ACTION_FREEZE_MISSING",
    "ACTION_FREEZE_UNRESOLVED",
    "ACTION_FREEZE_VIOLATION",
    "ANALYSIS_AUTHORIZED",
    "ANALYSIS_INVALIDATED_BY_ACTION_CHANGE",
    "FREEZE_ID",
    "FREEZE_FILENAME",
    "LOCKING_MECHANISM",
    "LOCKING_MECHANISM_UNSUPPORTED",
    "LOCK_FILENAME",
    "FreezeIntegrityError",
    "Phase5B0Authorization",
    "UnauthorizedAnalysisError",
    "authorize_phase5b0_analysis",
    "create_phase4c_action_freeze",
    "exclusive_freeze_lock",
    "freeze_is_verified",
    "freeze_paths",
    "freeze_phase4c_action",
    "freeze_report_payload",
    "phase4c_action_document",
    "require_phase4c_action_freeze",
    "verify_phase4c_action_freeze",
]


FREEZE_ID = "PHASE_4C_ACTION_FREEZE"
FREEZE_FILENAME = "phase4c_action_freeze.json"
LOCK_FILENAME = ".phase4c_action_freeze.lock"
FREEZE_DIR_ENV = "PHYSICS_LAB_FREEZE_DIR"
LOCKING_MECHANISM = "POSIX fcntl.flock LOCK_EX"
ACTION_FREEZE_MISSING = "ACTION_FREEZE_MISSING"
ACTION_FREEZE_VIOLATION = "ACTION_FREEZE_VIOLATION"
ACTION_FREEZE_UNRESOLVED = "ACTION_FREEZE_UNRESOLVED"
LOCKING_MECHANISM_UNSUPPORTED = "LOCKING_MECHANISM_UNSUPPORTED"
ANALYSIS_AUTHORIZED = "ANALYSIS_AUTHORIZED"
ANALYSIS_INVALIDATED_BY_ACTION_CHANGE = "ANALYSIS_INVALIDATED_BY_ACTION_CHANGE"


def _sym(name: str) -> dict[str, Any]:
    return {"symbol": name}


def _int(n: int) -> dict[str, Any]:
    return {"integer": n}


def _field(name: str) -> dict[str, Any]:
    return {"field": name}


def _mul(*args: Any) -> dict[str, Any]:
    return {"op": "mul", "args": list(args)}


def _half() -> dict[str, Any]:
    return {"rational": [1, 2]}


def _inner(left: Any, right: Any) -> dict[str, Any]:
    return {"op": "inner_product", "left": left, "right": right}


def _integral(integrand: Any) -> dict[str, Any]:
    return {
        "op": "integral",
        "coords": "d4x",
        "density": "sqrt_minus_g",
        "integrand": integrand,
    }


def _h_int_matrix() -> dict[str, Any]:
    """Existing 4C probe: diag(lam_a, lam_b, lam_b). Explicit operator, not spectrum."""
    z = _int(0)
    a = _sym("lam_a")
    b = _sym("lam_b")
    return {
        "op": "matrix",
        "rows": 3,
        "cols": 3,
        "entries": [[a, z, z], [z, b, z], [z, z, b]],
    }


def phase4c_action_document() -> dict[str, Any]:
    """Existing Phase 4C action content.  No analysis quantities."""
    dim = internal_dimension()
    kinetic = {
        "op": "metric_contraction",
        "metric": _sym("g_inv"),
        "indices": ["mu", "nu"],
        "operand": _inner(
            {"op": "derivative", "field": "Phi", "index": "mu"},
            {"op": "derivative", "field": "Phi", "index": "nu"},
        ),
    }
    return {
        "serializer_schema": SERIALIZER_SCHEMA,
        "phase": "4C",
        "action_type": "phase_4c_internal_hilbert_plus_gravity",
        "spacetime": {
            "dimension": 4,
            "signature_class": "lorentzian",
            "volume_element": "sqrt(-g)",
        },
        "fields": [
            {"id": "Phi", "type": "real_vector", "internal_dimension": dim},
            {"id": "metric", "type": "metric", "spacetime_dimension": 4},
        ],
        "internal_space": {
            "type": "R",
            "dimension": dim,
            "status": "INPUT",
        },
        "parameters": [
            {
                "id": "c0",
                "role": "gravity volume term",
                "provenance": "INPUT",
                "symbolic": True,
                "value_is_structural": False,
            },
            {
                "id": "c1",
                "role": "Einstein-Hilbert coefficient",
                "provenance": "INPUT",
                "symbolic": True,
                "value_is_structural": False,
            },
            {
                "id": "Z",
                "role": "matter kinetic coefficient",
                "provenance": "INPUT",
                "symbolic": True,
                "value_is_structural": False,
            },
            {
                "id": "kappa",
                "role": "Phi squared coefficient (branch I)",
                "provenance": "INPUT",
                "symbolic": True,
                "value_is_structural": False,
            },
            {
                "id": "c_H",
                "role": "H_int coupling (branch II)",
                "provenance": "INPUT",
                "symbolic": True,
                "value_is_structural": False,
            },
            {
                "id": "lam_a",
                "role": "H_int matrix entry",
                "provenance": "INPUT",
                "symbolic": True,
                "value_is_structural": False,
            },
            {
                "id": "lam_b",
                "role": "H_int matrix entry",
                "provenance": "INPUT",
                "symbolic": True,
                "value_is_structural": False,
            },
            {
                "id": "internal_dimension",
                "role": "dimension of H_R",
                "provenance": "INPUT",
                "symbolic": False,
                "value_is_structural": True,
                "value": dim,
            },
        ],
        "terms": [
            {
                "id": "gravity_c0",
                "expression": _integral(_sym("c0")),
                "coefficients": ["c0"],
                "provenance": ["ASSUMED"],
            },
            {
                "id": "gravity_c1_R",
                "expression": _integral(_mul(_sym("c1"), _sym("R"))),
                "coefficients": ["c1"],
                "provenance": ["ASSUMED"],
            },
            {
                "id": "matter_kinetic",
                "expression": _integral(_mul(_sym("Z"), kinetic)),
                "coefficients": ["Z"],
                "provenance": ["ASSUMED"],
            },
            {
                "id": "matter_phi_sq",
                "expression": _integral(
                    _mul(_sym("kappa"), _half(), _inner(_field("Phi"), _field("Phi")))
                ),
                "coefficients": ["kappa"],
                "provenance": ["ASSUMED"],
            },
            {
                "id": "matter_H_int",
                "expression": _integral(
                    _mul(
                        _sym("c_H"),
                        _half(),
                        _inner(
                            _field("Phi"),
                            {
                                "op": "operator_application",
                                "operator": _h_int_matrix(),
                                "operand": _field("Phi"),
                            },
                        ),
                    )
                ),
                "coefficients": ["c_H", "lam_a", "lam_b"],
                "provenance": ["ASSUMED"],
            },
        ],
        "assumptions": [
            {
                "id": "real_internal_space",
                "value": True,
                "provenance": "INPUT",
            },
            {
                "id": "internal_dimension",
                "value": dim,
                "provenance": "INPUT",
            },
            {
                "id": "spacetime_signature_class",
                "value": "lorentzian",
                "provenance": "CONVENTION",
            },
            {
                "id": "truncation_order",
                "value": "quadratic_hilbert_matter",
                "provenance": "ASSUMED",
            },
            {
                "id": "H_int_in_S_matter",
                "value": True,
                "provenance": "ASSUMED",
            },
            {
                "id": "internal_space_not_extra_dimension",
                "value": True,
                "provenance": "INPUT",
            },
        ],
        "approximations": [
            {
                "id": "quadratic_matter",
                "statement": "Matter density is quadratic in Phi and nabla Phi",
                "provenance": "ASSUMED",
            }
        ],
    }


def freeze_phase4c_action() -> dict[str, Any]:
    """Verified freeze envelope. Analysis results are not included."""
    document = phase4c_action_document()
    envelope = serialize_action(document)
    canonical = envelope["canonical_action"]
    digest = fingerprint_canonical_action(canonical)
    return {
        "serializer_schema": SERIALIZER_SCHEMA,
        "freeze_id": FREEZE_ID,
        "fingerprint": digest,
        "action_content_hash": digest,
        "canonical_action": canonical,
        "serializer_status": "VERIFIED",
        "freeze_status": "VERIFIED",
        "unsupported_equivalences": envelope["unsupported_equivalences"],
        "freeze_provenance": "METHOD / INTEGRITY CONTROL",
        "basis_convention": {
            "status": "CONVENTION",
            "hashed": False,
            "note": "A standard ONB is analysis, not action content. Basis equivalence is unsupported.",
        },
        "contract": "ACTION_SERIALIZER_CONTRACT",
    }


def freeze_is_verified(envelope: dict[str, Any] | None) -> bool:
    if not envelope:
        return False
    digest = envelope.get("fingerprint") or envelope.get("action_content_hash")
    return (
        envelope.get("serializer_status") == "VERIFIED"
        and envelope.get("freeze_status") == "VERIFIED"
        and envelope.get("serializer_schema") == SERIALIZER_SCHEMA
        and envelope.get("freeze_id") == FREEZE_ID
        and isinstance(digest, str)
        and len(digest) == 64
    )


class FreezeIntegrityError(Exception):
    """Technical freeze/gate failure.  Contains no scientific symmetry result."""

    def __init__(self, status: str, detail: str, payload: dict[str, Any] | None = None) -> None:
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.detail = detail
        self.payload = payload or integrity_only_payload(status, detail)


class UnauthorizedAnalysisError(Exception):
    """Symmetry analysis refused an object that is not a valid authorization."""

    def __init__(self, detail: str = "analysis object is not tied to a valid authorization") -> None:
        super().__init__(detail)
        self.status = "UNAUTHORIZED"


@dataclass
class Phase5B0Authorization:
    authorization_id: str
    freeze_id: str
    serializer_schema: str
    action_content_hash: str
    immutable_action_snapshot: dict[str, Any]
    status: str = ANALYSIS_AUTHORIZED

    def snapshot_hash(self) -> str:
        return fingerprint_canonical_action(self.immutable_action_snapshot)

    def bind_ok(self) -> bool:
        return (
            self.status == ANALYSIS_AUTHORIZED
            and self.freeze_id == FREEZE_ID
            and self.serializer_schema == SERIALIZER_SCHEMA
            and self.snapshot_hash() == self.action_content_hash
        )


def freeze_paths(root: Path | str | None = None) -> tuple[Path, Path]:
    if root is None:
        env = os.environ.get(FREEZE_DIR_ENV)
        root = Path(env) if env else Path(__file__).resolve().parent
    base = Path(root)
    return base / FREEZE_FILENAME, base / LOCK_FILENAME


def _fsync_file(path: Path) -> None:
    with open(path, "rb") as handle:
        os.fsync(handle.fileno())


def _fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def exclusive_freeze_lock(lock_path: Path | str | None = None) -> Iterator[None]:
    """POSIX fcntl.flock LOCK_EX.  No homemade fallback."""
    if fcntl is None:
        raise FreezeIntegrityError(
            LOCKING_MECHANISM_UNSUPPORTED,
            "fcntl.flock is unavailable on this platform",
        )
    if lock_path is None:
        _, lock_path = freeze_paths()
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except OSError as exc:
            raise FreezeIntegrityError(
                LOCKING_MECHANISM_UNSUPPORTED,
                f"fcntl.flock failed: {exc}",
            ) from exc
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()


def _provenance_summary() -> dict[str, Any]:
    return {
        "freeze_provenance": "METHOD / INTEGRITY CONTROL",
        "gravity": "ASSUMED / Phase 4A family, c0 c1 INPUT / FREE",
        "internal_space": "R^3 INPUT, not an extra dimension",
        "H_int": "INPUT matrix diag(lam_a, lam_b, lam_b)",
        "matter": "Z kinetic + kappa |Phi|^2 + ASSUMED c_H <Phi, H_int Phi>",
        "not_included": [
            "analysis results",
            "candidate symmetries",
            "Noether currents",
            "U(1) conclusions",
        ],
    }


def _artifact_from_current() -> dict[str, Any]:
    envelope = freeze_phase4c_action()
    artifact = {
        "freeze_id": FREEZE_ID,
        "serializer_schema": SERIALIZER_SCHEMA,
        "canonical_action": envelope["canonical_action"],
        "action_content_hash": envelope["fingerprint"],
        "provenance_summary": _provenance_summary(),
    }
    recomputed = fingerprint_canonical_action(artifact["canonical_action"])
    if recomputed != artifact["action_content_hash"]:
        raise FreezeIntegrityError(
            ACTION_FREEZE_UNRESOLVED,
            "internal hash of reconstructed action does not match",
        )
    return artifact


def _write_artifact_atomic(freeze_path: Path, artifact: dict[str, Any]) -> None:
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = freeze_path.with_name(freeze_path.name + ".tmp")
    payload = canonical_json_bytes(artifact)
    tmp.write_bytes(payload)
    _fsync_file(tmp)
    os.replace(tmp, freeze_path)
    _fsync_dir(freeze_path.parent)


def load_stored_freeze(freeze_path: Path | None = None) -> dict[str, Any]:
    if freeze_path is None:
        freeze_path, _ = freeze_paths()
    freeze_path = Path(freeze_path)
    if not freeze_path.is_file():
        raise FreezeIntegrityError(ACTION_FREEZE_MISSING, f"missing baseline {freeze_path}")
    try:
        data = json.loads(freeze_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreezeIntegrityError(
            ACTION_FREEZE_UNRESOLVED,
            f"unable to read freeze: {exc}",
        ) from exc
    if not isinstance(data, dict):
        raise FreezeIntegrityError(ACTION_FREEZE_UNRESOLVED, "freeze artifact is not an object")
    return data


def create_phase4c_action_freeze(
    *,
    replace: bool = False,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Explicit freeze publication.  Never called by analysis."""
    freeze_path, lock_path = freeze_paths(root)
    with exclusive_freeze_lock(lock_path):
        if freeze_path.is_file() and not replace:
            return load_stored_freeze(freeze_path)
        artifact = _artifact_from_current()
        _write_artifact_atomic(freeze_path, artifact)
        return artifact


def _verify_unlocked(freeze_path: Path) -> dict[str, Any]:
    if not freeze_path.is_file():
        return {
            "status": ACTION_FREEZE_MISSING,
            "detail": f"missing baseline {freeze_path}",
            "freeze_id": FREEZE_ID,
            "serializer_schema": SERIALIZER_SCHEMA,
            "action_content_hash": None,
            "current_hash": None,
            "canonical_action": None,
        }
    try:
        stored = load_stored_freeze(freeze_path)
    except FreezeIntegrityError as exc:
        return {
            "status": exc.status,
            "detail": exc.detail,
            "freeze_id": FREEZE_ID,
            "serializer_schema": SERIALIZER_SCHEMA,
            "action_content_hash": None,
            "current_hash": None,
            "canonical_action": None,
        }
    stored_hash = stored.get("action_content_hash")
    stored_action = stored.get("canonical_action")
    try:
        if not isinstance(stored_action, dict) or not isinstance(stored_hash, str):
            raise FreezeIntegrityError(ACTION_FREEZE_UNRESOLVED, "freeze fields missing")
        recomputed_stored = fingerprint_canonical_action(stored_action)
        current = freeze_phase4c_action()
        current_hash = current["fingerprint"]
    except (FreezeIntegrityError, SerializationUnresolved, TypeError, ValueError) as exc:
        return {
            "status": ACTION_FREEZE_UNRESOLVED,
            "detail": str(exc),
            "freeze_id": stored.get("freeze_id", FREEZE_ID),
            "serializer_schema": stored.get("serializer_schema", SERIALIZER_SCHEMA),
            "action_content_hash": stored_hash,
            "current_hash": None,
            "canonical_action": None,
        }
    if recomputed_stored != stored_hash:
        return {
            "status": ACTION_FREEZE_VIOLATION,
            "detail": "stored hash does not match stored canonical_action",
            "freeze_id": stored.get("freeze_id", FREEZE_ID),
            "serializer_schema": stored.get("serializer_schema", SERIALIZER_SCHEMA),
            "action_content_hash": stored_hash,
            "current_hash": current_hash,
            "canonical_action": stored_action,
        }
    if current_hash != stored_hash:
        return {
            "status": ACTION_FREEZE_VIOLATION,
            "detail": "current Phase 4C action hash differs from stored freeze",
            "freeze_id": stored.get("freeze_id", FREEZE_ID),
            "serializer_schema": stored.get("serializer_schema", SERIALIZER_SCHEMA),
            "action_content_hash": stored_hash,
            "current_hash": current_hash,
            "canonical_action": stored_action,
        }
    if stored.get("freeze_id") != FREEZE_ID or stored.get("serializer_schema") != SERIALIZER_SCHEMA:
        return {
            "status": ACTION_FREEZE_VIOLATION,
            "detail": "freeze_id or serializer_schema mismatch",
            "freeze_id": stored.get("freeze_id"),
            "serializer_schema": stored.get("serializer_schema"),
            "action_content_hash": stored_hash,
            "current_hash": current_hash,
            "canonical_action": stored_action,
        }
    return {
        "status": "VERIFIED",
        "detail": "stored freeze matches current Phase 4C action",
        "freeze_id": FREEZE_ID,
        "serializer_schema": SERIALIZER_SCHEMA,
        "action_content_hash": stored_hash,
        "current_hash": current_hash,
        "canonical_action": copy.deepcopy(stored_action),
        "provenance_summary": stored.get("provenance_summary"),
        "unsupported_equivalences": current.get("unsupported_equivalences"),
    }


def verify_phase4c_action_freeze(*, root: Path | str | None = None) -> dict[str, Any]:
    freeze_path, lock_path = freeze_paths(root)
    with exclusive_freeze_lock(lock_path):
        return _verify_unlocked(freeze_path)


def integrity_only_payload(status: str, detail: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "status": status,
        "detail": detail,
        "PRE_ANALYSIS_GATE": "FAIL",
        "scientific_analysis": None,
        "scientific_conclusions": None,
        "LOCKING_MECHANISM": LOCKING_MECHANISM,
        "freeze_id": FREEZE_ID,
        "serializer_schema": SERIALIZER_SCHEMA,
    }
    if extra:
        payload.update(extra)
    return payload


def require_phase4c_action_freeze(*, root: Path | str | None = None) -> dict[str, Any]:
    """HARD gate.  No symmetry analysis is performed here."""
    verification = verify_phase4c_action_freeze(root=root)
    if verification.get("status") != "VERIFIED":
        raise FreezeIntegrityError(
            str(verification.get("status")),
            str(verification.get("detail")),
            integrity_only_payload(
                str(verification.get("status")),
                str(verification.get("detail")),
                {
                    "action_content_hash": verification.get("action_content_hash"),
                    "current_hash": verification.get("current_hash"),
                },
            ),
        )
    return verification


def authorize_phase5b0_analysis(*, root: Path | str | None = None) -> Phase5B0Authorization:
    """Verify and bind an immutable snapshot under a single LOCK_EX."""
    freeze_path, lock_path = freeze_paths(root)
    with exclusive_freeze_lock(lock_path):
        verification = _verify_unlocked(freeze_path)
        if verification.get("status") != "VERIFIED":
            raise FreezeIntegrityError(
                str(verification.get("status")),
                str(verification.get("detail")),
                integrity_only_payload(
                    str(verification.get("status")),
                    str(verification.get("detail")),
                    {
                        "action_content_hash": verification.get("action_content_hash"),
                        "current_hash": verification.get("current_hash"),
                    },
                ),
            )
        snapshot = copy.deepcopy(verification["canonical_action"])
        digest = str(verification["action_content_hash"])
        return Phase5B0Authorization(
            authorization_id=secrets.token_hex(16),
            freeze_id=FREEZE_ID,
            serializer_schema=SERIALIZER_SCHEMA,
            action_content_hash=digest,
            immutable_action_snapshot=snapshot,
            status=ANALYSIS_AUTHORIZED,
        )


def freeze_report_payload(verification: dict[str, Any]) -> dict[str, Any]:
    ok = verification.get("status") == "VERIFIED"
    digest = verification.get("action_content_hash")
    return {
        "serializer_schema": verification.get("serializer_schema", SERIALIZER_SCHEMA),
        "freeze_id": verification.get("freeze_id", FREEZE_ID),
        "fingerprint": digest,
        "action_content_hash": digest,
        "canonical_action": verification.get("canonical_action"),
        "serializer_status": "VERIFIED" if ok else "FAIL",
        "freeze_status": "VERIFIED" if ok else verification.get("status"),
        "unsupported_equivalences": verification.get("unsupported_equivalences"),
        "freeze_provenance": "METHOD / INTEGRITY CONTROL",
        "contract": "ACTION_SERIALIZER_CONTRACT",
        "LOCKING_MECHANISM": LOCKING_MECHANISM,
        "verification_detail": verification.get("detail"),
        "provenance_summary": verification.get("provenance_summary"),
    }
