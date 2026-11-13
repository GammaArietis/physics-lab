"""Phase 11AE execution: sealed vacuum-selection authorization.

The containment audit recorded VACUUM_SELECTION_PRINCIPLE as NOT_FOUND.
This module does not reclassify that result. It records one human-declared
physical input, seals it, and evaluates only the consequences of that input.
Modulus stabilization (T10) and quantum SUGRA (T11) stay deactivated.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.core.provenance import Provenance
from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae_vacuum_selection import artifact_dir as phase11ae_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import QuantumEffectivePotential
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11u_supergravity import artifact_dir as phase11u_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir

__all__ = [
    "CLOSURE_CRITERION",
    "FrozenAuthorizationError",
    "SEALED_DECLARATION_HASH",
    "VACUUM_SELECTION_FIELDS",
    "VacuumSelectionAuthorization",
    "immutable",
    "run_phase_11AE_execution",
]

PHASE = "PHASE_11AE_EXECUTION"
GATE = "HUMAN-DECLARED NEW PHYSICAL INPUT"
CLOSURE_CRITERION = "DOMAIN_REDUCTION"
STATEMENT = "phi_vac in argmin_{phi in V_adm} E[phi]"

VACUUM_SELECTION_FIELDS: dict[str, Any] = {
    "functional_E": "Potenziale Efficace (Quantum Effective Potential)",
    "admissible_space_V_adm": "Spazio dei Moduli (configurazioni interne dei campi scalari)",
    "constraints": ["Invarianza di Lorentz 4D", "Covarianza Generale"],
    "theoretical_scope": "QFT",
    "minimization_type": "LOCAL_MINIMUM",
    "degeneracy_allowed": True,
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


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def _canonical_body() -> dict[str, Any]:
    return {
        "gate": GATE,
        "physical_input": "VACUUM_SELECTION_PRINCIPLE",
        "mathematical_statement": STATEMENT,
        "functional_E": VACUUM_SELECTION_FIELDS["functional_E"],
        "admissible_space_V_adm": VACUUM_SELECTION_FIELDS["admissible_space_V_adm"],
        "constraints": list(VACUUM_SELECTION_FIELDS["constraints"]),
        "theoretical_scope": VACUUM_SELECTION_FIELDS["theoretical_scope"],
        "minimization_type": VACUUM_SELECTION_FIELDS["minimization_type"],
        "degeneracy_allowed": VACUUM_SELECTION_FIELDS["degeneracy_allowed"],
        "T10_modulus_stabilization": "DEACTIVATED",
        "T11_quantum_sugra": "DEACTIVATED",
        "provenance": Provenance.ASSUMED.value,
        "derived": False,
        "closure_criterion": CLOSURE_CRITERION,
    }


SEALED_DECLARATION_HASH = _content_hash(_canonical_body())


@immutable
class VacuumSelectionAuthorization:
    """HUMAN-DECLARED NEW PHYSICAL INPUT for VACUUM_SELECTION_PRINCIPLE.

    The physical fields are the agreed configuration. They are not derived
    from the containment audit, and they cannot be replaced after construction.
    """

    def __init__(self) -> None:
        body = _canonical_body()
        self.gate = body["gate"]
        self.physical_input = body["physical_input"]
        self.mathematical_statement = body["mathematical_statement"]
        self.functional_E = body["functional_E"]
        self.admissible_space_V_adm = body["admissible_space_V_adm"]
        self.constraints = tuple(body["constraints"])
        self.theoretical_scope = body["theoretical_scope"]
        self.minimization_type = body["minimization_type"]
        self.degeneracy_allowed = body["degeneracy_allowed"]
        self.T10_modulus_stabilization = body["T10_modulus_stabilization"]
        self.T11_quantum_sugra = body["T11_quantum_sugra"]
        self.provenance = body["provenance"]
        self.derived = False
        self.closure_criterion = body["closure_criterion"]
        self.declaration_hash = SEALED_DECLARATION_HASH
        self._ready = True

    def provenance_entry(self) -> dict[str, Any]:
        return {
            "entry": "VACUUM_SELECTION_PRINCIPLE",
            "gate": self.gate,
            "Provenance": self.provenance,
            "derived": False,
            "declaration_hash": self.declaration_hash,
            "functional_E": self.functional_E,
            "admissible_space_V_adm": self.admissible_space_V_adm,
            "constraints": list(self.constraints),
            "theoretical_scope": self.theoretical_scope,
            "minimization_type": self.minimization_type,
            "degeneracy_allowed": self.degeneracy_allowed,
        }


def _authorization_intact(auth: Any) -> bool:
    if type(auth) is not VacuumSelectionAuthorization:
        return False
    if auth.declaration_hash != SEALED_DECLARATION_HASH:
        return False
    if auth.provenance != Provenance.ASSUMED.value or auth.derived is not False:
        return False
    if auth.theoretical_scope != "QFT":
        return False
    if auth.minimization_type != "LOCAL_MINIMUM" or auth.degeneracy_allowed is not True:
        return False
    if list(auth.constraints) != list(VACUUM_SELECTION_FIELDS["constraints"]):
        return False
    if auth.functional_E != VACUUM_SELECTION_FIELDS["functional_E"]:
        return False
    if auth.admissible_space_V_adm != VACUUM_SELECTION_FIELDS["admissible_space_V_adm"]:
        return False
    if auth.T10_modulus_stabilization != "DEACTIVATED":
        return False
    if auth.T11_quantum_sugra != "DEACTIVATED":
        return False
    if auth.closure_criterion != CLOSURE_CRITERION:
        return False
    return _content_hash(_canonical_body()) == SEALED_DECLARATION_HASH


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ae_execution_artifacts"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parent_paths() -> dict[str, Path]:
    return {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "11AE": phase11ae_artifact_dir() / "PHASE_11AE_VACUUM_SELECTION.json",
        "11P": phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json",
        "11Z": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
        "11U": phase11u_artifact_dir() / "PHASE_11U_SUPERGRAVITY.json",
    }


def _deactivated_controls(loaded: dict[str, Any]) -> dict[str, Any] | None:
    decision = loaded["11AD"].get("decision_map") or {}
    stabilization = loaded["11Z"].get("stabilization") or {}
    vacuum_energy = loaded["11U"].get("vacuum_energy") or {}
    coverage = loaded["11P"].get("existing_coverage_audit") or {}
    t10_off = (
        decision.get("T10") == "REQUIRES_NEW_PHYSICAL_INPUT"
        and stabilization.get("status") == "NOT_FOUND"
        and stabilization.get("vacuum_selected") is False
    )
    t11_off = (
        decision.get("T11") == "REQUIRES_NEW_PHYSICAL_INPUT"
        and vacuum_energy.get("selected_branch") is None
    )
    if not t10_off or not t11_off:
        return None
    if loaded["11AE"].get("VACUUM_SELECTION_INPUT_STATUS") != "PRINCIPLE_UNSPECIFIED":
        return None
    if coverage.get("quantum_effective_potential") != "UNTESTED":
        return None
    return {
        "T10_modulus_stabilization": "DEACTIVATED",
        "T11_quantum_sugra": "DEACTIVATED",
        "parent_T10": decision.get("T10"),
        "parent_T11": decision.get("T11"),
        "quantum_effective_potential_in_frozen_laboratory": coverage.get("quantum_effective_potential"),
    }


def _minimize(auth: VacuumSelectionAuthorization, controls: dict[str, Any]) -> dict[str, Any]:
    """Apply phi_vac in argmin_{phi in V_adm} E[phi] with the assumed Coleman-Weinberg potential.

    The historical 11P record stays UNTESTED. E is the sealed one-loop functional.
    The Phase 4C mass eigenvalues do not depend on phi, so a flat E does not cut V_adm.
    """
    potential = QuantumEffectivePotential()
    if potential.provenance != Provenance.ASSUMED.value or potential.gate != GATE:
        raise RuntimeError("effective potential is not the sealed assumed input")
    evaluated = potential.evaluate()
    flat = bool(evaluated["flat_on_V_adm"])
    domain_reduced = False if flat else bool(evaluated["domain_reduced"])
    observed = "DOMAIN_REDUCTION" if domain_reduced else "DOMAIN_UNREDUCED"
    return {
        "statement": auth.mathematical_statement,
        "minimization_type": auth.minimization_type,
        "degeneracy_allowed": auth.degeneracy_allowed,
        "uniqueness_forced": False,
        "E_formula_supplied": True,
        "functional": "QuantumEffectivePotential",
        "functional_provenance": potential.provenance,
        "functional_hash": potential.declaration_hash,
        "quadratic_substituted_for_E": False,
        "phi_vac": evaluated["local_minimum_set"] if flat else None,
        "argmin_status": "EVALUATED" if evaluated["gradient_vanishes"] else "NOT_EVALUATED",
        "local_minimum_set_constructed": flat,
        "isolated_local_minimum": evaluated["isolated_local_minimum"],
        "M2_depends_on_phi": evaluated["M2_depends_on_phi"],
        "domain_before": auth.admissible_space_V_adm,
        "domain_after": auth.admissible_space_V_adm if not domain_reduced else evaluated["local_minimum_set"],
        "domain_reduced": domain_reduced,
        "observed": observed,
        "T10_modulus_stabilization": controls["T10_modulus_stabilization"],
        "T11_quantum_sugra": controls["T11_quantum_sugra"],
    }


def _closure_comparison(minimization: dict[str, Any]) -> dict[str, Any]:
    observed = minimization["observed"]
    return {
        "entry": "closure comparison",
        "criterion": CLOSURE_CRITERION,
        "observed": observed,
        "objective_met": observed == CLOSURE_CRITERION,
        "post_hoc_validation": False,
        "closure_target_used_as_filter": False,
    }


def _write_log(payload: dict[str, Any]) -> None:
    destination = artifact_dir() / "PHASE_11AE_EXECUTION_PROVENANCE.json"
    forbidden = (
        phase11ad_artifact_dir().resolve(),
        phase11ae_artifact_dir().resolve(),
        phase11p_artifact_dir().resolve(),
        phase11z_artifact_dir().resolve(),
        phase11u_artifact_dir().resolve(),
    )
    resolved = destination.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_json_bytes(payload) + b"\n")


def _stop(detail: str, provenance_log: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "STOP",
        "PHASE": PHASE,
        "scientific_analysis": None,
        "detail": detail,
        "provenance_log": provenance_log,
        "principle_activated_as_derived": False,
        "new_parameter_count": 0,
        "T10_modulus_stabilization": "DEACTIVATED",
        "T11_quantum_sugra": "DEACTIVATED",
    }


def run_phase_11AE_execution(
    authorization: VacuumSelectionAuthorization,
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Evaluate the sealed principle against the predeclared closure criterion.

    DOMAIN_REDUCTION is fixed before the minimization. The comparison does not
    choose a different objective afterwards.
    """
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_CRITERION,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
    }
    provenance_log: list[dict[str, Any]] = [closure_entry]
    if not _authorization_intact(authorization):
        return _stop("authorization is not the sealed HUMAN-DECLARED input", provenance_log)

    provenance_log.append(authorization.provenance_entry())
    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return _stop("frozen 4C hash", provenance_log)

    paths = _parent_paths()
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return _stop("missing " + ", ".join(missing), provenance_log)
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    controls = _deactivated_controls(loaded)
    if controls is None:
        return _stop("T10 or T11 is not deactivated", provenance_log)
    if controls["T10_modulus_stabilization"] != "DEACTIVATED":
        return _stop("T10 modulus stabilization is not deactivated", provenance_log)
    if controls["T11_quantum_sugra"] != "DEACTIVATED":
        return _stop("T11 quantum sugra is not deactivated", provenance_log)

    provenance_log.append(
        {
            "entry": "module controls",
            "T10_modulus_stabilization": "DEACTIVATED",
            "T11_quantum_sugra": "DEACTIVATED",
        }
    )
    minimization = _minimize(authorization, controls)
    comparison = _closure_comparison(minimization)
    provenance_log.append(
        {
            "entry": "minimization",
            "statement": minimization["statement"],
            "argmin_status": minimization["argmin_status"],
            "phi_vac": minimization["phi_vac"],
            "Provenance": authorization.provenance,
            "domain_reduced": minimization["domain_reduced"],
        }
    )
    provenance_log.append(comparison)
    if provenance_log[0]["closure_target"] != CLOSURE_CRITERION:
        return _stop("closure criterion changed during execution", provenance_log)
    if authorization.provenance != Provenance.ASSUMED.value:
        return _stop("authorization provenance is not ASSUMED", provenance_log)

    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "gate": GATE,
        "action_content_hash": digest,
        "declaration_hash": authorization.declaration_hash,
        "provenance_log": provenance_log,
        "Provenance": Provenance.ASSUMED.value,
        "derived": False,
        "principle_activated_as_derived": False,
        "minimization": minimization,
        "closure_comparison": comparison,
        "objective_met": comparison["objective_met"],
        "observed": minimization["observed"],
        "phi_vac": minimization["phi_vac"],
        "T10_modulus_stabilization": "DEACTIVATED",
        "T11_quantum_sugra": "DEACTIVATED",
        "new_parameter_count": 0,
        "parents_unchanged": True,
    }
    if write_artifacts:
        _write_log(
            {
                "gate": GATE,
                "Provenance": Provenance.ASSUMED.value,
                "declaration_hash": authorization.declaration_hash,
                "log": provenance_log,
            }
        )
    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return _stop("parent artifact mutated", [closure_entry])
    return payload
