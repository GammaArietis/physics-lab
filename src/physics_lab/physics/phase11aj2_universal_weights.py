"""Phase 11AJ.2: assumed universal weight Z_A = c_W * (lambda_a * lambda_b).

The Phase 11AJ.1 audit stays NOT_FOUND. The relation is applied only on
an execution copy, using the discrete Z_2 moduli.
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
from physics_lab.physics.phase11ae3_discrete_vacuum import _magnitude_symbols
from physics_lab.physics.phase11aj_universal_weights import artifact_dir as phase11aj_artifact_dir
from physics_lab.physics.phase11aj_universal_weights import run_containment_audit_T08
from physics_lab.physics.spacetime import MOSTLY_PLUS, canonical_prefactor

__all__ = [
    "CLOSURE_TARGET",
    "WEIGHT_FORMULA",
    "FrozenAuthorizationError",
    "UniversalWeightsAuthorization",
    "run_phase_11AJ_2_execution",
]

PHASE = "PHASE_11AJ.2"
CLOSURE_TARGET = "NEW_PARAMETER_FREE_RELATION"
WEIGHT_FORMULA = "Z_A = c_W * (lambda_a * lambda_b)"
_FIELDS = {
    "constraint_type": "Universal Modular Weight T08",
    "formula": WEIGHT_FORMULA,
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
    return Path(__file__).resolve().parent / "phase11aj2_artifacts"


def _declaration_hash(body: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(body)).hexdigest()


def _authorization_body() -> dict[str, Any]:
    return {
        "gate": "HUMAN-DECLARED NEW PHYSICAL INPUT",
        "classification": "NEW PHYSICAL INPUT",
        "phase": PHASE,
        "constraint_type": _FIELDS["constraint_type"],
        "formula": _FIELDS["formula"],
        "theoretical_scope": _FIELDS["theoretical_scope"],
        "provenance": Provenance.ASSUMED.value,
        "derived": False,
        "closure_criterion": CLOSURE_TARGET,
        "previous_audit": "PHASE_11AJ.1 NOT_FOUND",
    }


DECLARATION_HASH = _declaration_hash(_authorization_body())


@immutable
class UniversalWeightsAuthorization:
    """Assumed modulus-gauge weight. It is not derived from the frozen action."""

    def __init__(self) -> None:
        body = _authorization_body()
        self.gate = body["gate"]
        self.classification = body["classification"]
        self.phase = body["phase"]
        self.constraint_type = body["constraint_type"]
        self.formula = body["formula"]
        self.theoretical_scope = body["theoretical_scope"]
        self.provenance = body["provenance"]
        self.derived = False
        self.closure_criterion = body["closure_criterion"]
        self.declaration_hash = DECLARATION_HASH
        self._ready = True

    def provenance_entry(self) -> dict[str, Any]:
        return {
            "entry": "UniversalWeightsAuthorization",
            "phase": self.phase,
            "gate": self.gate,
            "classification": self.classification,
            "Provenance": self.provenance,
            "derived": False,
            "constraint_type": self.constraint_type,
            "formula": self.formula,
            "theoretical_scope": self.theoretical_scope,
            "declaration_hash": self.declaration_hash,
        }


def _authorization_intact(auth: Any) -> bool:
    if type(auth) is not UniversalWeightsAuthorization:
        return False
    if auth.declaration_hash != DECLARATION_HASH:
        return False
    if auth.provenance != Provenance.ASSUMED.value or auth.classification != "NEW PHYSICAL INPUT":
        return False
    if auth.constraint_type != _FIELDS["constraint_type"]:
        return False
    if auth.formula != WEIGHT_FORMULA:
        return False
    if auth.theoretical_scope != _FIELDS["theoretical_scope"]:
        return False
    if auth.gate != "HUMAN-DECLARED NEW PHYSICAL INPUT" or auth.derived is not False:
        return False
    return _declaration_hash(_authorization_body()) == DECLARATION_HASH


def _execution_copy(signature: str, surviving: list[list[int]]) -> dict[str, Any]:
    action_copy = copy.deepcopy(phase4c_action_document())
    action_sites = canonical_json_bytes(action_copy).decode("utf-8").count("Z_A")
    rows = json.loads((phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json").read_text(encoding="utf-8"))
    eom_copy = copy.deepcopy(rows)
    eom_sites = 0
    for row in eom_copy:
        text = str(row.get("EOM", ""))
        eom_sites += text.count("Z_A")
        row["EOM"] = text.replace("Z_A", "(c_W*(lambda_a*lambda_b))")
    magnitudes = _magnitude_symbols()
    coupling, normalization = sp.symbols("c_W Z_A")
    kinetic = canonical_prefactor(signature)
    curvature = sp.symbols("c_H", real=True, nonzero=True)
    products = []
    corners = []
    for signs in surviving:
        lambda_a = sp.simplify(signs[0] * magnitudes["lambda_a"])
        lambda_b = sp.simplify(signs[1] * magnitudes["lambda_b"])
        product = sp.simplify(lambda_a * lambda_b)
        products.append(product)
        mass_a = sp.simplify(implemented_branch_II_m2(curvature, kinetic, lambda_a, signature))
        mass_b = sp.simplify(implemented_branch_II_m2(curvature, kinetic, lambda_b, signature))
        corners.append(
            {
                "lambda_signs": list(signs),
                "lambda_product": str(product),
                "Z_A": str(sp.simplify(coupling * product)),
                "mass_a2": str(mass_a),
                "mass_b2": str(mass_b),
                "mass_depends_on_c_W": coupling in mass_a.free_symbols or coupling in mass_b.free_symbols,
            }
        )
    same_product = bool(products) and all(sp.simplify(item - products[0]) == 0 for item in products)
    solved = sp.solve(sp.Eq(normalization, coupling * products[0]), coupling) if same_product else []
    coupling_value = sp.simplify(solved[0]) if len(solved) == 1 else None
    unique_absolute = bool(coupling_value is not None and coupling_value.is_number)
    gauge_normalization = sp.simplify(coupling * products[0]) if products else coupling
    ratio = sp.simplify(
        implemented_branch_II_m2(curvature, kinetic, magnitudes["lambda_a"], signature) / magnitudes["Q_a"]
    )
    ratio_after = sp.simplify(ratio.subs(normalization, coupling * products[0])) if products else ratio
    ratio_unchanged = bool(sp.simplify(ratio_after - ratio) == 0)
    parameter_free = ratio_after.free_symbols == set()
    absorbed = coupling in ratio.free_symbols and coupling not in ratio_after.free_symbols
    frozen_ids = [row["id"] for row in action_copy["parameters"]]
    constrained = {str(symbol) for symbol in gauge_normalization.free_symbols} & set(frozen_ids)
    generated = unique_absolute or bool(gauge_normalization.is_number) or (parameter_free and not ratio_unchanged)
    return {
        "execution_copy_only": True,
        "action_substitution_sites": action_sites,
        "eom_substitution_sites": eom_sites,
        "eom_changed": eom_sites != 0,
        "constraint_on_execution_copy": WEIGHT_FORMULA,
        "orbit": corners,
        "orbit_product_common": same_product,
        "c_W_solution": None if coupling_value is None else str(coupling_value),
        "c_W_is_unique_absolute_value": unique_absolute,
        "c_W_remains_free": not unique_absolute,
        "c_W_absorbed": absorbed,
        "gauge_normalization_is_number": bool(gauge_normalization.is_number),
        "charge_is_geometric_constant": bool(magnitudes["Q_a"].is_number),
        "mass_charge_ratio_unchanged": ratio_unchanged,
        "mass_charge_ratio_parameter_free": parameter_free,
        "frozen_parameters_constrained": sorted(constrained),
        "parameters_removed": 0,
        "execution_copy_adds_c_W": True,
        "c_W_added_to_frozen_parameter_list": False,
        "parameter_free_relation": generated,
    }


def run_phase_11AJ_2_execution(
    authorization: UniversalWeightsAuthorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Test whether the universal weight removes a free parameter.

    NEW_PARAMETER_FREE_RELATION is logged before that test.
    """
    prior = run_containment_audit_T08(write_artifacts=False)
    if prior.get("Provenance") != "NOT_FOUND" or prior.get("T08_activated") is not False:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "Phase 11AJ.1 is not the NOT_FOUND audit",
            "evaluated": False,
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    spectrum = next(row for row in prior["probes"] if row["probe"] == "internal_spectrum_and_z2_moduli")
    surviving = spectrum["evidence"]["surviving_class"]
    audit_entry = {
        "entry": "Phase 11AJ.1 audit",
        "previous_phase": "PHASE_11AJ.1",
        "previous_provenance": prior["Provenance"],
        "T07_STATUS": prior["T07_STATUS"],
        "previous_record_modified": False,
        "logged_before_weight_execution": True,
    }
    opening = {
        "entry": "Phase 11AJ.2 opening",
        "PHASE": PHASE,
        "topic": "T08: universal f_a(T) / fixed weights",
        "orbit_source": "PHASE_11AE.4",
    }
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "closure_target_used_as_filter": False,
    }
    provenance_log: list[dict[str, Any]] = [audit_entry, opening, closure_entry]
    if not _authorization_intact(authorization):
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "authorization is not the sealed weight constraint",
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
        "11AJ": phase11aj_artifact_dir() / "PHASE_11AJ_T08_CONTAINMENT.json",
        "EOM": phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json",
    }
    before = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    document_before = canonical_json_bytes(phase4c_action_document())
    analysis = _execution_copy(signature, surviving)
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
            "entry": "universal weight on execution copy",
            "formula": authorization.formula,
            "action_substitution_sites": analysis["action_substitution_sites"],
            "eom_substitution_sites": analysis["eom_substitution_sites"],
            "c_W_is_unique_absolute_value": analysis["c_W_is_unique_absolute_value"],
            "c_W_absorbed": analysis["c_W_absorbed"],
            "mass_charge_ratio_parameter_free": analysis["mass_charge_ratio_parameter_free"],
            "c_W_added_to_frozen_parameter_list": False,
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
        "constraint_type": authorization.constraint_type,
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
        destination = artifact_dir() / "PHASE_11AJ2_EXECUTION.json"
        forbidden = (
            phase11ad_artifact_dir().resolve(),
            phase11aj_artifact_dir().resolve(),
            phase10b8_artifact_dir().resolve(),
        )
        if any(destination.resolve().is_relative_to(root) for root in forbidden):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(payload) + b"\n")
    return payload
