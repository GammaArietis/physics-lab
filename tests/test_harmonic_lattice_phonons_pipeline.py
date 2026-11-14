"""End-to-end tests for finite harmonic-lattice phonon modes."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import HarmonicLatticePhononPipelineError, TheoryCandidateValidationError, load_theory_candidate, run_harmonic_lattice_phonon_pipeline, write_harmonic_lattice_phonon_report


CANDIDATE_PATH = "schemas/examples/theory_candidate_harmonic_lattice_phonons.json"


def test_phonon_candidate_declares_finite_periodic_chain() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "harmonic-lattice-phonons-v1"
    assert candidate["geometry"]["spacetime"]["manifold"] == "R_t x Z_N"


def test_phonon_runs_normal_mode_spectrum() -> None:
    report = run_harmonic_lattice_phonon_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["checks"]["translation_zero_mode_verified"] is True
    assert report["checks"]["normal_mode_dispersion_verified"] is True
    assert next(item for item in report["observables"] if item["name"] == "zero_mode_frequency")["value"] == pytest.approx(0.0)
    assert all(report["controls"].values())


def test_phonon_rejects_infinite_chain_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["manifold"] = "R_t x R"
    with pytest.raises(HarmonicLatticePhononPipelineError, match="finite"):
        run_harmonic_lattice_phonon_pipeline(candidate=candidate)


def test_phonon_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_harmonic_lattice_phonon_pipeline(candidate=candidate)


def test_phonon_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_harmonic_lattice_phonon_report(tmp_path / "first.json")
    second = write_harmonic_lattice_phonon_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
