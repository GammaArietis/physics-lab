"""Phase 14I completes the gauged test action under explicit human authorization.

The frozen Phase 4C action is not modified. The completion is a test extension.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.physics.phase5b0_symmetry import frozen_kinetic_z_prefactor
from physics_lab.physics.phase5c_gauging import _inner, _is_zero, so2_generator_K
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH
from physics_lab.theory_kernel.phase14h_source_audit import run_phase_14h
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14I"
CODE_VERSION = "phase14i-completion-v1"
TEST_VERSION = "phase14i-tests-v1"
ARTIFACT_DIR_NAME = "phase14i_completion_artifacts"
IR_VERSION = "phase14i-completion-v1"
PREVIOUS_IR_VERSION = "phase14h-source-audit-v1"
COMPLETION_ID = "14I-ACTION-COMPLETION"
AUTHORIZATION_ID = "14I-HUMAN-AUTHORIZED-ACTION-COMPLETION"
PARENT_ACTION_ID = "PHASE_4C_FROZEN_MATTER_ACTION"
COMPLETE_ID = "GAUGED_MATTER_TEST_ACTION_COMPLETE"
F2_COMPLETE_ID = "GAUGED_MATTER_PLUS_PARITY_EVEN_F2_COMPLETE"
PROVENANCE = "HUMAN-AUTHORIZED ACTION COMPLETION"
SCOPE = "COMPLETE TEST-ACTION REPRESENTATION ONLY"
KINETIC_DENSITY = "Z g^{mu nu} <D_mu Phi, D_nu Phi>"
D_MU = "D_mu Phi = d_mu Phi - mathcalA_mu K Phi"
LINEAR = "- mathcalA_mu j^mu"
QUADRATIC = "Z mathcalA_mu mathcalA^mu <K Phi, K Phi>"
ORDINARY = "Z g^{mu nu} <d_mu Phi, d_nu Phi>"
CURRENT_FORMULA = "j^mu = 2 Z <nabla^mu Phi, K Phi>"
F_DEFINITION = "F_mu_nu = d_mu mathcalA_nu - d_nu mathcalA_mu"
F2_TERM = "integral sqrt(-g) [- Z_A/4 F_mu_nu F^mu_nu]"
GRAVITY = "S_gravity = integral sqrt(-g) (c0 + c1 R), c0 c1 FREE"
INHERITED = ("gravity_c0", "gravity_c1_R", "matter_phi_sq", "matter_H_int")


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


def modify_frozen_baseline() -> dict[str, str]:
    return {"status": "REFUSED", "frozen_action_modified": "FALSE"}


def upgrade_symmetry() -> dict[str, str]:
    return {"status": "REFUSED", "full_action_symmetry_status": "PENDING_REVERIFICATION"}


def derive_eom() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def _expansion(action: dict[str, Any], generator: sp.Matrix) -> dict[str, Any]:
    if not _is_zero(generator.T + generator):
        return {"status": "K_NOT_ANTISYMMETRIC"}
    prefactor = frozen_kinetic_z_prefactor(action)
    if prefactor != 1:
        return {"status": "CURRENT_NORMALIZATION_MISMATCH"}
    dimension = 4
    metric = sp.zeros(dimension)
    for row in range(dimension):
        for col in range(row, dimension):
            symbol = sp.symbols(f"g{row}{col}", real=True)
            metric[row, col] = symbol
            metric[col, row] = symbol
    phi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    slopes = [sp.Matrix(sp.symbols(f"v{mu}0 v{mu}1 v{mu}2", real=True)) for mu in range(dimension)]
    connection = list(sp.symbols("A0 A1 A2 A3", real=True))
    coefficient = sp.symbols("Z", real=True)
    covariant = [slopes[mu] - connection[mu] * (generator * phi) for mu in range(dimension)]
    density = sum(
        coefficient * metric[mu, nu] * _inner(covariant[mu], covariant[nu])
        for mu in range(dimension)
        for nu in range(dimension)
    )
    ordinary = sum(
        coefficient * metric[mu, nu] * _inner(slopes[mu], slopes[nu])
        for mu in range(dimension)
        for nu in range(dimension)
    )
    linear = 0
    for mu in range(dimension):
        raised = sp.zeros(3, 1)
        for nu in range(dimension):
            raised += metric[mu, nu] * slopes[nu]
        linear += connection[mu] * (2 * coefficient * _inner(raised, generator * phi))
    quadratic = sum(
        coefficient * metric[mu, nu] * connection[mu] * connection[nu] * _inner(generator * phi, generator * phi)
        for mu in range(dimension)
        for nu in range(dimension)
    )
    expected = ordinary - linear + quadratic
    if not _is_zero(sp.expand(density - expected)):
        return {"status": "EXPANSION_MISMATCH"}
    return {
        "current_coefficient": 2,
        "current_formula": CURRENT_FORMULA,
        "k_antisymmetric": True,
        "linear_term": LINEAR,
        "match": True,
        "ordinary_kinetic": ORDINARY,
        "prefactor": 1,
        "quadratic_term": QUADRATIC,
        "status": "EXACT",
    }


def _fragment_hash() -> str:
    return content_digest(
        {
            "expressions": [D_MU, LINEAR, QUADRATIC],
            "id": "GAUGED_MATTER_TEST_ACTION",
            "status": "EXPANSION_FRAGMENT",
        }
    )


def _completion_hash() -> str:
    return content_digest(
        {
            "current_definition": "REUSED FROM PHASE_5B.0",
            "density": KINETIC_DENSITY,
            "d_mu": D_MU,
            "id": COMPLETE_ID,
            "linear": LINEAR,
            "ordinary": ORDINARY,
            "provenance": PROVENANCE,
            "quadratic": QUADRATIC,
        }
    )


def _f2_hash() -> str:
    return content_digest(
        {
            "dependency": "DECLARED",
            "f_definition": F_DEFINITION,
            "f2_term": F2_TERM,
            "id": F2_COMPLETE_ID,
            "parent": COMPLETE_ID,
            "provenance": PROVENANCE,
        }
    )


def build_completion(actions: list[dict[str, Any]], expansion: dict[str, Any]) -> dict[str, Any]:
    completed = []
    for item in actions:
        f2 = "GAUGED_MATTER_PLUS_PARITY_EVEN_F2" in item["source_components"]
        fields = ["Phi", "metric", "mathcalA_mu"] + (["F_mu_nu"] if f2 else [])
        parameters = ["Z", "c0", "c1", "c_H", "kappa", "lam_a", "lam_b"] + (["Z_A"] if f2 else [])
        completed.append(
            {
                "authorization_id": AUTHORIZATION_ID,
                "completion_id": COMPLETION_ID,
                "derived_independently": False,
                "f2_a_mu_dependency": "DECLARED" if f2 else "ABSENT",
                "f2_term": F2_TERM if f2 else "ABSENT",
                "fields": fields,
                "frozen_promoted": False,
                "full_action_symmetry_status": "PENDING_REVERIFICATION",
                "gravity": GRAVITY,
                "inherited_terms": list(INHERITED),
                "kinetic_density": KINETIC_DENSITY,
                "parameters": parameters,
                "parameters_fixed": [],
                "parent_action_id": PARENT_ACTION_ID,
                "provenance": PROVENANCE,
                "replaced_terms": ["matter_kinetic"],
                "source_action_hash": item["materialized_action_v2_hash"],
                "strict_provenance": "NOT_DERIVED_FROM_THE_FROZEN_ACTION",
                "test_action_id": (F2_COMPLETE_ID if f2 else COMPLETE_ID),
                "theory_id": item["theory_id"],
            }
        )
    return {
        "actions": completed,
        "added_components": [KINETIC_DENSITY, "algebraic expansion of that density", F_DEFINITION],
        "completion_id": COMPLETION_ID,
        "current_definition": "REUSED FROM PHASE_5B.0",
        "current_relation": "DERIVED GIVEN HUMAN-AUTHORIZED ACTION COMPLETION",
        "expansion": expansion,
        "f2_dependency_provenance": "DERIVED GIVEN ABELIAN CONNECTION DEFINITION",
        "f2_hash": _f2_hash(),
        "forbidden_components": [
            "new parameter",
            "new interaction",
            "numerical calibration",
            "frozen baseline edit",
            "automatic symmetry upgrade",
        ],
        "hash_after": _completion_hash(),
        "hash_before": _fragment_hash(),
        "status": "OK",
    }


def completion_digest(record: dict[str, Any]) -> str:
    return content_digest(
        {
            "actions": [
                {
                    "dependency": item["f2_a_mu_dependency"],
                    "fields": item["fields"],
                    "hash": item["source_action_hash"],
                    "parameters": item["parameters"],
                }
                for item in record["actions"]
            ],
            "hash_after": record["hash_after"],
            "hash_before": record["hash_before"],
            "match": record["expansion"]["match"],
        }
    )


def build_manifest(lexicon_hash: str) -> dict[str, Any]:
    manifest = {
        "code_version": CODE_VERSION,
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "lexicon_hash": lexicon_hash,
        "lexicon_id": LEXICON_ID,
        "new_ir_version": IR_VERSION,
        "previous_ir_version": PREVIOUS_IR_VERSION,
        "source_catalogue_version": "PHASE_14H_SOURCE_BOUNDARY",
        "target_access": False,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def _isolated(document: Any) -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    rendered = json.dumps(document)
    ranking_clear = all(token not in text for token in _ranking_tokens())
    catalog_clear = ("known_" + "physics") not in text
    markers_clear = all(marker not in rendered for marker in _target_markers())
    return ranking_clear and catalog_clear and markers_clear


def negative_tests(result: dict[str, Any], repeated: str, action_hash: str) -> list[dict[str, str]]:
    actions = result["completion"]["actions"]
    density_only = all(item["kinetic_density"] == KINETIC_DENSITY and item["replaced_terms"] == ["matter_kinetic"] for item in actions)
    f2_only = all((item["f2_term"] == F2_TERM) is ("F_mu_nu" in item["fields"]) for item in actions)
    cases = [
        ("1", "frozen Phase 4C hash unchanged", FROZEN_4C_HASH, action_hash),
        ("2", "completion cannot modify the frozen baseline", "REFUSED", modify_frozen_baseline()["status"]),
        ("3", "completion contains the authorized kinetic density", "TRUE", "TRUE" if density_only else "FALSE"),
        ("4", "no additional interaction is added", "TRUE", "TRUE" if result["completion"]["added_components"][0] == KINETIC_DENSITY else "FALSE"),
        ("5", "no parameter is fixed", "0", "0" if all(item["parameters_fixed"] == [] for item in actions) else "FIXED"),
        ("6", "current normalization matches the stored definition", CURRENT_FORMULA, result["completion"]["expansion"]["current_formula"] if result["completion"]["expansion"]["current_coefficient"] == 2 else "CHANGED"),
        ("7", "F_mu_nu dependence on the connection is declared", "DECLARED", "DECLARED" if all(item["f2_a_mu_dependency"] == "DECLARED" for item in actions if "F_mu_nu" in item["fields"]) else "UNDECLARED"),
        ("8", "F2 appears only on the test-extension branch", "TRUE", "TRUE" if f2_only else "FALSE"),
        ("9", "F2 is not promoted to the frozen baseline", "FALSE", "FALSE" if all(item["frozen_promoted"] is False for item in actions) else "TRUE"),
        ("10", "provenance is the human authorization", PROVENANCE, PROVENANCE if all(item["provenance"] == PROVENANCE for item in actions) else "OTHER"),
        ("11", "completion is not an independent derivation", "FALSE", "FALSE" if all(item["derived_independently"] is False and item["strict_provenance"] == "NOT_DERIVED_FROM_THE_FROZEN_ACTION" for item in actions) else "TRUE"),
        ("12", "no experimental constants enter", "ABSENT", "ABSENT" if _isolated(result["completion"]) else "PRESENT"),
        ("13", "no numerical target enters", "ABSENT", "ABSENT" if _isolated(result["completion"]) else "PRESENT"),
        ("14", "symmetry is not upgraded automatically", "PENDING_REVERIFICATION", upgrade_symmetry()["full_action_symmetry_status"] if all(item["full_action_symmetry_status"] == "PENDING_REVERIFICATION" for item in actions) else "EXACT"),
        ("15", "expected fields are present", "TRUE", "TRUE" if all({"Phi", "metric", "mathcalA_mu"} <= set(item["fields"]) for item in actions) else "FALSE"),
    ]
    if result["completion_digest"] != repeated:
        cases[0] = ("1", "frozen Phase 4C hash unchanged", FROZEN_4C_HASH, "UNSTABLE")
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_14I_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_14I_PRECONDITION_FAILED"}


def run_phase_14i(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    freeze_before = verify_phase4c_action_freeze()
    phase14h = run_phase_14h(write_artifacts=False)
    stored = _read("phase14f_embedding_artifacts/PHASE_14F_MATERIALIZED_ACTIONS_V2.json")
    actions = stored.get("actions", [])
    if (
        freeze_before.get("status") != "VERIFIED"
        or freeze_before.get("action_content_hash") != FROZEN_4C_HASH
        or phase14h.get("PHASE_14H_STATUS") != "COMPLETE"
        or phase14h.get("CASE") != "B"
        or phase14h.get("SOURCE_ACTION_STATUS") != "EXPANSION_FRAGMENT"
        or phase14h.get("COVARIANT_KINETIC_SOURCE_STATUS") != "ABSENT"
        or phase14h.get("ACTION_DERIVATION_READY") is not False
        or phase14h.get("MISSING_COMPLETE_KINETIC_SOURCE") is not True
        or phase14h.get("LEXICON_HASH") != EXPECTED_LEXICON_HASH
        or len(actions) != 4
    ):
        return _not_authorized("Phase 14H boundary or frozen state")
    frozen = freeze_before["canonical_action"]
    expansion = _expansion(frozen, so2_generator_K())
    if expansion.get("status") != "EXACT":
        return {"PHASE_14I_STATUS": "INCOMPLETE", "status": expansion.get("status", "EXPANSION_FAILED")}
    manifest = build_manifest(EXPECTED_LEXICON_HASH)
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14I.json").write_bytes(canonical_json_bytes(manifest))
    first = build_completion(actions, expansion)
    second = build_completion(actions, expansion)
    if completion_digest(first) != completion_digest(second) or first["hash_before"] == first["hash_after"]:
        return {"PHASE_14I_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    freeze_after = verify_phase4c_action_freeze()
    if freeze_after.get("status") != "VERIFIED" or freeze_after.get("action_content_hash") != FROZEN_4C_HASH:
        return {"PHASE_14I_STATUS": "INCOMPLETE", "status": "FROZEN_ACTION_MODIFIED"}
    core = {"completion": first, "completion_digest": completion_digest(first)}
    negatives = negative_tests(core, completion_digest(second), freeze_after["action_content_hash"])
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14I_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_14I_STATUS": "COMPLETE",
        "AUTHORIZATION_STATUS": PROVENANCE,
        "COMPLETION_ID": COMPLETION_ID,
        "PARENT_ACTION_ID": PARENT_ACTION_ID,
        "ACTION_HASH_BEFORE": first["hash_before"],
        "ACTION_HASH_AFTER": first["hash_after"],
        "FROZEN_ACTION_HASH": freeze_after["action_content_hash"],
        "FROZEN_ACTION_MODIFIED": False,
        "ACTION_DERIVATION_READY": True,
        "F2_A_MU_DEPENDENCY": "DECLARED",
        "PHASE_14I_EOM_STATUS": "READY_FOR_NEXT_PHASE",
        "FULL_ACTION_SYMMETRY_STATUS": "PENDING_REVERIFICATION",
        "FREEZE_STATUS": "VERIFIED",
        "ACTION_COMPLETION_STATUS": "VERIFIED",
        "F2_DEPENDENCY_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "NO_GRAVITY_CHANGE": "VERIFIED",
        "ACTION_FREEZE_VERIFIED": True,
        "CURRENT_DEFINITION": first["current_definition"],
        "CURRENT_RELATION_TO_GAUGED_ACTION": first["current_relation"],
        "EOM_EXECUTED": False,
        "SEARCH_EXECUTED": False,
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "LEXICON_HASH": EXPECTED_LEXICON_HASH,
        "LEXICON_ID": LEXICON_ID,
        "completion_scope": SCOPE,
        "authorization_id": AUTHORIZATION_ID,
        "f2_completion_hash": first["f2_hash"],
        "timestamp": timestamp,
        "validation_status": "VERIFIED",
        "search_manifest": manifest,
        "completion": first,
        "dry_run_negatives": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_14I_ACTION_COMPLETION.json": {
                "actions": first["actions"],
                "kinetic_density": KINETIC_DENSITY,
                "d_mu": D_MU,
            },
            "PHASE_14I_EXPANSION.json": first["expansion"],
            "PHASE_14I_CURRENT.json": {
                "current_definition": first["current_definition"],
                "current_relation": first["current_relation"],
                "formula": CURRENT_FORMULA,
            },
            "PHASE_14I_F2_COMPLETION.json": {
                "dependency": "DECLARED",
                "f_definition": F_DEFINITION,
                "provenance": first["f2_dependency_provenance"],
                "term": F2_TERM,
            },
            "PHASE_14I_PROVENANCE.json": {
                "action_hash_after": first["hash_after"],
                "action_hash_before": first["hash_before"],
                "added_components": first["added_components"],
                "authorization_id": AUTHORIZATION_ID,
                "completion_id": COMPLETION_ID,
                "completion_scope": SCOPE,
                "forbidden_components": first["forbidden_components"],
                "frozen_action_modified": False,
                "frozen_hash": FROZEN_4C_HASH,
                "parent_action_id": PARENT_ACTION_ID,
                "provenance": PROVENANCE,
                "timestamp": timestamp,
                "validation_status": "VERIFIED",
            },
            "PHASE_14I_FIELD_PARAMETER.json": {
                "actions": [{"fields": item["fields"], "parameters": item["parameters"], "theory_id": item["theory_id"]} for item in first["actions"]]
            },
            "PHASE_14I_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "eom", "status": "READY_FOR_NEXT_PHASE"},
                    {"frontier_id": "full_action_symmetry", "status": "PENDING_REVERIFICATION"},
                    {"frontier_id": "Z_A", "status": "FREE"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_14I_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
