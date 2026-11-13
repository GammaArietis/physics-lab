"""Load a model from YAML/JSON or from a Python builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, ProvenanceError
from physics_lab.models.examples import (
    c3_model,
    circle_model,
    coupling_model,
    coupling_norm_model,
    d3_canonical_model,
    d3_model,
    dynamic_geometry_model,
    dynamical_principle_model,
    dynamical_principle_phase2_model,
    kinetic_structure_model,
    spacetime_model,
    dynamical_metric_model,
    gravity_internal_model,
    internal_spectrum_model,
    gauge_internal_model,
    phase5b0_model,
    phase5c_model,
    phase5d_model,
    phase6_model,
    phase7_model,
    phase8_model,
    phase9_model,
    phase10a_model,
    phase10b1_model,
    phase10b2_model,
    phase10b3_model,
    phase10b4_model,
    phase10b5_model,
    phase10b6_model,
    phase10b7_model,
    phase10b8_model,
    phase10b9_model,
    phase10b10_model,
    phase10c_model,
    phase10d_model,
    phase10e_model,
    phase11a_input_model,
    phase11a_model,
    phase11b_qft_model,
    phase11c_model,
    phase11d_model,
    phase11e_model,
    phase11f_model,
    phase11fa_model,
    phase11fb_model,
    phase11g_model,
    phase11h_model,
    phase11i_model,
    phase11j_model,
    phase11k_model,
    phase11l_model,
    phase11m_model,
    phase11n_model,
    phase11o_model,
    phase11p_model,
    phase11q_model,
    phase11r_model,
    phase11s_model,
    phase11t_model,
    phase11u_model,
    phase11v_model,
    phase11w_model,
    phase11x_model,
    phase11y_model,
    phase11z_model,
    phase11aa_model,
    phase11ab_model,
    phase11ac_model,
    phase11ad_model,
    phase11ae_model,
    phase11ae1_model,
    phase11b1_model,
    phase11b2_model,
    phase11b3_model,
    phase11b4_model,
    phase11b5_model,
    phase11b6_model,
    phase12a_model,
    phase12b_model,
    phase12c_model,
    phase12d_model,
    phase13_model,
    phase13_1_model,
    phase14a_model,
    phase14b0_model,
    phase14b1_model,
    phase14b2_model,
    phase14b3_model,
    phase14b3r_model,
    phase14b4_model,
    phase14b4r_model,
    phase14b4r2_model,
    phase14b5_model,
    phase14b6_model,
    phase14c0_model,
    phase14c1_model,
    phase14c2_model,
    phase14c3_model,
    phase14c4_model,
    phase14c5_model,
    phase14c5q_model,
    phase14c5d_model,
    phase14c5e_model,
    phase14c5e1_model,
    phase14c5f_model,
    phase14c5g_model,
    phase14c5g1_model,
    phase14c5h_model,
    phase14c5h1_model,
    phase14c5h2_model,
    phase14c5h3_model,
    phase14c5h4_model,
    phase14c5h5_model,
    phase14c5i_model,
    phase14c5j_model,
    phase14c5k_model,
    emergent_vector_model,
    invariants_model,
    pure_c3_model,
    s1_c3_model,
    toy_mass_charge,
    twisted_s1_model,
)

BUILDERS: dict[str, Callable[[dict[str, Any]], Model]] = {
    "circle_model": circle_model.from_config,
    "circle": circle_model.from_config,
    "c3_model": c3_model.from_config,
    "c3": c3_model.from_config,
    "s1_c3": s1_c3_model.from_config,
    "s1_c3_model": s1_c3_model.from_config,
    "twisted_s1": twisted_s1_model.from_config,
    "twisted_s1_model": twisted_s1_model.from_config,
    "s1_c3_coupling": coupling_model.from_config,
    "s1_coupling": coupling_model.from_config,
    "coupling": coupling_model.from_config,
    "s1_c3_coupling_norm": coupling_norm_model.from_config,
    "s1_coupling_norm": coupling_norm_model.from_config,
    "coupling_norm": coupling_norm_model.from_config,
    "s1_c3_emergent_vector": emergent_vector_model.from_config,
    "s1_emergent_vector": emergent_vector_model.from_config,
    "emergent_vector": emergent_vector_model.from_config,
    "s1_c3_invariants": invariants_model.from_config,
    "s1_invariants": invariants_model.from_config,
    "invariants": invariants_model.from_config,
    "pure_c3": pure_c3_model.from_config,
    "c3_group": pure_c3_model.from_config,
    "d3": d3_model.from_config,
    "d3_group": d3_model.from_config,
    "d3_canonical": d3_canonical_model.from_config,
    "dynamic_geometry": dynamic_geometry_model.from_config,
    "t2_rectangular": dynamic_geometry_model.from_config,
    "dynamical_principle": dynamical_principle_model.from_config,
    "dynamical_principle_phase2": dynamical_principle_phase2_model.from_config,
    "kinetic_structure": kinetic_structure_model.from_config,
    "spacetime": spacetime_model.from_config,
    "minkowski": spacetime_model.from_config,
    "dynamical_metric": dynamical_metric_model.from_config,
    "lorentzianmanifold": dynamical_metric_model.from_config,
    "gravity_internal": gravity_internal_model.from_config,
    "dynamical_gravity": gravity_internal_model.from_config,
    "internal_spectrum": internal_spectrum_model.from_config,
    "gauge_internal": gauge_internal_model.from_config,
    "phase5b0": phase5b0_model.from_config,
    "phase5c": phase5c_model.from_config,
    "phase5d": phase5d_model.from_config,
    "phase6": phase6_model.from_config,
    "phase7": phase7_model.from_config,
    "phase8": phase8_model.from_config,
    "phase9": phase9_model.from_config,
    "phase10a": phase10a_model.from_config,
    "phase10b1": phase10b1_model.from_config,
    "phase10b2": phase10b2_model.from_config,
    "phase10b3": phase10b3_model.from_config,
    "phase10b4": phase10b4_model.from_config,
    "phase10b5": phase10b5_model.from_config,
    "phase10b6": phase10b6_model.from_config,
    "phase10b7": phase10b7_model.from_config,
    "phase10b8": phase10b8_model.from_config,
    "phase10b9": phase10b9_model.from_config,
    "phase10b10": phase10b10_model.from_config,
    "phase10c": phase10c_model.from_config,
    "phase10d": phase10d_model.from_config,
    "phase10e": phase10e_model.from_config,
    "phase11a_input": phase11a_input_model.from_config,
    "phase11a": phase11a_model.from_config,
    "phase11b_qft": phase11b_qft_model.from_config,
    "phase11c": phase11c_model.from_config,
    "phase11d": phase11d_model.from_config,
    "phase11e": phase11e_model.from_config,
    "phase11f": phase11f_model.from_config,
    "phase11fa": phase11fa_model.from_config,
    "phase11fb": phase11fb_model.from_config,
    "phase11g": phase11g_model.from_config,
    "phase11h": phase11h_model.from_config,
    "phase11i": phase11i_model.from_config,
    "phase11j": phase11j_model.from_config,
    "phase11k": phase11k_model.from_config,
    "phase11l": phase11l_model.from_config,
    "phase11m": phase11m_model.from_config,
    "phase11n": phase11n_model.from_config,
    "phase11o": phase11o_model.from_config,
    "phase11p": phase11p_model.from_config,
    "phase11q": phase11q_model.from_config,
    "phase11r": phase11r_model.from_config,
    "phase11s": phase11s_model.from_config,
    "phase11t": phase11t_model.from_config,
    "phase11u": phase11u_model.from_config,
    "phase11v": phase11v_model.from_config,
    "phase11w": phase11w_model.from_config,
    "phase11x": phase11x_model.from_config,
    "phase11y": phase11y_model.from_config,
    "phase11z": phase11z_model.from_config,
    "phase11aa": phase11aa_model.from_config,
    "phase11ab": phase11ab_model.from_config,
    "phase11ac": phase11ac_model.from_config,
    "phase11ad": phase11ad_model.from_config,
    "phase11ae": phase11ae_model.from_config,
    "phase11ae1": phase11ae1_model.from_config,
    "phase11b1": phase11b1_model.from_config,
    "phase11b2": phase11b2_model.from_config,
    "phase11b3": phase11b3_model.from_config,
    "phase11b4": phase11b4_model.from_config,
    "phase11b5": phase11b5_model.from_config,
    "phase11b6": phase11b6_model.from_config,
    "phase12a": phase12a_model.from_config,
    "phase12b": phase12b_model.from_config,
    "phase12c": phase12c_model.from_config,
    "phase12d": phase12d_model.from_config,
    "phase13": phase13_model.from_config,
    "phase13_1": phase13_1_model.from_config,
    "phase14a": phase14a_model.from_config,
    "phase14b0": phase14b0_model.from_config,
    "phase14b1": phase14b1_model.from_config,
    "phase14b2": phase14b2_model.from_config,
    "phase14b3": phase14b3_model.from_config,
    "phase14b3r": phase14b3r_model.from_config,
    "phase14b4": phase14b4_model.from_config,
    "phase14b4r": phase14b4r_model.from_config,
    "phase14b4r2": phase14b4r2_model.from_config,
    "phase14b5": phase14b5_model.from_config,
    "phase14b6": phase14b6_model.from_config,
    "phase14c0": phase14c0_model.from_config,
    "phase14c1": phase14c1_model.from_config,
    "phase14c2": phase14c2_model.from_config,
    "phase14c3": phase14c3_model.from_config,
    "phase14c4": phase14c4_model.from_config,
    "phase14c5": phase14c5_model.from_config,
    "phase14c5q": phase14c5q_model.from_config,
    "phase14c5d": phase14c5d_model.from_config,
    "phase14c5e": phase14c5e_model.from_config,
    "phase14c5e1": phase14c5e1_model.from_config,
    "phase14c5f": phase14c5f_model.from_config,
    "phase14c5g": phase14c5g_model.from_config,
    "phase14c5g1": phase14c5g1_model.from_config,
    "phase14c5h": phase14c5h_model.from_config,
    "phase14c5h1": phase14c5h1_model.from_config,
    "phase14c5h2": phase14c5h2_model.from_config,
    "phase14c5h3": phase14c5h3_model.from_config,
    "phase14c5h4": phase14c5h4_model.from_config,
    "phase14c5h5": phase14c5h5_model.from_config,
    "phase14c5i": phase14c5i_model.from_config,
    "phase14c5j": phase14c5j_model.from_config,
    "phase14c5k": phase14c5k_model.from_config,
    "toy_mass_charge": lambda cfg: toy_mass_charge.build_toy_mass_charge_model(),
}


def load_config(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    suffix = Path(path).suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif suffix == ".json":
        import json

        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"Config {path} must be a mapping.")
    return data


def load_model(path: str | Path) -> Model:
    config = load_config(path)
    return build_from_config(config)


def _reject_derived_config_parameters(config: dict[str, Any]) -> None:
    """Config values are inserted.  They cannot be labelled DERIVED."""
    params = config.get("parameters", {})
    if not isinstance(params, dict):
        return
    for name, block in params.items():
        if not isinstance(block, dict):
            continue
        provenance = str(block.get("provenance", "INPUT")).upper()
        if provenance == Provenance.DERIVED.value:
            raise ProvenanceError(
                f"Config parameter '{name}' is inserted from YAML/JSON and "
                "cannot be marked DERIVED. Use INPUT, ASSUMED, or CALIBRATED."
            )


def build_from_config(config: dict[str, Any]) -> Model:
    _reject_derived_config_parameters(config)
    name = str(config.get("name") or config.get("geometry", {}).get("type") or "")
    key = name.strip().lower()
    if key not in BUILDERS:
        geo = str(config.get("geometry", {}).get("type", "")).lower()
        if geo in BUILDERS:
            key = geo
        elif geo == "circle":
            key = "circle"
        else:
            raise KeyError(
                f"Unknown model '{name}'. Known: {sorted(BUILDERS)}"
            )
    return BUILDERS[key](config)
