"""Integrity tests 1-25 for Phase 5B.0 freeze infrastructure.

Scientific symmetry conclusions are not the subject of this file except
as negative checks that they are not emitted without authorization.
"""

from __future__ import annotations

import copy
import json
import os
import signal
import time
from multiprocessing import Event, Process, Queue
from pathlib import Path

import pytest

from physics_lab.physics.action_serializer import (
    SERIALIZER_SCHEMA,
    SerializationUnresolved,
    canonicalize_expr,
    serialize_action,
)
from physics_lab.physics.phase4c_action_freeze import (
    ACTION_FREEZE_MISSING,
    ACTION_FREEZE_VIOLATION,
    ANALYSIS_INVALIDATED_BY_ACTION_CHANGE,
    FREEZE_FILENAME,
    LOCKING_MECHANISM,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    create_phase4c_action_freeze,
    exclusive_freeze_lock,
    freeze_paths,
    freeze_phase4c_action,
    phase4c_action_document,
    require_phase4c_action_freeze,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5b0_symmetry import (
    analyze_frozen_action_symmetry,
    generator_build_count,
)
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.result import ModelResult, Spectrum
from physics_lab.reporting.phase5b0_report import format_phase5b0_report


def _fp(document: dict) -> str:
    return serialize_action(document)["fingerprint"]


def _seed_freeze(tmp_path: Path) -> Path:
    os.environ["PHYSICS_LAB_FREEZE_DIR"] = str(tmp_path)
    create_phase4c_action_freeze(replace=False)
    freeze_path, _ = freeze_paths()
    return freeze_path


def _mp_authorize(freeze_dir: str, queue: Queue) -> None:
    os.environ["PHYSICS_LAB_FREEZE_DIR"] = freeze_dir
    from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis as auth_fn

    item = auth_fn()
    queue.put((item.action_content_hash, item.authorization_id, item.bind_ok()))


def _mp_create(freeze_dir: str, queue: Queue) -> None:
    os.environ["PHYSICS_LAB_FREEZE_DIR"] = freeze_dir
    from physics_lab.physics.phase4c_action_freeze import create_phase4c_action_freeze as create_fn

    artifact = create_fn(replace=False)
    queue.put(artifact["action_content_hash"])


def _mp_hold_lock(freeze_dir: str, started: Event, proceed: Event) -> None:
    os.environ["PHYSICS_LAB_FREEZE_DIR"] = freeze_dir
    from physics_lab.physics.phase4c_action_freeze import exclusive_freeze_lock as lock_fn
    from physics_lab.physics.phase4c_action_freeze import freeze_paths as paths_fn

    _, lock_path = paths_fn()
    with lock_fn(lock_path):
        started.set()
        proceed.wait(timeout=30)


def _mp_hold_then_die(freeze_dir: str, started: Event) -> None:
    os.environ["PHYSICS_LAB_FREEZE_DIR"] = freeze_dir
    from physics_lab.physics.phase4c_action_freeze import exclusive_freeze_lock as lock_fn
    from physics_lab.physics.phase4c_action_freeze import freeze_paths as paths_fn

    _, lock_path = paths_fn()
    with lock_fn(lock_path):
        started.set()
        time.sleep(60)


def _mp_writer_during_hold(freeze_dir: str, started: Event, entering: Event, queue: Queue) -> None:
    os.environ["PHYSICS_LAB_FREEZE_DIR"] = freeze_dir
    started.wait(timeout=30)
    from physics_lab.physics.phase4c_action_freeze import create_phase4c_action_freeze as create_fn

    entering.set()
    t0 = time.monotonic()
    create_fn(replace=True)
    queue.put(time.monotonic() - t0)


def test_1_deterministic_repeated_serialization():
    doc = phase4c_action_document()
    a = serialize_action(doc)
    b = serialize_action(doc)
    assert a["canonical_bytes"] == b["canonical_bytes"]
    assert a["fingerprint"] == b["fingerprint"]


def test_2_independent_process_serialization(tmp_path: Path):
    first = freeze_phase4c_action()["fingerprint"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src") + os.pathsep + env.get("PYTHONPATH", "")
    import subprocess
    import sys

    code = (
        "from physics_lab.physics.phase4c_action_freeze import freeze_phase4c_action; "
        "print(freeze_phase4c_action()['fingerprint'])"
    )
    out = subprocess.check_output([sys.executable, "-c", code], env=env, text=True).strip()
    assert out == first


def test_3_dictionary_reordering():
    doc = phase4c_action_document()
    shuffled = {k: doc[k] for k in reversed(list(doc))}
    shuffled["terms"] = list(reversed(doc["terms"]))
    shuffled["parameters"] = list(reversed(doc["parameters"]))
    assert _fp(doc) == _fp(shuffled)


def test_4_additive_term_reordering():
    left = canonicalize_expr({"op": "add", "args": [{"symbol": "A"}, {"symbol": "B"}]})
    right = canonicalize_expr({"op": "add", "args": [{"symbol": "B"}, {"symbol": "A"}]})
    assert left == right


def test_5_symbolic_parameter_stability():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    for param in other["parameters"]:
        if param["id"] == "lam_a":
            param["runtime_value"] = 99
    assert _fp(doc) == _fp(other)


def test_6_term_addition_changes_hash():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    other["terms"].append(
        {
            "id": "extra",
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


def test_7_term_removal_changes_hash():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    other["terms"] = [t for t in other["terms"] if t["id"] != "matter_kinetic"]
    assert _fp(doc) != _fp(other)


def test_8_sign_change_changes_hash():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    for term in other["terms"]:
        if term["id"] == "gravity_c0":
            term["expression"]["integrand"] = {
                "op": "mul",
                "args": [{"integer": -1}, {"symbol": "c0"}],
            }
    assert _fp(doc) != _fp(other)


def test_9_hint_change_changes_hash():
    doc = phase4c_action_document()
    other = copy.deepcopy(doc)
    for term in other["terms"]:
        if term["id"] == "matter_H_int":
            matrix = term["expression"]["integrand"]["args"][2]["right"]["operator"]
            matrix["entries"][0][1] = {"symbol": "lam_a"}
    assert _fp(doc) != _fp(other)


def test_10_unsupported_expression_fails_closed():
    with pytest.raises(SerializationUnresolved) as exc:
        canonicalize_expr({"op": "not_a_real_op", "args": []})
    assert exc.value.status == "SERIALIZATION_UNRESOLVED"


def test_11_valid_freeze_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    create_phase4c_action_freeze()
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == "VERIFIED"
    assert ver["action_content_hash"] == freeze_phase4c_action()["fingerprint"]
    assert ver["serializer_schema"] == SERIALIZER_SCHEMA


def test_12_missing_freeze_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == ACTION_FREEZE_MISSING
    with pytest.raises(FreezeIntegrityError) as exc:
        require_phase4c_action_freeze()
    assert exc.value.status == ACTION_FREEZE_MISSING
    assert exc.value.payload["scientific_analysis"] is None
    assert not (tmp_path / FREEZE_FILENAME).exists()


def test_13_corrupted_hash_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    path = _seed_freeze(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["action_content_hash"] = "0" * 64
    path.write_text(json.dumps(data), encoding="utf-8")
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == ACTION_FREEZE_VIOLATION


def test_14_no_auto_refreeze(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    verify_phase4c_action_freeze()
    with pytest.raises(FreezeIntegrityError):
        authorize_phase5b0_analysis()
    assert not (tmp_path / FREEZE_FILENAME).exists()


def test_15_modified_action_violation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    create_phase4c_action_freeze()

    def mutated():
        doc = phase4c_action_document()
        doc["terms"] = [t for t in doc["terms"] if t["id"] != "matter_phi_sq"]
        return doc

    monkeypatch.setattr(
        "physics_lab.physics.phase4c_action_freeze.phase4c_action_document",
        mutated,
    )
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == ACTION_FREEZE_VIOLATION


def test_16_symmetry_not_called_when_gate_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    before = generator_build_count()
    from physics_lab.physics.phase5b0_gate import run_phase5b0_or_stop

    out = run_phase5b0_or_stop()
    assert out["status"] == "STOP"
    assert out["scientific_analysis"] is None
    assert generator_build_count() == before


def test_17_unauthorized_object_rejected():
    with pytest.raises(UnauthorizedAnalysisError):
        analyze_frozen_action_symmetry(object())
    fake = Phase5B0Authorization(
        authorization_id="x",
        freeze_id="NO",
        serializer_schema=SERIALIZER_SCHEMA,
        action_content_hash="0" * 64,
        immutable_action_snapshot=phase4c_action_document(),
        status="NOT_AUTHORIZED",
    )
    with pytest.raises(UnauthorizedAnalysisError):
        analyze_frozen_action_symmetry(fake)


def test_18_report_without_authorization_has_no_science():
    result = ModelResult(
        name="gate-fail",
        spectrum=Spectrum(states=[], method="none", operator="none"),
        parameters=ParameterRegistry([]),
        metadata={
            "phase5b0_integrity": {
                "PRE_ANALYSIS_GATE": "FAIL",
                "ATOMIC_GATE": "FAIL",
                "LOCKING_MECHANISM": LOCKING_MECHANISM,
            },
            "action_freeze": {"freeze_status": ACTION_FREEZE_MISSING},
        },
    )
    text = format_phase5b0_report(result)
    assert "SCIENTIFIC SYMMETRY CONCLUSIONS: NOT EMITTED" in text
    assert "full-action symmetry" not in text
    assert "EXACT GLOBAL" not in text


def test_19_concurrent_authorizations_serialized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    create_phase4c_action_freeze()
    q: Queue = Queue()
    procs = [
        Process(target=_mp_authorize, args=(str(tmp_path), q)),
        Process(target=_mp_authorize, args=(str(tmp_path), q)),
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=30)
        assert p.exitcode == 0
    hashes = []
    while not q.empty():
        digest, _aid, ok = q.get()
        hashes.append(digest)
        assert ok is True
    assert len(hashes) == 2
    assert hashes[0] == hashes[1] == freeze_phase4c_action()["fingerprint"]


def test_20_writer_blocked_during_held_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    create_phase4c_action_freeze()
    started = Event()
    proceed = Event()
    entering = Event()
    q: Queue = Queue()
    holder = Process(target=_mp_hold_lock, args=(str(tmp_path), started, proceed))
    writer = Process(target=_mp_writer_during_hold, args=(str(tmp_path), started, entering, q))
    holder.start()
    assert started.wait(timeout=10)
    writer.start()
    assert entering.wait(timeout=20)
    time.sleep(0.4)
    assert writer.is_alive()
    proceed.set()
    writer.join(timeout=30)
    holder.join(timeout=30)
    assert writer.exitcode == 0
    elapsed = q.get()
    assert elapsed >= 0.3
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == "VERIFIED"


def test_21_interrupted_writer_leaves_baseline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    create_phase4c_action_freeze()
    freeze_path, _ = freeze_paths()
    original = freeze_path.read_bytes()
    tmp = freeze_path.with_name(freeze_path.name + ".tmp")
    tmp.write_text("{this is not a complete freeze", encoding="utf-8")
    assert freeze_path.read_bytes() == original
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == "VERIFIED"


def test_22_killed_lock_owner_does_not_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    create_phase4c_action_freeze()
    started = Event()
    proc = Process(target=_mp_hold_then_die, args=(str(tmp_path), started))
    proc.start()
    assert started.wait(timeout=10)
    os.kill(proc.pid, signal.SIGKILL)
    proc.join(timeout=10)
    auth = authorize_phase5b0_analysis()
    assert auth.bind_ok()


def test_23_authorized_snapshot_bound_to_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    create_phase4c_action_freeze()
    auth = authorize_phase5b0_analysis()
    assert auth.snapshot_hash() == auth.action_content_hash
    assert auth.bind_ok()


def test_24_action_change_after_authorization_invalidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    create_phase4c_action_freeze()
    auth = authorize_phase5b0_analysis()
    auth.immutable_action_snapshot["terms"] = []
    out = analyze_frozen_action_symmetry(auth)
    assert out["status"] == ANALYSIS_INVALIDATED_BY_ACTION_CHANGE
    assert out.get("scientific_conclusions") is None


def test_25_simultaneous_create_not_partial(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHYSICS_LAB_FREEZE_DIR", str(tmp_path))
    q: Queue = Queue()
    procs = [
        Process(target=_mp_create, args=(str(tmp_path), q)),
        Process(target=_mp_create, args=(str(tmp_path), q)),
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=30)
        assert p.exitcode == 0
    freeze_path, _ = freeze_paths()
    data = json.loads(freeze_path.read_text(encoding="utf-8"))
    assert set(data) >= {
        "freeze_id",
        "serializer_schema",
        "canonical_action",
        "action_content_hash",
        "provenance_summary",
    }
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == "VERIFIED"
    hashes = [q.get(), q.get()]
    assert hashes[0] == hashes[1] == ver["action_content_hash"]
