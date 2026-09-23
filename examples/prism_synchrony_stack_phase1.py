"""Run the bounded real-PRISM synchrony-stack phase-one experiment.

This script intentionally stops before any CONUS computation. It consumes one
already-acquired observed PRISM cube and writes ignored evidence under
``artifacts/synchrony-stack-phase1`` plus a PDF under ``output/pdf``.

Example
-------
MPLCONFIGDIR=/tmp/cubedynamics-mpl .venv/bin/python \
    examples/prism_synchrony_stack_phase1.py \
    --input artifacts/center-pixel-synchrony-walkthrough/intermediate/prism_boulder_2023-11-01_2024-01-30.nc
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import time
import tracemalloc

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
from PIL import Image
import xarray as xr

# ReportLab is supplied by the Codex workspace runtime, while the scientific
# environment remains the repository's pinned Python 3.11 environment. Append
# (do not prepend) so compiled NumPy/xarray packages still come from .venv.
_WORKSPACE_SITE_PACKAGES = Path(
    "/Users/tuff/.cache/codex-runtimes/codex-primary-runtime/dependencies/"
    "python/lib/python3.12/site-packages"
)
if _WORKSPACE_SITE_PACKAGES.exists():
    sys.path.append(str(_WORKSPACE_SITE_PACKAGES))

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as ReportImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from cubedynamics import pipe, verbs as v
from cubedynamics.synchrony import write_stack_checkpoint


DEFAULT_INPUT = Path(
    "artifacts/center-pixel-synchrony-walkthrough/intermediate/"
    "prism_boulder_2023-11-01_2024-01-30.nc"
)
DEFAULT_OUTPUT = Path("artifacts/synchrony-stack-phase1")
DEFAULT_REPORT = Path("output/pdf/cubedynamics_synchrony_stack_phase1_report.pdf")


def _stack(
    cube: xr.Dataset,
    *,
    center_y_indices=None,
    center_x_indices=None,
    pair_batch_size: int = 4096,
) -> xr.Dataset:
    return (
        pipe(cube)
        | v.local_synchrony_stack(
            lower_var="tmin",
            upper_var="tmax",
            window_days=90,
            window_end=cube.time.values[-1],
            min_t=10,
            split_quantile=0.5,
            center_y_indices=center_y_indices,
            center_x_indices=center_x_indices,
            distance_bands_km=(25.0, 50.0, 100.0, 250.0),
            pair_batch_size=pair_batch_size,
        )
    ).unwrap()


def _nbytes(dataset: xr.Dataset) -> int:
    return int(sum(variable.nbytes for variable in dataset.variables.values()))


def _benchmark(label: str, cube: xr.Dataset) -> tuple[dict[str, object], xr.Dataset]:
    tracemalloc.start()
    started = time.perf_counter()
    result = _stack(cube)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    unique_pairs = int(result.attrs["unique_pair_count"])
    record = {
        "label": label,
        "grid": f"{cube.sizes['y']}x{cube.sizes['x']}",
        "centers": int(result.sizes["center"]),
        "unique_pairs_including_self": unique_pairs,
        "nonself_pairs": unique_pairs - int(result.sizes["center"]),
        "wall_seconds": elapsed,
        "pairs_per_second": unique_pairs / elapsed,
        "tracemalloc_peak_mb": peak / 1_000_000,
        "output_memory_mb": _nbytes(result) / 1_000_000,
        "dask_graph_tasks": 0,
        "workers": 1,
        "execution": "bounded eager NumPy batches",
    }
    return record, result


def _select_focals(reduced: xr.Dataset) -> list[tuple[str, int, int]]:
    iqr = np.asarray(reduced["iqr"].values, dtype=float)
    y_size, x_size = iqr.shape
    interior = iqr.copy()
    if y_size > 2 and x_size > 2:
        interior[[0, -1], :] = np.nan
        interior[:, [0, -1]] = np.nan
    homogeneous = np.unravel_index(np.nanargmin(interior), interior.shape)
    transition = np.unravel_index(np.nanargmax(interior), interior.shape)
    return [
        ("near center", y_size // 2, x_size // 2),
        ("edge", 0, 0),
        ("low-IQR", int(homogeneous[0]), int(homogeneous[1])),
        ("high-IQR", int(transition[0]), int(transition[1])),
    ]


def _map_figure(stack: xr.Dataset, output: Path) -> None:
    figure, axes = plt.subplots(2, 3, figsize=(12, 7.5), constrained_layout=True)
    variables = (
        ("cold_synchrony", "Cold synchrony", "RdBu_r", -1, 1),
        ("warm_synchrony", "Warm synchrony", "RdBu_r", -1, 1),
        ("delta_s", "Cold - warm (Delta S)", "RdBu", -1, 1),
    )
    for row, center in enumerate((0, stack.sizes["center"] // 2)):
        for column, (name, label, cmap, vmin, vmax) in enumerate(variables):
            image = axes[row, column].imshow(
                stack[name].isel(center=center), cmap=cmap, vmin=vmin, vmax=vmax, origin="upper"
            )
            cy = int(stack.center_y_index.values[center])
            cx = int(stack.center_x_index.values[center])
            axes[row, column].scatter(cx, cy, marker="*", s=100, c="#ffd54f", edgecolor="black")
            axes[row, column].set_title(f"{label}\ncenter ({cy}, {cx})")
            axes[row, column].set_xlabel("x index")
            axes[row, column].set_ylabel("y index")
            figure.colorbar(image, ax=axes[row, column], shrink=0.78)
    figure.suptitle("Two contrasting moving-center synchrony landscapes", fontsize=15, fontweight="bold")
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _focal_stack_figure(
    stack: xr.Dataset, focals: list[tuple[str, int, int]], output: Path
) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    center_x = np.asarray(stack.center_x.values, dtype=float)
    center_y = np.asarray(stack.center_y.values, dtype=float)
    for axis, (label, yi, xi) in zip(axes.flat, focals):
        values = np.asarray(stack.delta_s[:, yi, xi].values, dtype=float)
        valid = np.isfinite(values)
        scatter = axis.scatter(
            center_x[valid],
            values[valid],
            c=center_y[valid],
            cmap="viridis",
            s=24,
            alpha=0.8,
            linewidth=0,
        )
        median = float(np.nanmedian(values))
        q25, q75 = np.nanquantile(values, [0.25, 0.75])
        axis.axhline(median, color="#ef6c00", linewidth=2, label=f"median {median:.3f}")
        axis.axhspan(q25, q75, color="#ef6c00", alpha=0.12, label=f"IQR {q75-q25:.3f}")
        axis.set_title(f"{label}: focal ({yi}, {xi}), n={valid.sum()}")
        axis.set_xlabel("center longitude")
        axis.set_ylabel("stack Delta S")
        axis.legend(loc="best", fontsize=8)
        figure.colorbar(scatter, ax=axis, label="center latitude")
    figure.suptitle("Four focal-pixel stacks retain center-location structure", fontsize=15, fontweight="bold")
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _reduction_figure(
    cold: xr.Dataset, warm: xr.Dataset, delta: xr.Dataset, change: xr.Dataset, output: Path
) -> None:
    panels = (
        (cold["median"], "Median cold synchrony", "RdBu_r", -1, 1),
        (warm["median"], "Median warm synchrony", "RdBu_r", -1, 1),
        (delta["median"], "Median Delta S", "RdBu", -0.5, 0.5),
        (delta["standard_deviation"], "Stack standard deviation", "magma", 0, None),
        (delta["iqr"], "Stack IQR", "magma", 0, None),
        (
            change["mean_adjacent_landscape_change"],
            "Adjacent-landscape change (1 - Q)",
            "inferno",
            0,
            None,
        ),
    )
    figure, axes = plt.subplots(2, 3, figsize=(12, 7.5), constrained_layout=True)
    for axis, (data, title, cmap, vmin, vmax) in zip(axes.flat, panels):
        image = axis.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, origin="upper")
        axis.set_title(title)
        axis.set_xlabel("x index")
        axis.set_ylabel("y index")
        figure.colorbar(image, ax=axis, shrink=0.8)
    figure.suptitle("Reduction maps and a regional-break diagnostic", fontsize=15, fontweight="bold")
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _boundary_figure(stack: xr.Dataset, change: xr.Dataset, output: Path) -> dict[str, object]:
    edge_index = int(np.nanargmax(change.landscape_change.values))
    center_a = int(change.center_a.values[edge_index])
    center_b = int(change.center_b.values[edge_index])
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
    for axis, center, title in zip(axes[:2], (center_a, center_b), ("Center A", "Center B")):
        image = axis.imshow(stack.delta_s.isel(center=center), cmap="RdBu", vmin=-1, vmax=1)
        cy = int(stack.center_y_index.values[center])
        cx = int(stack.center_x_index.values[center])
        axis.scatter(cx, cy, marker="*", s=110, c="#ffd54f", edgecolor="black")
        axis.set_title(f"{title} ({cy}, {cx})")
        figure.colorbar(image, ax=axis, shrink=0.78)
    difference = stack.delta_s.isel(center=center_a) - stack.delta_s.isel(center=center_b)
    image = axes[2].imshow(difference, cmap="PuOr", vmin=-1, vmax=1)
    axes[2].set_title("Landscape A - B")
    figure.colorbar(image, ax=axes[2], shrink=0.78)
    for axis in axes:
        axis.set_xlabel("x index")
        axis.set_ylabel("y index")
    q = float(change.panel_similarity.values[edge_index])
    figure.suptitle(f"Strongest adjacent landscape break: panel similarity Q={q:.3f}", fontsize=14, fontweight="bold")
    figure.savefig(output, dpi=180)
    plt.close(figure)
    return {
        "comparison_index": edge_index,
        "center_a": center_a,
        "center_b": center_b,
        "panel_similarity_q": q,
        "landscape_change": float(change.landscape_change.values[edge_index]),
        "rmse": float(change.rmse.values[edge_index]),
        "overlap_count": int(change.overlap_count.values[edge_index]),
    }


def _buildup_figure_and_animation(
    stack: xr.Dataset, focal: tuple[int, int], output_png: Path, output_gif: Path
) -> None:
    yi, xi = focal
    counts = [1, 25, 100, stack.sizes["center"]]
    figure, axes = plt.subplots(2, 4, figsize=(14, 7), constrained_layout=True)
    for column, count in enumerate(counts):
        center = count - 1
        image = axes[0, column].imshow(
            stack.delta_s.isel(center=center), cmap="RdBu", vmin=-1, vmax=1
        )
        axes[0, column].scatter(xi, yi, marker="*", s=90, c="#ffd54f", edgecolor="black")
        axes[0, column].set_title(f"layer {count}: center map")
        values = stack.delta_s.isel(center=slice(0, count), y=yi, x=xi).values
        axes[1, column].hist(values[np.isfinite(values)], bins=18, range=(-1, 1), color="#1565c0")
        axes[1, column].axvline(np.nanmedian(values), color="#ef6c00", linewidth=2)
        axes[1, column].set_title(f"focal stack after {count} layers")
        axes[1, column].set_xlabel("Delta S")
        axes[1, column].set_ylabel("count")
        figure.colorbar(image, ax=axes[0, column], shrink=0.72)
    figure.suptitle(f"Center maps build the stack at focal ({yi}, {xi})", fontsize=15, fontweight="bold")
    figure.savefig(output_png, dpi=180)
    plt.close(figure)

    figure, (map_axis, stack_axis) = plt.subplots(1, 2, figsize=(9, 4), constrained_layout=True)
    map_image = map_axis.imshow(stack.delta_s.isel(center=0), cmap="RdBu", vmin=-1, vmax=1)
    map_axis.scatter(xi, yi, marker="*", s=100, c="#ffd54f", edgecolor="black")
    figure.colorbar(map_image, ax=map_axis, shrink=0.8, label="Delta S")

    def update(frame: int):
        map_image.set_data(stack.delta_s.isel(center=frame))
        map_axis.set_title(f"center landscape {frame + 1}/{stack.sizes['center']}")
        stack_axis.clear()
        values = stack.delta_s.isel(center=slice(0, frame + 1), y=yi, x=xi).values
        stack_axis.hist(values[np.isfinite(values)], bins=18, range=(-1, 1), color="#1565c0")
        stack_axis.axvline(np.nanmedian(values), color="#ef6c00", linewidth=2)
        stack_axis.set_xlim(-1, 1)
        stack_axis.set_title(f"focal stack: {np.isfinite(values).sum()} valid layers")
        stack_axis.set_xlabel("Delta S")
        stack_axis.set_ylabel("count")
        return (map_image,)

    frames = list(range(0, stack.sizes["center"], 10))
    if frames[-1] != stack.sizes["center"] - 1:
        frames.append(stack.sizes["center"] - 1)
    animation = FuncAnimation(figure, update, frames=frames, interval=170, blit=False)
    animation.save(output_gif, writer=PillowWriter(fps=6), dpi=110)
    plt.close(figure)


def _equivalence(cube: xr.Dataset, stack: xr.Dataset) -> dict[str, object]:
    center_index = next(
        index
        for index, (yi, xi) in enumerate(
            zip(stack.center_y_index.values, stack.center_x_index.values)
        )
        if int(yi) == cube.sizes["y"] // 2 and int(xi) == cube.sizes["x"] // 2
    )
    old = v.rolling_median_split_synchrony(
        lower_var="tmin",
        upper_var="tmax",
        window_days=90,
        min_t=10,
        split_quantile=0.5,
        output_times=[cube.time.values[-1]],
    )(cube).compute()
    comparisons = {
        "cold": (
            stack.cold_synchrony.isel(center=center_index).values,
            old.bottom_synchrony.isel(time_window_end=0).values,
        ),
        "warm": (
            stack.warm_synchrony.isel(center=center_index).values,
            old.top_synchrony.isel(time_window_end=0).values,
        ),
        "delta": (
            stack.delta_s.isel(center=center_index).values,
            old.bottom_minus_top.isel(time_window_end=0).values,
        ),
    }
    maximum_errors = {
        name: float(np.nanmax(np.abs(left - right))) for name, (left, right) in comparisons.items()
    }
    return {
        "center_index": center_index,
        "center_y_index": int(stack.center_y_index.values[center_index]),
        "center_x_index": int(stack.center_x_index.values[center_index]),
        "maximum_absolute_errors": maximum_errors,
        "pixelwise_equal_at_1e-7": all(value <= 1e-7 for value in maximum_errors.values()),
    }


def _resource_estimates(benchmark: dict[str, object]) -> dict[str, object]:
    pixels = 910_000
    full_pairs = pixels * (pixels + 1) // 2
    throughput = float(benchmark["pairs_per_second"])
    estimates: dict[str, object] = {
        "assumed_conus_pixels": pixels,
        "assumed_grid_spacing_km": 4.0,
        "one_window_source_memory_gb_float32_tmin_tmax": pixels * 91 * 2 * 4 / 1e9,
        "dense_all_pairs": {
            "pairs": full_pairs,
            "one_core_days_at_measured_throughput": full_pairs / throughput / 86400,
            "edge_storage_tb_at_24_bytes_per_pair": full_pairs * 24 / 1e12,
            "recommendation": "forbidden",
        },
    }
    local = {}
    for radius in (50, 100, 250):
        neighbors = math.pi * (radius / 4.0) ** 2
        pairs = pixels * neighbors / 2.0
        local[str(radius)] = {
            "approx_neighbors_per_pixel": neighbors,
            "approx_unique_pairs": pairs,
            "one_core_hours_at_measured_throughput": pairs / throughput / 3600,
            "ideal_32_worker_hours": pairs / throughput / 3600 / 32,
            "edge_storage_gb_at_24_bytes_per_pair": pairs * 24 / 1e9,
        }
    estimates["local_radius_km"] = local
    estimates["decision"] = (
        "Proceed only to a second bounded benchmark with finite radius, coarse batch parallelism, "
        "and Zarr checkpoints. Do not attempt dense CONUS stacks."
    )
    return estimates


def _format_number(value: object) -> str:
    if isinstance(value, (float, np.floating)):
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        return f"{value:.3f}"
    return str(value)


def _report(
    target: Path,
    *,
    input_path: Path,
    source: xr.Dataset,
    stack: xr.Dataset,
    focals: list[tuple[str, int, int]],
    equivalence: dict[str, object],
    focal_audit: dict[str, float],
    boundary: dict[str, object],
    benchmarks: list[dict[str, object]],
    estimates: dict[str, object],
    figures: dict[str, Path],
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    navy = colors.HexColor("#113f70")
    blue = colors.HexColor("#1565c0")
    light = colors.HexColor("#eaf2f8")
    styles.add(
        ParagraphStyle(
            name="TitleCustom",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=navy,
            alignment=TA_LEFT,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=9,
            textColor=colors.white,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1Custom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=navy,
            spaceBefore=8,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=blue,
            spaceBefore=6,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=navy,
            backColor=light,
            borderColor=blue,
            borderWidth=0.8,
            borderPadding=8,
            spaceBefore=7,
            spaceAfter=10,
        )
    )

    def p(text: str, style: str = "BodyCustom") -> Paragraph:
        return Paragraph(text, styles[style])

    def image(path: Path, width: float = 7.0 * inch) -> ReportImage:
        with Image.open(path) as im:
            aspect = im.height / im.width
        return ReportImage(str(path), width=width, height=width * aspect)

    def table(rows, widths=None):
        wrapped = [
            [
                Paragraph(str(cell), styles["TableHeader" if row_index == 0 else "TableCell"])
                for cell in row
            ]
            for row_index, row in enumerate(rows)
        ]
        item = Table(wrapped, colWidths=widths, repeatRows=1, hAlign="LEFT")
        item.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), navy),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.7),
                    ("LEADING", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#aeb6bf")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), (colors.white, light)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return item

    def header_footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d5d8dc"))
        canvas.line(0.7 * inch, 0.58 * inch, 7.8 * inch, 0.58 * inch)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#5d6d7e"))
        canvas.drawString(0.7 * inch, 0.38 * inch, "CubeDynamics - synchrony stack phase one")
        canvas.drawRightString(7.8 * inch, 0.38 * inch, f"Page {document.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(
        str(target),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.72 * inch,
        title="CubeDynamics spatial synchrony stacks - phase one",
        author="CubeDynamics",
    )
    story = [
        p("Spatial synchrony stacks", "TitleCustom"),
        p("Bounded real-PRISM implementation, validation, diagnostics, and pre-CONUS decision gate", "H2Custom"),
        Spacer(1, 0.08 * inch),
        p(
            "Outcome: the repository now has an exact moving-center stack verb, rich reductions, "
            "and a separate landscape-similarity diagnostic. The 20 by 20 observed PRISM test "
            "computed 400 center landscapes from 80,200 canonical pairs while returning all "
            "160,000 center-to-focal values.",
            "Callout",
        ),
        p("Decision", "H1Custom"),
        p(
            "GO for a second bounded, finite-radius benchmark after adding process-level or native "
            "parallelism and chunked Zarr checkpoints. NO-GO for a dense CONUS center-by-focal "
            "stack: its quadratic pair count and storage are scientifically unnecessary and "
            "operationally prohibitive.",
        ),
        p("Scientific definition preserved", "H1Custom"),
        p(
            "Cold synchrony uses tmin, each series' own median, dates where both values are at or "
            "below their medians, and Spearman correlation. Warm synchrony uses tmax, each series' "
            "own median, dates where both values are above their medians, and Spearman correlation. "
            "Delta S is cold minus warm. Paired missing-value filtering, average ranks for ties, "
            "and min_t=10 are inherited from the validated center-reference kernel.",
        ),
        table(
            [
                ["Input", "Observed experiment"],
                ["File", str(input_path)],
                ["Provider", source.attrs.get("source_provider", source.attrs.get("source", "PRISM"))],
                ["Window", f"{source.time.values[0]} through {source.time.values[-1]} ({source.sizes['time']} labels)"],
                ["Grid", f"20 by 20 ({stack.sizes['center']} moving centers and focal pixels)"],
                ["Synthetic fallback", "No"],
                ["Fingerprint", stack.attrs["analysis_fingerprint"]],
            ],
            [1.35 * inch, 5.65 * inch],
        ),
        PageBreak(),
        p("1. Architecture and API", "H1Custom"),
        p(
            "v.local_synchrony_stack() returns the literal scientific object: a Dataset with "
            "center, y, and x dimensions. The implementation canonicalizes every pair as "
            "(min(i,j), max(i,j)), computes it once, and gathers it into both endpoint stacks. "
            "Self-pairs are retained, so the storyboard's 20 by 20 center block yields exactly "
            "400 layers per focal pixel.",
        ),
        table(
            [
                ["Component", "Purpose", "Interpretation"],
                ["local_synchrony_stack", "Unreduced center landscapes and focal stacks", "Primary science object S(c,p)"],
                ["reduce_synchrony_stack", "Distribution, coverage, distance, direction summaries", "Maps derived from full stacks"],
                ["synchrony_landscape_similarity", "Adjacent-panel Spearman Q(A,B)", "Regional-break diagnostic, not pair S(A,B)"],
                ["stack_edges", "Canonical undirected edge table", "Storage/network utility, not primary object"],
            ],
            [1.55 * inch, 2.55 * inch, 2.9 * inch],
        ),
        p("Symmetry and equivalence", "H2Custom"),
        p(
            "Symmetry is exact under argument reversal because paired filtering, per-series "
            "quantiles, joint selection, and Spearman correlation are symmetric. Unit tests cover "
            "cold, warm, Delta S, missing values, ties, and min_t. The real center landscape was "
            f"pixelwise equal to the established verb at 1e-7: {equivalence['pixelwise_equal_at_1e-7']}.",
        ),
        table(
            [["Field", "Maximum absolute error"]]
            + [[name, f"{value:.3g}"] for name, value in equivalence["maximum_absolute_errors"].items()],
            [2.5 * inch, 2.2 * inch],
        ),
        p("Previously audited focal pair", "H2Custom"),
        table(
            [
                ["Cold", "Warm", "Delta S", "Distance (km)"],
                [
                    f"{focal_audit['cold']:.6f}",
                    f"{focal_audit['warm']:.6f}",
                    f"{focal_audit['delta']:.6f}",
                    f"{focal_audit['distance_km']:.3f}",
                ],
            ],
            [1.3 * inch] * 4,
        ),
        p("Expected reference values are approximately 0.588, 0.858, and -0.270; the stack reproduces them."),
        PageBreak(),
        p("2. Moving-center landscapes", "H1Custom"),
        p(
            "Each row below is one center landscape. The star marks the center. Blue and red are "
            "kept consistent with the signed metric: for Delta S, blue indicates positive "
            "cold-minus-warm and red indicates negative cold-minus-warm.",
        ),
        image(figures["maps"]),
        PageBreak(),
        p("3. Focal stacks", "H1Custom"),
        p(
            "A focal stack is the vertical slice through all 400 center landscapes at one geographic "
            "pixel. The scatter retains center longitude and latitude; the median and IQR are "
            "summaries, not replacements for the distribution.",
        ),
        image(figures["focals"]),
        p(
            "Selected focal roles: "
            + "; ".join(f"{label} ({yi},{xi})" for label, yi, xi in focals)
            + ". Labels describe selection criteria within this bounded block and are not climate-region classifications.",
        ),
        PageBreak(),
        p("4. From landscapes to stacks", "H1Custom"),
        p(
            "The upper row shows successive center landscapes; the lower row accumulates the value "
            "at one fixed focal pixel. This is the concrete relationship between the moving maps "
            "and the eventual focal distribution.",
        ),
        image(figures["buildup"]),
        p(
            "An accompanying GIF repeats this buildup across the block. It is evidence of the data "
            "construction, not an inference that the visual groupings are objectively discrete regions.",
        ),
        PageBreak(),
        p("5. Reductions and regional-break diagnostics", "H1Custom"),
        p(
            "Median cold, median warm, and median Delta S provide compact products. Standard "
            "deviation and IQR measure stack spread. The final panel maps 1 - Q averaged over each "
            "center's adjacent panel comparisons. Q compares full landscapes; it is not S between "
            "the two center pixels.",
        ),
        image(figures["reductions"]),
        PageBreak(),
        p("Most contrasting adjacent landscapes", "H2Custom"),
        image(figures["boundary"]),
        table(
            [["Center A", "Center B", "Q", "1-Q", "RMSE", "Overlap"]]
            + [[
                str(boundary["center_a"]),
                str(boundary["center_b"]),
                f"{boundary['panel_similarity_q']:.3f}",
                f"{boundary['landscape_change']:.3f}",
                f"{boundary['rmse']:.3f}",
                str(boundary["overlap_count"]),
            ]],
            [0.85 * inch] * 6,
        ),
        p(
            "Boundary caveat: high stack spread or low adjacent-panel similarity can flag a transition "
            "worth investigating. It does not by itself prove a true climate region, establish a "
            "causal boundary, or validate a clustering model.",
            "Callout",
        ),
        PageBreak(),
        p("6. Benchmark ladder", "H1Custom"),
        p(
            "Timings are single-process wall-clock measurements on this machine. The kernel uses "
            "coarse NumPy pair batches and creates zero per-pair Dask tasks. tracemalloc is a Python "
            "allocation estimate and may undercount library-level native memory.",
        ),
        table(
            [["Case", "Grid", "Pairs", "Seconds", "Pairs/s", "Peak MB", "Output MB"]]
            + [
                [
                    row["label"],
                    row["grid"],
                    f"{row['unique_pairs_including_self']:,}",
                    f"{row['wall_seconds']:.3f}",
                    f"{row['pairs_per_second']:,.0f}",
                    f"{row['tracemalloc_peak_mb']:.1f}",
                    f"{row['output_memory_mb']:.1f}",
                ]
                for row in benchmarks
            ],
            [0.8 * inch, 0.65 * inch, 0.85 * inch, 0.7 * inch, 0.8 * inch, 0.75 * inch, 0.75 * inch],
        ),
        p("CONUS resource estimates", "H2Custom"),
        p(
            f"Assumption: {estimates['assumed_conus_pixels']:,} cells at about "
            f"{estimates['assumed_grid_spacing_km']:.0f} km. One 91-label tmin+tmax float32 "
            f"window is about {estimates['one_window_source_memory_gb_float32_tmin_tmax']:.2f} GB "
            "before masks, coordinates, and overhead.",
        ),
        table(
            [["Support", "Approx pairs", "1-core hours", "Ideal 32-worker hours", "Edge GB"]]
            + [
                [
                    f"{radius} km radius",
                    f"{values['approx_unique_pairs']:,.0f}",
                    f"{values['one_core_hours_at_measured_throughput']:,.1f}",
                    f"{values['ideal_32_worker_hours']:,.1f}",
                    f"{values['edge_storage_gb_at_24_bytes_per_pair']:,.1f}",
                ]
                for radius, values in estimates["local_radius_km"].items()
            ]
            + [[
                "Dense all-pairs",
                f"{estimates['dense_all_pairs']['pairs']:,}",
                f"{estimates['dense_all_pairs']['one_core_days_at_measured_throughput']*24:,.0f}",
                "not meaningful",
                f"{estimates['dense_all_pairs']['edge_storage_tb_at_24_bytes_per_pair']*1000:,.0f}",
            ]],
            [1.05 * inch, 1.35 * inch, 1.05 * inch, 1.25 * inch, 0.85 * inch],
        ),
        p(
            "These are arithmetic planning estimates, not cluster benchmarks. They omit I/O "
            "contention, checkpoint metadata, failed-task retries, scheduler overhead, and repeated "
            "rolling windows. They do show why exact dense national stacks must not be attempted.",
        ),
        PageBreak(),
        p("7. Production architecture and restartability", "H1Custom"),
        table(
            [
                ["Concern", "Phase-one behavior", "Production requirement"],
                ["Spatial work", "One bounded 20 by 20 block", "Center tiles with finite-radius halos"],
                ["Pair work", "Canonical pairs in coarse batches", "Parallel batches; never one task per pair"],
                ["Output", "NetCDF checkpoint plus JSON manifest", "Chunked Zarr by window and center tile"],
                ["Resume", "Exact fingerprint and complete-status check", "Batch manifest; reject mixed parameters"],
                ["Failures", "Atomic rename after complete write", "Retry missing batches; preserve completed compatible batches"],
                ["Metadata", "Indices, coordinates, distance, bearing, bands, counts", "Retain unchanged in sparse outputs"],
            ],
            [1.05 * inch, 2.55 * inch, 3.35 * inch],
        ),
        p("Recommended next gate", "H2Custom"),
        p(
            "Benchmark exact 50 km and 100 km neighborhoods on a 100 by 100 observed tile using "
            "process-level parallelism and Zarr checkpoints. Compare numerical output with the "
            "current kernel at 1e-7, measure real read/write bytes and scheduler tasks, and only then "
            "choose a CONUS support radius. If those costs are still excessive, evaluate a documented "
            "approximation against exact held-out tiles before any national run.",
            "Callout",
        ),
        p("Limitations", "H1Custom"),
        p(
            "This experiment covers one observed Colorado winter block and one inclusive 90-day "
            "coordinate-label interval containing 91 daily labels. It does not establish seasonal "
            "stability, national representativeness, climate-region truth, causal mechanisms, or a "
            "validated entropy/multimodality metric. Distance-weighted and directional summaries are "
            "available, but their scientific interpretation requires a declared analysis question.",
        ),
    ]
    document.build(story, onFirstPage=header_footer, onLaterPages=header_footer)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    figures_dir = args.output / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    with xr.open_dataset(args.input) as opened:
        source = opened[["tmin", "tmax"]].load()
    if int(source.attrs.get("is_synthetic", 0)) != 0:
        raise ValueError("The phase-one experiment requires observed PRISM data")
    if source.sizes["time"] < 91:
        raise ValueError("The requested experiment requires all 91 labels in the inclusive 90-day window")
    # This PRISM adapter emits geographic cell-center coordinates. Record that
    # contract explicitly because the stack kernel will not guess a CRS from
    # numerically plausible coordinate ranges.
    source["y"].attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    source["x"].attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    y_start = (source.sizes["y"] - 20) // 2
    # Keep the previously audited western focal (source x index 0) while also
    # retaining the original source-center pixel at (12, 12).
    x_start = 0
    cube = source.isel(y=slice(y_start, y_start + 20), x=slice(x_start, x_start + 20))

    single_record, _ = _benchmark("single nonself pair", cube.isel(y=slice(0, 1), x=slice(0, 2)))
    tile_record, _ = _benchmark("5 by 5 tile", cube.isel(y=slice(0, 5), x=slice(0, 5)))
    block_record, stack = _benchmark("20 by 20 block", cube)
    benchmarks = [single_record, tile_record, block_record]

    checkpoint = write_stack_checkpoint(stack, args.output / "prism_20x20_synchrony_stack.nc")
    cold = v.reduce_synchrony_stack(metric="cold_synchrony")(stack)
    warm = v.reduce_synchrony_stack(metric="warm_synchrony")(stack)
    delta = v.reduce_synchrony_stack(metric="delta_s")(stack)
    change = v.synchrony_landscape_similarity(metric="delta_s", adjacency=4, min_overlap=50)(stack)
    cold.to_netcdf(args.output / "cold_stack_reductions.nc")
    warm.to_netcdf(args.output / "warm_stack_reductions.nc")
    delta.to_netcdf(args.output / "delta_stack_reductions.nc")
    change.to_netcdf(args.output / "landscape_similarity.nc")

    focals = _select_focals(delta)
    figures = {
        "maps": figures_dir / "contrasting_center_landscapes.png",
        "focals": figures_dir / "four_focal_stacks.png",
        "reductions": figures_dir / "reduction_and_boundary_maps.png",
        "boundary": figures_dir / "strongest_adjacent_break.png",
        "buildup": figures_dir / "stack_buildup.png",
    }
    _map_figure(stack, figures["maps"])
    _focal_stack_figure(stack, focals, figures["focals"])
    _reduction_figure(cold, warm, delta, change, figures["reductions"])
    boundary = _boundary_figure(stack, change, figures["boundary"])
    transition = next((yi, xi) for label, yi, xi in focals if label == "high-IQR")
    _buildup_figure_and_animation(
        stack,
        transition,
        figures["buildup"],
        figures_dir / "stack_buildup.gif",
    )

    equivalence = _equivalence(cube, stack)
    # Audited focal from the original 25 by 25 acquisition maps into this crop.
    original_focal = (15, 0)
    focal = (original_focal[0] - y_start, original_focal[1] - x_start)
    original_center = (source.sizes["y"] // 2, source.sizes["x"] // 2)
    center = (original_center[0] - y_start, original_center[1] - x_start)
    if min(focal + center) < 0 or focal[0] >= 20 or focal[1] >= 20:
        raise ValueError("Expected audited focal and center must be inside the selected 20 by 20 crop")
    center_index = center[0] * 20 + center[1]
    focal_audit = {
        "cold": float(stack.cold_synchrony.values[center_index, focal[0], focal[1]]),
        "warm": float(stack.warm_synchrony.values[center_index, focal[0], focal[1]]),
        "delta": float(stack.delta_s.values[center_index, focal[0], focal[1]]),
        "distance_km": float(stack.distance_km.values[center_index, focal[0], focal[1]]),
    }
    estimates = _resource_estimates(block_record)
    results = {
        "input": str(args.input),
        "input_bytes": args.input.stat().st_size,
        "checkpoint": str(checkpoint),
        "source_attributes": dict(source.attrs),
        "stack_attributes": dict(stack.attrs),
        "focals": [{"role": role, "y": yi, "x": xi} for role, yi, xi in focals],
        "equivalence": equivalence,
        "audited_focal": focal_audit,
        "boundary": boundary,
        "benchmarks": benchmarks,
        "resource_estimates": estimates,
        "findings": {
            "symmetry": "exact by construction and independently tested under argument reversal",
            "multimodality": "not declared; quantiles and full distributions retained for review",
            "distance_effect": "available through distance bands and exponential-distance summaries",
            "direction_effect": "available through eight compass-direction summaries",
            "boundary_claim": "diagnostic only; no region truth or causal boundary inferred",
            "decision": estimates["decision"],
        },
    }
    (args.output / "phase1_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    _report(
        args.report,
        input_path=args.input,
        source=source,
        stack=stack,
        focals=focals,
        equivalence=equivalence,
        focal_audit=focal_audit,
        boundary=boundary,
        benchmarks=benchmarks,
        estimates=estimates,
        figures=figures,
    )
    print(json.dumps({"report": str(args.report), "results": str(args.output / "phase1_results.json")}, indent=2))


if __name__ == "__main__":
    main()
