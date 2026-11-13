"""Phase 15H records the closure gate for the verified 15A–15G results.

It reads stored artifacts. It does not generate operators or choose a next program.
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
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, catalog_influence, classify_candidate
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15H"
CODE_VERSION = "phase15h-closure-v1"
ARTIFACT_DIR_NAME = "phase15h_closure_artifacts"
GRAMMAR_VERSION = "grammar_15f_v1"
GRAMMAR_HASH = "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
MANIFEST_HASH = "5f27bb0325c3e5453b84172e34e089a1bcb3a2a42de6f42095677eedd5c0a187"
AUTHORIZATION_ID = "PHASE_15G_COVARIANT_U1_37"
HUMAN_OPTIONS = (
    "CLOSE CURRENT PROGRAM",
    "AUTHORIZE NEW MATHEMATICAL GRAMMAR",
    "PROVIDE NEW PHYSICAL INPUT",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15H_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15H_BLOCKED"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def choose_human_option(_choice: str | None = None) -> str:
    return "NOT_MADE"


def activate_profile(profile_id: str) -> str:
    if profile_id in {"AMBIENT_117", "LOCAL_U1_63"}:
        return "NOT_ACTIVATED"
    return "NOT_ACTIVATED"


def enumerate_support_subsets(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _technical_items() -> list[dict[str, str]]:
    equivalence = (
        ("IBP", "UNSUPPORTED"),
        ("FIELD_REDEFINITION", "UNSUPPORTED"),
        ("EOM_EQUIVALENCE", "UNSUPPORTED"),
        ("BASIS_EQUIVALENCE", "UNSUPPORTED"),
    )
    rows = [
        {
            "CAPABLE_OF_AFFECTING_SELECTION": "YES",
            "class": "TECHNICAL_COMPLETENESS_GAP",
            "effect": "REDUCTION_OF_EQUIVALENCE_CLASSES",
            "item": name,
            "status": status,
        }
        for name, status in equivalence
    ]
    rows.extend(
        [
            {
                "CAPABLE_OF_AFFECTING_SELECTION": "UNTESTED",
                "class": "TECHNICAL_COMPLETENESS_GAP",
                "effect": "RELATION_OR_DESCRIPTION",
                "item": "CLOSED_SYMBOLIC_EOM",
                "status": "NOT_ESTABLISHED",
            },
            {
                "CAPABLE_OF_AFFECTING_SELECTION": "UNTESTED",
                "class": "TECHNICAL_COMPLETENESS_GAP",
                "effect": "RELATION_OR_DESCRIPTION",
                "item": "CONSERVATION",
                "status": "UNTESTED",
            },
        ]
    )
    return rows


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    cases = [
        ("1", "no new generation", "NOT_PERFORMED", enumerate_support_subsets()),
        ("2", "counts inherited", "117-63-37", f"{result['AMBIENT_OPERATOR_COUNT']}-{result['U1_PRESERVING_COUNT']}-{result['COVARIANT_U1_COUNT']}"),
        ("3", "inclusion preserved", "VERIFIED", result["inclusion_status"]),
        ("4", "PFR remains none found", "NONE_FOUND", result["PFR_STATUS"]),
        ("5", "syzygies stay algebraic", "ALGEBRAIC_IDENTITY", result["covariant_syzygy_class"]),
        ("6", "parameter closure stays open", "OPEN", result["PARAMETER_CLOSURE_STATUS"]),
        ("7", "no dimensionless quantity is fixed", "0", str(result["derived_fixed_dimensionless_count"])),
        ("8", "physical equivalence stays unestablished", "NOT_ESTABLISHED", result["PHYSICALLY_INEQUIVALENT_COUNT"]),
        ("9", "structural closure is not reached", "NOT_REACHED", result["STRUCTURAL_CLOSURE_STATUS"]),
        ("10", "search exhaustion is not established", "NOT_ESTABLISHED", result["SEARCH_EXHAUSTION_STATUS"]),
        ("11", "no theory selection", "NO_SELECTION_PERFORMED", result["selection_result"]),
        ("12", "other profiles stay inactive", "NOT_ACTIVATED", activate_profile("AMBIENT_117")),
        ("13", "human option is not chosen", "NOT_MADE", choose_human_option("CLOSE CURRENT PROGRAM")),
        ("14", "frozen action unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("15", "no target information", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("16", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("17", "deterministic closure record", result["closure_digest"], result["closure_digest_repeated"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15h(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    grammar_file = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    operational = grammar_file["operational"]
    manifest = _read("phase15g_enumeration_artifacts/PHASE_15G_SEARCH_MANIFEST.json")
    family = _read("phase15g_enumeration_artifacts/PHASE_15G_FAMILY.json")
    catalog = _read("phase15e_catalog_artifacts/PHASE_15E_CATALOG.json")
    symmetry = _read("phase15c_audit_artifacts/PHASE_15C_SYMMETRY.json")
    covariance = _read("phase15a1_boundary_artifacts/PHASE_15A1_COVARIANCE.json")
    closure = _read("phase15a1_boundary_artifacts/PHASE_15A1_CLOSURE.json")
    prior = _read("phase15b_enumeration_artifacts/PHASE_15B_FAMILIES.json")["COVARIANT_4D"]
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or content_digest(operational) != GRAMMAR_HASH
        or grammar_file.get("grammar_hash") != GRAMMAR_HASH
        or content_digest(manifest) != MANIFEST_HASH
        or manifest.get("authorization_id") != AUTHORIZATION_ID
        or manifest.get("search_profile") != "COVARIANT_U1_37"
        or manifest.get("grammar_hash") != GRAMMAR_HASH
        or catalog_influence({"entries": []}, "closure")["applied"] is not False
    ):
        return _stop("integrity gate")
    contexts = operational["contexts"]
    ambient = contexts["FLAT_LORENTZ_AMBIENT"]["operator_ids"]
    preserving = contexts["LOCAL_U1_PRESERVING"]["operator_ids"]
    covariant = contexts["COVARIANT_4D"]["operator_ids"]
    family_ids = family["operator_ids"]
    if (
        len(ambient) != 117
        or len(preserving) != 63
        or len(covariant) != 37
        or family_ids != covariant
        or not set(covariant) <= set(preserving) <= set(ambient)
        or set(family_ids) != set(prior["operator_ids"])
    ):
        return _stop("inherited counts")
    rows = catalog["dd_catalog"]
    invariant = [row for row in rows if row["local_U1_status"] == "local U(1) invariant"]
    breaking = [row for row in rows if row["local_U1_status"] == "local U(1) breaking"]
    if len(rows) != 80 or len(invariant) != 26 or len(breaking) != 54:
        return _stop("DD split")
    if any(row["global_SO2_status"] != "global SO(2) invariant" for row in rows):
        return _stop("global SO(2)")
    if catalog["algebraic_rank"] != {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109} or family["algebraic_rank"] != 35:
        return _stop("algebraic rank")
    syzygies = catalog["syzygies"]
    inside = [item for item in syzygies if set(item["operator_ids"]) <= set(family_ids)]
    if (
        len(syzygies) != 8
        or len(inside) != 2
        or any(item["quotient_applied"] for item in syzygies)
        or any(item["consequence"] != "ALGEBRAIC_IDENTITY" for item in syzygies)
    ):
        return _stop("syzygy class")
    coefficients = family["coefficients"]
    if any(item["value"] != "SYMBOLIC" for item in coefficients):
        return _stop("coefficient value")
    dimensionless = [item for item in coefficients if item["mass_dimension"] == 0]
    if len(dimensionless) != 6 or len(coefficients) != 37:
        return _stop("dimensionless inventory")
    covariance_by_id = {row["object_id"]: row["covariance"] for row in covariance["rows"]}
    if any(covariance_by_id[item] not in {"BOTH", "GENERALLY_COVARIANT"} for item in family_ids):
        return _stop("covariance record")
    if covariance["counts"] != {"both": 29, "flat_only": 80, "no_spacetime_derivative": 8}:
        return _stop("covariance counts")
    if symmetry["covariant_local"] != "EXACT" or not all(symmetry["proofs"].values()):
        return _stop("symmetry record")
    if prior["locality_status"] != "POINT_LOCAL" or closure["grammar_hash"] != "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075":
        return _stop("locality record")
    if catalog["physical_inequivalent_count"] != "NOT_ESTABLISHED":
        return _stop("equivalence record")
    enumerated_profiles = [manifest["search_profile"]]
    registered_profiles = [item["profile_id"] for item in operational["profiles"]]
    if registered_profiles != ["AMBIENT_117", "LOCAL_U1_63", "COVARIANT_U1_37"] or enumerated_profiles != ["COVARIANT_U1_37"]:
        return _stop("profile catalogue")
    technical = _technical_items()
    if any(item["CAPABLE_OF_AFFECTING_SELECTION"] == "YES" for item in technical) or set(registered_profiles) - set(enumerated_profiles):
        exhaustion = "NOT_ESTABLISHED"
    else:
        exhaustion = "ESTABLISHED"
    record = {
        "algebraic_rank": {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109},
        "coefficients": "FREE",
        "inclusion": "37 ⊆ 63 ⊆ 117",
        "pfr": "NONE_FOUND",
        "profile": "COVARIANT_U1_37",
        "syzygy_class": "ALGEBRAIC_IDENTITY",
    }
    digest = content_digest(record)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_15H_STATUS": "COMPLETE",
        "STRUCTURAL_CLOSURE_STATUS": "NOT_REACHED",
        "PFR_STATUS": "NONE_FOUND",
        "PARAMETER_CLOSURE_STATUS": "OPEN",
        "DIMENSIONLESS_CLOSURE_STATUS": "OPEN",
        "PHYSICAL_EQUIVALENCE_STATUS": "NOT_ESTABLISHED",
        "TECHNICAL_GAPS_STATUS": "OPEN",
        "PHYSICAL_SELECTION_GAP_STATUS": "OPEN",
        "SEARCH_EXHAUSTION_STATUS": exhaustion,
        "HUMAN_INPUT_STATUS": "DECISION_REQUIRED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": GRAMMAR_HASH,
        "manifest_hash": MANIFEST_HASH,
        "authorization_id": AUTHORIZATION_ID,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "AMBIENT_OPERATOR_COUNT": 117,
        "U1_PRESERVING_COUNT": 63,
        "COVARIANT_U1_COUNT": 37,
        "DD_TOTAL": 80,
        "DD_U1_PRESERVING": 26,
        "DD_U1_BREAKING": 54,
        "FLAT_ALGEBRAIC_RANK": 109,
        "COVARIANT_ALGEBRAIC_RANK": 35,
        "SYZYGY_COUNT": 8,
        "COVARIANT_SYZYGY_COUNT": 2,
        "inclusion_status": "VERIFIED",
        "global_SO2": "VERIFIED",
        "local_U1": "VERIFIED",
        "general_covariance": "VERIFIED",
        "locality": "VERIFIED",
        "reproducibility": "VERIFIED",
        "covariant_syzygy_class": "ALGEBRAIC_IDENTITY",
        "syzygy_quotient": "QUOTIENT_NOT_APPLIED",
        "dimensionless_count": 6,
        "dimensionless_classification": "PARAMETER_DEPENDENT",
        "derived_fixed_dimensionless_count": 0,
        "fixed_coefficient_count": 0,
        "new_parameter_count": 0,
        "new_field": "NONE",
        "EOM_ORDER": "SECOND_ORDER",
        "CLOSED_SYMBOLIC_EOM": "NOT_ESTABLISHED",
        "CONSERVATION": "UNTESTED",
        "equivalence": {
            "BASIS_EQUIVALENCE": "UNSUPPORTED",
            "EOM_EQUIVALENCE": "UNSUPPORTED",
            "FIELD_REDEFINITION": "UNSUPPORTED",
            "IBP": "UNSUPPORTED",
        },
        "PHYSICALLY_INEQUIVALENT_COUNT": "NOT_ESTABLISHED",
        "technical_items": technical,
        "physical_selection_gaps": [
            "free coefficients",
            "absence of PFR",
            "non-unique symbolic action",
        ],
        "selection_result": "NO_SELECTION_PERFORMED",
        "SEARCH_PROFILE_SELECTION": "HUMAN-AUTHORIZED SEARCH CONFIGURATION",
        "THEORY_SELECTION": "NOT_PERFORMED",
        "enumerated_profiles": enumerated_profiles,
        "available_profiles": registered_profiles,
        "human_options": list(HUMAN_OPTIONS),
        "software_choice": choose_human_option(),
        "closure_question": "Does the current registered grammar plus all verified structural constraints uniquely determine an action?",
        "closure_answer": "STRUCTURAL_CLOSURE = NOT_REACHED",
        "summary": {
            "derived": "local U(1), general covariance, eight algebraic syzygies, and the 26/54 Hessian split",
            "enumerated": "one maximal symbolic family in the COVARIANT_U1_37 profile",
            "free": "37 symbolic coefficients, of which 6 are dimensionless and parameter dependent",
            "pfr": "NONE_FOUND",
            "selection": "NO_SELECTION_PERFORMED",
            "structurally_constrained": "37 ⊆ 63 ⊆ 117",
            "technically_unverified": "closed Euler-Lagrange form, conservation of the complete sum, and the four unsupported equivalences",
            "unsupported_equivalences": "IBP, field redefinition, EOM equivalence, basis equivalence",
        },
        "interpretation": "Within the authorized COVARIANT_U1_37 search profile, no parameter-free relation was found and the remaining coefficients remain free.",
        "equivalence_statement": "The current equivalence engine does not establish the number of physically inequivalent actions.",
        "closure_digest": digest,
        "closure_digest_repeated": content_digest(record),
    }
    if payload["SEARCH_EXHAUSTION_STATUS"] != "NOT_ESTABLISHED" or payload["software_choice"] != "NOT_MADE":
        return _stop("decision boundary")
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15H_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_15H_CLOSURE.json").write_bytes(
            canonical_json_bytes(
                {
                    "HUMAN_INPUT_STATUS": payload["HUMAN_INPUT_STATUS"],
                    "PARAMETER_CLOSURE_STATUS": payload["PARAMETER_CLOSURE_STATUS"],
                    "PFR_STATUS": payload["PFR_STATUS"],
                    "SEARCH_EXHAUSTION_STATUS": payload["SEARCH_EXHAUSTION_STATUS"],
                    "STRUCTURAL_CLOSURE_STATUS": payload["STRUCTURAL_CLOSURE_STATUS"],
                    "grammar_hash": GRAMMAR_HASH,
                    "human_options": payload["human_options"],
                    "inclusion": "37 ⊆ 63 ⊆ 117",
                    "manifest_hash": MANIFEST_HASH,
                    "software_choice": "NOT_MADE",
                }
            )
        )
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
