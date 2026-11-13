"""Rectangular torus as internal geometry.  One dimensionless modulus a = Lx/Ly.

Overall area is a scale convention, not a shape parameter.
"""

from __future__ import annotations

from physics_lab.geometry.geometry import Geometry


class RectangularTorusGeometry(Geometry):
    """T² = R² / (Lx Z × Ly Z) with a = Lx/Ly.

    a is a modulus.  It is not inserted as a preferred fraction.
    """

    def __init__(self) -> None:
        super().__init__(
            name="T2_rectangular",
            coordinates=("x", "y"),
            periodic=True,
            description=self.domain_description(),
        )

    def period(self) -> None:
        return None

    def domain_description(self) -> str:
        return "T² rectangular: (x,y) ~ (x+Lx, y) ~ (x, y+Ly),  a = Lx/Ly, area factored out"

    def identifications(self) -> list[str]:
        return ["x ~ x + Lx", "y ~ y + Ly", "a ~ 1/a by swapping axes"]
