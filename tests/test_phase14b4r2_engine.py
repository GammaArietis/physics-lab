"""Engine isolation for G4R orbit-closure v2."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14b4r2_g4 import G4R2_CHAIN, G4R2_ID, g4r2_executable_registry


def test_g4r2_registry_does_not_expand_r_max():
    g = g4r2_executable_registry()[G4R2_ID]
    assert g["r_max"] == 1
    assert g["STRATUM_LIST_EXHAUSTIVE"] is False
    assert g["VEV_ORBIT_CLASSIFICATION"] == "PARTIAL"
    assert G4R2_CHAIN == (G4R2_ID,)


def test_g4r2_chain_exists_but_physics_remains_blocked(tmp_path: Path):
    engine = ClosureEngine(tmp_path / "g4r2_probe", chain="g4r2_only")
    assert engine.chain == [G4R2_ID]
    try:
        ClosureEngine(tmp_path / "physics", chain="physics")
        raise AssertionError("expected ILLEGAL_AUTOMATIC_EXTENSION")
    except EngineFailure as exc:
        assert exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
