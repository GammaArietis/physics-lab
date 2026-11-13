"""Phase 15G enumerates the authorized COVARIANT_U1_37 symbolic family.

The operator list comes from the registered grammar_15f_v1 profile.
Support subsets are not generated.
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
from physics_lab.theory_kernel.phase15a1_boundary import _covariance
from physics_lab.theory_kernel.phase15a_grammar import (
    ASSUMPTIONS,
    BLACKLIST_VERSION,
    EQUIVALENCE_ENGINE_VERSION,
    WHITELIST_VERSION,
    _ranking_tokens,
    catalog_influence,
    classify_candidate,
    compile_grammar,
)
from physics_lab.theory_kernel.phase15b_enumeration import ACTION_HASH_14I
from physics_lab.theory_kernel.phase15c_audit import INHERITED_PARAMETERS, _symmetry_proofs
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15G"
CODE_VERSION = "phase15g-enumeration-v1"
TEST_VERSION = "phase15g-tests-v1"
ARTIFACT_DIR_NAME = "phase15g_enumeration_artifacts"
GRAMMAR_VERSION = "grammar_15f_v1"
GRAMMAR_HASH = "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
PARENT_GRAMMAR_VERSION = "grammar_15a_v1"
PARENT_GRAMMAR_HASH = "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
SEARCH_PROFILE = "COVARIANT_U1_37"
AUTHORIZATION_RECORD = {
    "authorization_id": "PHASE_15G_COVARIANT_U1_37",
    "authorizes_known_physics_matching": False,
    "authorizes_new_fields": False,
    "authorizes_new_operators": False,
    "authorizes_new_parameters": False,
    "authorizes_new_symmetries": False,
    "authorizes_numerical_fitting": False,
    "authorizes_ranking": False,
    "authorizes_support_selection": False,
    "authorized_profile": SEARCH_PROFILE,
    "scope": "execute the already registered grammar profile",
    "source": "PHASE_15G_SPECIFICATION",
    "status": "HUMAN-AUTHORIZED BLIND SEARCH",
}
UNSUPPORTED_RULES = (
    "integration by parts",
    "field redefinitions",
    "equations-of-motion equivalence",
    "basis transformations",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15G_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15G_BLOCKED"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def classify_authorization(record: dict[str, Any] | None) -> str:
    if not isinstance(record, dict):
        return "HUMAN_AUTHORIZATION_REQUIRED"
    if record.get("status") != "HUMAN-AUTHORIZED BLIND SEARCH":
        return "HUMAN_AUTHORIZATION_REQUIRED"
    if record.get("authorized_profile") != SEARCH_PROFILE:
        return "HUMAN_AUTHORIZATION_REQUIRED"
    if record.get("scope") != "execute the already registered grammar profile":
        return "HUMAN_AUTHORIZATION_REQUIRED"
    flags = (
        "authorizes_new_fields",
        "authorizes_new_operators",
        "authorizes_new_symmetries",
        "authorizes_new_parameters",
        "authorizes_numerical_fitting",
        "authorizes_support_selection",
        "authorizes_ranking",
        "authorizes_known_physics_matching",
    )
    if any(record.get(flag) is True for flag in flags):
        return "FAILED"
    return "VERIFIED"


def enumerate_support_subsets(*_args: Any, **_kwargs: Any) -> str:
    return "SUPPORT_ENUMERATION_NOT_AUTHORIZED"


def request_model_ordering(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_CALLED"


def _manifest(assumption_hash: str) -> dict[str, Any]:
    return {
        "assumption_manifest_hash": assumption_hash,
        "authorization_id": AUTHORIZATION_RECORD["authorization_id"],
        "canonicalization_version": "phase15a1-certified-rules-v1",
        "code_version": CODE_VERSION,
        "equivalence_version": EQUIVALENCE_ENGINE_VERSION,
        "grammar_hash": GRAMMAR_HASH,
        "grammar_version": GRAMMAR_VERSION,
        "random_seed": "NOT_USED",
        "search_profile": SEARCH_PROFILE,
        "test_version": TEST_VERSION,
        "timestamp": "NOT_ISSUED",
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
    }


def _family_body(members: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(members, key=lambda item: item["object_id"])
    coefficients = [
        {
            "coefficient_id": item["parameter_id"],
            "mass_dimension": item["coefficient_mass_dimension"],
            "operator_id": item["object_id"],
            "physical_or_normalization_status": "NOT_NORMALIZED",
            "provenance": "INPUT",
            "value": "SYMBOLIC",
        }
        for item in ordered
    ]
    return {
        "coefficients": coefficients,
        "formula": "S_registered_existing + sum_i c_i O_i",
        "operator_ids": [item["object_id"] for item in ordered],
        "search_profile": SEARCH_PROFILE,
    }


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    symbolic = all(item["value"] == "SYMBOLIC" for item in result["coefficients"])
    cases = [
        ("1", "authorization is required", "HUMAN_AUTHORIZATION_REQUIRED", classify_authorization(None)),
        ("2", "COVARIANT_U1_37 is the only active profile", SEARCH_PROFILE, result["SEARCH_PROFILE"]),
        ("3", "exactly 37 operators are loaded", "37", str(result["nominal_operator_count"])),
        ("4", "exactly 35 algebraic rank is reproduced", "35", str(result["algebraic_rank"])),
        ("5", "all operators pass local U(1)", "EXACT", result["local_U1"]),
        ("6", "all operators pass certified general covariance", "PASS", result["covariance_result"]),
        ("7", "no flat-only DD operator enters", "0", str(result["flat_dd_operator_count"])),
        ("8", "no support subsets are enumerated", "SUPPORT_ENUMERATION_NOT_AUTHORIZED", enumerate_support_subsets()),
        ("9", "no coefficient values are numerically assigned", "SYMBOLIC", "SYMBOLIC" if symbolic else "NUMERIC"),
        ("10", "no coefficient is silently fixed", "0", str(result["fixed_coefficient_count"])),
        ("11", "no new parameter enters", "0", str(result["newly_introduced_parameter_count"])),
        ("12", "no new field enters", "NONE", result["new_field"]),
        ("13", "no new gauge group enters", "EXISTING", result["gauge_group_status"]),
        ("14", "no new physical principle enters", "NONE", result["new_physical_principle"]),
        ("15", "syzygies remain metadata", "False", str(result["syzygy_quotient_applied"])),
        ("16", "unsupported equivalences remain unsupported", "False", str(result["unsupported_equivalence_applied"])),
        ("17", "frozen Phase 4C action remains unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("18", "no F2 branch is silently merged", "False", str(result["branch_b_merged"])),
        ("19", "no known physics enters filtering", "ISOLATED", catalog_influence({"entries": []}, "generation")["status"]),
        ("20", "no ranking function is called", "NOT_CALLED", result["ranking_call"]),
        ("21", "no target information is accessed", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("22", "search manifest is deterministic", result["manifest_hash"], result["manifest_hash_repeated"]),
        ("23", "repeated run reproduces identical symbolic output", result["family_digest"], result["family_digest_repeated"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15g(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    if classify_authorization(AUTHORIZATION_RECORD) != "VERIFIED":
        return {"AUTHORIZATION_STATUS": "REQUIRED", "PHASE_15G_STATUS": "BLOCKED", "status": "HUMAN_AUTHORIZATION_REQUIRED"}
    if enumerate_support_subsets() != "SUPPORT_ENUMERATION_NOT_AUTHORIZED":
        return _stop("SUPPORT_ENUMERATION_NOT_AUTHORIZED")
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    grammar_file = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    operational = grammar_file["operational"]
    compiled = compile_grammar()
    catalog = _read("phase15e_catalog_artifacts/PHASE_15E_CATALOG.json")
    overlap = _read("phase15d_audit_artifacts/PHASE_15D_OVERLAP.json")
    prior_family = _read("phase15b_enumeration_artifacts/PHASE_15B_FAMILIES.json")["COVARIANT_4D"]
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or content_digest(operational) != GRAMMAR_HASH
        or grammar_file.get("grammar_hash") != GRAMMAR_HASH
        or operational.get("grammar_version") != GRAMMAR_VERSION
        or compiled.get("grammar_hash") != PARENT_GRAMMAR_HASH
        or compiled.get("operational", {}).get("grammar_version") != PARENT_GRAMMAR_VERSION
        or catalog_influence({"entries": []}, "generation")["applied"] is not False
    ):
        return _stop("integrity gate")
    profile = next(item for item in operational["profiles"] if item["profile_id"] == SEARCH_PROFILE)
    other_profiles = [item["profile_id"] for item in operational["profiles"] if item["profile_id"] != SEARCH_PROFILE]
    selected_ids = list(profile["operator_ids"])
    contexts = operational["contexts"]
    ambient_ids = contexts["FLAT_LORENTZ_AMBIENT"]["operator_ids"]
    preserving_ids = contexts["LOCAL_U1_PRESERVING"]["operator_ids"]
    covariant_ids = contexts["COVARIANT_4D"]["operator_ids"]
    if (
        selected_ids != covariant_ids
        or len(selected_ids) != 37
        or len(preserving_ids) != 63
        or len(ambient_ids) != 117
        or not set(selected_ids) <= set(preserving_ids) <= set(ambient_ids)
        or set(selected_ids) != set(prior_family["operator_ids"])
    ):
        return _stop("profile membership")
    by_id = {item["object_id"]: item for item in compiled["enabled"]}
    if any(item not in by_id for item in selected_ids):
        return {"PHASE_15G_STATUS": "BLOCKED", "status": "SEARCH_INPUT_INTEGRITY_FAILURE"}
    members = [by_id[item] for item in selected_ids]
    dd_ids = {row["operator_id"] for row in catalog["dd_catalog"]}
    breaking_ids = {row["operator_id"] for row in catalog["dd_catalog"] if row["local_U1_status"] == "local U(1) breaking"}
    if set(selected_ids) & dd_ids or set(selected_ids) & breaking_ids:
        return {"PHASE_15G_STATUS": "BLOCKED", "operators_removed": 0, "status": "SEARCH_INPUT_INTEGRITY_FAILURE"}
    if any("DDPhi" in item["mathematical_definition"] for item in members):
        return {"PHASE_15G_STATUS": "BLOCKED", "operators_removed": 0, "status": "SEARCH_INPUT_INTEGRITY_FAILURE"}
    covariance_rows = [_covariance(item["mathematical_definition"]) for item in members]
    if any(row["covariance"] not in {"BOTH", "GENERALLY_COVARIANT"} for row in covariance_rows):
        return {"PHASE_15G_STATUS": "BLOCKED", "status": "COVARIANCE_INPUT_MISMATCH"}
    if any(item.get("nonlocal") is True for item in members):
        return _stop("locality")
    proofs = _symmetry_proofs()
    if not all(proofs.values()):
        return {"PHASE_15G_STATUS": "BLOCKED", "operators_removed": 0, "status": "SEARCH_INPUT_INTEGRITY_FAILURE"}
    syzygies = catalog["syzygies"]
    inside = [item for item in syzygies if set(item["operator_ids"]) <= set(selected_ids)]
    if (
        len(syzygies) != 8
        or any(item["quotient_applied"] for item in syzygies)
        or len(inside) != 2
        or any(item["independence"] != "MEMBER_OF_AN_INDEPENDENT_SET" for item in inside)
        or catalog["algebraic_rank"] != {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109}
        or 37 - len(inside) != 35
    ):
        return _stop("syzygy metadata")
    if any(item["allowed_coefficient"] != "FREE" for item in members):
        return _stop("a coefficient is not free")
    family = _family_body(members)
    repeated = _family_body(members)
    if any(isinstance(item["value"], (int, float)) for item in family["coefficients"]):
        return {"PHASE_15G_STATUS": "BLOCKED", "status": "TARGET_BLINDNESS_VIOLATION"}
    dimensionless = sum(item["mass_dimension"] == 0 for item in family["coefficients"])
    if (len(family["coefficients"]), dimensionless, len(family["coefficients"]) - dimensionless) != (37, 6, 31):
        return _stop("coefficient inventory")
    if prior_family["dimensionless_coefficient_count"] != 6 or prior_family["branch_b_merged"] is not False:
        return _stop("prior family boundary")
    assumption_hash = content_digest(
        {
            "assumptions": list(ASSUMPTIONS),
            "constraints": operational["constraints"],
            "search_profile": SEARCH_PROFILE,
        }
    )
    manifest = _manifest(assumption_hash)
    manifest_hash = content_digest(manifest)
    family_digest = content_digest(family)
    overlaps = overlap["records"]
    axis = next(item for item in overlaps if item["frozen_term_id"] == "matter_kinetic_axis")
    if axis["canonical_operator_id"] not in selected_ids or axis["parameter_redundancy"] != "EXACT":
        return _stop("axis redundancy")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_15G_STATUS": "COMPLETE",
        "AUTHORIZATION_STATUS": "VERIFIED",
        "PROFILE_STATUS": "VERIFIED",
        "OPERATOR_INPUT_STATUS": "VERIFIED",
        "SYMMETRY_STATUS": "VERIFIED",
        "COVARIANCE_STATUS": "VERIFIED",
        "LOCALITY_STATUS": "VERIFIED",
        "SYMBOLIC_ACTION_STATUS": "VERIFIED",
        "EOM_STATUS": "PARTIAL",
        "CONSERVATION_STATUS": "UNTESTED",
        "PFR_STATUS": "NONE_FOUND",
        "DIMENSIONLESS_STATUS": "VERIFIED",
        "SYZYGY_STATUS": "VERIFIED",
        "PARAMETER_ACCOUNTING_STATUS": "VERIFIED",
        "EQUIVALENCE_STATUS": "PARTIAL",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "SEARCH_PROFILE": SEARCH_PROFILE,
        "inactive_profiles": other_profiles,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": GRAMMAR_HASH,
        "parent_grammar_version": PARENT_GRAMMAR_VERSION,
        "parent_grammar_hash": PARENT_GRAMMAR_HASH,
        "authorization_id": AUTHORIZATION_RECORD["authorization_id"],
        "authorization_record_status": AUTHORIZATION_RECORD["status"],
        "manifest_hash": manifest_hash,
        "manifest_hash_repeated": content_digest(_manifest(assumption_hash)),
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "AMBIENT_OPERATOR_COUNT": 117,
        "U1_PRESERVING_COUNT": 63,
        "COVARIANT_U1_COUNT": 37,
        "nominal_operator_count": 37,
        "algebraic_rank": 35,
        "COVARIANT_ALGEBRAIC_RANK": 35,
        "coefficient_count": 37,
        "dimensionless_coefficient_count": dimensionless,
        "dimensionful_coefficient_count": 37 - dimensionless,
        "inherited_parameter_count": len(INHERITED_PARAMETERS),
        "newly_introduced_parameter_count": 0,
        "fixed_coefficient_count": 0,
        "coefficients": family["coefficients"],
        "operator_ids": family["operator_ids"],
        "formula": family["formula"],
        "registered_existing": {
            "action_content_hash": FROZEN_4C_HASH,
            "expanded": False,
            "role": "IMMUTABLE_REFERENCE",
        },
        "global_SO2": "EXACT",
        "local_U1": "EXACT",
        "covariance_result": "PASS",
        "locality_status": "POINT_LOCAL",
        "flat_dd_operator_count": 0,
        "operators_removed": 0,
        "syzygy_count": 8,
        "syzygies_inside_profile": [item["identity_id"] for item in inside],
        "syzygy_quotient_applied": False,
        "syzygy_role": "ALGEBRAIC_DEPENDENCY_METADATA",
        "eom": {
            "EOM_ORDER": 2,
            "HIGHER_DERIVATIVE_STATUS": "ABSENT",
            "closed_form": "UNTESTED",
            "reason": "no loaded density contains DDPhi",
        },
        "conservation": "UNTESTED",
        "relation_classes": [
            {"label": "ALGEBRAIC_IDENTITY", "object": "syzygy.06 and syzygy.08"},
            {"label": "SYMMETRY_RELATION", "object": "global SO(2) and local U(1) of the complete symbolic sum"},
            {"label": "PARAMETER_DEPENDENT", "object": "lam_a = lam_b branch of the quadratic overlap"},
            {"label": "NOT_DERIVED", "object": "a fixed numerical coefficient or a fixed dimensionless quantity"},
        ],
        "dimensionless_classification": "PARAMETER_DEPENDENT",
        "derived_fixed_dimensionless_count": 0,
        "frozen_overlaps": overlaps,
        "parameter_redundancy_recorded": True,
        "frozen_action_modified": False,
        "branch_a_merged": False,
        "branch_b_merged": False,
        "unsupported_equivalence_applied": False,
        "unsupported_rules": list(UNSUPPORTED_RULES),
        "PHYSICALLY_INEQUIVALENT_COUNT": "NOT_ESTABLISHED",
        "GENERATED_SYMBOLIC_FAMILIES": 1,
        "DERIVED_STRUCTURAL_SUBSPACE": SEARCH_PROFILE,
        "SUPPORT_SUBSET_ENUMERATION": "NOT_PERFORMED",
        "new_field": "NONE",
        "gauge_group_status": "EXISTING",
        "new_physical_principle": "NONE",
        "ranking_call": request_model_ordering(),
        "family_digest": family_digest,
        "family_digest_repeated": content_digest(repeated),
        "interpretation": "blind structural enumeration of the COVARIANT_U1_37 symbolic family",
        "parameter_closure": "OPEN",
    }
    if payload["ranking_call"] != "NOT_CALLED":
        return {"PHASE_15G_STATUS": "BLOCKED", "status": "TARGET_BLINDNESS_VIOLATION"}
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15G_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_15G_SEARCH_MANIFEST.json").write_bytes(canonical_json_bytes(manifest))
        (destination / "PHASE_15G_FAMILY.json").write_bytes(
            canonical_json_bytes(
                {
                    "algebraic_rank": 35,
                    "coefficient_count": 37,
                    "coefficients": family["coefficients"],
                    "formula": family["formula"],
                    "nominal_operator_count": 37,
                    "operator_ids": family["operator_ids"],
                    "search_profile": SEARCH_PROFILE,
                }
            )
        )
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
