"""Report for Phase 4C internal Hilbert spectrum plus gravity."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def _mode_rows(modes: list[dict] | None) -> list[list[str]]:
    rows = []
    for item in modes or []:
        rows.append(
            [
                str(item.get("n")),
                str(item.get("lambda")),
                str(item.get("m_n2")),
                str(item.get("m_n2_provenance")),
                str(item.get("degeneracy")),
            ]
        )
    return rows


def format_internal_spectrum_report(result: ModelResult) -> str:
    data = result.metadata.get("internal_spectrum_analysis")
    if not data:
        return ""
    ml = data.get("massless_modes") or {}
    mv = data.get("massive_modes") or {}
    deg = data.get("degeneracy") or {}
    cmp4 = data.get("compare_4b") or {}
    lines = [
        banner("PHASE 4C — INTERNAL SPECTRUM + GRAVITY", width=46),
        "",
        "Internal Hilbert space:",
        str(data.get("internal_hilbert")),
        "",
        "Internal operator:",
        "H_int",
        str(data.get("internal_operator")),
        f"  probe: {data.get('H_int_probe')}",
        "",
        "Eigenstates:",
        str(data.get("eigenstates")),
        "",
        "Eigenvalues:",
        "λ_n",
        str(data.get("eigenvalues")),
        "",
        "Mode expansion:",
        str(data.get("mode_expansion")),
        "",
        "Effective masses (branch I, H_int not in S):",
        table(["n", "lambda", "m_n2", "provenance", "degeneracy"], _mode_rows(data.get("effective_masses_I"))),
        f"  {data.get('lambda_determines_m2_I', {}).get('statement')}",
        "",
        "Effective masses (branch II, H_int ASSUMED in S):",
        table(["n", "lambda", "m_n2", "provenance", "degeneracy"], _mode_rows(data.get("effective_masses_II"))),
        f"  {data.get('lambda_determines_m2_II', {}).get('statement')}",
        "",
        "Stress-energy:",
        "T_{μν}^{(n)}",
        str(data.get("stress_energy")),
        f"  conservation: {data.get('conservation')}",
        "",
        "Weak-field response:",
        "h_{μν}^{(n)}",
        str(data.get("weak_field")),
        "",
        "Metric field equation:",
        str(data.get("metric_field_equation")),
        "",
        "Common spectral origin:",
        str(data.get("common_spectral_origin")),
        "",
        "Massless modes:",
        f"  lambda={ml.get('lambda')}  m_n2={ml.get('m_n2')}  {ml.get('classification')}",
        f"  wave T_00 identically zero: {ml.get('T00_wave_zero')}",
        "",
        "Massive modes:",
        f"  lambda={mv.get('lambda')}  m_n2={mv.get('m_n2')}  {mv.get('classification')}",
        f"  m_n2 equals lambda: {mv.get('m_equals_lambda')}",
        f"  wave T_00 identically zero: {mv.get('T00_wave_zero')}",
        "",
        "Basis invariant:",
        str(data.get("basis_invariant")),
        "",
        "Degeneracy:",
        str(deg.get("dynamics")),
        f"  {deg.get('T_in_subspace')}",
        "",
        "Parameter-free relation:",
        str(data.get("parameter_free_relation")),
        "",
        "Unique relation:",
        str(data.get("unique_relation")),
        "",
        "Free parameters:",
        str(data.get("free_parameters")),
        "",
        "G:",
        str(data.get("G")),
        "",
        "c0, c1:",
        f"{data.get('c0')}, {data.get('c1')}",
        "",
        "Compared with Phase 4B:",
        f"  4B: {cmp4.get('phase_4b')}",
        f"  4C: {cmp4.get('phase_4c')}",
        f"  added: {cmp4.get('added')}",
        "",
        "More than many scalars + gravity:",
        str(data.get("more_than_many_scalars")),
        "",
        "New theoretical freedom:",
        str(data.get("new_theoretical_freedom")),
        "",
        "Quantum unitarity:",
        str(data.get("quantum_unitarity")),
        "",
        data.get("conclusion", ""),
        "",
        banner("PHASE 4C.1 — INVARIANT SPECTRAL-RATIO AUDIT", width=50),
        "",
        "Implemented Branch II map:",
        str((data.get("spectral_ratio_audit") or {}).get("implemented_map")),
        "",
        "quantity | Branch I | Branch II | provenance",
        table(
            ["quantity", "Branch I", "Branch II", "provenance"],
            (data.get("spectral_ratio_audit") or {}).get("table") or [],
        ),
        "",
        "Branch II mass-ratio identity holds:",
        str((data.get("spectral_ratio_audit") or {}).get("branch_II_ratio_holds")),
        f"  provenance: {(data.get('spectral_ratio_audit') or {}).get('branch_II_ratio_provenance')}",
        f"  absolute mass prediction: {not (data.get('spectral_ratio_audit') or {}).get('not_absolute_mass_prediction')}",
        "",
        "Overall c_H/Z rescaling:",
        str((data.get("spectral_ratio_audit") or {}).get("scale")),
        "",
        "Promoted to full-theory prediction:",
        str((data.get("spectral_ratio_audit") or {}).get("promoted_to_full_theory_prediction")),
        "",
        (data.get("spectral_ratio_audit") or {}).get("stop", ""),
    ]
    return "\n".join(lines)
