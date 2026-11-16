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
from physics_lab.search.eichhorn_held_asymptotic_safety import (
    EICHHORN_HELD_AS_VERSION,
    gravity_equation_fixed_point,
    literature_anchor_audit,
    run_eichhorn_held_campaign,
    write_eichhorn_held_report,
)
from physics_lab.search.eichhorn_held_anchor_audit import (
    ANCHOR_AUDIT_VERSION,
    run_anchor_audit,
    write_anchor_audit_report,
)
from physics_lab.search.eichhorn_held_ir_matching import (
    IR_MATCHING_VERSION,
    dimensionless_ir_observables,
    integrate_target_blind_trajectory,
    run_ir_matching_campaign,
    write_ir_matching_report,
)
from physics_lab.search.eichhorn_held_physical_matching import (
    PHYSICAL_MATCHING_VERSION,
    run_physical_matching_campaign,
    sm_matching_beta,
    write_physical_matching_report,
)

from physics_lab.search.smdr_backend import (
    SMDR_BRIDGE_VERSION,
    run_smdr_calc_all,
    target_blind_input_text,
    write_smdr_report,
)
from physics_lab.search.gauge_yukawa_threshold_eft import (
    THRESHOLD_EFT_VERSION,
    active_multiplicities,
    run_threshold_candidate,
    run_threshold_campaign,
    threshold_map,
    thresholded_gauge_coefficients,
    write_threshold_report,
)
from physics_lab.search.gauge_yukawa_precision_pipeline import (
    PRECISION_PIPELINE_VERSION,
    critical_exponents,
    precision_beta_state,
    run_precision_campaign,
    run_precision_candidate,
    search_fixed_points,
    two_loop_gauge_matrix,
    vacuum_stability,
    write_precision_report,
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
    "EICHHORN_HELD_AS_VERSION",
    "gravity_equation_fixed_point",
    "literature_anchor_audit",
    "run_eichhorn_held_campaign",
    "write_eichhorn_held_report",
    "ANCHOR_AUDIT_VERSION",
    "run_anchor_audit",
    "write_anchor_audit_report",
    "IR_MATCHING_VERSION",
    "dimensionless_ir_observables",
    "integrate_target_blind_trajectory",
    "run_ir_matching_campaign",
    "write_ir_matching_report",
    "PHYSICAL_MATCHING_VERSION",
    "run_physical_matching_campaign",
    "sm_matching_beta",
    "write_physical_matching_report",
    "SMDR_BRIDGE_VERSION",
    "run_smdr_calc_all",
    "target_blind_input_text",
    "write_smdr_report",
    "THRESHOLD_EFT_VERSION",
    "active_multiplicities",
    "run_threshold_candidate",
    "run_threshold_campaign",
    "threshold_map",
    "thresholded_gauge_coefficients",
    "write_threshold_report",
    "PRECISION_PIPELINE_VERSION",
    "critical_exponents",
    "precision_beta_state",
    "run_precision_campaign",
    "run_precision_candidate",
    "search_fixed_points",
    "two_loop_gauge_matrix",
    "vacuum_stability",
    "write_precision_report",
]
