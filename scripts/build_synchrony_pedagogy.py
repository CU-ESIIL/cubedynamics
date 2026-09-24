#!/usr/bin/env python3
"""Build the visual-first synchrony discussion deck and companion materials.

The deck deliberately separates empirical evidence from conceptual teaching
figures.  Every empirical number is loaded from the current repository
artifacts at build time and recorded in a machine-readable manifest.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import textwrap
from typing import Callable, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath
import numpy as np
import pandas as pd
import xarray as xr

try:
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.pdfgen import canvas
except ImportError:  # pragma: no cover - local fallback for the bundled runtime
    bundled = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/"
        "lib/python3.12/site-packages"
    )
    sys.path.append(str(bundled))
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cubedynamics.stats.tails import one_tail_spearman  # noqa: E402


DEFAULT_FEASIBILITY = ROOT / "artifacts/relational-convolution-feasibility"
DEFAULT_STACK = ROOT / "artifacts/synchrony-stack-phase1/prism_20x20_synchrony_stack.nc"
DEFAULT_CUBE = ROOT / "artifacts/synchrony-stack-phase2/prism_colorado_plus_100km_20231101_20240130.nc"
DEFAULT_COLORADO = ROOT / "artifacts/synchrony-stack-phase2/colorado_synchrony_signature.nc"
DEFAULT_BOUNDARY = ROOT / "artifacts/synchrony-stack-phase2/colorado_boundary.geojson"
DEFAULT_OUTPUT = ROOT / "output/pdf/synchrony_from_pixels_to_planet.pdf"
DEFAULT_BUNDLE = ROOT / "output/synchrony_from_pixels_to_planet"

# Fixed visual semantics: cold is blue, warm is red, positive Delta (cold > warm)
# is blue, and negative Delta (warm > cold) is red.
INK = "#102A43"
MUTED = "#627D98"
LIGHT = "#EAF2F8"
BG = "#F7FAFC"
WHITE = "#FFFFFF"
COLD = "#2563EB"
COLD_LIGHT = "#BFDBFE"
WARM = "#DC2626"
WARM_LIGHT = "#FECACA"
GOLD = "#F2B134"
GREEN = "#16826C"
PURPLE = "#7C3AED"
QUESTION = "#596275"
GRID = "#CBD5E1"

DATA_LABEL_COLORS = {
    "REAL PRISM": COLD,
    "REAL GHCN": GREEN,
    "SYNTHETIC": PURPLE,
    "CONCEPTUAL": QUESTION,
}


PAGE_GUIDE: list[tuple[str, str, str, str, str]] = [
    ("When do two places experience climate together?", "Start with one real pair through time.", "Synchrony asks a conditional question, not ordinary all-date correlation.", "Thinking the two lines must have equal absolute temperatures.", "What part of these histories should count as unusually cold or warm?"),
    ("What counts as cold or warm?", "Show the current median-split semantics.", "Each location supplies its own pair-valid threshold inside the 90-day window.", "Assuming one shared temperature cutoff or a fixed global threshold.", "Should the reference distribution remain local when we scale up?"),
    ("Cold synchrony", "Make the cold calculation tangible.", "Rank correlation uses only dates where both TMIN values are at or below their own medians.", "Reading cold synchrony as frequency of cold days.", "What information is excluded when we condition on the joint cold tail?"),
    ("Warm synchrony", "Mirror the cold page exactly.", "Rank correlation uses only dates where both TMAX values are above their own medians.", "Assuming warm is simply the negative of cold.", "Why might the warm relationship differ from the cold relationship?"),
    ("Delta synchrony", "Introduce the signed contrast.", "Delta S = cold S - warm S; blue positive means cold dominates, red negative means warm dominates.", "Interpreting red as hot temperature rather than warm-dominant synchrony.", "Do we want Delta alone, or cold and warm beside it?"),
    ("One center, one neighbor", "Translate the pair into a spatial edge.", "One line on a map represents the calculation just learned.", "Treating the line as movement or heat flow.", "What changes if the neighbor moves but the center stays fixed?"),
    ("One center, many neighbors", "Repeat the same calculation around one center.", "Every spoke has cold, warm, and Delta values.", "Assuming neighboring spokes are independent replicates.", "Which neighbors should be inside the observation window?"),
    ("The local synchrony surface", "Replace spokes with one readable relational map.", "Every cell is its relationship with the same gold center.", "Calling it an ordinary map of conditions at each cell.", "What does a blue cell mean on this surface?"),
    ("Why this is not an ordinary climate map", "Contrast state and relation.", "A temperature map asks what is here; a synchrony surface asks how here relates to the center.", "Reading the relational color as degrees Celsius.", "What must the legend say to prevent that mistake?"),
    ("Move the center one pixel", "Introduce a second focal view without combining it.", "A new center produces a new complete surface.", "Assuming the second surface is a shifted copy.", "Which values are shared geography and which are new relationships?"),
    ("The two surfaces overlap", "Show vertical stacking in 3-D.", "The layers revisit absolute cells from different focal centers.", "Thinking layer height is a physical altitude or time axis.", "What does the vertical dimension index?"),
    ("Move again", "Grow the stack to four layers.", "Every focal center contributes another relational view.", "Thinking more layers mean repeated temperature observations.", "What stays fixed as the focal center moves?"),
    ("Fill a small grid of centers", "Scale the stack intuition to 25 centers.", "A 5 x 5 focal grid creates 25 overlapping local surfaces.", "Confusing center count with neighbor count.", "How many times can one absolute cell appear?"),
    ("The 20 x 20 thought experiment", "Bridge the toy stack to the real experiment.", "The real block has 400 focal centers and 400 complete surface cells per center.", "Treating 160,000 directed views as independent pairs.", "Why are there only 80,200 canonical pairs?"),
    ("What each stack element means", "Zoom into one absolute location q.", "The column contains S(p1,q), S(p2,q), ...: distinct relationships involving q.", "Calling the column repeated estimates of one intrinsic synchrony of q.", "What scientific question can this column answer?"),
    ("Relative view", "Define dx and dy only after the stack is understood.", "The focal center is always recentered at (0,0).", "Assuming equal offsets always refer to equal geography.", "What useful shape information does the relative view preserve?"),
    ("Move the center", "Show geography moving through a relative window.", "Fixed terrain changes offset when the center moves.", "Thinking the terrain itself moves.", "How would we put the fixed feature back in place?"),
    ("Absolute view", "Project the same values to latitude and longitude.", "Known geographic alignment strongly improved agreement in the current real block.", "Assuming alignment is learned or optimized.", "What does alignment reveal that relative coordinates hide?"),
    ("The central insight", "State the overlap hypothesis plainly.", "Overlap is informative only when relationship locations remain attached to geography.", "Assuming overlap automatically creates a final map.", "Which repeatable geographic signal should we extract next?"),
    ("Ordinary convolution", "Introduce the sliding-window analogy.", "A kernel slides, operates locally, and usually reduces immediately.", "Assuming our method uses the same weighted sum.", "Which part of this geometry resembles our moving center?"),
    ("Our relational version", "Map the analogy onto climate time series.", "The moving operation returns a complete relational surface instead of one scalar.", "Calling the operator a learned filter.", "What do we gain by retaining the neighborhood?"),
    ("Why this is not a CNN", "Set the analogy boundary.", "There are no trained filters, labels, backpropagation, or learned objective.", "Overselling machine learning novelty.", "What scientific assumption defines our operator?"),
    ("We have too much information", "Finally name the four-dimensional object.", "x,y index focal geography; dx,dy index the relative comparison location.", "Treating all four axes as ordinary spatial dimensions.", "Which dimensions can we reduce without losing the question?"),
    ("The tempting easy solution", "Demonstrate independent scalar reduction.", "Median/dispersion make maps but cannot recover the 2-D arrangement.", "Assuming a stable map is automatically an informative map.", "What geometry disappears in a median?"),
    ("Radial reduction", "Show a transparent structured baseline.", "Distance profiles retain more structure but privilege radius.", "Assuming synchrony must decay monotonically.", "What patterns would a radial summary miss?"),
    ("Radial + directional", "Show the strongest interpretable independent baseline.", "Direction improves reconstruction, but each surface is still summarized alone.", "Equating lower reconstruction error with a final scientific product.", "Is independent summarization enough when surfaces overlap?"),
    ("The overlap idea", "Introduce align-first analysis.", "Align neighboring surfaces geographically before choosing the reduction.", "Thinking this requires learned image registration.", "What geographic organization is repeatedly supported?"),
    ("What the feasibility experiment found", "Present the measured alignment comparison.", "Absolute alignment greatly improved Delta correlation and gradient agreement in one bounded block.", "Calling a feasibility result a production algorithm.", "Which result is most compelling, and what replication is missing?"),
    ("Local block", "Anchor scaling in the actual 20 x 20 experiment.", "The current relational object is real but geographically bounded.", "Mistaking the block for statewide evidence.", "What must remain invariant when we tile outward?"),
    ("Colorado", "Show the existing statewide signature product.", "The operation already supports tiled, halo-aware statewide execution.", "Treating one reduced signature as the final overlap product.", "Which statewide product should be compared with the new aligned view?"),
    ("CONUS", "Make continental scaling spatially concrete.", "Every pixel may be a focal center with a finite observation window.", "Imagining an all-to-all continental graph.", "What window and tiling strategy makes this bounded?"),
    ("The computational picture", "Show the scalable dataflow.", "Sparse canonical pairs, tiles, halos, streaming, checkpoints, and parallelism avoid dense 4-D memory.", "Assuming we must hold S(x,y,dx,dy) densely.", "Which intermediate is the durable scientific object?"),
    ("What would the final map mean?", "Separate candidate meanings.", "There may be several legitimate map products, not one arbitrary score.", "Combining magnitude, heterogeneity, coherence, asymmetry, and change prematurely.", "Which quantity should a primary map communicate?"),
    ("What does hot mean?", "Introduce climate-relative thresholds.", "The same absolute temperature can be extreme at one place and ordinary at another.", "Using one global Celsius cutoff by default.", "Relative to which distribution should hot and cold be defined?"),
    ("Relative extremes are a feature", "Explain the strength of local thresholds.", "Places in different climates can be compared by departures relative to themselves.", "Assuming local standardization removes all climate context.", "What scientifically meaningful cross-climate question does this enable?"),
    ("But relativity creates a new problem", "Separate synchrony from climatic similarity.", "Joint local warm tails can occur at very different absolute temperatures and regimes.", "Calling relative synchrony absolute similarity.", "What absolute context must travel with a synchrony map?"),
    ("Local versus global variance", "Make washout risk visible.", "Global variation can dwarf coherent regional departures.", "Normalizing once at the global level because it is convenient.", "Which local structures must remain visible by design?"),
    ("The normalization question", "Lay out options without selecting one.", "Local, regional, multiscale, dual, and hierarchical representations answer different questions.", "Presenting alternatives as mutually interchangeable.", "Which strategy best protects both comparability and local meaning?"),
    ("The answer depends on the reference frame", "Connect spatial and temporal definitions.", "Reference distribution and observation window can both change the answer.", "Treating a map as scale-free.", "Which reference choices must appear in every product's metadata?"),
    ("We should not search for one magic radius", "Use current window sensitivity honestly.", "Rmax is an observation limit, not a discovered synchrony scale.", "Selecting 40 km because one comparison looks stable.", "How stable should a result be as the window expands?"),
    ("Keep relationships first", "Protect the fundamental object.", "Canonical pair relationships can support multiple downstream views.", "Discarding pairs after making the first map.", "What minimal provenance must each pair retain?"),
    ("Then ask questions at multiple scales", "Show reuse rather than recomputation.", "Local, regional, continental, and global views can derive from the same pair layer where definitions permit.", "Assuming aggregation never changes interpretation.", "Which parts can be reused, and which thresholds may need recalculation?"),
    ("A multiscale synchrony map", "Offer a discussion hypothesis.", "A location may need local, regional, and broader-scale synchrony values.", "Reading the illustrative layers as an implemented method.", "Would a family of scale-indexed maps be more honest than one value?"),
    ("Relative + absolute", "Propose a two-axis interpretation.", "Pair relative-extreme synchrony with absolute climate-state similarity.", "Collapsing the two axes before understanding them.", "Which scientific cases occupy each quadrant?"),
    ("PRISM is a gridded model", "Introduce observational context.", "Raw stations provide a second route to the same pair calculations.", "Calling station comparisons independent before contribution status is known.", "What can stations test that the grid alone cannot?"),
    ("Build the same relationships from stations", "Show methodological comparability.", "The same cold, warm, and Delta definitions apply to station pairs.", "Rasterizing stations and hiding their irregular network.", "How should shared-station dependence affect inference?"),
    ("Current preliminary result", "Report station-grid agreement with limits.", "Cold and Delta agreement are encouraging; warm agreement is weak; all contribution statuses are unknown.", "Calling the comparison validation.", "Why might warm agreement be weak?"),
    ("Why stations matter", "Define a future external test.", "A real gridded geography should receive some support from raw observation relationships.", "Expecting every grid feature to have a nearby station test.", "What station density and holdout design would be convincing?"),
    ("The entire method on one page", "Rehearse the full narrative.", "Pairs become surfaces, surfaces overlap, geography aligns them, scale choices shape maps.", "Skipping from pair synchrony directly to a global score.", "At which arrow is the group least confident?"),
    ("What we know versus what we are deciding", "Separate evidence from open choices.", "The relational object is understood; the second-stage map definition is not settled.", "Treating an open design choice as a failure of the first-stage method.", "Which open choice should be resolved first?"),
    ("Question 1", "Focus discussion on pixel meaning.", "A final pixel may need one or several explicitly named quantities.", "Voting for a metric before stating the use case.", "What should one pixel on the final map mean?"),
    ("Question 2", "Focus discussion on global extremes.", "Hot and cold can be pixel-relative, region-relative, global, or multiscale.", "Assuming one definition serves every question.", "What should hot and cold mean globally?"),
    ("Question 3", "Focus discussion on preservation.", "Stability is insufficient if meaningful regional structure disappears.", "Equating smoothness with scientific quality.", "How much local variation must we preserve?"),
    ("Question 4", "Focus discussion on product family.", "Cold, warm, and Delta may each need multiple spatial scales.", "Forcing everything into a single map for convenience.", "Is there one synchrony map or a family of maps?"),
    ("Question 5", "End with falsifiable evidence criteria.", "Replication, window stability, synthetic recovery, stations, and independent products can build confidence.", "Ending with a claim that synchrony is solved.", "What would convince us the map is real?"),
]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feasibility", type=Path, default=DEFAULT_FEASIBILITY)
    parser.add_argument("--stack", type=Path, default=DEFAULT_STACK)
    parser.add_argument("--cube", type=Path, default=DEFAULT_CUBE)
    parser.add_argument("--colorado", type=Path, default=DEFAULT_COLORADO)
    parser.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--keep-existing-figures", action="store_true")
    return parser


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rank_corr(x: np.ndarray, y: np.ndarray) -> float:
    return float(pd.Series(x).corr(pd.Series(y), method="spearman"))


def load_empirical_evidence(
    feasibility_dir: Path = DEFAULT_FEASIBILITY,
    stack_path: Path = DEFAULT_STACK,
    cube_path: Path = DEFAULT_CUBE,
    colorado_path: Path = DEFAULT_COLORADO,
) -> dict[str, object]:
    """Load and recompute every empirical value shown in the deck."""

    feasibility_dir = Path(feasibility_dir)
    with xr.open_dataset(stack_path) as source:
        stack = source.load()
    with xr.open_dataset(cube_path) as source:
        cube = source.load()
    with xr.open_dataset(colorado_path) as source:
        colorado = source.load()

    # A stable, interpretable pair in the real 20 x 20 Front Range block.
    center = 210
    comparison_y, comparison_x = 9, 13
    comparison = comparison_y * stack.sizes["x"] + comparison_x
    center_lat = float(stack.center_y[center])
    center_lon = float(stack.center_x[center])
    comparison_lat = float(stack.y[comparison_y])
    comparison_lon = float(stack.x[comparison_x])
    a_tmin = cube.tmin.sel(y=center_lat, x=center_lon).values.astype(float)
    b_tmin = cube.tmin.sel(y=comparison_lat, x=comparison_lon).values.astype(float)
    a_tmax = cube.tmax.sel(y=center_lat, x=center_lon).values.astype(float)
    b_tmax = cube.tmax.sel(y=comparison_lat, x=comparison_lon).values.astype(float)
    cold, cold_n = one_tail_spearman(a_tmin, b_tmin, tail="lower", b=0.5, min_t=10)
    warm, warm_n = one_tail_spearman(a_tmax, b_tmax, tail="upper", b=0.5, min_t=10)
    delta = cold - warm
    np.testing.assert_allclose(cold, float(stack.cold_synchrony[center, comparison_y, comparison_x]), atol=1e-6)
    np.testing.assert_allclose(warm, float(stack.warm_synchrony[center, comparison_y, comparison_x]), atol=1e-6)
    np.testing.assert_allclose(delta, float(stack.delta_s[center, comparison_y, comparison_x]), atol=1e-6)
    assert cold_n == int(stack.cold_joint_count[center, comparison_y, comparison_x])
    assert warm_n == int(stack.warm_joint_count[center, comparison_y, comparison_x])

    similarity = pd.read_csv(feasibility_dir / "relative_vs_absolute_similarity.csv")
    delta40 = similarity.query("metric == 'delta_s' and radius_km == 40")
    representations = pd.read_csv(feasibility_dir / "baseline_representation_comparison.csv").set_index("representation")
    windows = pd.read_csv(feasibility_dir / "observation_window_sensitivity.csv")
    station_pairs = pd.read_csv(feasibility_dir / "station_prism_pair_synchrony.csv")
    station_manifest = pd.read_csv(feasibility_dir / "station_manifest.csv")
    station_provenance = json.loads((feasibility_dir / "station_qc_provenance.json").read_text())
    station_summary = station_provenance["pair_summary"]
    summary = json.loads((feasibility_dir / "feasibility_summary.json").read_text())

    values = {
        "pair": {
            "center": center,
            "comparison": comparison,
            "center_grid": [10, 10],
            "comparison_grid": [comparison_y, comparison_x],
            "center_lat": center_lat,
            "center_lon": center_lon,
            "comparison_lat": comparison_lat,
            "comparison_lon": comparison_lon,
            "distance_km": float(stack.distance_km[center, comparison_y, comparison_x]),
            "cold": cold,
            "warm": warm,
            "delta": delta,
            "cold_n": cold_n,
            "warm_n": warm_n,
            "tmin_medians": [float(np.nanmedian(a_tmin)), float(np.nanmedian(b_tmin))],
            "tmax_medians": [float(np.nanmedian(a_tmax)), float(np.nanmedian(b_tmax))],
        },
        "alignment": {
            "radius_km": 40,
            "pearson_relative": float(delta40.pearson_relative.median()),
            "pearson_absolute": float(delta40.pearson_absolute.median()),
            "gradient_relative": float(delta40.gradient_similarity_relative.median()),
            "gradient_absolute": float(delta40.gradient_similarity_absolute.median()),
        },
        "representations": {
            name: float(row.median_normalized_rmse)
            for name, row in representations.iterrows()
        },
        "representation_surface_count": int(representations.loc["radial_plus_directional", "surface_count"]),
        "windows": windows.to_dict(orient="records"),
        "stations": {
            "count": int(station_summary["station_count"]),
            "pair_count": int(station_summary["pair_count"]),
            "cold_r": float(station_summary["cold"]["correlation"]),
            "warm_r": float(station_summary["warm"]["correlation"]),
            "delta_r": float(station_summary["delta"]["correlation"]),
            "contribution_status": station_provenance["prism_contribution_status"],
            "example_pair": {
                "station_i": str(station_pairs.iloc[0].station_i),
                "station_j": str(station_pairs.iloc[0].station_j),
                "cold": float(station_pairs.iloc[0].station_cold),
                "warm": float(station_pairs.iloc[0].station_warm),
                "delta": float(station_pairs.iloc[0].station_delta),
            },
        },
        "stack": {
            "surface_count": int(stack.sizes["center"]),
            "cells_per_surface": int(stack.sizes["y"] * stack.sizes["x"]),
            "grid_y": int(stack.sizes["y"]),
            "grid_x": int(stack.sizes["x"]),
            "directed_views": int(summary["directed_relationship_count"]),
            "canonical_pairs": int(summary["canonical_pair_count"]),
            "window_start": str(stack.attrs["window_start"])[:10],
            "window_end": str(stack.attrs["window_end"])[:10],
            "window_days": int(stack.attrs["window_days"]),
            "split_quantile": float(stack.attrs["split_quantile"]),
            "minimum_tail_count": int(stack.attrs["min_time_points_per_tail"]),
        },
        "arrays": {
            "time": cube.time.values,
            "a_tmin": a_tmin,
            "b_tmin": b_tmin,
            "a_tmax": a_tmax,
            "b_tmax": b_tmax,
            "stack": stack,
            "colorado": colorado,
            "station_pairs": station_pairs,
            "station_manifest": station_manifest,
            "block_final_tmin": cube.tmin.sel(y=stack.y, x=stack.x).isel(time=-1).values.astype(float),
        },
        "sources": {
            "stack": {"path": str(Path(stack_path).relative_to(ROOT)), "sha256": _sha256(Path(stack_path))},
            "cube": {"path": str(Path(cube_path).relative_to(ROOT)), "sha256": _sha256(Path(cube_path))},
            "colorado": {"path": str(Path(colorado_path).relative_to(ROOT)), "sha256": _sha256(Path(colorado_path))},
            "similarity": {"path": str((feasibility_dir / "relative_vs_absolute_similarity.csv").relative_to(ROOT)), "sha256": _sha256(feasibility_dir / "relative_vs_absolute_similarity.csv")},
            "representations": {"path": str((feasibility_dir / "baseline_representation_comparison.csv").relative_to(ROOT)), "sha256": _sha256(feasibility_dir / "baseline_representation_comparison.csv")},
            "windows": {"path": str((feasibility_dir / "observation_window_sensitivity.csv").relative_to(ROOT)), "sha256": _sha256(feasibility_dir / "observation_window_sensitivity.csv")},
            "station_pairs": {"path": str((feasibility_dir / "station_prism_pair_synchrony.csv").relative_to(ROOT)), "sha256": _sha256(feasibility_dir / "station_prism_pair_synchrony.csv")},
            "station_provenance": {"path": str((feasibility_dir / "station_qc_provenance.json").relative_to(ROOT)), "sha256": _sha256(feasibility_dir / "station_qc_provenance.json")},
        },
    }
    return values


def serializable_empirical_values(evidence: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in evidence.items() if key != "arrays"}


def _page(title: str, subtitle: str, data_label: str, section: str) -> tuple[plt.Figure, plt.GridSpec]:
    fig = plt.figure(figsize=(11, 8.5), facecolor=BG)
    fig.text(0.055, 0.958, section.upper(), fontsize=8.5, color=MUTED, fontweight="bold", va="top")
    title_size = 22 if len(title) < 48 else 18.5
    fig.text(0.055, 0.922, title, fontsize=title_size, fontweight="bold", color=INK, va="top")
    if subtitle:
        fig.text(0.055, 0.873, subtitle, fontsize=10.2, color=MUTED, va="top")
    color = DATA_LABEL_COLORS[data_label]
    fig.text(
        0.945,
        0.944,
        data_label,
        ha="right",
        va="top",
        fontsize=8.2,
        color=WHITE,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", facecolor=color, edgecolor=color),
    )
    grid = fig.add_gridspec(12, 12, left=0.055, right=0.955, bottom=0.09, top=0.83, hspace=0.8, wspace=0.75)
    return fig, grid


def _finish(fig: plt.Figure, page: int, source: str) -> None:
    fig.text(0.055, 0.038, source, fontsize=7.2, color=MUTED)
    fig.text(0.945, 0.038, f"{page} / 55", ha="right", fontsize=8, color=MUTED)


def _save(fig: plt.Figure, page: int, figures_dir: Path, source: str) -> Path:
    _finish(fig, page, source)
    path = figures_dir / f"page_{page:02d}.png"
    fig.savefig(path, dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def _clean_axes(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.15, color=GRID)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)


def _callout(ax, x: float, y: float, text: str, color: str = INK, size: float = 13, ha: str = "center") -> None:
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha=ha,
        va="center",
        fontsize=size,
        color=color,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor=WHITE, edgecolor=color, linewidth=1.3),
    )


def _arrow(ax, xy1, xy2, color=MUTED, lw=2.0, style="-|>") -> None:
    ax.add_patch(FancyArrowPatch(xy1, xy2, arrowstyle=style, mutation_scale=15, lw=lw, color=color))


def _grid(ax, n: int, center: tuple[int, int], highlighted: Iterable[tuple[int, int]] = ()) -> None:
    ax.set_aspect("equal")
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(n - 0.5, -0.5)
    for y in range(n):
        for x in range(n):
            fc = "#DCE9F2"
            if (y, x) in highlighted:
                fc = COLD_LIGHT
            ax.add_patch(Rectangle((x - 0.43, y - 0.43), 0.86, 0.86, facecolor=fc, edgecolor=WHITE, lw=1.2))
    cy, cx = center
    ax.scatter(cx, cy, s=260, marker="*", color=GOLD, edgecolor=INK, linewidth=1.2, zorder=5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)


def _surface(stack: xr.Dataset, center: int, metric: str = "delta_s", radius_km: float | None = None) -> np.ndarray:
    values = np.asarray(stack[metric].isel(center=center).values, dtype=float)
    if radius_km is not None:
        values = np.where(np.asarray(stack.distance_km.isel(center=center)) <= radius_km, values, np.nan)
    return values


def _delta_heat(ax, values: np.ndarray, title: str = "", extent=None, limit: float | None = None):
    values = np.asarray(values, dtype=float)
    if limit is None:
        limit = max(0.05, float(np.nanquantile(np.abs(values), 0.98)))
    image = ax.imshow(values, cmap="RdBu", vmin=-limit, vmax=limit, origin="upper", extent=extent, aspect="auto")
    if title:
        ax.set_title(title, fontsize=10.5, color=INK, fontweight="bold")
    return image


def _metric_heat(ax, values: np.ndarray, color: str, title: str):
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("metric", [WHITE, color])
    image = ax.imshow(values, cmap=cmap, vmin=-1, vmax=1, origin="upper", aspect="auto")
    ax.set_title(title, fontsize=10.5, color=INK, fontweight="bold")
    return image


def _draw_surface_plane(ax, z: float, values: np.ndarray, alpha: float = 0.72, center: tuple[int, int] | None = None) -> None:
    ny, nx = values.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    limit = max(0.05, float(np.nanquantile(np.abs(values), 0.98)))
    colors = matplotlib.colormaps["RdBu"](Normalize(-limit, limit)(np.nan_to_num(values)))
    colors[..., -1] = alpha
    ax.plot_surface(xx, yy, np.full_like(xx, z), facecolors=colors, rstride=1, cstride=1, shade=False, linewidth=0)
    if center is not None:
        cy, cx = center
        ax.scatter([cx], [cy], [z + 0.08], marker="*", s=90, color=GOLD, edgecolor=INK, depthshade=False)


def _usa_shape() -> np.ndarray:
    """Stylized contiguous-US outline used only on CONCEPTUAL pages."""
    return np.array([
        [0.6, 4.5], [1.2, 5.2], [2.4, 5.0], [3.2, 5.4], [4.8, 5.1], [6.2, 5.2],
        [7.2, 4.8], [8.5, 4.9], [9.2, 4.2], [8.9, 3.5], [8.0, 3.2], [7.5, 2.5],
        [6.6, 2.2], [5.4, 2.4], [4.3, 2.1], [3.2, 2.4], [2.0, 2.8], [1.2, 3.2],
    ])


def _draw_usa_grid(ax, cell: float = 0.45, color_by_x: bool = True) -> None:
    outline = _usa_shape()
    poly = Polygon(outline, closed=True, facecolor="#E2E8F0", edgecolor=INK, lw=2)
    ax.add_patch(poly)
    path = MplPath(outline)
    xs = np.arange(0.7, 9.1, cell)
    ys = np.arange(2.2, 5.25, cell)
    for y in ys:
        for x in xs:
            if path.contains_point((x, y)):
                color = matplotlib.colormaps["viridis"]((x - 0.7) / 8.4) if color_by_x else "#93C5FD"
                sq = Rectangle((x - cell * 0.38, y - cell * 0.38), cell * 0.76, cell * 0.76, facecolor=color, edgecolor=WHITE, lw=0.35)
                sq.set_clip_path(poly)
                ax.add_patch(sq)
    ax.set_xlim(0, 10)
    ax.set_ylim(1.5, 5.9)
    ax.set_aspect("equal")
    ax.axis("off")


def _state_outline(ax, boundary_path: Path) -> None:
    payload = json.loads(Path(boundary_path).read_text())
    geometries = [f["geometry"] for f in payload.get("features", [])]
    if not geometries and payload.get("type") in {"Polygon", "MultiPolygon"}:
        geometries = [payload]
    for geometry in geometries:
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        for polygon in polygons:
            ring = np.asarray(polygon[0])
            ax.plot(ring[:, 0], ring[:, 1], color=INK, lw=1.1)


def build_pages(evidence: dict[str, object], figures_dir: Path, boundary_path: Path) -> tuple[list[Path], dict[str, dict[str, object]]]:
    """Render all 55 pages and return paths plus per-page provenance."""

    arrays = evidence["arrays"]
    pair = evidence["pair"]
    alignment = evidence["alignment"]
    reps = evidence["representations"]
    stations = evidence["stations"]
    stack_info = evidence["stack"]
    stack: xr.Dataset = arrays["stack"]
    colorado: xr.Dataset = arrays["colorado"]
    time = pd.to_datetime(arrays["time"])
    a_tmin = np.asarray(arrays["a_tmin"])
    b_tmin = np.asarray(arrays["b_tmin"])
    a_tmax = np.asarray(arrays["a_tmax"])
    b_tmax = np.asarray(arrays["b_tmax"])
    figures_dir.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []
    provenance: dict[str, dict[str, object]] = {}

    def add(fig, number: int, data_label: str, source: str, empirical_keys: list[str] | None = None):
        pages.append(_save(fig, number, figures_dir, source))
        provenance[str(number)] = {
            "title": PAGE_GUIDE[number - 1][0],
            "data_class": data_label,
            "empirical_keys": empirical_keys or [],
            "source_line": source,
        }

    # 1 - one real pair through time
    fig, g = _page(
        "When do two places experience climate together?",
        f"One real Front Range pair, followed through the same {stack_info['window_days']}-day analysis window",
        "REAL PRISM",
        "1 - measuring one pair",
    )
    ax = fig.add_subplot(g[1:10, 0:12])
    ax.plot(time, a_tmin, color=COLD, lw=2, label=f"A  ({pair['center_lat']:.3f}, {pair['center_lon']:.3f})")
    ax.plot(time, b_tmin, color="#65A7F3", lw=2, label=f"B  ({pair['comparison_lat']:.3f}, {pair['comparison_lon']:.3f})")
    ax.fill_between(time, a_tmin, b_tmin, color=COLD_LIGHT, alpha=0.28)
    ax.set_ylabel("daily minimum temperature (C)")
    ax.legend(loc="upper right", frameon=False)
    _clean_axes(ax)
    fig.text(0.12, 0.11, "Not: Are all dates correlated?", fontsize=12.5, color=MUTED, fontweight="bold")
    fig.text(0.55, 0.12, "Instead: How do they move together\nin cold and warm tails?", fontsize=12.5, color=INK, fontweight="bold", va="center")
    add(fig, 1, "REAL PRISM", f"PRISM AN daily; {stack_info['window_start']} to {stack_info['window_end']}", ["pair", "stack.window_start", "stack.window_end"])

    # 2 - actual thresholds
    fig, g = _page(
        "What counts as cold or warm?",
        "Current CubeDynamics semantics: per-location medians on pair-valid observations",
        "REAL PRISM",
        "1 - measuring one pair",
    )
    for col, (left, right, medians, color, heading, rule) in enumerate(
        [
            (a_tmin, b_tmin, pair["tmin_medians"], COLD, "COLD: TMIN", "both values <= their own medians"),
            (a_tmax, b_tmax, pair["tmax_medians"], WARM, "WARM: TMAX", "both values > their own medians"),
        ]
    ):
        ax = fig.add_subplot(g[1:9, col * 6 : (col + 1) * 6])
        ax.plot(time, left, color=INK, lw=1.2, alpha=0.75, label="A")
        ax.plot(time, right, color=MUTED, lw=1.2, alpha=0.75, label="B")
        ax.axhline(medians[0], color=INK, ls="--", lw=1)
        ax.axhline(medians[1], color=MUTED, ls=":", lw=1)
        selected = (left <= medians[0]) & (right <= medians[1]) if color == COLD else (left > medians[0]) & (right > medians[1])
        ax.scatter(time[selected], (left[selected] + right[selected]) / 2, s=20, color=color, zorder=4, label="joint dates")
        ax.set_title(f"{heading}\n{rule}", color=color, fontsize=11.5, fontweight="bold")
        ax.set_ylabel("temperature (C)")
        ax.legend(loc="upper right", fontsize=8, frameon=False)
        _clean_axes(ax)
    fig.text(0.5, 0.105, "The threshold is relative to each location - not one shared Celsius cutoff.", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 2, "REAL PRISM", "Current one_tail_spearman semantics; pair-valid 0.5 quantiles", ["pair.tmin_medians", "pair.tmax_medians", "stack.split_quantile"])

    # 3 and 4 - mirrored tail pages
    for number, label, x, y, color, symbol, n_key, value_key, inequality in [
        (3, "Cold synchrony", a_tmin, b_tmin, COLD, "S_cold(A,B)", "cold_n", "cold", "<="),
        (4, "Warm synchrony", a_tmax, b_tmax, WARM, "S_warm(A,B)", "warm_n", "warm", ">"),
    ]:
        med_a = float(np.nanmedian(x))
        med_b = float(np.nanmedian(y))
        selected = (x <= med_a) & (y <= med_b) if inequality == "<=" else (x > med_a) & (y > med_b)
        fig, g = _page(
            label,
            "Rank the values only on dates when both locations occupy the selected tail",
            "REAL PRISM",
            "1 - measuring one pair",
        )
        ax1 = fig.add_subplot(g[1:10, 0:7])
        ax1.scatter(x[~selected], y[~selected], s=18, color="#D9E2EC", alpha=0.65, label="not used")
        ax1.scatter(x[selected], y[selected], s=38, color=color, edgecolor=WHITE, linewidth=0.5, label=f"used: n={pair[n_key]}")
        ax1.axvline(med_a, color=MUTED, ls="--", lw=1)
        ax1.axhline(med_b, color=MUTED, ls="--", lw=1)
        ax1.set_xlabel("location A temperature (C)")
        ax1.set_ylabel("location B temperature (C)")
        ax1.legend(frameon=False)
        _clean_axes(ax1)
        ax2 = fig.add_subplot(g[2:10, 8:12])
        ax2.axis("off")
        _callout(ax2, 0.5, 0.78, f"{symbol} = {pair[value_key]:.2f}", color=color, size=20)
        ax2.text(0.5, 0.52, "Spearman rank\ncorrelation", ha="center", va="center", fontsize=16, color=INK, fontweight="bold")
        ax2.text(0.5, 0.26, f"joint-tail dates\nn = {pair[n_key]}", ha="center", va="center", fontsize=13, color=MUTED)
        add(fig, number, "REAL PRISM", "PRISM pair recomputed with cubedynamics.stats.tails.one_tail_spearman", [f"pair.{value_key}", f"pair.{n_key}"])

    # 5 - Delta sign convention
    fig, g = _page(
        "Delta synchrony",
        "The signed contrast keeps cold and warm meanings visible",
        "REAL PRISM",
        "1 - measuring one pair",
    )
    ax = fig.add_subplot(g[0:7, 0:12]); ax.axis("off")
    cards = [
        (0.08, COLD, "COLD", f"{pair['cold']:.2f}"),
        (0.39, INK, "MINUS", "-"),
        (0.62, WARM, "WARM", f"{pair['warm']:.2f}"),
        (0.84, WARM, "DELTA", f"{pair['delta']:.2f}"),
    ]
    for x0, color, label, value in cards:
        ax.add_patch(FancyBboxPatch((x0 - 0.085, 0.28), 0.17, 0.45, boxstyle="round,pad=0.025", facecolor=WHITE, edgecolor=color, lw=2))
        ax.text(x0, 0.61, label, ha="center", fontsize=10, color=color, fontweight="bold")
        ax.text(x0, 0.40, value, ha="center", fontsize=25, color=color, fontweight="bold")
    ax.text(0.5, 0.08, "Delta S = S_cold - S_warm", ha="center", fontsize=18, color=INK, fontweight="bold")
    ax2 = fig.add_subplot(g[8:12, 0:12]); ax2.axis("off")
    examples = [("cold = warm", "0", QUESTION), ("cold > warm", "+", COLD), ("warm > cold", "-", WARM)]
    for i, (label, sign, color) in enumerate(examples):
        x0 = 0.17 + i * 0.33
        ax2.text(x0, 0.65, sign, ha="center", fontsize=28, color=color, fontweight="bold")
        ax2.text(x0, 0.22, label, ha="center", fontsize=12, color=INK)
    add(fig, 5, "REAL PRISM", "Delta S is cold-tail minus warm-tail Spearman synchrony", ["pair.cold", "pair.warm", "pair.delta"])

    # 6 - one mapped edge
    fig, g = _page("One center, one neighbor", "The line is the pair relationship from the first five pages", "CONCEPTUAL", "2 - one center to one surface")
    ax = fig.add_subplot(g[0:11, 2:10])
    _grid(ax, 9, (4, 4), highlighted=[(3, 7)])
    ax.plot([4, 7], [4, 3], color=INK, lw=3, zorder=3)
    ax.scatter(7, 3, s=150, color=COLD_LIGHT, edgecolor=COLD, lw=2, zorder=5)
    ax.text(4, 5.1, "A: focal center", ha="center", color=INK, fontweight="bold")
    ax.text(7.0, 2.2, "B: neighbor", ha="center", color=COLD, fontweight="bold")
    ax.text(5.65, 3.0, "one pair", rotation=18, color=INK, fontweight="bold")
    add(fig, 6, "CONCEPTUAL", "Conceptual grid; same pair meaning as pages 1-5")

    # 7 - spokes
    fig, g = _page("One center, many neighbors", "Repeat the same pair calculation while holding the gold center fixed", "CONCEPTUAL", "2 - one center to one surface")
    ax = fig.add_subplot(g[0:11, 2:10])
    neighbors = [(1, 2), (1, 6), (3, 7), (6, 7), (7, 4), (6, 1), (3, 1)]
    _grid(ax, 9, (4, 4), highlighted=neighbors)
    for i, (ny, nx) in enumerate(neighbors):
        color = COLD if i % 3 == 0 else WARM if i % 3 == 1 else QUESTION
        ax.plot([4, nx], [4, ny], color=color, lw=2.2, alpha=0.85)
        ax.scatter(nx, ny, s=75, color=WHITE, edgecolor=color, lw=2, zorder=4)
    ax.text(4, 8.15, "Every spoke carries:  S_cold   S_warm   Delta S", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 7, "CONCEPTUAL", "Conceptual neighborhood; pair semantics unchanged")

    # 8 - real local surface
    fig, g = _page("The local synchrony surface", "Each cell is Delta S between that cell and the SAME gold center", "REAL PRISM", "2 - one center to one surface")
    ax = fig.add_subplot(g[0:11, 1:9])
    values = _surface(stack, int(pair["center"]), "delta_s")
    im = _delta_heat(ax, values, limit=0.25)
    ax.scatter(10, 10, marker="*", s=170, color=GOLD, edgecolor=INK, zorder=5)
    ax.scatter(pair["comparison_grid"][1], pair["comparison_grid"][0], s=85, facecolor=WHITE, edgecolor=INK, lw=1.5, zorder=5)
    ax.set_xlabel("comparison x index"); ax.set_ylabel("comparison y index")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    cb.set_label("Delta S  (blue = cold-dominant; red = warm-dominant)", color=INK)
    ax2 = fig.add_subplot(g[2:10, 9:12]); ax2.axis("off")
    ax2.text(0.12, 0.80, "ONE CENTER", fontsize=15, color=GOLD, fontweight="bold")
    ax2.text(0.12, 0.57, "+", fontsize=18, color=INK, fontweight="bold")
    ax2.text(0.12, 0.34, f"{stack_info['cells_per_surface']} PAIR VALUES", fontsize=14, color=INK, fontweight="bold")
    ax2.text(0.12, 0.13, "= one local surface", fontsize=12, color=MUTED, fontweight="bold")
    add(fig, 8, "REAL PRISM", "Real 20 x 20 PRISM local synchrony stack", ["pair.center", "pair.delta"])

    # 9 - ordinary vs relational
    fig, g = _page("Why this is not an ordinary climate map", "State at a cell versus relationship to a chosen center", "REAL PRISM", "2 - one center to one surface")
    temp_map = np.asarray(arrays["block_final_tmin"])
    ax1 = fig.add_subplot(g[1:10, 0:5])
    timg = ax1.imshow(temp_map, cmap="coolwarm", origin="upper")
    ax1.set_title("Ordinary temperature map\n'What is the value here?'", color=INK, fontweight="bold")
    ax1.set_xticks([]); ax1.set_yticks([])
    fig.colorbar(timg, ax=ax1, fraction=0.047, pad=0.03, label="daily minimum temperature (C)")
    ax2 = fig.add_subplot(g[1:10, 7:12])
    simg = _delta_heat(ax2, values, limit=0.25)
    ax2.scatter(10, 10, marker="*", s=130, color=GOLD, edgecolor=INK)
    ax2.set_title("Center-reference surface\n'How does here relate to the center?'", color=INK, fontweight="bold")
    ax2.set_xticks([]); ax2.set_yticks([])
    fig.colorbar(simg, ax=ax2, fraction=0.047, pad=0.03, label="Delta S")
    add(fig, 9, "REAL PRISM", "Real PRISM final-day TMIN versus real center-reference Delta surface", ["pair.center", "sources.cube", "sources.stack"])

    # 10 - two separate surfaces
    fig, g = _page("Move the center one pixel", "A new focal center produces a NEW local surface", "REAL PRISM", "3 - what is the stack?")
    centers = [210, 211]
    for i, center in enumerate(centers):
        ax = fig.add_subplot(g[1:10, i * 6 : (i + 1) * 6])
        local = _surface(stack, center, "delta_s")
        im = _delta_heat(ax, local, limit=0.25, title=f"center {'A' if i == 0 else 'B'}")
        cy, cx = divmod(center, 20)
        ax.scatter(cx, cy, marker="*", s=145, color=GOLD, edgecolor=INK)
        ax.set_xticks([]); ax.set_yticks([])
    fig.text(0.5, 0.105, "Do not combine them yet: same geography, different focal relationships.", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 10, "REAL PRISM", "Two adjacent real PRISM focal-center surfaces", ["stack.surface_count"])

    # 11 - 3-D two surfaces
    fig, g = _page("The two surfaces overlap", "Layer height indexes focal center - not elevation and not time", "REAL PRISM", "3 - what is the stack?")
    ax = fig.add_subplot(g[0:11, 1:11], projection="3d")
    for z, center in enumerate(centers):
        _draw_surface_plane(ax, z * 3.2, _surface(stack, center), center=divmod(center, 20))
    ax.set(xlabel="absolute x", ylabel="absolute y", zlabel="layer / focal center", zlim=(-0.2, 4.2))
    ax.view_init(elev=24, azim=-58)
    ax.set_zticks([0, 3.2], ["center A", "center B"])
    add(fig, 11, "REAL PRISM", "Two real PRISM surfaces shown as transparent relational layers", ["stack.surface_count"])

    # 12 - four layers
    fig, g = _page("Move again", "Centers A, B, C, and D each create a complete relational view", "REAL PRISM", "3 - what is the stack?")
    ax = fig.add_subplot(g[0:11, 1:11], projection="3d")
    centers4 = [210, 211, 231, 230]
    for i, center in enumerate(centers4):
        _draw_surface_plane(ax, i * 2.4, _surface(stack, center), alpha=0.58, center=divmod(center, 20))
    ax.set(xlabel="absolute x", ylabel="absolute y", zlabel="focal-center layer", zlim=(-0.2, 8.0))
    ax.view_init(elev=25, azim=-58)
    ax.set_zticks([i * 2.4 for i in range(4)], list("ABCD"))
    add(fig, 12, "REAL PRISM", "Four adjacent real PRISM focal-center surfaces", ["stack.surface_count"])

    # 13 - 5x5 exploded conceptual stack
    fig, g = _page("Fill a small grid of centers", "25 focal pixels -> 25 overlapping relational surfaces", "CONCEPTUAL", "3 - what is the stack?")
    ax1 = fig.add_subplot(g[1:10, 0:5]); _grid(ax1, 5, (2, 2), highlighted=[(y, x) for y in range(5) for x in range(5)])
    ax1.set_title("5 x 5 possible centers", color=INK, fontweight="bold")
    ax2 = fig.add_subplot(g[0:11, 6:12], projection="3d")
    base = _surface(stack, 210)[5:15, 5:15]
    for i in range(25):
        _draw_surface_plane(ax2, i * 0.42, np.roll(base, (i % 5) - 2, axis=1), alpha=0.12)
    ax2.set(xlabel="x", ylabel="y", zlabel="25 focal centers")
    ax2.view_init(elev=22, azim=-60)
    ax2.set_zticks([0, 5, 10], ["1", "13", "25"])
    add(fig, 13, "CONCEPTUAL", "Conceptual 5 x 5 stack using a real surface as visual texture")

    # 14 - 20x20 thought experiment with column through stack
    fig, g = _page(f"The {stack_info['grid_y']} x {stack_info['grid_x']} thought experiment", f"The real block has {stack_info['surface_count']} focal surfaces; one absolute cell appears in many layers", "REAL PRISM", "3 - what is the stack?")
    ax1 = fig.add_subplot(g[1:10, 0:5]); _grid(ax1, 20, (10, 10), highlighted=[(0, i) for i in range(20)] + [(19, i) for i in range(20)] + [(i, 0) for i in range(20)] + [(i, 19) for i in range(20)])
    ax1.scatter(13, 9, s=90, facecolor=WHITE, edgecolor=INK, lw=2)
    ax1.set_title("perimeter first -> fill the interior", color=INK, fontsize=11, fontweight="bold")
    ax2 = fig.add_subplot(g[0:11, 6:12], projection="3d")
    sample_centers = np.linspace(0, 399, 14, dtype=int)
    for i, center in enumerate(sample_centers):
        _draw_surface_plane(ax2, i * 0.65, _surface(stack, int(center))[5:15, 5:15], alpha=0.16)
    ax2.plot([6.5, 6.5], [4.5, 4.5], [0, 8.5], color=GOLD, lw=4)
    ax2.scatter([6.5] * len(sample_centers), [4.5] * len(sample_centers), np.arange(len(sample_centers)) * 0.65, color=GOLD, s=22)
    ax2.set(xlabel="absolute x", ylabel="absolute y", zlabel="400 layers (sampled)")
    ax2.view_init(elev=23, azim=-58)
    fig.text(0.52, 0.10, f"{stack_info['surface_count']} surfaces x {stack_info['cells_per_surface']} cells = {stack_info['directed_views']:,} directed views", ha="center", fontsize=13, color=INK, fontweight="bold")
    add(fig, 14, "REAL PRISM", "Real 20 x 20 stack counts; stack planes visually sampled", ["stack.surface_count", "stack.cells_per_surface", "stack.directed_views", "stack.canonical_pairs"])

    # 15 - column semantics
    fig, g = _page("What each element in the stack means", "A column through q is a collection of relationships involving q", "CONCEPTUAL", "3 - what is the stack?")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    qx, qy = 0.73, 0.52
    ax.scatter([qx], [qy], s=520, facecolor=WHITE, edgecolor=INK, lw=2.5, zorder=5)
    ax.text(qx, qy, "q", ha="center", va="center", fontsize=22, color=INK, fontweight="bold")
    centers_xy = [(0.14, 0.78), (0.18, 0.35), (0.43, 0.18), (0.48, 0.82)]
    for i, (x0, y0) in enumerate(centers_xy, 1):
        color = [COLD, WARM, GREEN, PURPLE][i - 1]
        ax.scatter([x0], [y0], s=230, color=color, edgecolor=WHITE, lw=1.2)
        ax.text(x0, y0, f"p{i}", ha="center", va="center", fontsize=11, color=WHITE, fontweight="bold")
        _arrow(ax, (x0 + 0.03, y0), (qx - 0.04, qy), color=color, lw=2)
        ax.text((x0 + qx) / 2, (y0 + qy) / 2 + 0.03, f"S(p{i}, q)", color=color, fontsize=11, fontweight="bold")
    ax.text(0.92, 0.72, "NOT", ha="center", fontsize=12, color=WARM, fontweight="bold")
    ax.text(0.92, 0.55, "four repeats of\n\"the synchrony of q\"", ha="center", fontsize=13, color=MUTED)
    ax.text(0.92, 0.31, "IS", ha="center", fontsize=12, color=GREEN, fontweight="bold")
    ax.text(0.92, 0.15, "four different\nrelationships involving q", ha="center", fontsize=13, color=INK, fontweight="bold")
    add(fig, 15, "CONCEPTUAL", "Conceptual relationship column through one absolute cell")

    # 16 - relative view
    fig, g = _page("Relative view", "For every focal center p, describe neighbors by dx and dy; p is always (0,0)", "REAL PRISM", "4 - relative versus absolute")
    ax = fig.add_subplot(g[0:11, 2:10])
    local = _surface(stack, 210)
    fy, fx = divmod(210, 20)
    _delta_heat(ax, local, limit=0.25)
    ax.set_xticks([0, 5, 10, 15, 19], [str(v - fx) for v in [0, 5, 10, 15, 19]])
    ax.set_yticks([0, 5, 10, 15, 19], [str(v - fy) for v in [0, 5, 10, 15, 19]])
    ax.scatter(fx, fy, marker="*", s=170, color=GOLD, edgecolor=INK)
    ax.set_xlabel("dx index"); ax.set_ylabel("dy index")
    ax.axhline(fy, color=WHITE, lw=0.8, alpha=0.7); ax.axvline(fx, color=WHITE, lw=0.8, alpha=0.7)
    add(fig, 16, "REAL PRISM", "Real PRISM surface shown in focal-relative coordinates", ["pair.center"])

    # 17 - same feature shifts in relative coordinates
    fig, g = _page("Move the center", "In relative coordinates, fixed geography appears to move through the window", "CONCEPTUAL", "4 - relative versus absolute")
    for i, focal_x in enumerate([4, 6, 8]):
        ax = fig.add_subplot(g[1:10, i * 4 : (i + 1) * 4])
        ax.set_xlim(-5, 5); ax.set_ylim(-5, 5); ax.set_aspect("equal")
        ax.axvline(0, color=GRID, lw=1); ax.axhline(0, color=GRID, lw=1)
        ax.scatter(0, 0, marker="*", s=150, color=GOLD, edgecolor=INK)
        ridge_dx = 7 - focal_x
        ax.axvspan(ridge_dx - 0.45, ridge_dx + 0.45, color=GREEN, alpha=0.55)
        ax.text(ridge_dx, 4.4, "fixed ridge", ha="center", fontsize=9, color=GREEN, fontweight="bold")
        ax.set_title(f"center moves east\nstep {i + 1}", color=INK, fontweight="bold")
        ax.set_xlabel("dx"); ax.set_ylabel("dy"); ax.set_xticks([-4, 0, 4]); ax.set_yticks([-4, 0, 4])
    add(fig, 17, "CONCEPTUAL", "Conceptual fixed geographic ridge viewed from moving centers")

    # 18 - absolute alignment and measured comparison
    fig, g = _page("Absolute view", "Latitude/longitude keep fixed features fixed while the focal center moves", "REAL PRISM", "4 - relative versus absolute")
    ax1 = fig.add_subplot(g[1:10, 0:8])
    for i, center in enumerate([207, 209, 211, 213]):
        local = _surface(stack, center, radius_km=40)
        alpha = 0.22 + i * 0.08
        ax1.contour(local, levels=[-0.12, -0.06, 0.0, 0.06], colors=[WARM, "#F87171", QUESTION, COLD], linewidths=1.2, alpha=alpha + 0.35)
        cy, cx = divmod(center, 20)
        ax1.scatter(cx, cy, marker="*", s=60, color=GOLD, edgecolor=INK, zorder=5)
    ax1.set_title("Four surfaces on the same absolute grid", color=INK, fontweight="bold")
    ax1.set_xlabel("absolute x index"); ax1.set_ylabel("absolute y index")
    ax1.set_aspect("equal")
    ax2 = fig.add_subplot(g[2:10, 9:12]); ax2.axis("off")
    _callout(ax2, 0.5, 0.78, f"correlation\n{alignment['pearson_relative']:.2f} -> {alignment['pearson_absolute']:.2f}", color=GREEN, size=15)
    _callout(ax2, 0.5, 0.37, f"gradient agreement\n{alignment['gradient_relative']:.2f} -> {alignment['gradient_absolute']:.2f}", color=COLD, size=15)
    add(fig, 18, "REAL PRISM", "Real 40 km Delta alignment medians from the bounded feasibility experiment", ["alignment.pearson_relative", "alignment.pearson_absolute", "alignment.gradient_relative", "alignment.gradient_absolute"])

    # 19 - central insight
    fig, g = _page("The central insight", "Overlap contains information only if relationship locations remain attached to geography", "CONCEPTUAL", "4 - relative versus absolute")
    ax = fig.add_subplot(g[0:11, 0:12], projection="3d")
    base = _surface(stack, 210)[4:16, 4:16]
    for i in range(7):
        _draw_surface_plane(ax, i * 1.0, np.roll(base, i - 3, axis=1), alpha=0.2)
    xx = np.linspace(1.5, 9.5, 80)
    yy = 5.0 + 0.9 * np.sin(xx * 0.7)
    for z in np.linspace(0, 6, 7):
        ax.plot(xx, yy, zs=z + 0.05, color=GOLD, lw=2.2, alpha=0.85)
    ax.set(xlabel="absolute geography x", ylabel="absolute geography y", zlabel="focal-center views")
    ax.view_init(elev=23, azim=-58)
    fig.text(0.5, 0.105, "ALIGN FIRST. THEN ASK WHAT GEOGRAPHIC ORGANIZATION REPEATS.", ha="center", fontsize=17, color=INK, fontweight="bold")
    add(fig, 19, "CONCEPTUAL", "Conceptual transparent alignment using real surface texture")

    # 20 - ordinary convolution
    fig, g = _page("Ordinary convolution", "A kernel slides over an image and usually emits one reduced output per location", "CONCEPTUAL", "5 - why convolution-like")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    image = np.arange(64, dtype=float).reshape(8, 8) % 11
    inset = ax.inset_axes([0.03, 0.18, 0.34, 0.66])
    inset.imshow(image, cmap="Blues"); inset.set_xticks([]); inset.set_yticks([])
    inset.add_patch(Rectangle((2.5, 2.5), 3, 3, fill=False, edgecolor=GOLD, lw=4))
    kernel = ax.inset_axes([0.45, 0.34, 0.18, 0.38])
    kernel.imshow(np.array([[0, 1, 0], [1, 4, 1], [0, 1, 0]]), cmap="Greys")
    kernel.set_xticks([]); kernel.set_yticks([]); kernel.set_title("operation", color=INK, fontweight="bold")
    _arrow(ax, (0.37, 0.52), (0.45, 0.52), color=MUTED, lw=2.5)
    _arrow(ax, (0.64, 0.52), (0.73, 0.52), color=MUTED, lw=2.5)
    ax.add_patch(Circle((0.82, 0.52), 0.095, facecolor=WHITE, edgecolor=GREEN, lw=3))
    ax.text(0.82, 0.52, "one\noutput", ha="center", va="center", fontsize=16, color=GREEN, fontweight="bold")
    ax.text(0.19, 0.08, "neighborhood", ha="center", fontsize=13, color=INK, fontweight="bold")
    ax.text(0.54, 0.08, "local rule", ha="center", fontsize=13, color=INK, fontweight="bold")
    ax.text(0.82, 0.08, "immediate reduction", ha="center", fontsize=13, color=INK, fontweight="bold")
    add(fig, 20, "CONCEPTUAL", "Conceptual textbook convolution geometry")

    # 21 - relational version
    fig, g = _page("Our relational version", "The center slides, but the scientifically defined operation returns a complete surface", "CONCEPTUAL", "5 - why convolution-like")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    stages = [
        (0.08, "climate\ntime-series cube", COLD),
        (0.35, "pairwise conditional\nsynchrony", GOLD),
        (0.67, "complete local\nrelational surface", GREEN),
    ]
    for x0, label, color in stages:
        ax.add_patch(FancyBboxPatch((x0, 0.32), 0.2, 0.38, boxstyle="round,pad=0.025", facecolor=WHITE, edgecolor=color, lw=2.4))
        ax.text(x0 + 0.1, 0.51, label, ha="center", va="center", fontsize=15, color=INK, fontweight="bold")
    _arrow(ax, (0.285, 0.51), (0.345, 0.51), lw=3)
    _arrow(ax, (0.555, 0.51), (0.665, 0.51), lw=3)
    ax.text(0.50, 0.15, "difference from ordinary convolution: retain the relational neighborhood", ha="center", fontsize=15, color=INK, fontweight="bold")
    add(fig, 21, "CONCEPTUAL", "Conceptual relational sliding-window analogy")

    # 22 - not a CNN
    fig, g = _page("Why this is not a CNN", "The analogy describes sliding and overlapping geometry - not machine learning", "CONCEPTUAL", "5 - why convolution-like")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    left = ["scientifically defined tail rule", "pairwise Spearman association", "complete neighborhood retained", "explicit provenance"]
    right = ["no trained filters", "no backpropagation", "no learned objective", "no image labels required"]
    ax.text(0.25, 0.86, "WE HAVE", ha="center", fontsize=15, color=GREEN, fontweight="bold")
    ax.text(0.75, 0.86, "WE DO NOT HAVE", ha="center", fontsize=15, color=WARM, fontweight="bold")
    for i, label in enumerate(left):
        ax.text(0.25, 0.69 - i * 0.16, f"+  {label}", ha="center", fontsize=14, color=INK, fontweight="bold")
    for i, label in enumerate(right):
        ax.text(0.75, 0.69 - i * 0.16, f"x  {label}", ha="center", fontsize=14, color=INK, fontweight="bold")
    ax.plot([0.5, 0.5], [0.1, 0.83], color=GRID, lw=2)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    add(fig, 22, "CONCEPTUAL", "Conceptual boundary of the convolution analogy")

    # 23 - notation after meaning
    fig, g = _page("We have too much information", "Now the notation has a physical meaning", "CONCEPTUAL", "6 - from stack to map")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    ax.text(0.5, 0.70, "S(x, y, dx, dy)", ha="center", fontsize=38, color=INK, fontweight="bold")
    ax.text(0.28, 0.43, "x, y", ha="center", fontsize=24, color=GOLD, fontweight="bold")
    ax.text(0.28, 0.28, "where the focal center lives", ha="center", fontsize=14, color=MUTED)
    ax.text(0.72, 0.43, "dx, dy", ha="center", fontsize=24, color=PURPLE, fontweight="bold")
    ax.text(0.72, 0.28, "where the comparison lies\nrelative to that center", ha="center", fontsize=14, color=MUTED)
    ax.text(0.5, 0.09, "A normal map has two spatial axes.\nThis field has focal geography plus within-surface geometry.", ha="center", fontsize=13, color=INK, fontweight="bold")
    add(fig, 23, "CONCEPTUAL", "Conceptual notation for the already-introduced relational object")

    # 24 - tempting reductions with real reconstruction errors
    fig, g = _page("The tempting easy solution", "Collapse each surface independently to a median, mean, or spread statistic", "REAL PRISM", "6 - from stack to map")
    local_stack = np.asarray(stack.delta_s.values)
    med = np.nanmedian(local_stack, axis=(1, 2)).reshape(20, 20)
    iqr = (np.nanquantile(local_stack, 0.75, axis=(1, 2)) - np.nanquantile(local_stack, 0.25, axis=(1, 2))).reshape(20, 20)
    for i, (arr, title, cmap) in enumerate([(med, "one median per surface", "RdBu"), (iqr, "one IQR per surface", "magma")]):
        ax = fig.add_subplot(g[1:9, i * 5 : i * 5 + 5])
        lim = float(np.nanquantile(np.abs(arr), 0.98))
        im = ax.imshow(arr, cmap=cmap, origin="upper", vmin=-lim if cmap == "RdBu" else None, vmax=lim if cmap == "RdBu" else None)
        ax.set_title(title, color=INK, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([]); fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
    ax3 = fig.add_subplot(g[2:9, 10:12]); ax3.axis("off")
    _callout(ax3, 0.5, 0.68, f"median-only\nnRMSE = {reps['median_only']:.2f}", color=WARM, size=14)
    ax3.text(0.5, 0.28, "Easy map.\nLost 2-D arrangement.", ha="center", fontsize=13, color=INK, fontweight="bold")
    fig.text(0.5, 0.105, "Reduction is necessary. Independent scalar reduction is not automatically sufficient.", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 24, "REAL PRISM", "Real PRISM 20 x 20 stack and held-out reconstruction benchmark", ["representations.median_only"])

    # 25 - radial
    fig, g = _page("Radial reduction", "Distance profiles retain structure, but they privilege radius", "REAL PRISM", "6 - from stack to map")
    center = int(pair["center"])
    d = np.asarray(stack.distance_km.isel(center=center))
    v = np.asarray(stack.delta_s.isel(center=center))
    bins = np.arange(0, 75, 7.5); mids = (bins[:-1] + bins[1:]) / 2
    profile = [float(np.nanmedian(v[(d >= lo) & (d < hi)])) for lo, hi in zip(bins[:-1], bins[1:])]
    ax1 = fig.add_subplot(g[1:10, 0:7])
    ax1.scatter(d.ravel(), v.ravel(), s=12, color="#94A3B8", alpha=0.35, label="pair values")
    ax1.plot(mids, profile, "o-", color=PURPLE, lw=3, label="radial median")
    ax1.axhline(0, color=GRID, lw=1); ax1.set(xlabel="distance from center (km)", ylabel="Delta S")
    ax1.legend(frameon=False); _clean_axes(ax1)
    ax2 = fig.add_subplot(g[2:10, 8:12]); ax2.axis("off")
    _callout(ax2, 0.5, 0.70, f"fine radial\nnRMSE = {reps['fine_radial_profile']:.2f}", color=PURPLE, size=15)
    ax2.text(0.5, 0.32, "Useful baseline\nnot a law of\ndistance decay", ha="center", fontsize=15, color=INK, fontweight="bold")
    add(fig, 25, "REAL PRISM", "Real PRISM focal surface and representation benchmark", ["representations.fine_radial_profile", "pair.center"])

    # 26 - radial directional
    fig, g = _page("Radial + directional", "Direction preserves substantially more local geometry than median-only summaries", "REAL PRISM", "6 - from stack to map")
    ax1 = fig.add_subplot(g[1:10, 0:6], projection="polar")
    bearing = np.deg2rad(np.asarray(stack.bearing_degrees.isel(center=center)))
    valid = np.isfinite(bearing) & np.isfinite(v) & (d <= 40)
    ax1.scatter(bearing[valid], np.abs(v[valid]), c=v[valid], cmap="RdBu", vmin=-0.25, vmax=0.25, s=28, alpha=0.75)
    ax1.set_title("direction remains visible", color=INK, fontweight="bold", pad=16)
    ax2 = fig.add_subplot(g[2:10, 7:12]); ax2.axis("off")
    ax2.set_xlim(0, 1.12); ax2.set_ylim(0, 1)
    values = [("median only", reps["median_only"], WARM), ("fine radial", reps["fine_radial_profile"], PURPLE), ("radial + directional", reps["radial_plus_directional"], GREEN)]
    for i, (label, value, color) in enumerate(values):
        y = 0.80 - i * 0.26
        ax2.text(0.0, y, label, fontsize=12, color=INK, fontweight="bold")
        ax2.add_patch(Rectangle((0.0, y - 0.10), value / 1.2, 0.09, color=color, alpha=0.85))
        ax2.text(min(value / 1.2 + 0.03, 0.92), y - 0.055, f"nRMSE {value:.2f}", va="center", fontsize=10.5, color=color, fontweight="bold")
    ax2.text(0.0, 0.02, "Lower is better. Each surface\nis still summarized independently.", fontsize=10.5, color=MUTED, fontweight="bold")
    add(fig, 26, "REAL PRISM", f"Real PRISM representation benchmark; {evidence['representation_surface_count']} interior surfaces", ["representations.median_only", "representations.fine_radial_profile", "representations.radial_plus_directional", "representation_surface_count"])

    # 27 - align first
    fig, g = _page("The overlap idea", "Instead of compressing each surface alone, align neighboring surfaces first", "CONCEPTUAL", "6 - from stack to map")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    for i in range(3):
        inset = ax.inset_axes([0.03 + i * 0.18, 0.28 + i * 0.08, 0.28, 0.50])
        inset.imshow(np.roll(_surface(stack, 207 + i * 2), i, axis=1), cmap="RdBu", vmin=-0.25, vmax=0.25, alpha=0.72)
        inset.set_xticks([]); inset.set_yticks([])
        inset.set_title(f"surface {i+1}", fontsize=9, color=INK)
    _arrow(ax, (0.60, 0.52), (0.71, 0.52), color=GOLD, lw=4)
    result = ax.inset_axes([0.73, 0.23, 0.24, 0.58])
    result.imshow(_surface(stack, 210), cmap="RdBu", vmin=-0.25, vmax=0.25)
    result.contour(np.abs(np.gradient(_surface(stack, 210), axis=1)), levels=[0.04, 0.08], colors=[GOLD, INK])
    result.set_xticks([]); result.set_yticks([]); result.set_title("repeated geographic support", color=GREEN, fontweight="bold", fontsize=10)
    ax.text(0.42, 0.10, "ALIGN TO GEOGRAPHY", ha="center", fontsize=15, color=GOLD, fontweight="bold")
    ax.text(0.84, 0.10, "THEN REDUCE", ha="center", fontsize=15, color=GREEN, fontweight="bold")
    add(fig, 27, "CONCEPTUAL", "Conceptual align-first workflow using real PRISM surface texture")

    # 28 - measured result
    fig, g = _page("What the feasibility experiment found", f"One bounded real block suggests recoverable geography at {alignment['radius_km']} km", "REAL PRISM", "6 - from stack to map")
    ax = fig.add_subplot(g[1:10, 1:11])
    labels = ["surface correlation", "gradient agreement"]
    relative = [alignment["pearson_relative"], alignment["gradient_relative"]]
    absolute = [alignment["pearson_absolute"], alignment["gradient_absolute"]]
    xx = np.arange(2)
    ax.bar(xx - 0.18, relative, 0.36, color=QUESTION, label="relative coordinates")
    ax.bar(xx + 0.18, absolute, 0.36, color=GREEN, label="absolute geography")
    for x0, value in zip(xx - 0.18, relative): ax.text(x0, value + 0.03, f"{value:.2f}", ha="center", color=QUESTION, fontweight="bold")
    for x0, value in zip(xx + 0.18, absolute): ax.text(x0, value + 0.03, f"{value:.2f}", ha="center", color=GREEN, fontweight="bold")
    ax.set_xticks(xx, labels); ax.set_ylim(0, 1.08); ax.set_ylabel("median agreement at 40 km")
    ax.legend(frameon=False, loc="upper left"); _clean_axes(ax)
    fig.text(0.5, 0.105, "Evidence for a direction - not a final overlap operator and not a production map.", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 28, "REAL PRISM", "Bounded 20 x 20 real-PRISM feasibility experiment", ["alignment.pearson_relative", "alignment.pearson_absolute", "alignment.gradient_relative", "alignment.gradient_absolute"])

    # 29 - local block
    fig, g = _page("Local block", "The current overlap experiment is a 20 x 20 Front Range relational field", "REAL PRISM", "7 - toward CONUS")
    ax = fig.add_subplot(g[0:11, 2:10])
    extent = [float(stack.x.min()), float(stack.x.max()), float(stack.y.min()), float(stack.y.max())]
    im = _delta_heat(ax, _surface(stack, 210), extent=extent, limit=0.25)
    ax.scatter(float(stack.center_x[210]), float(stack.center_y[210]), marker="*", s=170, color=GOLD, edgecolor=INK)
    ax.set(xlabel="longitude", ylabel="latitude")
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03, label="Delta S")
    fig.text(0.5, 0.105, f"{stack_info['surface_count']} focal surfaces | {stack_info['canonical_pairs']:,} canonical pairs | one 90-day window", ha="center", fontsize=13.5, color=INK, fontweight="bold")
    add(fig, 29, "REAL PRISM", "Real 20 x 20 Front Range stack", ["stack.surface_count", "stack.canonical_pairs", "stack.window_days"])

    # 30 - Colorado existing signature
    fig, g = _page("Colorado", "The same pair operation already runs statewide with tiles and halos", "REAL PRISM", "7 - toward CONUS")
    radii = np.asarray(colorado.radius_km.values, dtype=float)
    ridx = int(np.argmin(np.abs(radii - 40)))
    arr = np.asarray(colorado.delta_median.isel(time_window_end=0, radius_km=ridx))
    mask = np.asarray(colorado.output_mask)
    arr = np.where(mask, arr, np.nan)
    ax = fig.add_subplot(g[0:11, 1:9])
    cext = [float(colorado.x.min()), float(colorado.x.max()), float(colorado.y.min()), float(colorado.y.max())]
    im = _delta_heat(ax, arr, extent=cext, limit=max(0.05, float(np.nanquantile(np.abs(arr), 0.98))))
    _state_outline(ax, boundary_path)
    ax.set(xlabel="longitude", ylabel="latitude")
    ax.set_title(f"existing Delta median signature at {radii[ridx]:g} km", color=INK, fontweight="bold")
    fig.colorbar(im, ax=ax, fraction=0.038, pad=0.03, label="Delta S")
    ax2 = fig.add_subplot(g[2:10, 9:12]); ax2.axis("off")
    ax2.text(0.12, 0.78, "streaming", color=COLD, fontsize=13, fontweight="bold")
    ax2.text(0.12, 0.59, "tiles", color=GREEN, fontsize=13, fontweight="bold")
    ax2.text(0.12, 0.40, "halos", color=PURPLE, fontsize=13, fontweight="bold")
    ax2.text(0.12, 0.21, "checkpoints", color=GOLD, fontsize=13, fontweight="bold")
    add(fig, 30, "REAL PRISM", "Existing Colorado synchrony signature; shown as context, not final overlap product", ["sources.colorado"])

    # 31 - CONUS conceptual
    fig, g = _page("CONUS", "Every pixel can be a focal center with a finite surrounding observation window", "CONCEPTUAL", "7 - toward CONUS")
    ax = fig.add_subplot(g[0:10, 1:11]); _draw_usa_grid(ax)
    center_xy = (4.8, 3.7)
    ax.scatter(*center_xy, marker="*", s=230, color=GOLD, edgecolor=INK, zorder=6)
    ax.add_patch(Circle(center_xy, 0.85, fill=False, edgecolor=PURPLE, lw=3, ls="--"))
    ax.text(4.8, 2.65, "finite observation window", ha="center", color=PURPLE, fontsize=12, fontweight="bold")
    fig.text(0.5, 0.105, "Canonical pair identity avoids calculating S(i,j) and S(j,i) as separate evidence.", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 31, "CONCEPTUAL", "Conceptual CONUS grid; no empirical CONUS synchrony result is shown")

    # 32 - compute flow
    fig, g = _page("The computational picture", "We do not need to hold the full relational field densely in memory", "CONCEPTUAL", "7 - toward CONUS")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    stages = [
        ("streaming\nclimate data", COLD),
        ("canonical\npair batches", PURPLE),
        ("local relational\nsurfaces", GOLD),
        ("geographic\nalignment", GREEN),
        ("named map\nproducts", WARM),
    ]
    for i, (label, color) in enumerate(stages):
        x0 = 0.02 + i * 0.195
        ax.add_patch(FancyBboxPatch((x0, 0.42), 0.16, 0.30, boxstyle="round,pad=0.02", facecolor=WHITE, edgecolor=color, lw=2.2))
        ax.text(x0 + 0.08, 0.57, label, ha="center", va="center", color=INK, fontsize=12.5, fontweight="bold")
        if i < len(stages) - 1: _arrow(ax, (x0 + 0.165, 0.57), (x0 + 0.19, 0.57), lw=2.2)
    tags = ["sparse", "tiling", "halos", "parallel", "checkpointed"]
    for i, tag in enumerate(tags):
        ax.text(0.10 + i * 0.195, 0.25, tag, ha="center", fontsize=11, color=MUTED, fontweight="bold")
    ax.text(0.5, 0.08, "Dense S(x,y,dx,dy) is a scientific concept - not a memory requirement.", ha="center", fontsize=15, color=INK, fontweight="bold")
    add(fig, 32, "CONCEPTUAL", "Conceptual scalable flow consistent with CubeDynamics tiling/halo architecture")

    # 33 - candidate meanings
    fig, g = _page("What would the final map mean?", "Candidate products answer different scientific questions", "CONCEPTUAL", "7 - toward CONUS")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    cards = [
        ("A", "magnitude", "How strong?", COLD),
        ("B", "heterogeneity", "How mixed?", PURPLE),
        ("C", "overlap coherence", "How repeatedly supported?", GREEN),
        ("D", "cold-warm asymmetry", "Which tail dominates?", WARM),
        ("E", "relational change", "Where does structure shift?", GOLD),
    ]
    for i, (letter, title, question, color) in enumerate(cards):
        x0 = 0.02 + i * 0.195
        ax.add_patch(FancyBboxPatch((x0, 0.25), 0.17, 0.52, boxstyle="round,pad=0.02", facecolor=WHITE, edgecolor=color, lw=2.2))
        ax.text(x0 + 0.085, 0.68, letter, ha="center", fontsize=20, color=color, fontweight="bold")
        ax.text(x0 + 0.085, 0.51, title, ha="center", fontsize=11.5, color=INK, fontweight="bold", wrap=True)
        ax.text(x0 + 0.085, 0.34, question, ha="center", fontsize=10.5, color=MUTED, wrap=True)
    ax.text(0.5, 0.09, "Do not collapse these into one unnamed 'synchrony score.'", ha="center", fontsize=15, color=INK, fontweight="bold")
    add(fig, 33, "CONCEPTUAL", "Conceptual candidate map meanings; no final operator selected")

    # 34 - what does hot mean
    fig, g = _page("What does 'hot' mean?", "A temperature can be extreme in one climate and ordinary in another", "SYNTHETIC", "8 - the relativism problem")
    rng = np.random.default_rng(20260923)
    mountain = rng.normal(8, 5, 500)
    desert = rng.normal(28, 6, 500)
    for i, (values2, label, color) in enumerate([(mountain, "cool mountain", COLD), (desert, "hot desert", WARM)]):
        ax = fig.add_subplot(g[1:9, i * 6 : (i + 1) * 6])
        ax.hist(values2, bins=30, color=color, alpha=0.70, density=True)
        median = float(np.median(values2)); ax.axvline(median, color=INK, ls="--", lw=2)
        ax.fill_betweenx([0, ax.get_ylim()[1]], median, values2.max(), color=color, alpha=0.12)
        ax.set(title=label, xlabel="temperature (C)", ylabel="density")
        _clean_axes(ax)
    fig.text(0.5, 0.105, "Current implementation: each location uses its own pair-valid median inside the analysis window.", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 34, "SYNTHETIC", "Synthetic contrasting climate distributions; threshold semantics are current CubeDynamics", ["stack.split_quantile", "stack.window_days"])

    # 35 - relative extremes feature
    fig, g = _page("Relative extremes are a feature", "Different climates can both be unusually warm relative to themselves", "SYNTHETIC", "8 - the relativism problem")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    for x0, base, color, label in [(0.18, 8, COLD, "mountain"), (0.62, 28, WARM, "desert")]:
        days = np.arange(12)
        vals = base + np.array([-3, -1, 1, 0, 2, 4, 5, 3, -2, 6, 7, 2])
        inset = ax.inset_axes([x0, 0.32, 0.28, 0.48])
        inset.plot(days, vals, color=color, lw=2)
        med = np.median(vals); inset.axhline(med, color=INK, ls="--")
        warm_mask = vals > med
        inset.scatter(days[warm_mask], vals[warm_mask], color=WARM, s=40, zorder=4)
        inset.set_title(label, color=INK, fontweight="bold"); inset.set_xticks([]); inset.set_ylabel("C")
        _clean_axes(inset)
    _arrow(ax, (0.48, 0.55), (0.60, 0.55), color=GREEN, lw=3, style="<->")
    ax.text(0.54, 0.67, "compare\nrelative state", ha="center", fontsize=13, color=GREEN, fontweight="bold")
    ax.text(0.5, 0.13, "Question enabled: Are both places unusually warm or cold\nrelative to themselves at the same time?", ha="center", fontsize=13, color=INK, fontweight="bold")
    add(fig, 35, "SYNTHETIC", "Synthetic climate histories illustrating local-relative thresholds")

    # 36 - relativity problem
    fig, g = _page("But relativity creates a new problem", "Relative synchrony does not necessarily mean absolute climatic similarity", "SYNTHETIC", "8 - the relativism problem")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    for x0, absolute, relative in [(0.18, "12 C", "+1.3 local SD"), (0.68, "36 C", "+1.2 local SD")]:
        ax.add_patch(Circle((x0, 0.56), 0.15, facecolor=WARM_LIGHT, edgecolor=WARM, lw=3))
        ax.text(x0, 0.60, absolute, ha="center", fontsize=22, color=WARM, fontweight="bold")
        ax.text(x0, 0.49, relative, ha="center", fontsize=12, color=INK, fontweight="bold")
    ax.text(0.5, 0.63, "same relative tail", ha="center", fontsize=15, color=GREEN, fontweight="bold")
    _arrow(ax, (0.35, 0.56), (0.50, 0.56), color=GREEN, lw=3, style="<->")
    _arrow(ax, (0.50, 0.56), (0.53, 0.56), color=GREEN, lw=3, style="<->")
    ax.text(0.5, 0.26, "Very different absolute temperatures, variances, seasons, and climate regimes.", ha="center", fontsize=16, color=INK, fontweight="bold")
    ax.text(0.5, 0.11, "Keep the distinction: relative-extreme synchrony != absolute climate similarity", ha="center", fontsize=16, color=WARM, fontweight="bold")
    add(fig, 36, "SYNTHETIC", "Synthetic absolute/relative contrast")

    # 37 - nested variance washout
    fig, g = _page("Local versus global variance", "A global scale can wash out subtle but coherent regional structure", "CONCEPTUAL", "8 - the relativism problem")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    levels = [(0.5, 0.5, 0.86, 0.72, "GLOBAL", QUESTION), (0.5, 0.5, 0.64, 0.52, "CONTINENTAL", PURPLE), (0.5, 0.5, 0.43, 0.34, "REGIONAL", GREEN), (0.5, 0.5, 0.22, 0.17, "LOCAL", GOLD)]
    for cx, cy, w, h, label, color in levels:
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.01", fill=False, edgecolor=color, lw=3))
        ax.text(cx - w / 2 + 0.02, cy + h / 2 - 0.055, label, color=color, fontsize=11, fontweight="bold")
    ax.text(0.5, 0.47, "Colorado signal", ha="center", fontsize=13, color=GOLD, fontweight="bold")
    ax.text(0.5, 0.055, "Do not let Sahara-vs-Arctic variation set the only scale\nfor Front Range-vs-Western Slope structure.", ha="center", fontsize=13, color=INK, fontweight="bold")
    add(fig, 37, "CONCEPTUAL", "Conceptual nested variance scales")

    # 38 - strategy options
    fig, g = _page("The normalization question", "Five strategies for discussion - none is selected here", "CONCEPTUAL", "8 - the relativism problem")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    strategies = [
        ("A", "LOCAL RELATIVE", "comparable extremes; may hide absolute context", COLD),
        ("B", "REGIONAL", "climate-aware; depends on region definitions", GREEN),
        ("C", "MULTISCALE", "preserves nested departures; more complex", PURPLE),
        ("D", "LOCAL + ABSOLUTE", "keeps both meanings; two-axis product", WARM),
        ("E", "HIERARCHICAL", "separates levels; modeling assumptions", GOLD),
    ]
    for i, (letter, title, note, color) in enumerate(strategies):
        y = 0.84 - i * 0.17
        ax.add_patch(Circle((0.08, y), 0.045, facecolor=color, edgecolor=WHITE, lw=1.2))
        ax.text(0.08, y, letter, ha="center", va="center", color=WHITE, fontweight="bold")
        ax.text(0.16, y + 0.018, title, fontsize=12.5, color=INK, fontweight="bold")
        ax.text(0.16, y - 0.045, note, fontsize=11, color=MUTED)
    ax.text(0.72, 0.48, "CHOICE =\nSCIENTIFIC QUESTION", ha="center", va="center", fontsize=19, color=QUESTION, fontweight="bold", bbox=dict(boxstyle="round,pad=0.7", facecolor=WHITE, edgecolor=QUESTION, lw=2))
    add(fig, 38, "CONCEPTUAL", "Conceptual normalization strategy menu")

    # 39 - reference frames
    fig, g = _page("The answer can depend on the reference frame", "Temporal reference, spatial reference, window, and normalization must be explicit", "CONCEPTUAL", "9 - reference-scale problem")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    boxes = [
        (0.06, 0.12, 0.48, 0.74, "GLOBE", QUESTION),
        (0.10, 0.19, 0.40, 0.60, "CONTINENT", PURPLE),
        (0.15, 0.27, 0.30, 0.44, "STATE / REGION", GREEN),
        (0.21, 0.36, 0.18, 0.25, "LOCAL", GOLD),
    ]
    for x0, y0, width, height, label, color in boxes:
        ax.add_patch(FancyBboxPatch((x0, y0), width, height, boxstyle="round,pad=0.008", fill=False, edgecolor=color, lw=2.6))
        ax.text(x0 + 0.018, y0 + height - 0.055, label, color=color, fontsize=9.5, fontweight="bold")
    ax.text(0.75, 0.73, "REFERENCE DISTRIBUTION", ha="center", color=INK, fontsize=12, fontweight="bold")
    ax.text(0.75, 0.61, "changes what counts\nas unusual", ha="center", color=MUTED, fontsize=11)
    ax.text(0.75, 0.43, "OBSERVATION WINDOW", ha="center", color=INK, fontsize=12, fontweight="bold")
    ax.text(0.75, 0.31, "changes which relationships\nare visible", ha="center", color=MUTED, fontsize=11)
    ax.text(0.5, 0.07, "A synchrony product is not scale-free.", ha="center", fontsize=16, color=WARM, fontweight="bold")
    add(fig, 39, "CONCEPTUAL", "Conceptual reference-frame dependence")

    # 40 - window sensitivity
    fig, g = _page("We should not search for one magic radius", "Rmax is an observation limit - not automatically the scale of synchrony", "REAL PRISM", "9 - reference-scale problem")
    rows = evidence["windows"]
    labels = [f"{int(r['left_radius_km'])}->{int(r['right_radius_km'])} km" for r in rows]
    pearson = [r["pearson"] for r in rows]
    rank = [r["spearman"] for r in rows]
    ax = fig.add_subplot(g[1:10, 1:11])
    xx = np.arange(len(rows)); ax.bar(xx - 0.18, pearson, 0.36, color=COLD, label="Pearson")
    ax.bar(xx + 0.18, rank, 0.36, color=GREEN, label="rank")
    for x0, value in zip(xx - 0.18, pearson): ax.text(x0, value + 0.02, f"{value:.2f}", ha="center", color=COLD, fontweight="bold")
    for x0, value in zip(xx + 0.18, rank): ax.text(x0, value + 0.02, f"{value:.2f}", ha="center", color=GREEN, fontweight="bold")
    ax.set_xticks(xx, labels); ax.set_ylim(0, 1.05); ax.set_ylabel("candidate-map agreement")
    ax.legend(frameon=False); _clean_axes(ax)
    fig.text(0.5, 0.105, "Ask whether geographic organization persists as the observation window expands.", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 40, "REAL PRISM", "Real PRISM 20/40/60 km observation-window sensitivity", ["windows"])

    # 41 - canonical pairs first
    fig, g = _page("Keep relationships first", "Canonical pair relationships are the durable scientific object", "CONCEPTUAL", "10 - a multiscale hypothesis")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    nodes = [(0.16, 0.72), (0.35, 0.36), (0.58, 0.70), (0.78, 0.33), (0.88, 0.73)]
    edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4)]
    for edge_id, (i, j) in enumerate(edges):
        xi, yi = nodes[i]; xj, yj = nodes[j]
        color = COLD if edge_id % 3 == 0 else WARM if edge_id % 3 == 1 else GREEN
        ax.plot([xi, xj], [yi, yj], color=color, lw=4, alpha=0.8)
        ax.text((xi + xj) / 2, (yi + yj) / 2 + 0.035, f"pair {edge_id+1}", ha="center", fontsize=9, color=color, fontweight="bold")
    for i, (x0, y0) in enumerate(nodes):
        ax.scatter(x0, y0, s=480, color=WHITE, edgecolor=INK, lw=2.2, zorder=5)
        ax.text(x0, y0, str(i + 1), ha="center", va="center", fontsize=15, color=INK, fontweight="bold")
    ax.text(0.5, 0.10, "Store identity + endpoints + cold + warm + Delta + support + provenance.", ha="center", fontsize=15, color=INK, fontweight="bold")
    add(fig, 41, "CONCEPTUAL", "Conceptual canonical pair layer")

    # 42 - derive scales
    fig, g = _page("Then ask questions at multiple scales", "Derive views from the same pair layer whenever definitions permit", "CONCEPTUAL", "10 - a multiscale hypothesis")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.05, 0.37), 0.22, 0.28, boxstyle="round,pad=0.03", facecolor=WHITE, edgecolor=INK, lw=2.5))
    ax.text(0.16, 0.51, "canonical\npair layer", ha="center", va="center", fontsize=16, color=INK, fontweight="bold")
    targets = [(0.43, 0.75, "LOCAL", GOLD), (0.70, 0.75, "REGIONAL", GREEN), (0.43, 0.25, "CONTINENTAL", PURPLE), (0.70, 0.25, "GLOBAL", QUESTION)]
    for x0, y0, label, color in targets:
        ax.add_patch(FancyBboxPatch((x0, y0 - 0.11), 0.22, 0.22, boxstyle="round,pad=0.02", facecolor=WHITE, edgecolor=color, lw=2.2))
        ax.text(x0 + 0.11, y0, label, ha="center", va="center", fontsize=13, color=color, fontweight="bold")
        _arrow(ax, (0.28, 0.51), (x0 - 0.015, y0), color=color, lw=2.2)
    ax.text(0.5, 0.07, "Reuse relationships; revisit threshold definitions when the scientific reference changes.", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 42, "CONCEPTUAL", "Conceptual multiscale reuse of canonical relationships")

    # 43 - multiscale maps
    fig, g = _page("A multiscale synchrony map", "One location may need local, regional, and broader-scale values", "CONCEPTUAL", "10 - a multiscale hypothesis")
    yy, xx = np.mgrid[-1:1:80j, -1:1:120j]
    maps = [
        np.sin(7 * xx) * np.cos(5 * yy) + 0.3 * np.exp(-((xx + 0.4) ** 2 + yy**2) / 0.04),
        np.sin(3 * xx) * np.cos(2 * yy) + 0.6 * np.exp(-((xx + 0.2) ** 2 + (yy - 0.1) ** 2) / 0.25),
        0.8 * xx - 0.35 * yy + 0.25 * np.sin(2 * yy),
    ]
    labels2 = ["LOCAL VIEW", "REGIONAL VIEW", "CONTINENTAL VIEW"]
    for i, (arr, label) in enumerate(zip(maps, labels2)):
        ax = fig.add_subplot(g[1:10, i * 4 : (i + 1) * 4])
        ax.imshow(arr, cmap="RdBu", vmin=-1.4, vmax=1.4, origin="lower")
        ax.scatter(66, 42, marker="*", s=120, color=GOLD, edgecolor=INK)
        ax.set_title(label, color=INK, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([])
    fig.text(0.5, 0.105, "Hypothesis for discussion - these scale-indexed maps are not yet implemented products.", ha="center", fontsize=14, color=INK, fontweight="bold")
    add(fig, 43, "CONCEPTUAL", "Conceptual multiscale fields; no empirical result")

    # 44 - dual axes
    fig, g = _page("Relative + absolute", "A two-axis view may prevent synchrony from being mistaken for climatic similarity", "CONCEPTUAL", "10 - a multiscale hypothesis")
    ax = fig.add_subplot(g[1:10, 1:11])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axvline(0.5, color=GRID, lw=1.5); ax.axhline(0.5, color=GRID, lw=1.5)
    points = [(0.78, 0.82, COLD), (0.84, 0.22, WARM), (0.26, 0.75, GREEN), (0.20, 0.28, QUESTION)]
    for x0, y0, color in points: ax.scatter(x0, y0, s=160, color=color, edgecolor=WHITE, lw=1.2)
    ax.text(0.75, 0.92, "relative tails move together\nand climate states are similar", ha="center", color=INK, fontsize=11, fontweight="bold")
    ax.text(0.76, 0.08, "relative tails move together\nbut absolute states differ", ha="center", color=INK, fontsize=11, fontweight="bold")
    ax.text(0.24, 0.91, "absolute states similar\nwithout tail synchrony", ha="center", color=INK, fontsize=11, fontweight="bold")
    ax.set_xlabel("relative-extreme synchrony ->", fontsize=13)
    ax.set_ylabel("absolute climate-state similarity ->", fontsize=13)
    ax.set_xticks([]); ax.set_yticks([])
    ax.spines[:].set_color(INK)
    add(fig, 44, "CONCEPTUAL", "Conceptual two-axis representation")

    # 45 - station context
    fig, g = _page("PRISM is a gridded model", "Raw GHCN-Daily stations provide another source of evidence", "REAL GHCN", "11 - station validation")
    manifest: pd.DataFrame = arrays["station_manifest"]
    station_pairs: pd.DataFrame = arrays["station_pairs"]
    ax = fig.add_subplot(g[0:11, 1:11])
    _state_outline(ax, boundary_path)
    indexed = manifest.set_index("station_id")
    for row in station_pairs.itertuples():
        a = indexed.loc[row.station_i]; b = indexed.loc[row.station_j]
        ax.plot([a.longitude, b.longitude], [a.latitude, b.latitude], color="#94A3B8", lw=0.7, alpha=0.45)
    sc = ax.scatter(manifest.longitude, manifest.latitude, c=manifest.elevation_m, cmap="terrain", s=48, edgecolor=INK, lw=0.6, zorder=4)
    fig.colorbar(sc, ax=ax, fraction=0.038, pad=0.03, label="station elevation (m)")
    ax.set(xlabel="longitude", ylabel="latitude")
    ax.set_title(f"{stations['count']} selected stations | {stations['pair_count']} eligible pair edges", color=INK, fontweight="bold")
    add(fig, 45, "REAL GHCN", "NOAA/NCEI GHCN-Daily station branch; Colorado outline for context", ["stations.count", "stations.pair_count"])

    # 46 - same station relationship
    fig, g = _page("Build the same relationships from stations", "Irregular station pairs use the SAME cold, warm, and Delta definitions", "REAL GHCN", "11 - station validation")
    row = station_pairs.iloc[0]
    a = indexed.loc[row.station_i]; b = indexed.loc[row.station_j]
    ax = fig.add_subplot(g[0:11, 0:7])
    _state_outline(ax, boundary_path)
    ax.scatter([a.longitude, b.longitude], [a.latitude, b.latitude], s=180, color=[COLD, WARM], edgecolor=INK, zorder=4)
    ax.plot([a.longitude, b.longitude], [a.latitude, b.latitude], color=INK, lw=3)
    ax.text(a.longitude, a.latitude + 0.13, "station A", ha="center", color=COLD, fontweight="bold")
    ax.text(b.longitude, b.latitude + 0.13, "station B", ha="center", color=WARM, fontweight="bold")
    ax.set(xlabel="longitude", ylabel="latitude")
    ax2 = fig.add_subplot(g[1:10, 8:12]); ax2.axis("off")
    _callout(ax2, 0.5, 0.78, f"cold  {row.station_cold:.2f}", color=COLD, size=15)
    _callout(ax2, 0.5, 0.50, f"warm  {row.station_warm:.2f}", color=WARM, size=15)
    _callout(ax2, 0.5, 0.22, f"Delta  {row.station_delta:.2f}", color=INK, size=15)
    add(fig, 46, "REAL GHCN", "One real GHCN-Daily station pair from the frozen feasibility branch", ["stations.example_pair", "sources.station_pairs"])

    # 47 - station results
    fig, g = _page("Current preliminary result", "Descriptive station-vs-PRISM pair agreement - not independent validation", "REAL GHCN", "11 - station validation")
    ax = fig.add_subplot(g[1:9, 0:8])
    metrics = ["cold", "warm", "Delta"]
    vals = [stations["cold_r"], stations["warm_r"], stations["delta_r"]]
    colors = [COLD, WARM, GREEN]
    ax.bar(np.arange(3), vals, color=colors, width=0.58)
    for x0, value, color in zip(range(3), vals, colors): ax.text(x0, value + 0.04, f"r = {value:.2f}", ha="center", color=color, fontsize=13, fontweight="bold")
    ax.set_xticks(range(3), metrics); ax.set_ylim(-0.05, 1.05); ax.set_ylabel("pairwise station-vs-PRISM correlation")
    _clean_axes(ax)
    ax2 = fig.add_subplot(g[1:10, 9:12]); ax2.axis("off")
    ax2.text(0.0, 0.88, "ENCOURAGING", color=GREEN, fontsize=11, fontweight="bold")
    ax2.text(0.0, 0.76, "cold + Delta", color=INK, fontsize=13, fontweight="bold")
    ax2.text(0.0, 0.57, "WEAK", color=WARM, fontsize=11, fontweight="bold")
    ax2.text(0.0, 0.45, "warm", color=INK, fontsize=13, fontweight="bold")
    ax2.text(0.0, 0.25, "LIMITS", color=QUESTION, fontsize=11, fontweight="bold")
    ax2.text(0.0, 0.05, "sparse graph\nshared stations\nPRISM contribution\nstatus: UNKNOWN", color=INK, fontsize=9.5, fontweight="bold", va="bottom")
    add(fig, 47, "REAL GHCN", f"{stations['count']} GHCN stations, {stations['pair_count']} shared-station edges; all PRISM contribution statuses UNKNOWN", ["stations.cold_r", "stations.warm_r", "stations.delta_r", "stations.contribution_status", "stations.pair_count", "stations.count"])

    # 48 - why stations
    fig, g = _page("Why stations matter", "They offer an external observational test for at least some gridded structure", "CONCEPTUAL", "11 - station validation")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.06, 0.35), 0.30, 0.34, boxstyle="round,pad=0.03", facecolor=WHITE, edgecolor=COLD, lw=2.5))
    ax.text(0.21, 0.52, "gridded relational\ngeography", ha="center", va="center", fontsize=16, color=INK, fontweight="bold")
    ax.add_patch(FancyBboxPatch((0.64, 0.35), 0.30, 0.34, boxstyle="round,pad=0.03", facecolor=WHITE, edgecolor=GREEN, lw=2.5))
    ax.text(0.79, 0.52, "raw-station\nrelationships", ha="center", va="center", fontsize=16, color=INK, fontweight="bold")
    _arrow(ax, (0.38, 0.52), (0.62, 0.52), color=GOLD, lw=4, style="<->")
    ax.text(0.5, 0.66, "future holdout test", ha="center", color=GOLD, fontsize=13, fontweight="bold")
    ax.text(0.5, 0.19, "Needed: temporal replication + leave-one-station-out + spatial-block holdout\n+ product independence audit", ha="center", fontsize=12, color=INK, fontweight="bold")
    add(fig, 48, "CONCEPTUAL", "Conceptual future station-validation role, informed by current limitations")

    # 49 - complete pipeline
    fig, g = _page("The entire method on one page", "Every arrow preserves a scientific meaning - the reference frame remains open", "CONCEPTUAL", "12 - put it together")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    labels = [
        "WEATHER\nTHROUGH TIME", "HOT / COLD\nCLASSIFICATION", "PAIR\nSYNCHRONY", "ONE LOCAL\nSURFACE",
        "MOVE CENTER", "OVERLAPPING\nSTACK", "ABSOLUTE\nALIGNMENT", "RELATIONAL\nFIELD",
        "MULTISCALE\nVIEW", "COLORADO", "CONUS", "GLOBAL",
    ]
    colors = [COLD, WARM, PURPLE, GOLD, GOLD, PURPLE, GREEN, GREEN, QUESTION, COLD, COLD, QUESTION]
    for i, (label, color) in enumerate(zip(labels, colors)):
        col = i % 6; rown = i // 6
        x0 = 0.02 + col * 0.145; y0 = 0.65 - rown * 0.43
        ax.add_patch(FancyBboxPatch((x0, y0), 0.12, 0.22, boxstyle="round,pad=0.014", facecolor=WHITE, edgecolor=color, lw=1.8))
        ax.text(x0 + 0.06, y0 + 0.11, label, ha="center", va="center", fontsize=8.9, color=INK, fontweight="bold")
        if col < 5: _arrow(ax, (x0 + 0.122, y0 + 0.11), (x0 + 0.142, y0 + 0.11), lw=1.5)
        elif rown == 0: _arrow(ax, (x0 + 0.06, y0 - 0.01), (0.02, 0.43), lw=1.8)
    ax.text(0.94, 0.55, "OPEN\nQUESTION", ha="center", color=WARM, fontsize=11, fontweight="bold")
    ax.text(0.94, 0.37, "What is the\nappropriate\nreference frame?", ha="center", color=INK, fontsize=11, fontweight="bold")
    add(fig, 49, "CONCEPTUAL", "Conceptual complete pipeline")

    # 50 - known/deciding
    fig, g = _page("What we know versus what we are deciding", "Evidence and open design choices belong in separate columns", "CONCEPTUAL", "12 - put it together")
    ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    known = ["pairwise tail calculation", "local surface construction", "surfaces overlap", "absolute alignment helps", "scalar reductions lose geometry", "canonical symmetry"]
    deciding = ["second-stage operator", "primary map quantity", "local / regional / global views", "global normalization", "window strategy", "validation sufficiency", "weak warm agreement"]
    ax.text(0.25, 0.93, "CURRENTLY SUPPORTED", ha="center", color=GREEN, fontsize=15, fontweight="bold")
    ax.text(0.75, 0.93, "STILL DECIDING", ha="center", color=WARM, fontsize=15, fontweight="bold")
    for i, item in enumerate(known): ax.text(0.08, 0.80 - i * 0.12, f"+  {item}", color=INK, fontsize=12.3, fontweight="bold")
    for i, item in enumerate(deciding): ax.text(0.56, 0.80 - i * 0.105, f"?  {item}", color=INK, fontsize=12.0, fontweight="bold")
    ax.plot([0.5, 0.5], [0.08, 0.88], color=GRID, lw=2)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    add(fig, 50, "CONCEPTUAL", "Evidence/open-decision synthesis grounded in current repository artifacts")

    # 51-55 - discussion questions
    questions = [
        (51, "WHAT SHOULD ONE PIXEL ON THE FINAL MAP MEAN?", ["average synchrony", "local relational coherence", "cold", "warm", "Delta", "multiple named values"]),
        (52, "WHAT SHOULD 'HOT' AND 'COLD' MEAN GLOBALLY?", ["pixel-relative", "region-relative", "globally standardized", "multiscale"]),
        (53, "HOW MUCH LOCAL VARIATION MUST WE PRESERVE?", ["If a global view is stable but hides meaningful regional structure, is that acceptable?", "Which regional patterns must the method preserve by design?"]),
        (54, "IS THERE ONE SYNCHRONY MAP OR A FAMILY OF MAPS?", ["cold  x  local / regional / global", "warm  x  local / regional / global", "Delta x  local / regional / global"]),
        (55, "WHAT WOULD CONVINCE US THE MAP IS REAL?", ["observation-window stability", "temporal replication", "raw-station support", "synthetic recovery", "independent climate products", "interpretable geography"]),
    ]
    for number, question, options in questions:
        fig, g = _page(f"Question {number - 50}", "Group discussion", "CONCEPTUAL", "13 - discussion")
        ax = fig.add_subplot(g[0:11, 0:12]); ax.axis("off")
        ax.text(0.5, 0.80, question, ha="center", va="center", fontsize=22 if len(question) < 48 else 18, color=INK, fontweight="bold")
        if len(options) <= 4:
            for i, option in enumerate(options):
                y = 0.58 - i * 0.14
                ax.text(0.5, y, option, ha="center", fontsize=14, color=[COLD, GREEN, PURPLE, WARM][i % 4], fontweight="bold", wrap=True)
        else:
            for i, option in enumerate(options):
                col = i % 2; rown = i // 2
                x0 = 0.28 + col * 0.44; y = 0.57 - rown * 0.15
                ax.text(x0, y, option, ha="center", fontsize=12.5, color=[COLD, WARM, GREEN, PURPLE, GOLD, QUESTION][i % 6], fontweight="bold", wrap=True)
        if number == 55:
            ax.text(0.5, 0.08, "We now understand the object well enough to decide how it should scale.", ha="center", fontsize=16, color=GREEN, fontweight="bold")
        add(fig, number, "CONCEPTUAL", "Structured scientific discussion prompt")

    if len(pages) != 55:
        raise AssertionError(f"Expected 55 pages, built {len(pages)}")
    return pages, provenance


def assemble_pdf(pages: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(".partial.pdf")
    width, height = landscape(letter)
    pdf = canvas.Canvas(str(partial), pagesize=(width, height), pageCompression=1)
    pdf.setTitle("From two pixels to a planet: understanding synchrony as a relational field")
    pdf.setAuthor("CubeDynamics")
    pdf.setSubject("Visual discussion guide for cold, warm, and Delta synchrony scaling")
    for page in pages:
        pdf.drawImage(str(page), 0, 0, width=width, height=height, preserveAspectRatio=True, anchor="c")
        pdf.showPage()
    pdf.save()
    partial.replace(output)


def validate_page_provenance(provenance: dict[str, dict[str, object]]) -> None:
    """Require every empirical page to declare live artifact dependencies."""

    expected = {str(i) for i in range(1, 56)}
    if set(provenance) != expected:
        raise ValueError("Figure provenance must contain exactly pages 1 through 55")
    missing = [
        page
        for page, entry in provenance.items()
        if str(entry["data_class"]).startswith("REAL") and not entry["empirical_keys"]
    ]
    if missing:
        raise ValueError(f"Empirical pages are missing artifact keys: {missing}")


def write_speaker_guide(bundle: Path) -> None:
    lines = [
        "# Speaker guide: From two pixels to a planet",
        "",
        "Use one page at a time. Pause on the question before advancing.",
        "",
    ]
    for page, (title, purpose, point, confusion, question) in enumerate(PAGE_GUIDE, 1):
        lines.extend(
            [
                f"## Page {page}: {title}",
                "",
                f"- **Purpose:** {purpose}",
                f"- **Main point:** {point}",
                f"- **Likely confusion:** {confusion}",
                f"- **Ask the group:** {question}",
                "",
            ]
        )
    (bundle / "speaker_guide.md").write_text("\n".join(lines), encoding="utf-8")


def write_glossary(bundle: Path) -> None:
    entries = [
        ("Cold synchrony", "Spearman rank correlation calculated only on pair-valid dates when both locations' daily minimum temperatures are at or below their own median thresholds in the analysis window."),
        ("Warm synchrony", "Spearman rank correlation calculated only on pair-valid dates when both locations' daily maximum temperatures are above their own median thresholds in the analysis window."),
        ("Delta synchrony", "Cold synchrony minus warm synchrony. Positive means cold-tail synchrony is stronger; negative means warm-tail synchrony is stronger."),
        ("Focal / center pixel", "The reference location held fixed while it is compared with locations in its observation window."),
        ("Pair", "Two geographic locations plus their conditional relationship and support information."),
        ("Local synchrony surface", "A 2-D map of pair relationships between one focal center and every comparison location in its local domain."),
        ("Stack", "The collection of local surfaces created by moving the focal center. It is a stack of relationships, not repeated temperature maps."),
        ("Relative coordinates", "Offsets dx and dy from the focal center, which is always represented as (0,0)."),
        ("Absolute geography", "The fixed latitude/longitude or grid coordinates of the focal and comparison locations."),
        ("Canonical pair", "One undirected identity for endpoints i and j, so S(i,j) and S(j,i) are not counted as independent evidence."),
        ("Relational field", "The full collection S(x,y,dx,dy): focal geography plus within-surface relative geometry."),
        ("Overlap", "Multiple focal-center surfaces revisiting the same absolute geographic cells or edges through different relationships."),
        ("Observation window", "The finite spatial neighborhood within which pairs are evaluated; its maximum radius is an observation limit, not automatically a characteristic synchrony scale."),
        ("Local normalization", "Defining states relative to each location's own distribution or local context."),
        ("Global normalization", "Defining states or scales from a pooled global reference; useful for some comparisons but capable of washing out regional variation."),
    ]
    lines = ["# One-page glossary", "", "Concise terms used in the discussion PDF.", ""]
    for term, definition in entries:
        lines.append(f"**{term}.** {definition}")
        lines.append("")
    (bundle / "glossary.md").write_text("\n".join(lines), encoding="utf-8")


def write_unresolved_decisions(bundle: Path) -> None:
    decisions = [
        "What one pixel in the final product should mean, and whether one pixel needs multiple named values.",
        "Which second-stage overlap operator is scientifically interpretable and robust across time and space.",
        "How local, regional, continental, and global representations should coexist.",
        "Whether hot/cold definitions remain pixel-relative, become region-relative, or are represented at multiple scales.",
        "How to retain absolute climate context alongside relative-extreme synchrony.",
        "How much local variance a continental/global representation must preserve by design.",
        "How observation-window sensitivity should be evaluated without claiming one magic radius.",
        "What temporal replication, station holdout, spatial-block holdout, and independent-product evidence are sufficient.",
        "Why warm station-vs-PRISM pair agreement is weak in the current preliminary branch.",
        "When an experimental aligned-view layer is mature enough for a public CubeDynamics verb.",
    ]
    lines = ["# Unresolved scientific decisions", "", "These are discussion decisions, not implementation defects.", ""]
    lines.extend(f"{i}. {decision}" for i, decision in enumerate(decisions, 1))
    lines.extend(["", "The current endpoint is deliberately: *we understand the object well enough to decide how it should scale.*", ""])
    (bundle / "unresolved_scientific_decisions.md").write_text("\n".join(lines), encoding="utf-8")


def write_readme(bundle: Path, output: Path) -> None:
    text = f"""# Synchrony from pixels to planet

This bundle accompanies `{output.relative_to(ROOT)}`.

## Contents

- `figures/page_01.png` through `figures/page_55.png`: the complete generated page figures.
- `speaker_guide.md`: purpose, main point, likely confusion, and discussion question for every page.
- `glossary.md`: concise one-page glossary.
- `unresolved_scientific_decisions.md`: decisions intentionally left open.
- `empirical_values.json`: every empirical number used by the deck plus source hashes.
- `figure_manifest.json`: page classification and empirical-key provenance.

## Regenerate

From the repository root:

```bash
.venv/bin/python scripts/build_synchrony_pedagogy.py
```

The build requires the current PRISM stack, Colorado signature, and bounded
feasibility artifacts already present under `artifacts/`. It performs no live
network access. Cold/warm pair values are recomputed with the installed
`one_tail_spearman` implementation and asserted against the stored stack.

## Validate

```bash
.venv/bin/python -m pytest tests/test_synchrony_pedagogy.py -q
pdfinfo {output.relative_to(ROOT)}
```

Render for visual inspection:

```bash
mkdir -p tmp/pdfs/synchrony_from_pixels_to_planet_rendered
pdftoppm -png -r 100 {output.relative_to(ROOT)} tmp/pdfs/synchrony_from_pixels_to_planet_rendered/page
```

Every page carries one of four data labels: `REAL PRISM`, `REAL GHCN`,
`SYNTHETIC`, or `CONCEPTUAL`. CONUS, global, and proposed multiscale products
are intentionally conceptual.
"""
    (bundle / "README.md").write_text(text, encoding="utf-8")


def write_manifests(bundle: Path, evidence: dict[str, object], provenance: dict[str, dict[str, object]], output: Path) -> None:
    (bundle / "empirical_values.json").write_text(
        json.dumps(serializable_empirical_values(evidence), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    figure_manifest = {
        "analysis": "synchrony_from_pixels_to_planet_pedagogy",
        "page_count": 55,
        "figures": provenance,
        "pdf": {
            "path": str(output.relative_to(ROOT)),
            "bytes": output.stat().st_size,
            "sha256": _sha256(output),
        },
    }
    (bundle / "figure_manifest.json").write_text(json.dumps(figure_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = _parser().parse_args()
    output = args.output.resolve()
    bundle = args.bundle.resolve()
    figures = bundle / "figures"
    bundle.mkdir(parents=True, exist_ok=True)
    if figures.exists() and not args.keep_existing_figures:
        shutil.rmtree(figures)
    figures.mkdir(parents=True, exist_ok=True)

    evidence = load_empirical_evidence(
        args.feasibility.resolve(),
        args.stack.resolve(),
        args.cube.resolve(),
        args.colorado.resolve(),
    )
    pages, provenance = build_pages(evidence, figures, args.boundary.resolve())
    validate_page_provenance(provenance)
    assemble_pdf(pages, output)
    write_speaker_guide(bundle)
    write_glossary(bundle)
    write_unresolved_decisions(bundle)
    write_readme(bundle, output)
    write_manifests(bundle, evidence, provenance, output)
    print(f"Wrote {output} ({len(pages)} pages)")
    print(f"Wrote companion bundle {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
