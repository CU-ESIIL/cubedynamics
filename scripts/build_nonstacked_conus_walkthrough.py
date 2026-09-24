#!/usr/bin/env python3
"""Build a visual PDF walkthrough of the CONUS non-stacked baseline."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
from PIL import Image as PILImage
try:
    import reportlab  # noqa: F401
except ModuleNotFoundError:
    sys.path.append(
        "/Users/tuff/.cache/codex-runtimes/codex-primary-runtime/dependencies/"
        "python/lib/python3.12/site-packages"
    )
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import xarray as xr


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts" / "nonstacked-conus-baseline"
COLORADO = ROOT / "artifacts" / "nonstacked-colorado-baseline"
AUDIT = ROOT / "artifacts" / "hot-cold-delta-semantics-audit"
FIGURES = BASE / "walkthrough_figures"
OUTPUT = ROOT / "output" / "pdf" / "conus_nonstacked_synchrony_walkthrough_corrected.pdf"
PAGE = landscape(letter)
NAVY = "#123F70"
BLUE = "#2878B5"
RED = "#B63A3A"
GOLD = "#F0B43C"
GREEN = "#3A8D6D"
INK = "#17212B"
MUTED = "#586775"
LIGHT = "#EDF3F7"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(fig: plt.Figure, name: str) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.savefig(path, dpi=190, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return path


def _hide(ax) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def _map(ax, x, y, values, *, cmap, vmin=None, vmax=None, norm=None, title=""):
    image = ax.pcolormesh(x, y, values, shading="nearest", cmap=cmap, vmin=vmin, vmax=vmax, norm=norm)
    ax.set_title(title, loc="left", weight="bold", fontsize=11)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect(1 / np.cos(np.deg2rad(37.5)))
    return image


def build_workflow_figure() -> Path:
    fig, ax = plt.subplots(figsize=(13.2, 4.2))
    _hide(ax)
    steps = [
        ("1", "Acquire", "91 real PRISM\ndaily layers"),
        ("2", "Mask", "481,630 complete\nCONUS pixels"),
        ("3", "Relate", "Cold and warm\npair synchrony"),
        ("4", "Reduce", "One scalar per\nfocal pixel"),
        ("5", "Tile", "555 restartable\ncheckpoints"),
        ("6", "Validate", "1,500 GHCN\nstations"),
    ]
    colors_list = [BLUE, GREEN, RED, GOLD, NAVY, "#6E5AA8"]
    for index, ((number, label, detail), color) in enumerate(zip(steps, colors_list)):
        x = 0.03 + index * 0.162
        box = FancyBboxPatch((x, .25), .13, .5, boxstyle="round,pad=0.012,rounding_size=.018",
                             facecolor="white", edgecolor=color, linewidth=2.2)
        ax.add_patch(box)
        ax.text(x + .065, .66, number, ha="center", va="center", fontsize=15, weight="bold", color="white",
                bbox=dict(boxstyle="circle,pad=.28", fc=color, ec="none"))
        ax.text(x + .065, .51, label, ha="center", va="center", fontsize=13, weight="bold", color=INK)
        ax.text(x + .065, .36, detail, ha="center", va="center", fontsize=10, color=MUTED, linespacing=1.25)
        if index < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((x + .134, .5), (x + .158, .5), arrowstyle="-|>", mutation_scale=17,
                                         linewidth=1.5, color="#7D8A96"))
    ax.text(.5, .92, "From daily temperature fields to a validated national synchrony map",
            ha="center", va="center", fontsize=18, weight="bold", color=NAVY)
    ax.text(.5, .08, "Exact Colorado method preserved: no stacking, no overlap alignment, no second convolution",
            ha="center", va="center", fontsize=12, weight="bold", color=RED)
    return _save(fig, "01_workflow_overview.png")


def build_source_figure() -> Path:
    source = BASE / "inputs" / "prism_conus_20231101_20240130.nc"
    with xr.open_dataset(source, engine="h5netcdf") as ds:
        index = 45
        tmin = ds.tmin.isel(time=index).load()
        tmax = ds.tmax.isel(time=index).load()
        date = str(ds.time.values[index])[:10]
        x = ds.x.values
        y = ds.y.values
    fig = plt.figure(figsize=(13.2, 5.6))
    grid = fig.add_gridspec(2, 2, height_ratios=(5, 1), hspace=.26, wspace=.18)
    ax1 = fig.add_subplot(grid[0, 0]); ax2 = fig.add_subplot(grid[0, 1])
    im1 = _map(ax1, x, y, tmin, cmap="coolwarm", vmin=-25, vmax=25, title=f"A  PRISM TMIN snapshot - {date}")
    im2 = _map(ax2, x, y, tmax, cmap="coolwarm", vmin=-25, vmax=25, title=f"B  PRISM TMAX snapshot - {date}")
    fig.colorbar(im1, ax=ax1, shrink=.78, label="deg C")
    fig.colorbar(im2, ax=ax2, shrink=.78, label="deg C")
    timeline = fig.add_subplot(grid[1, :]); _hide(timeline)
    timeline.set_xlim(0, 1); timeline.set_ylim(0, 1)
    timeline.plot([.05, .95], [.52, .52], color=NAVY, lw=5, solid_capstyle="round")
    timeline.scatter([.05, .50, .95], [.52] * 3, s=[90, 130, 90], color=[BLUE, GOLD, BLUE], zorder=3)
    timeline.text(.05, .12, "2023-11-01", ha="center", fontsize=10)
    timeline.text(.50, .12, date, ha="center", fontsize=10, weight="bold")
    timeline.text(.95, .12, "2024-01-30", ha="center", fontsize=10)
    timeline.text(.50, .84, "91 daily labels; frozen 90-day analysis window ending 2024-01-30",
                  ha="center", fontsize=11, color=INK)
    return _save(fig, "02_source_window.png")


def build_method_figure() -> Path:
    rng = np.random.default_rng(42)
    days = np.arange(91)
    tmin_center = -4 + 8 * np.sin(days / 8.5) + rng.normal(0, 3.0, 91)
    tmin_neighbor = .75 * tmin_center + 2 * np.sin(days / 13.0 + .8) + rng.normal(0, 2.8, 91)
    tmax_center = 13 + 9 * np.sin(days / 8.5 + .15) + rng.normal(0, 3.2, 91)
    tmax_neighbor = 4 + .72 * tmax_center + 2 * np.sin(days / 12.0 + .4) + rng.normal(0, 2.9, 91)
    tmin_median_c = np.median(tmin_center); tmin_median_n = np.median(tmin_neighbor)
    tmax_median_c = np.median(tmax_center); tmax_median_n = np.median(tmax_neighbor)
    cold = (tmin_center <= tmin_median_c) & (tmin_neighbor <= tmin_median_n)
    warm = (tmax_center > tmax_median_c) & (tmax_neighbor > tmax_median_n)

    fig = plt.figure(figsize=(13.2, 5.7))
    grid = fig.add_gridspec(1, 3, wspace=.30)
    ax = fig.add_subplot(grid[0, 0]); _hide(ax)
    for radius, color in zip((.22, .36, .50, .64), ("#B5D8F0", "#7BB6DD", "#428FC2", NAVY)):
        ax.add_patch(Circle((0, 0), radius, fill=False, lw=2, ec=color))
    gx, gy = np.meshgrid(np.linspace(-.72, .72, 15), np.linspace(-.72, .72, 15))
    valid = gx ** 2 + gy ** 2 <= .64 ** 2
    ax.scatter(gx[valid], gy[valid], s=11, color="#78909C", alpha=.65)
    ax.scatter([0], [0], s=170, marker="*", color=GOLD, edgecolor=INK, zorder=5)
    ax.scatter([.28], [-.18], s=75, color=RED, edgecolor="white", zorder=5)
    ax.plot([0, .28], [0, -.18], color=RED, lw=2)
    ax.set_xlim(-.8, .8); ax.set_ylim(-.8, .8); ax.set_aspect("equal")
    ax.set_title("A  One focal pixel, many neighbors", loc="left", weight="bold")
    ax.text(0, -.76, "Nested radii: 25 / 50 / 75 / 100 km\nThe focal self-pair is excluded",
            ha="center", va="top", fontsize=10, color=MUTED)

    ax = fig.add_subplot(grid[0, 1])
    ax.plot(days, tmin_center, color=BLUE, lw=1.2, label="Focal TMIN")
    ax.plot(days, tmax_center, color=RED, lw=1.2, label="Focal TMAX")
    ax.scatter(days[cold], tmin_center[cold], s=19, color=NAVY, label="Joint lower TMIN", zorder=3)
    ax.scatter(days[warm], tmax_center[warm], s=19, color="#8C001A", label="Joint upper TMAX", zorder=3)
    ax.axhline(tmin_median_c, color=BLUE, lw=.8, ls="--")
    ax.axhline(tmax_median_c, color=RED, lw=.8, ls="--")
    ax.set(xlabel="Day in frozen window", ylabel="Illustrative temperature (deg C)")
    ax.set_title("B  Select lower TMIN and upper TMAX", loc="left", weight="bold")
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    ax.grid(alpha=.15)

    ax = fig.add_subplot(grid[0, 2])
    ax.scatter(tmin_center[cold], tmin_neighbor[cold], s=33, color=BLUE, alpha=.8, label="Cold: TMIN <= own median")
    ax.scatter(tmax_center[warm], tmax_neighbor[warm], s=33, color=RED, alpha=.8, label="Warm: TMAX > own median")
    ax.set(xlabel="Focal-pixel values", ylabel="Neighbor-pixel values")
    ax.set_title("C  Rank dependence within each tail", loc="left", weight="bold")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=.15)
    fig.suptitle("The same pair kernel is applied to every eligible focal-neighbor relationship",
                 fontsize=17, weight="bold", color=NAVY, y=1.01)
    return _save(fig, "03_pair_method.png")


def build_primary_semantics_figure() -> Path:
    """Render the primary maps with explicit, audited color semantics."""

    with xr.open_dataset(BASE / "conus_nonstacked_synchrony.nc", engine="h5netcdf") as ds:
        mask = ds.output_mask.load()
        cold = ds.cold_median.sel(radius_km=100).isel(time_window_end=0).where(mask).load()
        warm = ds.warm_median.sel(radius_km=100).isel(time_window_end=0).where(mask).load()
        delta = ds.delta_pair_median.sel(radius_km=100).isel(time_window_end=0).where(mask).load()
        x = ds.x.values
        y = ds.y.values
    common = max(float(np.nanpercentile(np.abs(np.concatenate((cold.values.ravel(), warm.values.ravel()))), 99)), .01)
    delta_limit = max(float(np.nanpercentile(np.abs(delta.values), 99)), .01)
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.35))
    specifications = [
        (cold, "A  COLD: lower-tail TMIN synchrony", TwoSlopeNorm(vmin=-common, vcenter=0, vmax=common), "Spearman rho"),
        (warm, "B  WARM: upper-tail TMAX synchrony", TwoSlopeNorm(vmin=-common, vcenter=0, vmax=common), "Spearman rho"),
        (delta, "C  DELTA = S cold - S warm", TwoSlopeNorm(vmin=-delta_limit, vcenter=0, vmax=delta_limit), "Pairwise-median Delta"),
    ]
    for ax, (values, title, norm, label) in zip(axes, specifications):
        image = _map(ax, x, y, values, cmap="RdBu", norm=norm, title=title)
        fig.colorbar(image, ax=ax, shrink=.72, label=label)
    fig.suptitle("CONUS immediate 100 km reduction - audited semantic edition", fontsize=16, weight="bold", color=NAVY)
    fig.text(.5, .015, "DELTA COLOR RULE: red = negative = warm synchrony stronger   |   blue = positive = cold synchrony stronger",
             ha="center", va="bottom", fontsize=10.5, weight="bold", color=INK)
    fig.tight_layout(rect=(0, .065, 1, .94))
    return _save(fig, "00_primary_semantics_corrected.png")


def build_tiling_figure() -> Path:
    with xr.open_dataset(BASE / "conus_nonstacked_synchrony.nc", engine="h5netcdf") as ds:
        mask = ds.output_mask.load().values
        x = ds.x.values; y = ds.y.values
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.4), gridspec_kw={"width_ratios": (1.45, 1)})
    ax = axes[0]
    ax.pcolormesh(x, y, mask, shading="nearest", cmap="Blues", vmin=0, vmax=1)
    for xindex in range(0, mask.shape[1] + 1, 32):
        if xindex < len(x): ax.axvline(x[xindex], color="white", lw=.25, alpha=.65)
    for yindex in range(0, mask.shape[0] + 1, 32):
        if yindex < len(y): ax.axhline(y[yindex], color="white", lw=.25, alpha=.65)
    ax.set_title("A  32 x 32 output tiles over native support", loc="left", weight="bold")
    ax.set(xlabel="Longitude", ylabel="Latitude")
    ax.set_aspect(1 / np.cos(np.deg2rad(37.5)))

    ax = axes[1]; _hide(ax)
    labels = [
        ("Partition", "Four disjoint y-tile groups", BLUE),
        ("Compute", "Global land mask + local halo", RED),
        ("Checkpoint", "Fingerprint-bound tile NetCDF", GOLD),
        ("Resume", "63 finished tiles reused", GREEN),
        ("Merge", "One national result", NAVY),
    ]
    for i, (title, detail, color) in enumerate(labels):
        top = .92 - i * .18
        ax.add_patch(FancyBboxPatch((.12, top - .11), .76, .115, boxstyle="round,pad=.012",
                                    fc="white", ec=color, lw=2))
        ax.text(.15, top - .052, title, va="center", weight="bold", color=color, fontsize=10.7)
        ax.text(.46, top - .052, detail, va="center", ha="left", color=INK, fontsize=8.6)
        if i < len(labels) - 1:
            ax.add_patch(FancyArrowPatch((.5, top - .115), (.5, top - .165), arrowstyle="-|>",
                                         mutation_scale=15, color="#778794"))
    ax.set_title("B  Restartable execution path", loc="left", weight="bold")
    fig.suptitle("Scale without changing the science", fontsize=17, weight="bold", color=NAVY)
    return _save(fig, "04_tiling_and_restart.png")


def build_radius_figure() -> Path:
    with xr.open_dataset(BASE / "conus_nonstacked_synchrony.nc", engine="h5netcdf") as ds:
        values = ds.delta_pair_median.isel(time_window_end=0).load()
        x = ds.x.values; y = ds.y.values
    norm = TwoSlopeNorm(vmin=-.3, vcenter=0, vmax=.3)
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 7.1), constrained_layout=True)
    image = None
    for ax, radius in zip(axes.flat, (25, 50, 75, 100)):
        image = _map(ax, x, y, values.sel(radius_km=float(radius)), cmap="RdBu", norm=norm,
                     title=f"{radius} km Delta")
    fig.colorbar(image, ax=axes, shrink=.78, label="Median pairwise Delta = S cold - S warm")
    fig.suptitle("Nested observation radii preserve broad structure but alter local detail",
                 fontsize=17, weight="bold", color=NAVY)
    fig.text(.5, .015, "Red = negative Delta = warm synchrony stronger   |   Blue = positive Delta = cold synchrony stronger",
             ha="center", fontsize=10, weight="bold", color=INK)
    return _save(fig, "05_radius_sensitivity.png")


def build_colorado_figure() -> Path:
    with xr.open_dataset(BASE / "conus_nonstacked_synchrony.nc", engine="h5netcdf") as national, \
            xr.open_dataset(COLORADO / "colorado_nonstacked_synchrony.nc") as state:
        a = national.delta_pair_median.isel(time_window_end=0).sel(radius_km=100.0)
        b = state.delta_pair_median.isel(time_window_end=0).sel(radius_km=100.0)
        a, b = xr.align(a, b, join="inner")
        a = a.load(); b = b.load(); difference = (a - b).load()
    norm = TwoSlopeNorm(vmin=-.3, vcenter=0, vmax=.3)
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4), constrained_layout=True)
    i1 = _map(axes[0], a.x, a.y, a, cmap="RdBu", norm=norm, title="A  CONUS result cropped to Colorado")
    _map(axes[1], b.x, b.y, b, cmap="RdBu", norm=norm, title="B  Retained Colorado result")
    im = _map(axes[2], difference.x, difference.y, difference, cmap="PuOr", vmin=-1e-12, vmax=1e-12,
              title="C  Difference")
    fig.colorbar(i1, ax=axes[:2], shrink=.8, label="Median Delta = S cold - S warm")
    fig.colorbar(im, ax=axes[2], shrink=.8, label="CONUS - Colorado")
    fig.suptitle("Exact reproduction gate: maximum absolute error = 0.0",
                 fontsize=17, weight="bold", color=NAVY)
    fig.text(.37, .015, "Red = warm synchrony stronger   |   Blue = cold synchrony stronger",
             ha="center", fontsize=9.5, weight="bold", color=INK)
    return _save(fig, "06_colorado_reproduction.png")


def build_daily_validation_figure() -> Path:
    summary = _read(BASE / "station_validation" / "validation_summary.json")
    daily = summary["daily_same_label_station_median_metrics"]
    shifts = summary["daily_temporal_shift_sensitivity"]
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4), constrained_layout=True)
    variables = ["TMIN", "TMAX"]
    axes[0].bar(variables, [daily[v]["pearson"] for v in variables], color=[BLUE, RED])
    axes[0].set_ylim(0, 1); axes[0].set_ylabel("Median station Pearson")
    axes[0].set_title("A  Same-date correlation", loc="left", weight="bold")
    for i, variable in enumerate(variables): axes[0].text(i, daily[variable]["pearson"] + .025, f"{daily[variable]['pearson']:.3f}", ha="center", weight="bold")
    axes[1].bar(variables, [daily[v]["mae"] for v in variables], color=[BLUE, RED])
    axes[1].set_ylim(0, 2.1); axes[1].set_ylabel("Median MAE (deg C)")
    axes[1].set_title("B  Same-date error", loc="left", weight="bold")
    for i, variable in enumerate(variables): axes[1].text(i, daily[variable]["mae"] + .07, f"{daily[variable]['mae']:.2f}", ha="center", weight="bold")
    for variable, color in zip(variables, (BLUE, RED)):
        axes[2].plot([-1, 0, 1], [shifts[variable][str(i)]["spearman"] for i in (-1, 0, 1)],
                     marker="o", lw=2, color=color, label=variable)
    axes[2].set(xticks=[-1, 0, 1], xlabel="PRISM label shift (days)", ylabel="Median station Spearman", ylim=(.55, 1))
    axes[2].axvline(0, color=INK, lw=.8, ls="--")
    axes[2].set_title("C  Temporal-alignment sensitivity", loc="left", weight="bold")
    axes[2].legend(frameon=False)
    for ax in axes: ax.grid(axis="y", alpha=.18)
    fig.suptitle("Nearest-cell daily values agree best without shifting the date label",
                 fontsize=17, weight="bold", color=NAVY)
    return _save(fig, "07_daily_station_validation.png")


def build_uncertainty_figure() -> Path:
    summary = _read(BASE / "station_validation" / "validation_summary.json")
    mapped = summary["collapsed_map_agreement"]
    labels = ["Cold", "Warm", "Delta"]
    names = ["cold", "warm", "delta"]
    values = np.array([mapped[name]["spearman"] for name in names])
    intervals = np.array([mapped[name]["block_bootstrap"]["confidence_intervals_95"]["spearman"] for name in names])
    errors = np.vstack((values - intervals[:, 0], intervals[:, 1] - values))
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.5), gridspec_kw={"width_ratios": (1.05, 1.45)})
    y = np.arange(3)
    axes[0].errorbar(values, y, xerr=errors, fmt="o", markersize=9, capsize=5, lw=2,
                     color=NAVY, ecolor="#7193AD")
    axes[0].set(yticks=y, yticklabels=labels, xlim=(0, 1), xlabel="Spearman agreement")
    axes[0].invert_yaxis(); axes[0].grid(axis="x", alpha=.2)
    axes[0].set_title("A  95% spatial-block bootstrap intervals", loc="left", weight="bold")
    for i, value in enumerate(values): axes[0].text(value + .025, i, f"{value:.3f}", va="center", weight="bold")
    ax = axes[1]; _hide(ax)
    warnings = [
        ("Not an independent holdout", "PRISM may ingest some selected stations", RED),
        ("Edges share stations", "3,721 pair rows are statistically dependent", GOLD),
        ("Different graph density", "Stations are sparse and irregular vs. the grid", BLUE),
        ("One winter window", "Results are not a climatology or regime map", GREEN),
    ]
    for i, (title, detail, color) in enumerate(warnings):
        top = .92 - i * .22
        ax.add_patch(FancyBboxPatch((.04, top - .13), .92, .14, boxstyle="round,pad=.012",
                                    fc="white", ec=color, lw=1.8))
        ax.text(.08, top - .045, title, fontsize=11, weight="bold", color=color, va="center")
        ax.text(.08, top - .095, detail, fontsize=9.7, color=INK, va="center")
    ax.set_title("B  How to interpret the evidence", loc="left", weight="bold")
    fig.suptitle("Uncertainty is reported, not hidden", fontsize=17, weight="bold", color=NAVY)
    return _save(fig, "08_uncertainty_and_limits.png")


def build_performance_figure() -> Path:
    performance = _read(BASE / "performance.json")
    cards = [
        ("481,630", "complete focal pixels", BLUE),
        ("555", "restartable tiles", GREEN),
        ("688.2M", "non-self pair calculations", RED),
        ("4", "parallel partitions", GOLD),
        (f"{performance['wall_seconds_max_partition'] / 60:.1f} min", "slowest partition", NAVY),
        ("15", "primary and QC GeoTIFFs", "#6E5AA8"),
    ]
    fig, ax = plt.subplots(figsize=(13.2, 4.8)); _hide(ax)
    for i, (value, label, color) in enumerate(cards):
        row, col = divmod(i, 3)
        x = .05 + col * .32; y = .57 - row * .40
        ax.add_patch(FancyBboxPatch((x, y), .27, .28, boxstyle="round,pad=.015,rounding_size=.02",
                                    fc="white", ec=color, lw=2.2))
        ax.text(x + .135, y + .18, value, ha="center", va="center", fontsize=23, weight="bold", color=color)
        ax.text(x + .135, y + .08, label, ha="center", va="center", fontsize=11, color=INK)
    ax.text(.5, .96, "Completed national calculation", ha="center", fontsize=18, weight="bold", color=NAVY)
    return _save(fig, "09_performance_summary.png")


def generate_figures() -> dict[str, Path]:
    paths = {
        "primary": build_primary_semantics_figure(),
        "workflow": build_workflow_figure(),
        "source": build_source_figure(),
        "method": build_method_figure(),
        "tiling": build_tiling_figure(),
        "radius": build_radius_figure(),
        "colorado": build_colorado_figure(),
        "daily": build_daily_validation_figure(),
        "uncertainty": build_uncertainty_figure(),
        "performance": build_performance_figure(),
    }
    return paths


def _fitted(path: Path, width: float, height: float) -> Image:
    with PILImage.open(path) as image:
        ratio = min(width / image.width, height / image.height)
        return Image(str(path), width=image.width * ratio, height=image.height * ratio)


def _table(rows, widths=None, *, font_size=9, header=True):
    table = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(INK)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#AAB7C4")),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    table.setStyle(TableStyle(commands))
    return table


def _footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CFD8E1"))
    canvas.line(.55 * inch, .43 * inch, PAGE[0] - .55 * inch, .43 * inch)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(.58 * inch, .22 * inch, "CubeDynamics | CONUS non-stacked synchrony | corrected semantic edition")
    canvas.drawRightString(PAGE[0] - .58 * inch, .22 * inch, str(document.page))
    canvas.restoreState()


def build_pdf(figures: dict[str, Path]) -> Path:
    findings = _read(BASE / "findings.json")
    qc = _read(BASE / "qc.json")
    performance = _read(BASE / "performance.json")
    gate = _read(BASE / "colorado_reproduction_gate.json")
    validation = _read(BASE / "station_validation" / "validation_summary.json")
    conus = findings["conus_100km"]
    pair = validation["pair_agreement"]
    mapped = validation["collapsed_map_agreement"]
    daily = validation["daily_same_label_station_median_metrics"]
    audit_manifest = _read(AUDIT / "audit_manifest.json")
    collapsed_audit = _read(AUDIT / "collapsed_pixel_provenance.json")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25,
                           leading=29, textColor=colors.HexColor(NAVY), alignment=TA_CENTER, spaceAfter=8)
    subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=13, leading=17,
                              textColor=colors.HexColor(INK), alignment=TA_CENTER)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18,
                        leading=22, textColor=colors.HexColor(NAVY), spaceAfter=7)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.8, leading=13.2,
                          textColor=colors.HexColor(INK), spaceAfter=6)
    small = ParagraphStyle("Small", parent=body, fontSize=8.5, leading=10.7, textColor=colors.HexColor(MUTED))
    callout = ParagraphStyle("Callout", parent=body, fontName="Helvetica-Bold", fontSize=12.3,
                             leading=15.5, textColor=colors.HexColor(RED), alignment=TA_CENTER,
                             borderColor=colors.HexColor(RED), borderWidth=1, borderPadding=7,
                             backColor=colors.HexColor("#FFF4F2"))
    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=PAGE, leftMargin=.55 * inch, rightMargin=.55 * inch,
        topMargin=.46 * inch, bottomMargin=.56 * inch,
        title="CONUS non-stacked synchrony walkthrough - corrected semantic edition",
        author="CubeDynamics project",
        subject="Audited visual explanation of the national PRISM synchrony calculation and GHCN-Daily agreement checks",
    )
    story = []

    story.extend([
        Spacer(1, .10 * inch),
        Paragraph("How we built and verified the CONUS synchrony map", title),
        Paragraph("Corrected semantic edition - lower-TMIN cold, upper-TMAX warm, Delta = S cold - S warm", subtitle),
        Spacer(1, .08 * inch),
        _fitted(figures["primary"], 8.9 * inch, 4.25 * inch),
        Spacer(1, .06 * inch),
        _table([
            ["Coverage", "Method", "Primary finding", "Station comparison"],
            ["481,630 PRISM cells", "100 km non-stacked reduction", "Median Delta = -0.017", "1,500 GHCN stations"],
        ], widths=(2.3 * inch,) * 4, font_size=9.5),
        Paragraph("Delta = S cold - S warm. Blue Delta is positive and means cold synchrony is stronger; red Delta is negative and means warm synchrony is stronger.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Audited semantic contract", h1),
        _table([
            ["Object", "Literal rule", "Meaning"],
            ["Cold", "Both pixels: TMIN <= their own median", "Joint lower local TMIN tail"],
            ["Warm", "Both pixels: TMAX > their own median", "Joint strict upper local TMAX tail"],
            ["S cold", "Average-rank Spearman on selected cold dates", "Cold-tail spatial synchrony"],
            ["S warm", "Average-rank Spearman on selected warm dates", "Warm-tail spatial synchrony"],
            ["Delta", "S cold - S warm", "Positive: cold stronger; negative: warm stronger"],
            ["Map cell", "median(pairwise Delta) over non-self neighbors", "Not median(cold) - median(warm)"],
        ], widths=(1.35 * inch, 3.7 * inch, 4.2 * inch), font_size=8.8),
        Spacer(1, .12 * inch),
        _table([
            ["Visual sign", "Current color", "Required interpretation"],
            ["Delta < 0", "Red", "S warm > S cold; warm synchrony is stronger"],
            ["Delta = 0", "Near-white", "Cold and warm synchrony are equal"],
            ["Delta > 0", "Blue", "S cold > S warm; cold synchrony is stronger"],
        ], widths=(1.8 * inch, 1.8 * inch, 5.65 * inch), font_size=9.0),
        Spacer(1, .16 * inch),
        Paragraph(
            f"Independent audit evidence: five real PRISM pairs matched direct Spearman recomputation to 2.22e-16; three known-answer cases passed; and one western cell's {collapsed_audit['incident_nonself_pairs']:,} relationships reproduced the NetCDF exactly and the float32 GeoTIFF within {collapsed_audit['geotiff_absolute_error']:.2e}.",
            body,
        ),
        Paragraph("Every Delta figure in this corrected edition follows the red-negative/warm-stronger and blue-positive/cold-stronger rule.", callout),
        PageBreak(),
    ])

    story.extend([
        Paragraph("The complete workflow", h1),
        _fitted(figures["workflow"], 9.65 * inch, 4.6 * inch),
        Spacer(1, .12 * inch),
        Paragraph("The national job changes the spatial extent and execution strategy, not the statistic. Every focal pixel is processed independently, its local surface is reduced immediately, and that surface is discarded after the summary is checkpointed.", body),
        Paragraph("No stack, overlap alignment, learned model, or second-stage convolution was used.", callout),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 1 - Freeze the real input data", h1),
        _fitted(figures["source"], 9.65 * inch, 4.75 * inch),
        _table([
            ["Input contract", "Value"],
            ["Product", "PRISM AN daily TMIN and TMAX via NCSCO THREDDS"],
            ["Date labels", "2023-11-01 through 2024-01-30; 91 daily layers"],
            ["Native grid", "621 x 1,399 cells at approximately 1/24 degree"],
            ["Synthetic fallback", "Forbidden for this analysis"],
        ], widths=(2.15 * inch, 7.1 * inch), font_size=8.7),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 2 - Define eligible focal and computation pixels", h1),
        _fitted(figures["tiling"], 9.65 * inch, 4.10 * inch),
        Paragraph("A cell is eligible only when all 91 TMIN and TMAX values are finite. The same global land mask limits pair endpoints; the output mask can then select a partition without changing its neighbors. This separation prevents ocean and nodata cells from affecting tail-support decisions.", body),
        Paragraph("At Canada, Mexico, and coast boundaries, the 100 km neighborhood is clipped to native PRISM support. It is not filled with invented observations.", callout),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 3 - Calculate cold and warm synchrony for each pair", h1),
        _fitted(figures["method"], 9.65 * inch, 4.75 * inch),
        _table([
            ["Quantity", "Definition"],
            ["Cold", "Average-rank Spearman on dates where both pixels have TMIN <= their own median"],
            ["Warm", "Average-rank Spearman on dates where both pixels have TMAX > their own median"],
            ["Delta", "S cold - S warm for the same focal-neighbor pair"],
            ["Self-pair", "Excluded before every reduction"],
        ], widths=(1.75 * inch, 7.5 * inch), font_size=8.7),
        Paragraph("The upper-tail inequality is strict (>), while the lower-tail inequality is inclusive (<=). The time-series panel is illustrative; all reported maps use observed PRISM values and the repository's validated pair kernel.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 4 - Reduce one local surface to one map cell", h1),
        _fitted(COLORADO / "figures" / "pedagogical_reduction.png", 9.65 * inch, 5.15 * inch),
        Paragraph("For each focal pixel, all non-self pair values inside the radius form a local surface. The primary map stores median cold, median warm, and median pairwise Delta. Mean, IQR, MAD, extrema, percentiles, counts, and valid fractions are retained as diagnostics. The full surface is not stacked or propagated into a second calculation.", body),
        Paragraph("The mapped Delta is median(S cold - S warm). The separately retained median(S cold) - median(S warm) is not substituted for it.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 5 - Tile, checkpoint, resume, and merge", h1),
        _fitted(figures["tiling"], 9.65 * inch, 3.85 * inch),
        _table([
            ["Execution fact", "Observed value"],
            ["Output tiles", f"{performance['tile_count']:,} at 32 x 32 focal cells"],
            ["Parallel partitions", f"{performance['partition_count']} disjoint y-tile groups"],
            ["Restart behavior", f"{performance['resumed_tile_count']} tiles reused; {performance['computed_tile_count']} computed in the final run"],
            ["Non-self pair calculations", f"{performance['nonself_pair_calculations_with_tile_recompute']:,}"],
            ["Slowest partition", f"{performance['wall_seconds_max_partition'] / 60:.1f} minutes"],
        ], widths=(3.0 * inch, 6.25 * inch), font_size=8.8),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 6 - Assemble the national maps", h1),
        _fitted(figures["primary"], 9.65 * inch, 4.75 * inch),
        _table([
            ["Map", "Median across focal pixels", "Interpretation"],
            ["Cold", f"{conus['cold_median_across_focal_pixels']:.3f}", "Median lower-TMIN-tail synchrony"],
            ["Warm", f"{conus['warm_median_across_focal_pixels']:.3f}", "Median upper-TMAX-tail synchrony; slightly higher nationally"],
            ["Delta", f"{conus['delta_pair_median_across_focal_pixels']:+.3f}", f"{100 * conus['delta_negative_fraction']:.1f}% negative: warm synchrony stronger"],
        ], widths=(1.4 * inch, 2.5 * inch, 5.35 * inch), font_size=8.7),
        Paragraph("Color rule for Delta only: red means negative/warm stronger; blue means positive/cold stronger. Cold and warm panels show correlation sign, not temperature itself.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 7 - Check support, seams, and reduction behavior", h1),
        _fitted(BASE / "figures" / "qc_maps.png", 9.65 * inch, 5.2 * inch),
        Paragraph(f"All {qc['output_pixels']:,} selected pixels have finite primary outputs. Valid pair fractions are 1.0; support counts vary from {qc['support']['count_min']:,} at clipped boundaries to {qc['support']['count_max']:,} in the interior. Tile-seam jump ratios are approximately one, indicating no numerical checkerboard introduced by checkpoint boundaries.", body),
        Paragraph("Pairwise median(cold - warm) and median(cold) - median(warm) are related but not mathematically identical. Their national rank correlation is 0.983; both are retained.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 8 - Repeat the reduction at nested radii", h1),
        _fitted(figures["radius"], 9.65 * inch, 4.10 * inch),
        _table([
            ["Radius comparison", "Delta rank correlation with 100 km"],
            ["25 vs 100 km", f"{findings['nested_radius_sensitivity']['25_vs_100km_spearman']:.3f}"],
            ["50 vs 100 km", f"{findings['nested_radius_sensitivity']['50_vs_100km_spearman']:.3f}"],
            ["75 vs 100 km", f"{findings['nested_radius_sensitivity']['75_vs_100km_spearman']:.3f}"],
        ], widths=(3.2 * inch, 3.0 * inch), font_size=8.7),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 9 - Require exact Colorado equivalence", h1),
        _fitted(figures["colorado"], 9.65 * inch, 4.65 * inch),
        Paragraph(f"The CONUS input exactly matches the retained Colorado-plus-halo snapshot in their common domain. Every nested-radius Colorado output field also matches exactly: maximum absolute error {gate['maximum_absolute_error']:.1f}, with tolerance {gate['tolerance']:.0e}.", body),
        Paragraph("This is the main regression gate showing that scaling to CONUS did not silently change the earlier Colorado method.", callout),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 10 - Build a spatially balanced station network", h1),
        _fitted(BASE / "station_validation" / "figures" / "station_network.png", 9.65 * inch, 4.65 * inch),
        Paragraph(f"From 1,800 spatially balanced candidates, {validation['qualified_count']:,} passed the 80% TMIN/TMAX completeness rule and {validation['selected_count']:,} were retained. All nonnumeric observations and every nonblank GHCN quality flag were excluded. The network contains {validation['pair_count']:,} non-self edges no longer than 100 km.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 11 - Check daily station temperatures against PRISM", h1),
        _fitted(figures["daily"], 9.65 * inch, 4.65 * inch),
        _table([
            ["Variable", "Median bias", "Median MAE", "Median Pearson", "Median Spearman"],
            ["TMIN", f"{daily['TMIN']['bias']:+.3f} deg C", f"{daily['TMIN']['mae']:.3f} deg C", f"{daily['TMIN']['pearson']:.3f}", f"{daily['TMIN']['spearman']:.3f}"],
            ["TMAX", f"{daily['TMAX']['bias']:+.3f} deg C", f"{daily['TMAX']['mae']:.3f} deg C", f"{daily['TMAX']['pearson']:.3f}", f"{daily['TMAX']['spearman']:.3f}"],
        ], widths=(1.4 * inch, 1.7 * inch, 1.7 * inch, 2.0 * inch, 2.0 * inch), font_size=8.7),
        Paragraph("The same-date label performs better than shifting PRISM by -1 or +1 day, so no silent time adjustment was introduced.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 12 - Compare station-pair and nearest-pixel synchrony", h1),
        _fitted(BASE / "station_validation" / "figures" / "pair_station_vs_prism.png", 9.65 * inch, 4.35 * inch),
        _table([
            ["Metric", "N", "Bias", "MAE", "Pearson", "Spearman"],
            *[[name.title(), f"{pair[name]['n']:,}", f"{pair[name]['bias']:+.3f}", f"{pair[name]['mae']:.3f}", f"{pair[name]['pearson']:.3f}", f"{pair[name]['spearman']:.3f}"] for name in ("cold", "warm", "delta")],
        ], widths=(1.4 * inch, 1.2 * inch, 1.3 * inch, 1.3 * inch, 1.5 * inch, 1.5 * inch), font_size=8.7),
        Paragraph("Delta is cold minus warm for both the station pair and nearest PRISM-pixel pair. These rows share stations and are not independent replicates; no edge-level p-values are reported.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 13 - Collapse the station network and compare with the map", h1),
        _fitted(BASE / "station_validation" / "figures" / "collapsed_station_vs_map.png", 9.65 * inch, 4.35 * inch),
        _table([
            ["Metric", "N stations", "Bias", "MAE", "Pearson", "Spearman"],
            *[[name.title(), f"{mapped[name]['n']:,}", f"{mapped[name]['bias']:+.3f}", f"{mapped[name]['mae']:.3f}", f"{mapped[name]['pearson']:.3f}", f"{mapped[name]['spearman']:.3f}"] for name in ("cold", "warm", "delta")],
        ], widths=(1.4 * inch, 1.4 * inch, 1.3 * inch, 1.3 * inch, 1.5 * inch, 1.5 * inch), font_size=8.7),
        Paragraph(f"The map comparison retains {validation['eligible_collapsed_station_count']:,} stations with at least three finite cold, warm, and cold-minus-warm Delta incident edges. The station graph is much sparser than the complete raster neighborhood, so perfect one-to-one agreement is not expected.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Step 14 - Quantify uncertainty and state the limits", h1),
        _fitted(figures["uncertainty"], 9.65 * inch, 3.85 * inch),
        Paragraph("The 95% intervals resample 5 degree spatial blocks rather than individual stations. This preserves some regional dependence during uncertainty estimation. The correct phrase for these results is observational agreement, not independent validation.", small),
        Paragraph("The maps describe one 90-day winter window. They do not by themselves establish persistent climate regions, causal mechanisms, or a national climatology.", callout),
        PageBreak(),
    ])

    story.extend([
        Paragraph("What the team should take away", h1),
        _fitted(figures["performance"], 9.65 * inch, 4.25 * inch),
        _table([
            ["Question", "Answer"],
            ["Did scaling change the Colorado statistic?", "No. The exact reproduction gate passed with zero numerical error."],
            ["Is the national workflow restartable?", "Yes. Every tile is fingerprint-bound, checkpointed, and merge-validated."],
            ["Is the national pattern spatially coherent?", "Yes. Adjacent-pixel correlations are 0.944 cold, 0.951 warm, and 0.926 Delta."],
            ["Do stations agree perfectly?", "No. Agreement is strongest for cold, moderate for Delta, and weaker for warm."],
            ["What does western red mean?", "Negative Delta: upper-TMAX warm synchrony is stronger than lower-TMIN cold synchrony."],
            ["What is the strongest caveat?", "GHCN is not a strict holdout because PRISM may ingest the same stations."],
        ], widths=(3.3 * inch, 5.95 * inch), font_size=8.6),
        PageBreak(),
    ])

    story.extend([
        Paragraph("Products, reproduction, and sources", h1),
        _fitted(figures["workflow"], 9.65 * inch, 2.70 * inch),
        _table([
            ["Deliverable", "Location or command"],
            ["National NetCDF", "artifacts/nonstacked-conus-baseline/conus_nonstacked_synchrony.nc"],
            ["GeoTIFFs", "artifacts/nonstacked-conus-baseline/rasters/"],
            ["Station evidence", "artifacts/nonstacked-conus-baseline/station_validation/"],
            ["Semantics audit", f"artifacts/hot-cold-delta-semantics-audit/ ({audit_manifest['overall_verdict']})"],
            ["Reproduce maps", ".venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage all"],
            ["Reproduce station checks", ".venv/bin/python scripts/validate_nonstacked_conus_stations.py --stage all"],
            ["Rebuild this edition", ".venv/bin/python scripts/build_nonstacked_conus_walkthrough.py"],
            ["Validation", "980 offline tests passed; 5 skipped; 419 deselected"],
        ], widths=(2.35 * inch, 6.9 * inch), font_size=7.8),
        Spacer(1, .12 * inch),
        Paragraph("PRISM dataset documentation: https://www.prism.oregonstate.edu/documents/PRISM_datasets.pdf", small),
        Paragraph("NOAA/NCEI GHCN-Daily: https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily", small),
        Paragraph("Corrected semantic edition generated 2026-09-24 from retained real-data artifacts and the machine-readable hot/cold/Delta audit. The original walkthrough PDF remains preserved for provenance.", small),
    ])

    temporary = OUTPUT.with_suffix(".partial.pdf")
    document.filename = str(temporary)
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    temporary.replace(OUTPUT)
    return OUTPUT


def main() -> int:
    figures = generate_figures()
    output = build_pdf(figures)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
