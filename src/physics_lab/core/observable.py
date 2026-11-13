"""Observable operators attached to a model.

An observable is a *definition* (for example Q = kappa * p_xi).  Evaluating
it on a spectrum produces tracked quantities with provenance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from physics_lab.core.model import Model
    from physics_lab.core.result import Quantity, Spectrum


@dataclass
class Observable(ABC):
    name: str
    description: str = ""

    @abstractmethod
    def evaluate(self, model: "Model", spectrum: "Spectrum") -> list["Quantity"]:
        """Compute the observable on every eigenstate."""


@dataclass
class NamedOperator:
    """Symbolic / numeric stand-in for an operator such as p_xi or Q."""

    name: str
    formula: str
    symbolic: Any = None
    description: str = ""
