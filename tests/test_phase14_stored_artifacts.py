"""Fast integrity checks for the committed Phase 14L–14N records."""

from physics_lab.theory_kernel.phase14l_symmetry import verify_stored_phase_14l
from physics_lab.theory_kernel.phase14m_consequences import verify_stored_phase_14m
from physics_lab.theory_kernel.phase14n_constraints import verify_stored_phase_14n


def _assert_stored(result: dict[str, object], phase: str) -> None:
    assert result["status"] == "OK"
    assert result[f"{phase}_STATUS"] == "COMPLETE"
    assert result["verification_mode"] == "STORED_ARTIFACT"
    assert result["independent_replay"] == "NOT_PERFORMED"


def test_phase14l_stored_record_is_verifiable() -> None:
    _assert_stored(verify_stored_phase_14l(), "PHASE_14L")


def test_phase14m_stored_record_is_verifiable() -> None:
    _assert_stored(verify_stored_phase_14m(), "PHASE_14M")


def test_phase14n_stored_record_is_verifiable() -> None:
    _assert_stored(verify_stored_phase_14n(), "PHASE_14N")
