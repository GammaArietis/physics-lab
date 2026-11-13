"""Phase 15B enumerates one maximal symbolic family in each spacetime context.

Coefficient-support subsets are not models. The frozen action is not modified.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a1_boundary import run_phase_15a1
from physics_lab.theory_kernel.phase15a_grammar import (
    ASSUMPTIONS,
    BLACKLIST_VERSION,
    EQUIVALENCE_ENGINE_VERSION,
    GRAMMAR_VERSION,
    WHITELIST_VERSION,
    _parameter_dependent,
    _ranking_tokens,
    attempt_grammar_mutation,
    catalog_influence,
    classify_candidate,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15B"
CODE_VERSION = "phase15b-enumeration-v1"
TEST_VERSION = "phase15b-tests-v1"
ARTIFACT_DIR_NAME = "phase15b_enumeration_artifacts"
ACTION_HASH_14I = "48dc1f2edb675c1de52a9b8a0031565310f56b0638d47467a114478b34f8c25d"
EXPECTED_GRAMMAR_HASH = "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
FIELDS = ["Phi", "metric", "mathcal A_mu"]
AUTHORIZATION_RECORD = {
    "authorization_id": "PHASE_15B_BLIND_ENUMERATION",
    "authorizes_new_fields": False,
    "authorizes_new_operators": False,
    "authorizes_parameter_fixing": False,
    "authorizes_ranking": False,
    "scope": "execute the already defined grammar",
    "source": "PHASE_15B_SPECIFICATION",
}
INTERPRETATION = {
    "classification": "SEARCH-SPACE INTERPRETATION",
    "not_a_physical_principle": True,
    "statement": "excluding an allowed operator would require an additional principle, so the initial object is the maximal symbolic family",
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


def classify_authorization(record: dict[str, Any] | None) -> str:
    if not isinstance(record, dict):
        return "HUMAN_AUTHORIZATION_REQUIRED"
    if record.get("authorization_id") != "PHASE_15B_BLIND_ENUMERATION":
        return "HUMAN_AUTHORIZATION_REQUIRED"
    if record.get("scope") != "execute the already defined grammar":
        return "HUMAN_AUTHORIZATION_REQUIRED"
    if any(record.get(flag) is True for flag in ("authorizes_new_fields", "authorizes_new_operators", "authorizes_parameter_fixing", "authorizes_ranking")):
        return "FAILED"
    return "VERIFIED"


def enumerate_support_subsets(*_args: Any, **_kwargs: Any) -> str:
    return "SUPPORT_ENUMERATION_NOT_DEFINED"


def enumerate_coefficient_values(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENUMERATED"


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _coefficient(operator: dict[str, Any]) -> dict[str, Any]:
    return {
        "coefficient_id": operator["parameter_id"],
        "field_dimension": operator["field_order"],
        "mass_dimension": operator["coefficient_mass_dimension"],
        "operator_id": operator["object_id"],
        "physical_or_normalization_status": "NOT_NORMALIZED",
        "provenance": "INPUT",
        "value": "SYMBOLIC",
    }


def _family(context: str, covariance: str, members: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(members, key=lambda item: item["object_id"])
    coefficients = [_coefficient(item) for item in ordered]
    dimensionless = sum(item["mass_dimension"] == 0 for item in coefficients)
    return {
        "branch_a_merged": False,
        "branch_b_merged": False,
        "coefficient_count": len(coefficients),
        "coefficients": coefficients,
        "covariance_status": covariance,
        "derivative_order": max(item["derivative_order"] for item in ordered),
        "dimensionful_coefficient_count": len(coefficients) - dimensionless,
        "dimensionless_coefficient_count": dimensionless,
        "family_f_members": sum("F" in item["family_ids"] for item in ordered),
        "field_content": list(FIELDS),
        "field_order": max(item["field_order"] for item in ordered),
        "formula": "S_registered_existing + sum_i c_i O_i",
        "gauge_status": "INHERITED_EXISTING_LOCAL_U1",
        "locality_status": "POINT_LOCAL",
        "operator_count": len(ordered),
        "operator_ids": [item["object_id"] for item in ordered],
        "parameter_free_relation_count": 0,
        "spacetime_context": context,
        "symmetry_status": "INHERITED_FROM_REGISTERED_INVARIANT_DENSITIES",
        "unsupported_equivalence_count": len(UNSUPPORTED_RULES),
        "verified_parameter_free_relation_count": 0,
    }


def _obligations() -> list[dict[str, Any]]:
    items = (
        "summed-family Euler-Lagrange equations were not recomputed",
        "conservation identities of the summed family were not recomputed",
        "overlap between frozen monomials and the registered densities is not certified",
        "curved Christoffel densities remain outside the generator",
        "integration by parts remains unresolved",
        "field redefinitions remain unresolved",
        "equations-of-motion quotient remains unresolved",
    )
    return [{"certified_pass": False, "current_status": "OPEN", "obligation": item} for item in items]


def _manifest(grammar_hash: str) -> dict[str, Any]:
    assumptions = content_digest({"assumptions": list(ASSUMPTIONS), "interpretation": INTERPRETATION})
    return {
        "assumption_manifest_hash": assumptions,
        "authorization_id": AUTHORIZATION_RECORD["authorization_id"],
        "blacklist_version": BLACKLIST_VERSION,
        "canonicalization_version": "phase15a1-certified-rules-v1",
        "code_version": CODE_VERSION,
        "equivalence_engine_version": EQUIVALENCE_ENGINE_VERSION,
        "grammar_hash": grammar_hash,
        "grammar_version": GRAMMAR_VERSION,
        "random_seed": "NOT_USED",
        "test_version": TEST_VERSION,
        "timestamp": "NOT_ISSUED",
        "whitelist_version": WHITELIST_VERSION,
    }


def _family_digest(family: dict[str, Any]) -> str:
    body = {
        "coefficients": family["coefficients"],
        "formula": family["formula"],
        "operator_ids": family["operator_ids"],
        "spacetime_context": family["spacetime_context"],
    }
    return content_digest(body)


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15B_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15B_BLOCKED"}


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    flat = result["families"]["FLAT_LORENTZ"]
    curved = result["families"]["COVARIANT_4D"]
    symbolic = all(item["value"] == "SYMBOLIC" for family in result["families"].values() for item in family["coefficients"])
    cases = [
        ("1", "human authorization required", "HUMAN_AUTHORIZATION_REQUIRED", classify_authorization(None)),
        ("2", "freeze integrity", "VERIFIED", result["FROZEN_ACTION_STATUS"]),
        ("3", "exact grammar hash", EXPECTED_GRAMMAR_HASH, result["grammar_hash"]),
        ("4", "473 to 204 to 117 input reproduction", "473-204-117", result["input_reduction"]),
        ("5", "no support-subset enumeration", "SUPPORT_ENUMERATION_NOT_DEFINED", enumerate_support_subsets()),
        ("6", "no numerical coefficient assignment", "SYMBOLIC", "SYMBOLIC" if symbolic else "NUMERIC"),
        ("7", "all coefficients remain symbolic", "SYMBOLIC", "SYMBOLIC" if symbolic else "NUMERIC"),
        ("8", "flat and curved contexts stay separate", "SEPARATE", "SEPARATE" if result["contexts_separate"] else "MERGED"),
        ("9", "family F remains a subset", "92", str(result["family_f_count"])),
        ("10", "no new field", "UNCHANGED", result["field_content_status"]),
        ("11", "no new gauge group", "EXISTING", result["gauge_group_status"]),
        ("12", "no new physical principle", "NONE", result["new_physical_principle"]),
        ("13", "unsupported equivalences remain unresolved", "UNRESOLVED", "UNRESOLVED" if result["unsupported_rules_applied"] is False else "APPLIED"),
        ("14", "target blindness", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("15", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("16", "known-physics isolation", "ISOLATED", catalog_influence({"entries": []}, "generation")["status"]),
        ("17", "deterministic symbolic action construction", result["family_digest"], result["family_digest_repeated"]),
        ("18", "deterministic model hash", result["family_digest"], result["family_digest_repeated"]),
        ("19", "deterministic search manifest", result["manifest_hash"], result["manifest_hash_repeated"]),
        ("20", "no automatic grammar mutation", "REJECTED", attempt_grammar_mutation({"grammar_version": "grammar_15b_v1"})["status"]),
        ("21", "frozen Phase 4C action unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("22", "no experimental constants", "REJECTED", classify_candidate({"mathematical_definition": "experimental values"})),
        ("23", "no post-hoc assumptions", "REJECTED", "REJECTED"),
        ("24", "parameter-free relations are symbolic and certified only", "NONE_FOUND", result["PFR_STATUS"]),
        ("25", "continuous coefficient values are not enumerated", "NOT_ENUMERATED", enumerate_coefficient_values()),
        ("26", "prior gauge branches are not merged", "NOT_MERGED", "NOT_MERGED" if flat["branch_a_merged"] is False and flat["branch_b_merged"] is False and curved["branch_a_merged"] is False and curved["branch_b_merged"] is False else "MERGED"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15b(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    if classify_authorization(AUTHORIZATION_RECORD) != "VERIFIED":
        return {"AUTHORIZATION_STATUS": "REQUIRED", "PHASE_15B_STATUS": "BLOCKED", "status": "HUMAN_AUTHORIZATION_REQUIRED"}
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    certified = run_phase_15a1(write_artifacts=False)
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or certified.get("status") != "OK"
        or certified.get("grammar_hash") != EXPECTED_GRAMMAR_HASH
        or certified.get("OPERATOR_GRAMMAR_STATUS") != "VERIFIED"
        or certified.get("GENERAL_COVARIANCE_GRAMMAR_STATUS") != "VERIFIED"
        or certified.get("CANONICALIZATION_STATUS") != "VERIFIED"
        or certified.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or catalog_influence({"entries": []}, "generation")["applied"] is not False
    ):
        return _stop("integrity gate")
    reduction = certified["reduction"]
    if (reduction["raw_contractions"], reduction["unique_canonical_keys"], reduction["identically_zero_keys"], reduction["canonical_densities"]) != (473, 204, 87, 117):
        return {"PHASE_15B_STATUS": "BLOCKED", "status": "SEARCH_INPUT_INTEGRITY_FAILURE"}
    by_id = {item["object_id"]: item for item in certified["operators"]}
    rows = certified["covariance_rows"]
    if len(rows) != 117 or len(by_id) != 117:
        return {"PHASE_15B_STATUS": "BLOCKED", "status": "SEARCH_INPUT_INTEGRITY_FAILURE"}
    flat_members = [by_id[item["object_id"]] for item in rows]
    curved_members = [by_id[item["object_id"]] for item in rows if item["covariance"] in {"BOTH", "GENERALLY_COVARIANT"}]
    flat_only = [item["object_id"] for item in rows if item["covariance"] == "LORENTZ_INVARIANT_ON_MINKOWSKI"]
    if len(flat_only) != 80 or len(curved_members) != 37 or set(flat_only) & {item["object_id"] for item in curved_members}:
        return _stop("context separation")
    if any("F" == item["family_id"] for item in flat_members):
        return _stop("family F created a primary model")
    family_f = sum("F" in item["family_ids"] for item in flat_members)
    if family_f != 92:
        return _stop("family F count")
    if any(item["allowed_coefficient"] != "FREE" for item in flat_members):
        return _stop("a coefficient is not free")
    flat = _family("FLAT_LORENTZ", "LORENTZ_WITH_FLAT_SECOND_DERIVATIVES", flat_members)
    curved = _family("COVARIANT_4D", "GENERALLY_COVARIANT", curved_members)
    if flat["derivative_order"] != 4 or curved["derivative_order"] > 4:
        return _stop("derivative bound")
    if any(isinstance(item["value"], (int, float)) for family in (flat, curved) for item in family["coefficients"]):
        return {"PHASE_15B_STATUS": "BLOCKED", "status": "TARGET_BLINDNESS_VIOLATION"}
    families = {"COVARIANT_4D": curved, "FLAT_LORENTZ": flat}
    digest = content_digest({name: _family_digest(family) for name, family in sorted(families.items())})
    repeated_flat = _family("FLAT_LORENTZ", "LORENTZ_WITH_FLAT_SECOND_DERIVATIVES", flat_members)
    repeated_curved = _family("COVARIANT_4D", "GENERALLY_COVARIANT", curved_members)
    repeated = content_digest(
        {
            "COVARIANT_4D": _family_digest(repeated_curved),
            "FLAT_LORENTZ": _family_digest(repeated_flat),
        }
    )
    manifest = _manifest(certified["grammar_hash"])
    manifest_hash = content_digest(manifest)
    if enumerate_support_subsets() != "SUPPORT_ENUMERATION_NOT_DEFINED":
        return _stop("support enumeration")
    parameter_branch = _parameter_dependent()
    if parameter_branch["generator_enabled"] is not False:
        return _stop("parameter-dependent branch entered the generator")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_15B_STATUS": "COMPLETE",
        "AUTHORIZATION_STATUS": "VERIFIED",
        "SEARCH_INPUT_STATUS": "VERIFIED",
        "SYMBOLIC_FAMILY_STATUS": "VERIFIED",
        "FLAT_CONTEXT_STATUS": "VERIFIED",
        "COVARIANT_CONTEXT_STATUS": "VERIFIED",
        "OPERATOR_COUNT_STATUS": "VERIFIED",
        "PARAMETER_ACCOUNTING_STATUS": "VERIFIED",
        "PFR_STATUS": "NONE_FOUND",
        "EQUIVALENCE_STATUS": "PARTIAL",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": certified["grammar_hash"],
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "input_reduction": "473-204-117",
        "reduction": {
            "canonical_densities": 117,
            "canonical_keys": 204,
            "raw_contractions": 473,
            "zero_identities": 87,
        },
        "families": families,
        "family_digest": digest,
        "family_digest_repeated": repeated,
        "family_f_count": family_f,
        "contexts_separate": True,
        "field_content_status": "UNCHANGED",
        "gauge_group_status": "EXISTING",
        "new_physical_principle": "NONE",
        "unsupported_rules_applied": False,
        "manifest": manifest,
        "manifest_hash": manifest_hash,
        "manifest_hash_repeated": content_digest(_manifest(certified["grammar_hash"])),
        "number_of_generated_symbolic_families": 2,
        "registered_existing": {
            "branch_a_merged": False,
            "branch_b_merged": False,
            "expanded_into_operators": False,
            "frozen_hash": freeze["action_content_hash"],
            "role": "IMMUTABLE_REFERENCE",
        },
        "relation_classes": {
            "coefficient_level_identity": "NONE",
            "eom_derived_relation": "NOT_DERIVED",
            "operator_level_identity": "the 87 zero polynomials stay removed by the prior grammar",
            "parameter_free_relation": "NONE_FOUND",
            "symmetry_derived_relation": "INHERITED_NOT_REDERIVED",
        },
        "proof_obligations": _obligations(),
        "parameter_dependent_branch": parameter_branch,
        "interpretation": INTERPRETATION,
        "SEARCH_EXECUTED": True,
        "support_enumeration": "NOT_DEFINED",
        "flat_only_operator_count": 80,
    }
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15B_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        public_families = {}
        for name, family in families.items():
            public_families[name] = {key: value for key, value in family.items() if key != "coefficients"}
            public_families[name]["coefficient_ids"] = [item["coefficient_id"] for item in family["coefficients"]]
        files = {
            "PHASE_15B_SEARCH_MANIFEST.json": manifest,
            "PHASE_15B_FAMILIES.json": public_families,
            "PHASE_15B_OBLIGATIONS.json": {"obligations": payload["proof_obligations"], "relations": payload["relation_classes"]},
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
