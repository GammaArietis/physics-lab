"""Regression controls for historical hashes and portable artifact paths."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from physics_lab.physics.portability import portable_path


ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "docs" / "validation" / "HISTORICAL_INTEGRITY_PORTABILITY_2026-11-13.json"
ABSOLUTE_PATH = re.compile(r"/(?:Users|tmp|home)/")


def _record() -> dict[str, object]:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_versioned_record_resolves_historical_hashes() -> None:
    record = _record()
    hashes = record["hash_resolution"]
    assert isinstance(hashes, dict)
    for key in ("v22_docx", "v23_docx", "v23_pdf"):
        item = hashes[key]
        assert isinstance(item, dict)
        path = ROOT / item["repository_path"]
        assert _sha256(path) == item["observed_sha256"]
    assert hashes["v23_pdf"]["observed_sha256"] != hashes["v23_pdf"]["legacy_record_sha256"]
    assert hashes["v22_cross_check_copied_into_v23"]["correct_sha256"] == hashes["v22_docx"]["observed_sha256"]


def test_all_legacy_absolute_path_files_are_declared() -> None:
    record = _record()
    portability = record["portability"]
    declared = set(portability["historical_absolute_path_files"])
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src" / "physics_lab" / "physics").rglob("*.json")
        if ABSOLUTE_PATH.search(path.read_text(encoding="utf-8"))
    }
    v22_validation = ROOT / "docs" / "history" / "20Ottobre2026" / "REPORT_V22_VALIDATION.json"
    if ABSOLUTE_PATH.search(v22_validation.read_text(encoding="utf-8")):
        actual.add(v22_validation.relative_to(ROOT).as_posix())
    assert len(actual) == portability["historical_absolute_path_json_count"]
    assert actual == declared


def test_new_path_serializer_is_repository_relative() -> None:
    example = ROOT / "src" / "physics_lab" / "physics" / "phase14c0_artifacts" / "PHASE_14C0_SUMMARY.json"
    assert portable_path(example) == "src/physics_lab/physics/phase14c0_artifacts/PHASE_14C0_SUMMARY.json"
    temporary = Path("/tmp") / "not-a-repository-artifact.json"
    assert portable_path(temporary, anchor=Path("/tmp")) == "not-a-repository-artifact.json"
    with pytest.raises(ValueError, match="outside repository"):
        portable_path(temporary)
