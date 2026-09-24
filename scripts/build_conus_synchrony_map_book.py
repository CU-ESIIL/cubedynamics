#!/usr/bin/env python3
"""Build a three-page, high-resolution CONUS synchrony map book."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import Normalize, TwoSlopeNorm
import numpy as np
import xarray as xr


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts" / "nonstacked-conus-baseline" / "conus_nonstacked_synchrony.nc"
OUTPUT = ROOT / "output" / "pdf" / "conus_synchrony_maps_high_resolution.pdf"

# A 24 x 13.5 inch page matches a 16:9 presentation canvas and gives the
# 1,399-column source grid ample room at 400 dpi without changing its values.
PAGE_SIZE = (24.0, 13.5)
MAP_DPI = 400
NAVY = "#123F70"
INK = "#17212B"
MUTED = "#586775"
GRID = "#9AA7B2"


def _add_page(
    pdf: PdfPages,
    *,
    x: np.ndarray,
    y: np.ndarray,
    mask: np.ndarray,
    values: np.ndarray,
    title: str,
    subtitle: str,
    cmap: str,
    norm: Normalize,
    colorbar_label: str,
    footer: str,
    extend: str,
) -> None:
    fig = plt.figure(figsize=PAGE_SIZE, facecolor="white")
    ax = fig.add_axes((0.055, 0.185, 0.89, 0.675))

    masked = np.ma.masked_where(~mask | ~np.isfinite(values), values)
    image = ax.pcolormesh(
        x,
        y,
        masked,
        shading="nearest",
        cmap=cmap,
        norm=norm,
        rasterized=True,
    )
    ax.contour(x, y, mask.astype(float), levels=(0.5,), colors=INK, linewidths=0.75)
    ax.set_aspect(1 / np.cos(np.deg2rad(37.5)))
    ax.set_xlim(float(x.min()), float(x.max()))
    ax.set_ylim(float(y.min()), float(y.max()))
    ax.set_xlabel("Longitude", fontsize=15, labelpad=10)
    ax.set_ylabel("Latitude", fontsize=15, labelpad=10)
    ax.tick_params(axis="both", labelsize=12, length=5, width=0.8)
    ax.grid(color=GRID, linewidth=0.45, alpha=0.34)
    for spine in ax.spines.values():
        spine.set_color(INK)
        spine.set_linewidth(0.8)

    colorbar_ax = fig.add_axes((0.145, 0.105, 0.71, 0.027))
    colorbar = fig.colorbar(image, cax=colorbar_ax, orientation="horizontal", extend=extend)
    colorbar.set_label(colorbar_label, fontsize=14, labelpad=8, color=INK)
    colorbar.ax.tick_params(labelsize=11)

    fig.text(0.055, 0.946, title, ha="left", va="top", fontsize=27, weight="bold", color=NAVY)
    fig.text(0.055, 0.898, subtitle, ha="left", va="top", fontsize=15, color=INK)
    fig.text(0.055, 0.037, footer, ha="left", va="bottom", fontsize=10.5, color=MUTED)
    fig.text(
        0.945,
        0.037,
        "CubeDynamics | corrected semantic edition",
        ha="right",
        va="bottom",
        fontsize=10.5,
        color=MUTED,
    )

    # The dpi controls only the rasterized map layer; text, axes and outlines
    # remain vector elements in the PDF.
    pdf.savefig(fig, dpi=MAP_DPI, facecolor="white")
    plt.close(fig)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with xr.open_dataset(SOURCE, engine="h5netcdf") as dataset:
        mask = np.asarray(dataset.output_mask.values, dtype=bool)
        x = np.asarray(dataset.x.values, dtype=float)
        y = np.asarray(dataset.y.values, dtype=float)
        cold = np.asarray(
            dataset.cold_median.sel(radius_km=100).isel(time_window_end=0).values,
            dtype=float,
        )
        warm = np.asarray(
            dataset.warm_median.sel(radius_km=100).isel(time_window_end=0).values,
            dtype=float,
        )
        delta = np.asarray(
            dataset.delta_pair_median.sel(radius_km=100).isel(time_window_end=0).values,
            dtype=float,
        )

    pooled = np.concatenate((cold[mask], warm[mask]))
    synchrony_low, synchrony_high = np.nanpercentile(pooled, (1, 99))
    delta_limit = float(np.nanpercentile(np.abs(delta[mask]), 99))
    synchrony_norm = Normalize(vmin=float(synchrony_low), vmax=float(synchrony_high))
    delta_norm = TwoSlopeNorm(vmin=-delta_limit, vcenter=0.0, vmax=delta_limit)
    common_footer = (
        "Observed PRISM daily data, 2023-11-01 through 2024-01-30 | "
        "100 km observation radius | self-pairs excluded | 481,630 complete focal cells | "
        "native result grid: 1,399 x 621"
    )

    metadata = {
        "Title": "High-resolution CONUS synchrony maps",
        "Author": "CubeDynamics project",
        "Subject": "Cold-tail, warm-tail, and cold-minus-warm synchrony over CONUS",
        "Keywords": "CONUS, PRISM, synchrony, cold, warm, Delta",
    }
    with PdfPages(OUTPUT, metadata=metadata) as pdf:
        _add_page(
            pdf,
            x=x,
            y=y,
            mask=mask,
            values=cold,
            title="Cold synchrony across CONUS",
            subtitle=(
                "Median local pair synchrony for joint lower-tail TMIN days: "
                "both pixels are at or below their own TMIN median"
            ),
            cmap="viridis",
            norm=synchrony_norm,
            colorbar_label=(
                f"Median lower-tail TMIN Spearman synchrony "
                f"(shared 1st-99th percentile display range: {synchrony_low:.3f} to {synchrony_high:.3f})"
            ),
            footer=common_footer,
            extend="both",
        )
        _add_page(
            pdf,
            x=x,
            y=y,
            mask=mask,
            values=warm,
            title="Warm synchrony across CONUS",
            subtitle=(
                "Median local pair synchrony for joint upper-tail TMAX days: "
                "both pixels are strictly above their own TMAX median"
            ),
            cmap="viridis",
            norm=synchrony_norm,
            colorbar_label=(
                f"Median upper-tail TMAX Spearman synchrony "
                f"(shared 1st-99th percentile display range: {synchrony_low:.3f} to {synchrony_high:.3f})"
            ),
            footer=common_footer,
            extend="both",
        )
        _add_page(
            pdf,
            x=x,
            y=y,
            mask=mask,
            values=delta,
            title="Cold-minus-warm synchrony across CONUS",
            subtitle=(
                "Primary pixel value = median over neighboring pairs of Delta = S cold - S warm; "
                "red is negative/warm stronger, blue is positive/cold stronger"
            ),
            cmap="RdBu",
            norm=delta_norm,
            colorbar_label=(
                f"Median pairwise Delta (symmetric 99th-percentile absolute display limit: "
                f"-{delta_limit:.3f} to +{delta_limit:.3f})"
            ),
            footer=common_footer,
            extend="both",
        )

    print(OUTPUT)


if __name__ == "__main__":
    main()
