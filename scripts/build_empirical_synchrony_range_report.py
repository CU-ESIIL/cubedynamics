#!/usr/bin/env python3
"""Build the visual empirical synchrony-range pilot walkthrough."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, TwoSlopeNorm
import numpy as np
from PIL import Image as PILImage
try:
    import reportlab  # noqa: F401
except ModuleNotFoundError:
    import sys

    sys.path.append(
        "/Users/tuff/.cache/codex-runtimes/codex-primary-runtime/dependencies/"
        "python/lib/python3.12/site-packages"
    )
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from shapely.geometry import shape
import xarray as xr

from cubedynamics.synchrony.ranges import empirical_synchrony_range


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts" / "empirical-synchrony-range"
FIGURES = BASE / "figures"
ASSETS = BASE / "report_assets"
OUTPUT = ROOT / "output" / "pdf" / "empirical_synchrony_range_pilot_walkthrough.pdf"
COLORADO_BASELINE = ROOT / "artifacts" / "nonstacked-colorado-baseline" / "colorado_nonstacked_synchrony.nc"
COLORADO_BOUNDARY = ROOT / "artifacts" / "synchrony-stack-phase2" / "colorado_boundary.geojson"
PILOT = BASE / "colorado_25_site_range_pilot.nc"
PAGE = landscape(letter)

NAVY = "#123F70"
BLUE = "#2878B5"
RED = "#B63A3A"
GOLD = "#F0B43C"
GREEN = "#3A8D6D"
INK = "#17212B"
MUTED = "#586775"
LIGHT = "#EDF3F7"


def _save(fig: plt.Figure, name: str) -> Path:
    ASSETS.mkdir(parents=True, exist_ok=True)
    path = ASSETS / name
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _boundary():
    document = json.loads(COLORADO_BOUNDARY.read_text(encoding="utf-8"))
    return shape(document["features"][0]["geometry"])


def _outline(ax, boundary) -> None:
    geometries = list(boundary.geoms) if hasattr(boundary, "geoms") else [boundary]
    for geometry in geometries:
        xx, yy = geometry.exterior.xy
        ax.plot(xx, yy, color=INK, lw=0.8)
    ax.set_aspect(1 / np.cos(np.deg2rad(39.0)))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")


def _build_assets() -> dict[str, Path]:
    ASSETS.mkdir(parents=True, exist_ok=True)
    assets: dict[str, Path] = {}

    fig, ax = plt.subplots(figsize=(12.2, 3.2))
    ax.axis("off")
    steps = ["Focal pixel", "Neighbors <= 100 km", "Validated pair synchrony", "Median pairwise Delta", "One output pixel"]
    for index, label in enumerate(steps):
        x = 0.04 + index * 0.195
        ax.add_patch(plt.Rectangle((x, .34), .155, .32, fc="white", ec=NAVY, lw=2))
        ax.text(x + .0775, .50, label, ha="center", va="center", fontsize=10, weight="bold", wrap=True)
        if index < len(steps) - 1:
            ax.annotate("", (x + .19, .50), (x + .158, .50), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.5))
    ax.text(.5, .83, "Existing fixed 100 km control", ha="center", fontsize=17, weight="bold", color=NAVY)
    ax.text(.5, .12, "No stacking | no second convolution | self-pair excluded", ha="center", fontsize=11, color=RED, weight="bold")
    assets["fixed_workflow"] = _save(fig, "fixed_workflow.png")

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.0), constrained_layout=True)
    for ax in axes:
        ax.set_aspect("equal"); ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15); ax.axis("off")
    for x in (-.6, 0, .6):
        axes[0].add_patch(plt.Circle((x, 0), .35, fill=False, lw=2, color=BLUE))
        axes[0].scatter([x], [0], marker="*", s=100, color=GOLD, edgecolor=INK)
    axes[0].set_title("Fixed: every focal pixel gets 100 km", weight="bold", color=NAVY)
    for x, radius in zip((-.6, 0, .6), (.22, .55, .82)):
        axes[1].add_patch(plt.Circle((x, 0), radius, fill=False, lw=2, color=GREEN))
        axes[1].scatter([x], [0], marker="*", s=100, color=GOLD, edgecolor=INK)
    axes[1].set_title("Question: does empirical support differ?", weight="bold", color=NAVY)
    fig.suptitle("The experiment changes neighbor selection only", fontsize=16, weight="bold")
    assets["why_adaptive"] = _save(fig, "why_adaptive.png")

    with xr.open_dataset(PILOT, engine="h5netcdf") as pilot:
        status_counts = {}
        mask = np.asarray(pilot.output_mask.values, dtype=bool)
        for metric in ("cold", "warm", "common"):
            status = pilot[f"{metric}_range_status"].isel(time_window_end=0).values[mask]
            status_counts[metric] = [int(np.count_nonzero(status == code)) for code in range(4)]
        sample_y, sample_x = np.nonzero(mask)
        lon = np.asarray(pilot.x.values)[sample_x]
        lat = np.asarray(pilot.y.values)[sample_y]

    fig, ax = plt.subplots(figsize=(9.6, 4.0), constrained_layout=True)
    bottom = np.zeros(3)
    labels = ("Insufficient", "Flat", "Censored/unresolved", "Resolved")
    palette = ("#A9B4BD", GOLD, RED, GREEN)
    for code, (label, color) in enumerate(zip(labels, palette)):
        values = [status_counts[m][code] for m in ("cold", "warm", "common")]
        ax.bar(("Cold", "Warm", "Common"), values, bottom=bottom, color=color, label=label)
        bottom += values
    ax.set(ylabel="Pilot sites", ylim=(0, 27))
    ax.set_title("Only 1 of 25 sites resolves a common range", color=NAVY, weight="bold")
    ax.legend(frameon=False, ncol=4, loc="upper center")
    assets["status_summary"] = _save(fig, "status_summary.png")

    background_rows = list(csv.DictReader((BASE / "background_method_sensitivity.csv").open(encoding="utf-8")))
    methods = ("outer_annuli", "smoothed_outer_annuli", "distant_pairs")
    counts = [sum(row["background_method"] == method and row["common_status"] == "resolved" for row in background_rows) for method in methods]
    fig, ax = plt.subplots(figsize=(9.4, 3.7), constrained_layout=True)
    bars = ax.bar(("Outer annuli", "Smoothed outer", "Distant pairs"), counts, color=(BLUE, GOLD, GREEN))
    for bar, value in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, value + .2, str(value), ha="center", weight="bold")
    ax.set(ylabel="Resolved common ranges (of 25)", ylim=(0, 25))
    ax.set_title("Changing the empirical background does not rescue identifiability", color=NAVY, weight="bold")
    assets["background_summary"] = _save(fig, "background_summary.png")

    performance = json.loads((BASE / "performance.json").read_text(encoding="utf-8"))
    pair_bounds = performance["rough_full_colorado_pair_work_lower_upper"], performance["rough_full_conus_pair_work_lower_upper"]
    fig, ax = plt.subplots(figsize=(9.5, 4.0), constrained_layout=True)
    positions = np.arange(2)
    lows = np.asarray([item[0] for item in pair_bounds], dtype=float)
    highs = np.asarray([item[1] for item in pair_bounds], dtype=float)
    ax.bar(positions, highs, color=(BLUE, RED), alpha=.78)
    ax.bar(positions, lows, color=(NAVY, "#7D0018"), alpha=.95)
    ax.set_yscale("log")
    ax.set_xticks(positions, ("Full Colorado", "Full CONUS"))
    ax.set_ylabel("Estimated discovery-radius pair work")
    ax.set_title("500 km discovery support changes the engineering scale", color=NAVY, weight="bold")
    for x, low, high in zip(positions, lows, highs):
        ax.text(x, high * 1.08, f"{low/1e9:.2f}-{high/1e9:.2f} billion", ha="center", fontsize=10)
    assets["performance"] = _save(fig, "performance_scale.png")

    boundary = _boundary()
    fig, ax = plt.subplots(figsize=(7.7, 5.0), constrained_layout=True)
    _outline(ax, boundary)
    ax.scatter(lon, lat, s=72, color=GOLD, edgecolor=INK, linewidth=.7)
    ax.set_title("25 spatially balanced Colorado pilot sites", color=NAVY, weight="bold")
    assets["site_map"] = _save(fig, "colorado_site_map.png")

    with xr.open_dataset(COLORADO_BASELINE, engine="scipy") as baseline:
        mask_state = baseline.output_mask.values.astype(bool)
        cold = baseline.cold_median.sel(radius_km=100).isel(time_window_end=0).where(baseline.output_mask).values
        warm = baseline.warm_median.sel(radius_km=100).isel(time_window_end=0).where(baseline.output_mask).values
        delta = baseline.delta_pair_median.sel(radius_km=100).isel(time_window_end=0).where(baseline.output_mask).values
        bx, by = baseline.x.values, baseline.y.values
    sync_low, sync_high = np.nanpercentile(np.concatenate((cold[mask_state], warm[mask_state])), (1, 99))
    dlim = max(float(np.nanpercentile(np.abs(delta[mask_state]), 99)), .05)
    fig, axes = plt.subplots(1, 3, figsize=(13.4, 4.2), constrained_layout=True)
    for ax, values, title, cmap, norm in (
        (axes[0], cold, "Fixed cold", "viridis", Normalize(sync_low, sync_high)),
        (axes[1], warm, "Fixed warm", "viridis", Normalize(sync_low, sync_high)),
        (axes[2], delta, "Fixed Delta", "RdBu", TwoSlopeNorm(vmin=-dlim, vcenter=0, vmax=dlim)),
    ):
        image = ax.pcolormesh(bx, by, values, shading="nearest", cmap=cmap, norm=norm, rasterized=True)
        _outline(ax, boundary); ax.set_title(title, weight="bold")
        fig.colorbar(image, ax=ax, shrink=.72)
    fig.suptitle("Validated full-state 100 km control remains unchanged", fontsize=16, weight="bold", color=NAVY)
    assets["fixed_maps"] = _save(fig, "fixed_colorado_maps.png")

    with xr.open_dataset(PILOT, engine="h5netcdf") as pilot, xr.open_dataset(COLORADO_BASELINE, engine="scipy") as baseline:
        mask = pilot.output_mask.values.astype(bool)
        yy, xx = np.nonzero(mask)
        pilot_delta_iqr = baseline.delta_iqr.sel(radius_km=100).isel(time_window_end=0).reindex(y=pilot.y, x=pilot.x).values[yy, xx]
        gap = baseline.delta_reduction_gap.sel(radius_km=100).isel(time_window_end=0).reindex(y=pilot.y, x=pilot.x).values[yy, xx]
        cold_range = pilot.cold_range_km.isel(time_window_end=0).values[yy, xx]
        warm_range = pilot.warm_range_km.isel(time_window_end=0).values[yy, xx]
    for values, xlabel, panel_title, asset_name, filename in (
        (
            pilot_delta_iqr,
            "Fixed 100 km Delta IQR",
            "Range vs relational heterogeneity",
            "qc_iqr",
            "qc_iqr.png",
        ),
        (
            gap,
            "Fixed 100 km reduction gap",
            "Range vs reduction non-commutativity",
            "qc_gap",
            "qc_reduction_gap.png",
        ),
    ):
        fig, ax = plt.subplots(figsize=(9.6, 4.2), constrained_layout=True)
        for ranges, color, label in ((cold_range, BLUE, "Cold R*"), (warm_range, RED, "Warm R*")):
            valid = np.isfinite(ranges)
            ax.scatter(values[valid], ranges[valid], s=68, color=color, alpha=.8, label=label)
        ax.set(xlabel=xlabel, ylabel="Resolved tail range (km)", title=panel_title)
        ax.grid(alpha=.16)
        ax.legend(frameon=False)
        fig.suptitle(
            "Common-range inference is too sparse for a valid map-level relationship",
            fontsize=14,
            color=NAVY,
            weight="bold",
        )
        assets[asset_name] = _save(fig, filename)

    assets.update(_standalone_method_panels())
    assets.update(_standalone_pilot_maps())
    assets.update(_standalone_mountain_curves())
    return assets


def _crop_panels(path: Path, prefix: str, rows: int, columns: int) -> dict[str, Path]:
    image = PILImage.open(path).convert("RGB")
    width, height = image.size
    top_trim = int(height * 0.055)
    content = image.crop((0, top_trim, width, height))
    panel_height = content.height / rows
    panel_width = content.width / columns
    result = {}
    for row in range(rows):
        for column in range(columns):
            left = int(column * panel_width)
            upper = int(row * panel_height)
            right = int((column + 1) * panel_width)
            lower = int((row + 1) * panel_height)
            cropped = content.crop((left, upper, right, lower))
            target = ASSETS / f"{prefix}_{row}_{column}.png"
            cropped.save(target)
            result[f"{prefix}_{row}_{column}"] = target
    return result


def _standalone_method_panels() -> dict[str, Path]:
    result: dict[str, Path] = {}
    rng = np.random.default_rng(42)
    distance = rng.uniform(0, 500, 1500)
    synchrony = 0.25 + 0.6 * np.exp(-distance / 90) + rng.normal(0, 0.08, distance.size)
    radial = np.arange(10, 501, 20)
    curve = 0.25 + 0.6 * np.exp(-radial / 90)

    fig, ax = plt.subplots(figsize=(7.3, 4.5), constrained_layout=True)
    for radius, color in ((.25, "#C7DCEF"), (.5, "#83B4D7"), (.75, "#3E84B8"), (1.0, NAVY)):
        ax.add_patch(plt.Circle((0, 0), radius, fill=False, color=color, lw=2.3))
    ax.scatter([0], [0], marker="*", s=190, color=GOLD, edgecolor=INK, zorder=5)
    ax.set(xlim=(-1.08, 1.08), ylim=(-1.08, 1.08), aspect="equal")
    ax.axis("off"); ax.set_title("One focal pixel inside large discovery support", color=NAVY, weight="bold")
    result["pedagogy_0_0"] = _save(fig, "standalone_focal_discovery.png")

    fig, ax = plt.subplots(figsize=(7.5, 4.4), constrained_layout=True)
    ax.scatter(distance, synchrony, s=7, alpha=.20, color=BLUE)
    ax.set(xlabel="Physical distance (km)", ylabel="Pair synchrony", xlim=(0, 500), ylim=(-.1, 1.05))
    ax.grid(alpha=.15); ax.set_title("Individual pair values versus distance", color=NAVY, weight="bold")
    result["pedagogy_0_1"] = _save(fig, "standalone_pair_scatter.png")

    fig, ax = plt.subplots(figsize=(7.3, 4.5), constrained_layout=True)
    for radius in range(20, 501, 20):
        ax.add_patch(plt.Circle((0, 0), radius / 500, fill=False, color=BLUE, alpha=.25, lw=1.1))
    ax.scatter([0], [0], marker="*", s=190, color=GOLD, edgecolor=INK, zorder=5)
    ax.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05), aspect="equal")
    ax.axis("off"); ax.set_title("Twenty-kilometer physical annuli", color=NAVY, weight="bold")
    result["pedagogy_0_2"] = _save(fig, "standalone_annuli.png")

    fig, ax = plt.subplots(figsize=(7.5, 4.4), constrained_layout=True)
    ax.plot(radial, curve, color=BLUE, lw=2.2, marker="o", ms=3.5)
    ax.axhline(.25, color=GOLD, lw=2, label="Distant background")
    ax.axvline(260, color=GREEN, lw=2.2, label="Candidate R*")
    ax.set(xlabel="Distance (km)", ylabel="Annular synchrony", xlim=(0, 500), ylim=(.2, .9))
    ax.grid(alpha=.15); ax.legend(frameon=False)
    ax.set_title("Persistent approach to empirical background", color=NAVY, weight="bold")
    result["pedagogy_1_0"] = _save(fig, "standalone_range_criterion.png")

    inside = distance <= 260
    fig, ax = plt.subplots(figsize=(7.5, 4.4), constrained_layout=True)
    ax.scatter(distance[~inside], synchrony[~inside], s=6, alpha=.08, color=MUTED, label="Excluded")
    ax.scatter(distance[inside], synchrony[inside], s=7, alpha=.24, color=GREEN, label="Retained")
    ax.axvline(260, color=INK, lw=1.5)
    ax.set(xlabel="Distance (km)", ylabel="Pair synchrony", xlim=(0, 500), ylim=(-.1, 1.05))
    ax.grid(alpha=.15); ax.legend(frameon=False)
    ax.set_title("R* selects neighbors; it does not weight them", color=NAVY, weight="bold")
    result["pedagogy_1_1"] = _save(fig, "standalone_neighbor_selection.png")

    fig, ax = plt.subplots(figsize=(7.5, 4.4), constrained_layout=True)
    ax.hist(synchrony[inside], bins=30, color=GREEN, alpha=.82)
    median = float(np.median(synchrony[inside]))
    ax.axvline(median, color=INK, lw=2.2, label=f"Median = {median:.3f}")
    ax.set(xlabel="Retained pair synchrony", ylabel="Count")
    ax.legend(frameon=False); ax.set_title("The validated median collapse is unchanged", color=NAVY, weight="bold")
    result["pedagogy_1_2"] = _save(fig, "standalone_median_collapse.png")
    return result


def _standalone_pilot_maps() -> dict[str, Path]:
    result: dict[str, Path] = {}
    boundary = _boundary()
    with xr.open_dataset(PILOT, engine="h5netcdf") as pilot:
        mask = pilot.output_mask.values.astype(bool)
        yy, xx = np.nonzero(mask)
        lon = np.asarray(pilot.x.values)[xx]
        lat = np.asarray(pilot.y.values)[yy]
        fields = {
            "comparison_0_1": (
                pilot.adaptive_delta_pair_median.isel(time_window_end=0).values[yy, xx],
                "Adaptive common-range Delta", "RdBu", TwoSlopeNorm(vmin=-.3, vcenter=0, vmax=.3),
            ),
            "comparison_1_1": (
                pilot.adaptive_minus_fixed_delta.isel(time_window_end=0).values[yy, xx],
                "Adaptive minus fixed Delta", "PiYG", TwoSlopeNorm(vmin=-.07, vcenter=0, vmax=.07),
            ),
            "range_0_0": (
                pilot.cold_range_km.isel(time_window_end=0).values[yy, xx],
                "Cold empirical range R* (km)", "viridis", Normalize(0, 500),
            ),
            "range_0_1": (
                pilot.warm_range_km.isel(time_window_end=0).values[yy, xx],
                "Warm empirical range R* (km)", "viridis", Normalize(0, 500),
            ),
            "range_1_0": (
                pilot.common_range_km.isel(time_window_end=0).values[yy, xx],
                "Common empirical range R* (km)", "viridis", Normalize(0, 500),
            ),
            "range_1_1": (
                pilot.range_difference_cold_minus_warm_km.isel(time_window_end=0).values[yy, xx],
                "Cold R* minus warm R* (km)", "PuOr", TwoSlopeNorm(vmin=-250, vcenter=0, vmax=250),
            ),
        }
    for key, (values, title, cmap, norm) in fields.items():
        fig, ax = plt.subplots(figsize=(7.6, 4.8), constrained_layout=True)
        _outline(ax, boundary)
        image = ax.scatter(lon, lat, c=values, s=92, cmap=cmap, norm=norm, edgecolor="white", linewidth=.7, zorder=3)
        unresolved = ~np.isfinite(values)
        ax.scatter(lon[unresolved], lat[unresolved], marker="x", s=78, color=INK, lw=1.6, zorder=4)
        fig.colorbar(image, ax=ax, shrink=.8)
        ax.set_title(title + " - x marks unresolved", color=NAVY, weight="bold")
        result[key] = _save(fig, f"standalone_{key}.png")
    return result


def _standalone_mountain_curves() -> dict[str, Path]:
    result: dict[str, Path] = {}
    checkpoint = BASE / "pair_checkpoints" / "colorado_mountains.nc"
    with xr.open_dataset(checkpoint, engine="h5netcdf") as opened:
        pairs = opened.load()
    summary = empirical_synchrony_range(pairs)
    yi, xi = np.argwhere(pairs.output_mask.values.astype(bool))[0]
    focal = int(yi) * pairs.sizes["x"] + int(xi)
    source = np.asarray(pairs.source_index.values)
    target = np.asarray(pairs.target_index.values)
    incident = ((source == focal) | (target == focal)) & (source != target)
    distance = np.asarray(pairs.distance_km.values)[incident]
    rng = np.random.default_rng(17)
    index = np.flatnonzero(incident)
    if index.size > 7000:
        index = np.sort(rng.choice(index, size=7000, replace=False))
    for key, metric, prefix, color in (
        ("mountain_0_0", "cold_synchrony", "cold", BLUE),
        ("mountain_1_0", "warm_synchrony", "warm", RED),
    ):
        fig, ax = plt.subplots(figsize=(9.5, 4.4), constrained_layout=True)
        ax.scatter(
            np.asarray(pairs.distance_km.values)[index],
            np.asarray(pairs[metric].values)[index],
            s=4, alpha=.08, color=color, rasterized=True,
        )
        radius = summary.radius_km.values
        median = summary[f"{prefix}_annular_median"].isel(time_window_end=0, y=yi, x=xi).values
        q25 = summary[f"{prefix}_annular_q25"].isel(time_window_end=0, y=yi, x=xi).values
        q75 = summary[f"{prefix}_annular_q75"].isel(time_window_end=0, y=yi, x=xi).values
        cumulative = summary[f"{prefix}_cumulative_median"].isel(time_window_end=0, y=yi, x=xi).values
        background = float(summary[f"{prefix}_background"].isel(time_window_end=0, y=yi, x=xi))
        estimated = float(summary[f"{prefix}_range_km"].isel(time_window_end=0, y=yi, x=xi))
        status_code = int(summary[f"{prefix}_range_status"].isel(time_window_end=0, y=yi, x=xi))
        ax.fill_between(radius, q25, q75, color=color, alpha=.22, label="Annular IQR")
        ax.plot(radius, median, color=color, lw=2.2, marker="o", ms=3.2, label="Annular median")
        ax.plot(radius, cumulative, color=INK, lw=1.8, ls="--", label="Cumulative median")
        ax.axhline(background, color=GOLD, lw=2, label="Distant background")
        if np.isfinite(estimated): ax.axvline(estimated, color=GREEN, lw=2.2, label=f"R* = {estimated:.0f} km")
        ax.axvline(500, color=MUTED, lw=1.5, ls=":", label="Discovery limit")
        status = "resolved" if status_code == 3 else "right-censored or unresolved"
        ax.set(xlabel="Physical distance (km)", ylabel="Spearman synchrony", xlim=(0, 505), ylim=(-.4, 1.03))
        ax.grid(alpha=.15); ax.legend(frameon=False, ncol=3, fontsize=8, loc="lower left")
        ax.set_title(f"Colorado mountains - {prefix} response: {status}", color=NAVY, weight="bold")
        result[key] = _save(fig, f"standalone_{key}.png")
    return result


class Report:
    def __init__(self, output: Path):
        output.parent.mkdir(parents=True, exist_ok=True)
        self.canvas = canvas.Canvas(str(output), pagesize=PAGE)
        self.canvas.setTitle("Empirical local synchrony range - bounded real-data pilot")
        self.canvas.setAuthor("CubeDynamics project")
        self.canvas.setSubject("Kernel-agnostic range estimator, sensitivity gate, and Colorado pilot")
        self.page_number = 0
        self.width, self.height = PAGE
        self.body_style = ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10.4, leading=14.2,
            textColor=colors.HexColor(INK), alignment=TA_LEFT,
        )
        self.caption_style = ParagraphStyle(
            "caption", fontName="Helvetica-Oblique", fontSize=8.3, leading=10.3,
            textColor=colors.HexColor(MUTED), alignment=TA_LEFT,
        )

    def _frame(self, title: str, kicker: str) -> None:
        self.page_number += 1
        c = self.canvas
        c.setFillColor(colors.HexColor(NAVY))
        c.setFont("Helvetica-Bold", 21)
        c.drawString(38, self.height - 46, title)
        c.setFillColor(colors.HexColor(MUTED))
        c.setFont("Helvetica", 8.7)
        c.drawString(39, self.height - 63, kicker.upper())
        c.setStrokeColor(colors.HexColor("#CCD7DF"))
        c.line(38, 34, self.width - 38, 34)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor(MUTED))
        c.drawString(38, 20, "CubeDynamics | empirical synchrony-range pilot | real PRISM data")
        page = f"{self.page_number} / 30"
        c.drawRightString(self.width - 38, 20, page)

    def page(
        self,
        title: str,
        kicker: str,
        body: str,
        *,
        image: Path | None = None,
        caption: str | None = None,
        table_data: list[list[str]] | None = None,
        image_height: float = 4.45 * inch,
    ) -> None:
        self._frame(title, kicker)
        c = self.canvas
        body_paragraph = Paragraph(body, self.body_style)
        body_width = self.width - 80
        _, body_height = body_paragraph.wrap(body_width, 90)
        body_y = self.height - 82 - body_height
        body_paragraph.drawOn(c, 40, body_y)
        content_top = body_y - 12
        if table_data is not None:
            table = Table(table_data, colWidths=[2.2 * inch, 4.9 * inch], repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("LEADING", (0, 0), (-1, -1), 10.5),
                        ("GRID", (0, 0), (-1, -1), .45, colors.HexColor("#CBD5DD")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(LIGHT)]),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 7),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            _, table_height = table.wrap(self.width - 80, content_top - 55)
            table.drawOn(c, 40, content_top - table_height)
        elif image is not None:
            available_height = min(image_height, content_top - 56)
            self._image(image, 40, 48, self.width - 80, available_height)
            if caption:
                paragraph = Paragraph(caption, self.caption_style)
                _, height = paragraph.wrap(self.width - 100, 34)
                paragraph.drawOn(c, 50, 42 + available_height - height)
        self.canvas.showPage()

    def cover(self) -> None:
        self.page_number += 1
        c = self.canvas
        c.setFillColor(colors.HexColor(NAVY))
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 28)
        c.drawString(48, self.height - 92, "Empirical local synchrony range")
        c.setFont("Helvetica", 17)
        c.drawString(50, self.height - 122, "Adaptive-range versus fixed 100 km synchrony")
        c.setFillColor(colors.HexColor(GOLD))
        c.roundRect(50, self.height - 225, 185, 58, 8, fill=1, stroke=0)
        c.setFillColor(colors.HexColor(INK))
        c.setFont("Helvetica-Bold", 25)
        c.drawCentredString(142.5, self.height - 204, "HOLD")
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(265, self.height - 182, "The method is implemented and validated,")
        c.drawString(265, self.height - 204, "but the real-data scale-up gate fails.")
        c.setFont("Helvetica", 11)
        lines = [
            "0 of 5 national representative pixels resolved a common range at 500 km / 20 km bins.",
            "1 of 25 Colorado pilot sites resolved a common cold/warm range.",
            "96% of Colorado common estimates were censored or unresolved.",
            "0 of 25 stabilized between 400 and 500 km.",
        ]
        y = self.height - 284
        for line in lines:
            c.setFillColor(colors.HexColor("#DDEAF3"))
            c.circle(58, y + 4, 3, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.drawString(70, y, line)
            y -= 27
        c.setStrokeColor(colors.HexColor("#6F96B7"))
        c.line(50, 92, self.width - 50, 92)
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#C9DCEB"))
        c.drawString(50, 68, "Real PRISM daily TMIN/TMAX | 2023-11-01 through 2024-01-30")
        c.drawRightString(self.width - 50, 68, "Kernel agnostic | no stacking | no distance weighting")
        c.setFont("Helvetica", 8)
        c.drawRightString(self.width - 38, 20, "1 / 30")
        self.canvas.showPage()

    def _image(self, path: Path, x: float, y: float, width: float, height: float) -> None:
        with PILImage.open(path) as image:
            ratio = min(width / image.width, height / image.height)
            draw_width = image.width * ratio
            draw_height = image.height * ratio
        self.canvas.drawImage(
            str(path),
            x + (width - draw_width) / 2,
            y + (height - draw_height) / 2,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask="auto",
        )

    def save(self) -> None:
        if self.page_number != 30:
            raise RuntimeError(f"Expected 30 pages, created {self.page_number}")
        self.canvas.save()


def main() -> None:
    required = [PILOT, BASE / "summary.json", BASE / "decision_gate.json"]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)
    assets = _build_assets()
    report = Report(OUTPUT)
    report.cover()
    report.page(
        "Existing fixed 100 km method", "1. Control",
        "The validated control calculates physical-distance pairs once, applies the established cold/warm tail-Spearman kernel, excludes self-pairs, and immediately collapses pairwise Delta to one focal-pixel value. This result is preserved unchanged.",
        image=assets["fixed_workflow"],
    )
    report.page(
        "Why test an adaptive range?", "2. Scientific question",
        "A uniform 100 km radius is a defensible control, but it may cross distinct terrain and climate regimes in one place while truncating coherent structure elsewhere. The experiment changes only which neighbors enter the same robust collapse.",
        image=assets["why_adaptive"],
    )
    report.page(
        "Start with one focal pixel", "3. Local scientific object",
        "Every estimate is focal-centered. Distance is measured in great-circle kilometers from the focal cell to eligible PRISM cells. Raster-cell counts and angular degrees are never treated as range units.",
        image=assets["pedagogy_0_0"], image_height=4.7*inch,
    )
    report.page(
        "Observe well beyond the candidate range", "4. Discovery support",
        "The pilot uses a 500 km discovery radius so the empirical curve has an opportunity to approach a distant background. Discovery support is an observation limit, not an inferred range; reaching it produces a censoring flag.",
        image=assets["pedagogy_0_2"], image_height=4.7*inch,
    )
    report.page(
        "Reuse every pair relationship", "5. Pair product",
        "One canonical 500 km pair table supplies the fixed 100 km control, annular summaries, cumulative summaries, background comparisons, adaptive reductions, and every sensitivity test. Cold uses lower-tail TMIN; warm uses strictly upper-tail TMAX; Delta_S = S_cold - S_warm.",
        image=assets["pedagogy_0_1"], image_height=4.7*inch,
    )
    report.page(
        "Real synchrony-distance responses", "6. Representative evidence",
        "Individual relationships remain visible as light points. The colored line is the annular median, the ribbon is its IQR, and the dashed line is the cumulative median. The curves are not forced to be monotonic or fitted to a parametric decay kernel.",
        image=FIGURES / "diagnostic_colorado_mountains.png", image_height=4.55*inch,
    )
    report.page(
        "Summarize physical annuli", "7. Empirical support",
        "The primary 20 km bins are wider than the roughly 4 km PRISM cells and contain ample relationships in the pilot. Counts are retained for every annulus. Unsupported bins cannot establish convergence.",
        image=assets["pedagogy_0_2"], image_height=4.7*inch,
    )
    report.page(
        "Annular and cumulative views answer different questions", "8. Two convergence tests",
        "Annular medians ask whether newly encountered neighbors still differ from the distant background. Cumulative medians ask whether extending the neighborhood still changes the final collapse. Both must stabilize for three consecutive supported annuli.",
        image=assets["mountain_0_0"], image_height=4.55*inch,
    )
    report.page(
        "Estimate a nonzero empirical background", "9. Background",
        "Broad-scale climate forcing can leave substantial synchrony at long distance. The method therefore estimates background rather than assuming zero. Outer annuli, smoothed outer annuli, and distant pairs are all retained and compared.",
        image=assets["background_summary"],
    )
    report.page(
        "Identify R* with persistence", "10. Deterministic criterion",
        "R* is the first supported annulus whose median is near background and whose cumulative median is stable for three consecutive bins, with a later-shell safeguard. Candidates at or beyond 80% of discovery support remain unresolved.",
        image=assets["pedagogy_1_0"], image_height=4.7*inch,
    )
    report.page(
        "Estimate cold range separately", "11. R*cold",
        "Cold range is inferred from joint lower-tail TMIN synchrony. In the mountain example the profile continues reorganizing with distance and is right-censored or unresolved at the primary setting.",
        image=assets["mountain_0_0"], image_height=4.55*inch,
    )
    report.page(
        "Estimate warm range separately", "12. R*warm",
        "Warm range is inferred independently from joint upper-tail TMAX synchrony. The mountain warm response resolves at 380 km for this setting, but a tail-specific result cannot by itself support primary adaptive Delta.",
        image=assets["mountain_1_0"], image_height=4.55*inch,
    )
    report.page(
        "Require a common neighbor set for Delta", "13. R*common",
        "Primary adaptive Delta is defined only when both tail ranges resolve. Then R*common = max(R*cold, R*warm), and cold, warm, and pairwise Delta are evaluated over exactly the same neighbors. Otherwise common range and adaptive Delta remain missing.",
        image=assets["status_summary"],
    )
    report.page(
        "Use range for selection, not weighting", "14. Adaptive neighborhood",
        "Pairs inside the resolved range are retained without distance weights; pairs outside are omitted. No exponential, Gaussian, power-law, or other kernel is imposed. The experiment isolates one change: neighborhood extent.",
        image=assets["pedagogy_1_1"], image_height=4.7*inch,
    )
    report.page(
        "Apply the same robust collapse", "15. One adaptive pixel",
        "The retained relationships are reduced with the existing exact median. Primary adaptive Delta is median[S_cold(i,j) - S_warm(i,j)] within R*common; it is not the difference between two separately ranged marginal medians.",
        image=assets["pedagogy_1_2"], image_height=4.7*inch,
    )
    report.page(
        "Repeat on a bounded Colorado pilot", "16. Spatial gate",
        "Twenty-five spatially balanced focal cells cover Colorado plains, foothills, mountains, and high elevation. They are a method gate, not a statewide raster, and use the full CONUS snapshot for complete 500 km land support.",
        image=assets["site_map"],
    )
    report.page(
        "The fixed control remains available everywhere", "17. Fixed products",
        "The validated statewide 100 km cold, warm, and Delta maps are unchanged. The fixed Delta uses red for negative/warm-stronger and blue for positive/cold-stronger.",
        image=assets["fixed_maps"], image_height=4.6*inch,
    )
    report.page(
        "Adaptive Delta exists only where common range resolves", "18. Adaptive product",
        "Only one of 25 pilot sites resolves both cold and warm ranges at the primary setting. Crosses mark unresolved sites. Filling those cells with 500 km would convert an observation boundary into a false scientific estimate.",
        image=assets["comparison_0_1"], image_height=4.65*inch,
    )
    report.page(
        "Adaptive minus fixed Delta", "19. Difference product",
        "With one resolved common range, Pearson, Spearman, RMSE, sign-change frequency, and threshold exceedance rates are not scientifically estimable. The requested comparison statistics are retained with an explicit insufficient-support status.",
        image=assets["comparison_1_1"], image_height=4.65*inch,
    )
    report.page(
        "Common synchrony-range map", "20. Primary range product",
        "R*common is shown only for the single site where both tail ranges resolve. The other 24 sites are censored or unresolved. This is the core reason a statewide product was not run.",
        image=assets["range_1_0"], image_height=4.65*inch,
    )
    report.page(
        "Cold range map", "21. Tail-specific range",
        "Nine of 25 pilot sites resolve a cold range, while the remainder are right-censored or unresolved. Tail-specific values are retained even when common range cannot be formed.",
        image=assets["range_0_0"], image_height=4.65*inch,
    )
    report.page(
        "Warm range map", "22. Tail-specific range",
        "Nine of 25 pilot sites resolve a warm range, but often at different locations from cold. This supports keeping cold and warm range as separate scientific dimensions.",
        image=assets["range_0_1"], image_height=4.65*inch,
    )
    report.page(
        "Cold-minus-warm range", "23. Delta_R is not Delta_S",
        "Delta_R = R*cold - R*warm can be calculated only where both ranges resolve. It measures spatial extent, not synchrony strength. The pilot provides too little common support for geographic interpretation.",
        image=assets["range_1_1"], image_height=4.65*inch,
    )
    report.page(
        "Uncertainty is part of the result", "24. Reliability and censoring",
        "The output retains a status code, boundary-censor flag, later-shell agreement, and reliability score. Reliability never overrides an unresolved status. Sector diagnostics also fail to establish scalar isotropy.",
        image=FIGURES / "colorado_reliability_censoring.png", image_height=4.55*inch,
    )
    report.page(
        "Discovery-radius and bin-width sensitivity", "25. Stability test",
        "Ten, 20, and 40 km bins were tested under 200, 300, 400, and 500 km discovery limits using the same 500 km pairs. Crosses denote unresolved results. No Colorado pilot site stabilized between 400 and 500 km at the primary bin width.",
        image=FIGURES / "representative_sensitivity.png", image_height=4.5*inch,
    )
    report.page(
        "Relationship with Delta IQR", "26. Existing QC",
        "Tail-specific resolved ranges can be plotted against fixed-radius relational heterogeneity, but common-range coverage is too sparse for a valid map-level association. The pilot therefore makes no claim about whether short or long range tracks high Delta IQR.",
        image=assets["qc_iqr"],
    )
    report.page(
        "Relationship with the reduction gap", "27. Existing QC",
        "The reduction gap measures non-commutativity between median pairwise Delta and the difference of marginal medians. It remains conceptually separate from empirical range, and the current pilot cannot establish a robust relationship.",
        image=assets["qc_gap"],
    )
    report.page(
        "What changed - and what did not", "28. Contract boundary",
        "The new work adds empirical distance-response summaries and a guarded neighbor-selection rule. It does not revise historical fixed-radius values, change cold/warm tail semantics, add a kernel weight, or reinterpret range as dispersal.",
        table_data=[
            ["Changed", "Unchanged"],
            ["Large discovery support", "Validated PRISM observations and pair kernel"],
            ["Annular plus cumulative summaries", "Cold <= TMIN median; warm > TMAX median"],
            ["Cold/warm/common R* statuses", "Delta_S = S_cold - S_warm"],
            ["Adaptive neighbor inclusion", "Exact median pairwise-Delta collapse"],
            ["Reliability and censoring", "No stacking, second convolution, or distance weights"],
        ],
    )
    report.page(
        "Decision: HOLD before full Colorado or CONUS", "30. Interpretation and next step",
        "The empirical curves are real and geographically structured, but the predeclared scalar range criterion is not identifiable or stable often enough to support adaptive production maps. The 25-site pilot evaluated 1.18 million nonself pairs; planning bounds reach 0.38-0.77 billion for Colorado and 11.35-22.69 billion for CONUS. No full Colorado or CONUS adaptive-range production run was performed. Reproduce with:<br/><br/><font name='Courier'>.venv/bin/python scripts/run_empirical_synchrony_range_pilot.py</font><br/><br/>Next: test a revised, predeclared empirical criterion or longer independent windows. Do not tune thresholds merely to increase map coverage.",
        table_data=[
            ["Gate", "Observed"],
            ["Common resolved >= 70%", "4% (1 of 25)"],
            ["Discovery-stable >= 70%", "0% (0 of 25)"],
            ["Representative resolved >= 4 of 5", "0 of 5"],
            ["Scale-up decision", "HOLD"],
        ],
    )
    report.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
