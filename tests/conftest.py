"""Test isolation for phase artifacts.

Many historical phase tests intentionally materialize JSON reports and then
assert that parent artifacts were not changed.  Pytest normally keeps those
writes in the checkout, so a later test can accidentally observe the previous
test's generated state.  The fixture below preserves the repository baseline
once per test session and restores only files whose metadata changed after
each test.  This keeps the tests' in-test mutation checks meaningful while
making the cumulative suite independent of collection order.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


PHYSICS_ROOT = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "physics"


def _files(root: Path) -> dict[Path, tuple[int, int]]:
    """Return relative file paths and cheap signatures for a tree."""
    return {
        path.relative_to(root): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    }


def _restore_artifacts(backup: Path, baseline: dict[Path, tuple[int, int]]) -> None:
    current = _files(PHYSICS_ROOT)

    for relative in current.keys() - baseline.keys():
        (PHYSICS_ROOT / relative).unlink(missing_ok=True)

    for relative, signature in baseline.items():
        source = backup / relative
        destination = PHYSICS_ROOT / relative
        if not destination.is_file() or current.get(relative) != signature:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    for directory in sorted(PHYSICS_ROOT.rglob("*"), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()


@pytest.fixture(scope="session")
def _phase_artifact_baseline(tmp_path_factory: pytest.TempPathFactory):
    backup = tmp_path_factory.mktemp("phase-artifact-baseline") / "physics"
    shutil.copytree(PHYSICS_ROOT, backup, copy_function=shutil.copy2)
    return backup, _files(PHYSICS_ROOT)


@pytest.fixture(autouse=True)
def restore_phase_artifacts_after_test(_phase_artifact_baseline):
    yield
    backup, baseline = _phase_artifact_baseline
    _restore_artifacts(backup, baseline)
