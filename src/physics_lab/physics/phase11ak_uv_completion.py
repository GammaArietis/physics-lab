"""Phase 11AK: containment audit and assumed UV cutoff for T12.

The cutoff is added only on an execution copy, and only after the audit.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.core.provenance import Provenance
from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.dynamical_metric import coefficient_table
from physics_lab.physics.gravity_internal import analyze_gravity_internal
from physics_lab.physics.internal_spectrum import implemented_branch_II_m2
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae3_discrete_vacuum import _magnitude_symbols
from physics_lab.physics.phase11ae4_degenerate_vacuum import artifact_dir as phase11ae4_artifact_dir
from physics_lab.physics.phase11ae4_degenerate_vacuum import run_phase_11AE_4_synthesis
from physics_lab.physics.phase11q_uv_consistency import uv_consistency_identities
from physics_lab.physics.spacetime import MOSTLY_PLUS, canonical_prefactor

__all__ = [
    "AUDIT_CLOSURE_TARGET",
    "EXECUTION_CLOSURE_TARGET",
    "UV_FORMULA",
    "FrozenAuthorizationError",
    "UVCompletionAuthorization",
    "run_containment_audit_T12",
    "run_phase_11AK_2_execution",
]

PHASE_AUDIT = "PHASE_11AK.1"
PHASE_EXECUTION = "PHASE_11AK.2"
AUDIT_CLOSURE_TARGET = "UV_COMPLETION_DERIVED"
EXECUTION_CLOSURE_TARGET = "NEW_PARAMETER_FREE_RELATION"
UV_FORMULA = "Lambda_UV^2 = M_Planck^2 / (lambda_a * lambda_b)"
_FIELDS = {
    "principle": "String-Scale UV Cutoff T12",
    "formula": UV_FORMULA,
    "theoretical_scope": "STRING_EFFECTIVE_THEORY",
}


class FrozenAuthorizationError(AttributeError):
    """Raised when a sealed authorization field is assigned or deleted."""


def immutable(cls):
    """Seal an authorization after construction. Later assignment fails."""
    init = cls.__init__

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, "_sealed", False)
        init(self, *args, **kwargs)
        if not getattr(self, "_ready", False):
            raise RuntimeError("authorization was not sealed")
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name, value):
        if getattr(self, "_sealed", False):
            raise FrozenAuthorizationError("sealed authorization cannot be altered: " + name)
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if getattr(self, "_sealed", False):
            raise FrozenAuthorizationError("sealed authorization cannot be altered: " + name)
        object.__delattr__(self, name)

    cls.__init__ = __init__
    cls.__setattr__ = __setattr__
    cls.__delattr__ = __delattr__
    return cls


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ak_artifacts"


def _declaration_hash(body: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(body)).hexdigest()


def _authorization_body() -> dict[str, Any]:
    return {
        "gate": "HUMAN-DECLARED NEW PHYSICAL INPUT",
        "classification": "NEW PHYSICAL INPUT",
        "phase": PHASE_EXECUTION,
        "principle": _FIELDS["principle"],
        "formula": _FIELDS["formula"],
        "theoretical_scope": _FIELDS["theoretical_scope"],
        "provenance": Provenance.ASSUMED.value,
        "derived": False,
        "closure_criterion": EXECUTION_CLOSURE_TARGET,
        "previous_audit": "PHASE_11AK.1 NOT_FOUND",
    }


DECLARATION_HASH = _declaration_hash(_authorization_body())


@immutable
class UVCompletionAuthorization:
    """Assumed UV cutoff. It is not derived from the frozen action."""

    def __init__(self) -> None:
        body = _authorization_body()
        self.gate = body["gate"]
        self.classification = body["classification"]
        self.phase = body["phase"]
        self.principle = body["principle"]
        self.formula = body["formula"]
        self.theoretical_scope = body["theoretical_scope"]
        self.provenance = body["provenance"]
        self.derived = False
        self.closure_criterion = body["closure_criterion"]
        self.declaration_hash = DECLARATION_HASH
        self._ready = True

    def provenance_entry(self) -> dict[str, Any]:
        return {
            "entry": "UVCompletionAuthorization",
            "phase": self.phase,
            "gate": self.gate,
            "classification": self.classification,
            "Provenance": self.provenance,
            "derived": False,
            "principle": self.principle,
            "formula": self.formula,
            "theoretical_scope": self.theoretical_scope,
            "declaration_hash": self.declaration_hash,
        }


def _authorization_intact(auth: Any) -> bool:
    if type(auth) is not UVCompletionAuthorization:
        return False
    if auth.declaration_hash != DECLARATION_HASH:
        return False
    if auth.provenance != Provenance.ASSUMED.value or auth.classification != "NEW PHYSICAL INPUT":
        return False
    if auth.principle != _FIELDS["principle"] or auth.formula != UV_FORMULA:
        return False
    if auth.theoretical_scope != _FIELDS["theoretical_scope"] or auth.derived is not False:
        return False
    return _declaration_hash(_authorization_body()) == DECLARATION_HASH


def _probe(name: str, found: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe": name,
        "found": found,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "evidence": evidence,
        "closure_target_used_as_filter": False,
    }


def _fixed_by_planck(expr: Any, planck: Any) -> bool:
    symbols = expr.free_symbols
    return bool(symbols) and symbols <= {planck} and bool(expr.is_number or symbols == {planck} and expr != planck)


def _scan(vacuum: dict[str, Any], signature: str) -> list[dict[str, Any]]:
    planck = sp.symbols("M_Planck", positive=True)
    document = phase4c_action_document()
    parameters = {row["id"]: row for row in document["parameters"]}
    low_energy = [sp.symbols(name) for name in ("c0", "c1", "Z", "kappa", "c_H", "lam_a", "lam_b")]
    action_fixed = any(_fixed_by_planck(symbol, planck) for symbol in low_energy)
    identities = uv_consistency_identities()
    action_probe = _probe(
        "frozen_action",
        action_fixed or "M_Planck" in parameters,
        {
            "planck_in_freeze": "M_Planck" in parameters,
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
            "finite_order_is_not_UV_completion": identities["finite_order_is_not_UV_completion"],
            "beta_does_not_fix_boundary": identities["beta_does_not_fix_boundary"],
        },
    )

    table = coefficient_table()
    gravity = analyze_gravity_internal(signature=signature)
    derived_coefficients = [row[0] for row in table if str(row[2]).startswith("DERIVED")]
    gravity_probe = _probe(
        "gravity_4a_4b",
        bool(derived_coefficients) or gravity["newton_G_used_to_fix_c1"] is True or gravity["m_eff2_without_free_parameters"] == "YES",
        {
            "coefficient_provenance": [row[2] for row in table],
            "c0": gravity["c0"],
            "c1": gravity["c1"],
            "newton_G_used_to_fix_c1": gravity["newton_G_used_to_fix_c1"],
            "m_eff2_without_free_parameters": gravity["m_eff2_without_free_parameters"],
        },
    )

    magnitudes = _magnitude_symbols()
    product = sp.simplify(magnitudes["lambda_a"] * magnitudes["lambda_b"])
    moduli_fixed = planck in product.free_symbols or _fixed_by_planck(product, planck)
    rows = json.loads((phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json").read_text(encoding="utf-8"))
    planck_equations = [str(row.get("EOM", "")) for row in rows if "Planck" in str(row.get("EOM", ""))]
    moduli_probe = _probe(
        "moduli_and_eom",
        moduli_fixed or bool(planck_equations),
        {
            "symmetry": vacuum["synthesis"]["symmetry"],
            "surviving_class": vacuum["synthesis"]["surviving_class"],
            "moduli_depend_on_planck": planck in product.free_symbols,
            "equations_naming_planck": planck_equations,
        },
    )
    return [action_probe, gravity_probe, moduli_probe]


def run_containment_audit_T12(
    closure_target: str | None = None,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Scan for a UV scale that already fixes the low-energy parameters."""
    if closure_target is not None and closure_target != AUDIT_CLOSURE_TARGET:
        return {
            "status": "CLOSURE_CRITERION_REFUSED",
            "PHASE": PHASE_AUDIT,
            "topic": "T12: UV completion",
            "rule": "Target-Blind rule",
            "scanned": False,
            "provenance_log": [
                {
                    "entry": "Pre-Execution Closure Criterion",
                    "rule": "Target-Blind rule",
                    "closure_target": None,
                    "accepted": False,
                    "logged_before_logical_execution": True,
                    "post_hoc_validation": False,
                }
            ],
            "new_parameter_count": 0,
            "T12_activated": False,
        }
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": AUDIT_CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "accepted": True,
    }
    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE_AUDIT,
            "scanned": False,
            "provenance_log": [closure_entry],
            "detail": "frozen 4C hash",
            "new_parameter_count": 0,
            "T12_activated": False,
        }
    parents = {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "EOM": phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json",
        "11AE4": phase11ae4_artifact_dir() / "PHASE_11AE4_SYNTHESIS.json",
    }
    before = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    decision = json.loads(parents["11AD"].read_text(encoding="utf-8")).get("decision_map") or {}
    if decision.get("T12") != "REQUIRES_NEW_PHYSICAL_INPUT":
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE_AUDIT,
            "scanned": False,
            "provenance_log": [closure_entry],
            "detail": "parent T12 decision",
            "new_parameter_count": 0,
            "T12_activated": False,
        }
    document_before = canonical_json_bytes(phase4c_action_document())
    vacuum = run_phase_11AE_4_synthesis(write_artifacts=False, signature=signature)
    if vacuum.get("PROGRAM_CLOSURE_STATUS") != "CLOSED_UNDER_DECLARED_SCOPE":
        return {
            "status": "STOP",
            "PHASE": PHASE_AUDIT,
            "detail": "Phase 11AE.4 is not the closed vacuum record",
            "scanned": False,
            "provenance_log": [closure_entry],
            "new_parameter_count": 0,
            "T12_activated": False,
        }
    probes = _scan(vacuum, signature)
    document_after = canonical_json_bytes(phase4c_action_document())
    after = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    if document_after != document_before or after != before:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE_AUDIT,
            "detail": "parent artifact mutated",
            "scanned": False,
            "new_parameter_count": 0,
            "T12_activated": False,
        }
    found = any(item["found"] for item in probes)
    provenance_log = [closure_entry, *probes]
    payload = {
        "status": "OK",
        "PHASE": PHASE_AUDIT,
        "topic": "T12: UV completion",
        "rule": "Target-Blind rule",
        "closure_target": AUDIT_CLOSURE_TARGET,
        "closure_target_used_as_filter": False,
        "scanned": True,
        "action_content_hash": digest,
        "probes": probes,
        "provenance_log": provenance_log,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "UV_COMPLETION_STATUS": "DERIVED" if found else "NOT_FOUND",
        "T12_activated": False,
        "new_parameter_count": 0,
        "frozen_action_modified": False,
    }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AK_T12_CONTAINMENT.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes({"Provenance": payload["Provenance"], "log": provenance_log}) + b"\n")
    return payload


def _execution_copy(signature: str, surviving: list[list[int]]) -> dict[str, Any]:
    action_copy = copy.deepcopy(phase4c_action_document())
    action_text = canonical_json_bytes(action_copy).decode("utf-8")
    action_sites = action_text.count("M_Planck") + action_text.count("Lambda_UV")
    magnitudes = _magnitude_symbols()
    cutoff, planck = sp.symbols("Lambda_UV M_Planck", positive=True)
    products = []
    for signs in surviving:
        product = sp.simplify(signs[0] * magnitudes["lambda_a"] * signs[1] * magnitudes["lambda_b"])
        products.append(product)
    same_product = bool(products) and all(sp.simplify(item - products[0]) == 0 for item in products)
    cutoff_value = sp.simplify(planck**2 / products[0]) if same_product else None
    unique_absolute = bool(cutoff_value is not None and cutoff_value.is_number)
    kinetic = canonical_prefactor(signature)
    curvature = sp.symbols("c_H", real=True, nonzero=True)
    mass = sp.simplify(implemented_branch_II_m2(curvature, kinetic, magnitudes["lambda_a"], signature))
    ratio = sp.simplify(mass / magnitudes["Q_a"])
    ratio_after = sp.simplify(ratio.subs(planck, cutoff)) if cutoff_value is not None else ratio
    ratio_unchanged = bool(sp.simplify(ratio_after - ratio) == 0)
    parameter_free = ratio_after.free_symbols == set()
    charge_solution = sp.solve(sp.Eq(cutoff**2, planck**2 / products[0]), magnitudes["Q_a"]) if same_product else []
    charge_fixed = len(charge_solution) == 1 and bool(sp.simplify(charge_solution[0]).is_number)
    frozen_ids = [row["id"] for row in action_copy["parameters"]]
    generated = unique_absolute or charge_fixed or (parameter_free and not ratio_unchanged)
    return {
        "execution_copy_only": True,
        "action_substitution_sites": action_sites,
        "orbit_product_common": same_product,
        "Lambda_UV2": None if cutoff_value is None else str(cutoff_value),
        "Lambda_UV_is_number": unique_absolute,
        "M_Planck_remains_free": not unique_absolute,
        "mass_depends_on_cutoff": cutoff in mass.free_symbols or planck in mass.free_symbols,
        "mass_charge_ratio_unchanged": ratio_unchanged,
        "mass_charge_ratio_parameter_free": parameter_free,
        "charge_fixed_to_number": charge_fixed,
        "frozen_parameters_removed": [name for name in frozen_ids if name in {"M_Planck", "Lambda_UV"}],
        "parameters_removed": 0,
        "execution_copy_adds_M_Planck": True,
        "M_Planck_added_to_frozen_parameter_list": False,
        "parameter_free_relation": generated,
    }


def run_phase_11AK_2_execution(
    authorization: UVCompletionAuthorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Test the assumed cutoff after a NOT_FOUND audit."""
    prior = run_containment_audit_T12(write_artifacts=False, signature=signature)
    if prior.get("Provenance") != "NOT_FOUND" or prior.get("T12_activated") is not False:
        return {
            "status": "STOP",
            "PHASE": PHASE_EXECUTION,
            "detail": "Phase 11AK.1 did not return NOT_FOUND",
            "evaluated": False,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    surviving = next(row for row in prior["probes"] if row["probe"] == "moduli_and_eom")["evidence"]["surviving_class"]
    audit_entry = {
        "entry": "Phase 11AK.1 audit",
        "previous_provenance": prior["Provenance"],
        "previous_record_modified": False,
        "logged_before_uv_execution": True,
    }
    opening = {"entry": "Phase 11AK.2 opening", "PHASE": PHASE_EXECUTION, "topic": "T12: UV completion"}
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": EXECUTION_CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "closure_target_used_as_filter": False,
    }
    provenance_log: list[dict[str, Any]] = [audit_entry, opening, closure_entry]
    if not _authorization_intact(authorization):
        return {
            "status": "STOP",
            "PHASE": PHASE_EXECUTION,
            "detail": "authorization is not the sealed UV input",
            "evaluated": False,
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    provenance_log.append(authorization.provenance_entry())
    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return {
            "status": "STOP",
            "PHASE": PHASE_EXECUTION,
            "detail": "frozen 4C hash",
            "evaluated": False,
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    document_before = canonical_json_bytes(phase4c_action_document())
    analysis = _execution_copy(signature, surviving)
    document_after = canonical_json_bytes(phase4c_action_document())
    if document_after != document_before:
        return {
            "status": "STOP",
            "PHASE": PHASE_EXECUTION,
            "detail": "frozen action mutated",
            "evaluated": False,
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": True,
        }
    generated = bool(analysis["parameter_free_relation"])
    observed = EXECUTION_CLOSURE_TARGET if generated else "RELATION_NOT_DERIVED"
    program_status = "CLOSED_UNDER_DECLARED_SCOPE" if generated else "RELATION_NOT_DERIVED"
    provenance_log.append(
        {
            "entry": "UV cutoff on execution copy",
            "formula": authorization.formula,
            "Lambda_UV_is_number": analysis["Lambda_UV_is_number"],
            "mass_charge_ratio_parameter_free": analysis["mass_charge_ratio_parameter_free"],
            "M_Planck_added_to_frozen_parameter_list": False,
            "Provenance": authorization.provenance,
            "classification": authorization.classification,
        }
    )
    comparison = {
        "entry": "closure comparison",
        "criterion": EXECUTION_CLOSURE_TARGET,
        "observed": observed,
        "objective_met": observed == EXECUTION_CLOSURE_TARGET,
        "PROGRAM_CLOSURE_STATUS": program_status,
        "post_hoc_validation": False,
        "closure_target_used_as_filter": False,
    }
    provenance_log.append(comparison)
    payload = {
        "status": "OK",
        "PHASE": PHASE_EXECUTION,
        "gate": authorization.gate,
        "principle": authorization.principle,
        "formula": authorization.formula,
        "theoretical_scope": authorization.theoretical_scope,
        "Provenance": Provenance.ASSUMED.value,
        "classification": "NEW PHYSICAL INPUT",
        "derived": False,
        "declaration_hash": authorization.declaration_hash,
        "previous_audit_provenance": prior["Provenance"],
        "action_content_hash": digest,
        "frozen_action_modified": False,
        "analysis": analysis,
        "parameter_free_relation": generated,
        "closure_comparison": comparison,
        "observed": observed,
        "objective_met": comparison["objective_met"],
        "PROGRAM_CLOSURE_STATUS": program_status,
        "provenance_log": provenance_log,
        "new_parameter_count": 0,
    }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AK2_EXECUTION.json"
        if destination.resolve().is_relative_to(phase11ae4_artifact_dir().resolve()):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(payload) + b"\n")
    return payload
