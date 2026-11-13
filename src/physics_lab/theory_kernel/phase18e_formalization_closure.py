"""Phase 18E classifies missing formal information and does not close it."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase18c_authorization_design import UNRESOLVED

PHASE = "PHASE_18E"
CODE_VERSION = "phase18e-formalization-closure-v1"
SCHEMA_VERSION = "formalization_closure_audit_18e_v1"
ARTIFACT_DIR_NAME = "phase18e_formalization_closure_artifacts"
AUDIT_NAME = "PHASE_18E_FORMALIZATION_CLOSURE_AUDIT.json"
AUDIT_TIMESTAMP = "2026-10-26T13:01:00Z"
CLOSURE_CLASSES = (
    "DERIVED_STRUCTURE",
    "NEUTRAL_MATHEMATICAL_DEFINITION",
    "THEORY_SELECTION_REQUIRED",
    "NEW_PHYSICAL_INPUT_REQUIRED",
    "UNDECIDED",
)
NEUTRAL_RECORDS = {
    "boundary_conditions",
    "boundary_data",
    "configuration_set",
    "configuration_space",
    "coupling_coordinates",
    "coupling_space",
    "dynamical_domain",
    "evolution_index",
    "fields",
    "flow_parameter",
    "functional_variation",
    "initial_conditions",
    "initial_or_final_conditions",
    "phase_space",
    "state_or_configuration_space",
    "sum_or_measure",
    "symbolic_coefficients",
}
SEALED = {
    "phase17a": "60adceeff480b9e688f9f2f4c12c05aeede96210da0c9d2354cf8d028075c529",
    "phase17b": "0b5d211cd94e509c8f285a1c680abd151d40cf4ddf950ebc77a4c86f084ade58",
    "phase17b1": "24f3dc952b8e415570952d84b87623b86ca6ad623e3179d993a352570daef28b",
    "phase17c": "2302ab4d0f3960c8107cd4f0b4b6982d77822ec7eed37e3c30c2b99cd760e0cf",
    "phase17d": "1230f968adfb4de7e030821ea644648954c6e15f4feea3fbf1362cd5ca4fed2f",
    "phase17e": "37cccb3ba8fbfd3f99739faeac77411ca88d122856d3eb5f9370d3a08d16ef7a",
    "phase18a_file": "108a3be2d1a57f036ce47b190cf0441f3ad119dc8416a4413a0a79d603ca7d43",
    "phase18a_audit_hash": "e5d2310b3d5b57c1aafe86a3e5f14611ea2a8affa4dbc6a83f7674ccf71a8076",
    "phase18b_file": "f6264e49dc0d7c20562833b26891b67ff556477669f308fb646c919632235d84",
    "phase18b_proposal_hash": "e3031ab3f89acadc60e09cb9045590d78cde4a6f71e0de2cb3bbee5c3e399e89",
    "phase18c_file": "21100e7f920f85070dffba6b10cb12488160481f6e5d70c7464d3815bcf182e2",
    "phase18c_proposal_hash": "ad6e71b76e4016be842c5ce517c6546741c96c5703aef9fc89479d2d801144b7",
    "phase18d_file": "6dae892e4fa27d98765194098a3b0b5b631adc8b53c4f12ef9ae93c317c5e581",
    "phase18d_audit_hash": "5d12cfa2381a27b1b6b365b4fe175b05b548d2262f96550bc8ce180410b21fce",
    "v23_docx": "cd587b4fd90259f264392ccfb1bcdbb013a4c38076bf401f646a07e8b92cc5b0",
}
EXPECTED_IDS = (
    "g17b1.riemann_cartan__constrained_action__1",
    "g17b1.metric_affine__constrained_action__1",
    "g17b1.higher_derivative_qft__constrained_action__1",
    "g17b1.causal_set__discrete_dynamical_rule__0",
    "g17b1.discrete_complex__discrete_dynamical_rule__0",
    "g17b1.causal_triangulation__discrete_dynamical_rule__0",
    "g17b1.spin_network__discrete_dynamical_rule__1",
    "g17b1.conformal__hamiltonian_or_canonical_formulation__1",
    "g17b1.metric_affine__hamiltonian_or_canonical_formulation__2",
    "g17b1.higher_dimensional__hamiltonian_or_canonical_formulation__1",
    "g17b1.warped_product__hamiltonian_or_canonical_formulation__1",
    "g17b1.internal_manifold__hamiltonian_or_canonical_formulation__1",
    "g17b1.worldsheet__hamiltonian_or_canonical_formulation__1",
    "g17b1.worldvolume__hamiltonian_or_canonical_formulation__1",
    "g17b1.conformal__local_action_functional__0",
    "g17b1.weyl__local_action_functional__0",
    "g17b1.riemann_cartan__local_action_functional__0",
    "g17b1.affine__local_action_functional__1",
    "g17b1.metric_affine__local_action_functional__0",
    "g17b1.characteristic_class__local_action_functional__0",
    "g17b1.higher_dimensional__local_action_functional__0",
    "g17b1.warped_product__local_action_functional__0",
    "g17b1.internal_manifold__local_action_functional__0",
    "g17b1.finsler__local_action_functional__0",
    "g17b1.pseudo_finsler__local_action_functional__0",
    "g17b1.group_field__local_action_functional__0",
    "g17b1.worldsheet__local_action_functional__0",
    "g17b1.worldvolume__local_action_functional__0",
    "g17b1.higher_derivative_qft__local_action_functional__0",
    "g17b1.spin_structure__not_yet_specifiable__0",
    "g17b1.vector_bundle__not_yet_specifiable__0",
    "g17b1.holonomy__not_yet_specifiable__0",
    "g17b1.finite_algebra__not_yet_specifiable__0",
    "g17b1.weyl__other_formal_dynamics__1",
    "g17b1.projective__other_formal_dynamics__0",
    "g17b1.affine__other_formal_dynamics__0",
    "g17b1.finsler__other_formal_dynamics__1",
    "g17b1.pseudo_finsler__other_formal_dynamics__1",
    "g17b1.tensor_model__other_formal_dynamics__1",
    "g17b1.rg_flow__renormalization_flow__0",
    "g17b1.causal_set__state_sum_or_transition_amplitude__1",
    "g17b1.discrete_complex__state_sum_or_transition_amplitude__1",
    "g17b1.causal_triangulation__state_sum_or_transition_amplitude__1",
    "g17b1.spin_network__state_sum_or_transition_amplitude__0",
    "g17b1.spin_foam__state_sum_or_transition_amplitude__0",
    "g17b1.tensor_model__state_sum_or_transition_amplitude__0",
    "g17b1.group_field__state_sum_or_transition_amplitude__1",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stop(reason: str) -> dict[str, Any]:
    return {
        "PHASE18E_STATUS": "INCOMPLETE",
        "SEARCH_STATUS": "NOT_STARTED",
        "SEARCH_ACTIVE": False,
        "status": "AUDIT_FAILED",
        "reason": reason,
    }


def execute_search(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def select_theory(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def select_action(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def select_vacuum(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def introduce_bound(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _phrases(record: dict[str, Any]) -> list[str]:
    return [item["item"] for item in record["DATA_MISSING"] if "blocks_formal_definition" in item]


def _object(
    name: str,
    classification: str,
    *,
    blocks: bool,
    tests: dict[str, str],
    rationale: str,
    necessity: str,
) -> dict[str, Any]:
    return {
        "blocks_closure": blocks,
        "classification": classification,
        "necessity": necessity,
        "object": name,
        "rationale": rationale,
        "tests": tests,
    }


def _neutral(name: str, necessity: str) -> dict[str, Any]:
    return _object(
        name,
        "NEUTRAL_MATHEMATICAL_DEFINITION",
        blocks=necessity in {"ABSENT", "UNREGISTERED"},
        necessity=necessity,
        rationale="Test D1 fails. Test D2 holds for the mathematical setting of the registered class. The setting does not identify the dynamical law, and this audit does not write it.",
        tests={"D1": "FAIL", "D2": "PASS", "D3": "NOT_REACHED", "D4": "NOT_REACHED", "D5": "NOT_REACHED"},
    )


def _undecided(name: str, necessity: str, blocks: bool) -> dict[str, Any]:
    return _object(
        name,
        "UNDECIDED",
        blocks=blocks,
        necessity=necessity,
        rationale="Test D1 fails because the registered record does not derive the object. Test D2 fails because a placeholder would not identify it. Test D3 is not proved inside this formulation. Test D4 is not established by the inherited structural flag. Test D5 leaves the origin undecided.",
        tests={"D1": "FAIL", "D2": "FAIL", "D3": "NOT_PROVED", "D4": "NOT_ESTABLISHED", "D5": "UNDECIDED"},
    )


def _theory(name: str, necessity: str, rationale: str) -> dict[str, Any]:
    return _object(
        name,
        "THEORY_SELECTION_REQUIRED",
        blocks=True,
        necessity=necessity,
        rationale=rationale,
        tests={"D1": "FAIL", "D2": "FAIL", "D3": "PASS", "D4": "NOT_REACHED", "D5": "NOT_REACHED"},
    )


def _phrase_object(phrase: str) -> dict[str, Any]:
    if phrase == "fixed point is not chosen":
        return _object(
            phrase,
            "NOT_A_CLOSURE_BLOCKER",
            blocks=False,
            necessity="DOWNSTREAM_ONLY",
            rationale="Phase 18D records this phrase as downstream of the formal flow definition. No fixed point is selected.",
            tests={"D1": "NOT_APPLIED", "D2": "NOT_APPLIED", "D3": "NOT_APPLIED", "D4": "NOT_APPLIED", "D5": "NOT_APPLIED"},
        )
    if phrase.startswith("which "):
        return _theory(
            phrase,
            "ABSENT",
            "The registered missing phrase states an unresolved selection. A placeholder would not identify the object, and choosing one reading would change the formulation. No selection is performed.",
        )
    if phrase == "multiplication presentation":
        return _theory(
            phrase,
            "ABSENT",
            "An abstract unsigned description does not identify a multiplication. A concrete table would select an algebra. No algebra is selected.",
        )
    if "not chosen" in phrase:
        return _neutral(phrase, "ABSENT")
    if "coefficient" in phrase:
        return _neutral(phrase, "ABSENT")
    if phrase in {"derivative order", "invariant measure"} or "order" in phrase:
        return _undecided(phrase, "ABSENT", True)
    return _undecided(phrase, "ABSENT", True)


def _row_object(row: dict[str, str], phrases: list[str], parent_id: str) -> dict[str, Any]:
    name = row["record"]
    necessity = row["status"]
    if row.get("information_class") == "DOWNSTREAM_ONLY" or necessity in {"NOT_APPLICABLE", "NOT_REQUIRED"}:
        return _object(
            name,
            "NOT_A_CLOSURE_BLOCKER",
            blocks=False,
            necessity=necessity,
            rationale="Phase 18D does not treat this record as a missing closure object.",
            tests={"D1": "NOT_APPLIED", "D2": "NOT_APPLIED", "D3": "NOT_APPLIED", "D4": "NOT_APPLIED", "D5": "NOT_APPLIED"},
        )
    if name == "multiplication_presentation" and parent_id == "g17b1.finite_algebra":
        return _theory(name, necessity, "An abstract unsigned description does not identify a multiplication. A concrete table would select an algebra. No algebra is selected.")
    if name == "constraint_structure" and any(item.startswith("which structural relations") for item in phrases):
        return _theory(name, necessity, "The registered phrase states that the dynamical constraints are an unresolved selection. No constraint is chosen.")
    if name == "topological_sector" and any(item.startswith("which characteristic class") for item in phrases):
        return _theory(name, necessity, "The registered phrase states that the class entering the functional is an unresolved selection. No class is chosen.")
    if necessity == "NOT_DECIDED":
        return _undecided(name, necessity, False)
    if name in NEUTRAL_RECORDS:
        return _neutral(name, necessity)
    if name == "derivative_order":
        return _undecided(name, necessity, True)
    return _undecided(name, necessity, necessity in {"ABSENT", "UNREGISTERED"})


def _closure(objects: list[dict[str, Any]]) -> str:
    labels = {item["classification"] for item in objects if item["blocks_closure"]}
    if "THEORY_SELECTION_REQUIRED" in labels:
        return "THEORY_SELECTION_REQUIRED"
    if "NEW_PHYSICAL_INPUT_REQUIRED" in labels:
        return "NEW_PHYSICAL_INPUT_REQUIRED"
    if "UNDECIDED" in labels:
        return "UNDECIDED"
    if labels == {"NEUTRAL_MATHEMATICAL_DEFINITION"}:
        return "NEUTRAL_MATHEMATICAL_DEFINITION"
    if labels == {"DERIVED_STRUCTURE"}:
        return "DERIVED_STRUCTURE"
    return ""


def _audit_one(record: dict[str, Any]) -> dict[str, Any]:
    phrases = _phrases(record)
    objects = [_row_object(row, phrases, record["PARENT_STRUCTURE_ID"]) for row in record["MINIMUM_MATHEMATICAL_DATA"]]
    objects.extend(_phrase_object(phrase) for phrase in phrases)
    closure = _closure(objects)
    status = record["FORMALIZATION_STATUS"]
    kind = record["DYNAMICAL_CLASS"]
    class_resolved = kind not in {"OTHER_FORMAL_DYNAMICS", "NOT_YET_SPECIFIABLE"}
    nonunique = record["DYNAMICAL_NONUNIQUENESS"]["parent_claim"] == "DYNAMICAL_NONUNIQUENESS"
    labels = {item["classification"] for item in objects}
    if closure == "THEORY_SELECTION_REQUIRED":
        rationale = "At least one missing object is an unresolved selection already stated by the Phase 18D record. No selection is performed. Other missing objects may remain undecided."
        step = "A later authorization would have to record an explicit selection, or a registered proof that the selection is forced. This phase does neither."
    else:
        rationale = "The dynamical law is not derived, a neutral setting does not identify it, multiplicity inside this formulation is not proved, and a new physical input is not established."
        step = "A later phase would need a registered derivation or an explicit decision about the unidentified law. This phase supplies neither."
    return {
        "formulation_id": record["FORMULATION_ID"],
        "parent_grammar": record["PARENT_STRUCTURE_ID"],
        "dynamical_class": kind,
        "current_formalization_status": status,
        "required_objects": [row["record"] for row in record["MINIMUM_MATHEMATICAL_DATA"]],
        "missing_objects": [item["object"] for item in objects if item["blocks_closure"]],
        "object_classification": objects,
        "closure_classification": closure,
        "derived_structure": "DERIVED_STRUCTURE" in labels,
        "neutral_mathematical_definition": "NEUTRAL_MATHEMATICAL_DEFINITION" in labels,
        "theory_selection_required": "THEORY_SELECTION_REQUIRED" in labels,
        "new_physical_input_required": False,
        "undecided": "UNDECIDED" in labels,
        "dynamical_nonuniqueness": {
            "collapsed": False,
            "registered_parent_claim": record["DYNAMICAL_NONUNIQUENESS"]["parent_claim"],
            "registered_plan_multiplicity": nonunique,
            "within_formulation_multiplicity": "NOT_PROVED",
        },
        "dynamical_class_resolved": class_resolved,
        "ready_for_finite_bounding": False,
        "reason_not_ready": "The formulation is not formally closed. Readiness for a later bound is not an impossibility claim and is not an authorization.",
        "next_allowed_phase": "NOT_ACTIVATED",
        "PHYSICAL_INPUT_REQUIREMENT": "NOT_DECIDED",
        "RATIONALE": rationale,
        "THEORY_SELECTION_REQUIRED": closure == "THEORY_SELECTION_REQUIRED",
        "NEW_PHYSICAL_INPUT_REQUIRED": False,
        "UNDECIDED_FLAG": "UNDECIDED" in labels,
        "NEXT_FORMALIZATION_STEP": step,
        "SEARCH_ELIGIBILITY": "NOT_ELIGIBLE",
        "FORMALIZATION_STATUS_CURRENT": status,
        "computational_limit_is_not_a_mathematical_claim": True,
        "copied_from_phase17c": False,
        "algebra_selected": False,
        "reclassified": False,
    }


def _integrity(physics: Path) -> dict[str, Any]:
    paths = {
        "phase17a": physics / "phase17a_geometry_audit_artifacts" / "PHASE_17A_GEOMETRY_CATALOG.json",
        "phase17b": physics / "phase17b_geometry_formalization_artifacts" / "PHASE_17B_GEOMETRY_GRAMMARS.json",
        "phase17b1": physics / "phase17b1_fundamental_structure_artifacts" / "PHASE_17B1_FUNDAMENTAL_STRUCTURE.json",
        "phase17c": physics / "phase17c_bound_architecture_artifacts" / "PHASE_17C_BOUND_ARCHITECTURE.json",
        "phase17d": physics / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json",
        "phase17e": physics / "phase17e_frontier_artifacts" / "PHASE_17E_FRONTIER.json",
        "phase18a": physics / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json",
        "phase18b": physics / "phase18b_batch_proposal_artifacts" / "PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json",
        "phase18c": physics / "phase18c_authorization_artifacts" / "PHASE_18C_DYNAMICAL_BATCH_AUTHORIZATION_DESIGN.json",
        "phase18d": physics / "phase18d_formalization_artifacts" / "PHASE_18D_CLASS_SPECIFIC_FORMALIZATION_AUDIT.json",
    }
    root = _repo_root()
    history = root / "docs" / "history"
    v22 = history / "20Ottobre2026" / "rapporto_laboratorio_struttura_interna_FINAL_v22_TOPDOWN_QFT_CUMULATIVE.docx"
    v23_docx = history / "26Ottobre2026" / "rapporto_laboratorio_struttura_interna_FINAL_v23_TOPDOWN_QFT_CUMULATIVE.docx"
    v23_pdf = history / "26Ottobre2026" / "rapporto_laboratorio_struttura_interna_FINAL_v23_TOPDOWN_QFT_CUMULATIVE.pdf"
    v23_validation = history / "26Ottobre2026" / "REPORT_V23_VALIDATION.json"
    recorded: dict[str, Any] = {}
    for key, path in paths.items():
        if not path.is_file():
            recorded[key] = {"status": "UNVERIFIED", "reason": "file absent"}
            continue
        digest = _sha(path)
        expected = SEALED[{"phase18a": "phase18a_file", "phase18b": "phase18b_file", "phase18c": "phase18c_file", "phase18d": "phase18d_file"}.get(key, key)]
        recorded[key] = {"sha256": digest, "status": "VERIFIED" if digest == expected else "UNVERIFIED"}
    if v23_docx.is_file() and _sha(v23_docx) == SEALED["v23_docx"]:
        recorded["v23_docx"] = {"sha256": SEALED["v23_docx"], "status": "VERIFIED", "rewritten": False}
    else:
        recorded["v23_docx"] = {"status": "UNVERIFIED", "rewritten": False}
    validation = json.loads(v23_validation.read_text(encoding="utf-8")) if v23_validation.is_file() else {}
    recorded["v23_pdf"] = {
        "file_sha256": _sha(v23_pdf) if v23_pdf.is_file() else "ABSENT",
        "recorded_sha256": validation.get("REPORT_V23_PDF_SHA256", "ABSENT"),
        "status": "UNVERIFIED",
        "correction": "NOT_PERFORMED",
    }
    v22_digest = _sha(v22) if v22.is_file() else "ABSENT"
    recorded["v22_cross_check_inside_v23_validation"] = {
        "file_sha256": v22_digest,
        "recorded_sha256": validation.get("REPORT_V22_SHA256", "ABSENT"),
        "status": "UNVERIFIED",
        "correction": "NOT_PERFORMED",
    }
    recorded["v23_role"] = "DOCUMENTARY_REFERENCE_NOT_REWRITTEN"
    return recorded


def run_phase_18e(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    physics = _physics_dir()
    design_path = physics / "phase18d_formalization_artifacts" / "PHASE_18D_CLASS_SPECIFIC_FORMALIZATION_AUDIT.json"
    prior_paths = [
        physics / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json",
        physics / "phase18b_batch_proposal_artifacts" / "PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json",
        physics / "phase18c_authorization_artifacts" / "PHASE_18C_DYNAMICAL_BATCH_AUTHORIZATION_DESIGN.json",
        design_path,
    ]
    prior_bytes = [path.read_bytes() for path in prior_paths]
    design = json.loads(prior_bytes[-1])
    integrity = _integrity(physics)
    records = design.get("formulation_records", [])
    identifiers = [item["FORMULATION_ID"] for item in records]
    if (
        any(item["status"] != "VERIFIED" for key, item in integrity.items() if key.startswith("phase"))
        or design.get("audit_hash") != SEALED["phase18d_audit_hash"]
        or design.get("classification_counts") != {
            "FORMALIZATION_COMPLETE": 0,
            "FORMALIZATION_PARTIAL": 34,
            "FORMALIZATION_UNRESOLVED": 9,
            "NOT_YET_SPECIFIABLE": 4,
        }
        or set(identifiers) != set(EXPECTED_IDS)
        or len(identifiers) != 47
        or execute_search() != "NOT_PERFORMED"
        or select_theory() != "NOT_PERFORMED"
        or select_vacuum() != "NOT_PERFORMED"
        or introduce_bound() != "NOT_PERFORMED"
    ):
        return _stop("sealed input mismatch")
    audited = [_audit_one(record) for record in records]
    if any(item["closure_classification"] not in CLOSURE_CLASSES for item in audited):
        return _stop("closure classification")
    if any(item["current_formalization_status"] == "FORMALIZATION_COMPLETE" or item["ready_for_finite_bounding"] for item in audited):
        return _stop("closure leak")
    if any(item["dynamical_class"] == "OTHER_FORMAL_DYNAMICS" and item["dynamical_class_resolved"] for item in audited):
        return _stop("other class rewritten")
    finite = next(item for item in audited if item["formulation_id"] == "g17b1.finite_algebra__not_yet_specifiable__0")
    if finite["algebra_selected"] or finite["closure_classification"] != "THEORY_SELECTION_REQUIRED":
        return _stop("finite algebra")
    counts = {name: 0 for name in CLOSURE_CLASSES}
    status_counts = {"FORMALIZATION_COMPLETE": 0, "FORMALIZATION_PARTIAL": 0, "FORMALIZATION_UNRESOLVED": 0, "NOT_YET_SPECIFIABLE": 0}
    for item in audited:
        counts[item["closure_classification"]] += 1
        status_counts[item["current_formalization_status"]] += 1
    if sum(counts.values()) != 47 or sum(status_counts.values()) != 47:
        return _stop("count reconciliation")
    if counts["DERIVED_STRUCTURE"] != 0 or counts["NEW_PHYSICAL_INPUT_REQUIRED"] != 0 or counts["NEUTRAL_MATHEMATICAL_DEFINITION"] != 0:
        return _stop("unexpected closure partition")
    payload: dict[str, Any] = {
        "phase": PHASE,
        "status": "COMPLETE",
        "PHASE18E_STATUS": "COMPLETE",
        "CODE_VERSION": CODE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "timestamp": AUDIT_TIMESTAMP,
        "parent_phase18a_hash": SEALED["phase18a_audit_hash"],
        "parent_phase18b_hash": SEALED["phase18b_proposal_hash"],
        "parent_phase18c_hash": SEALED["phase18c_proposal_hash"],
        "parent_phase18d_hash": SEALED["phase18d_audit_hash"],
        "formulations_total": 47,
        "formulations_complete": status_counts["FORMALIZATION_COMPLETE"],
        "formulations_partial": status_counts["FORMALIZATION_PARTIAL"],
        "formulations_unresolved": status_counts["FORMALIZATION_UNRESOLVED"],
        "formulations_not_yet_specifiable": status_counts["NOT_YET_SPECIFIABLE"],
        "derived_structure_count": counts["DERIVED_STRUCTURE"],
        "neutral_definition_count": counts["NEUTRAL_MATHEMATICAL_DEFINITION"],
        "theory_selection_required_count": counts["THEORY_SELECTION_REQUIRED"],
        "new_physical_input_required_count": counts["NEW_PHYSICAL_INPUT_REQUIRED"],
        "undecided_count": counts["UNDECIDED"],
        "count_meaning": "The five origin counts partition formulations by closure_classification. Neutral setting objects can occur inside a formulation whose closure remains UNDECIDED.",
        "ready_for_finite_bounding_count": 0,
        "bound_derived": 0,
        "bound_proposed": 0,
        "bound_authorized": 0,
        "BOUND_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
        "search_status": "NOT_STARTED",
        "search_active": False,
        "dynamical_pfr_status": "NOT_TESTED",
        "parameter_closure_status": "NOT_TESTED",
        "action_selected": False,
        "theory_selected": False,
        "vacuum_selected": False,
        "VACUUM_SELECTION": "NOT_INSERTED",
        "new_physical_input_activated": False,
        "numerical_bounds_introduced": False,
        "per_formulation_audit": audited,
        "historical_integrity": integrity,
        "firewall_status": {
            "bound_copy_from_phase17c": False,
            "empirical_comparison": "NOT_PERFORMED",
            "equivalence_transfer": "NOT_PERFORMED",
            "reference_names_supply_dynamics": False,
            "search": "NOT_PERFORMED",
            "unresolved_equivalence_ids": list(UNRESOLVED),
            "vacuum": "NOT_INSERTED",
        },
        "validation_status": "INTERNAL_CHECKS_PASSED",
        "equivalence_resolved_count": 0,
        "models_generated": 0,
        "selected_formulation": "NONE",
        "NEXT_ALLOWED_PHASE": "NOT_ACTIVATED",
        "conclusion": "The audit classifies the origin of the missing mathematical information for each registered formulation. It does not decide which dynamics is viable, which theory is physical, which parameter or vacuum is selected, or whether a parameter-free relation exists.",
    }
    payload["audit_hash"] = content_digest({key: value for key, value in payload.items() if key != "audit_hash"})
    if write_artifacts:
        destination = physics / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / AUDIT_NAME).write_bytes(canonical_json_bytes(payload))
        if _unchanged(snapshot_existing_phases()) != before or [path.read_bytes() for path in prior_paths] != prior_bytes:
            return _stop("historical artifact changed")
    payload["status_flag"] = "OK"
    payload["HISTORICAL_ARTIFACTS_MODIFIED"] = False
    return payload
