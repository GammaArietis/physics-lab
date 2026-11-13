"""Phase 11AF: T10 modulus-stabilization containment audit.

Phase 11AE is paused. T09 is frozen. This module only asks whether the
current grammar already stabilizes lam_a and lam_b. It does not add a
stabilization mechanism.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.core.provenance import Provenance
from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.dynamical_metric import coefficient_table
from physics_lab.physics.gravity_internal import analyze_gravity_internal
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase5d_gauge_dynamics import phase5d_scope_summary
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import QuantumEffectivePotential
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import modulus_mediation_identities
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "CLOSURE_TARGETS_T10",
    "PAUSE_MOTIVATION",
    "PHASE_11AE_STATUS",
    "PRE_EXECUTION_CLOSURE_TARGET_T10",
    "EXECUTION_CLOSURE_TARGET",
    "FLUX_POTENTIAL_FORMULA",
    "ModulusStabilizationAuthorization",
    "ModulusStabilizationAuthorization_Balanced",
    "T09_STATUS",
    "run_containment_audit_T10",
    "run_phase_11AF_2_execution",
    "run_phase_11AF_execution",
]

PHASE = "PHASE_11AF"
PHASE_11AE_STATUS = "PAUSED_DOMAIN_UNREDUCED"
T09_STATUS = "FROZEN"
PAUSE_MOTIVATION = (
    "L'assenza di dipendenza dal campo in M^2 rende inefficace il meccanismo "
    "radiativo a 1-loop nella grammatica corrente"
)
CLOSURE_TARGETS_T10 = ("MODULI_FIXED_AT_FINITE_VALUE", "MASS_GENERATION_FOR_MODULI")
PRE_EXECUTION_CLOSURE_TARGET_T10: str | None = None

def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11af_artifacts"


def _resolve_target(closure_target: str | None) -> tuple[str | None, str | None]:
    explicit = closure_target
    constant = PRE_EXECUTION_CLOSURE_TARGET_T10
    if explicit is not None and constant is not None and explicit != constant:
        return None, "argument and PRE_EXECUTION_CLOSURE_TARGET_T10 disagree"
    chosen = explicit if explicit is not None else constant
    if chosen is None:
        return None, "closure target was not declared"
    if chosen not in CLOSURE_TARGETS_T10:
        return None, "closure target is outside the T10 objective set"
    return chosen, None


def _pause_record(loop: dict[str, Any]) -> dict[str, Any]:
    return {
        "entry": "Phase 11AE pause",
        "PHASE_11AE_STATUS": PHASE_11AE_STATUS,
        "T09_STATUS": T09_STATUS,
        "T09_topic": "VACUUM_SELECTION_PRINCIPLE",
        "motivation": PAUSE_MOTIVATION,
        "M2_depends_on_phi": loop["M2_depends_on_phi"],
        "flat_on_V_adm": loop["flat_on_V_adm"],
        "logged_before_t10_scan": True,
    }


def _refusal(detail: str, pause: dict[str, Any] | None) -> dict[str, Any]:
    log = [pause] if pause is not None else []
    log.append(
        {
            "entry": "Pre-Execution Closure Criterion",
            "rule": "Target-Blind rule",
            "closure_target": None,
            "logged_before_logical_execution": True,
            "post_hoc_validation": False,
            "accepted": False,
            "detail": detail,
        }
    )
    return {
        "status": "CLOSURE_CRITERION_REFUSED",
        "PHASE": PHASE,
        "PHASE_11AE_STATUS": PHASE_11AE_STATUS,
        "T09_STATUS": T09_STATUS,
        "rule": "Target-Blind rule",
        "scanned": False,
        "provenance_log": log,
        "new_parameter_count": 0,
        "T10_activated": False,
    }


def _probe(name: str, found: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe": name,
        "found": found,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "evidence": evidence,
        "closure_target_used_as_filter": False,
    }


def _parameter_fixed(row: dict[str, Any]) -> bool:
    provenance = str(row.get("provenance", ""))
    return provenance == "DERIVED" and row.get("symbolic") is False and row.get("value_is_structural") is True


def _scan(loop: dict[str, Any]) -> list[dict[str, Any]]:
    document = phase4c_action_document()
    parameters = {row["id"]: row for row in document["parameters"]}
    lam_a = parameters["lam_a"]
    lam_b = parameters["lam_b"]
    frozen_hit = _parameter_fixed(lam_a) and _parameter_fixed(lam_b)
    frozen_probe = _probe(
        "frozen_internal_moduli",
        frozen_hit,
        {
            "lam_a_provenance": lam_a["provenance"],
            "lam_b_provenance": lam_b["provenance"],
            "lam_a_symbolic": lam_a["symbolic"],
            "lam_b_symbolic": lam_b["symbolic"],
            "fixed_at_finite_value": False,
        },
    )

    gravity_rows = coefficient_table()
    gravity_symbols = [row[0] for row in gravity_rows]
    gravity_free = all(row[2] == "INPUT / FREE" for row in gravity_rows)
    phase4b = analyze_gravity_internal(signature=MOSTLY_PLUS)
    gravity_fields = list(phase4b.get("dynamical_fields") or [])
    gravity_hit = (
        "lam_a" in gravity_symbols
        and "lam_b" in gravity_symbols
        and not gravity_free
        and phase4b.get("c0") == "DERIVED"
        and phase4b.get("c1") == "DERIVED"
    )
    gravity_probe = _probe(
        "gravity_phase_4a_4b",
        gravity_hit,
        {
            "phase4a_coefficients": gravity_symbols,
            "phase4a_coefficients_free": gravity_free,
            "phase4b_status": phase4b.get("phase4b_status"),
            "phase4b_c0": phase4b.get("c0"),
            "phase4b_c1": phase4b.get("c1"),
            "phase4b_dynamical_fields": gravity_fields,
            "lam_a_in_gravity_fields": "lam_a" in gravity_fields,
            "parameter_free_relation": phase4b.get("conclusion"),
        },
    )

    scope = phase5d_scope_summary()
    in_scope = " ".join(scope["in_scope"]).lower()
    gauge_mentions_moduli = "lam_a" in in_scope or "modulus stabil" in in_scope
    flows_in_scope = "beta function" in in_scope or "running coupling" in in_scope
    gauge_probe = _probe(
        "gauge_phase_5d",
        bool(gauge_mentions_moduli or flows_in_scope),
        {
            "tests_only": scope["tests_only"],
            "modulus_operator_in_scope": gauge_mentions_moduli,
            "beta_flow_in_scope": flows_in_scope,
            "running_couplings_listed_out_of_scope": "running couplings" in " ".join(scope["out_of_scope"]).lower(),
        },
    )

    identities = modulus_mediation_identities()
    z_path = phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json"
    z_doc = json.loads(z_path.read_text(encoding="utf-8"))
    stabilization = z_doc.get("stabilization") or {}
    z_status = str(stabilization.get("status", ""))
    z_hit = z_status == "DERIVED" and stabilization.get("vacuum_selected") is True and identities.get("no_stabilization_assumed") is False
    modulus_probe = _probe(
        "existing_modulus_sector",
        z_hit,
        {
            "stabilization_status": z_status,
            "vacuum_selected": stabilization.get("vacuum_selected"),
            "no_stabilization_assumed": identities.get("no_stabilization_assumed"),
            "c0_FREE": identities.get("c0_FREE"),
            "c1_FREE": identities.get("c1_FREE"),
            "no_T_in_freeze": identities.get("no_T_in_freeze"),
        },
    )

    radiative_probe = _probe(
        "radiative_one_loop",
        bool(loop["M2_depends_on_phi"] and loop["domain_reduced"]),
        {
            "M2_depends_on_phi": loop["M2_depends_on_phi"],
            "flat_on_V_adm": loop["flat_on_V_adm"],
            "fixes_lam_a_lam_b": False,
        },
    )
    return [frozen_probe, gravity_probe, gauge_probe, modulus_probe, radiative_probe]


def _write_log(payload: dict[str, Any]) -> None:
    destination = artifact_dir() / "PHASE_11AF_T10_CONTAINMENT.json"
    forbidden = (
        phase11ad_artifact_dir().resolve(),
        phase11z_artifact_dir().resolve(),
    )
    resolved = destination.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_json_bytes(payload) + b"\n")


def run_containment_audit_T10(
    closure_target: str | None = None,
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Scan existing structures for a modulus-stabilization mechanism.

    The T10 target is fixed before the scan. T09 stays frozen.
    """
    loop = QuantumEffectivePotential().evaluate()
    if loop["M2_depends_on_phi"] or not loop["flat_on_V_adm"] or loop["Provenance"] != "ASSUMED":
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "pause motivation does not match the effective potential",
            "scanned": False,
            "new_parameter_count": 0,
            "T10_activated": False,
        }
    pause = _pause_record(loop)
    chosen, refusal = _resolve_target(closure_target)
    if chosen is None:
        return _refusal(refusal or "closure target was not declared", pause)

    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": chosen,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "accepted": True,
    }
    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "provenance_log": [pause, closure_entry],
            "detail": "frozen 4C hash",
            "new_parameter_count": 0,
            "T10_activated": False,
        }

    ad_path = phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json"
    z_path = phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json"
    before = {"11AD": ad_path.read_bytes(), "11Z": z_path.read_bytes()}
    decision = json.loads(before["11AD"].decode("utf-8")).get("decision_map") or {}
    if decision.get("T09") != "REQUIRES_NEW_PHYSICAL_INPUT" or decision.get("T10") != "REQUIRES_NEW_PHYSICAL_INPUT":
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "provenance_log": [pause, closure_entry],
            "detail": "parent decision map",
            "new_parameter_count": 0,
            "T10_activated": False,
        }

    probes = _scan(loop)
    found = any(item["found"] for item in probes)
    provenance_log = [pause, closure_entry, *probes]
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "topic": "T10: modulus stabilization",
        "PHASE_11AE_STATUS": PHASE_11AE_STATUS,
        "T09_STATUS": T09_STATUS,
        "T09_reopened": False,
        "rule": "Target-Blind rule",
        "closure_target": chosen,
        "closure_target_used_as_filter": False,
        "scanned": True,
        "action_content_hash": digest,
        "probes": probes,
        "provenance_log": provenance_log,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "MODULUS_STABILIZATION_STATUS": "DERIVED" if found else "NOT_FOUND",
        "T10_activated": False,
        "new_parameter_count": 0,
    }
    if write_artifacts:
        _write_log(
            {
                "PHASE_11AE_STATUS": PHASE_11AE_STATUS,
                "T09_STATUS": T09_STATUS,
                "motivation": PAUSE_MOTIVATION,
                "Provenance": payload["Provenance"],
                "log": provenance_log,
            }
        )
    after = {"11AD": ad_path.read_bytes(), "11Z": z_path.read_bytes()}
    if after != before:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "detail": "parent artifact mutated",
            "new_parameter_count": 0,
            "T10_activated": False,
        }
    return payload


FLUX_POTENTIAL_FORMULA = (
    "V_flux(lambda) = (Q_a^2 / lambda_a^2) + (Q_b^2 / lambda_b^2) - Lambda_bulk"
)
EXECUTION_CLOSURE_TARGET = "MODULI_FIXED_AT_FINITE_VALUE"
_FLUX_FIELDS = {
    "mechanism": "Background Fluxes",
    "potential_formula": FLUX_POTENTIAL_FORMULA,
    "theoretical_scope": "CLASSICAL_GRAVITY_WITH_SOURCES",
    "target_variables": ["lambda_a", "lambda_b"],
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


def _declaration_hash(body: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(body)).hexdigest()


def _flux_body() -> dict[str, Any]:
    return {
        "gate": "HUMAN-DECLARED NEW PHYSICAL INPUT",
        "physical_input": "MODULUS_STABILIZATION",
        "classification": "NEW PHYSICAL INPUT",
        "mechanism": _FLUX_FIELDS["mechanism"],
        "potential_formula": _FLUX_FIELDS["potential_formula"],
        "theoretical_scope": _FLUX_FIELDS["theoretical_scope"],
        "target_variables": list(_FLUX_FIELDS["target_variables"]),
        "provenance": Provenance.ASSUMED.value,
        "derived": False,
        "closure_criterion": EXECUTION_CLOSURE_TARGET,
        "T09_STATUS": T09_STATUS,
    }


FLUX_DECLARATION_HASH = _declaration_hash(_flux_body())


@immutable
class ModulusStabilizationAuthorization:
    """HUMAN-DECLARED NEW PHYSICAL INPUT for background-flux stabilization.

    The formula is assumed. It is not derived from the frozen action.
    """

    def __init__(self) -> None:
        body = _flux_body()
        self.gate = body["gate"]
        self.physical_input = body["physical_input"]
        self.classification = body["classification"]
        self.mechanism = body["mechanism"]
        self.potential_formula = body["potential_formula"]
        self.theoretical_scope = body["theoretical_scope"]
        self.target_variables = tuple(body["target_variables"])
        self.provenance = body["provenance"]
        self.derived = False
        self.closure_criterion = body["closure_criterion"]
        self.T09_STATUS = body["T09_STATUS"]
        self.declaration_hash = FLUX_DECLARATION_HASH
        self._ready = True

    def provenance_entry(self) -> dict[str, Any]:
        return {
            "entry": "MODULUS_STABILIZATION",
            "gate": self.gate,
            "classification": self.classification,
            "Provenance": self.provenance,
            "derived": False,
            "mechanism": self.mechanism,
            "potential_formula": self.potential_formula,
            "declaration_hash": self.declaration_hash,
        }


def _authorization_intact(auth: Any) -> bool:
    if type(auth) is not ModulusStabilizationAuthorization:
        return False
    if auth.declaration_hash != FLUX_DECLARATION_HASH:
        return False
    if auth.provenance != Provenance.ASSUMED.value or auth.classification != "NEW PHYSICAL INPUT":
        return False
    if auth.mechanism != _FLUX_FIELDS["mechanism"]:
        return False
    if auth.potential_formula != FLUX_POTENTIAL_FORMULA:
        return False
    if auth.theoretical_scope != _FLUX_FIELDS["theoretical_scope"]:
        return False
    if list(auth.target_variables) != list(_FLUX_FIELDS["target_variables"]):
        return False
    if auth.closure_criterion != EXECUTION_CLOSURE_TARGET or auth.T09_STATUS != T09_STATUS:
        return False
    return _declaration_hash(_flux_body()) == FLUX_DECLARATION_HASH


def _finite_nonzero(value: Any, charges: set[Any]) -> bool:
    if value is None or value == 0:
        return False
    if getattr(value, "is_infinite", None) is True:
        return False
    if not getattr(value, "is_finite", False):
        return False
    return bool(value.free_symbols & charges)


def _flux_stationarity() -> dict[str, Any]:
    """Stationarity of the declared flux potential. Does not alter the frozen action."""
    lambda_a, lambda_b = sp.symbols("lambda_a lambda_b", real=True, nonzero=True)
    charge_a, charge_b = sp.symbols("Q_a Q_b", real=True, nonzero=True)
    bulk = sp.symbols("Lambda_bulk", real=True)
    potential = charge_a**2 / lambda_a**2 + charge_b**2 / lambda_b**2 - bulk
    derivative_a = sp.simplify(sp.diff(potential, lambda_a))
    derivative_b = sp.simplify(sp.diff(potential, lambda_b))
    solutions = sp.solve([derivative_a, derivative_b], [lambda_a, lambda_b], dict=True)
    charges = {charge_a, charge_b, bulk}
    finite = []
    for solution in solutions:
        value_a = solution.get(lambda_a)
        value_b = solution.get(lambda_b)
        if _finite_nonzero(value_a, charges) and _finite_nonzero(value_b, charges):
            finite.append({"lambda_a": str(value_a), "lambda_b": str(value_b)})
    return {
        "V_flux": str(potential),
        "dV_dlambda_a": str(derivative_a),
        "dV_dlambda_b": str(derivative_b),
        "Lambda_bulk_appears_in_eom": bulk in derivative_a.free_symbols or bulk in derivative_b.free_symbols,
        "finite_nonzero_solutions": finite,
        "moduli_fixed": bool(finite),
    }


def run_phase_11AF_execution(
    authorization: ModulusStabilizationAuthorization,
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Add the assumed flux potential and test modulus stationarity.

    MODULI_FIXED_AT_FINITE_VALUE is declared before the equations are solved.
    CLOSED_UNDER_DECLARED_SCOPE is returned only when finite solutions exist.
    """
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": EXECUTION_CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
    }
    provenance_log: list[dict[str, Any]] = [closure_entry]
    if not _authorization_intact(authorization):
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "T09_STATUS": T09_STATUS,
            "detail": "authorization is not the sealed flux input",
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
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    document_before = canonical_json_bytes(phase4c_action_document())
    stationarity = _flux_stationarity()
    document_after = canonical_json_bytes(phase4c_action_document())
    if document_after != document_before:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "frozen action mutated",
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": True,
        }
    moduli_fixed = bool(stationarity["moduli_fixed"])
    observed = EXECUTION_CLOSURE_TARGET if moduli_fixed else "NO_FINITE_STATIONARY_POINT"
    program_status = "CLOSED_UNDER_DECLARED_SCOPE" if moduli_fixed else "NOT_CLOSED"
    provenance_log.append(
        {
            "entry": "flux stationarity",
            "total_action": "S_frozen + integral V_flux",
            "V_flux_added_to_frozen_parameter_list": False,
            "dV_dlambda_a": stationarity["dV_dlambda_a"],
            "dV_dlambda_b": stationarity["dV_dlambda_b"],
            "finite_nonzero_solutions": stationarity["finite_nonzero_solutions"],
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
        "PHASE": PHASE,
        "gate": authorization.gate,
        "PHASE_11AE_STATUS": PHASE_11AE_STATUS,
        "T09_STATUS": T09_STATUS,
        "T09_reopened": False,
        "mechanism": authorization.mechanism,
        "Provenance": Provenance.ASSUMED.value,
        "classification": "NEW PHYSICAL INPUT",
        "derived": False,
        "declaration_hash": authorization.declaration_hash,
        "action_content_hash": digest,
        "frozen_action_modified": False,
        "total_action": "S_frozen + integral V_flux",
        "stationarity": stationarity,
        "closure_comparison": comparison,
        "objective_met": comparison["objective_met"],
        "PROGRAM_CLOSURE_STATUS": program_status,
        "provenance_log": provenance_log,
        "new_parameter_count": 0,
    }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AF_EXECUTION.json"
        forbidden = (
            phase11ad_artifact_dir().resolve(),
            phase11z_artifact_dir().resolve(),
        )
        if any(destination.resolve().is_relative_to(root) for root in forbidden):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(payload) + b"\n")
    return payload


_BALANCED_FORMULA = (
    "V_eff(lambda_a, lambda_b) = (Q_a^2 / lambda_a^2) + T_a * lambda_a^2"
    " + (Q_b^2 / lambda_b^2) + T_b * lambda_b^2"
)
_BALANCED_FIELDS = {
    "mechanism": "Fluxes balanced by Internal Curvature/Tension",
    "potential_formula": _BALANCED_FORMULA,
    "theoretical_scope": "CLASSICAL_GRAVITY_WITH_SOURCES",
    "target_variables": ["lambda_a", "lambda_b"],
}


def _balanced_body() -> dict[str, Any]:
    return {
        "gate": "HUMAN-DECLARED NEW PHYSICAL INPUT",
        "physical_input": "MODULUS_STABILIZATION_BALANCED",
        "classification": "NEW PHYSICAL INPUT",
        "phase": "PHASE_11AF.2",
        "mechanism": _BALANCED_FIELDS["mechanism"],
        "potential_formula": _BALANCED_FIELDS["potential_formula"],
        "theoretical_scope": _BALANCED_FIELDS["theoretical_scope"],
        "target_variables": list(_BALANCED_FIELDS["target_variables"]),
        "provenance": Provenance.ASSUMED.value,
        "derived": False,
        "closure_criterion": EXECUTION_CLOSURE_TARGET,
        "previous_record": "PHASE_11AF NO_FINITE_STATIONARY_POINT",
    }


BALANCED_DECLARATION_HASH = _declaration_hash(_balanced_body())


@immutable
class ModulusStabilizationAuthorization_Balanced:
    """Assumed flux potential balanced by an internal tension term.

    This does not replace the Phase 11AF.1 authorization.
    """

    def __init__(self) -> None:
        body = _balanced_body()
        self.gate = body["gate"]
        self.physical_input = body["physical_input"]
        self.classification = body["classification"]
        self.phase = body["phase"]
        self.mechanism = body["mechanism"]
        self.potential_formula = body["potential_formula"]
        self.theoretical_scope = body["theoretical_scope"]
        self.target_variables = tuple(body["target_variables"])
        self.provenance = body["provenance"]
        self.derived = False
        self.closure_criterion = body["closure_criterion"]
        self.declaration_hash = BALANCED_DECLARATION_HASH
        self._ready = True

    def provenance_entry(self) -> dict[str, Any]:
        return {
            "entry": "MODULUS_STABILIZATION_BALANCED",
            "phase": self.phase,
            "gate": self.gate,
            "classification": self.classification,
            "Provenance": self.provenance,
            "derived": False,
            "mechanism": self.mechanism,
            "potential_formula": self.potential_formula,
            "declaration_hash": self.declaration_hash,
        }


def _balanced_intact(auth: Any) -> bool:
    if type(auth) is not ModulusStabilizationAuthorization_Balanced:
        return False
    if auth.declaration_hash != BALANCED_DECLARATION_HASH:
        return False
    if auth.provenance != Provenance.ASSUMED.value or auth.classification != "NEW PHYSICAL INPUT":
        return False
    if auth.mechanism != _BALANCED_FIELDS["mechanism"]:
        return False
    if auth.potential_formula != _BALANCED_FORMULA:
        return False
    if auth.theoretical_scope != _BALANCED_FIELDS["theoretical_scope"]:
        return False
    if list(auth.target_variables) != ["lambda_a", "lambda_b"]:
        return False
    return _declaration_hash(_balanced_body()) == BALANCED_DECLARATION_HASH


def _real_roots(charge: Any, tension: Any, modulus: Any) -> list[Any]:
    return list(sp.solve(charge**2 - tension * modulus**4, modulus))


def _balanced_stationarity() -> dict[str, Any]:
    """Stationarity of the balanced potential on the competing-tension domain."""
    lambda_a, lambda_b = sp.symbols("lambda_a lambda_b", real=True, nonzero=True)
    charge_a, charge_b = sp.symbols("Q_a Q_b", positive=True)
    tension_a, tension_b = sp.symbols("T_a T_b", positive=True)
    potential = (
        charge_a**2 / lambda_a**2
        + tension_a * lambda_a**2
        + charge_b**2 / lambda_b**2
        + tension_b * lambda_b**2
    )
    derivative_a = sp.factor(sp.diff(potential, lambda_a))
    derivative_b = sp.factor(sp.diff(potential, lambda_b))
    roots_a = _real_roots(charge_a, tension_a, lambda_a)
    roots_b = _real_roots(charge_b, tension_b, lambda_b)
    charges = {charge_a, tension_a, charge_b, tension_b}
    solutions = []
    for value_a in roots_a:
        for value_b in roots_b:
            real_finite = (
                value_a.is_real
                and value_b.is_real
                and value_a.is_finite
                and value_b.is_finite
                and value_a != 0
                and value_b != 0
                and bool(value_a.free_symbols & {charge_a, tension_a})
                and bool(value_b.free_symbols & {charge_b, tension_b})
            )
            if real_finite:
                solutions.append({"lambda_a": str(value_a), "lambda_b": str(value_b)})
    hessian = sp.hessian(potential, [lambda_a, lambda_b])
    sample = {lambda_a: roots_a[-1], lambda_b: roots_b[-1]} if roots_a and roots_b else {}
    hessian_at_minimum = sp.simplify(hessian.subs(sample)) if sample else None
    positive_definite = False
    if hessian_at_minimum is not None:
        positive_definite = bool(
            sp.simplify(hessian_at_minimum[0, 0] - 8 * tension_a) == 0
            and sp.simplify(hessian_at_minimum[1, 1] - 8 * tension_b) == 0
            and sp.simplify(hessian_at_minimum[0, 1]) == 0
        )
    negative_a = sp.symbols("T_a", negative=True)
    negative_roots = sp.solve(charge_a**2 - negative_a * lambda_a**4, lambda_a)
    return {
        "V_eff": str(potential),
        "dV_dlambda_a": str(derivative_a),
        "dV_dlambda_b": str(derivative_b),
        "reality_domain": "T_a > 0 and T_b > 0; Q_a and Q_b nonzero",
        "finite_nonzero_solutions": solutions,
        "solution_count": len(solutions),
        "depends_on_Q_and_T": bool(solutions),
        "hessian_positive_definite_on_domain": positive_definite,
        "real_roots_when_tension_negative": [str(item) for item in negative_roots],
        "moduli_fixed": bool(solutions) and positive_definite and negative_roots == [],
    }


def run_phase_11AF_2_execution(
    authorization: ModulusStabilizationAuthorization_Balanced,
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Test the balanced flux-tension potential without rewriting Phase 11AF.1."""
    previous = _flux_stationarity()
    if previous["moduli_fixed"]:
        return {
            "status": "STOP",
            "PHASE": "PHASE_11AF.2",
            "detail": "previous flux record is not the unresolved repulsive case",
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    previous_entry = {
        "entry": "Phase 11AF.1 failure",
        "previous_phase": "PHASE_11AF",
        "observed": "NO_FINITE_STATIONARY_POINT",
        "PROGRAM_CLOSURE_STATUS": "NOT_CLOSED",
        "previous_record_modified": False,
        "logged_before_balanced_solve": True,
    }
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": EXECUTION_CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
    }
    provenance_log: list[dict[str, Any]] = [previous_entry, closure_entry]
    if not _balanced_intact(authorization):
        return {
            "status": "STOP",
            "PHASE": "PHASE_11AF.2",
            "T09_STATUS": T09_STATUS,
            "detail": "authorization is not the sealed balanced input",
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
            "PHASE": "PHASE_11AF.2",
            "detail": "frozen 4C hash",
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    document_before = canonical_json_bytes(phase4c_action_document())
    stationarity = _balanced_stationarity()
    document_after = canonical_json_bytes(phase4c_action_document())
    if document_after != document_before:
        return {
            "status": "STOP",
            "PHASE": "PHASE_11AF.2",
            "detail": "frozen action mutated",
            "provenance_log": provenance_log,
            "new_parameter_count": 0,
            "frozen_action_modified": True,
        }
    moduli_fixed = bool(stationarity["moduli_fixed"])
    observed = EXECUTION_CLOSURE_TARGET if moduli_fixed else "NO_FINITE_STATIONARY_POINT"
    program_status = "CLOSED_UNDER_DECLARED_SCOPE" if moduli_fixed else "NOT_CLOSED"
    provenance_log.append(
        {
            "entry": "balanced stationarity",
            "total_action": "S_frozen + integral V_eff",
            "V_eff_added_to_frozen_parameter_list": False,
            "solution_count": stationarity["solution_count"],
            "reality_domain": stationarity["reality_domain"],
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
        "PHASE": "PHASE_11AF.2",
        "gate": authorization.gate,
        "T09_STATUS": T09_STATUS,
        "T09_reopened": False,
        "mechanism": authorization.mechanism,
        "Provenance": Provenance.ASSUMED.value,
        "classification": "NEW PHYSICAL INPUT",
        "derived": False,
        "declaration_hash": authorization.declaration_hash,
        "action_content_hash": digest,
        "frozen_action_modified": False,
        "previous_record_modified": False,
        "total_action": "S_frozen + integral V_eff",
        "stationarity": stationarity,
        "closure_comparison": comparison,
        "objective_met": comparison["objective_met"],
        "PROGRAM_CLOSURE_STATUS": program_status,
        "T10_STABILIZED_MODULI": moduli_fixed,
        "provenance_log": provenance_log,
        "new_parameter_count": 0,
    }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AF2_EXECUTION.json"
        forbidden = (
            phase11ad_artifact_dir().resolve(),
            phase11z_artifact_dir().resolve(),
        )
        if any(destination.resolve().is_relative_to(root) for root in forbidden):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(payload) + b"\n")
    return payload
