"""D3 canonical-dynamics catalog.  No extra coordinates, no selected H."""

from __future__ import annotations

from typing import Any

from physics_lab.core.model import Model
from physics_lab.core.parameter import ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Eigenstate, Quantity, Spectrum
from physics_lab.dynamics.hamiltonian import Hamiltonian
from physics_lab.geometry.d3_group import D3GroupGeometry
from physics_lab.physics.d3_canonical import (
    analyze_canonical,
    assert_solve_context,
    IRREPS,
)


def build_d3_canonical_model() -> Model:
    dynamics = Hamiltonian(
        name="H_D3_catalog",
        kind="group_algebra_catalog",
        matrix=None,
        formula="center = span{z_e, z_rotations, z_reflections}; no unique H",
        description="Catalog of D3 class sums and Cayley Laplacians. No selected Hamiltonian.",
    )

    def solve_spectrum(model: Model) -> Spectrum:
        assert_solve_context()
        data = analyze_canonical()
        states: list[Eigenstate] = []
        index = 0
        for cand in data["candidates"]:
            if cand["kind"] == "linear_combination":
                continue
            if "w_rot" in str(cand.get("eigenvalues")):
                continue
            evals = cand["eigenvalues"]
            try:
                numbers = {k: float(evals[k]) for k in IRREPS}
            except (TypeError, ValueError):
                continue
            for irrep, value in numbers.items():
                deg = 2 if irrep == "std" else 1
                copies = deg
                for copy in range(copies):
                    qty = Quantity(
                        name=f"lambda[{index}]",
                        value=value,
                        provenance=Provenance.DERIVED,
                        formula=f"{cand['name']} on {irrep}",
                        state_label=f"{cand['name']}:{irrep}:{copy}",
                        notes=("Internal eigenvalue of a candidate operator. Not unique.",),
                    )
                    states.append(
                        Eigenstate(
                            label=f"{cand['name']}:{irrep}:{copy}",
                            quantum_numbers={
                                "operator": cand["name"],
                                "irrep": irrep,
                                "degeneracy": deg,
                                "affine_family": cand["affine_family"],
                            },
                            eigenvalue=qty,
                        )
                    )
                    index += 1
        model.metadata["_analysis"] = data
        return Spectrum(
            states=states,
            method="analytic:class sums and single-class Laplacians",
            operator="catalog",
        )

    def postprocess(model: Model, spectrum: Spectrum) -> dict[str, Any]:
        data = model.metadata.pop("_analysis", None) or analyze_canonical()
        return {
            "notes": [
                "Central algebra dimension equals the number of conjugacy classes.",
                "z_rotations and z_reflections are not affine-equivalent.",
                "Unique canonical Hamiltonian: NO.",
                "Physical interpretation: UNTESTED.",
            ],
            "symmetries": ["D3"],
            "d3_canonical_test": True,
            "include_c3": False,
            "c3_detected": False,
            "d3_canonical_analysis": data,
            "quantization_chain": (
                "D3 conjugacy classes → class sums (center). "
                "Cayley Laplacians from conjugation-invariant generating sets. "
                "Two affine families remain. Unique canonical Hamiltonian: NO."
            ),
            "symbolic_formulas": {
                "z_rotations": "sum of non-identity rotations",
                "z_reflections": "sum of reflections",
                "generic_central": "a z_rotations + b z_reflections + c I",
                "affine": "H -> p H + q I",
            },
        }

    return Model(
        name="d3_canonical",
        geometry=D3GroupGeometry(),
        dynamics=dynamics,
        parameters=ParameterRegistry([]),
        observables=[],
        symmetries=["D3"],
        description="Canonical-dynamics test for D3. Catalog, no selected H.",
        solve_spectrum=solve_spectrum,
        postprocess=postprocess,
        metadata={"d3_canonical_test": True},
    )


def from_config(config: dict[str, Any]) -> Model:
    return build_d3_canonical_model()
