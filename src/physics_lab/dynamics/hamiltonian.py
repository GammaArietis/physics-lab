"""Hamiltonian definitions (geometry-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np


@dataclass
class Hamiltonian:
    """An internal Hamiltonian: analytic, dense matrix, or callable."""

    name: str = "H"
    kind: str = "generic"
    matrix: np.ndarray | None = None
    potential: Callable[[np.ndarray], np.ndarray] | None = None
    formula: str = ""
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_hermitian(self, atol: float = 1e-10) -> bool | None:
        if self.matrix is None:
            return None
        h = np.asarray(self.matrix)
        return bool(np.allclose(h, h.conj().T, atol=atol))


def laplacian_circle_formula() -> str:
    return "H = p_xi**2  [ASSUMED]  with  p_xi = -i*hbar*d/dxi"
