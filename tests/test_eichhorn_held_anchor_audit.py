from __future__ import annotations

from physics_lab.search.eichhorn_held_anchor_audit import (
    SOURCE_COUNTS,
    VERSION_ANCHORS,
    beta_gravity,
    find_roots,
    run_anchor_audit,
)


def test_both_source_versions_have_distinct_printed_systems() -> None:
    v1 = beta_gravity("arxiv-v1-v2", (4.1, -9.9), SOURCE_COUNTS)
    v3 = beta_gravity("arxiv-v3-final", (3.29, -4.51), SOURCE_COUNTS)
    assert v1 != v3
    assert max(abs(value) for value in v1) > 1e-2
    assert max(abs(value) for value in v3) < 1e-2


def test_source_version_roots_are_retained_without_anchor_fitting() -> None:
    report = run_anchor_audit()
    cases = {case["version"]: case for case in report["exact_source_cases"]}
    assert set(cases) == set(VERSION_ANCHORS)
    assert cases["arxiv-v1-v2"]["root_from_published_anchor"]["max_residual"] < 1e-8
    assert cases["arxiv-v3-final"]["root_from_published_anchor"]["max_residual"] < 1e-8
    assert report["headline_diagnostics"]["v3_anchor_is_zero_with_source_counts"] is False


def test_all_roots_are_retained_including_gaussian_branch() -> None:
    roots = find_roots("arxiv-v3-final", SOURCE_COUNTS)
    assert any(max(abs(value) for value in root["state"]) < 1e-8 for root in roots)
    assert all(root["max_residual"] < 1e-8 for root in roots)


def test_count_grid_is_diagnostic_and_complete() -> None:
    report = run_anchor_audit()
    grid = report["count_grid"]
    assert grid["case_count"] == 54
    assert len(grid["cases"]) == 54
    assert grid["grid_is_diagnostic_only"] is True
    assert grid["selection_performed"] is False
    assert grid["ranking_performed"] is False
    assert report["controls"]["no_parameter_fitting"] is True
