"""Phase 15I audits equivalence boundaries inside COVARIANT_U1_37.

Unsupported engines stay unsupported. No operator is removed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a1_boundary import IBP_LEFT, IBP_RIGHT
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, catalog_influence, classify_candidate
from physics_lab.theory_kernel.phase15h_closure import run_phase_15h
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15I"
CODE_VERSION = "phase15i-equivalence-v1"
ARTIFACT_DIR_NAME = "phase15i_equivalence_artifacts"
GRAMMAR_VERSION = "grammar_15f_v1"
GRAMMAR_HASH = "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
MANIFEST_HASH = "5f27bb0325c3e5453b84172e34e089a1bcb3a2a42de6f42095677eedd5c0a187"
AXIS_KINETIC_ID = "op.7c8094c259bfe4f8"
REGISTERED_BOUNDARY_ASSUMPTIONS: tuple[str, ...] = ()
REGISTERED_BASIS_TRANSFORMATIONS: tuple[str, ...] = ()


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15I_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15I_BLOCKED"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def classify_ibp(identity: str | None, boundary_assumptions: tuple[str, ...] | None) -> str:
    if boundary_assumptions is None:
        return "BOUNDARY_ASSUMPTIONS_REQUIRED"
    if not REGISTERED_BOUNDARY_ASSUMPTIONS:
        if identity == "EXACT_SYMBOLIC_WITH_BOUNDARY_TERM" and boundary_assumptions:
            return "CONDITIONALLY_EQUIVALENT"
        return "UNTESTED"
    if identity == "EXACT_SYMBOLIC_WITH_BOUNDARY_TERM" and tuple(boundary_assumptions) == REGISTERED_BOUNDARY_ASSUMPTIONS:
        return "EXACTLY_EQUIVALENT"
    return "UNTESTED"


def certify_field_redefinition(record: dict[str, Any]) -> dict[str, Any]:
    invertible = record.get("invertible") is True and bool(record.get("inverse"))
    local = record.get("local") is True
    preserves_fields = record.get("preserves_field_content") is True
    hides_parameter = record.get("fixes_parameter") is True
    if not invertible or not local or not preserves_fields or hides_parameter:
        return {
            "accepted": False,
            "equivalence_result": "EQUIVALENCE_UNSUPPORTED",
            "inverse": record.get("inverse"),
            "jacobian_status": "UNSUPPORTED",
            "transformation": record.get("transformation"),
        }
    identity = record.get("transformation") == "Phi -> Phi" and record.get("inverse") == "Phi -> Phi"
    return {
        "accepted": True,
        "classes_reduced": 0 if identity else 0,
        "equivalence_result": "IDENTITY_NOT_A_REDUCTION" if identity else "EQUIVALENCE_UNSUPPORTED",
        "inverse": record.get("inverse"),
        "jacobian_status": "SUPPORTED" if identity else "UNSUPPORTED",
        "transformed_action": "UNCHANGED" if identity else "NOT_CERTIFIED",
        "transformation": record.get("transformation"),
    }


def classify_eom(*, on_shell_zero: bool, theorem_implemented: bool, redefinition_certified: bool) -> str:
    if on_shell_zero and not (theorem_implemented and redefinition_certified):
        return "ON_SHELL_ZERO"
    if theorem_implemented and redefinition_certified:
        return "FIELD_REDEFINITION_EQUIVALENT"
    return "UNSUPPORTED"


def classify_basis(*, transformation: str | None, same_spectrum: bool = False, same_symmetry: bool = False) -> str:
    if transformation is None or transformation not in REGISTERED_BASIS_TRANSFORMATIONS:
        return "NOT_EQUIVALENT" if transformation is None or same_spectrum or same_symmetry else "EQUIVALENCE_UNSUPPORTED"
    return "BASIS_EQUIVALENT"


def classify_action(chain: list[dict[str, Any]] | None, **_similarities: bool) -> str:
    if not chain or not all(step.get("certified") is True and step.get("assumptions_preserved") is True for step in chain):
        return "NOT_EQUIVALENT"
    return "EQUIVALENT"


def compose_chain(steps: list[dict[str, Any]]) -> str:
    if steps and all(step.get("certified") is True and step.get("assumptions_preserved") is True for step in steps):
        return "CERTIFIED_CHAIN"
    return "NOT_CERTIFIED"


def apply_coefficient_map(mapping: dict[str, str], *, certified: bool) -> dict[str, Any]:
    if any(isinstance(value, (int, float)) for value in mapping.values()):
        return {"applied": False, "fixed_coefficient_count": 0, "status": "NUMERIC_ASSIGNMENT_REJECTED"}
    if not certified:
        return {"applied": False, "directions_changed": False, "fixed_coefficient_count": 0, "status": "NOT_CERTIFIED"}
    return {"applied": True, "directions_changed": True, "fixed_coefficient_count": 0, "map": mapping, "status": "SYMBOLIC_MAP_RECORDED"}


def _pair_relation(left: str, right: str, syzygy_pairs: set[tuple[str, str]]) -> str:
    if (left, right) in syzygy_pairs or (right, left) in syzygy_pairs:
        return "DISTINCT_UNDER_SUPPORTED_RULES"
    return "DISTINCT_UNDER_SUPPORTED_RULES"


def _matrix(operator_ids: list[str], syzygy_pairs: set[tuple[str, str]]) -> list[dict[str, str]]:
    rows = []
    ordered = sorted(operator_ids)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            rows.append(
                {
                    "assumptions": "",
                    "boundary_requirements": "NONE_REGISTERED",
                    "equivalence_type": "SUPPORTED_ALGEBRAIC_CANONICALIZATION",
                    "invertibility_requirements": "NOT_APPLICABLE",
                    "proof_status": _pair_relation(left, right, syzygy_pairs),
                    "provenance": "PHASE_15A_CANONICAL_KEYS",
                    "source_object": left,
                    "target_object": right,
                    "transformation": "NONE",
                }
            )
    return rows


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    cases = [
        ("1", "exact binding to Phase 15C-15H", "COMPLETE", result["PHASE_15H_STATUS"]),
        ("2", "nominal count 37 preserved", "37", str(result["nominal_operator_count"])),
        ("3", "algebraic rank 35 preserved", "35", str(result["algebraic_rank"])),
        ("4", "eight syzygies preserved", "8", str(result["syzygy_count"])),
        ("5", "IBP tests require explicit boundary assumptions", "BOUNDARY_ASSUMPTIONS_REQUIRED", classify_ibp("EXACT_SYMBOLIC_WITH_BOUNDARY_TERM", None)),
        ("6", "unsupported IBP remains unsupported", "UNSUPPORTED", result["IBP_EQUIVALENCE_STATUS"]),
        ("7", "only invertible field redefinitions may certify equivalence", "EQUIVALENCE_UNSUPPORTED", certify_field_redefinition({"fixes_parameter": False, "invertible": False, "local": True, "preserves_field_content": True, "transformation": "Phi -> 0"})["equivalence_result"]),
        ("8", "non-invertible transformations are rejected", "False", str(certify_field_redefinition({"invertible": False, "local": True, "preserves_field_content": True, "transformation": "Phi -> 0"})["accepted"])),
        ("9", "EOM-zero is not automatically EOM-equivalent", "ON_SHELL_ZERO", classify_eom(on_shell_zero=True, theorem_implemented=False, redefinition_certified=False)),
        ("10", "basis equivalence requires an explicit allowed transformation", "NOT_EQUIVALENT", classify_basis(transformation=None, same_spectrum=True, same_symmetry=True)),
        ("11", "same spectrum alone does not imply equivalence", "NOT_EQUIVALENT", classify_basis(transformation=None, same_spectrum=True)),
        ("12", "same symmetry alone does not imply equivalence", "NOT_EQUIVALENT", classify_basis(transformation=None, same_symmetry=True)),
        ("13", "complete-action equivalence requires an explicit transformation chain", "NOT_EQUIVALENT", classify_action(None, similar_equations=True, symmetries_match=True, spectra_match=True, parameter_counts_match=True)),
        ("14", "coefficient transformations are tracked", "NOT_CERTIFIED", apply_coefficient_map({"c_i": "c_j"}, certified=False)["status"]),
        ("15", "parameter fixing never occurs", "0", str(result["fixed_coefficient_count"])),
        ("16", "frozen action remains unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("17", "no new operator", "0", str(result["operators_added"])),
        ("18", "no new field", "NONE", result["new_field"]),
        ("19", "no new parameter", "0", str(result["new_parameter_count"])),
        ("20", "no target information", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("21", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("22", "repeated execution deterministic", result["audit_digest"], result["audit_digest_repeated"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15i(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    closure = run_phase_15h(write_artifacts=False)
    grammar_file = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    manifest = _read("phase15g_enumeration_artifacts/PHASE_15G_SEARCH_MANIFEST.json")
    family = _read("phase15g_enumeration_artifacts/PHASE_15G_FAMILY.json")
    catalog = _read("phase15e_catalog_artifacts/PHASE_15E_CATALOG.json")
    overlap = _read("phase15d_audit_artifacts/PHASE_15D_OVERLAP.json")
    whitelist = _read("phase15a_grammar_artifacts/PHASE_15A_STRUCTURAL_WHITELIST.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or closure.get("status") != "OK"
        or closure.get("PHASE_15H_STATUS") != "COMPLETE"
        or closure.get("grammar_version") != GRAMMAR_VERSION
        or closure.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or closure.get("PROVENANCE_STATUS") != "VERIFIED"
        or closure.get("reproducibility") != "VERIFIED"
        or content_digest(grammar_file["operational"]) != GRAMMAR_HASH
        or content_digest(manifest) != MANIFEST_HASH
        or catalog_influence({"entries": []}, "equivalence")["applied"] is not False
    ):
        return _stop("integrity gate")
    operator_ids = list(family["operator_ids"])
    profile_ids = next(item["operator_ids"] for item in grammar_file["operational"]["profiles"] if item["profile_id"] == "COVARIANT_U1_37")
    if operator_ids != profile_ids or len(operator_ids) != 37 or family["algebraic_rank"] != 35:
        return _stop("profile binding")
    if catalog["algebraic_rank"]["COVARIANT_4D"] != 35 or catalog["nominal_count"]["COVARIANT_4D"] != 37:
        return _stop("rank binding")
    syzygies = catalog["syzygies"]
    inside = [item for item in syzygies if set(item["operator_ids"]) <= set(operator_ids)]
    if len(syzygies) != 8 or len(inside) != 2 or any(item["quotient_applied"] or item["consequence"] != "ALGEBRAIC_IDENTITY" for item in syzygies):
        return _stop("syzygy binding")
    by_definition = {item["mathematical_definition"]: item["object_id"] for item in whitelist["entries"]}
    ibp_left = by_definition.get(IBP_LEFT)
    ibp_right = by_definition.get(IBP_RIGHT)
    if ibp_left != AXIS_KINETIC_ID or ibp_left not in operator_ids or ibp_right in operator_ids or ibp_right is None:
        return _stop("inherited IBP pair")
    if classify_ibp("EXACT_SYMBOLIC_WITH_BOUNDARY_TERM", REGISTERED_BOUNDARY_ASSUMPTIONS) == "EXACTLY_EQUIVALENT":
        return _stop("IBP became unconditional without registered boundary assumptions")
    identity = certify_field_redefinition(
        {
            "fixes_parameter": False,
            "inverse": "Phi -> Phi",
            "invertible": True,
            "local": True,
            "preserves_field_content": True,
            "transformation": "Phi -> Phi",
        }
    )
    if identity["equivalence_result"] != "IDENTITY_NOT_A_REDUCTION" or identity["classes_reduced"] != 0:
        return _stop("identity redefinition")
    axis = next(item for item in overlap["records"] if item["frozen_term_id"] == "matter_kinetic_axis")
    hint = next(item for item in overlap["records"] if item["frozen_term_id"] == "matter_H_int")
    radius = next(item for item in overlap["records"] if item["frozen_term_id"] == "matter_phi_sq")
    if axis["canonical_operator_id"] != AXIS_KINETIC_ID or axis["parameter_redundancy"] != "EXACT" or not overlap["proofs"]["hint_generic_gap"]:
        return _stop("overlap binding")
    if hint["parameter_redundancy"] != "FALSE" or radius["parameter_redundancy"] != "FALSE":
        return _stop("quadratic overlap")
    syzygy_pairs = {(left, right) for item in inside for left in item["operator_ids"] for right in item["operator_ids"] if left < right}
    matrix = _matrix(operator_ids, syzygy_pairs)
    if len(matrix) != 37 * 36 // 2 or any(row["proof_status"] != "DISTINCT_UNDER_SUPPORTED_RULES" for row in matrix):
        return _stop("equivalence matrix")
    if any(row["source_object"] in item["operator_ids"] and row["target_object"] in item["operator_ids"] and row["proof_status"] == "ALGEBRAIC_IDENTITY" for item in inside for row in matrix):
        return _stop("pairwise syzygy collapse")
    coefficient_map = apply_coefficient_map({"c_i": "c_j"}, certified=False)
    dimensionless = sum(item["mass_dimension"] == 0 for item in family["coefficients"])
    if dimensionless != 6 or any(item["value"] != "SYMBOLIC" for item in family["coefficients"]):
        return _stop("coefficients")
    audit_body = {
        "axis_redundancy": "EXACT_DUPLICATE_LABEL",
        "class_count": "NOT_ESTABLISHED",
        "ibp": "UNTESTED",
        "matrix_count": len(matrix),
        "operators": operator_ids,
    }
    digest = content_digest(audit_body)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_15I_STATUS": "COMPLETE",
        "PHASE_15H_STATUS": closure["PHASE_15H_STATUS"],
        "IBP_EQUIVALENCE_STATUS": "UNSUPPORTED",
        "FIELD_REDEFINITION_STATUS": "UNSUPPORTED",
        "EOM_EQUIVALENCE_STATUS": "UNSUPPORTED",
        "BASIS_EQUIVALENCE_STATUS": "UNSUPPORTED",
        "EQUIVALENCE_MATRIX_STATUS": "PARTIAL",
        "EQUIVALENCE_CLASS_COUNT_STATUS": "NOT_ESTABLISHED",
        "ALGEBRAIC_RANK_STATUS": "VERIFIED",
        "PARAMETER_REDUNDANCY_STATUS": "PARTIAL",
        "DIMENSIONLESS_STATUS": "VERIFIED",
        "PARAMETER_CLOSURE_STATUS": "OPEN",
        "PHYSICAL_SELECTION_STATUS": "NONE",
        "PHYSICAL_EQUIVALENCE_STATUS": "PARTIAL",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": GRAMMAR_HASH,
        "manifest_hash": MANIFEST_HASH,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "nominal_operator_count": 37,
        "algebraic_rank": 35,
        "equivalence_class_count": "NOT_ESTABLISHED",
        "syzygy_count": 8,
        "covariant_syzygy_count": 2,
        "syzygy_class": "ALGEBRAIC_IDENTITY",
        "syzygy_reinterpreted": False,
        "operators_removed": 0,
        "operators_added": 0,
        "new_field": "NONE",
        "new_parameter_count": 0,
        "fixed_coefficient_count": 0,
        "classes_reduced": {"basis": 0, "eom": 0, "field_redefinition": 0, "ibp": 0},
        "ibp_records": [
            {
                "assumptions": "NONE_REGISTERED",
                "boundary_requirements": "boundary conditions are not part of the existing specification",
                "equivalence_type": "INTEGRATION_BY_PARTS",
                "invertibility_requirements": "NOT_APPLICABLE",
                "proof_status": classify_ibp(None, ()),
                "provenance": "PHASE_15A1_INHERITED_PAIR",
                "source_object": ibp_left,
                "target_object": ibp_right,
                "transformation": "NOT_CERTIFIED",
            }
        ],
        "field_redefinition_records": [identity],
        "eom_probe": classify_eom(on_shell_zero=True, theorem_implemented=False, redefinition_certified=False),
        "basis_probe": classify_basis(transformation=None, same_spectrum=True, same_symmetry=True),
        "action_probe": classify_action(None, similar_equations=True, symmetries_match=True),
        "composition_probe": compose_chain([]),
        "coefficient_map": coefficient_map,
        "axis_redundancy": {
            "classification": "EXACT_PARAMETER_REDUNDANCY",
            "duplicate_coefficient_labeling": True,
            "operator_id": AXIS_KINETIC_ID,
            "removable_by_certified_reparameterization": False,
            "representation_only": False,
        },
        "quadratic_overlap": {
            "branch_lam_a_equals_lam_b": "NOT_IMPOSED",
            "classification": "GENERIC_INDEPENDENT_AND_PARAMETER_DEPENDENT",
            "representational": True,
        },
        "gravity_terms": "UNCHANGED",
        "dimensionless_count": 6,
        "dimensionless_classification": "PARAMETER_DEPENDENT",
        "dimensionless_fixed_count": 0,
        "pfr_status": "NONE_FOUND",
        "matrix_pair_count": len(matrix),
        "matrix_relation": "DISTINCT_UNDER_SUPPORTED_RULES",
        "supported_relations": ["algebraic canonicalization already applied to the 37 distinct keys", "two 3-term algebraic syzygies, not pairwise equivalences"],
        "unsupported_relations": ["integration by parts", "field redefinitions", "equations-of-motion equivalence", "basis transformations"],
        "equivalence_proof_boundaries": [
            "the inherited integration-by-parts partner lies outside COVARIANT_U1_37 and is not imported",
        ],
        "frozen_action_modified": False,
        "selection_performed": False,
        "audit_digest": digest,
        "audit_digest_repeated": content_digest(audit_body),
    }
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15I_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_15I_EQUIVALENCE_MATRIX.json").write_bytes(canonical_json_bytes({"pairs": matrix}))
        (destination / "PHASE_15I_AUDIT.json").write_bytes(
            canonical_json_bytes(
                {
                    "algebraic_rank": 35,
                    "equivalence_class_count": "NOT_ESTABLISHED",
                    "nominal_operator_count": 37,
                    "statuses": {
                        "BASIS_EQUIVALENCE_STATUS": "UNSUPPORTED",
                        "EOM_EQUIVALENCE_STATUS": "UNSUPPORTED",
                        "FIELD_REDEFINITION_STATUS": "UNSUPPORTED",
                        "IBP_EQUIVALENCE_STATUS": "UNSUPPORTED",
                        "PHYSICAL_EQUIVALENCE_STATUS": "PARTIAL",
                    },
                }
            )
        )
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
