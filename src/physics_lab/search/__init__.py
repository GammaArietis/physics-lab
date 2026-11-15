"""Bounded, provenance-preserving search pilots."""

from physics_lab.search.alpha_geometry_pilot import (
    ALPHA_GEOMETRY_SEARCH_VERSION,
    DEFAULT_ACTIONS,
    DEFAULT_GRAPH_FAMILIES,
    enumerate_alpha_geometry_pilot,
    run_alpha_geometry_pilot,
    write_alpha_geometry_report,
)
from physics_lab.search.wyler_neighborhood import (
    WYLER_SEARCH_VERSION,
    run_wyler_neighborhood_pilot,
    write_wyler_report,
    wyler_anchor,
)
from physics_lab.search.wyler_dimension_scan import (
    DEFAULT_ABSTRACT_DIMENSIONS,
    WYLER_DIMENSION_SCAN_VERSION,
    run_wyler_dimension_scan,
    write_wyler_dimension_report,
)
from physics_lab.search.sm_gravity_mixing_rg import (
    SM_GRAVITY_MIXING_RG_VERSION,
    run_sm_gravity_mixing_campaign,
    write_sm_gravity_mixing_report,
)
from physics_lab.search.gravity_sm_fixed_point_rg import (
    GRAVITY_SM_FIXED_POINT_RG_VERSION,
    run_gravity_sm_fixed_point_campaign,
    write_gravity_sm_fixed_point_report,
)

__all__ = [
    "ALPHA_GEOMETRY_SEARCH_VERSION",
    "DEFAULT_ACTIONS",
    "DEFAULT_GRAPH_FAMILIES",
    "enumerate_alpha_geometry_pilot",
    "run_alpha_geometry_pilot",
    "write_alpha_geometry_report",
    "WYLER_SEARCH_VERSION",
    "run_wyler_neighborhood_pilot",
    "write_wyler_report",
    "wyler_anchor",
    "DEFAULT_ABSTRACT_DIMENSIONS",
    "WYLER_DIMENSION_SCAN_VERSION",
    "run_wyler_dimension_scan",
    "write_wyler_dimension_report",
    "SM_GRAVITY_MIXING_RG_VERSION",
    "run_sm_gravity_mixing_campaign",
    "write_sm_gravity_mixing_report",
    "GRAVITY_SM_FIXED_POINT_RG_VERSION",
    "run_gravity_sm_fixed_point_campaign",
    "write_gravity_sm_fixed_point_report",
]
