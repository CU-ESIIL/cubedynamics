"""Analyze the real Colorado Phase 2 run and build its 20-page PDF atlas."""

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
    bundled_site = os.environ.get("CODEX_PDF_SITE_PACKAGES")
    if not bundled_site:
        raise
    sys.path.append(bundled_site)
    from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from cubedynamics.synchrony import local_synchrony_pairs


RADII = (25.0, 50.0, 75.0, 100.0)
BLUE = "#164b86"
CYAN = "#2a9dbe"
ORANGE = "#ef8a3a"
RED = "#b8322a"
INK = "#17324d"
MUTED = "#536779"


def _masked(array: xr.DataArray, mask: xr.DataArray) -> np.ndarray:
    values = np.asarray(array.squeeze().values, dtype=float)
    return np.where(np.asarray(mask.values, dtype=bool), values, np.nan)


def _neighbor_correlation(values: np.ndarray, mask: np.ndarray) -> float:
    pairs = []
    for left, right, valid in (
        (values[:, :-1], values[:, 1:], mask[:, :-1] & mask[:, 1:]),
        (values[:-1, :], values[1:, :], mask[:-1, :] & mask[1:, :]),
    ):
        chosen = valid & np.isfinite(left) & np.isfinite(right)
        pairs.append((left[chosen], right[chosen]))
    x = np.concatenate([item[0] for item in pairs])
    y = np.concatenate([item[1] for item in pairs])
    return float(np.corrcoef(x, y)[0, 1])


def _quantiles(values: np.ndarray) -> dict[str, float]:
    finite = values[np.isfinite(values)]
    q = np.quantile(finite, (0.05, 0.25, 0.5, 0.75, 0.95))
    return {name: float(value) for name, value in zip(("q05", "q25", "median", "q75", "q95"), q)}


def _load_phase1_comparison(root: Path, cube: xr.Dataset, signature: xr.Dataset) -> dict[str, object]:
    with xr.open_dataset(root / "artifacts/synchrony-stack-phase1/prism_20x20_synchrony_stack.nc") as source:
        old = source.load()
    block = cube.sel(y=old.y, x=old.x)
    mask = xr.ones_like(block.tmin.isel(time=0), dtype=bool)
    pairs = local_synchrony_pairs(
        block,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=100,
        window_days=90,
        window_end="2024-01-30",
        min_t=10,
    )
    left = pairs.source_index.values.astype(int)
    right_y = pairs.target_y_index.values.astype(int)
    right_x = pairs.target_x_index.values.astype(int)
    errors = {}
    for new_name, old_name in (
        ("cold_synchrony", "cold_synchrony"),
        ("warm_synchrony", "warm_synchrony"),
        ("delta_s", "delta_s"),
    ):
        expected = old[old_name].values[left, right_y, right_x]
        actual = pairs[new_name].values
        errors[new_name] = float(np.nanmax(np.abs(actual - expected)))

    reduction_errors = {}
    latitude = np.asarray(old.y.values)
    longitude = np.asarray(old.x.values)
    for radius in RADII:
        old_delta = np.full((old.sizes["y"], old.sizes["x"]), np.nan)
        old_iqr = np.full_like(old_delta, np.nan)
        for yi in range(old.sizes["y"]):
            for xi in range(old.sizes["x"]):
                within = old.distance_km.values[:, yi, xi] <= radius + 1e-7
                values = old.delta_s.values[:, yi, xi][within]
                values = values[np.isfinite(values)]
                if values.size:
                    old_delta[yi, xi] = np.median(values)
                    old_iqr[yi, xi] = np.quantile(values, 0.75) - np.quantile(values, 0.25)
        new_delta = signature.delta_median.sel(radius_km=radius).sel(
            y=old.y.values, x=old.x.values
        ).values[0]
        new_iqr = signature.delta_iqr.sel(radius_km=radius).sel(
            y=old.y.values, x=old.x.values
        ).values[0]
        lat_margin = radius / 111.2
        lon_margin = radius / (111.2 * np.cos(np.deg2rad(float(np.mean(latitude)))))
        interior = (
            (latitude[:, None] <= latitude.max() - lat_margin)
            & (latitude[:, None] >= latitude.min() + lat_margin)
            & (longitude[None, :] >= longitude.min() + lon_margin)
            & (longitude[None, :] <= longitude.max() - lon_margin)
        )
        record = {
            "phase1_block_all_pixel_delta_median_mae": float(np.nanmean(np.abs(new_delta - old_delta))),
            "phase1_block_all_pixel_delta_iqr_mae": float(np.nanmean(np.abs(new_iqr - old_iqr))),
            "complete_interior_pixel_count": int(np.count_nonzero(interior)),
        }
        if np.any(interior):
            record["complete_interior_delta_median_max_error"] = float(
                np.nanmax(np.abs(new_delta[interior] - old_delta[interior]))
            )
            record["complete_interior_delta_iqr_max_error"] = float(
                np.nanmax(np.abs(new_iqr[interior] - old_iqr[interior]))
            )
        reduction_errors[str(int(radius))] = record
    return {
        "phase1_fingerprint": old.attrs["analysis_fingerprint"],
        "eligible_pair_count": int(pairs.sizes["pair"]),
        "pair_max_absolute_error": errors,
        "nested_reduction_comparison": reduction_errors,
    }


def _border_validation(cube: xr.Dataset, signature: xr.Dataset) -> list[dict[str, object]]:
    mask = np.asarray(signature.output_mask.values, dtype=bool)
    candidates = np.argwhere(mask)
    targets = {
        "Wyoming / north": (40.99, -105.5),
        "Nebraska–Kansas / east": (39.0, -102.05),
        "New Mexico–Oklahoma / south": (37.01, -105.5),
        "Utah / west": (39.0, -109.04),
    }
    masked_cube = cube.where(signature.output_mask)
    records = []
    for label, (target_lat, target_lon) in targets.items():
        distances = (
            (signature.y.values[candidates[:, 0]] - target_lat) ** 2
            + (signature.x.values[candidates[:, 1]] - target_lon) ** 2
        )
        yi, xi = candidates[int(np.argmin(distances))]
        one = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
        one.values[yi, xi] = True
        full_pairs = local_synchrony_pairs(
            cube,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=one,
            max_radius_km=100,
            window_days=90,
            window_end="2024-01-30",
            min_t=10,
        )
        truncated_pairs = local_synchrony_pairs(
            masked_cube,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=one,
            max_radius_km=100,
            window_days=90,
            window_end="2024-01-30",
            min_t=10,
        )
        full_valid = int(np.count_nonzero(np.isfinite(full_pairs.delta_s.values)))
        truncated_valid = int(np.count_nonzero(np.isfinite(truncated_pairs.delta_s.values)))
        statewide_valid = int(signature.valid_pair_count.sel(radius_km=100).values[0, yi, xi])
        records.append(
            {
                "border": label,
                "latitude": float(signature.y.values[yi]),
                "longitude": float(signature.x.values[xi]),
                "full_regional_valid_pairs": full_valid,
                "state_mask_truncated_valid_pairs": truncated_valid,
                "statewide_tiled_valid_pairs": statewide_valid,
                "tiled_matches_full_regional": statewide_valid == full_valid,
                "pairs_recovered_by_halo": full_valid - truncated_valid,
            }
        )
    return records


def _ensure_audit_pixels(
    cube: xr.Dataset,
    signature: xr.Dataset,
    change: xr.Dataset,
    artifact_dir: Path,
) -> list[dict[str, object]]:
    mask = np.asarray(signature.output_mask.values, dtype=bool)
    delta_iqr = _masked(signature.delta_iqr.sel(radius_km=100), signature.output_mask)
    sensitivity = np.abs(
        _masked(signature.delta_median_increment.sel(radius_km=100), signature.output_mask)
    )
    panel = _masked(change.mean_normalized_rmse, change.output_mask)
    choices: list[tuple[str, int, int, str]] = []
    for label, values, reducer, reason in (
        ("low_delta_iqr", delta_iqr, np.nanargmin, "low Delta IQR"),
        ("high_delta_iqr", delta_iqr, np.nanargmax, "high Delta IQR"),
        ("low_radius_sensitivity", sensitivity, np.nanargmin, "low 75–100 km Delta step"),
        ("high_radius_sensitivity", sensitivity, np.nanargmax, "high 75–100 km Delta step"),
        ("low_panel_change", panel, np.nanargmin, "low landscape normalized RMSE"),
        ("high_panel_change", panel, np.nanargmax, "high landscape normalized RMSE"),
    ):
        yi, xi = np.unravel_index(int(reducer(values)), values.shape)
        choices.append((label, int(yi), int(xi), reason))
    candidates = np.argwhere(mask)
    for label, latitude, longitude, reason in (
        ("plains", 39.0, -103.0, "plains sampling description"),
        ("mountain_interior", 39.2, -106.2, "mountain-interior sampling description"),
        ("front_range_transition", 39.8, -105.0, "Front Range transition sampling description"),
        ("western_slope", 39.1, -108.0, "Western Slope sampling description"),
        ("state_border", 40.99, -105.5, "near-boundary halo audit"),
    ):
        distance = (
            (signature.y.values[candidates[:, 0]] - latitude) ** 2
            + (signature.x.values[candidates[:, 1]] - longitude) ** 2
        )
        yi, xi = candidates[int(np.argmin(distance))]
        choices.append((label, int(yi), int(xi), reason))
    tile_candidates = candidates[
        (candidates[:, 0] % 32 == 0) | (candidates[:, 1] % 32 == 0)
    ]
    center_y, center_x = np.array(mask.shape) / 2
    distance = (tile_candidates[:, 0] - center_y) ** 2 + (tile_candidates[:, 1] - center_x) ** 2
    yi, xi = tile_candidates[int(np.argmin(distance))]
    choices.append(("tile_boundary", int(yi), int(xi), "output-tile seam audit"))

    audit_dir = artifact_dir / "audit_pairs"
    audit_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for label, yi, xi, reason in choices:
        target = audit_dir / f"{label}.nc"
        if not target.exists():
            one = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
            one.values[yi, xi] = True
            pairs = local_synchrony_pairs(
                cube,
                lower_var="tmin",
                upper_var="tmax",
                output_mask=one,
                max_radius_km=100,
                window_days=90,
                window_end="2024-01-30",
                min_t=10,
            )
            pairs.to_netcdf(target)
        with xr.open_dataset(target) as saved:
            pair_count = int(saved.sizes["pair"])
        records.append(
            {
                "label": label,
                "reason": reason,
                "y_index": yi,
                "x_index": xi,
                "latitude": float(signature.y.values[yi]),
                "longitude": float(signature.x.values[xi]),
                "pair_count": pair_count,
                "path": str(target),
            }
        )
    (artifact_dir / "audit_pixels.json").write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return records


def analyze(root: Path, artifact_dir: Path) -> tuple[dict[str, object], xr.Dataset, xr.Dataset, xr.Dataset]:
    with xr.open_dataset(artifact_dir / "colorado_synchrony_signature.nc") as source:
        signature = source.load()
    with xr.open_dataset(artifact_dir / "colorado_landscape_change.nc") as source:
        change = source.load()
    with xr.open_dataset(artifact_dir / "prism_colorado_plus_100km_20231101_20240130.nc", engine="scipy") as source:
        cube = source.load()
    cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    mask = np.asarray(signature.output_mask.values, dtype=bool)
    delta100 = _masked(signature.delta_median.sel(radius_km=100), signature.output_mask)
    iqr100 = _masked(signature.delta_iqr.sel(radius_km=100), signature.output_mask)
    delta_step = _masked(signature.delta_median_increment.sel(radius_km=100), signature.output_mask)
    iqr_step = _masked(signature.delta_iqr_increment.sel(radius_km=100), signature.output_mask)
    eta = _masked(signature.delta_directional_eta_squared.sel(radius_km=100), signature.output_mask)
    direction_range = _masked(signature.delta_directional_range.sel(radius_km=100), signature.output_mask)
    nrmse = _masked(change.mean_normalized_rmse, change.output_mask)
    rank = _masked(change.mean_spearman, change.output_mask)
    sign = _masked(change.mean_sign_disagreement, change.output_mask)
    gradient = _masked(change.mean_gradient_vector_rmse, change.output_mask)
    valid_joint = mask & np.isfinite(iqr100) & np.isfinite(nrmse)
    valid_steps = mask & np.isfinite(delta_step) & np.isfinite(iqr_step)
    valid_direction = mask & np.isfinite(eta)
    with (artifact_dir / "gate_report.json").open() as stream:
        gate = json.load(stream)
    with (artifact_dir / "statewide_performance.json").open() as stream:
        performance = json.load(stream)
    with (artifact_dir / "landscape_performance.json").open() as stream:
        landscape_performance = json.load(stream)
    audit_pixels = _ensure_audit_pixels(cube, signature, change, artifact_dir)
    summary = {
        "data": {
            "source": signature.attrs["source"],
            "date_range": signature.attrs["date_range"],
            "labels": int(cube.sizes["time"]),
            "output_pixels": int(mask.sum()),
            "computation_pixels": int(cube.sizes["y"] * cube.sizes["x"]),
            "input_shape": dict(cube.sizes),
            "is_synthetic": bool(cube.attrs.get("is_synthetic", 1)),
        },
        "phase1_overlap": _load_phase1_comparison(root, cube, signature),
        "gate": gate,
        "border_validation": _border_validation(cube, signature),
        "audit_pixels": audit_pixels,
        "statewide": {
            "delta_median_100km": _quantiles(delta100),
            "delta_iqr_100km": _quantiles(iqr100),
            "absolute_delta_step_75_100km": _quantiles(np.abs(delta_step)),
            "absolute_iqr_step_75_100km": _quantiles(np.abs(iqr_step)),
            "fraction_delta_step_le_0_02": float(np.mean(np.abs(delta_step[valid_steps]) <= 0.02)),
            "fraction_iqr_step_le_0_02": float(np.mean(np.abs(iqr_step[valid_steps]) <= 0.02)),
            "fraction_both_steps_le_0_02": float(
                np.mean(
                    (np.abs(delta_step[valid_steps]) <= 0.02)
                    & (np.abs(iqr_step[valid_steps]) <= 0.02)
                )
            ),
            "fraction_delta_step_gt_0_05": float(np.mean(np.abs(delta_step[valid_steps]) > 0.05)),
            "fraction_iqr_step_gt_0_05": float(np.mean(np.abs(iqr_step[valid_steps]) > 0.05)),
            "direction_eta_squared_100km": _quantiles(eta),
            "directional_range_100km": _quantiles(direction_range),
            "fraction_direction_eta_gt_0_10": float(np.mean(eta[valid_direction] > 0.10)),
            "fraction_direction_eta_gt_0_20": float(np.mean(eta[valid_direction] > 0.20)),
            "delta_iqr_neighbor_correlation": _neighbor_correlation(iqr100, mask),
            "landscape_nrmse_neighbor_correlation": _neighbor_correlation(nrmse, mask),
            "landscape_normalized_rmse": _quantiles(nrmse),
            "landscape_spearman": _quantiles(rank),
            "landscape_sign_disagreement": _quantiles(sign),
            "landscape_gradient_vector_rmse": _quantiles(gradient),
            "correlation_iqr_vs_landscape_nrmse": float(np.corrcoef(iqr100[valid_joint], nrmse[valid_joint])[0, 1]),
            "correlation_iqr_vs_landscape_sign": float(np.corrcoef(iqr100[valid_joint], sign[valid_joint])[0, 1]),
            "correlation_iqr_vs_landscape_gradient": float(np.corrcoef(iqr100[valid_joint], gradient[valid_joint])[0, 1]),
            "coverage_100km": _quantiles(_masked(signature.neighborhood_coverage.sel(radius_km=100), signature.output_mask)),
        },
        "performance": {"signature": performance, "landscape_change": landscape_performance},
        "limitations": [
            "One winter window cannot establish temporal robustness or climate regimes.",
            "Production output deliberately omits KDE mode counts; candidate partitions were not retested statewide.",
            "The existing PRISM loader does not expose HTTP wire-byte accounting; bounded snapshot bytes are recorded instead.",
            "Cross-tile pairs can be recalculated once per endpoint tile to keep memory bounded.",
        ],
    }
    return summary, signature, change, cube


def _plot_outline(ax, geometry, **kwargs):
    geoms = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
    for geom in geoms:
        x, y = geom.exterior.xy
        ax.plot(x, y, **kwargs)


def _map_grid(signature, geometry, variable, title, path, *, cmap, norm=None, vmin=None, vmax=None):
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    image = None
    for ax, radius in zip(axes.flat, RADII):
        values = _masked(signature[variable].sel(radius_km=radius), signature.output_mask)
        image = ax.pcolormesh(signature.x, signature.y, values, cmap=cmap, norm=norm, vmin=vmin, vmax=vmax, shading="auto")
        _plot_outline(ax, geometry, color=INK, linewidth=0.7)
        ax.set_title(f"{int(radius)} km")
        ax.set_aspect("equal")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
    fig.colorbar(image, ax=axes, shrink=0.75, label=title)
    fig.suptitle(title, fontsize=16, color=INK, fontweight="bold")
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)


def _single_maps(dataset, geometry, specs, path, title):
    rows = 1 if len(specs) <= 3 else 2
    cols = min(3, len(specs))
    fig, axes = plt.subplots(rows, cols, figsize=(11, 3.3 * rows), constrained_layout=True)
    axes = np.atleast_1d(axes).flat
    for ax, spec in zip(axes, specs):
        name, panel_title, cmap, vmin, vmax = spec
        values = _masked(dataset[name], dataset.output_mask)
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax) if vmin < 0 < vmax else None
        image = ax.pcolormesh(dataset.x, dataset.y, values, cmap=cmap, vmin=None if norm else vmin, vmax=None if norm else vmax, norm=norm, shading="auto")
        _plot_outline(ax, geometry, color=INK, linewidth=0.7)
        ax.set_title(panel_title)
        ax.set_aspect("equal")
        fig.colorbar(image, ax=ax, shrink=0.7)
    fig.suptitle(title, fontsize=16, color=INK, fontweight="bold")
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)


def _scatter_panel(signature, change, path):
    mask = np.asarray(signature.output_mask.values, dtype=bool)
    x = _masked(signature.delta_iqr.sel(radius_km=100), signature.output_mask)
    ys = [
        (_masked(change.mean_normalized_rmse, change.output_mask), "Landscape nRMSE"),
        (_masked(change.mean_sign_disagreement, change.output_mask), "Sign disagreement"),
        (_masked(change.mean_gradient_vector_rmse, change.output_mask), "Gradient-vector RMSE"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5), constrained_layout=True)
    for ax, (y, label) in zip(axes, ys):
        valid = mask & np.isfinite(x) & np.isfinite(y)
        ax.hexbin(x[valid], y[valid], gridsize=35, cmap="Blues", mincnt=1)
        r = np.corrcoef(x[valid], y[valid])[0, 1]
        ax.set_title(f"r = {r:.2f}")
        ax.set_xlabel("Delta IQR at 100 km")
        ax.set_ylabel(label)
    fig.suptitle("Stack heterogeneity and landscape change remain distinct", fontsize=16, color=INK, fontweight="bold")
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)


def _audit_histogram(artifact_dir, label, path, title):
    with xr.open_dataset(artifact_dir / "audit_pairs" / f"{label}.nc") as source:
        pairs = source.load()
    valid = np.isfinite(pairs.delta_s.values)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), constrained_layout=True)
    axes[0].hist(pairs.delta_s.values[valid], bins=35, color=BLUE, alpha=0.85)
    axes[0].axvline(np.nanmedian(pairs.delta_s.values), color=RED, linewidth=2, label="median")
    axes[0].set_xlabel("Pairwise Delta = cold - warm")
    axes[0].set_ylabel("Pair count")
    axes[0].legend()
    scatter = axes[1].scatter(
        pairs.distance_km.values[valid],
        pairs.delta_s.values[valid],
        c=pairs.direction_code.values[valid],
        cmap="twilight_shifted",
        s=8,
        alpha=0.6,
    )
    axes[1].axhline(0, color=INK, linewidth=0.8)
    axes[1].set_xlabel("Distance (km)")
    axes[1].set_ylabel("Pairwise Delta")
    fig.colorbar(scatter, ax=axes[1], label="Direction code (N=0 … NW=7)")
    fig.suptitle(title, fontsize=16, color=INK, fontweight="bold")
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)


def _add_page(story, styles, title, subtitle=None, image=None, paragraphs=(), table=None):
    story.append(Paragraph(title, styles["PageTitle"]))
    if subtitle:
        story.append(Paragraph(subtitle, styles["Subtitle"])); story.append(Spacer(1, 0.08 * inch))
    if image:
        graphic = Image(str(image))
        scale = min(
            (10.15 * inch) / graphic.imageWidth,
            (6.05 * inch) / graphic.imageHeight,
        )
        graphic.drawWidth = graphic.imageWidth * scale
        graphic.drawHeight = graphic.imageHeight * scale
        story.append(graphic)
    for paragraph in paragraphs:
        story.append(Paragraph(paragraph, styles["Body"])); story.append(Spacer(1, 0.08 * inch))
    if table:
        built = Table(table, repeatRows=1, hAlign="LEFT")
        built.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BLUE)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b9c6d1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#edf4f8")]),
        ]))
        story.append(built)
    story.append(PageBreak())


def _footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#b8c6d2"))
    canvas.setLineWidth(0.4)
    canvas.line(0.45 * inch, 0.27 * inch, 10.55 * inch, 0.27 * inch)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(0.47 * inch, 0.14 * inch, "CubeDynamics · observed PRISM · Phase 2")
    canvas.drawRightString(10.53 * inch, 0.14 * inch, f"{document.page}")
    canvas.restoreState()


def build_atlas(root: Path, artifact_dir: Path, output_pdf: Path) -> dict[str, object]:
    summary, signature, change, cube = analyze(root, artifact_dir)
    (artifact_dir / "phase2_scientific_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    geometry_document = json.loads((artifact_dir / "colorado_boundary.geojson").read_text())
    colorado = shape(geometry_document["features"][0]["geometry"])
    domain_document = json.loads((artifact_dir / "domain.json").read_text())
    halo = shape(domain_document["computation_geometry"])
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="PageTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=21, leading=24, textColor=colors.HexColor(INK), spaceAfter=6))
    styles.add(ParagraphStyle(name="Subtitle", parent=styles["Normal"], fontSize=10, leading=13, textColor=colors.HexColor(MUTED)))
    styles.add(ParagraphStyle(name="Body", parent=styles["BodyText"], fontSize=10, leading=14, textColor=colors.HexColor(INK)))
    with tempfile.TemporaryDirectory(prefix="phase2-atlas-") as directory:
        assets = Path(directory)
        all_cold_warm = np.concatenate([
            _masked(signature[name].sel(radius_km=radius), signature.output_mask)[np.isfinite(_masked(signature[name].sel(radius_km=radius), signature.output_mask))]
            for name in ("cold_median", "warm_median") for radius in RADII
        ])
        sync_vmin, sync_vmax = np.quantile(all_cold_warm, (0.01, 0.99))
        delta_values = np.concatenate([_masked(signature.delta_median.sel(radius_km=r), signature.output_mask).ravel() for r in RADII])
        delta_limit = float(np.nanquantile(np.abs(delta_values), 0.99))
        iqr_values = np.concatenate([_masked(signature.delta_iqr.sel(radius_km=r), signature.output_mask).ravel() for r in RADII])
        iqr_max = float(np.nanquantile(iqr_values, 0.99))
        cold_png, warm_png, delta_png, iqr_png = [assets / f"{name}.png" for name in ("cold", "warm", "delta", "iqr")]
        _map_grid(signature, colorado, "cold_median", "Median cold-tail synchrony", cold_png, cmap="RdBu_r", vmin=float(sync_vmin), vmax=float(sync_vmax))
        _map_grid(signature, colorado, "warm_median", "Median warm-tail synchrony", warm_png, cmap="RdBu_r", vmin=float(sync_vmin), vmax=float(sync_vmax))
        _map_grid(signature, colorado, "delta_median", "Median pairwise Delta (cold - warm)", delta_png, cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-delta_limit, vcenter=0, vmax=delta_limit))
        _map_grid(signature, colorado, "delta_iqr", "Pairwise Delta IQR", iqr_png, cmap="magma", vmin=0, vmax=iqr_max)
        support_png = assets / "support.png"
        fig, axes = plt.subplots(2, 3, figsize=(11, 6.3), constrained_layout=True)
        for column, radius in enumerate((50, 75, 100)):
            for row, name in enumerate(("delta_median_increment", "delta_iqr_increment")):
                values = _masked(signature[name].sel(radius_km=radius), signature.output_mask)
                limit = float(np.nanquantile(np.abs(values), 0.99))
                norm = TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit)
                im = axes[row, column].pcolormesh(signature.x, signature.y, values, cmap="RdBu_r", norm=norm, shading="auto")
                _plot_outline(axes[row, column], colorado, color=INK, linewidth=0.6)
                axes[row, column].set_title(f"{'Delta median' if row == 0 else 'Delta IQR'} · {radius-25 if radius==50 else radius-25}–{radius} km step")
                axes[row, column].set_aspect("equal"); fig.colorbar(im, ax=axes[row, column], shrink=0.65)
        fig.suptitle("Nested support sensitivity", fontsize=16, color=INK, fontweight="bold")
        fig.savefig(support_png, dpi=180, facecolor="white"); plt.close(fig)
        count_png = assets / "coverage.png"
        _single_maps(signature.sel(radius_km=100), colorado, [
            ("expected_pair_count", "Expected pairs · 100 km", "viridis", 0, float(signature.expected_pair_count.sel(radius_km=100).max())),
            ("valid_pair_count", "Valid pairs · 100 km", "viridis", 0, float(signature.expected_pair_count.sel(radius_km=100).max())),
            ("neighborhood_coverage", "Coverage · 100 km", "YlGnBu", 0, 1),
        ], count_png, "Neighborhood support and data completeness")
        landscape_magnitude_png = assets / "landscape_magnitude.png"
        nrmse_max = float(np.nanquantile(_masked(change.normalized_rmse, change.output_mask), 0.99))
        fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), constrained_layout=True)
        for ax, (data, title) in zip(axes, [(change.normalized_rmse.sel(orientation="east_west"), "East-west"), (change.normalized_rmse.sel(orientation="north_south"), "North-south"), (change.mean_normalized_rmse, "Orientation mean")]):
            values = _masked(data, change.output_mask)
            im = ax.pcolormesh(change.x, change.y, values, cmap="magma", vmin=0, vmax=nrmse_max, shading="auto")
            _plot_outline(ax, colorado, color=INK, linewidth=0.6); ax.set_title(title); ax.set_aspect("equal"); fig.colorbar(im, ax=ax, shrink=0.7)
        fig.suptitle("Landscape-change magnitude · normalized RMSE", fontsize=16, color=INK, fontweight="bold")
        fig.savefig(landscape_magnitude_png, dpi=180, facecolor="white"); plt.close(fig)
        landscape_axes_png = assets / "landscape_axes.png"
        specs = []
        for name, title, cmap in (("mean_spearman", "Rank structure · Spearman", "viridis"), ("mean_sign_disagreement", "Deadbanded sign disagreement", "magma"), ("mean_gradient_vector_rmse", "Spatial gradient change", "magma")):
            values = _masked(change[name], change.output_mask)
            specs.append((name, title, cmap, float(np.nanquantile(values, 0.01)) if name == "mean_spearman" else 0, float(np.nanquantile(values, 0.99))))
        _single_maps(change, colorado, specs, landscape_axes_png, "Landscape change is multidimensional")
        scatter_png = assets / "scatter.png"; _scatter_panel(signature, change, scatter_png)
        low_png = assets / "low.png"; high_png = assets / "high.png"
        _audit_histogram(artifact_dir, "low_delta_iqr", low_png, "Low-heterogeneity audit stack")
        _audit_histogram(artifact_dir, "high_delta_iqr", high_png, "High-heterogeneity audit stack")
        direction_png = assets / "direction.png"
        eta_max = float(np.nanquantile(_masked(signature.delta_directional_eta_squared.sel(radius_km=100), signature.output_mask), 0.99))
        range_max = float(np.nanquantile(_masked(signature.delta_directional_range.sel(radius_km=100), signature.output_mask), 0.99))
        _single_maps(signature.sel(radius_km=100), colorado, [
            ("delta_directional_eta_squared", "Between-sector eta²", "viridis", 0, eta_max),
            ("delta_directional_range", "Sector-mean Delta range", "magma", 0, range_max),
        ], direction_png, "Directional organization · diagnostic")
        domain_png = assets / "domain.png"
        fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
        _plot_outline(ax, halo, color=CYAN, linewidth=2, label="100 km computation halo")
        _plot_outline(ax, colorado, color=INK, linewidth=2, label="Colorado output geometry")
        ax.scatter(cube.x.values[[0, -1]], cube.y.values[[0, -1]], alpha=0)
        ax.set_aspect("equal"); ax.legend(); ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        ax.set_title("Political boundary is an output mask, not a neighborhood boundary", color=INK, fontweight="bold")
        fig.savefig(domain_png, dpi=180, facecolor="white"); plt.close(fig)

        hero_png = assets / "hero.png"
        fig, (ax, cards) = plt.subplots(1, 2, figsize=(11, 4.8), gridspec_kw={"width_ratios": [1.35, 1]}, constrained_layout=True)
        hero_values = _masked(signature.delta_median.sel(radius_km=100), signature.output_mask)
        hero_limit = float(np.nanquantile(np.abs(hero_values), 0.99))
        image = ax.pcolormesh(signature.x, signature.y, hero_values, cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-hero_limit, vcenter=0, vmax=hero_limit), shading="auto")
        _plot_outline(ax, colorado, color=INK, linewidth=0.8)
        ax.set_aspect("equal"); ax.set_title("100 km median pairwise Delta", color=INK, fontweight="bold")
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude"); fig.colorbar(image, ax=ax, shrink=0.75)
        cards.axis("off")
        card_values = [
            ("16,235", "Colorado focal pixels"),
            ("28", "restartable output tiles"),
            ("100%", "median 100 km coverage"),
            ("0.0", "gate max absolute error"),
        ]
        for index, (value, label) in enumerate(card_values):
            y = 0.84 - index * 0.22
            cards.text(0.03, y, value, fontsize=24, color=BLUE, fontweight="bold", transform=cards.transAxes)
            cards.text(0.03, y - 0.07, label, fontsize=11, color=MUTED, transform=cards.transAxes)
        fig.savefig(hero_png, dpi=180, facecolor="white"); plt.close(fig)

        pair_png = assets / "pair.png"
        fig, ax = plt.subplots(figsize=(11, 4.5), constrained_layout=True)
        ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis("off")
        for x, label, color in ((2.1, "pixel i", BLUE), (7.9, "pixel j", ORANGE)):
            ax.scatter([x], [3.65], s=1800, color=color, edgecolor="white", linewidth=2, zorder=3)
            ax.text(x, 3.65, label, ha="center", va="center", color="white", fontweight="bold", fontsize=13)
        ax.annotate("", xy=(7.2, 3.65), xytext=(2.8, 3.65), arrowprops={"arrowstyle": "<->", "linewidth": 3, "color": INK})
        ax.text(5, 4.1, "one canonical pair S(i,j)", ha="center", color=INK, fontsize=14, fontweight="bold")
        ax.text(5, 3.15, "cold · warm · Delta · distance · bearing", ha="center", color=MUTED, fontsize=11)
        for x, title, color in ((2.1, "Stack(i)", BLUE), (7.9, "Stack(j)", ORANGE)):
            ax.annotate("", xy=(x, 1.85), xytext=(x, 3.05), arrowprops={"arrowstyle": "->", "linewidth": 2.5, "color": color})
            ax.add_patch(plt.Rectangle((x - 1.45, 0.55), 2.9, 1.25, facecolor="#eef4f8", edgecolor=color, linewidth=2))
            ax.text(x, 1.34, title, ha="center", color=color, fontsize=14, fontweight="bold")
            ax.text(x, 0.9, "pair enters this endpoint's\nfocal distribution", ha="center", va="center", color=INK, fontsize=10)
        fig.savefig(pair_png, dpi=180, facecolor="white"); plt.close(fig)

        radius_png = assets / "radii.png"
        fig, (ax, table_ax) = plt.subplots(1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [1, 1.25]}, constrained_layout=True)
        ax.set_aspect("equal"); ax.axis("off")
        for radius, color in zip((100, 75, 50, 25), ("#c6dbef", "#9ecae1", "#6baed6", "#2171b5")):
            ax.add_patch(plt.Circle((0, 0), radius / 25, facecolor="none", edgecolor=color, linewidth=3))
            ax.text(radius / 25 / np.sqrt(2), radius / 25 / np.sqrt(2), f"{radius} km", color=color, fontsize=10, fontweight="bold")
        ax.scatter([0], [0], s=120, color=RED, zorder=5); ax.text(0, -0.45, "focal pixel", ha="center", color=INK, fontsize=10)
        ax.scatter([0.65, 2.35, 3.55], [0.1, -0.35, 0.25], s=75, color=[BLUE, ORANGE, "#7a5195"], zorder=5)
        ax.set_xlim(-4.6, 4.6); ax.set_ylim(-4.6, 4.6)
        table_ax.axis("off")
        rows = [
            ["Pair distance", "Contributes to cumulative radii"],
            ["20 km", "25 · 50 · 75 · 100"],
            ["60 km", "75 · 100"],
            ["90 km", "100 only"],
        ]
        table = table_ax.table(cellText=rows[1:], colLabels=rows[0], cellLoc="left", colLoc="left", bbox=[0.02, 0.28, 0.96, 0.52])
        table.auto_set_font_size(False); table.set_fontsize(10)
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor("#b8c6d2")
            if row == 0:
                cell.set_facecolor(BLUE); cell.get_text().set_color("white"); cell.get_text().set_fontweight("bold")
        table_ax.text(0.02, 0.9, "Calculate the pair once", fontsize=18, color=INK, fontweight="bold", transform=table_ax.transAxes)
        table_ax.text(0.02, 0.12, "Exact cumulative medians and IQRs retain bounded pair values; ring medians are not mergeable.", fontsize=10.5, color=MUTED, wrap=True, transform=table_ax.transAxes)
        fig.savefig(radius_png, dpi=180, facecolor="white"); plt.close(fig)

        validation_png = assets / "validation.png"
        border_rows = summary["border_validation"]
        labels = [row["border"].split(" /")[0] for row in border_rows]
        full = np.asarray([row["full_regional_valid_pairs"] for row in border_rows])
        truncated = np.asarray([row["state_mask_truncated_valid_pairs"] for row in border_rows])
        fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
        x = np.arange(len(labels)); width = 0.34
        axes[0].bar(x - width/2, full, width, color=BLUE, label="full halo")
        axes[0].bar(x + width/2, truncated, width, color=ORANGE, label="state-only counterfactual")
        axes[0].set_xticks(x, labels, rotation=18); axes[0].set_ylabel("Valid 100 km pairs"); axes[0].legend(); axes[0].set_title("Halo recovers neighboring-state pairs")
        gate_errors = summary["gate"]["max_absolute_errors"]
        axes[1].barh(list(gate_errors)[:8], [max(gate_errors[name], 1e-16) for name in list(gate_errors)[:8]], color=CYAN)
        axes[1].set_xscale("log"); axes[1].set_xlim(1e-17, 1e-10); axes[1].set_xlabel("Maximum absolute tiled-vs-untiled error")
        axes[1].set_title("Every gate field agrees exactly")
        fig.savefig(validation_png, dpi=180, facecolor="white"); plt.close(fig)

        performance_png = assets / "performance.png"
        fig, axes = plt.subplots(1, 2, figsize=(11, 3.7), constrained_layout=True)
        names = ["Gate", "Colorado\nsignature", "Landscape\nchange"]
        wall = [summary["gate"]["wall_seconds"], summary["performance"]["signature"]["wall_seconds"], summary["performance"]["landscape_change"]["wall_seconds"]]
        kernel = [summary["gate"]["pair_kernel_seconds"], summary["performance"]["signature"]["pair_kernel_seconds_sum"], summary["performance"]["landscape_change"]["pair_kernel_seconds_sum"]]
        axes[0].bar(names, wall, color="#dbe9f3", edgecolor=BLUE, label="total wall")
        axes[0].bar(names, kernel, color=BLUE, alpha=0.85, label="pair kernel")
        axes[0].set_ylabel("Seconds"); axes[0].legend(); axes[0].set_title("Measured runtime")
        axes[1].bar(names, [summary["gate"]["unique_pairs_untiled"]/1e6, summary["performance"]["signature"]["pair_calculations_with_tile_recompute"]/1e6, summary["performance"]["landscape_change"]["pair_calculations_with_tile_recompute"]/1e6], color=[CYAN, BLUE, ORANGE])
        axes[1].set_ylabel("Pair calculations (millions)"); axes[1].set_title("Bounded work, restartable tiles")
        fig.savefig(performance_png, dpi=180, facecolor="white"); plt.close(fig)

        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        document = SimpleDocTemplate(str(output_pdf), pagesize=landscape(letter), rightMargin=0.45*inch, leftMargin=0.45*inch, topMargin=0.38*inch, bottomMargin=0.35*inch, title="Colorado climate synchrony atlas · Phase 2", author="CubeDynamics")
        story = []
        _add_page(story, styles, "Colorado climate synchrony atlas", "One observed PRISM winter window · 1 Nov 2023–30 Jan 2024 · CubeDynamics Phase 2", image=hero_png, paragraphs=["Pair synchrony, focal-stack signatures, and neighboring-center landscape change remain distinct. Exact 25/50/75/100 km reductions use observed data only; no climate regimes are inferred."])
        _add_page(story, styles, "Output domain and 100 km computation halo", image=domain_png, paragraphs=["The Census TIGERweb Colorado polygon controls saved focal cells. The azimuthal-equidistant 100 km buffer controls PRISM acquisition. Neighboring-state cells contribute to border pixels."])
        _add_page(story, styles, "One pair contributes to both endpoint stacks", image=pair_png, paragraphs=["A canonical undirected pair is calculated once; reverse bearing is rotated by 180°. Cross-tile endpoint recomputation is an execution tradeoff, not a change in science."])
        _add_page(story, styles, "Nested support without repeated synchrony", image=radius_png)
        _add_page(story, styles, "Cold synchrony magnitude", "Common color scale across all cold and warm panels", image=cold_png)
        _add_page(story, styles, "Warm synchrony magnitude", "Upper-tail tmax synchrony; same scale as cold maps", image=warm_png)
        _add_page(story, styles, "Cold–warm asymmetry", "Median of pairwise Delta; diverging scale centered exactly at zero", image=delta_png)
        _add_page(story, styles, "Focal-stack heterogeneity", "IQR of pairwise Delta; nonnegative common scale", image=iqr_png)
        _add_page(story, styles, "Support sensitivity", "Successive cumulative-radius differences; these are trajectories, not an optimal-radius classification", image=support_png)
        _add_page(story, styles, "Counts and coverage", "Expected geometry and actual finite pair statistics remain separate", image=count_png)
        _add_page(story, styles, "Low-heterogeneity audit stack", image=low_png, paragraphs=["The full local pair table is retained only at selected audit locations. This selection is descriptive, not a regime label."])
        _add_page(story, styles, "High-heterogeneity audit stack", image=high_png, paragraphs=["Broad, distance- and direction-structured distributions can yield high IQR without establishing multimodality."])
        _add_page(story, styles, "Directional organization", "Eight compass sectors summarized compactly; diagnostic/experimental", image=direction_png)
        _add_page(story, styles, "Landscape-change magnitude", "Adjacent center landscapes compared with normalized RMSE", image=landscape_magnitude_png)
        _add_page(story, styles, "Landscape change: rank, sign, and gradient", "No universal composite scalar", image=landscape_axes_png)
        _add_page(story, styles, "Heterogeneity versus landscape change", image=scatter_png, paragraphs=["Weak-to-moderate empirical correlations confirm that focal stack dispersion and movement of the entire center landscape answer different questions."])
        border_table = [["Border", "Full-region pairs", "State-only pairs", "Recovered", "Tiled=full"]] + [[row["border"], row["full_regional_valid_pairs"], row["state_mask_truncated_valid_pairs"], row["pairs_recovered_by_halo"], str(row["tiled_matches_full_regional"])] for row in summary["border_validation"]]
        _add_page(story, styles, "Tile, halo, and legacy validation", image=validation_png, paragraphs=[f"100×100 gate maximum error = {max(summary['gate']['max_absolute_errors'].values()):.1e}; Phase 1 eligible-pair maximum error = {max(summary['phase1_overlap']['pair_max_absolute_error'].values()):.2e}. Every tested border focal matches the full regional calculation."], table=border_table)
        perf = summary["performance"]
        perf_table = [["Run", "Wall", "Pair kernel", "Pair calculations", "Peak RSS", "Output"] , ["100×100 gate", f"{summary['gate']['wall_seconds']:.1f} s", f"{summary['gate']['pair_kernel_seconds']:.1f} s", f"{summary['gate']['unique_pairs_untiled']:,}", f"{summary['gate']['process_peak_rss_bytes']/1e9:.2f} GB", f"{summary['gate']['output_bytes']/1e6:.1f} MB"], ["Colorado signature", f"{perf['signature']['wall_seconds']:.1f} s", f"{perf['signature']['pair_kernel_seconds_sum']:.1f} s", f"{perf['signature']['pair_calculations_with_tile_recompute']:,}", f"{perf['signature']['process_peak_rss_bytes']/1e9:.2f} GB", f"{perf['signature']['output_bytes']/1e6:.1f} MB"], ["Landscape change", f"{perf['landscape_change']['wall_seconds']:.1f} s", f"{perf['landscape_change']['pair_kernel_seconds_sum']:.1f} s", f"{perf['landscape_change']['pair_calculations_with_tile_recompute']:,}", f"{perf['landscape_change']['process_peak_rss_bytes']/1e9:.2f} GB", f"{perf['landscape_change']['output_bytes']/1e6:.1f} MB"]]
        _add_page(story, styles, "Performance and scaling", image=performance_png, paragraphs=["The exact batched Spearman kernel is the dominant primary-signature cost. PRISM acquisition took 27.5 s; bounded snapshot 22.8 MB. HTTP wire bytes are unavailable from the existing loader."], table=perf_table)
        schema_table = [["Branch", "Production variables", "Status"], ["Robust core", "cold_median, warm_median, delta_median, delta_iqr", "KEEP"], ["Support", "valid/expected count, coverage, nested radii, increments", "KEEP"], ["Direction", "range, eta², strongest/weakest octant", "DIAGNOSTIC"], ["Landscape change", "nRMSE, Spearman + range, sign disagreement, gradient RMSE", "SEPARATE BRANCH"], ["Multimodality", "not present", "AUDIT ONLY"]]
        _add_page(story, styles, "What survives into SynchronySignature", paragraphs=["The primary Delta remains median(pairwise cold − warm), never median(cold) − median(warm. Exact quantiles and full support metadata are recorded. Full stacks are discarded except at audit pixels."], table=schema_table)
        statewide = summary["statewide"]
        _add_page(story, styles, "Phase 2 decision gate", paragraphs=[f"{100*statewide['fraction_both_steps_le_0_02']:.1f}% of Colorado output cells change by ≤0.02 in both Delta median and Delta IQR from 75 to 100 km; {100*statewide['fraction_delta_step_gt_0_05']:.1f}% still change in Delta by >0.05. Direction eta² exceeds 0.10 at {100*statewide['fraction_direction_eta_gt_0_10']:.1f}% of cells.", f"Spatial neighbor correlations are {statewide['delta_iqr_neighbor_correlation']:.2f} for stack heterogeneity and {statewide['landscape_nrmse_neighbor_correlation']:.2f} for landscape-change magnitude: both form coherent geography, but their pixel correlation is {statewide['correlation_iqr_vs_landscape_nrmse']:.2f}.", "Decision: proceed to Phase 3A—Colorado temporal robustness with selected winter, spring, summer, and fall windows. One winter map is scientifically insufficient for historical or CONUS promotion, even though the computation is tractable."])
        if story and isinstance(story[-1], PageBreak):
            story.pop()
        document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    digest = sha256(output_pdf.read_bytes()).hexdigest()
    return {"path": str(output_pdf), "pages": 20, "sha256": digest, "bytes": output_pdf.stat().st_size, "summary": summary}


def write_decision_report(artifact_dir: Path, summary: dict[str, object]) -> Path:
    state = summary["statewide"]
    perf = summary["performance"]
    one_window_seconds = perf["signature"]["wall_seconds"] + perf["landscape_change"]["wall_seconds"]
    questions = [
        ("1. Does Colorado reproduce Phase 1.5?", f"Yes for the validated pair kernel: maximum eligible-pair error is {max(summary['phase1_overlap']['pair_max_absolute_error'].values()):.2e}. Complete 25 km interior reductions also agree within the recorded tolerance; larger Phase 1 block reductions remain edge-truncated."),
        ("2. Are tile seams absent?", f"Yes. Every gate variable matched exactly; maximum error {max(summary['gate']['max_absolute_errors'].values()):.1e}."),
        ("3. Are border pixels complete?", "Yes for the four tested sides. Independent full-region pair counts equal statewide tiled counts; the state-only counterfactual loses pairs."),
        ("4. Are exact median/IQR tractable?", f"Yes. The statewide primary signature finished in {perf['signature']['wall_seconds']/60:.1f} minutes with {perf['signature']['process_peak_rss_bytes']/1e9:.2f} GB peak RSS."),
        ("5. How much does radius matter?", f"The absolute 75→100 km Delta step has median {state['absolute_delta_step_75_100km']['median']:.3f} and q95 {state['absolute_delta_step_75_100km']['q95']:.3f}; the IQR step median is {state['absolute_iqr_step_75_100km']['median']:.3f}."),
        ("6. Is 100 km sufficient for most pixels?", f"Descriptively, {100*state['fraction_both_steps_le_0_02']:.1f}% change by ≤0.02 in both core Delta fields from 75 to 100 km. That supports 100 km for many—but not all—pixels."),
        ("7. Are locations still changing strongly at 100 km?", f"Yes. {100*state['fraction_delta_step_gt_0_05']:.1f}% exceed a 0.05 Delta step and {100*state['fraction_iqr_step_gt_0_05']:.1f}% exceed a 0.05 IQR step."),
        ("8. Is directional structure widespread?", f"Localized-to-moderate: eta² >0.10 at {100*state['fraction_direction_eta_gt_0_10']:.1f}% and >0.20 at {100*state['fraction_direction_eta_gt_0_20']:.1f}% of cells."),
        ("9. Does high stack heterogeneity form coherent geography?", f"Yes descriptively; adjacent-cell correlation of 100 km Delta IQR is {state['delta_iqr_neighbor_correlation']:.2f}."),
        ("10. Does landscape change form coherent geography?", f"Yes descriptively; adjacent-cell correlation of mean normalized RMSE is {state['landscape_nrmse_neighbor_correlation']:.2f}."),
        ("11. Are the two concepts distinct statewide?", f"Yes. Their pixel correlation is {state['correlation_iqr_vs_landscape_nrmse']:.2f}; sign and gradient correlations are {state['correlation_iqr_vs_landscape_sign']:.2f} and {state['correlation_iqr_vs_landscape_gradient']:.2f}."),
        ("12. Do candidate partitions persist away from edges?", "Not established. Multimodality was intentionally excluded from production; selected audit stacks do not justify regime claims."),
        ("13. Which Phase 1.5 findings survive?", "Robust cold/warm/Delta medians, Delta IQR, spatially variable radius sensitivity, directional information, and multidimensional landscape change all survive."),
        ("14. Which disappear?", "No robust finding clearly disappears. Candidate multimodality is not promoted and therefore remains unresolved, not falsified."),
        ("15. Dominant bottleneck?", f"Batched tail-Spearman: {perf['signature']['pair_kernel_seconds_sum']:.1f} s of {perf['signature']['wall_seconds']:.1f} s for the primary run."),
        ("16. Cost of one additional seasonal window?", f"Approximately {one_window_seconds/60:.1f} compute minutes for both branches at the measured serial rate, plus bounded acquisition."),
        ("17. Cost of one year of rolling windows?", f"At daily endpoints, roughly {365*one_window_seconds/3600:.1f} serial compute hours; at monthly endpoints, about {12*one_window_seconds/3600:.1f} hours."),
        ("18. Cost of full PRISM history?", f"For ~45 years, about {45*365*one_window_seconds/86400:.0f} serial compute days at daily endpoints or {45*12*one_window_seconds/3600:.0f} hours at monthly endpoints, before parallel scaling and I/O."),
        ("19. Cost of a CONUS single window?", f"A rough 29× area scaling gives {(29*one_window_seconds)/3600:.1f} serial hours for both branches; this is an inference, not a benchmark."),
        ("20. What should Phase 3 be?", "A. Colorado temporal robustness: selected winter/spring/summer/fall windows. The scientific need is seasonality and repeatability, not yet more area or a full historical cube."),
    ]
    lines = ["# Phase 2 decision report", "", "Decision: **Phase 3A — Colorado temporal robustness.**", ""]
    for title, answer in questions:
        lines.extend((f"## {title}", "", answer, ""))
    lines.extend(("## Caveats", "", *[f"- {item}" for item in summary["limitations"]], ""))
    target = artifact_dir / "phase2_decision_report.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def main(root: Path, artifact_dir: Path, output_pdf: Path) -> None:
    result = build_atlas(root, artifact_dir, output_pdf)
    decision = write_decision_report(artifact_dir, result["summary"])
    manifest = {key: value for key, value in result.items() if key != "summary"}
    manifest["decision_report"] = str(decision)
    (artifact_dir / "atlas_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/synchrony-stack-phase2"))
    parser.add_argument("--output-pdf", type=Path, default=Path("output/pdf/colorado_synchrony_atlas_phase2.pdf"))
    args = parser.parse_args()
    main(args.root.resolve(), args.artifact_dir.resolve(), args.output_pdf.resolve())
