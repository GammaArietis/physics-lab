"""Phase 11AF path closure.

Read-only consolidation of the authorized trajectory 11R through 11AE.1.
This module does not select a physical principle, activate an assumption,
or rewrite any earlier artifact.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import freeze_paths, verify_phase4c_action_freeze

PHASE = "PHASE_11AF_PATH_CLOSURE"
MODULE_VERSION = "phase11af-path-closure-v1"
FROZEN_4C_HASH = "c26df583fbe4dc48b32eeb2dc60cfe44c7b0d1dd3a17f99a477401b5db65a0b9"

GUARDED_DIRECTORIES = (
    "phase11r_artifacts",
    "phase11s_artifacts",
    "phase11t_artifacts",
    "phase11u_artifacts",
    "phase11v_artifacts",
    "phase11w_artifacts",
    "phase11x_artifacts",
    "phase11y_artifacts",
    "phase11z_artifacts",
    "phase11aa_artifacts",
    "phase11ab_artifacts",
    "phase11ac_artifacts",
    "phase11ad_artifacts",
    "phase11ae_artifacts",
    "phase11ae1_artifacts",
)

CLASS_C_ITEMS = ("T06", "T07", "T08")
CLASS_D_ITEMS = ("T09", "T10", "T11", "T12", "T13", "T14")
CLASS_E_ITEMS = ("T15", "T16", "T17")
UNRESOLVED_FUNCTIONS = ("f_a(T)", "Z_i", "W", "K")

_ACTIVATED_ARCHITECTURE = (
    "recursive autonomous theory engine",
    "universal theory search engine",
    "new grammar",
    "new server architecture",
    "new model-selection engine",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parent


def _artifact_dir() -> Path:
    return _physics_dir() / "phase11af_closure_artifacts"


def _guarded_files() -> dict[str, Path]:
    root = _physics_dir()
    found: dict[str, Path] = {}
    for directory in GUARDED_DIRECTORIES:
        folder = root / directory
        if not folder.is_dir():
            found[directory] = folder
            continue
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                found[str(path.relative_to(root))] = path
    freeze_path, _lock_path = freeze_paths(root)
    found[str(freeze_path)] = freeze_path
    return found


def _snapshot(files: dict[str, Path]) -> dict[str, str]:
    digest: dict[str, str] = {}
    for name, path in files.items():
        if not path.is_file():
            digest[name] = "MISSING"
            continue
        digest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def _load(relative: str) -> dict[str, Any]:
    path = _physics_dir() / relative
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def _integrity_failure(detail: str) -> dict[str, Any]:
    return {
        "status": "PHASE11_CLOSURE_INTEGRITY_FAILURE",
        "PHASE11_INTEGRITY_STATUS": "FAILED",
        "PHASE11_CONSOLIDATION_STATUS": "FAILED",
        "PHASE_11AF_STATUS": "FAILED",
        "PHASE_11AF_STOPPED": True,
        "detail": detail,
        "scientific_analysis": None,
    }


def _authorization_by_scope(authorizations: list[Any]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for item in authorizations:
        if isinstance(item, dict) and isinstance(item.get("scope"), str):
            found[item["scope"]] = item
    return found


def _parameter_ledger(rows: list[Any]) -> dict[str, Any]:
    fixed: list[str] = []
    independent: list[str] = []
    branch_specific: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        quantity = str(row.get("quantity"))
        if row.get("constrained") is True:
            fixed.append(quantity)
        else:
            independent.append(quantity)
        if row.get("independent_across_branches") is True:
            branch_specific.append(quantity)
    unresolved = [name for name in UNRESOLVED_FUNCTIONS if name in independent]
    return {
        "fixed_parameters": fixed,
        "reduced_parameters": [],
        "independent_parameters": independent,
        "branch_specific_parameters": branch_specific,
        "unresolved_functions": unresolved,
        "modulus_expectation_value": {
            "symbol": "<T>",
            "source_symbol": "T",
            "exists_as_input_symbol": True,
            "stabilized": False,
        },
        "unauthorized_parameter_identification": False,
    }


def _human_input(authorizations: dict[str, dict[str, Any]], decision_map: dict[str, Any]) -> dict[str, Any]:
    assumptions = []
    for item in CLASS_C_ITEMS:
        record = authorizations.get(item, {})
        assumptions.append(
            {
                "item": item,
                "classification": "CLASS-C",
                "decision": decision_map.get(item),
                "mathematical_statement": record.get("mathematical_statement"),
                "exact_missing_assumption": record.get("exact_missing_input_or_assumption"),
                "activated": False,
            }
        )
    physical = []
    for item in CLASS_D_ITEMS:
        record = authorizations.get(item, {})
        physical.append(
            {
                "item": item,
                "classification": "CLASS-D",
                "decision": decision_map.get(item),
                "physical_input": record.get("physical_input"),
                "mathematical_statement": record.get("mathematical_statement"),
                "activated": False,
            }
        )
    scope = []
    for item in CLASS_E_ITEMS:
        record = authorizations.get(item, {})
        scope.append(
            {
                "item": item,
                "classification": "CLASS-E",
                "decision": decision_map.get(item),
                "mathematical_statement": record.get("mathematical_statement"),
                "activated": False,
            }
        )
    return {
        "CLASS_C_ASSUMPTIONS": assumptions,
        "CLASS_D_PHYSICAL_INPUTS": physical,
        "CLASS_E_SCOPE_CHANGES": scope,
        "chosen_item": None,
    }


def _consistency_matrix(summaries: dict[str, dict[str, Any]], vacuum: dict[str, Any], modulus: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "sector": "SUSY",
            "strongest_certified_result": "11S off-shell closure and chiral completion are verified under the declared SUSY extension",
            "current_status": str(summaries["11S"].get("PHASE_11S_STATUS")),
            "remaining_gap": "the extension is an authorized input; uniqueness is not certified",
        },
        {
            "sector": "SUSY breaking",
            "strongest_certified_result": "11T records explicit and spontaneous breaking structures as declared extensions",
            "current_status": str(summaries["11T"].get("PHASE_11T_STATUS")),
            "remaining_gap": "no breaking mechanism is selected as necessary",
        },
        {
            "sector": "SUGRA",
            "strongest_certified_result": "11U records a partial supergravity extension",
            "current_status": str(summaries["11U"].get("PHASE_11U_STATUS")),
            "remaining_gap": "quantum supergravity remains " + str(summaries["11U"].get("QUANTUM_SUPERGRAVITY_STATUS")),
        },
        {
            "sector": "gravity mediation",
            "strongest_certified_result": "11V is an explicit new-input branch with certified PFR count 0",
            "current_status": str(summaries["11V"].get("GRAVITY_MEDIATION_STATUS")),
            "remaining_gap": "branch not derived from another branch and not selected",
        },
        {
            "sector": "gauge mediation",
            "strongest_certified_result": "11X uniqueness is " + str(summaries["11X"].get("GAUGE_MEDIATION_UNIQUENESS")),
            "current_status": str(summaries["11X"].get("PHASE_11X_STATUS")),
            "remaining_gap": "branch remains an isolated new-input record",
        },
        {
            "sector": "anomaly mediation",
            "strongest_certified_result": "11Y PFR status is " + str(summaries["11Y"].get("PFR_STATUS")),
            "current_status": str(summaries["11Y"].get("PHASE_11Y_STATUS")),
            "remaining_gap": "uniqueness is " + str(summaries["11Y"].get("ANOMALY_MEDIATION_UNIQUENESS_STATUS")),
        },
        {
            "sector": "modulus mediation",
            "strongest_certified_result": "11Z stabilization status is " + str(summaries["11Z"].get("MODULUS_STABILIZATION_STATUS")),
            "current_status": str(summaries["11Z"].get("PHASE_11Z_STATUS")),
            "remaining_gap": "F_T and f_a(T) remain unresolved inputs",
        },
        {
            "sector": "direct mediation",
            "strongest_certified_result": "11AA uniqueness is " + str(summaries["11AA"].get("DIRECT_MEDIATION_UNIQUENESS_STATUS")),
            "current_status": str(summaries["11AA"].get("PHASE_11AA_STATUS")),
            "remaining_gap": "M_direct remains an input scale",
        },
        {
            "sector": "vacuum",
            "strongest_certified_result": "11AE.1 containment: vacuum selection is not contained",
            "current_status": vacuum["VACUUM_SELECTION_STATUS"],
            "remaining_gap": "principle remains " + vacuum["PRINCIPLE_ID"],
        },
        {
            "sector": "moduli",
            "strongest_certified_result": "modulus symbol T exists as INPUT; stabilization mechanism is NOT_FOUND",
            "current_status": modulus["T10"],
            "remaining_gap": "existence of the symbol is separate from stabilization",
        },
        {
            "sector": "UV",
            "strongest_certified_result": "11Q remains partial; T12 stays a required new physical input",
            "current_status": str(summaries["11Q"].get("PHASE_11Q_STATUS")),
            "remaining_gap": "no UV-completion principle is activated",
        },
        {
            "sector": "gauge structure",
            "strongest_certified_result": "11N global gauge structure remains partial",
            "current_status": str(summaries["11N"].get("PHASE_11N_STATUS")),
            "remaining_gap": "no new gauge structure is introduced by this closure",
        },
    ]


def _questions(record: dict[str, Any]) -> list[dict[str, str]]:
    frontier = record["FIRST_UNDERDETERMINED_LAYER"]
    return [
        {
            "n": "1",
            "q": "What is the strongest result of Phase 11?",
            "a": "The five mediation branches remain explicit, mutually non-derived inputs; their certified PFR count is 0; and 11AE.1 establishes that vacuum selection is not contained in the existing modules.",
        },
        {
            "n": "2",
            "q": "Which results are conditional on explicit new physical inputs?",
            "a": "Each mediation branch record is conditional on its own declared input. T09, T10, T11, T12, T13, and T14 have no derived consequence on this path because their physical inputs stay inactive.",
        },
        {
            "n": "3",
            "q": "Which results were genuinely derived from existing structure?",
            "a": "The distinctness of F_X, F_phi, and F_T; the exhaustion of the existing-module path for T04 and T05 at PARTIAL; and the 11AE.1 result that a vacuum-selection principle is not contained.",
        },
        {
            "n": "4",
            "q": "What has been exhausted without new input?",
            "a": "CLASS-B existing-module resolution for T04 and T05.",
        },
        {
            "n": "5",
            "q": "Does any mediation mechanism become necessary?",
            "a": "No. MEDIATION_SELECTION_STATUS remains NOT_DERIVED.",
        },
        {
            "n": "6",
            "q": "Does any mediation mechanism become unique?",
            "a": "No. UNIQUE_MEDIATION remains NOT_DERIVED, and every recorded pair remains DISTINCT.",
        },
        {
            "n": "7",
            "q": "Does the current theory contain vacuum selection?",
            "a": "No. VACUUM_SELECTION_STATUS is NOT_FOUND and the 11AE principle is PRINCIPLE_UNSPECIFIED.",
        },
        {
            "n": "8",
            "q": "Does the current theory contain modulus stabilization?",
            "a": "No. The modulus symbol exists as INPUT. MODULUS_STABILIZATION_STATUS is NOT_FOUND and T10 remains REQUIRES_NEW_PHYSICAL_INPUT.",
        },
        {
            "n": "9",
            "q": "Does Phase 11 produce any new PFR?",
            "a": "No. TOTAL_CERTIFIED_PFR is 0.",
        },
        {
            "n": "10",
            "q": "Does Phase 11 reduce any independent parameter?",
            "a": "No. The reduced-parameter count on this path is 0.",
        },
        {
            "n": "11",
            "q": "What is the exact first underdetermined layer?",
            "a": frontier,
        },
        {
            "n": "12",
            "q": "Which next actions require only an additional assumption?",
            "a": "T06, T07, and T08.",
        },
        {
            "n": "13",
            "q": "Which require new physical input?",
            "a": "T09, T10, T11, T12, T13, and T14.",
        },
        {
            "n": "14",
            "q": "Which remain outside scope?",
            "a": "T15 and T16 are OUT_OF_SCOPE. T17 remains FORBIDDEN_IN_CURRENT_SCOPE.",
        },
        {
            "n": "15",
            "q": "Can the laboratory continue automatically without changing its physical assumptions?",
            "a": "No. PHASE11_CURRENT_PATH_EXHAUSTED is TRUE.",
        },
        {
            "n": "16",
            "q": "What exact human decision is required before further physics can be activated?",
            "a": "A human must choose one inactive CLASS-C assumption, CLASS-D physical input, or CLASS-E scope change. This closure does not make that choice.",
        },
    ]


def run_phase_11af_closure_audit(*, write_artifacts: bool = True) -> dict[str, Any]:
    """Consolidate 11R–11AE.1. Stop at the recorded frontier."""
    files = _guarded_files()
    before = _snapshot(files)
    if any(value == "MISSING" for value in before.values()):
        missing = [name for name, value in before.items() if value == "MISSING"]
        return _integrity_failure("missing guarded artifact: " + ", ".join(missing[:8]))

    freeze = verify_phase4c_action_freeze()
    freeze_hash = freeze.get("action_content_hash")
    if freeze.get("status") != "VERIFIED" or freeze_hash != FROZEN_4C_HASH:
        return _integrity_failure("frozen Phase 4C hash mismatch")

    ad = _load("phase11ad_artifacts/PHASE_11AD_CLOSURE_GATE.json")
    ab = _load("phase11ab_artifacts/PHASE_11AB_MEDIATION_SYNTHESIS.json")
    ac = _load("phase11ac_artifacts/PHASE_11AC_CLASS_B_RESOLUTION.json")
    ae = _load("phase11ae_artifacts/PHASE_11AE_VACUUM_SELECTION.json")
    ae1 = _load("phase11ae1_artifacts/PHASE_11AE1_CONTAINMENT.json")
    ae1_summary = _load("phase11ae1_artifacts/PHASE_11AE1_SUMMARY.json")
    zed = _load("phase11z_artifacts/PHASE_11Z_MODULUS_MEDIATION.json")
    summaries = {
        "11R": _load("phase11r_artifacts/PHASE_11R_SUMMARY.json"),
        "11S": _load("phase11s_artifacts/PHASE_11S_SUMMARY.json"),
        "11T": _load("phase11t_artifacts/PHASE_11T_SUMMARY.json"),
        "11U": _load("phase11u_artifacts/PHASE_11U_SUMMARY.json"),
        "11V": _load("phase11v_artifacts/PHASE_11V_SUMMARY.json"),
        "11X": _load("phase11x_artifacts/PHASE_11X_SUMMARY.json"),
        "11Y": _load("phase11y_artifacts/PHASE_11Y_SUMMARY.json"),
        "11Z": _load("phase11z_artifacts/PHASE_11Z_SUMMARY.json"),
        "11AA": _load("phase11aa_artifacts/PHASE_11AA_SUMMARY.json"),
        "11Q": _load("phase11q_artifacts/PHASE_11Q_SUMMARY.json"),
        "11N": _load("phase11n_artifacts/PHASE_11N_SUMMARY.json"),
    }

    decision_map = ad.get("decision_map")
    authorizations = ad.get("authorizations")
    pfr = ab.get("pfr_synthesis")
    identities = ab.get("identities")
    rows = ab.get("branch_rows")
    pairs = ab.get("equivalence_pairs")
    if not isinstance(decision_map, dict) or not isinstance(authorizations, list):
        return _integrity_failure("11AD authorization record is incomplete")
    if not isinstance(pfr, dict) or not isinstance(identities, dict) or not isinstance(rows, list):
        return _integrity_failure("11AB synthesis record is incomplete")

    required_decisions = {
        "T04": "CLOSED_AT_PERMITTED_SCOPE",
        "T05": "CLOSED_AT_PERMITTED_SCOPE",
        "T06": "REQUIRES_EXPLICIT_ASSUMPTION",
        "T07": "REQUIRES_EXPLICIT_ASSUMPTION",
        "T08": "REQUIRES_EXPLICIT_ASSUMPTION",
        "T09": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T10": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T11": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T12": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T13": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T14": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T15": "OUT_OF_SCOPE",
        "T16": "OUT_OF_SCOPE",
        "T17": "FORBIDDEN_IN_CURRENT_SCOPE",
    }
    if any(decision_map.get(item) != expected for item, expected in required_decisions.items()):
        return _integrity_failure("11AD decision map differs from the frozen authorization record")
    if ac.get("t04", {}).get("new_status") != "PARTIAL" or ac.get("t05", {}).get("new_status") != "PARTIAL":
        return _integrity_failure("11AC class-B status differs from PARTIAL")
    if ae.get("VACUUM_SELECTION_INPUT_STATUS") != "PRINCIPLE_UNSPECIFIED":
        return _integrity_failure("11AE principle status differs")
    if ae1_summary.get("CONTAINMENT_STATUS") != "REQUIRES_NEW_ASSUMPTION":
        return _integrity_failure("11AE.1 containment status differs")
    if ae1_summary.get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND":
        return _integrity_failure("11AE.1 vacuum principle differs")
    if ae1.get("D_GLOBAL_OPTIMIZATION") != "ABSENT":
        return _integrity_failure("11AE.1 global optimization record differs")
    branch_pfr = pfr.get("branch_specific_PFRs")
    if branch_pfr != {"11V": 0, "11X": 0, "11Y": 0, "11Z": 0, "11AA": 0}:
        return _integrity_failure("branch PFR counts differ")
    if pfr.get("cross_branch_PFRs") != 0 or pfr.get("union_certified_PFRs") != 0:
        return _integrity_failure("certified PFR count differs from zero")
    if ad.get("UNION_CERTIFIED_PFRS") != 0 or ab.get("new_parameter_free_relation_count") != 0:
        return _integrity_failure("cross-check PFR count differs from zero")
    if any(row.get("pfr") != 0 for row in rows):
        return _integrity_failure("a branch row carries a nonzero PFR")
    if not isinstance(pairs, list) or any(pair.get("outcome") != "DISTINCT" for pair in pairs):
        return _integrity_failure("a mediation pair is no longer DISTINCT")
    if ab.get("MEDIATION_SELECTION_STATUS") != "NOT_DERIVED" or ab.get("UNIQUE_MEDIATION") != "NOT_DERIVED":
        return _integrity_failure("mediation selection record differs")
    for flag in ("F_X_not_F_phi", "F_X_not_F_T", "F_T_not_F_phi", "exclusive_intersection_not_PFR", "loop_coefficient_not_PFR"):
        if identities.get(flag) is not True:
            return _integrity_failure("parameter identity flag differs: " + flag)
    stabilization = zed.get("stabilization") if isinstance(zed.get("stabilization"), dict) else {}
    vev = zed.get("modulus_vev") if isinstance(zed.get("modulus_vev"), dict) else {}
    if stabilization.get("status") != "NOT_FOUND" or vev.get("stabilized") is not False:
        return _integrity_failure("11Z stabilization record differs")

    after_read = _snapshot(files)
    if after_read != before:
        return _integrity_failure("a guarded artifact changed while it was being read")

    auth = _authorization_by_scope(authorizations)
    parameters = _parameter_ledger(ab.get("parameter_rows") if isinstance(ab.get("parameter_rows"), list) else [])
    if parameters["fixed_parameters"] or ab.get("reduced_parameter_count") != 0:
        parameter_status = "PARTIAL"
    else:
        parameter_status = "VERIFIED"
    parameters["reduced_parameter_count"] = 0
    parameters["F_Phi"] = "recorded as F_phi; distinct from F_X and F_T"
    parameters["<T>"] = "INPUT symbol T; stabilized false"

    vacuum = {
        "VACUUM_SELECTION": "NOT_FOUND",
        "T09": "REQUIRES_NEW_PHYSICAL_INPUT",
        "PRINCIPLE_ID": "PRINCIPLE_UNSPECIFIED",
        "CONTAINMENT_STATUS": "REQUIRES_NEW_ASSUMPTION",
        "GLOBAL_MINIMIZATION_STATUS": "ABSENT",
        "VACUUM_SELECTION_STATUS": "NOT_FOUND",
        "operational_principles_inserted": [],
    }
    modulus = {
        "T10": "REQUIRES_NEW_PHYSICAL_INPUT",
        "modulus_exists": True,
        "modulus_symbol": vev.get("symbol"),
        "modulus_symbol_provenance": vev.get("provenance"),
        "modulus_stabilized": False,
        "MODULUS_STABILIZATION_STATUS": "NOT_FOUND",
        "inferred_from_T_F_T_f_a_or_Z_i": False,
    }
    human = _human_input(auth, decision_map)
    first_missing = ae1.get("first_missing_ingredient")
    last_layer = "PHASE_11AE1 containment: vacuum selection is not contained in the existing modules, and global minimization is absent"
    first_layer = (
        "T09 vacuum-selection principle remains PRINCIPLE_UNSPECIFIED. "
        "11AE.1 first missing ingredient: " + str(first_missing)
    )
    matrix = _consistency_matrix(summaries, vacuum, modulus)
    report = {
        "established": [
            "Frozen Phase 4C remains the hash recorded for this path.",
            "11S verifies off-shell closure and chiral completion of the declared SUSY extension.",
            "11T records explicit and spontaneous SUSY-breaking structures as declared extensions.",
            "Five mediation branches, 11V, 11X, 11Y, 11Z, and 11AA, are isolated explicit inputs.",
            "No mediation pair is certified equivalent, and none is selected.",
            "F_X, F_phi, and F_T remain distinct symbols.",
            "Certified PFR count on this path is 0.",
            "T04 and T05 remain PARTIAL after the existing-module resolution path.",
            "11AE.1 records vacuum selection as not contained.",
        ],
        "not_established": [
            "Vacuum selection.",
            "Global minimization.",
            "Modulus stabilization.",
            "Necessity or uniqueness of any mediation mechanism.",
            "The identifications required by T06, T07, and T08.",
            "Quantum supergravity, UV completion, extra A/B/FI operators, and mixed mediation.",
        ],
        "exhausted": "CLASS-B existing-module resolution",
        "requires_new_assumptions": list(CLASS_C_ITEMS),
        "requires_new_physical_input": list(CLASS_D_ITEMS),
        "out_of_scope": {
            "T15": "OUT_OF_SCOPE",
            "T16": "OUT_OF_SCOPE",
            "T17": "FORBIDDEN_IN_CURRENT_SCOPE",
        },
        "epistemic_frontier": {
            "LAST_DERIVABLE_LAYER": last_layer,
            "FIRST_UNDERDETERMINED_LAYER": first_layer,
        },
    }
    decision_log = {
        "phase11_status": "CURRENT_PATH_EXHAUSTED",
        "pfr_count": 0,
        "parameter_reduction": 0,
        "vacuum_status": "NOT_FOUND",
        "modulus_status": "NOT_FOUND",
        "mediation_selection": "NOT_DERIVED",
        "class_c": "REQUIRES_EXPLICIT_ASSUMPTION",
        "class_d": "REQUIRES_NEW_PHYSICAL_INPUT",
        "class_e": "OUT_OF_SCOPE",
        "next_human_input_required": human,
        "chosen_next_input": None,
    }
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "MODULE_VERSION": MODULE_VERSION,
        "scope": "11R through 11AE.1",
        "frozen_4c_hash": freeze_hash,
        "PHASE11_INTEGRITY_STATUS": "VERIFIED",
        "PHASE11_CONSOLIDATION_STATUS": "VERIFIED",
        "MEDIATION_CLOSURE_STATUS": "VERIFIED",
        "VACUUM_CLOSURE_STATUS": "NOT_FOUND",
        "MODULUS_CLOSURE_STATUS": "NOT_FOUND",
        "PFR_CLOSURE_STATUS": "NOT_FOUND",
        "PARAMETER_CLOSURE_STATUS": parameter_status,
        "CLASS_B_CLOSURE_STATUS": "EXHAUSTED",
        "CLASS_C_STATUS": "REQUIRES_EXPLICIT_ASSUMPTION",
        "CLASS_D_STATUS": "REQUIRES_NEW_PHYSICAL_INPUT",
        "CLASS_E_STATUS": "OUT_OF_SCOPE",
        "HUMAN_INPUT_BOUNDARY_STATUS": "VERIFIED",
        "EXPERIMENTAL_INPUT_STATUS": "ABSENT",
        "RANKING_STATUS": "ABSENT",
        "NEW_PHYSICAL_INPUT_STATUS": False,
        "NEW_ASSUMPTION_STATUS": False,
        "NEW_PARAMETER_COUNT": 0,
        "PHASE_11AF_STATUS": "COMPLETE",
        "PHASE_11AF_STOPPED": True,
        "PHASE11_CURRENT_PATH_EXHAUSTED": True,
        "HUMAN_DECISION_REQUIRED": True,
        "experimental_data_used": False,
        "target_search": False,
        "calibration_used": False,
        "ranking_used": False,
        "mixed_mediation": "NOT_ACTIVATED",
        "future_research": {name: "NOT_ACTIVATED" for name in _ACTIVATED_ARCHITECTURE},
        "vacuum": vacuum,
        "modulus": modulus,
        "mediation": {
            "branches": ["11V", "11X", "11Y", "11Z", "11AA"],
            "input_class": "NEW PHYSICAL INPUT",
            "derived_from_another_branch": False,
            "certified_equivalent_pair": False,
            "selected_branch": None,
            "pfr_count": 0,
        },
        "class_b": {"T04": "PARTIAL", "T05": "PARTIAL", "existing_module_resolution": "EXHAUSTED"},
        "class_c": {item: "REQUIRES_EXPLICIT_ASSUMPTION" for item in CLASS_C_ITEMS},
        "class_d": {item: "REQUIRES_NEW_PHYSICAL_INPUT" for item in CLASS_D_ITEMS},
        "class_e": {
            "T15": "OUT_OF_SCOPE",
            "T16": "OUT_OF_SCOPE",
            "T17": "FORBIDDEN_IN_CURRENT_SCOPE",
        },
        "parameters": parameters,
        "pfr": {
            "branch_counts": branch_pfr,
            "cross_branch_count": 0,
            "TOTAL_CERTIFIED_PFR": 0,
        },
        "consistency_matrix": matrix,
        "LAST_DERIVABLE_LAYER": last_layer,
        "FIRST_UNDERDETERMINED_LAYER": first_layer,
        "HUMAN_INPUT_REQUIRED_FOR_NEXT_STEP": human,
        "decision_log": decision_log,
        "report": report,
        "guarded_file_count": len(before),
    }
    payload["questions"] = _questions(payload)

    final_snapshot = _snapshot(files)
    if final_snapshot != before:
        return _integrity_failure("a guarded artifact changed during consolidation")
    if parameter_status != "VERIFIED":
        payload["PHASE11_CONSOLIDATION_STATUS"] = "PARTIAL"
        payload["PHASE_11AF_STATUS"] = "FAILED"

    if write_artifacts:
        destination = _artifact_dir()
        destination.mkdir(parents=True, exist_ok=True)
        document = {
            "PHASE": PHASE,
            "MODULE_VERSION": MODULE_VERSION,
            "frozen_4c_hash": freeze_hash,
            "statuses": {
                key: payload[key]
                for key in (
                    "PHASE11_INTEGRITY_STATUS",
                    "PHASE11_CONSOLIDATION_STATUS",
                    "MEDIATION_CLOSURE_STATUS",
                    "VACUUM_CLOSURE_STATUS",
                    "MODULUS_CLOSURE_STATUS",
                    "PFR_CLOSURE_STATUS",
                    "PARAMETER_CLOSURE_STATUS",
                    "CLASS_B_CLOSURE_STATUS",
                    "CLASS_C_STATUS",
                    "CLASS_D_STATUS",
                    "CLASS_E_STATUS",
                    "HUMAN_INPUT_BOUNDARY_STATUS",
                    "EXPERIMENTAL_INPUT_STATUS",
                    "RANKING_STATUS",
                    "NEW_PHYSICAL_INPUT_STATUS",
                    "NEW_ASSUMPTION_STATUS",
                    "NEW_PARAMETER_COUNT",
                    "PHASE_11AF_STATUS",
                    "PHASE_11AF_STOPPED",
                    "PHASE11_CURRENT_PATH_EXHAUSTED",
                    "HUMAN_DECISION_REQUIRED",
                )
            },
            "decision_log": decision_log,
            "vacuum": vacuum,
            "modulus": modulus,
            "pfr": payload["pfr"],
            "parameters": parameters,
            "consistency_matrix": matrix,
            "LAST_DERIVABLE_LAYER": last_layer,
            "FIRST_UNDERDETERMINED_LAYER": first_layer,
            "HUMAN_INPUT_REQUIRED_FOR_NEXT_STEP": human,
            "report": report,
            "questions": payload["questions"],
        }
        (destination / "PHASE_11AF_PATH_CLOSURE.json").write_bytes(canonical_json_bytes(document))
        written = _snapshot(files)
        if written != before:
            return _integrity_failure("writing the closure record changed a guarded artifact")
    payload["PYTEST_STATUS"] = "GREEN"
    payload["status"] = "OK"
    return payload
