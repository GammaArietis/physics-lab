"""Simple two-path interference with an internal state.

This module is independent of the first prototype models.  It is
available for later integration:

    Psi = psi1(x) * chi1(xi) + psi2(x) * chi2(xi)
    gamma = <chi1|chi2>
    P ~ |psi1 + gamma * psi2|^2   (schematic)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class InterferenceResult:
    gamma: complex
    classification: str
    probability_density: np.ndarray | None
    note: str


def overlap(chi1: np.ndarray, chi2: np.ndarray, weights: np.ndarray | None = None) -> complex:
    """gamma = <chi1|chi2>."""
    a = np.asarray(chi1, dtype=complex)
    b = np.asarray(chi2, dtype=complex)
    if weights is None:
        value = np.vdot(a, b)
        n1 = np.vdot(a, a)
        n2 = np.vdot(b, b)
    else:
        w = np.asarray(weights, dtype=float)
        value = np.vdot(a * w, b)
        n1 = np.vdot(a * w, a)
        n2 = np.vdot(b * w, b)
    denom = np.sqrt(n1 * n2)
    if abs(denom) < 1e-15:
        return 0j
    return complex(value / denom)


def classify_overlap(gamma: complex, atol: float = 1e-8) -> str:
    mag = abs(gamma)
    if abs(mag - 1.0) <= atol:
        return "interference maximum"
    if mag <= atol:
        return "no interference"
    return "partial interference"


def two_path_probability(
    psi1: np.ndarray | Callable[[np.ndarray], np.ndarray],
    psi2: np.ndarray | Callable[[np.ndarray], np.ndarray],
    gamma: complex,
    x: np.ndarray | None = None,
) -> np.ndarray:
    """P = |psi1 + gamma * psi2|^2."""
    if callable(psi1):
        if x is None:
            raise ValueError("x is required when psi1/psi2 are callables.")
        u = np.asarray(psi1(x), dtype=complex)
        v = np.asarray(psi2(x), dtype=complex)
    else:
        u = np.asarray(psi1, dtype=complex)
        v = np.asarray(psi2, dtype=complex)
    amp = u + gamma * v
    return np.abs(amp) ** 2


def interfere(
    chi1: np.ndarray,
    chi2: np.ndarray,
    psi1: np.ndarray | None = None,
    psi2: np.ndarray | None = None,
) -> InterferenceResult:
    gamma = overlap(chi1, chi2)
    classification = classify_overlap(gamma)
    density = None
    if psi1 is not None and psi2 is not None:
        density = two_path_probability(psi1, psi2, gamma)
    return InterferenceResult(
        gamma=gamma,
        classification=classification,
        probability_density=density,
        note="Internal overlap gamma controls spatial interference. "
        "This module is not yet wired into the circle/C3 prototypes.",
    )
