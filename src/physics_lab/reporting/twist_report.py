"""Report for the twisted-boundary spectrum test."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def _block(title: str, mapping: dict) -> list[str]:
    lines = [title]
    for key, value in mapping.items():
        if key == "name":
            continue
        lines.append(f"  {key}: {value}")
    return lines


def format_twist_report(result: ModelResult) -> str:
    data = result.metadata.get("twist_comparison")
    if not data:
        return ""
    tests = data.get("solver_tests") or []
    test_rows = [
        [
            t.get("label"),
            t.get("rho"),
            t.get("role"),
            "PASS" if t.get("solver_ok") else "FAIL",
        ]
        for t in tests
    ]
    lines = [
        banner("TWISTED BOUNDARY SPECTRUM TEST", width=44),
        "",
        "Periodic S¹:",
        *_block("", data.get("periodic") or {}),
        "",
        "General twist:",
        *_block("", data.get("general_twist") or {}),
        "",
        "C3:",
        *_block("", data.get("c3") or {}),
        "",
        "Twist forced by C3:",
        data.get("twist_forced_by_c3", "UNTESTED"),
        "",
        "Spectral shift:",
        data.get("spectral_shift", ""),
        "",
        "Shift provenance:",
        data.get("shift_provenance", ""),
        "",
        "Fractional spectrum:",
        data.get("fractional_spectrum", "UNTESTED"),
        "",
        "Unique prediction:",
        data.get("unique_prediction", "UNTESTED"),
        "",
        "Free continuous parameters:",
        data.get("free_continuous_parameters", ""),
        "",
        "Interpretation as electric charge:",
        data.get("charge_interpretation", "UNTESTED"),
        "",
        "Solver test inputs (NOT model results):",
        table(
            ["example", "rho", "role", "solver"],
            test_rows,
            widths=[24, 10, 36, 8],
        ),
        "",
        data.get("conclusion", ""),
        "",
        "=" * 44,
    ]
    return "\n".join(lines)
