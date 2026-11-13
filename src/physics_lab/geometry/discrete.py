"""Discrete / periodic 1D geometries used by numerical solvers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from physics_lab.geometry.geometry import Geometry


@dataclass
class DiscretePeriodicGeometry(Geometry):
    length: float = 2.0 * np.pi
    n_points: int = 128
    coordinate: str = "x"

    def __init__(
        self,
        length: float = 2.0 * np.pi,
        n_points: int = 128,
        coordinate: str = "x",
        name: str = "discrete_periodic",
    ) -> None:
        if n_points < 2:
            raise ValueError("n_points must be at least 2.")
        self.length = float(length)
        self.n_points = int(n_points)
        self.coordinate = coordinate
        super().__init__(
            name=name,
            coordinates=(coordinate,),
            periodic=True,
            description=self.domain_description(),
        )

    def period(self) -> float:
        return self.length

    def dx(self) -> float:
        return self.length / self.n_points

    def grid(self) -> np.ndarray:
        return np.linspace(0.0, self.length, self.n_points, endpoint=False)

    def domain_description(self) -> str:
        return (
            f"{self.coordinate} ~ {self.coordinate} + {self.length:g}, "
            f"discretized with {self.n_points} points"
        )

    def identifications(self) -> list[str]:
        return [self.domain_description()]
