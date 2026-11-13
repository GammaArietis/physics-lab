"""Phase 11AI.1: containment audit for T07, the F_T identification.

T06 stays pending an injection. This module asks whether F_T is already
a trace, a geometric current, or another frozen combination.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.gravity_internal import minkowski_metric, stress_energy_closed_form
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase5c_gauging import _stress_energy_gauged
from physics_lab.physics.phase5d_gauge_dynamics import _F2, _eta, _independent_F
from physics_lab.physics.phase9_internal_gap import _bianchi_coverage
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae4_degenerate_vacuum import artifact_dir as phase11ae4_artifact_dir
from physics_lab.physics.phase11ae4_degenerate_vacuum import run_phase_11AE_4_synthesis
from physics_lab.physics.phase11ah_t06_containment import artifact_dir as phase11ah_artifact_dir
from physics_lab.physics.phase11ah_t06_containment import run_containment_audit_T06
from physics_lab.physics.phase11o_gravity_matter import artifact_dir as phase11o_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import modulus_mediation_identities
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "CLOSURE_TARGET",
    "T06_STATUS",
    "run_containment_audit_T07",
]

PHASE = "PHASE_11AI.1"
T06_STATUS = "AUDIT_COMPLETED_PENDING_INJECTION"
CLOSURE_TARGET = "F_T_IDENTIFICATION_DERIVED"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ai_artifacts"


def _probe(name: str, found: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe": name,
        "found": found,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "evidence": evidence,
        "closure_target_used_as_filter": False,
    }


def _coincides(left: Any, right: Any) -> bool:
    """Equality with no extra constant factor."""
    return bool(sp.simplify(left - right) == 0)


def _matter_trace(signature: str) -> Any:
    metric, inverse = minkowski_metric(signature)
    chi, kinetic = sp.symbols("chi X", real=True)
    kx, k0, k2 = sp.symbols("kx k0 k2", real=True)
    density = kx * kinetic + k0 + k2 / 2 * chi**2
    slopes = list(sp.symbols("dchi0 dchi1 dchi2 dchi3", real=True))
    tensor = stress_energy_closed_form(density, kinetic, metric, slopes)
    return sp.simplify(sum(inverse[mu, nu] * tensor[mu, nu] for mu in range(4) for nu in range(4)))


def _gauge_trace(signature: str) -> Any:
    normalization = sp.symbols("Z_A", positive=True)
    eta = _eta(signature)
    field_strength, _ = _independent_F()
    invariant = _F2(field_strength, eta)
    tensor = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            contracted = sum(
                field_strength[mu, lam] * sum(field_strength[nu, sig] * eta[lam, sig] for sig in range(4))
                for lam in range(4)
            )
            tensor[mu, nu] = normalization * (
                contracted - sp.Rational(1, 4) * eta[mu, nu] * invariant
            )
    return sp.simplify(sum(eta[mu, nu] * tensor[mu, nu] for mu in range(4) for nu in range(4)))


def _scan(vacuum: dict[str, Any], signature: str) -> list[dict[str, Any]]:
    order_parameter = sp.symbols("F_T")
    rows = json.loads((phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json").read_text(encoding="utf-8"))
    derived_rows = [row for row in rows if str(row.get("provenance", "")).startswith("DERIVED")]
    linked = [str(row.get("EOM", "")) for row in derived_rows if "F_T" in str(row.get("EOM", ""))]
    eom_probe = _probe(
        "eom_4d",
        any(_coincides(order_parameter, sp.sympify(text.split("=", 1)[-1])) for text in linked if "=" in text),
        {
            "derived_row_count": len(derived_rows),
            "equations_naming_F_T": linked,
        },
    )

    bianchi = _bianchi_coverage()
    gravity = json.loads(
        (phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json").read_text(encoding="utf-8")
    )
    current_is_zero = bianchi["bianchi_holds_identically"] is True and bianchi["double_divergence_vanishes_by_antisymmetry"] is True
    current_match = current_is_zero and _coincides(order_parameter, sp.Integer(0))
    bianchi_probe = _probe(
        "bianchi_identity",
        bool(bianchi["new_parameter_relation"]) or current_match,
        {
            "geometric_identity": gravity["bianchi_analysis"]["geometric_identity"],
            "gauge_current": gravity["gauge_current"]["nabla_mu j^mu"],
            "new_parameter_relation": bianchi["new_parameter_relation"],
            "bianchi_current_equals_F_T": current_match,
        },
    )

    matter_trace = _matter_trace(signature)
    gauge_trace = _gauge_trace(signature)
    gauged = _stress_energy_gauged()
    identities = modulus_mediation_identities()
    hidden = sp.symbols("F_X")
    compensator = sp.symbols("F_phi")
    matter_match = _coincides(order_parameter, matter_trace)
    gauge_match = _coincides(order_parameter, gauge_trace)
    hidden_match = _coincides(order_parameter, hidden)
    compensator_match = _coincides(order_parameter, compensator)
    stress_probe = _probe(
        "stress_energy_trace",
        matter_match or gauge_match or hidden_match or compensator_match,
        {
            "matter_trace": str(matter_trace),
            "matter_trace_equals_F_T": matter_match,
            "gauge_trace": str(gauge_trace),
            "gauge_trace_equals_F_T": gauge_match,
            "gauge_kinetic_stress_in_frozen_action": gauged["T_gauge_kinetic"] != "NOT PRESENT",
            "F_T_equals_F_X": hidden_match,
            "F_T_equals_F_phi": compensator_match,
            "F_T_is_INPUT_symbol": identities["F_T_is_INPUT_symbol"],
            "no_T_in_freeze": identities["no_T_in_freeze"],
            "ad_hoc_constant_introduced": False,
        },
    )

    surviving = vacuum["synthesis"]["surviving_class"]
    moduli_text = json.dumps(surviving)
    moduli_probe = _probe(
        "z2_moduli",
        "F_T" in moduli_text,
        {
            "symmetry": vacuum["synthesis"]["symmetry"],
            "V_adm": vacuum["synthesis"]["V_adm"],
            "surviving_class": surviving,
            "class_mentions_F_T": "F_T" in moduli_text,
        },
    )
    return [eom_probe, bianchi_probe, stress_probe, moduli_probe]


def run_containment_audit_T07(
    closure_target: str | None = None,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Scan for an existing algebraic identification of F_T.

    F_T_IDENTIFICATION_DERIVED is logged before the scan. A free factor
    does not count as an identification.
    """
    if closure_target is not None and closure_target != CLOSURE_TARGET:
        return {
            "status": "CLOSURE_CRITERION_REFUSED",
            "PHASE": PHASE,
            "topic": "T07: F_T identification",
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
            "T07_activated": False,
        }
    prior = run_containment_audit_T06(write_artifacts=False)
    if prior.get("Provenance") != "NOT_FOUND" or prior.get("T06_activated") is not False:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "Phase 11AH.1 is not the completed NOT_FOUND audit",
            "scanned": False,
            "new_parameter_count": 0,
            "T07_activated": False,
        }
    t06_entry = {
        "entry": "T06 status",
        "T06_STATUS": T06_STATUS,
        "previous_audit": "PHASE_11AH.1",
        "previous_audit_provenance": prior["Provenance"],
        "injection_performed": False,
        "logged_before_t07_scan": True,
    }
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
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
            "provenance_log": [t06_entry, closure_entry],
            "detail": "frozen 4C hash",
            "new_parameter_count": 0,
            "T07_activated": False,
        }
    parents = {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "EOM": phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json",
        "11O": phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json",
        "11AE4": phase11ae4_artifact_dir() / "PHASE_11AE4_SYNTHESIS.json",
        "11AH": phase11ah_artifact_dir() / "PHASE_11AH_T06_CONTAINMENT.json",
    }
    before = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    decision = json.loads(parents["11AD"].read_text(encoding="utf-8")).get("decision_map") or {}
    if decision.get("T07") != "REQUIRES_EXPLICIT_ASSUMPTION":
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "provenance_log": [t06_entry, closure_entry],
            "detail": "parent T07 decision",
            "new_parameter_count": 0,
            "T07_activated": False,
        }
    document_before = canonical_json_bytes(phase4c_action_document())
    vacuum = run_phase_11AE_4_synthesis(write_artifacts=False)
    if vacuum.get("PROGRAM_CLOSURE_STATUS") != "CLOSED_UNDER_DECLARED_SCOPE" or vacuum.get("synthesis", {}).get("symmetry") != "Z_2":
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "Z_2 moduli class is not the closed Phase 11AE.4 record",
            "scanned": False,
            "provenance_log": [t06_entry, closure_entry],
            "new_parameter_count": 0,
            "T07_activated": False,
        }
    probes = _scan(vacuum, signature)
    document_after = canonical_json_bytes(phase4c_action_document())
    after = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    if document_after != document_before or after != before:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "detail": "parent artifact mutated",
            "scanned": False,
            "new_parameter_count": 0,
            "T07_activated": False,
        }
    found = any(item["found"] for item in probes)
    provenance_log = [t06_entry, closure_entry, *probes]
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "topic": "T07: F_T identification",
        "T06_STATUS": T06_STATUS,
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "closure_target_used_as_filter": False,
        "scanned": True,
        "action_content_hash": digest,
        "probes": probes,
        "provenance_log": provenance_log,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "F_T_IDENTIFICATION_STATUS": "DERIVED" if found else "NOT_FOUND",
        "T07_activated": False,
        "new_parameter_count": 0,
        "frozen_action_modified": False,
    }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AI_T07_CONTAINMENT.json"
        forbidden = (
            phase11ad_artifact_dir().resolve(),
            phase11ae4_artifact_dir().resolve(),
            phase11ah_artifact_dir().resolve(),
            phase10b8_artifact_dir().resolve(),
            phase11o_artifact_dir().resolve(),
        )
        if any(destination.resolve().is_relative_to(root) for root in forbidden):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(
            canonical_json_bytes(
                {
                    "T06_STATUS": T06_STATUS,
                    "topic": payload["topic"],
                    "Provenance": payload["Provenance"],
                    "log": provenance_log,
                }
            )
            + b"\n"
        )
    return payload
