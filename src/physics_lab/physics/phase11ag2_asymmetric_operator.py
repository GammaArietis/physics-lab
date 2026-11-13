"""Phase 11AG.2: assumed soft term on the discrete T10 configurations.

The Phase 11AG.1 audit stays NOT_FOUND. This module adds
V_soft only on an execution copy of the vacuum energy.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.core.provenance import Provenance
from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.internal_spectrum import implemented_branch_II_m2
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ae3_discrete_vacuum import (
    _SIGN_PAIRS,
    _loop_value,
    _magnitude_symbols,
    run_phase_11AE_3_execution,
)
from physics_lab.physics.phase11ag_abfi_operators import T09_STATUS, run_containment_audit_T13
from physics_lab.physics.phase11ag_abfi_operators import artifact_dir as phase11ag_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS, canonical_prefactor

__all__ = [
    "CLOSURE_TARGET",
    "SOFT_FORMULA",
    "AsymmetricOperatorAuthorization",
    "FrozenAuthorizationError",
    "run_phase_11AG_2_execution",
]

PHASE = "PHASE_11AG.2"
CLOSURE_TARGET = "DEGENERACY_LIFTED"
SOFT_FORMULA = "V_soft(lambda_a, lambda_b) = m_soft^2 * (lambda_a^2 - lambda_b^2)"
_FIELDS = {
    "operator_type": "Soft Asymmetric Mass Term",
    "formula": SOFT_FORMULA,
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
    return Path(__file__).resolve().parent / "phase11ag2_artifacts"


def _declaration_hash(body: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(body)).hexdigest()


def _authorization_body() -> dict[str, Any]:
    return {
        "gate": "HUMAN-DECLARED NEW PHYSICAL INPUT",
        "classification": "NEW PHYSICAL INPUT",
        "phase": PHASE,
        "operator_type": _FIELDS["operator_type"],
        "formula": _FIELDS["formula"],
        "theoretical_scope": _FIELDS["theoretical_scope"],
        "provenance": Provenance.ASSUMED.value,
        "derived": False,
        "closure_criterion": CLOSURE_TARGET,
        "previous_audit": "PHASE_11AG NOT_FOUND",
    }


DECLARATION_HASH = _declaration_hash(_authorization_body())


@immutable
class AsymmetricOperatorAuthorization:
    """Assumed soft operator. It is not derived from the frozen action."""

    def __init__(self) -> None:
        body = _authorization_body()
        self.gate = body["gate"]
        self.classification = body["classification"]
        self.phase = body["phase"]
        self.operator_type = body["operator_type"]
        self.formula = body["formula"]
        self.theoretical_scope = body["theoretical_scope"]
        self.provenance = body["provenance"]
        self.derived = False
        self.closure_criterion = body["closure_criterion"]
        self.declaration_hash = DECLARATION_HASH
        self._ready = True

    def provenance_entry(self) -> dict[str, Any]:
        return {
            "entry": "AsymmetricOperatorAuthorization",
            "phase": self.phase,
            "gate": self.gate,
            "classification": self.classification,
            "Provenance": self.provenance,
            "derived": False,
            "operator_type": self.operator_type,
            "formula": self.formula,
            "theoretical_scope": self.theoretical_scope,
            "declaration_hash": self.declaration_hash,
        }


def _authorization_intact(auth: Any) -> bool:
    if type(auth) is not AsymmetricOperatorAuthorization:
        return False
    if auth.declaration_hash != DECLARATION_HASH:
        return False
    if auth.provenance != Provenance.ASSUMED.value or auth.classification != "NEW PHYSICAL INPUT":
        return False
    if auth.operator_type != _FIELDS["operator_type"]:
        return False
    if auth.formula != SOFT_FORMULA:
        return False
    if auth.theoretical_scope != _FIELDS["theoretical_scope"]:
        return False
    if auth.gate != "HUMAN-DECLARED NEW PHYSICAL INPUT" or auth.derived is not False:
        return False
    return _declaration_hash(_authorization_body()) == DECLARATION_HASH


def _vacuum_totals(signature: str) -> dict[str, Any]:
    """Add V_soft to Coleman-Weinberg on the four T10 sign sectors."""
    magnitudes = _magnitude_symbols()
    kinetic = canonical_prefactor(signature)
    m_soft = sp.symbols("m_soft", real=True, nonzero=True)
    mu, scheme_c = sp.symbols("mu c", positive=True)
    c_h_positive = sp.symbols("c_H", positive=True)
    soft_values = []
    rows = []
    valid_expressions = []
    for sign_of_c_h, c_h in ((1, c_h_positive), (-1, -c_h_positive)):
        for sign_a, sign_b in _SIGN_PAIRS:
            lambda_a = sp.simplify(sign_a * magnitudes["lambda_a"])
            lambda_b = sp.simplify(sign_b * magnitudes["lambda_b"])
            soft = sp.simplify(m_soft**2 * (lambda_a**2 - lambda_b**2))
            soft_values.append(soft)
            mass_a = sp.simplify(implemented_branch_II_m2(c_h, kinetic, lambda_a, signature))
            mass_b = sp.simplify(implemented_branch_II_m2(c_h, kinetic, lambda_b, signature))
            real_spectrum = bool(mass_a.is_positive and mass_b.is_positive)
            if real_spectrum:
                loop = _loop_value(mass_a, mass_b, mu, scheme_c)
                total = sp.simplify(loop + soft)
                valid_expressions.append(total)
                loop_text = str(loop)
                total_text = str(total)
            else:
                loop_text = "NOT_REAL"
                total_text = "NOT_REAL"
            rows.append(
                {
                    "lambda_signs": [sign_a, sign_b],
                    "c_H_sign": sign_of_c_h,
                    "V_soft": str(soft),
                    "V_1loop": loop_text,
                    "V_tot": total_text,
                    "real_spectrum": real_spectrum,
                    "physically_valid": real_spectrum,
                }
            )
    soft_even = bool(soft_values) and all(
        sp.simplify(value - soft_values[0]) == 0 for value in soft_values
    )
    if len(valid_expressions) == 2:
        difference = sp.simplify(valid_expressions[0] - valid_expressions[1])
        distinct = bool(difference != 0)
        difference_text = str(difference)
    else:
        distinct = False
        difference_text = "UNDEFINED"
    return {
        "configuration_count": 4,
        "rows": rows,
        "valid_state_count": len(valid_expressions),
        "V_soft_invariant_under_sign_flip": soft_even,
        "valid_energy_difference": difference_text,
        "valid_energies_distinct": distinct and soft_even and len(valid_expressions) >= 2,
    }


def run_phase_11AG_2_execution(
    authorization: AsymmetricOperatorAuthorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Test whether V_soft splits the non-tachyonic T10 corners.

    DEGENERACY_LIFTED is logged before that comparison. CLOSED_UNDER_DECLARED_SCOPE
    is returned only when those corners have distinct real energies.
    """
    audit = run_containment_audit_T13(write_artifacts=False)
    previous = run_phase_11AE_3_execution(write_artifacts=False, signature=signature)
    if audit.get("Provenance") != "NOT_FOUND" or audit.get("T13_activated") is not False:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "Phase 11AG.1 is not the NOT_FOUND audit",
            "evaluated": False,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    if previous.get("PROGRAM_CLOSURE_STATUS") != "DOMAIN_UNREDUCED":
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "Phase 11AE.3 did not leave a residual degeneracy",
            "evaluated": False,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    opening = {
        "entry": "Phase 11AG.2 opening",
        "PHASE": PHASE,
        "previous_audit": "PHASE_11AG",
        "previous_audit_provenance": audit["Provenance"],
        "previous_record_modified": False,
        "T09_STATUS": T09_STATUS,
        "T10_reexecuted": False,
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
            "detail": "authorization is not the sealed soft input",
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
    document_before = canonical_json_bytes(phase4c_action_document())
    totals = _vacuum_totals(signature)
    document_after = canonical_json_bytes(phase4c_action_document())
    if document_after != document_before:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "frozen action mutated",
            "evaluated": False,
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": True,
        }
    prior_valid = previous["evaluation"]["real_configurations"]
    same_valid_set = [row["lambda_signs"] for row in totals["rows"] if row["physically_valid"]] == [
        item["lambda_signs"] for item in prior_valid
    ]
    lifted = bool(totals["valid_energies_distinct"]) and same_valid_set and totals["valid_state_count"] == len(prior_valid)
    observed = CLOSURE_TARGET if lifted else "DEGENERACY_UNLIFTED"
    program_status = "CLOSED_UNDER_DECLARED_SCOPE" if lifted else "NOT_CLOSED"
    provenance_log.append(
        {
            "entry": "soft term on discrete configurations",
            "total_potential": "V_1loop + V_soft",
            "V_soft_added_to_frozen_parameter_list": False,
            "configuration_count": totals["configuration_count"],
            "valid_state_count": totals["valid_state_count"],
            "valid_energies_distinct": totals["valid_energies_distinct"],
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
        "operator_type": authorization.operator_type,
        "formula": authorization.formula,
        "theoretical_scope": authorization.theoretical_scope,
        "Provenance": Provenance.ASSUMED.value,
        "classification": "NEW PHYSICAL INPUT",
        "derived": False,
        "declaration_hash": authorization.declaration_hash,
        "T09_STATUS": T09_STATUS,
        "T10_reexecuted": False,
        "previous_record_modified": False,
        "action_content_hash": digest,
        "frozen_action_modified": False,
        "total_potential": "V_1loop + V_soft",
        "V_soft_added_to_frozen_parameter_list": False,
        "configurations": totals["rows"],
        "valid_state_count": totals["valid_state_count"],
        "V_soft_invariant_under_sign_flip": totals["V_soft_invariant_under_sign_flip"],
        "valid_energy_difference": totals["valid_energy_difference"],
        "valid_energies_distinct": totals["valid_energies_distinct"],
        "degeneracy_lifted": lifted,
        "closure_comparison": comparison,
        "observed": observed,
        "objective_met": comparison["objective_met"],
        "PROGRAM_CLOSURE_STATUS": program_status,
        "provenance_log": provenance_log,
        "new_parameter_count": 0,
    }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AG2_EXECUTION.json"
        if destination.resolve().is_relative_to(phase11ag_artifact_dir().resolve()):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(payload) + b"\n")
    return payload
