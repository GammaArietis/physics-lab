"""Phase 10A report: model-space grammar and integrity firewall."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.physics.phase10a_model_grammar import (
    phase10a_objective_text,
    phase10a_scope_summary_text,
)
from physics_lab.reporting.formatting import banner, table


def format_phase10a_report(result: ModelResult) -> str:
    data = result.metadata.get("phase10a_analysis")
    integrity = result.metadata.get("phase10a_integrity") or {}
    freeze = result.metadata.get("action_freeze") or {}
    if not data and not integrity and not freeze:
        return ""
    science = data
    if isinstance(data, dict) and data.get("scientific_analysis") is not None:
        science = data.get("scientific_analysis")
    authorized = bool(
        integrity.get("PRE_ANALYSIS_GATE") == "VERIFIED"
        and integrity.get("ATOMIC_GATE") == "VERIFIED"
        and isinstance(science, dict)
        and science.get("status") == "OK"
    )
    lines = [
        banner("PHASE 10A — AUTOMATED STRUCTURAL MODEL EXPLORER", width=56),
        "",
        phase10a_objective_text(),
        "",
        phase10a_scope_summary_text(),
        "",
        "ACTION_CONTENT_HASH:",
        f"    {freeze.get('action_content_hash') or freeze.get('fingerprint') or integrity.get('ACTION_CONTENT_HASH')}",
        "FREEZE_STATUS:",
        f"    {freeze.get('freeze_status') or integrity.get('FREEZE_STATUS')}",
        "PHASE_5C_UNCHANGED:",
        f"    {integrity.get('PHASE_5C_UNCHANGED', 'UNTESTED')}",
        "PHASE_5D_UNCHANGED:",
        f"    {integrity.get('PHASE_5D_UNCHANGED', 'UNTESTED')}",
        "PHASE_6_UNCHANGED:",
        f"    {integrity.get('PHASE_6_UNCHANGED', 'UNTESTED')}",
        "PHASE_7_UNCHANGED:",
        f"    {integrity.get('PHASE_7_UNCHANGED', 'UNTESTED')}",
        "PHASE_8_UNCHANGED:",
        f"    {integrity.get('PHASE_8_UNCHANGED', 'UNTESTED')}",
        "PHASE_9_UNCHANGED:",
        f"    {integrity.get('PHASE_9_UNCHANGED', 'UNTESTED')}",
        "FROZEN_ACTION_MODIFIED:",
        f"    {integrity.get('FROZEN_ACTION_MODIFIED', 'UNTESTED')}",
        "EXPERIMENTAL_INPUTS:",
        f"    {integrity.get('EXPERIMENTAL_INPUTS', 'UNTESTED')}",
        "FITTING:",
        f"    {integrity.get('FITTING', 'UNTESTED')}",
        "CALIBRATION:",
        f"    {integrity.get('CALIBRATION', 'UNTESTED')}",
        "NUMERICAL_TARGET_SEARCH:",
        f"    {integrity.get('NUMERICAL_TARGET_SEARCH', 'UNTESTED')}",
        "PYTEST:",
        f"    {integrity.get('PYTEST', integrity.get('PYTEST_STATUS', 'UNTESTED'))}",
        "",
    ]
    if not authorized:
        lines.extend(
            [
                "SCIENTIFIC GRAMMAR CONCLUSIONS: NOT EMITTED",
                "Gate failed or analysis was not authorized.",
            ]
        )
        return "\n".join(lines)
    qs = science.get("scientific_questions") or {}
    size = science.get("search_size_estimate") or {}
    catalogs = science.get("catalogs") or {}
    cat_rows = [[axis, ", ".join(ids)] for axis, ids in catalogs.items()]
    lines.extend(
        [
            "PHASE 10A STATUS",
            "",
            f"MODEL_GRAMMAR_STATUS = {science.get('MODEL_GRAMMAR_STATUS')}",
            f"PROVENANCE_FIREWALL_STATUS = {science.get('PROVENANCE_FIREWALL_STATUS')}",
            f"CANONICALIZATION_STATUS = {science.get('CANONICALIZATION_STATUS')}",
            f"DEDUPLICATION_STATUS = {science.get('DEDUPLICATION_STATUS')}",
            f"PARAMETER_ACCOUNTING_STATUS = {science.get('PARAMETER_ACCOUNTING_STATUS')}",
            f"TARGET_BLINDNESS_STATUS = {science.get('TARGET_BLINDNESS_STATUS')}",
            f"SEARCH_REPRODUCIBILITY_STATUS = {science.get('SEARCH_REPRODUCIBILITY_STATUS')}",
            f"KNOWN_PHYSICS_ISOLATION_STATUS = {science.get('KNOWN_PHYSICS_ISOLATION_STATUS')}",
            f"MANDATORY_RULES_STATUS = {science.get('MANDATORY_RULES_STATUS')}",
            f"REFERENCE_SEPARATION_STATUS = {science.get('REFERENCE_SEPARATION_STATUS')}",
            f"EXAMPLE_SEPARATION_STATUS = {science.get('EXAMPLE_SEPARATION_STATUS')}",
            f"GRAMMAR_REGISTRATION_STATUS = {science.get('GRAMMAR_REGISTRATION_STATUS')}",
            f"WHITELIST_STATUS = {science.get('WHITELIST_STATUS')}",
            f"BLACKLIST_STATUS = {science.get('BLACKLIST_STATUS')}",
            f"PHASE_10A_STATUS = {science.get('PHASE_10A_STATUS')}",
            "",
            f"grammar_version = {science.get('grammar_version')}",
            f"grammar_hash = {science.get('grammar_hash')}",
            f"finite_combination_count (not instantiated) = {size.get('finite_combination_count')}",
            f"large_scale_generation_executed = {science.get('large_scale_generation_executed')}",
            f"baseline_hash = {science.get('baseline_hash')}",
            "",
            "A. MANDATORY RULE SET",
            table(
                ["id", "class", "rule"],
                [
                    [item["identifier"], item.get("status"), item["mathematical_definition"]]
                    for item in science.get("mandatory_rule_set") or []
                ],
                widths=[6, 12, 90],
            ),
            "",
            "B. REFERENCE CATALOG",
            table(
                ["id", "status", "generator_enabled", "note"],
                [
                    [
                        item["identifier"],
                        item.get("status"),
                        str(item.get("generator_enabled")),
                        item["mathematical_definition"],
                    ]
                    for item in science.get("reference_catalog") or []
                ],
                widths=[40, 16, 18, 72],
            ),
            "",
            "C. EXAMPLE CATALOG",
            table(
                ["id", "status", "generator_enabled", "illustration"],
                [
                    [
                        item["identifier"],
                        item.get("status"),
                        str(item.get("generator_enabled")),
                        item["mathematical_definition"],
                    ]
                    for item in science.get("example_catalog") or []
                ],
                widths=[36, 14, 18, 72],
            ),
            "",
            "Registered generator catalogs (MANDATORY, generator_enabled = TRUE):",
            table(["axis", "ids"], cat_rows, widths=[28, 72]),
            "",
            "SEARCH-SPACE REPORT",
            table(
                ["item", "class", "value"],
                [
                    [key, (val or {}).get("status"), str((val or {}).get("value"))]
                    for key, val in (science.get("search_space_report") or {}).items()
                ],
                widths=[32, 16, 80],
            ),
            "",
            "supported equivalences (MANDATORY):",
            f"    {science.get('supported_equivalences')}",
            "unsupported equivalences (MANDATORY):",
            f"    {science.get('unsupported_equivalences')}",
            "prohibited structures (MANDATORY):",
            f"    {science.get('blacklist_ids')}",
            "registered blind filters (MANDATORY):",
            f"    {science.get('blind_filters')}",
            "documentary filters (REFERENCE_ONLY):",
            f"    {[item.get('mathematical_definition') for item in science.get('reference_blind_filters') or []]}",
            "cluster labels (EXAMPLE_ONLY):",
            f"    {science.get('cluster_labels')}",
            "",
            "1. Grammar finite and explicit?",
            f"    {qs.get('1_grammar_finite_and_explicit')}",
            "2. Large-scale run in 10A?",
            f"    {qs.get('2_large_scale_run')}",
            "3. Baseline is established structure only?",
            f"    {qs.get('3_baseline_is_established_only')}",
            "4. F^2 in frozen baseline?",
            f"    {qs.get('4_F2_in_frozen_baseline')}",
            "5. Target-blind?",
            f"    {qs.get('5_target_blind')}",
            "6. Known-physics catalog isolated?",
            f"    {qs.get('6_known_physics_isolated')}",
            "7. Ready for Phase 10B?",
            f"    {qs.get('7_ready_for_10B')}",
            "8. Examples separated from mandatory rules?",
            f"    {qs.get('8_examples_separated_from_rules')}",
            "9. Reference material separated from generator?",
            f"    {qs.get('9_reference_separated_from_rules')}",
            "",
            "Phase 10A STOP. No brute-force exploration. No ranking.",
            "A documented example is not a generator rule.",
            "REFERENCE_ONLY content is not a generator rule.",
            "",
            "PHASE 10A CLOSED" if science.get("PHASE_10A_CLOSED") else "Phase 10A is not closed.",
        ]
    )
    return "\n".join(lines)
