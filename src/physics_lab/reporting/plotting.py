"""Optional spectrum plot.  No GUI is launched unless the caller displays it."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from physics_lab.core.result import ModelResult


def plot_spectrum(result: ModelResult, path: str | Path | None = None):
    """Bar plot of internal eigenvalues."""
    values = result.spectrum.eigenvalues()
    labels = result.spectrum.labels()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(np.arange(len(values)), values, color="steelblue")
    ax.set_xticks(np.arange(len(values)), labels, rotation=45, ha="right")
    ax.set_ylabel("lambda")
    ax.set_title(f"Internal spectrum: {result.name}")
    ax.axhline(0.0, color="black", linewidth=0.6)
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, dpi=120)
    return fig
