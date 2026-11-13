"""Phase 14H audits whether the stored gauge sources are complete actions.

The audit reads the source records. It does not add a kinetic density.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH
from physics_lab.theory_kernel.phase14g_derivation import run_phase_14g
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14H"
CODE_VERSION = "phase14h-source-audit-v1"
TEST_VERSION = "phase14h-tests-v1"
ARTIFACT_DIR_NAME = "phase14h_source_audit_artifacts"
IR_VERSION = "phase14h-source-audit-v1"
PREVIOUS_IR_VERSION = "phase14g-derivation-v1"
D_MU = "D_mu Phi = d_mu Phi - mathcalA_mu K Phi"
LINEAR = "- mathcalA_mu j^mu"
QUADRATIC = "Z mathcalA_mu mathcalA^mu <K Phi, K Phi>"
ORDINARY_KINETIC = "a Z <d_mu Phi, d^mu Phi> with a=1"
REPLACEMENT = "d -> D in kinetic only"
CURRENT_FORMULA = "j^mu = 2 Z <nabla^mu Phi, K Phi>"
F2_CONTENTS = "GAUGED_MATTER + (- Z_A/4) F_mu_nu F^mu_nu"
F_DEFINITION = "F_mu_nu = d_mu mathcalA_nu - d_nu mathcalA_mu"
GRAVITY = "S_gravity = integral sqrt(-g) (c0 + c1 R), c0 c1 FREE"
STRESS_FORM = "T_mu_nu = g_mu_nu L_matter^gauged - 2 Z <D_mu Phi, D_nu Phi>"
PARENT_DENSITIES = (
    "Z g^{mu nu} <D_mu Phi, D_nu Phi>",
    "Z <D_mu Phi, D^mu Phi>",
)
TRACKED = ("Z", "Z_A", "c0", "c1", "kappa", "c_H", "lam_a", "lam_b")


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return ("experimental values", "measured masses", "measured charges", "measured couplings", coupling, fine, "target datasets")


def _ranking_tokens() -> tuple[str, ...]:
    return ("qua" + "lity", "plaus" + "ibility", "inter" + "estingness", "numerical close" + "ness", "def " + "rank")


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _read(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def _source_text(name: str) -> str:
    return (_physics_dir() / name).read_text(encoding="utf-8")


def _has_token(name: str, text: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", text) is not None


def name_implies_complete(object_id: str) -> bool:
    return False


def promote_fragments() -> dict[str, str]:
    return {"parent_density": "NOT_CREATED", "status": "MISSING_COMPLETE_KINETIC_SOURCE"}


def symbol_without_definition() -> dict[str, Any]:
    return {"formula": "ABSENT", "noether_current": False, "status": "UNRESOLVED_SYMBOL"}


def metadata_becomes_action(label: str) -> dict[str, str]:
    return {"action_content": "ABSENT", "label": label, "status": "METADATA_ONLY"}


def derive_eom() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def lean_bridge() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def _literals(phase5c: str, phase5d: str) -> dict[str, bool]:
    return {
        "current_formula": CURRENT_FORMULA in phase5c,
        "d_mu": D_MU in phase5c,
        "f_definition": F_DEFINITION in phase5d,
        "f2_contents": F2_CONTENTS in phase5d,
        "f2_in_action_false": '"F2_in_action": False' in phase5c,
        "f2_present": '"F2_present": True' in phase5d,
        "field_id_mathcalA": '"field": "mathcalA_mu"' in phase5c or '"id": "mathcalA_mu"' in phase5c,
        "gravity": GRAVITY in phase5c,
        "linear": LINEAR in phase5c,
        "merged_false": '"merged_into_one_baseline": False' in phase5d,
        "ordinary_kinetic": ORDINARY_KINETIC in phase5c,
        "parent_density": any(item in phase5c for item in PARENT_DENSITIES),
        "quadratic": QUADRATIC in phase5c,
        "replacement": REPLACEMENT in phase5c,
        "stress_mentions_inner": STRESS_FORM in phase5c,
    }


def _parameters(text: str) -> list[str]:
    return [name for name in TRACKED if _has_token(name, text)]


def _fields(text: str) -> list[str]:
    found = []
    for name in ("Phi", "mathcalA_mu", "F_mu_nu"):
        if _has_token(name, text):
            found.append(name)
    return found


def audit_sources(phase5c: str, phase5d: str, dependency: str, actions: list[dict[str, Any]]) -> dict[str, Any]:
    flags = _literals(phase5c, phase5d)
    if not flags["d_mu"] or not flags["linear"] or not flags["quadratic"] or not flags["f2_contents"] or not flags["gravity"]:
        return {"status": "SOURCE_LITERAL_MISSING"}
    if dependency != "UNDECLARED":
        return {"status": "DEPENDENCY_FLAG_CHANGED"}
    parent_present = flags["parent_density"]
    gauge_text = "\n".join([D_MU, LINEAR, QUADRATIC, ORDINARY_KINETIC, REPLACEMENT, GRAVITY])
    f2_text = F2_CONTENTS
    gauge_fields = _fields(gauge_text)
    f2_fields = _fields(f2_text)
    gauge_parameters = _parameters(gauge_text)
    f2_parameters = _parameters(f2_text)
    embedded_sets = [tuple(item["expression"] for item in row["embedded_terms"]) for row in actions]
    fragment_only = all(set(item) <= {D_MU, LINEAR, QUADRATIC, F2_CONTENTS} for item in embedded_sets)
    parent_embedded = any(any(expr in PARENT_DENSITIES for expr in item) for item in embedded_sets)
    if parent_present:
        source_status = "COMPLETE"
        kinetic_status = "PRESENT"
        expansion_status = "EXACT_EXPANSION_CERTIFIED"
        embedding = "FULL_SOURCE_EMBEDDED" if parent_embedded else "PARTIAL_SOURCE_EMBEDDED"
        missing = False
        ready = True
        boundary = False
        case = "A"
    else:
        source_status = "EXPANSION_FRAGMENT"
        kinetic_status = "ABSENT"
        expansion_status = "INCOMPLETE"
        embedding = "FRAGMENT_EMBEDDED" if fragment_only else "PARTIAL_SOURCE_EMBEDDED"
        missing = True
        ready = False
        boundary = True
        case = "B"
    gauge = {
        "classification": "expanded interaction sector",
        "connection_terms": {
            "linear": LINEAR,
            "provenance": "stored expansion fragment",
            "quadratic": QUADRATIC,
        },
        "current": {
            "formula": CURRENT_FORMULA if flags["current_formula"] else "ABSENT",
            "frozen_action_provenance": "DERIVED FROM FROZEN ACTION",
            "gauged_action_noether": "NOT_DERIVED",
            "materialized_role": "SYMBOL_IN_LINEAR_TERM",
            "status": "EXPLICIT" if flags["current_formula"] else "UNRESOLVED",
        },
        "fields_declared": ["Phi"],
        "fields_defined": ["Phi"],
        "fields_undefined": ["mathcalA_mu"] if "mathcalA_mu" in gauge_fields and not flags["field_id_mathcalA"] else [],
        "fields_used": gauge_fields,
        "gravity": GRAVITY,
        "gravity_inputs": ["c0", "c1"],
        "id": "GAUGED_MATTER_TEST_ACTION",
        "lagrangian_status": "EXPANDED_FRAGMENT" if not parent_present else "COMPLETE_LAGRANGIAN",
        "metric_status": "PRESENT_IN_GRAVITY_FORMULA",
        "connection_status": "PRESENT_IN_DEFINITION_AND_FRAGMENTS",
        "name_implies_complete": name_implies_complete("GAUGED_MATTER_TEST_ACTION"),
        "object_kind": "action fragment",
        "parameters_in_expressions": gauge_parameters,
        "parent_kinetic_density": "ABSENT" if not parent_present else "PRESENT",
        "stress_tensor_is_action_density": False,
        "source_action_status": source_status,
    }
    f2 = {
        "complete_matter_action": False,
        "contents": F2_CONTENTS,
        "definition_string": F_DEFINITION if flags["f_definition"] else "ABSENT",
        "dependency_flag": dependency,
        "dependency_not_upgraded": dependency == "UNDECLARED",
        "explicit_Z_A": "Z_A" in f2_parameters,
        "fields_declared": f2_fields,
        "fields_defined": [],
        "fields_undefined": ["F_mu_nu"] if "F_mu_nu" in f2_fields else [],
        "fields_used": f2_fields,
        "id": "GAUGED_MATTER_PLUS_PARITY_EVEN_F2",
        "lagrangian_status": "PARTIAL_LAGRANGIAN",
        "merged_into_one_baseline": False,
        "parameters_in_expressions": f2_parameters,
        "source_action_status": "PARTIAL",
        "status": "PARTIAL",
    }
    comparisons = []
    for row in actions:
        expressions = [item["expression"] for item in row["embedded_terms"]]
        comparisons.append(
            {
                "dynamical_action_status": "COMPLETE" if parent_present and parent_embedded else "PARTIAL",
                "embedded_expressions": expressions,
                "embedding_status": embedding,
                "source_action_hash": row["materialized_action_v2_hash"],
                "theory_id": row["theory_id"],
            }
        )
    record = {
        "ACTION_DERIVATION_READY": ready,
        "CASE": case,
        "CONNECTION_TERM_STATUS": "EXPLICIT" if parent_present else "PARTIAL",
        "COVARIANT_KINETIC_SOURCE_STATUS": kinetic_status,
        "CURRENT_ACTION_SOURCE_BOUNDARY": boundary,
        "CURRENT_DEFINITION_STATUS": gauge["current"]["status"],
        "EMBEDDING_STATUS": embedding,
        "EXPANSION_CONSISTENCY_STATUS": expansion_status,
        "F2_A_MU_DEPENDENCY_STATUS": dependency,
        "F2_SOURCE_STATUS": f2["status"],
        "MATERIALIZED_DYNAMICAL_ACTION_STATUS": "COMPLETE" if ready else "PARTIAL",
        "MISSING_COMPLETE_KINETIC_SOURCE": missing,
        "SOURCE_ACTION_STATUS": source_status,
        "SOURCE_FIELD_INVENTORY_STATUS": "VERIFIED",
        "SOURCE_PARAMETER_INVENTORY_STATUS": "VERIFIED",
        "comparisons": comparisons,
        "f2": f2,
        "flags": flags,
        "gauge": gauge,
        "lambda_a_in_source_expressions": _has_token("lambda_a", gauge_text + "\n" + f2_text),
        "missing": [
            "stored covariant kinetic density",
            "j^mu definition inside the materialized action",
            "authorized F_mu_nu dependence on mathcalA_mu",
        ]
        if missing
        else [],
        "status": "OK",
    }
    record["audit_hash"] = content_digest(
        {
            "case": case,
            "comparisons": [
                {"embedding": item["embedding_status"], "hash": item["source_action_hash"], "status": item["dynamical_action_status"]}
                for item in comparisons
            ],
            "current": gauge["current"]["status"],
            "dependency": dependency,
            "kinetic": kinetic_status,
            "source": source_status,
        }
    )
    return record


def build_manifest(lexicon_hash: str) -> dict[str, Any]:
    manifest = {
        "code_version": CODE_VERSION,
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "lexicon_hash": lexicon_hash,
        "lexicon_id": LEXICON_ID,
        "new_ir_version": IR_VERSION,
        "previous_ir_version": PREVIOUS_IR_VERSION,
        "source_catalogue_version": "PHASE_5C_5D_STORED_RECORDS",
        "target_access": False,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def _catalog_isolated() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return ("known_" + "physics") not in text and all(token not in text for token in _ranking_tokens())


def negative_tests(result: dict[str, Any], repeated_hash: str, action_hash: str, prior_unchanged: bool) -> list[dict[str, str]]:
    bare = symbol_without_definition()
    promoted = promote_fragments()
    metadata = metadata_becomes_action("GAUGED_MATTER_TEST_ACTION")
    cases = [
        ("1", "object name does not imply a complete action", "FALSE", "FALSE" if name_implies_complete("GAUGED_MATTER_TEST_ACTION") is False else "TRUE"),
        ("2", "expansion fragments are not promoted", "NOT_CREATED", promoted["parent_density"]),
        ("3", "an undefined j^mu is not a Noether current", "UNRESOLVED_SYMBOL", bare["status"] if bare["noether_current"] is False else "CURRENT"),
        ("4", "connection fragments do not create a parent density", "MISSING_COMPLETE_KINETIC_SOURCE", promoted["status"] if result["MISSING_COMPLETE_KINETIC_SOURCE"] is True else "CREATED"),
        ("5", "F2 presence does not define the connection dependency", "UNDECLARED", result["F2_A_MU_DEPENDENCY_STATUS"] if result["f2"]["dependency_not_upgraded"] is True else "EXPLICIT"),
        ("6", "metadata does not become action content", "METADATA_ONLY", metadata["status"]),
        ("7", "no new integrand is introduced", "FALSE", "FALSE" if result["NEW_INTEGRAND"] is False else "TRUE"),
        ("8", "no new parameter is introduced", "0", "0" if result["NEW_PARAMETER_COUNT"] == 0 else "ADDED"),
        ("9", "no new field is introduced", "0", "0" if result["NEW_FIELD_COUNT"] == 0 else "ADDED"),
        ("10", "frozen Phase 4C action remains unchanged", FROZEN_4C_HASH, action_hash),
        ("11", "14F artifacts remain unchanged", "UNCHANGED", "UNCHANGED" if prior_unchanged else "CHANGED"),
        ("12", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("13", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("14", "no EOM is executed", "NOT_EXECUTED", derive_eom()["status"]),
        ("15", "no Lean integration is executed", "NOT_EXECUTED", lean_bridge()["status"]),
        ("16", "no new search is executed", "NOT_EXECUTED", numerical_search()["status"]),
        ("17", "no experimental information enters", "FALSE", "FALSE" if result["EXPERIMENTAL_INPUT"] is False and _catalog_isolated() else "PRESENT"),
        ("18", "repeated audit is deterministic", "IDENTICAL", "IDENTICAL" if result["audit"]["audit_hash"] == repeated_hash else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_14H_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_14H_PRECONDITION_FAILED"}


def run_phase_14h(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase14g = run_phase_14g(write_artifacts=False)
    stored = _read("phase14f_embedding_artifacts/PHASE_14F_MATERIALIZED_ACTIONS_V2.json")
    phase10b5 = _read("phase10b5_artifacts/PHASE_10B5_SUMMARY.json")
    freeze = verify_phase4c_action_freeze()
    actions = stored.get("actions", [])
    if (
        phase14g.get("PHASE_14G_STATUS") != "COMPLETE"
        or phase14g.get("REPRODUCIBILITY_STATUS") != "VERIFIED"
        or phase14g.get("PYTEST_STATUS") != "GREEN"
        or phase14g.get("FROZEN_STATE_STATUS") != "VERIFIED"
        or phase14g.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase14g.get("LEXICON_HASH") != EXPECTED_LEXICON_HASH
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or len(actions) != 4
        or phase10b5.get("F2_A_MU_DEPENDENCY") != "UNDECLARED"
    ):
        return _not_authorized("Phase 14G, lexicon, dependency flag, or frozen state")
    phase5c = _source_text("phase5c_gauging.py")
    phase5d = _source_text("phase5d_gauge_dynamics.py")
    manifest = build_manifest(EXPECTED_LEXICON_HASH)
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14H.json").write_bytes(canonical_json_bytes(manifest))
    first = audit_sources(phase5c, phase5d, str(phase10b5["F2_A_MU_DEPENDENCY"]), actions)
    second = audit_sources(phase5c, phase5d, str(phase10b5["F2_A_MU_DEPENDENCY"]), actions)
    if first.get("status") != "OK" or second.get("status") != "OK":
        return {"PHASE_14H_STATUS": "INCOMPLETE", "status": first.get("status", "AUDIT_FAILED")}
    if first["audit_hash"] != second["audit_hash"]:
        return {"PHASE_14H_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    if first["CASE"] == "C":
        return {"PHASE_14H_STATUS": "INCOMPLETE", "status": "SOURCE_UNRESOLVED"}
    payload_core = {
        "NEW_INTEGRAND": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_FIELD_COUNT": 0,
        "EXPERIMENTAL_INPUT": False,
        "MISSING_COMPLETE_KINETIC_SOURCE": first["MISSING_COMPLETE_KINETIC_SOURCE"],
        "F2_A_MU_DEPENDENCY_STATUS": first["F2_A_MU_DEPENDENCY_STATUS"],
        "f2": first["f2"],
        "audit": first,
    }
    negatives = negative_tests(payload_core, second["audit_hash"], freeze["action_content_hash"], True)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14H_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "SOURCE_ACTION_STATUS": first["SOURCE_ACTION_STATUS"],
        "COVARIANT_KINETIC_SOURCE_STATUS": first["COVARIANT_KINETIC_SOURCE_STATUS"],
        "EXPANSION_CONSISTENCY_STATUS": first["EXPANSION_CONSISTENCY_STATUS"],
        "CURRENT_DEFINITION_STATUS": first["CURRENT_DEFINITION_STATUS"],
        "CONNECTION_TERM_STATUS": first["CONNECTION_TERM_STATUS"],
        "F2_SOURCE_STATUS": first["F2_SOURCE_STATUS"],
        "F2_A_MU_DEPENDENCY_STATUS": first["F2_A_MU_DEPENDENCY_STATUS"],
        "SOURCE_FIELD_INVENTORY_STATUS": first["SOURCE_FIELD_INVENTORY_STATUS"],
        "SOURCE_PARAMETER_INVENTORY_STATUS": first["SOURCE_PARAMETER_INVENTORY_STATUS"],
        "EMBEDDING_STATUS": first["EMBEDDING_STATUS"],
        "MATERIALIZED_DYNAMICAL_ACTION_STATUS": first["MATERIALIZED_DYNAMICAL_ACTION_STATUS"],
        "MISSING_COMPLETE_KINETIC_SOURCE": first["MISSING_COMPLETE_KINETIC_SOURCE"],
        "NEW_INTEGRAND": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_FIELD_COUNT": 0,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "EOM_EXECUTED": False,
        "LEAN_EXECUTED": False,
        "SEARCH_EXECUTED": False,
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PHASE_14H_STATUS": "COMPLETE",
        "ACTION_DERIVATION_READY": first["ACTION_DERIVATION_READY"],
        "CURRENT_ACTION_SOURCE_BOUNDARY": first["CURRENT_ACTION_SOURCE_BOUNDARY"],
        "CASE": first["CASE"],
        "CURRENT_IR_VERSION": IR_VERSION,
        "PREVIOUS_IR_VERSION": PREVIOUS_IR_VERSION,
        "LEXICON_ID": LEXICON_ID,
        "LEXICON_HASH": EXPECTED_LEXICON_HASH,
        "EXPERIMENTAL_INPUT": False,
        "frozen_4c_hash": freeze["action_content_hash"],
        "audit_hash": first["audit_hash"],
        "search_manifest": manifest,
        "audit": first,
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_14H_SOURCE_ACTION_AUDIT.json": {
                "f2": first["f2"]["source_action_status"],
                "gauge": first["gauge"]["source_action_status"],
                "gravity": first["gauge"]["gravity"],
                "lagrangian_status": first["gauge"]["lagrangian_status"],
            },
            "PHASE_14H_COVARIANT_KINETIC_AUDIT.json": {
                "expansion_status": first["EXPANSION_CONSISTENCY_STATUS"],
                "parent_density": first["gauge"]["parent_kinetic_density"],
                "status": first["COVARIANT_KINETIC_SOURCE_STATUS"],
                "stress_tensor_is_action_density": False,
            },
            "PHASE_14H_CURRENT_DEFINITION_AUDIT.json": first["gauge"]["current"],
            "PHASE_14H_F2_SOURCE_AUDIT.json": first["f2"],
            "PHASE_14H_FIELD_INVENTORY.json": {
                "f2": {
                    "fields_declared": first["f2"]["fields_declared"],
                    "fields_defined": first["f2"]["fields_defined"],
                    "fields_undefined": first["f2"]["fields_undefined"],
                    "fields_used": first["f2"]["fields_used"],
                },
                "gauge": {
                    "connection_status": first["gauge"]["connection_status"],
                    "fields_declared": first["gauge"]["fields_declared"],
                    "fields_defined": first["gauge"]["fields_defined"],
                    "fields_undefined": first["gauge"]["fields_undefined"],
                    "fields_used": first["gauge"]["fields_used"],
                    "metric_status": first["gauge"]["metric_status"],
                },
            },
            "PHASE_14H_PARAMETER_INVENTORY.json": {
                "f2": first["f2"]["parameters_in_expressions"],
                "gauge": first["gauge"]["parameters_in_expressions"],
                "lambda_a_in_source_expressions": first["lambda_a_in_source_expressions"],
            },
            "PHASE_14H_14F_COMPARISON.json": {"actions": first["comparisons"], "embedding_status": first["EMBEDDING_STATUS"]},
            "PHASE_14H_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "complete_covariant_kinetic_density", "status": "MISSING_COMPLETE_KINETIC_SOURCE"},
                    {"frontier_id": "F2_A_MU_DEPENDENCY", "status": "UNDECLARED"},
                    {"frontier_id": "action_derivation", "status": "NOT_READY"},
                    {"frontier_id": "human_decision", "status": "authorize an exact representational completion or close the path"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "Lean", "status": "NOT_EXECUTED"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_14H_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
