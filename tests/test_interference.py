"""Interference module (independent of the first prototypes)."""

from __future__ import annotations

import numpy as np

from physics_lab.physics.interference import classify_overlap, interfere, overlap


def test_maximum_interference_identical_internal_states():
    chi = np.array([1.0, 0.0, 0.0], dtype=complex)
    result = interfere(chi, chi)
    assert result.classification == "interference maximum"
    assert abs(result.gamma - 1) < 1e-12


def test_no_interference_orthogonal_states():
    chi1 = np.array([1.0, 0.0], dtype=complex)
    chi2 = np.array([0.0, 1.0], dtype=complex)
    assert classify_overlap(overlap(chi1, chi2)) == "no interference"


def test_partial_interference():
    chi1 = np.array([1.0, 0.0], dtype=complex)
    chi2 = np.array([1.0, 1.0], dtype=complex)
    mag = abs(overlap(chi1, chi2))
    assert 0 < mag < 1
    assert classify_overlap(overlap(chi1, chi2)) == "partial interference"
