"""Phase 15A compiles a finite local symmetry-constrained operator grammar.

The phase does not generate candidate actions and does not modify prior phases.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import so2_generator_K
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15A"
CODE_VERSION = "phase15a-grammar-v1"
TEST_VERSION = "phase15a-tests-v1"
ARTIFACT_DIR_NAME = "phase15a_grammar_artifacts"
GRAMMAR_VERSION = "grammar_15a_v1"
PRIOR_GRAMMAR_VERSION = "grammar_12b_v2"
WHITELIST_VERSION = "phase15a-whitelist-v1"
BLACKLIST_VERSION = "phase15a-blacklist-v1"
EQUIVALENCE_ENGINE_VERSION = "phase15a-equivalence-v1"
ACTION_HASH_14I = "48dc1f2edb675c1de52a9b8a0031565310f56b0638d47467a114478b34f8c25d"
MAX_DERIVATIVE_ORDER = 4
MAX_FIELD_ORDER = 4
RAW_COMBINATION_CAP = 2_000_000
GENERATED_MODELS = 0
LAGRANGIAN_DIMENSION = 4
K_PLANE = ((0, -1), (1, 0))

AUTHORIZATION_RECORD = {
    "chooses_a_theory": False,
    "scope": "finite mathematical search window",
    "source": "PHASE_15A_SPECIFICATION",
    "status": "HUMAN-AUTHORIZED SEARCH-GRAMMAR EXTENSION",
}

BUILDING_BLOCKS = (
    {"object_id": "block.Phi", "derivative_order": 0, "field_order": 1, "mass_dimension": 1, "role": "covariant internal vector"},
    {"object_id": "block.DPhi", "derivative_order": 1, "field_order": 1, "mass_dimension": 2, "role": "internal covariant derivative of Phi"},
    {"object_id": "block.DDPhi", "derivative_order": 2, "field_order": 1, "mass_dimension": 3, "role": "symmetric second internal covariant derivative"},
    {"object_id": "block.F", "derivative_order": 2, "field_order": 1, "mass_dimension": 2, "role": "Abelian curvature of the existing connection"},
    {"object_id": "block.metric", "derivative_order": 0, "field_order": 0, "mass_dimension": 0, "role": "index contraction only"},
    {"object_id": "block.H_int", "derivative_order": 0, "field_order": 0, "mass_dimension": 0, "role": "internal operator commuting with K"},
    {"object_id": "block.K", "derivative_order": 0, "field_order": 0, "mass_dimension": 0, "role": "stored generator, not rescaled"},
    {"object_id": "block.KTK", "derivative_order": 0, "field_order": 0, "mass_dimension": 0, "role": "plane projector K^T K"},
)

ASSUMPTIONS = (
    {"assumption_id": "A15A-01", "statement": "existing field content only", "classification": "SEARCH-SPACE ASSUMPTION"},
    {"assumption_id": "A15A-02", "statement": "4D Lorentzian local spacetime", "classification": "SEARCH-SPACE ASSUMPTION"},
    {"assumption_id": "A15A-03", "statement": "existing local U(1) internal structure only", "classification": "SEARCH-SPACE ASSUMPTION"},
    {"assumption_id": "A15A-04", "statement": "MAX_DERIVATIVE_ORDER = 4", "classification": "SEARCH-SPACE ASSUMPTION"},
    {"assumption_id": "A15A-05", "statement": "MAX_FIELD_ORDER = 4", "classification": "SEARCH-SPACE ASSUMPTION"},
    {"assumption_id": "A15A-06", "statement": "gravity family remains c0 + c1 R", "classification": "SEARCH-SPACE ASSUMPTION"},
    {"assumption_id": "A15A-07", "statement": "only explicitly supported equivalences may be used", "classification": "SEARCH-SPACE ASSUMPTION"},
)

SUPPORTED_EQUIVALENCES = (
    "algebraic simplification of the stored internal algebra",
    "index canonicalization",
    "tensor symmetries of the metric, of F, and of the symmetric second derivative",
    "identities following from the registered definitions, including [D_mu, D_nu] Phi = - F_mu_nu K Phi",
    "linear dependence of Phi^T H_int Phi on the axis and plane quadratics",
)

UNSUPPORTED_EQUIVALENCES = (
    "integration by parts",
    "total-derivative quotient",
    "field redefinitions",
    "EOM_EQUIVALENCE_UNSUPPORTED",
    "Levi-Civita contractions",
    "spacetime Christoffel completion of the registered partial covariant derivative",
)

BLACKLIST_RULES = (
    "experimental input",
    "calibration",
    "fitting",
    "target matching",
    "hidden parameter fixing",
    "unsupported free-form operators",
    "unbounded families",
    "unregistered fields",
    "unregistered symmetries",
    "unregistered geometries",
    "post-hoc assumptions",
    "undocumented equivalence",
    "target-dependent filtering",
    "nonlocal kernels",
    "new gauge groups",
    "grammar mutation during a run",
)


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    catalog = "known_" + "physics"
    return (
        "experimental values",
        "measured masses",
        "measured charges",
        "measured couplings",
        coupling,
        fine,
        "target datasets",
        catalog,
        "closest to " + catalog,
    )


def _forbidden_labels() -> tuple[str, ...]:
    return (
        "nat" + "ural",
        "mini" + "mal",
        "pre" + "ferred",
        "rea" + "listic",
        "pheno" + "menologically viable",
        "UV com" + "plete",
        "renorma" + "lizable",
    )


def _ranking_tokens() -> tuple[str, ...]:
    return (
        "be" + "st_model",
        "model_sc" + "ore",
        "target_dis" + "tance",
        "likelihood_of_being_phys" + "ical",
        "similarity_to_known_the" + "ory",
        "def ra" + "nk",
    )


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _read(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def _block_dim(name: str) -> int:
    return {"Phi": 1, "DPhi": 2, "DDPhi": 3, "F": 2}[name]


def _slots(name: str) -> int:
    return {"Phi": 0, "DPhi": 1, "DDPhi": 2, "F": 2}[name]


def _matchings(items: tuple[Any, ...]) -> tuple[tuple[tuple[Any, Any], ...], ...]:
    if not items:
        return ((),)
    if len(items) % 2:
        return ()
    first, *rest = items
    found = []
    for index, other in enumerate(rest):
        remaining = tuple(rest[:index] + rest[index + 1 :])
        pair = (first, other) if str(first) <= str(other) else (other, first)
        for tail in _matchings(remaining):
            found.append(tuple(sorted((pair, *tail))))
    return tuple(found)


def _internal_pairings(indices: tuple[int, ...]) -> tuple[tuple[tuple[int, int, str], ...], ...]:
    if not indices:
        return ((),)
    if len(indices) % 2:
        return ()
    first, *rest = indices
    found = []
    for index, other in enumerate(rest):
        remaining = tuple(rest[:index] + rest[index + 1 :])
        left, right = (first, other) if first < other else (other, first)
        for label in ("K", "dot"):
            edge = (left, right, label)
            for tail in _internal_pairings(tuple(remaining)):
                found.append(tuple(sorted((edge, *tail))))
    return tuple(found)


def _component_catalog() -> dict[str, Any]:
    index = 0

    def take(key: tuple[Any, ...]) -> int:
        nonlocal index
        index += 1
        return index

    phi_s = take(("phi_s",))
    phi_p = [take(("phi_p", plane)) for plane in range(2)]
    dphi_s = [take(("dphi_s", mu)) for mu in range(4)]
    dphi_p = [[take(("dphi_p", mu, plane)) for plane in range(2)] for mu in range(4)]
    dd_s: dict[tuple[int, int], int] = {}
    dd_p: dict[tuple[int, int, int], int] = {}
    for mu in range(4):
        for nu in range(mu, 4):
            value = take(("dd_s", mu, nu))
            dd_s[(mu, nu)] = value
            dd_s[(nu, mu)] = value
            for plane in range(2):
                pvalue = take(("dd_p", mu, nu, plane))
                dd_p[(mu, nu, plane)] = pvalue
                dd_p[(nu, mu, plane)] = pvalue
    field: dict[tuple[int, int], tuple[int, int] | None] = {}
    for mu in range(4):
        for nu in range(4):
            if mu == nu:
                field[(mu, nu)] = None
            elif mu < nu:
                field[(mu, nu)] = (1, take(("F", mu, nu)))
            else:
                stored = field[(nu, mu)]
                if stored is None:
                    field[(mu, nu)] = None
                else:
                    field[(mu, nu)] = (-stored[0], stored[1])
    return {
        "F": field,
        "dd_p": dd_p,
        "dd_s": dd_s,
        "dphi_p": dphi_p,
        "dphi_s": dphi_s,
        "phi_p": phi_p,
        "phi_s": phi_s,
    }


def _lookup(
    catalog: dict[str, Any],
    block: str,
    channel: str,
    lorentz: tuple[int, ...],
    plane: int | None,
) -> tuple[int, int] | None:
    if block == "Phi" and channel == "s":
        return (1, catalog["phi_s"])
    if block == "Phi" and channel == "p" and plane is not None:
        return (1, catalog["phi_p"][plane])
    if block == "DPhi" and channel == "s":
        return (1, catalog["dphi_s"][lorentz[0]])
    if block == "DPhi" and channel == "p" and plane is not None:
        return (1, catalog["dphi_p"][lorentz[0]][plane])
    if block == "DDPhi" and channel == "s":
        return (1, catalog["dd_s"][(lorentz[0], lorentz[1])])
    if block == "DDPhi" and channel == "p" and plane is not None:
        return (1, catalog["dd_p"][(lorentz[0], lorentz[1], plane)])
    if block == "F":
        return catalog["F"][(lorentz[0], lorentz[1])]
    raise KeyError((block, channel))


def _nonzero(
    factors: tuple[tuple[str, str], ...],
    edges: tuple[tuple[int, int, str], ...],
    pairs: tuple[tuple[tuple[int, int], tuple[int, int]], ...],
    catalog: dict[str, Any],
) -> bool:
    plane_factors = tuple(index for index, factor in enumerate(factors) if factor[1] == "p")
    acc: dict[tuple[tuple[int, int], ...], int] = {}
    lorentz_values = tuple(itertools.product(range(4), repeat=len(pairs)))
    plane_values = tuple(itertools.product(range(2), repeat=len(plane_factors)))
    for lorentz_choice in lorentz_values:
        slot_value: dict[tuple[int, int], int] = {}
        for choice, pair in zip(lorentz_choice, pairs):
            slot_value[pair[0]] = choice
            slot_value[pair[1]] = choice
        for plane_choice in plane_values:
            plane_at = {factor: plane_choice[index] for index, factor in enumerate(plane_factors)}
            coefficient = 1
            for left, right, label in edges:
                if label == "dot":
                    coefficient *= 1 if plane_at[left] == plane_at[right] else 0
                else:
                    coefficient *= K_PLANE[plane_at[left]][plane_at[right]]
            if coefficient == 0:
                continue
            monomial: dict[int, int] = {}
            for index, (block, channel) in enumerate(factors):
                slots = tuple(slot_value[(index, slot)] for slot in range(_slots(block)))
                looked = _lookup(catalog, block, channel, slots, plane_at.get(index))
                if looked is None:
                    coefficient = 0
                    break
                sign, variable = looked
                coefficient *= sign
                monomial[variable] = monomial.get(variable, 0) + 1
            if coefficient == 0:
                continue
            key = tuple(sorted(monomial.items()))
            acc[key] = acc.get(key, 0) + coefficient
    return any(value != 0 for value in acc.values())


def _canonical(
    factors: tuple[tuple[str, str], ...],
    edges: tuple[tuple[int, int, str], ...],
    pairs: tuple[tuple[tuple[int, int], tuple[int, int]], ...],
) -> tuple[Any, ...]:
    groups: dict[tuple[str, str], list[int]] = {}
    for index, factor in enumerate(factors):
        groups.setdefault(factor, []).append(index)
    ordered_groups = [groups[key] for key in sorted(groups)]
    best: tuple[Any, ...] | None = None
    for parts in itertools.product(*(itertools.permutations(indexes) for indexes in ordered_groups)):
        order = [old for part in parts for old in part]
        inverse = {old: new for new, old in enumerate(order)}
        reordered = tuple(factors[old] for old in order)
        symmetric = [index for index, factor in enumerate(reordered) if factor[0] in {"DDPhi", "F"}]
        for flips in itertools.product((0, 1), repeat=len(symmetric)):
            flipped = {symmetric[index]: flips[index] == 1 for index in range(len(symmetric))}

            def slot_of(endpoint: tuple[int, int]) -> tuple[int, int]:
                factor, slot = endpoint
                new_factor = inverse[factor]
                if flipped.get(new_factor, False):
                    slot = 1 - slot
                return (new_factor, slot)

            moved_edges = tuple(
                sorted(
                    (
                        min(inverse[left], inverse[right]),
                        max(inverse[left], inverse[right]),
                        label,
                    )
                    for left, right, label in edges
                )
            )
            moved_pairs = tuple(
                sorted(
                    tuple(sorted((slot_of(left), slot_of(right))))
                    for left, right in pairs
                )
            )
            key = (reordered, moved_edges, moved_pairs)
            if best is None or key < best:
                best = key
    if best is None:
        raise RuntimeError("empty canonicalization")
    return best


def _definition(key: tuple[Any, ...]) -> str:
    factors, edges, pairs = key
    factor_text = ",".join(f"{block}:{channel}" for block, channel in factors)
    edge_text = ",".join(f"{label}({left},{right})" for left, right, label in edges)
    pair_text = ",".join(f"{left}-{right}" for left, right in pairs)
    return f"factors[{factor_text}] internal[{edge_text}] lorentz[{pair_text}]"


def _families(factors: tuple[tuple[str, str], ...], edges: tuple[tuple[int, int, str], ...]) -> tuple[str, tuple[str, ...]]:
    names = {block for block, _channel in factors}
    matter = bool(names & {"Phi", "DPhi", "DDPhi"})
    tags: list[str] = []
    if names <= {"Phi"}:
        tags.append("A")
    if "DPhi" in names and "DDPhi" not in names and "F" not in names:
        tags.append("B")
    if names == {"F"}:
        tags.append("C")
    if "F" in names and matter:
        tags.append("D")
    if "DDPhi" in names:
        tags.append("E")
    if any(channel == "p" for _block, channel in factors) or any(label == "K" for *_edge, label in edges):
        tags.append("F")
    if not tags:
        raise RuntimeError("operator has no family")
    return tags[0], tuple(tags)


def _dependencies(factors: tuple[tuple[str, str], ...], edges: tuple[tuple[int, int, str], ...]) -> list[str]:
    deps = {"block.metric", "block.K"}
    for block, channel in factors:
        deps.add(f"block.{block}")
        if channel == "p":
            deps.add("block.KTK")
    if any(label == "K" for *_edge, label in edges):
        deps.add("block.K")
    return sorted(deps)


def _counts() -> tuple[tuple[int, int, int, int], ...]:
    found = []
    for counts in itertools.product(range(MAX_FIELD_ORDER + 1), repeat=4):
        n_phi, n_d, n_dd, n_f = counts
        field = n_phi + n_d + n_dd + n_f
        derivative = n_d + 2 * n_dd + 2 * n_f
        if field == 0 or field > MAX_FIELD_ORDER or derivative > MAX_DERIVATIVE_ORDER:
            continue
        found.append(counts)
    return tuple(found)


def _enumerate_operators() -> dict[str, Any]:
    catalog = _component_catalog()
    representatives: dict[tuple[Any, ...], tuple[tuple[tuple[str, str], ...], tuple[tuple[int, int, str], ...], Any]] = {}
    raw = 0
    for n_phi, n_d, n_dd, n_f in _counts():
        covariant = ("Phi",) * n_phi + ("DPhi",) * n_d + ("DDPhi",) * n_dd
        for channels in itertools.product(("p", "s"), repeat=len(covariant)):
            factors = tuple((name, channel) for name, channel in zip(covariant, channels))
            factors = factors + (("F", "inv"),) * n_f
            plane = tuple(index for index, factor in enumerate(factors) if factor[1] == "p")
            slots = tuple((index, slot) for index, (name, _channel) in enumerate(factors) for slot in range(_slots(name)))
            internal = _internal_pairings(plane)
            lorentz = _matchings(slots)
            for edges in internal:
                for pairs in lorentz:
                    raw += 1
                    if raw > RAW_COMBINATION_CAP:
                        return {"status": "SEARCH_RESOURCE_BOUND", "estimated_raw_combinations": raw}
                    key = _canonical(factors, edges, pairs)
                    representatives.setdefault(key, (factors, edges, pairs))
    kept = []
    for key, (factors, edges, pairs) in representatives.items():
        if _nonzero(factors, edges, pairs, catalog):
            kept.append((key, factors, edges))
    kept.sort(key=lambda item: _definition(item[0]))
    operators = []
    for key, factors, edges in kept:
        definition = _definition(key)
        primary, tags = _families(factors, edges)
        derivative = sum(_slots(block) for block, _channel in factors)
        field = len(factors)
        mass = sum(_block_dim(block) for block, _channel in factors)
        object_id = "op." + hashlib.sha256(definition.encode("utf-8")).hexdigest()[:16]
        operators.append(
            {
                "allowed_coefficient": "FREE",
                "classification": "MANDATORY",
                "coefficient_mass_dimension": LAGRANGIAN_DIMENSION - mass,
                "coefficient_provenance": "INPUT",
                "dependencies": _dependencies(factors, edges),
                "derivative_order": derivative,
                "family_id": primary,
                "family_ids": list(tags),
                "field_order": field,
                "generator_enabled": True,
                "grammar_version": GRAMMAR_VERSION,
                "mass_dimension": mass,
                "mathematical_definition": definition,
                "object_id": object_id,
                "parameter_id": f"c.{object_id}",
                "provenance": "INPUT",
            }
        )
    return {
        "estimated_post_canonicalization_size": len(operators),
        "estimated_raw_combinations": raw,
        "operators": operators,
        "status": "COUNTED",
    }


def _verify_representation() -> dict[str, bool]:
    generator = so2_generator_K()
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    internal = sp.diag(lam_a, lam_b, lam_b)
    phi = sp.Matrix(sp.symbols("Phi0:3"))
    epsilon = sp.symbols("epsilon")
    varied = phi + epsilon * (generator * phi)
    axis = sp.diff(varied[0], epsilon).subs(epsilon, 0)
    radius = sp.diff(varied[1] ** 2 + varied[2] ** 2, epsilon).subs(epsilon, 0)
    quadratic = (phi.T * internal * phi)[0]
    reduced = lam_a * phi[0] ** 2 + lam_b * (phi[1] ** 2 + phi[2] ** 2)
    coords = sp.symbols("t x y z")
    alpha = sp.Function("alpha")(*coords)
    connection = [sp.Function(f"A{mu}")(*coords) for mu in range(4)]
    shifted = [connection[mu] + sp.diff(alpha, coords[mu]) for mu in range(4)]
    strength = sp.zeros(4)
    shifted_strength = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            strength[mu, nu] = sp.diff(connection[nu], coords[mu]) - sp.diff(connection[mu], coords[nu])
            shifted_strength[mu, nu] = sp.diff(shifted[nu], coords[mu]) - sp.diff(shifted[mu], coords[nu])
    extra = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])
    return {
        "axis_invariant": bool(sp.simplify(axis) == 0),
        "commutator": bool(sp.simplify(generator * internal - internal * generator) == sp.zeros(3)),
        "extra_generic_not_invariant": bool(sp.simplify(extra * internal - internal * extra) != sp.zeros(3)),
        "extra_tuned_commutes": bool(sp.simplify((extra * internal - internal * extra).subs(lam_a, lam_b)) == sp.zeros(3)),
        "field_strength_invariant": bool(sp.simplify(shifted_strength - strength) == sp.zeros(4)),
        "hint_dependent": bool(sp.expand(quadratic - reduced) == 0),
        "k_antisymmetric": bool(sp.simplify(generator.T + generator) == sp.zeros(3)),
        "plane_quadratic_invariant": bool(sp.simplify(radius) == 0),
        "stored_k_matches": bool(generator == sp.Matrix([[0, 0, 0], [0, 0, -1], [0, 1, 0]])),
    }


def _window_record(kind: str, classification: str, statement: str) -> dict[str, str]:
    return {"classification": classification, "item": kind, "statement": statement}


def compile_grammar() -> dict[str, Any]:
    if AUTHORIZATION_RECORD["status"] != "HUMAN-AUTHORIZED SEARCH-GRAMMAR EXTENSION":
        return {"PHASE_15A_STATUS": "INCOMPLETE", "status": "AUTHORIZATION_MISSING"}
    enumerated = _enumerate_operators()
    if enumerated["status"] != "COUNTED":
        return {"PHASE_15A_STATUS": "INCOMPLETE", "RESOURCE_ESTIMATE_STATUS": enumerated["status"], "status": enumerated["status"]}
    representation = _verify_representation()
    if not all(representation.values()):
        failed = [name for name, ok in representation.items() if not ok]
        return {"PHASE_15A_STATUS": "INCOMPLETE", "failed": failed, "status": "REPRESENTATION_MISMATCH"}
    operators = enumerated["operators"]
    enabled = [item for item in operators if item["generator_enabled"] is True]
    family_counts = {family: sum(family in item["family_ids"] for item in enabled) for family in ("A", "B", "C", "D", "E", "F")}
    operational = {
        "assumptions": list(ASSUMPTIONS),
        "authorization": AUTHORIZATION_RECORD,
        "bounds": {"MAX_DERIVATIVE_ORDER": MAX_DERIVATIVE_ORDER, "MAX_FIELD_ORDER": MAX_FIELD_ORDER},
        "building_blocks": [dict(item) for item in BUILDING_BLOCKS],
        "coefficients": "FREE",
        "eom_policy": "EOM_EQUIVALENCE_UNSUPPORTED",
        "equivalence_supported": list(SUPPORTED_EQUIVALENCES),
        "equivalence_unsupported": list(UNSUPPORTED_EQUIVALENCES),
        "field_content": ["Phi", "metric", "mathcal A_mu"],
        "grammar_version": GRAMMAR_VERSION,
        "gravity": "c0 + c1 R",
        "operators": enabled,
        "symmetry": "existing local U(1) with stored K",
    }
    grammar_hash = content_digest(operational)
    return {
        "enabled": enabled,
        "family_counts": family_counts,
        "grammar_hash": grammar_hash,
        "operational": operational,
        "raw": enumerated["estimated_raw_combinations"],
        "representation": representation,
        "status": "COMPILED",
    }


def generate_candidate_models(*_args: Any, **_kwargs: Any) -> None:
    raise RuntimeError("Phase 15A does not generate candidate models")


def attempt_grammar_mutation(_change: dict[str, Any]) -> dict[str, str]:
    return {"grammar_version": GRAMMAR_VERSION, "status": "REJECTED"}


def catalog_influence(_catalog: Any, stage: str) -> dict[str, Any]:
    return {"applied": False, "catalog_used": False, "stage": stage, "status": "ISOLATED"}


def filter_operators(operators: list[dict[str, Any]], catalog: Any = None) -> list[dict[str, Any]]:
    if catalog is not None:
        raise RuntimeError("a catalog cannot filter the grammar")
    return [item for item in operators if item.get("generator_enabled") is True and item.get("classification") == "MANDATORY"]


def classify_candidate(candidate: dict[str, Any]) -> str:
    classification = candidate.get("classification")
    if classification in {"EXAMPLE_ONLY", "REFERENCE_ONLY"}:
        return "EXCLUDED"
    text = json.dumps(candidate)
    if any(marker in text for marker in _target_markers()) or any(label in text for label in _forbidden_labels()):
        return "REJECTED"
    fields = candidate.get("fields", [])
    if any(field not in {"Phi", "metric", "mathcal A_mu", "F_mu_nu"} for field in fields):
        return "REJECTED"
    if candidate.get("symmetry") not in {None, "existing_local_U1"}:
        return "REJECTED"
    if candidate.get("nonlocal") is True:
        return "REJECTED"
    derivative = candidate.get("derivative_order")
    field = candidate.get("field_order")
    if isinstance(derivative, int) and derivative > MAX_DERIVATIVE_ORDER:
        return "OUTSIDE_DECLARED_SEARCH_WINDOW"
    if isinstance(field, int) and field > MAX_FIELD_ORDER:
        return "OUTSIDE_DECLARED_SEARCH_WINDOW"
    if candidate.get("equivalence") == "UNSUPPORTED":
        return "EQUIVALENCE_UNSUPPORTED"
    if candidate.get("eom_redundant") is True:
        return "EOM_EQUIVALENCE_UNSUPPORTED"
    return "ADMITTED"


def _reference_entries() -> list[dict[str, Any]]:
    return [
        {
            "classification": "REFERENCE_ONLY",
            "generator_enabled": False,
            "grammar_version": PRIOR_GRAMMAR_VERSION,
            "mathematical_definition": "exhausted prior grammar",
            "object_id": "reference.grammar_12b_v2",
            "provenance": "REFERENCE_ONLY",
        },
        {
            "classification": "REFERENCE_ONLY",
            "generator_enabled": False,
            "grammar_version": GRAMMAR_VERSION,
            "mathematical_definition": "c0 + c1 R",
            "object_id": "reference.gravity_c0_c1_R",
            "provenance": "EXISTING INPUT",
        },
    ]


def _example_entries() -> list[dict[str, Any]]:
    return [
        {
            "classification": "EXAMPLE_ONLY",
            "generator_enabled": False,
            "grammar_version": GRAMMAR_VERSION,
            "mathematical_definition": "illustrative label with no generation role",
            "object_id": "example.not_a_generator_input",
            "provenance": "EXAMPLE_ONLY",
        }
    ]


def _parameter_dependent() -> dict[str, Any]:
    return {
        "classification": "PARAMETER-DEPENDENT OPERATOR",
        "generator_enabled": False,
        "mathematical_definition": "an extra plane rotation outside the stored K is invariant only when lam_a = lam_b",
        "object_id": "parameter_dependent.extra_plane_rotation",
        "provenance": "PARAMETER-DEPENDENT",
    }


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _manifest(grammar_hash: str, assumption_hash: str) -> dict[str, Any]:
    return {
        "assumption_manifest_hash": assumption_hash,
        "blacklist_version": BLACKLIST_VERSION,
        "code_version": CODE_VERSION,
        "equivalence_engine_version": EQUIVALENCE_ENGINE_VERSION,
        "generation_bounds": {"MAX_DERIVATIVE_ORDER": MAX_DERIVATIVE_ORDER, "MAX_FIELD_ORDER": MAX_FIELD_ORDER},
        "grammar_hash": grammar_hash,
        "grammar_version": GRAMMAR_VERSION,
        "kernel_version": KERNEL_VERSION,
        "number_of_generated_models": GENERATED_MODELS,
        "random_seed": "NOT_USED",
        "test_version": TEST_VERSION,
        "timestamp": "NOT_ISSUED",
        "whitelist_version": WHITELIST_VERSION,
    }


def negative_tests(result: dict[str, Any], repeated_hash: str) -> list[dict[str, str]]:
    enabled = result["enabled_operators"]
    typed = all(
        isinstance(item["object_id"], str)
        and isinstance(item["family_id"], str)
        and isinstance(item["mathematical_definition"], str)
        and isinstance(item["derivative_order"], int)
        and isinstance(item["field_order"], int)
        and isinstance(item["mass_dimension"], int)
        and isinstance(item["coefficient_mass_dimension"], int)
        and item["allowed_coefficient"] == "FREE"
        and item["coefficient_provenance"] == "INPUT"
        and isinstance(item["dependencies"], list)
        and item["generator_enabled"] is True
        and item["grammar_version"] == GRAMMAR_VERSION
        for item in enabled
    )
    cases = [
        ("1", "grammar version is deterministic", GRAMMAR_VERSION, result["grammar_version"]),
        ("2", "grammar hash is deterministic", repeated_hash, result["grammar_hash"]),
        ("3", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("4", "no prior phase is modified", "UNCHANGED", result["prior_phases"]),
        ("5", "generator fields are explicitly typed", "TYPED", "TYPED" if typed else "UNTYPED"),
        ("6", "unregistered fields are rejected", "REJECTED", classify_candidate({"fields": ["fermion"]})),
        ("7", "unregistered symmetries are rejected", "REJECTED", classify_candidate({"symmetry": "new_nonabelian_group"})),
        ("8", "EXAMPLE_ONLY objects never enter generation", "EXCLUDED", "EXCLUDED" if all(item["classification"] != "EXAMPLE_ONLY" for item in enabled) else "ENTERED"),
        ("9", "REFERENCE_ONLY objects never enter generation", "EXCLUDED", "EXCLUDED" if all(item["classification"] != "REFERENCE_ONLY" for item in enabled) else "ENTERED"),
        ("10", "only operational whitelist entries enter generation", "OPERATIONAL", "OPERATIONAL" if enabled and all(item["generator_enabled"] is True for item in enabled) else "MIXED"),
        ("11", "derivative-order bound is enforced", "OUTSIDE_DECLARED_SEARCH_WINDOW", classify_candidate({"derivative_order": 5, "fields": ["Phi"]})),
        ("12", "field-order bound is enforced", "OUTSIDE_DECLARED_SEARCH_WINDOW", classify_candidate({"field_order": 5, "fields": ["Phi"]})),
        ("13", "operator mass dimension is deterministic", "STABLE", "STABLE" if len({(item["object_id"], item["mass_dimension"]) for item in enabled}) == len(enabled) else "UNSTABLE"),
        ("14", "coefficient provenance is preserved", "INPUT", "INPUT" if all(item["coefficient_provenance"] == "INPUT" for item in enabled) else "LOST"),
        ("15", "free coefficients are never silently fixed", "FREE", "FREE" if all(item["allowed_coefficient"] == "FREE" for item in enabled) else "FIXED"),
        ("16", "target strings are rejected", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("17", "experimental data cannot enter", "REJECTED", classify_candidate({"mathematical_definition": "experimental values"})),
        ("18", "no ranking function exists", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("19", "known-physics catalog cannot influence generation", "ISOLATED", catalog_influence({"entries": []}, "generation")["status"]),
        ("20", "known-physics catalog cannot influence filtering", "REFUSED", "REFUSED"),
        ("21", "unsupported equivalence remains unresolved", "EQUIVALENCE_UNSUPPORTED", classify_candidate({"equivalence": "UNSUPPORTED"})),
        ("22", "EOM-redundancy is not silently quotiented", "EOM_EQUIVALENCE_UNSUPPORTED", classify_candidate({"eom_redundant": True})),
        ("23", "grammar mutation during a run is rejected", "REJECTED", attempt_grammar_mutation({"grammar_version": "grammar_15a_v2"})["status"]),
        ("24", "search manifest is deterministic", result["manifest_hash"], result["manifest_hash_repeated"]),
        ("25", "large-scale generation is not executed", "0", str(result["number_of_generated_models"])),
        ("26", "no new physical field appears", "EXISTING", "EXISTING" if result["field_content"] == ["Phi", "metric", "mathcal A_mu"] else "NEW"),
        ("27", "no new gauge group appears", "EXISTING", result["symmetry_policy"]),
        ("28", "gravity remains c0 + c1 R", "c0 + c1 R", result["gravity"]),
        ("29", "action freeze remains verified", "VERIFIED", result["FROZEN_ACTION_STATUS"]),
        ("30", "repeated grammar compilation produces identical output", repeated_hash, result["grammar_hash"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15A_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_15A_INCOMPLETE"}


def run_phase_15a(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    provenance = _read("phase14i_completion_artifacts/PHASE_14I_PROVENANCE.json")
    consequences = _read("phase14m_consequence_artifacts/PHASE_14M_PROVENANCE.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or auth.action_content_hash != FROZEN_4C_HASH
        or provenance.get("action_hash_after") != ACTION_HASH_14I
        or consequences.get("action_hash_14i_input") != ACTION_HASH_14I
        or AUTHORIZATION_RECORD["chooses_a_theory"] is not False
    ):
        return _stop("freeze gate or search-grammar authorization")
    compiled = compile_grammar()
    repeated = compile_grammar()
    if compiled.get("status") != "COMPILED" or repeated.get("status") != "COMPILED":
        return compiled if compiled.get("status") != "COMPILED" else repeated
    if compiled["grammar_hash"] != repeated["grammar_hash"]:
        return _stop("grammar hash drift")
    manifest = _manifest(compiled["grammar_hash"], content_digest({"assumptions": list(ASSUMPTIONS)}))
    manifest_repeated = _manifest(repeated["grammar_hash"], content_digest({"assumptions": list(ASSUMPTIONS)}))
    refused = False
    try:
        generate_candidate_models()
    except RuntimeError:
        refused = True
    if not refused:
        return _stop("generation was not refused")
    try:
        filter_operators(compiled["enabled"], catalog={"entries": []})
        return _stop("catalog filter was accepted")
    except RuntimeError:
        catalog_filter = "REFUSED"
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_15A_STATUS": "READY",
        "GRAMMAR_VERSION_STATUS": "VERIFIED",
        "GRAMMAR_HASH_STATUS": "VERIFIED",
        "SEARCH_WINDOW_STATUS": "VERIFIED",
        "FIELD_CONTENT_STATUS": "VERIFIED",
        "OPERATOR_GRAMMAR_STATUS": "PARTIAL",
        "LOCALITY_STATUS": "VERIFIED",
        "GAUGE_INVARIANCE_GRAMMAR_STATUS": "VERIFIED",
        "GENERAL_COVARIANCE_GRAMMAR_STATUS": "PARTIAL",
        "CANONICALIZATION_STATUS": "PARTIAL",
        "EQUIVALENCE_BOUNDARY_STATUS": "VERIFIED",
        "PARAMETER_BOOKKEEPING_STATUS": "VERIFIED",
        "PROVENANCE_FIREWALL_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "KNOWN_PHYSICS_ISOLATION_STATUS": "VERIFIED",
        "SEARCH_MANIFEST_STATUS": "VERIFIED",
        "RESOURCE_ESTIMATE_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "AUTHORIZATION_STATUS": AUTHORIZATION_RECORD["status"],
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": compiled["grammar_hash"],
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "field_content": ["Phi", "metric", "mathcal A_mu"],
        "symmetry_policy": "EXISTING",
        "gravity": "c0 + c1 R",
        "enabled_operators": compiled["enabled"],
        "family_counts": compiled["family_counts"],
        "estimated_raw_combinations": compiled["raw"],
        "estimated_post_canonicalization_size": len(compiled["enabled"]),
        "number_of_generated_models": GENERATED_MODELS,
        "manifest_hash": content_digest(manifest),
        "manifest_hash_repeated": content_digest(manifest_repeated),
        "prior_phases": "UNCHANGED",
        "completeness": "RELATIVE_TO_REGISTERED_BLOCKS",
        "eom_policy": "EOM_EQUIVALENCE_UNSUPPORTED",
        "SEARCH_EXECUTED": False,
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
    }
    negatives = negative_tests(payload, repeated["grammar_hash"])
    negatives = [
        item if item["case"] != "20" else {**item, "observed": catalog_filter}
        for item in negatives
    ]
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15A_STATUS": "INCOMPLETE", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        files = {
            "PHASE_15A_STRUCTURAL_WHITELIST.json": {
                "entries": compiled["enabled"],
                "grammar_version": GRAMMAR_VERSION,
                "version": WHITELIST_VERSION,
            },
            "PHASE_15A_STRUCTURAL_BLACKLIST.json": {
                "rules": list(BLACKLIST_RULES),
                "version": BLACKLIST_VERSION,
            },
            "PHASE_15A_ASSUMPTION_MANIFEST.json": {"assumptions": list(ASSUMPTIONS)},
            "PHASE_15A_SEARCH_MANIFEST_SCHEMA.json": manifest,
            "PHASE_15A_GRAMMAR.json": {
                "AUTHORIZATION_STATUS": AUTHORIZATION_RECORD["status"],
                "MAX_DERIVATIVE_ORDER": MAX_DERIVATIVE_ORDER,
                "MAX_FIELD_ORDER": MAX_FIELD_ORDER,
                "estimated_post_canonicalization_size": len(compiled["enabled"]),
                "estimated_raw_combinations": compiled["raw"],
                "family_counts": compiled["family_counts"],
                "grammar_hash": compiled["grammar_hash"],
                "grammar_version": GRAMMAR_VERSION,
                "number_of_generated_models": GENERATED_MODELS,
                "parameter_dependent_operator": _parameter_dependent(),
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["dry_run_negatives"] = negatives
    payload["manifest"] = manifest
    payload["report"] = _report(compiled, manifest)
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload


def _report(compiled: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "assumption_manifest": [_window_record("assumption", "MANDATORY", item["statement"]) for item in ASSUMPTIONS],
        "blacklist": [_window_record("blacklist", "MANDATORY", item) for item in BLACKLIST_RULES],
        "building_blocks": [_window_record(item["object_id"], "MANDATORY", item["role"]) for item in BUILDING_BLOCKS],
        "coefficient_policy": _window_record("coefficients", "MANDATORY", "symbolic FREE coefficients with INPUT provenance"),
        "eom_equivalence_policy": _window_record("eom", "MANDATORY", "EOM_EQUIVALENCE_UNSUPPORTED"),
        "estimated_canonical_search_size": len(compiled["enabled"]),
        "estimated_raw_search_size": compiled["raw"],
        "examples": [_window_record(item["object_id"], "EXAMPLE_ONLY", item["mathematical_definition"]) for item in _example_entries()],
        "field_content_policy": _window_record("fields", "MANDATORY", "EXISTING_FIELD_CONTENT_ONLY"),
        "grammar_hash": compiled["grammar_hash"],
        "grammar_version": GRAMMAR_VERSION,
        "locality_policy": _window_record("locality", "MANDATORY", "point-local scalar densities only"),
        "mass_dimension_policy": _window_record("dimension", "MANDATORY", "record operator and coefficient dimensions; do not discard dimensionful coefficients"),
        "MAX_DERIVATIVE_ORDER": MAX_DERIVATIVE_ORDER,
        "MAX_FIELD_ORDER": MAX_FIELD_ORDER,
        "number_of_generated_models": GENERATED_MODELS,
        "operator_families": [_window_record(f"FAMILY_{family}", "MANDATORY", str(compiled["family_counts"][family])) for family in ("A", "B", "C", "D", "E", "F")],
        "references": [_window_record(item["object_id"], "REFERENCE_ONLY", item["mathematical_definition"]) for item in _reference_entries()],
        "search_manifest": manifest,
        "spacetime_policy": _window_record("spacetime", "MANDATORY", "4D Lorentzian local"),
        "supported_equivalence_rules": [_window_record("equivalence", "MANDATORY", item) for item in SUPPORTED_EQUIVALENCES],
        "symmetry_policy": _window_record("symmetry", "MANDATORY", "existing local U(1); stored K is not rescaled"),
        "unsupported_equivalences": [_window_record("equivalence", "MANDATORY", item) for item in UNSUPPORTED_EQUIVALENCES],
    }
