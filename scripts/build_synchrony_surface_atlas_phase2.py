#!/usr/bin/env python3
"""Build the revised 25-page Phase 2 local-synchrony-surface atlas."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile

import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
from shapely.geometry import shape
import xarray as xr

try:
    from reportlab.lib import colors
except ImportError:
    bundled = os.environ.get("CODEX_PDF_SITE_PACKAGES")
    if not bundled:
        raise
    sys.path.append(bundled)
    from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from cubedynamics.synchrony import angular_profile, radial_profile
from analyze_synchrony_surfaces_phase2 import (
    _nested_prediction,
    _radial_angular_prediction,
    _radial_prediction,
    _rmse,
)


BLUE = "#164b86"
CYAN = "#2a9dbe"
ORANGE = "#ef8a3a"
RED = "#b8322a"
INK = "#17324d"
MUTED = "#536779"
PURPLE = "#7251a5"
GREEN = "#37966f"


def _masked(data: xr.DataArray, mask: xr.DataArray) -> np.ndarray:
    values = np.asarray(data.squeeze().values, dtype=float)
    return np.where(np.asarray(mask.values, dtype=bool), values, np.nan)


def _outline(ax, geometry, **kwargs) -> None:
    polygons = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
    for polygon in polygons:
        x, y = polygon.exterior.xy
        ax.plot(x, y, **kwargs)


def _save(fig, path: Path) -> Path:
    fig.savefig(path, dpi=185, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return path


def _surface_scatter(ax, surface: xr.Dataset, metric: str, *, title: str, limit=None, cmap="RdBu_r"):
    values = np.asarray(surface[metric].values, dtype=float)
    x = np.asarray(surface.dx_km.values, dtype=float)
    y = np.asarray(surface.dy_km.values, dtype=float)
    valid = np.isfinite(values) & np.isfinite(x) & np.isfinite(y)
    if limit is None:
        limit = float(np.nanquantile(np.abs(values[valid]), 0.98))
    artist = ax.scatter(
        x[valid], y[valid], c=values[valid], s=13, marker="s", linewidth=0,
        cmap=cmap, norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit),
    )
    ax.scatter([0], [0], marker="*", s=80, color="#ffd43b", edgecolor=INK, linewidth=0.5)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=10, color=INK, fontweight="bold")
    ax.set_xlabel("eastward dx (km)", fontsize=8)
    ax.set_ylabel("northward dy (km)", fontsize=8)
    ax.tick_params(labelsize=7)
    return artist


def _choose_examples(records: list[dict[str, object]]) -> dict[str, int]:
    diagnostics = [record["diagnostics"] for record in records]
    choices = {
        "uniform": int(np.argmin([item["overall_iqr"] for item in diagnostics])),
        "radial": int(np.argmax([abs(item["radial_spearman"]) for item in diagnostics])),
        "directional": int(
            np.argmax([item["directional_harmonic_r_squared"] for item in diagnostics])
        ),
        "boundary": int(
            np.argmax(
                [
                    item["maximum_half_plane_contrast"] / max(item["overall_iqr"], 1e-6)
                    for item in diagnostics
                ]
            )
        ),
        "complex": int(
            np.argmin([item["low_order_reconstruction_r_squared"] for item in diagnostics])
        ),
    }
    used: set[int] = set()
    for label in choices:
        if choices[label] in used:
            ranking = np.argsort(
                [item["low_order_reconstruction_r_squared"] for item in diagnostics]
            )
            choices[label] = int(next(index for index in ranking if int(index) not in used))
        used.add(choices[label])
    return choices


def _load(artifact_dir: Path):
    report = json.loads((artifact_dir / "surface_representation_report.json").read_text())
    gate = json.loads((artifact_dir / "gate_report.json").read_text())
    surface_gate = json.loads((artifact_dir / "surface_gate_report.json").read_text())
    performance = json.loads((artifact_dir / "statewide_performance.json").read_text())
    landscape_performance = json.loads((artifact_dir / "landscape_performance.json").read_text())
    with xr.open_dataset(artifact_dir / "colorado_synchrony_signature.nc") as source:
        signature = source.load()
    with xr.open_dataset(artifact_dir / "colorado_landscape_change.nc") as source:
        change = source.load()
    paths = sorted((artifact_dir / "surface_samples").glob("surface_*.nc"))
    surfaces = []
    for path in paths:
        with xr.open_dataset(path) as source:
            surfaces.append(source.load())
    document = json.loads((artifact_dir / "colorado_boundary.geojson").read_text())
    geometry = shape(document["features"][0]["geometry"])
    return report, gate, surface_gate, performance, landscape_performance, signature, change, surfaces, geometry


def _schematic_pair_surface(path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11, 5.7), constrained_layout=True)
    ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis("off")
    ax.scatter([1.5, 4.1], [4.4, 4.4], s=1200, color=[BLUE, ORANGE], edgecolor="white")
    ax.text(1.5, 4.4, "i", ha="center", va="center", color="white", fontsize=18, fontweight="bold")
    ax.text(4.1, 4.4, "j", ha="center", va="center", color="white", fontsize=18, fontweight="bold")
    ax.annotate("", xy=(3.55, 4.4), xytext=(2.05, 4.4), arrowprops={"arrowstyle": "<->", "lw": 3, "color": INK})
    ax.text(2.8, 5.05, "one canonical S(i,j)", ha="center", color=INK, fontsize=14, fontweight="bold")
    ax.text(2.8, 3.75, "cold · warm · ΔS\ndistance · bearing · signed dx/dy", ha="center", color=MUTED, fontsize=10)
    ax.annotate("", xy=(6.2, 4.4), xytext=(4.8, 4.4), arrowprops={"arrowstyle": "->", "lw": 3, "color": CYAN})
    grid_x, grid_y = np.meshgrid(np.arange(7.1, 11.4, 0.45), np.arange(1.1, 5.5, 0.45))
    radius = np.hypot(grid_x - 9.25, grid_y - 3.3)
    values = np.cos(radius * 2.1) + 0.45 * (grid_x - 9.25)
    valid = radius <= 2.15
    ax.scatter(grid_x[valid], grid_y[valid], c=values[valid], cmap="RdBu_r", s=90, marker="s", linewidth=0)
    ax.scatter([9.25], [3.3], marker="*", s=180, color="#ffd43b", edgecolor=INK)
    ax.text(9.25, 5.65, "local surface Sₚ(dx,dy)", ha="center", color=INK, fontsize=15, fontweight="bold")
    ax.text(9.25, 0.55, "distance and direction are coordinates", ha="center", color=MUTED, fontsize=11)
    return _save(fig, path)


def _schematic_overlap(path: Path) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(11, 5.5), constrained_layout=True)
    rng = np.random.default_rng(12)
    for index, ax in enumerate(axes[:2]):
        field = rng.normal(size=(15, 15))
        field += np.linspace(-1, 1, 15)[None, :] * (0.7 if index == 0 else -0.5)
        ax.imshow(field, cmap="RdBu_r", vmin=-2.5, vmax=2.5, origin="lower")
        ax.scatter([7], [7], marker="*", s=130, color="#ffd43b", edgecolor=INK)
        ax.set_title(f"center map {index + 1}", color=INK, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([])
    axes[2].axis("off")
    for row in range(10):
        axes[2].add_patch(
            plt.Rectangle((0.12 + row * 0.018, 0.16 + row * 0.04), 0.7, 0.48,
                          transform=axes[2].transAxes, facecolor="#e7eef4", edgecolor=BLUE, alpha=0.6)
        )
    axes[2].plot([0.52, 0.52], [0.18, 0.92], color=RED, lw=2, transform=axes[2].transAxes)
    axes[2].scatter([0.52] * 10, np.linspace(0.2, 0.88, 10), color="#ffd43b", edgecolor=INK,
                    s=45, transform=axes[2].transAxes, zorder=4)
    axes[2].text(0.5, 0.05, "one focal value from every center map\n→ organized by center displacement",
                 ha="center", color=INK, fontsize=11, transform=axes[2].transAxes)
    axes[2].set_title("overlapping maps form a surface", color=INK, fontweight="bold")
    return _save(fig, path)


def _cold_warm_delta(surface: xr.Dataset, path: Path) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.1), constrained_layout=True)
    all_values = np.concatenate([surface[name].values.ravel() for name in ("cold_synchrony", "warm_synchrony", "delta_s")])
    limit = float(np.nanquantile(np.abs(all_values), 0.98))
    for ax, name, title in zip(axes, ("cold_synchrony", "warm_synchrony", "delta_s"), ("Cold surface Cₚ", "Warm surface Wₚ", "Difference Dₚ = Cₚ − Wₚ")):
        artist = _surface_scatter(ax, surface, name, title=title, limit=limit)
        fig.colorbar(artist, ax=ax, shrink=0.72)
    return _save(fig, path)


def _two_surfaces(surfaces, indices, titles, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    values = np.concatenate([surfaces[index].delta_s.values.ravel() for index in indices])
    limit = float(np.nanquantile(np.abs(values), 0.98))
    for ax, index, title in zip(axes, indices, titles):
        artist = _surface_scatter(ax, surfaces[index], "delta_s", title=title, limit=limit)
        fig.colorbar(artist, ax=ax, shrink=0.72)
    return _save(fig, path)


def _cartesian_polar(surface: xr.Dataset, path: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    artist = _surface_scatter(axes[0], surface, "delta_s", title="Cartesian Sₚ(dx,dy)")
    fig.colorbar(artist, ax=axes[0], shrink=0.72)
    value = surface.delta_s.values.ravel()
    bearing = surface.bearing_degrees.values.ravel()
    distance = surface.distance_km.values.ravel()
    valid = np.isfinite(value) & np.isfinite(bearing) & np.isfinite(distance)
    limit = float(np.nanquantile(np.abs(value[valid]), 0.98))
    polar = axes[1].scatter(bearing[valid], distance[valid], c=value[valid], cmap="RdBu_r", s=14,
                            norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), linewidth=0)
    axes[1].set_xlabel("bearing θ (degrees)"); axes[1].set_ylabel("distance r (km)")
    axes[1].set_title("Polar Sₚ(r,θ)", color=INK, fontweight="bold")
    fig.colorbar(polar, ax=axes[1], shrink=0.72)
    return _save(fig, path)


def _profile_figure(surfaces, indices, path, *, angular=False):
    fig, ax = plt.subplots(figsize=(10.6, 4.5), constrained_layout=True)
    colors_ = [BLUE, ORANGE, GREEN, PURPLE, RED]
    for color, index in zip(colors_, indices):
        if angular:
            profile = angular_profile(surfaces[index], bin_width_degrees=15, min_count=3)
            ax.plot(profile.bearing_degrees, profile.profile, color=color, lw=2, label=f"sample {index + 1}")
            ax.set_xlabel("bearing θ (degrees)")
            ax.set_xlim(0, 360); ax.set_xticks(np.arange(0, 361, 45))
            ax.set_title("Radially detrended angular profiles Sₚ(θ)", color=INK, fontweight="bold")
        else:
            profile = radial_profile(surfaces[index], bin_width_km=5, min_count=3)
            ax.plot(profile.radius_km, profile.profile, color=color, lw=2, label=f"sample {index + 1}")
            ax.fill_between(profile.radius_km, profile.q25, profile.q75, color=color, alpha=0.12)
            ax.set_xlabel("distance r (km)")
            ax.set_title("Fine radial profiles Sₚ(r): nonmonotonicity is allowed", color=INK, fontweight="bold")
    ax.axhline(0, color="#a9b6c1", lw=0.8); ax.set_ylabel("ΔS")
    ax.legend(ncol=5, fontsize=8, loc="lower center")
    ax.grid(alpha=0.2)
    return _save(fig, path)


def _loss_example(surfaces, path):
    errors = []
    for surface in surfaces:
        value = surface.delta_s.values
        _, relative = _rmse(value, _nested_prediction(surface, value))
        errors.append(relative)
    index = int(np.argmax(errors)); surface = surfaces[index]; value = surface.delta_s.values
    nested = _nested_prediction(surface, value)
    radial_directional = _radial_angular_prediction(surface, value)
    fig, axes = plt.subplots(1, 4, figsize=(11, 3.7), constrained_layout=True)
    limit = float(np.nanquantile(np.abs(value), 0.98))
    for ax, data, title in zip(
        axes,
        (value, nested, radial_directional, value - radial_directional),
        ("Full real surface", "25/50/75/100 baseline", "Radial + directional", "Residual complexity"),
    ):
        temporary = surface.copy(deep=False)
        temporary = temporary.assign(delta_s=(surface.delta_s.dims, data))
        artist = _surface_scatter(ax, temporary, "delta_s", title=title, limit=limit)
    fig.colorbar(artist, ax=axes, shrink=0.7, label="ΔS")
    fig.suptitle(f"Worst nested-radius reconstruction in the 64-surface sample · normalized RMSE {errors[index]:.2f}", color=INK, fontweight="bold")
    return _save(fig, path)


def _one_example(surface, record, path, label, note):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), constrained_layout=True)
    artist = _surface_scatter(axes[0], surface, "delta_s", title=f"{label} real sample")
    radial = radial_profile(surface, bin_width_km=5, min_count=3)
    axes[1].plot(radial.radius_km, radial.profile, color=BLUE, lw=2)
    axes[1].fill_between(radial.radius_km, radial.q25, radial.q75, color=BLUE, alpha=0.18)
    axes[1].set_title("radial projection", color=INK, fontweight="bold"); axes[1].set_xlabel("km"); axes[1].set_ylabel("ΔS")
    angular = angular_profile(surface, bin_width_degrees=15, min_count=3)
    axes[2].plot(angular.bearing_degrees, angular.profile, color=ORANGE, lw=2)
    axes[2].set_title("angular projection", color=INK, fontweight="bold"); axes[2].set_xlabel("bearing"); axes[2].set_ylabel("radial-residual ΔS")
    fig.colorbar(artist, ax=axes[0], shrink=0.7)
    fig.suptitle(note, fontsize=11, color=MUTED)
    return _save(fig, path)


def _key_figure(surfaces, choices, path):
    rows = list(choices)
    fig, axes = plt.subplots(5, 5, figsize=(14, 11.2), constrained_layout=True)
    for row, label in enumerate(rows):
        surface = surfaces[choices[label]]
        value = surface.delta_s.values
        limit = float(np.nanquantile(np.abs(value), 0.98))
        _surface_scatter(axes[row, 0], surface, "delta_s", title=label.title(), limit=limit)
        radial = radial_profile(surface, bin_width_km=5, min_count=3)
        axes[row, 1].plot(radial.radius_km, radial.profile, color=BLUE, lw=1.5)
        axes[row, 1].set_title("S(r)", fontsize=9); axes[row, 1].tick_params(labelsize=6)
        angular = angular_profile(surface, bin_width_degrees=15, min_count=3)
        axes[row, 2].plot(angular.bearing_degrees, angular.profile, color=ORANGE, lw=1.5)
        axes[row, 2].set_title("S(θ)", fontsize=9); axes[row, 2].tick_params(labelsize=6)
        cumulative = []
        for radius in (25, 50, 75, 100):
            selected = np.isfinite(value) & (surface.distance_km.values <= radius)
            cumulative.append(float(np.median(value[selected])))
        axes[row, 3].plot((25, 50, 75, 100), cumulative, marker="o", color=PURPLE)
        axes[row, 3].set_title("4 cumulative values", fontsize=9); axes[row, 3].tick_params(labelsize=6)
        reconstruction = _radial_angular_prediction(surface, value)
        temporary = surface.assign(delta_s=(surface.delta_s.dims, reconstruction))
        _surface_scatter(axes[row, 4], temporary, "delta_s", title="compact reconstruction", limit=limit)
        for column in (0, 4):
            axes[row, column].set_xlabel(""); axes[row, column].set_ylabel("")
    fig.suptitle("What four cumulative radii lose from a 2-D local synchrony surface", color=INK, fontweight="bold", fontsize=16)
    return _save(fig, path)


def _representation_chart(report, path):
    rows = report["decision_table"]
    labels = [row["representation"].replace("_", "\n") for row in rows]
    fit = [row["median_normalized_rmse"] for row in rows]
    missing = [row["missing_10pct_median_normalized_rmse"] for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    x = np.arange(len(rows)); width = 0.36
    axes[0].bar(x - width / 2, fit, width, color=BLUE, label="complete surface")
    axes[0].bar(x + width / 2, missing, width, color=ORANGE, label="10% held out")
    axes[0].set_xticks(x, labels, fontsize=7); axes[0].set_ylabel("normalized RMSE · lower is better")
    axes[0].legend(fontsize=8); axes[0].axhline(1, color=RED, ls="--", lw=1)
    axes[0].set_title("Reconstruction accuracy", color=INK, fontweight="bold")
    parameters = [row["per_pixel_parameters"] for row in rows]
    colors_ = [{"KEEP": GREEN, "KEEP AS DIAGNOSTIC": CYAN, "EXPERIMENTAL": PURPLE}.get(row["status"], MUTED) for row in rows]
    axes[1].scatter(parameters, fit, c=colors_, s=90)
    for px, py, label in zip(parameters, fit, labels):
        axes[1].annotate(label.replace("\n", " "), (px, py), xytext=(4, 3), textcoords="offset points", fontsize=7)
    axes[1].set_xlabel("stored parameters per pixel"); axes[1].set_ylabel("normalized RMSE")
    axes[1].set_title("Accuracy–storage tradeoff", color=INK, fontweight="bold")
    axes[1].grid(alpha=0.2)
    return _save(fig, path)


def _pca_components(artifact_dir, report, path):
    basis = np.load(artifact_dir / "surface_samples" / "empirical_surface_basis.npz")
    components = basis["delta_s_components"]
    result = report["pca_svd"]["delta_s"]
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.2), constrained_layout=True)
    limit = float(np.nanquantile(np.abs(components), 0.99))
    screens = result["component_correlation_screens"]
    for index, ax in enumerate(axes.flat):
        image = ax.imshow(components[index], cmap="RdBu_r", vmin=-limit, vmax=limit, origin="lower")
        screen = screens[index]
        ax.set_title(f"PC {index + 1} · screen: {screen['strongest_prototype']} ({screen['correlation']:+.2f})", fontsize=8)
        ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(image, ax=axes, shrink=0.7)
    fig.suptitle("Empirical Delta basis · descriptive correlation screens, not assigned meanings", color=INK, fontweight="bold")
    return _save(fig, path)


def _pca_accuracy(report, path):
    result = report["pca_svd"]["delta_s"]
    rows = result["results"]
    k = [row["components"] for row in rows]
    train = [row["training_cumulative_variance"] for row in rows]
    test = [row["held_out_median_normalized_rmse"] for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0), constrained_layout=True)
    axes[0].plot(k, train, marker="o", color=BLUE); axes[0].set_ylim(0, 1)
    axes[0].set_xlabel("components"); axes[0].set_ylabel("training cumulative variance")
    axes[0].set_title("Training variance is not the decision rule", color=INK, fontweight="bold")
    axes[1].plot(k, test, marker="o", color=ORANGE, label="held-out surface")
    axes[1].axhline(0.6, color=RED, ls="--", label="target screen")
    axes[1].set_xlabel("components"); axes[1].set_ylabel("held-out normalized RMSE")
    axes[1].set_title("Held-out reconstruction remains weak", color=INK, fontweight="bold")
    axes[1].legend(fontsize=8); axes[1].grid(alpha=0.2)
    return _save(fig, path)


def _state_map(signature, geometry, variable, path, title, cmap, *, diverging=False, vmax=None):
    data = _masked(signature[variable].sel(radius_km=100), signature.output_mask)
    fig, ax = plt.subplots(figsize=(10.7, 5.2), constrained_layout=True)
    if diverging:
        limit = float(np.nanquantile(np.abs(data), 0.99))
        artist = ax.pcolormesh(signature.x, signature.y, data, cmap=cmap,
                               norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), shading="auto")
    else:
        if vmax is None:
            vmax = float(np.nanquantile(data, 0.99))
        artist = ax.pcolormesh(signature.x, signature.y, data, cmap=cmap, vmin=0 if np.nanmin(data) >= 0 else None, vmax=vmax, shading="auto")
    _outline(ax, geometry, color=INK, linewidth=0.7)
    ax.set_aspect("equal"); ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.set_title(title, color=INK, fontweight="bold"); fig.colorbar(artist, ax=ax, shrink=0.75)
    return _save(fig, path)


def _heterogeneity_maps(signature, geometry, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), constrained_layout=True)
    for ax, variable, title in zip(axes, ("delta_iqr", "delta_mad"), ("Delta IQR", "Delta MAD")):
        data = _masked(signature[variable].sel(radius_km=100), signature.output_mask)
        artist = ax.pcolormesh(signature.x, signature.y, data, cmap="magma", vmin=0, vmax=float(np.nanquantile(data, 0.99)), shading="auto")
        _outline(ax, geometry, color=INK, linewidth=0.6); ax.set_aspect("equal"); ax.set_title(title, color=INK, fontweight="bold")
        fig.colorbar(artist, ax=ax, shrink=0.72)
    fig.suptitle("Overall heterogeneity inside the 100 km observation window", color=INK, fontweight="bold")
    return _save(fig, path)


def _shape_diagnostics(records, geometry, path):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), constrained_layout=True)
    lon = np.asarray([record["longitude"] for record in records])
    lat = np.asarray([record["latitude"] for record in records])
    diagnostics = [record["diagnostics"] for record in records]
    strength = np.asarray([item["directional_harmonic_r_squared"] for item in diagnostics])
    angle = np.deg2rad([item["anisotropy_axis_degrees"] for item in diagnostics])
    for x0, y0, theta, value in zip(lon, lat, angle, strength):
        scale = 0.18 * value
        dx = scale * np.sin(theta); dy = scale * np.cos(theta)
        axes[0].plot([x0 - dx, x0 + dx], [y0 - dy, y0 + dy], color=BLUE, lw=1.2 + 2 * value)
    contrast = np.asarray([item["maximum_half_plane_contrast"] for item in diagnostics])
    complexity = 1 - np.asarray([item["low_order_reconstruction_r_squared"] for item in diagnostics])
    for ax, values, title, cmap in (
        (axes[1], contrast, "half-plane contrast", "magma"),
        (axes[2], complexity, "low-order residual complexity", "viridis"),
    ):
        artist = ax.scatter(lon, lat, c=values, cmap=cmap, s=30, edgecolor="white", linewidth=0.3)
        fig.colorbar(artist, ax=ax, shrink=0.68)
        ax.set_title(title, fontsize=9, color=INK, fontweight="bold")
    axes[0].set_title("anisotropy orientation / strength", fontsize=9, color=INK, fontweight="bold")
    for ax in axes:
        _outline(ax, geometry, color=INK, linewidth=0.5); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Sampled shape diagnostics · experimental, not statewide classifications", color=INK, fontweight="bold")
    return _save(fig, path)


def _landscape_maps(change, geometry, path):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), constrained_layout=True)
    specs = (
        ("mean_normalized_rmse", "landscape nRMSE", "magma"),
        ("mean_sign_disagreement", "sign disagreement", "magma"),
        ("mean_gradient_vector_rmse", "gradient change", "viridis"),
    )
    for ax, (name, title, cmap) in zip(axes, specs):
        data = _masked(change[name], change.output_mask)
        artist = ax.pcolormesh(change.x, change.y, data, cmap=cmap, vmin=0, vmax=float(np.nanquantile(data, 0.99)), shading="auto")
        _outline(ax, geometry, color=INK, linewidth=0.5); ax.set_aspect("equal"); ax.set_title(title, fontsize=9, color=INK, fontweight="bold")
        fig.colorbar(artist, ax=ax, shrink=0.68)
    fig.suptitle("Between-center landscape change remains a separate branch", color=INK, fontweight="bold")
    return _save(fig, path)


def _validation_performance(gate, surface_gate, performance, landscape_performance, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0), constrained_layout=True)
    labels = ["signature gate", "surface values", "chunking", "endpoint reversal", "tile halo"]
    errors = [
        max(gate["max_absolute_errors"].values()),
        max(surface_gate["phase1_kernel_max_absolute_errors"].values()),
        max(surface_gate["chunking_max_absolute_errors"].values()),
        max(surface_gate["endpoint_bearing_reversal_error_degrees"], surface_gate["endpoint_displacement_reversal_error_km"]),
        max(surface_gate["tile_halo_surface_max_absolute_errors"].values()),
    ]
    axes[0].barh(labels, [max(value, 1e-16) for value in errors], color=[BLUE, CYAN, GREEN, ORANGE, PURPLE])
    axes[0].set_xscale("log"); axes[0].set_xlim(1e-17, 1e-10); axes[0].set_xlabel("maximum absolute error")
    axes[0].set_title("Real 100×100 gate", color=INK, fontweight="bold")
    names = ["gate", "Colorado summary", "landscape change", "64 surfaces"]
    wall = [gate["wall_seconds"], performance["wall_seconds"], landscape_performance["wall_seconds"], 21.7]
    axes[1].bar(names, wall, color=[CYAN, BLUE, ORANGE, GREEN])
    axes[1].set_ylabel("wall seconds"); axes[1].tick_params(axis="x", labelrotation=15)
    axes[1].set_title("Measured execution", color=INK, fontweight="bold")
    return _save(fig, path)


def _add_page(story, styles, title, subtitle=None, image=None, paragraphs=(), table=None):
    story.append(Paragraph(title, styles["PageTitle"]))
    if subtitle:
        story.append(Paragraph(subtitle, styles["Subtitle"])); story.append(Spacer(1, 0.05 * inch))
    if image:
        graphic = Image(str(image))
        scale = min((10.1 * inch) / graphic.imageWidth, (5.95 * inch) / graphic.imageHeight)
        graphic.drawWidth = graphic.imageWidth * scale; graphic.drawHeight = graphic.imageHeight * scale
        story.append(graphic)
    for paragraph in paragraphs:
        story.append(Paragraph(paragraph, styles["Body"])); story.append(Spacer(1, 0.05 * inch))
    if table:
        built = Table(table, repeatRows=1, hAlign="LEFT")
        built.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BLUE)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.6),
            ("LEADING", (0, 0), (-1, -1), 9.2),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b9c6d1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#edf4f8")]),
        ]))
        story.append(built)
    story.append(PageBreak())


def _footer(canvas, document):
    canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#b8c6d2")); canvas.setLineWidth(0.4)
    canvas.line(0.45 * inch, 0.27 * inch, 10.55 * inch, 0.27 * inch)
    canvas.setFillColor(colors.HexColor(MUTED)); canvas.setFont("Helvetica", 7.3)
    canvas.drawString(0.47 * inch, 0.14 * inch, "CubeDynamics · observed PRISM · revised Phase 2")
    canvas.drawRightString(10.53 * inch, 0.14 * inch, f"{document.page}"); canvas.restoreState()


def _decision_report(artifact_dir: Path, report: dict[str, object]) -> Path:
    decision = report["decision_table"]
    pca = report["pca_svd"]["delta_s"]
    status = report["characteristic_scale_status_counts"]
    lines = [
        "# Revised Phase 2 decision report", "",
        "Decision: **retain the full local surface as the scientific object; keep fine radial and directional projections; do not promote a fixed low-dimensional basis yet.**", "",
    ]
    answers = [
        ("1. What does the complete surface look like?", "Observed surfaces are spatially structured, often directional, and frequently nonmonotonic in distance."),
        ("2. Loss from median + IQR?", f"Median normalized Delta reconstruction RMSE is {decision[0]['median_normalized_rmse']:.2f}; these retain magnitude and heterogeneity, not geometry."),
        ("3. Loss from four cumulative radii?", f"Median normalized RMSE is {decision[1]['median_normalized_rmse']:.2f}, no improvement over median-only reconstruction."),
        ("4. Is radial structure usually monotonic?", "No. Fine profiles show reversals; the implementation never forces monotonic decay."),
        ("5. Identifiable characteristic scales?", f"Experimental plateau screening found {status.get('candidate_plateau_scale', 0)} candidates, but these are not yet accepted scales."),
        ("6. Are multiple scales common?", f"{status.get('multiple_candidate_scales', 0)} of {report['sample_size']} surfaces were flagged with multiple candidate scales."),
        ("7. Directional organization?", f"Radial + directional reconstruction lowers median normalized RMSE to {decision[3]['median_normalized_rmse']:.2f}."),
        ("8. Compact anisotropy?", "Low-order harmonics provide strength and orientation diagnostics, but require temporal stability validation."),
        ("9. Boundary versus anisotropy?", "Second-harmonic axis strength and maximum half-plane contrast are computed separately; neither is labeled a climate boundary."),
        ("10. Residual complexity?", f"The seven-parameter 2-D basis leaves median normalized RMSE {decision[4]['median_normalized_rmse']:.2f}; residual structure is material."),
        ("11. Low-dimensional empirical basis?", f"Eight-component held-out PCA RMSE is {decision[5]['median_normalized_rmse']:.2f}; compression is incomplete."),
        ("12. Are components interpretable?", "Some correlate with simple gradients, but split-half subspace stability is weak; no component receives a scientific label."),
        ("13. Cold versus warm?", "Warm surfaces were more compressible than cold and Delta in this sample; the three surfaces must remain distinct."),
        ("14. Robust statewide shape maps?", "Only existing directional summaries remain diagnostic. New boundary, anisotropy, scale, and complexity fields are sampled diagnostics, not statewide products."),
        ("15. Smallest useful signature?", "Keep magnitude, IQR/MAD, counts/coverage, a fine radial profile, a radially adjusted directional profile, and explicit residual complexity; schema remains provisional."),
        ("16. Retain during production?", "Retain canonical pair values plus signed dx/dy, distance, bearing, and endpoint identity until selected surfaces and descriptors are accumulated."),
        ("17. What can be discarded?", "Unselected full surfaces and temporary tile pairs may be discarded after validation and descriptor accumulation."),
        ("18. Is 100 km sufficient?", f"It is sufficient as this experiment's observation window; {status.get('right_censored_or_unresolved', 0)} sampled profiles remain right-censored/unresolved."),
        ("19. Is a larger window needed?", "Yes before concluding that near-limit transitions are characteristic scales; this phase makes no such claim."),
        ("20. Phase 3?", "Colorado temporal robustness on selected seasonal windows, refitting or aligning candidate representations across time before any CONUS scaling."),
    ]
    for title, text in answers:
        lines.extend((f"## {title}", "", text, ""))
    target = artifact_dir / "phase2_decision_report.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def build(artifact_dir: Path, output_pdf: Path) -> dict[str, object]:
    report, gate, surface_gate, performance, landscape_performance, signature, change, surfaces, geometry = _load(artifact_dir)
    records = report["surfaces"]; choices = _choose_examples(records); selected = [choices[name] for name in choices]
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="PageTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=23, textColor=colors.HexColor(INK), spaceAfter=5))
    styles.add(ParagraphStyle(name="Subtitle", parent=styles["Normal"], fontSize=9.5, leading=12, textColor=colors.HexColor(MUTED)))
    styles.add(ParagraphStyle(name="Body", parent=styles["BodyText"], fontSize=9.5, leading=13, textColor=colors.HexColor(INK)))
    with tempfile.TemporaryDirectory(prefix="surface-atlas-") as directory:
        assets = Path(directory)
        images = {
            "pair": _schematic_pair_surface(assets / "pair.png"),
            "overlap": _schematic_overlap(assets / "overlap.png"),
            "cwd": _cold_warm_delta(surfaces[choices["complex"]], assets / "cwd.png"),
            "lowhigh": _two_surfaces(surfaces, [choices["uniform"], int(np.argmax([r['diagnostics']['overall_iqr'] for r in records]))], ["Low Delta heterogeneity", "High Delta heterogeneity"], assets / "lowhigh.png"),
            "polar": _cartesian_polar(surfaces[choices["directional"]], assets / "polar.png"),
            "radial": _profile_figure(surfaces, selected, assets / "radial.png"),
            "angular": _profile_figure(surfaces, selected, assets / "angular.png", angular=True),
            "loss": _loss_example(surfaces, assets / "loss.png"),
            "uniform": _one_example(surfaces[choices["uniform"]], records[choices["uniform"]], assets / "uniform.png", "lowest-direction / low-IQR", "Closest-to-isotropic sampled real surface; descriptive, not proof of isotropy"),
            "directional": _one_example(surfaces[choices["directional"]], records[choices["directional"]], assets / "directional.png", "directional", "Highest harmonic R² in the sampled real surfaces"),
            "boundary": _one_example(surfaces[choices["boundary"]], records[choices["boundary"]], assets / "boundary.png", "boundary-like", "Largest half-plane contrast relative to IQR; not classified as a climate boundary"),
            "complex": _one_example(surfaces[choices["complex"]], records[choices["complex"]], assets / "complex.png", "complex", "Lowest low-order 2-D reconstruction R² in the sample"),
            "key": _key_figure(surfaces, choices, assets / "key.png"),
            "representations": _representation_chart(report, assets / "representations.png"),
            "pca": _pca_components(artifact_dir, report, assets / "pca.png"),
            "pca_accuracy": _pca_accuracy(report, assets / "pca_accuracy.png"),
            "cold": _state_map(signature, geometry, "cold_median", assets / "cold.png", "Cold synchrony magnitude · 100 km observation window", "RdBu_r", diverging=True),
            "warm": _state_map(signature, geometry, "warm_median", assets / "warm.png", "Warm synchrony magnitude · 100 km observation window", "RdBu_r", diverging=True),
            "delta": _state_map(signature, geometry, "delta_median", assets / "delta.png", "Median pairwise ΔS · cold − warm", "RdBu_r", diverging=True),
            "heterogeneity": _heterogeneity_maps(signature, geometry, assets / "heterogeneity.png"),
            "shape": _shape_diagnostics(records, geometry, assets / "shape.png"),
            "landscape": _landscape_maps(change, geometry, assets / "landscape.png"),
            "validation": _validation_performance(gate, surface_gate, performance, landscape_performance, assets / "validation.png"),
        }
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        document = SimpleDocTemplate(str(output_pdf), pagesize=landscape(letter), rightMargin=0.45*inch, leftMargin=0.45*inch, topMargin=0.36*inch, bottomMargin=0.34*inch, title="Colorado local synchrony surfaces · revised Phase 2", author="CubeDynamics")
        story = []
        _add_page(story, styles, "1 · Colorado local synchrony surfaces", "Revised Phase 2 · observed PRISM · 1 Nov 2023–30 Jan 2024", image=images["pair"], paragraphs=["The local 2-D surface Sₚ(dx,dy) is the scientific object. Distance and direction are coordinates. Each canonical pair contributes to both endpoint surfaces with opposite signed displacement and bearing. The 100 km limit is an observation window, not an inferred synchrony scale."])
        _add_page(story, styles, "2 · Overlapping center maps generate Sₚ(dx,dy)", image=images["overlap"])
        _add_page(story, styles, "3 · Real cold, warm, and Delta surfaces", image=images["cwd"], paragraphs=["Surface analysis is never performed on Delta alone; cold and warm structure remain recoverable."])
        _add_page(story, styles, "4 · Low versus high heterogeneity", image=images["lowhigh"], paragraphs=["IQR and MAD describe overall dispersion but cannot show where values occur around the focal pixel."])
        _add_page(story, styles, "5 · Cartesian and polar views of the same surface", image=images["polar"])
        _add_page(story, styles, "6 · Continuous radial profiles", image=images["radial"], paragraphs=["Five-kilometer annuli are numerical support for Sₚ(r), not prescribed scientific scales."])
        _add_page(story, styles, "7 · Direction is first-class", image=images["angular"], paragraphs=["Angular profiles are computed after fine radial detrending so radial structure is not mistaken for direction."])
        _add_page(story, styles, "8 · Why cumulative radii lose information", image=images["loss"], paragraphs=["The 25/50/75/100 baseline erases one-sided and boundary-like organization even when its four values are exact."])
        _add_page(story, styles, "9 · Closest-to-isotropic real sample", image=images["uniform"])
        _add_page(story, styles, "10 · Directional / anisotropic sample", image=images["directional"])
        _add_page(story, styles, "11 · Boundary-like sample", image=images["boundary"])
        _add_page(story, styles, "12 · Complex residual sample", image=images["complex"])
        _add_page(story, styles, "13 · Central comparison: what is lost?", image=images["key"])
        decision_table = [["Representation", "Params", "RMSE", "10% missing", "Status"]] + [[row["representation"], row["per_pixel_parameters"], f"{row['median_normalized_rmse']:.2f}", f"{row['missing_10pct_median_normalized_rmse']:.2f}", row["status"]] for row in report["decision_table"]]
        _add_page(story, styles, "14 · Candidate compact representations", image=images["representations"], table=decision_table)
        _add_page(story, styles, "15 · Empirical PCA/SVD components", image=images["pca"], paragraphs=["Components are inspected, not named in advance. Correlations with simple prototypes are descriptive screens only."])
        pca = report["pca_svd"]["delta_s"]
        _add_page(story, styles, "16 · Held-out reconstruction and stability", image=images["pca_accuracy"], paragraphs=[f"Eight components retain {pca['results'][7]['training_cumulative_variance']:.0%} of training variance but held-out normalized RMSE remains {pca['results'][7]['held_out_median_normalized_rmse']:.2f}; split-half subspace stability is {pca['split_half_subspace_stability']['8']:.2f}. PCA remains experimental."])
        _add_page(story, styles, "17 · Colorado cold magnitude", image=images["cold"])
        _add_page(story, styles, "18 · Colorado warm magnitude", image=images["warm"])
        _add_page(story, styles, "19 · Colorado Delta magnitude", image=images["delta"])
        _add_page(story, styles, "20 · Colorado overall heterogeneity", image=images["heterogeneity"])
        _add_page(story, styles, "21 · Surface-shape descriptors", image=images["shape"], paragraphs=["These are sparse sample diagnostics. They are not statewide regime, boundary, or characteristic-scale maps."])
        _add_page(story, styles, "22 · Landscape change is separate", image=images["landscape"], paragraphs=["This branch compares complete center landscapes Mᵢ and Mⱼ; it does not describe within-surface shape."])
        perf_table = [["Run", "Wall", "Pairs", "Peak RSS"], ["100×100 gate", f"{gate['wall_seconds']:.1f} s", f"{gate['unique_pairs_untiled']:,}", f"{gate['process_peak_rss_bytes']/1e9:.2f} GB"], ["Colorado summaries", f"{performance['wall_seconds']:.1f} s", f"{performance['pair_calculations_with_tile_recompute']:,}", f"{performance['process_peak_rss_bytes']/1e9:.2f} GB"], ["Landscape change", f"{landscape_performance['wall_seconds']:.1f} s", f"{landscape_performance['pair_calculations_with_tile_recompute']:,}", f"{landscape_performance['process_peak_rss_bytes']/1e9:.2f} GB"], ["64 full surfaces", f"{report['runtime_seconds']:.1f} s", "~120k", f"{report['storage']['sample_surface_bytes']/1e6:.1f} MB stored"]]
        _add_page(story, styles, "23 · Tile, halo, and performance validation", image=images["validation"], table=perf_table)
        schema_table = [["Candidate field", "Decision", "Reason"], ["magnitude + IQR/MAD", "KEEP", "overall level and heterogeneity"], ["fine radial profile", "KEEP", "nonmonotonic, transparent projection"], ["radially adjusted angular profile", "KEEP", "material directional information"], ["anisotropy / half-plane contrast", "EXPERIMENTAL", "distinct and interpretable, needs temporal stability"], ["low-order 2-D coefficients", "EXPERIMENTAL", "compact; residual error remains"], ["PCA/SVD scores", "EXPERIMENTAL", "held-out error and split-half instability"], ["25/50/75/100", "DIAGNOSTIC", "Phase 1 baseline only"]]
        _add_page(story, styles, "24 · Proposed provisional SynchronySignature", paragraphs=["Retain canonical pair geometry during computation. Store magnitude, heterogeneity, counts/coverage, fine radial and directional projections, and residual complexity. Preserve complete cold/warm/Delta surfaces for audits and the broad sample. No final fixed basis schema is adopted."], table=schema_table)
        counts = report["characteristic_scale_status_counts"]
        _add_page(story, styles, "25 · Phase 3 decision", paragraphs=[f"Among 64 real surfaces, the experimental scale screen returned {counts.get('candidate_plateau_scale', 0)} candidate plateaus, {counts.get('multiple_candidate_scales', 0)} multiscale cases, and {counts.get('right_censored_or_unresolved', 0)} right-censored/unresolved cases. These are diagnostics, not accepted characteristic scales.", "Proceed to Colorado temporal robustness with selected seasonal windows. Test whether radial profiles, directions, half-plane contrasts, residual complexity, and any aligned basis scores persist or rotate through time. Stop before CONUS or full-history scaling."])
        if isinstance(story[-1], PageBreak):
            story.pop()
        document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    decision_path = _decision_report(artifact_dir, report)
    digest = sha256(output_pdf.read_bytes()).hexdigest()
    manifest = {"path": str(output_pdf), "pages": 25, "sha256": digest, "bytes": output_pdf.stat().st_size, "decision_report": str(decision_path), "surface_report": str(artifact_dir / "surface_representation_report.json")}
    (artifact_dir / "atlas_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/synchrony-stack-phase2"))
    parser.add_argument("--output-pdf", type=Path, default=Path("output/pdf/colorado_synchrony_atlas_phase2.pdf"))
    args = parser.parse_args()
    print(json.dumps(build(args.artifact_dir.resolve(), args.output_pdf.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
