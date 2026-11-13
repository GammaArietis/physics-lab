"""Internal space = the finite group D3 ≃ S3.  No continuous coordinate."""

from __future__ import annotations

from physics_lab.geometry.geometry import Geometry


class D3GroupGeometry(Geometry):
    """D3 = <r, s | r^3 = e, s^2 = e, s r s = r^{-1}>.

    This is not a discretized circle and not C3.
    """

    def __init__(self) -> None:
        super().__init__(
            name="D3",
            coordinates=(),
            periodic=False,
            description=self.domain_description(),
        )

    def period(self) -> None:
        return None

    def domain_description(self) -> str:
        return "internal space = group D3 = <r,s | r^3=e, s^2=e, s r s = r^{-1}>"

    def identifications(self) -> list[str]:
        return ["r^3 = e", "s^2 = e", "s r s = r^{-1}"]
