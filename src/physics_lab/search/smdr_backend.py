"""Bridge to the official SMDR v1.3 executable.

The bridge is deliberately an external-backend adapter.  The official SMDR
repository remains the authority for two-loop self-energies, tadpoles, heavy
particle decoupling and pole observables.  The laboratory supplies only a
target-blind MSbar state and records the raw/parsed result; it never asks SMDR
to fit or select a trajectory.
"""

from __future__ import annotations

import json
import hashlib
import math
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


SMDR_BRIDGE_VERSION = "smdr-bridge-v1"
# Backward-compatible public name for callers that describe the adapter as a
# backend rather than a bridge.
SMDR_BACKEND_VERSION = SMDR_BRIDGE_VERSION
ELECTROWEAK_VEV_GEV = 246.21965


class SMDRBackendError(RuntimeError):
    """Raised when the official SMDR backend cannot be executed."""


def _positive(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise SMDRBackendError(f"{name} must be finite and positive")
    return result


def smdr_root_from_environment() -> Path | None:
    value = os.environ.get("SMDR_ROOT")
    return Path(value).expanduser() if value else None


def _calc_all_path(root: Path) -> Path:
    executable = root / "calc_all"
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise SMDRBackendError(f"SMDR executable not found or not executable: {executable}")
    return executable


def target_blind_input_text(
    matter_state: Sequence[float],
    *,
    scale_gev: float = ELECTROWEAK_VEV_GEV,
    vev_gev: float = ELECTROWEAK_VEV_GEV,
    delta_alpha_hadronic: float = 0.0,
) -> str:
    """Create an SMDR input with no experimental pole-mass targets.

    The W11 state stores GUT-normalized ``g1`` and ``lambda_4``.  SMDR uses
    ``gp = sqrt(3/5) g1`` and the conventional ``lambda = 2 lambda_4``.
    Lower-family Yukawas and the non-perturbative hadronic alpha contribution
    are set to zero as explicit neutral controls, not imported from data.
    """

    if len(matter_state) != 6:
        raise SMDRBackendError("matter_state must contain g1,g2,g3,yt,yb,lambda_4")
    g1, g2, g3, yt, yb, lambda_4 = (float(value) for value in matter_state)
    if not all(math.isfinite(value) for value in (g1, g2, g3, yt, yb, lambda_4)):
        raise SMDRBackendError("matter_state must be finite")
    scale = _positive(scale_gev, "scale_gev")
    vev = _positive(vev_gev, "vev_gev")
    if not math.isfinite(delta_alpha_hadronic) or delta_alpha_hadronic < 0.0:
        raise SMDRBackendError("delta_alpha_hadronic must be finite and nonnegative")
    values = {
        "SMDR_Q_in": scale,
        "SMDR_g3_in": abs(g3),
        "SMDR_g_in": abs(g2),
        "SMDR_gp_in": abs(math.sqrt(3.0 / 5.0) * g1),
        "SMDR_v_in": vev,
        "SMDR_lambda_in": 2.0 * lambda_4,
        "SMDR_yt_in": yt,
        "SMDR_yb_in": yb,
        "SMDR_yc_in": 0.0,
        "SMDR_ys_in": 0.0,
        "SMDR_yd_in": 0.0,
        "SMDR_yu_in": 0.0,
        "SMDR_ytau_in": 0.0,
        "SMDR_ymu_in": 0.0,
        "SMDR_ye_in": 0.0,
        "SMDR_Delta_alpha_had_5_MZ_in": delta_alpha_hadronic,
        "SMDR_m2_in": -2.0 * lambda_4 * vev**2,
        "SMDR_Lambda_in": 0.0,
    }
    return "# physics-lab target-blind SMDR input\n" + "\n".join(
        f"{key} = {value:.17g};" for key, value in values.items()
    ) + "\n"


def parse_calc_all_output(output: str) -> dict[str, Any]:
    """Parse the stable headline observables printed by ``calc_all``."""

    def match(pattern: str, name: str) -> float | None:
        found = re.findall(pattern, output, flags=re.MULTILINE)
        if not found:
            return None
        try:
            return float(found[-1])
        except ValueError as exc:
            raise SMDRBackendError(f"could not parse {name}") from exc

    return {
        "version": (re.search(r"SMDR .*? v([0-9.]+)", output) or [None, None])[1],
        "top_pole_gev": match(r"^Mt = ([0-9.eE+-]+);", "top_pole_gev"),
        "higgs_pole_gev": match(r"^Mh = ([0-9.eE+-]+);", "higgs_pole_gev"),
        "z_pole_gev": match(r"^MZ = ([0-9.eE+-]+);", "z_pole_gev"),
        "w_pole_gev": match(r"^MW = ([0-9.eE+-]+);", "w_pole_gev"),
        "alpha_sommerfeld_inverse": match(r"alpha = 1/([0-9.eE+-]+);", "alpha_sommerfeld_inverse"),
        "gf_gev_minus_two": match(r"GFermi = ([0-9.eE+-]+) 10\^-5", "gf_gev_minus_two"),
    }


def run_smdr_calc_all(
    root: str | Path,
    *,
    input_text: str | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Run official ``calc_all`` in reference or target-blind mode."""

    smdr_root = Path(root).expanduser().resolve()
    executable = _calc_all_path(smdr_root)
    command = [str(executable)]
    temporary_input: Path | None = None
    if input_text is not None:
        handle = tempfile.NamedTemporaryFile("w", suffix=".dat", prefix="physics_lab_smdr_", delete=False)
        temporary_input = Path(handle.name)
        handle.write(input_text)
        handle.close()
        command.extend(["-i", str(temporary_input)])
    try:
        completed = subprocess.run(
            command,
            cwd=smdr_root,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise SMDRBackendError(f"SMDR timed out after {timeout_seconds}s") from exc
    finally:
        if temporary_input is not None:
            temporary_input.unlink(missing_ok=True)
    if completed.returncode != 0:
        raise SMDRBackendError(
            f"SMDR calc_all failed with exit code {completed.returncode}: {completed.stderr[-1000:]}"
        )
    parsed = parse_calc_all_output(completed.stdout)
    input_sha256 = None if input_text is None else hashlib.sha256(input_text.encode("utf-8")).hexdigest()
    return {
        "status": "COMPLETE",
        "command": command if input_text is None else [str(executable), "-i", "<target-blind-input.dat>"],
        "input_sha256": input_sha256,
        "parsed": parsed,
        "stdout_tail": completed.stdout[-4000:],
        "stderr": completed.stderr,
        "target_blind_input": input_text is not None,
    }


def write_smdr_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "ELECTROWEAK_VEV_GEV",
    "SMDR_BACKEND_VERSION",
    "SMDR_BRIDGE_VERSION",
    "SMDRBackendError",
    "parse_calc_all_output",
    "run_smdr_calc_all",
    "smdr_root_from_environment",
    "target_blind_input_text",
    "write_smdr_report",
]
