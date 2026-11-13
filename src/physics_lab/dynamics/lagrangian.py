"""Lagrangian container.  Optional in the MVP; kept for extensibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from physics_lab.dynamics.hamiltonian import Hamiltonian


@dataclass
class Lagrangian:
    kinetic_formula: str
    potential_formula: str = "0"
    description: str = ""
    metadata: dict[str, Any] | None = None

    def formula(self) -> str:
        return f"L = {self.kinetic_formula} - ({self.potential_formula})"

    def to_hamiltonian(self, name: str = "H") -> Hamiltonian:
        """Formal Legendre map for standard quadratic kinetics."""
        return Hamiltonian(
            name=name,
            kind="from_lagrangian",
            formula=f"H = {self.kinetic_formula} + ({self.potential_formula})",
            description="Obtained from L by the standard quadratic-kinetic map. "
            "This map is a MODEL ASSUMPTION unless derived separately.",
        )
