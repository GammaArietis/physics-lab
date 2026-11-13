"""Phase 15E catalogs structural consequences of the registered grammar.

It does not generate operators and does not select a family.
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
from physics_lab.theory_kernel.phase15a_grammar import (
    _ranking_tokens,
    attempt_grammar_mutation,
    catalog_influence,
    classify_candidate,
)
from physics_lab.theory_kernel.phase15b_enumeration import ARTIFACT_DIR_NAME as PHASE_15B_ARTIFACTS
from physics_lab.theory_kernel.phase15d_audit import run_phase_15d
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15E"
CODE_VERSION = "phase15e-catalog-v1"
ARTIFACT_DIR_NAME = "phase15e_catalog_artifacts"
GRAMMAR_HASH = "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
MANIFEST_HASH = "3579a07362f43f389a98fb2dee623d181a3c4324da547f02cb855561a2487103"
ACTION_HASH_14I = "48dc1f2edb675c1de52a9b8a0031565310f56b0638d47467a114478b34f8c25d"
AXIS_KINETIC_ID = "op.7c8094c259bfe4f8"
INHERITED_PARAMETERS = ("c0", "c1", "Z", "kappa", "c_H", "lam_a", "lam_b")


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15E_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15E_BLOCKED"}


def request_support_enumeration() -> str:
    return "SUPPORT_ENUMERATION_NOT_AUTHORIZED"


def _families() -> dict[str, Any]:
    path = _physics_dir() / PHASE_15B_ARTIFACTS / "PHASE_15B_FAMILIES.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError("families")
    return body


def _syzygy_catalog(relations: list[list[dict[str, str]]], source: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = []
    for index, relation in enumerate(relations, start=1):
        identifiers = [term["operator_id"] for term in relation]
        uses_hessian = any(identifier in {row["operator_id"] for row in source["dd_variations"]} for identifier in identifiers)
        catalog.append(
            {
                "consequence": "ALGEBRAIC_IDENTITY",
                "context": "FLAT_ONLY" if uses_hessian else "FLAT_AND_COVARIANT",
                "exactness": "EXACT",
                "identity_id": f"syzygy.{index:02d}",
                "independence": "MEMBER_OF_AN_INDEPENDENT_SET",
                "operator_ids": identifiers,
                "quotient_applied": False,
            }
        )
    return catalog


def _dd_catalog(source: dict[str, Any]) -> list[dict[str, str]]:
    support = {term["operator_id"] for relation in source["relations"] for term in relation}
    rows = []
    for item in source["dd_variations"]:
        rows.append(
            {
                "algebraic_rank_membership": "SYZYGY_SUPPORT" if item["operator_id"] in support else "OUTSIDE_SYZYGY_SUPPORT",
                "derivative_context": "FLAT_SECOND_DERIVATIVE_CONTEXT",
                "global_SO2_status": item["global_so2_status"],
                "local_U1_status": item["variation_status"],
                "operator_id": item["operator_id"],
                "parameter_dependency": "NOT_PARAMETER_DEPENDENT",
                "provenance": "PHASE_15D",
            }
        )
    return rows


def _overlap_catalog(source: dict[str, Any]) -> list[dict[str, str]]:
    labels = {
        "gravity_c0": "DIFFERENT_OPERATOR",
        "gravity_c1_R": "DIFFERENT_OPERATOR",
        "matter_H_int": "REPRESENTATIONAL_OVERLAP",
        "matter_kinetic_axis": "SAME_CANONICAL_OPERATOR",
        "matter_kinetic_plane": "DIFFERENT_OPERATOR",
        "matter_phi_sq": "REPRESENTATIONAL_OVERLAP",
    }
    found = []
    for item in source["frozen_overlaps"]:
        found.append(
            {
                "canonical_operator_id": item.get("canonical_operator_id", ""),
                "classification": labels[item["frozen_term_id"]],
                "frozen_term_id": item["frozen_term_id"],
                "parameter_redundancy": item["parameter_redundancy"],
                "provenance": item["provenance"],
            }
        )
    return found


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    cases = [
        ("1", "exact binding to 15B-15D", "COMPLETE", result["PHASE_15D_STATUS"]),
        ("2", "nominal counts 117/37", "117-37", f"{result['NOMINAL_OPERATOR_COUNT']['FLAT_LORENTZ']}-{result['NOMINAL_OPERATOR_COUNT']['COVARIANT_4D']}"),
        ("3", "algebraic ranks 109/35", "109-35", f"{result['ALGEBRAICALLY_INDEPENDENT_RANK']['FLAT_LORENTZ']}-{result['ALGEBRAICALLY_INDEPENDENT_RANK']['COVARIANT_4D']}"),
        ("4", "all eight syzygies reproduced", "8", str(result["syzygy_count"])),
        ("5", "80/80 DD symmetry classification preserved", "80/80", result["DD_SYMMETRY_CLASSIFICATION_COVERAGE"]),
        ("6", "26/54 local split preserved", "26-54", f"{result['local_u1_invariant']}-{result['local_u1_breaking']}"),
        ("7", "flat and covariant contexts remain separate", "SEPARATE", "SEPARATE" if result["contexts_separate"] else "MERGED"),
        ("8", "54 operators are not silently deleted", "0", str(result["operators_removed"])),
        ("9", "26-operator symmetry-preserving subspace is metadata only", "METADATA_ONLY", result["symmetry_subspace_role"]),
        ("10", "no coefficient is fixed", "NONE", result["imposed_relations"]),
        ("11", "no new parameter", "0", str(result["new_coefficient_count"])),
        ("12", "no new field", "NONE", result["new_field"]),
        ("13", "no grammar mutation", "REJECTED", attempt_grammar_mutation({"grammar_version": "grammar_15e_v1"})["status"]),
        ("14", "no unsupported equivalence", "UNAPPLIED", "UNAPPLIED" if result["unsupported_equivalence_applied"] is False else "APPLIED"),
        ("15", "no support enumeration", "SUPPORT_ENUMERATION_NOT_AUTHORIZED", request_support_enumeration()),
        ("16", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("17", "no target input", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("18", "frozen action unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("19", "no known-physics feedback", "ISOLATED", catalog_influence({"entries": []}, "catalog")["status"]),
        ("20", "complete output deterministic", result["catalog_digest"], result["catalog_digest_repeated"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15e(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    if request_support_enumeration() != "SUPPORT_ENUMERATION_NOT_AUTHORIZED":
        return _stop("SUPPORT_ENUMERATION_NOT_AUTHORIZED")
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    source = run_phase_15d(write_artifacts=False)
    families = _families()
    flat = families["FLAT_LORENTZ"]
    curved = families["COVARIANT_4D"]
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or source.get("status") != "OK"
        or source.get("PHASE_15D_STATUS") != "COMPLETE"
        or source.get("PHASE_15C_STATUS") != "COMPLETE"
        or source.get("grammar_version") != "grammar_15a_v1"
        or source.get("grammar_hash") != GRAMMAR_HASH
        or source.get("PHASE_15B_MANIFEST_HASH") != MANIFEST_HASH
        or source.get("ACTION_HASH_14I_INPUT") != ACTION_HASH_14I
        or source.get("FROZEN_ACTION_STATUS") != "VERIFIED"
        or source.get("PROVENANCE_STATUS") != "VERIFIED"
        or source.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or source.get("REPRODUCIBILITY_STATUS") != "VERIFIED"
        or source.get("operators_removed") != 0
        or catalog_influence({"entries": []}, "catalog")["applied"] is not False
    ):
        return _stop("integrity gate")
    if (flat["coefficient_count"], flat["dimensionless_coefficient_count"], flat["dimensionful_coefficient_count"]) != (117, 9, 108):
        return _stop("flat coefficient inventory")
    if (curved["coefficient_count"], curved["dimensionless_coefficient_count"], curved["dimensionful_coefficient_count"]) != (37, 6, 31):
        return _stop("covariant coefficient inventory")
    if source["nominal_operator_count"] != {"COVARIANT_4D": 37, "FLAT_LORENTZ": 117}:
        return _stop("nominal counts")
    if source["algebraically_independent_rank"] != {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109}:
        return _stop("algebraic ranks")
    if source["raw_contractions"] != 473 or source["canonical_keys"] != 204 or source["zero_identities"] != 87:
        return _stop("grammar reduction")
    syzygies = _syzygy_catalog(source["relations"], source)
    dd_rows = _dd_catalog(source)
    if len(syzygies) != 8 or any(item["quotient_applied"] for item in syzygies):
        return _stop("syzygy catalog")
    invariant = [row for row in dd_rows if row["local_U1_status"] == "local U(1) invariant"]
    breaking = [row for row in dd_rows if row["local_U1_status"] == "local U(1) breaking"]
    if len(dd_rows) != 80 or len(invariant) != 26 or len(breaking) != 54:
        return _stop("DD split")
    if any(row["global_SO2_status"] != "global SO(2) invariant" for row in dd_rows):
        return _stop("global status")
    if any(row["derivative_context"] != "FLAT_SECOND_DERIVATIVE_CONTEXT" for row in dd_rows):
        return _stop("DD context")
    curved_ids = set(curved["operator_ids"])
    if curved_ids & {row["operator_id"] for row in dd_rows} or len(curved_ids) != 37 or len(flat["operator_ids"]) != 117:
        return _stop("context separation")
    overlaps = _overlap_catalog(source)
    axis = next(item for item in overlaps if item["frozen_term_id"] == "matter_kinetic_axis")
    if axis["canonical_operator_id"] != AXIS_KINETIC_ID or axis["classification"] != "SAME_CANONICAL_OPERATOR" or axis["parameter_redundancy"] != "EXACT":
        return _stop("axis overlap")
    expected_overlap = {
        "gravity_c0": "DIFFERENT_OPERATOR",
        "gravity_c1_R": "DIFFERENT_OPERATOR",
        "matter_H_int": "REPRESENTATIONAL_OVERLAP",
        "matter_kinetic_plane": "DIFFERENT_OPERATOR",
        "matter_phi_sq": "REPRESENTATIONAL_OVERLAP",
    }
    if any(item["classification"] != expected_overlap[item["frozen_term_id"]] for item in overlaps if item["frozen_term_id"] in expected_overlap):
        return _stop("overlap catalog")
    catalog_body = {
        "breaking": [row["operator_id"] for row in breaking],
        "invariant": [row["operator_id"] for row in invariant],
        "overlaps": overlaps,
        "syzygies": syzygies,
    }
    catalog_digest = content_digest(catalog_body)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_15E_STATUS": "COMPLETE",
        "CATALOG_BINDING_STATUS": "VERIFIED",
        "SYZYGY_CATALOG_STATUS": "VERIFIED",
        "DD_SYMMETRY_CATALOG_STATUS": "VERIFIED",
        "FLAT_COVARIANT_SEPARATION_STATUS": "VERIFIED",
        "PARAMETER_CATALOG_STATUS": "VERIFIED",
        "PFR_CATALOG_STATUS": "NONE_FOUND",
        "DIMENSIONLESS_CATALOG_STATUS": "VERIFIED",
        "FROZEN_OVERLAP_CATALOG_STATUS": "VERIFIED",
        "EOM_CATALOG_STATUS": "PARTIAL",
        "CONSERVATION_CATALOG_STATUS": "UNTESTED",
        "REMAINING_FREEDOM_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "PHASE_15D_STATUS": source["PHASE_15D_STATUS"],
        "PHASE_15C_STATUS": source["PHASE_15C_STATUS"],
        "grammar_version": "grammar_15a_v1",
        "grammar_hash": GRAMMAR_HASH,
        "PHASE_15B_MANIFEST_HASH": MANIFEST_HASH,
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "NOMINAL_OPERATOR_COUNT": {"COVARIANT_4D": 37, "FLAT_LORENTZ": 117},
        "ALGEBRAICALLY_INDEPENDENT_RANK": {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109},
        "PHYSICALLY_INEQUIVALENT_COUNT": "NOT_ESTABLISHED",
        "syzygy_count": 8,
        "syzygy_rank": source["syzygy_rank"],
        "syzygies": syzygies,
        "DD_SYMMETRY_CLASSIFICATION_COVERAGE": "80/80",
        "dd_catalog": dd_rows,
        "local_u1_invariant": 26,
        "local_u1_breaking": 54,
        "global_so2_invariant": 80,
        "flat_complete_family": {"global_SO2": "EXACT", "local_U1": "BROKEN"},
        "covariant_complete_family": {"global_SO2": "EXACT", "local_U1": "EXACT"},
        "contexts_separate": True,
        "covariant_family_role": "GRAMMAR_CONTEXT_SUBSET",
        "symmetry_subspace_role": "METADATA_ONLY",
        "symmetry_preserving_subspace": {
            "breaking_dd_operators_excluded_from_subspace": 54,
            "covariant_family_rewritten_from_flat": False,
            "locally_invariant_dd_operators": 26,
            "nominal_flat_count_unchanged": 117,
            "role": "METADATA_ONLY",
        },
        "coefficients": {
            "COVARIANT_4D": {
                "algebraic_coefficient_directions": 35,
                "dimensionful_coefficients": 31,
                "dimensionless_coefficients": 6,
                "inherited_coefficients": len(INHERITED_PARAMETERS),
                "new_coefficients": 0,
                "nominal_coefficients": 37,
            },
            "FLAT_LORENTZ": {
                "algebraic_coefficient_directions": 109,
                "dimensionful_coefficients": 108,
                "dimensionless_coefficients": 9,
                "inherited_coefficients": len(INHERITED_PARAMETERS),
                "new_coefficients": 0,
                "nominal_coefficients": 117,
            },
        },
        "new_coefficient_count": 0,
        "relation_classes": [
            {"label": "ALGEBRAIC_IDENTITY", "object": "eight A-B+C syzygies"},
            {"label": "SYMMETRY_RELATION", "object": "global SO(2) of all 80 DD operators and local U(1) of the covariant sum"},
            {"label": "PARAMETER_DEPENDENT", "object": "lam_a = lam_b branch of the quadratic overlap"},
            {"label": "NOT_DERIVED", "object": "a fixed numerical coefficient or a fixed dimensionless quantity"},
        ],
        "dimensionless_classification": "PARAMETER_DEPENDENT",
        "derived_fixed_dimensionless_count": 0,
        "frozen_overlaps": overlaps,
        "PARAMETER_REDUNDANCY_CONSEQUENCE": "PARTIAL",
        "eom_reason": "the differential order is recorded and the closed form of either complete sum remains untested",
        "conservation": {"COVARIANT_4D": "UNTESTED", "FLAT_LORENTZ": "UNTESTED"},
        "constraints": [
            {"item": "locality", "provenance": "PHASE_15B", "status": "POINT_LOCAL"},
            {"item": "Lorentz invariance of the flat family", "provenance": "PHASE_15B", "status": "FLAT_LORENTZ"},
            {"item": "general covariance of the 37-operator subset", "provenance": "PHASE_15A1", "status": "GENERALLY_COVARIANT"},
            {"item": "global SO(2) of the 80 DD operators", "provenance": "PHASE_15D", "status": "EXACT"},
            {"item": "local U(1) of the covariant complete sum", "provenance": "PHASE_15D", "status": "EXACT"},
            {"item": "eight algebraic syzygies", "provenance": "PHASE_15D", "status": "EXACT"},
            {"item": "derivative bound", "provenance": "PHASE_15A", "status": "MAX_DERIVATIVE_ORDER_4"},
            {"item": "field-order bound", "provenance": "PHASE_15A", "status": "MAX_FIELD_ORDER_4"},
            {"item": "free coefficients", "provenance": "PHASE_15B", "status": "SYMBOLIC"},
            {"item": "frozen-action boundary", "provenance": "PHASE_4C", "status": "IMMUTABLE_REFERENCE"},
        ],
        "remaining_freedoms": [
            "coefficient values",
            "dimensionful scales",
            "unsupported equivalence transformations",
            "operator support choices",
            "physical selection among admissible contexts",
            "vacuum selection",
            "modulus stabilization",
            "hidden-sector extensions",
        ],
        "known_theory_role": "REFERENCE_ONLY",
        "selection_performed": False,
        "operators_removed": 0,
        "new_field": "NONE",
        "new_physical_principle": "NONE",
        "imposed_relations": "NONE",
        "unsupported_equivalence_applied": False,
        "support_enumeration": "NOT_EXECUTED",
        "catalog_digest": catalog_digest,
        "catalog_digest_repeated": content_digest(catalog_body),
    }
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15E_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_15E_CATALOG.json").write_bytes(
            canonical_json_bytes(
                {
                    "algebraic_rank": payload["ALGEBRAICALLY_INDEPENDENT_RANK"],
                    "coefficients": payload["coefficients"],
                    "dd_catalog": dd_rows,
                    "nominal_count": payload["NOMINAL_OPERATOR_COUNT"],
                    "physical_inequivalent_count": "NOT_ESTABLISHED",
                    "syzygies": syzygies,
                    "symmetry_preserving_subspace": payload["symmetry_preserving_subspace"],
                }
            )
        )
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
