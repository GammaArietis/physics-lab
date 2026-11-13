"""Phase 11AH.2: assumed identification F_X = c_F * Phi.

The relation is applied only on an execution copy. It is not written into
the frozen action.
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
from physics_lab.physics.internal_spectrum import implemented_branch_II_m2
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ah_t06_containment import artifact_dir as phase11ah_artifact_dir
from physics_lab.physics.phase11ai_ft_identification import T06_STATUS
from physics_lab.physics.phase11ai_ft_identification import artifact_dir as phase11ai_artifact_dir
from physics_lab.physics.phase11ai_ft_identification import run_containment_audit_T07
from physics_lab.physics.spacetime import MOSTLY_PLUS, canonical_prefactor

__all__ = [
    "CLOSURE_TARGET",
    "IDENTIFICATION_FORMULA",
    "FrozenAuthorizationError",
    "OrderParameterIdentificationAuthorization",
    "run_phase_11AH_2_execution",
]

PHASE = "PHASE_11AH.2"
CLOSURE_TARGET = "NEW_PARAMETER_FREE_RELATION"
IDENTIFICATION_FORMULA = "F_X = c_F * Phi"
_FIELDS = {
    "identification_type": "Direct Proportionality T06",
    "formula": IDENTIFICATION_FORMULA,
    "theoretical_scope": "EFFECTIVE_QFT",
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
    return Path(__file__).resolve().parent / "phase11ah2_artifacts"


def _declaration_hash(body: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(body)).hexdigest()


def _authorization_body() -> dict[str, Any]:
    return {
        "gate": "HUMAN-DECLARED NEW PHYSICAL INPUT",
        "classification": "NEW PHYSICAL INPUT",
        "phase": PHASE,
        "identification_type": _FIELDS["identification_type"],
        "formula": _FIELDS["formula"],
        "theoretical_scope": _FIELDS["theoretical_scope"],
        "provenance": Provenance.ASSUMED.value,
        "derived": False,
        "closure_criterion": CLOSURE_TARGET,
        "previous_audit": "PHASE_11AH.1 NOT_FOUND",
    }


DECLARATION_HASH = _declaration_hash(_authorization_body())


@immutable
class OrderParameterIdentificationAuthorization:
    """Assumed proportionality. It is not derived from the frozen action."""

    def __init__(self) -> None:
        body = _authorization_body()
        self.gate = body["gate"]
        self.classification = body["classification"]
        self.phase = body["phase"]
        self.identification_type = body["identification_type"]
        self.formula = body["formula"]
        self.theoretical_scope = body["theoretical_scope"]
        self.provenance = body["provenance"]
        self.derived = False
        self.closure_criterion = body["closure_criterion"]
        self.declaration_hash = DECLARATION_HASH
        self._ready = True

    def provenance_entry(self) -> dict[str, Any]:
        return {
            "entry": "OrderParameterIdentificationAuthorization",
            "phase": self.phase,
            "gate": self.gate,
            "classification": self.classification,
            "Provenance": self.provenance,
            "derived": False,
            "identification_type": self.identification_type,
            "formula": self.formula,
            "theoretical_scope": self.theoretical_scope,
            "declaration_hash": self.declaration_hash,
        }


def _authorization_intact(auth: Any) -> bool:
    if type(auth) is not OrderParameterIdentificationAuthorization:
        return False
    if auth.declaration_hash != DECLARATION_HASH:
        return False
    if auth.provenance != Provenance.ASSUMED.value or auth.classification != "NEW PHYSICAL INPUT":
        return False
    if auth.identification_type != _FIELDS["identification_type"]:
        return False
    if auth.formula != IDENTIFICATION_FORMULA:
        return False
    if auth.theoretical_scope != _FIELDS["theoretical_scope"]:
        return False
    if auth.gate != "HUMAN-DECLARED NEW PHYSICAL INPUT" or auth.derived is not False:
        return False
    return _declaration_hash(_authorization_body()) == DECLARATION_HASH


def _substitute_token(text: str, token: str, replacement: str) -> tuple[str, int]:
    count = text.count(token)
    return text.replace(token, replacement), count


def _execution_copy(signature: str) -> dict[str, Any]:
    """Apply F_X = c_F * Phi on copies of the action and the recorded equations."""
    action_copy = copy.deepcopy(phase4c_action_document())
    action_text = canonical_json_bytes(action_copy).decode("utf-8")
    _replaced_action, action_sites = _substitute_token(action_text, "F_X", "(c_F*Phi)")
    rows = json.loads((phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json").read_text(encoding="utf-8"))
    eom_copy = copy.deepcopy(rows)
    eom_sites = 0
    for row in eom_copy:
        replaced, count = _substitute_token(str(row.get("EOM", "")), "F_X", "(c_F*Phi)")
        eom_sites += count
        row["EOM"] = replaced
    order_parameter, coupling, phi = sp.symbols("F_X c_F Phi")
    identification = sp.Eq(order_parameter, coupling * phi)
    solved = sp.solve(identification, coupling)
    coupling_value = sp.simplify(solved[0]) if len(solved) == 1 else None
    unique_absolute = bool(coupling_value is not None and coupling_value.is_number)
    kinetic = canonical_prefactor(signature)
    curvature, modulus, charge = sp.symbols("c_H lam_a Q_a", real=True, nonzero=True)
    mass2 = sp.simplify(implemented_branch_II_m2(curvature, kinetic, modulus, signature))
    ratio = sp.simplify(mass2 / charge)
    ratio_after = sp.simplify(ratio.subs(order_parameter, coupling * phi))
    ratio_unchanged = bool(sp.simplify(ratio_after - ratio) == 0)
    parameter_free = ratio_after.free_symbols == set()
    frozen_ids = [row["id"] for row in action_copy["parameters"]]
    constrained = {str(symbol) for symbol in (coupling * phi).free_symbols} & set(frozen_ids)
    generated = unique_absolute or (parameter_free and not ratio_unchanged)
    return {
        "execution_copy_only": True,
        "action_substitution_sites": action_sites,
        "eom_substitution_sites": eom_sites,
        "eom_changed": eom_sites != 0,
        "constraint_on_execution_copy": IDENTIFICATION_FORMULA,
        "c_F_solution": None if coupling_value is None else str(coupling_value),
        "c_F_is_unique_absolute_value": unique_absolute,
        "c_F_remains_free": not unique_absolute,
        "mass_charge_ratio": str(ratio),
        "mass_charge_ratio_unchanged": ratio_unchanged,
        "mass_charge_ratio_parameter_free": parameter_free,
        "frozen_parameters_constrained": sorted(constrained),
        "parameters_removed": 0,
        "execution_copy_adds_c_F": True,
        "c_F_added_to_frozen_parameter_list": False,
        "parameter_free_relation": generated,
    }


def run_phase_11AH_2_execution(
    authorization: OrderParameterIdentificationAuthorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Test whether F_X = c_F * Phi creates a parameter-free relation.

    NEW_PARAMETER_FREE_RELATION is logged before that test. The frozen
    action is not modified.
    """
    prior = run_containment_audit_T07(write_artifacts=False)
    if prior.get("Provenance") != "NOT_FOUND" or prior.get("T06_STATUS") != T06_STATUS:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "T06 and T07 audits are not the recorded NOT_FOUND results",
            "evaluated": False,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    opening = {
        "entry": "Phase 11AH.2 opening",
        "PHASE": PHASE,
        "T06_STATUS": T06_STATUS,
        "previous_T06_provenance": prior["provenance_log"][0]["previous_audit_provenance"],
        "previous_T07_provenance": prior["Provenance"],
        "T07_activated": False,
        "injection_is_assumed": True,
    }
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "closure_target_used_as_filter": False,
    }
    provenance_log: list[dict[str, Any]] = [opening, closure_entry]
    if not _authorization_intact(authorization):
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "authorization is not the sealed identification",
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
            "PHASE": PHASE,
            "detail": "frozen 4C hash",
            "evaluated": False,
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    parents = {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "11AH": phase11ah_artifact_dir() / "PHASE_11AH_T06_CONTAINMENT.json",
        "11AI": phase11ai_artifact_dir() / "PHASE_11AI_T07_CONTAINMENT.json",
        "EOM": phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json",
    }
    before = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    document_before = canonical_json_bytes(phase4c_action_document())
    analysis = _execution_copy(signature)
    document_after = canonical_json_bytes(phase4c_action_document())
    after = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    if document_after != document_before or after != before:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "frozen record mutated",
            "evaluated": False,
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": document_after != document_before,
        }
    generated = bool(analysis["parameter_free_relation"])
    observed = CLOSURE_TARGET if generated else "RELATION_NOT_DERIVED"
    program_status = "CLOSED_UNDER_DECLARED_SCOPE" if generated else "RELATION_NOT_DERIVED"
    provenance_log.append(
        {
            "entry": "identification on execution copy",
            "formula": authorization.formula,
            "action_substitution_sites": analysis["action_substitution_sites"],
            "eom_substitution_sites": analysis["eom_substitution_sites"],
            "c_F_is_unique_absolute_value": analysis["c_F_is_unique_absolute_value"],
            "mass_charge_ratio_parameter_free": analysis["mass_charge_ratio_parameter_free"],
            "c_F_added_to_frozen_parameter_list": False,
            "Provenance": authorization.provenance,
            "classification": authorization.classification,
        }
    )
    comparison = {
        "entry": "closure comparison",
        "criterion": CLOSURE_TARGET,
        "observed": observed,
        "objective_met": observed == CLOSURE_TARGET,
        "PROGRAM_CLOSURE_STATUS": program_status,
        "post_hoc_validation": False,
        "closure_target_used_as_filter": False,
    }
    provenance_log.append(comparison)
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "gate": authorization.gate,
        "identification_type": authorization.identification_type,
        "formula": authorization.formula,
        "theoretical_scope": authorization.theoretical_scope,
        "Provenance": Provenance.ASSUMED.value,
        "classification": "NEW PHYSICAL INPUT",
        "derived": False,
        "declaration_hash": authorization.declaration_hash,
        "T06_STATUS": T06_STATUS,
        "T07_activated": False,
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
        destination = artifact_dir() / "PHASE_11AH2_EXECUTION.json"
        forbidden = (
            phase11ad_artifact_dir().resolve(),
            phase11ah_artifact_dir().resolve(),
            phase11ai_artifact_dir().resolve(),
            phase10b8_artifact_dir().resolve(),
        )
        if any(destination.resolve().is_relative_to(root) for root in forbidden):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(payload) + b"\n")
    return payload
