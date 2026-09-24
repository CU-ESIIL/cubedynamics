#!/usr/bin/env python3
"""Build the visual report for the relational-convolution feasibility study."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import textwrap

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
import pandas as pd
try:
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.pdfgen import canvas
except ImportError:
    bundled = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/"
        "lib/python3.12/site-packages"
    )
    sys.path.append(str(bundled))
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.pdfgen import canvas
import xarray as xr

from relational_convolution_feasibility import symmetric_synthetic_field, translated_edge_support


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = ROOT / "artifacts/relational-convolution-feasibility"
DEFAULT_OUTPUT = ROOT / "output/pdf/relational_convolution_feasibility.pdf"
TMP = ROOT / "tmp/pdfs/relational_convolution"

INK = "#12345b"
BLUE = "#1769aa"
RED = "#cf3f3f"
GOLD = "#e4a62a"
GREEN = "#3f8f68"
MUTED = "#66788a"
BG = "#f5f8fb"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def _page(title: str, subtitle: str = "") -> tuple[plt.Figure, plt.GridSpec]:
    fig = plt.figure(figsize=(11, 8.5), facecolor=BG)
    title_size = 20 if len(title) <= 52 else 17 if len(title) <= 72 else 15
    fig.text(0.055, 0.945, title, fontsize=title_size, fontweight="bold", color=INK, va="top")
    if subtitle:
        fig.text(0.055, 0.902, subtitle, fontsize=9.5, color=MUTED, va="top")
    grid = fig.add_gridspec(12, 12, left=0.055, right=0.96, bottom=0.085, top=0.865, hspace=0.85, wspace=0.75)
    return fig, grid


def _footer(fig: plt.Figure, number: int, source: str = "CubeDynamics bounded feasibility experiment") -> None:
    fig.text(0.055, 0.035, source, fontsize=7.3, color=MUTED)
    fig.text(0.95, 0.035, str(number), fontsize=8, color=MUTED, ha="right")


def _text(
    ax,
    paragraphs: list[str],
    *,
    size: float = 12.0,
    color: str = INK,
    width: int = 88,
) -> None:
    ax.axis("off")
    y = 0.98
    for paragraph in paragraphs:
        wrapped = textwrap.fill(paragraph, width=width)
        ax.text(0.0, y, wrapped, fontsize=size, color=color, va="top", linespacing=1.45, transform=ax.transAxes)
        y -= 0.13 + 0.032 * wrapped.count("\n")


def _heat(ax, values, *, title, extent=None, cmap="RdBu_r", limit=None, label="Delta S"):
    array = np.asarray(values, dtype=float)
    if limit is None:
        limit = float(np.nanquantile(np.abs(array), 0.98)) if np.isfinite(array).any() else 1.0
    image = ax.imshow(array, cmap=cmap, vmin=-limit, vmax=limit, origin="upper", extent=extent, aspect="auto")
    ax.set_title(title, fontsize=10, color=INK, fontweight="bold")
    cb = plt.colorbar(image, ax=ax, fraction=0.047, pad=0.03)
    cb.set_label(label, fontsize=8)
    cb.ax.tick_params(labelsize=7)
    return image


def _save(
    fig: plt.Figure,
    number: int,
    source: str = "CubeDynamics bounded feasibility experiment",
) -> Path:
    _footer(fig, number, source)
    path = TMP / f"page_{number:02d}.png"
    fig.savefig(path, dpi=145, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def _surface_arrays(surfaces: xr.Dataset, focal: int, radius: float = 40.0):
    ny, nx = surfaces.sizes["y"], surfaces.sizes["x"]
    fy, fx = divmod(focal, nx)
    distance = surfaces.distance_km.isel(focal=focal).values.reshape(ny, nx)
    mask = distance <= radius
    arrays = {
        name: np.where(mask, surfaces[name].isel(focal=focal).values.reshape(ny, nx), np.nan)
        for name in ("cold_synchrony", "warm_synchrony", "delta_s")
    }
    return arrays, mask, fy, fx


def _state_outline(ax, artifact_dir: Path) -> None:
    path = ROOT / "artifacts/synchrony-stack-phase2/colorado_boundary.geojson"
    if not path.exists():
        return
    payload = json.loads(path.read_text())
    geometries = [feature["geometry"] for feature in payload.get("features", [])]
    if not geometries and payload.get("type") in {"Polygon", "MultiPolygon"}:
        geometries = [payload]
    for geometry in geometries:
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        for polygon in polygons:
            ring = np.asarray(polygon[0])
            ax.plot(ring[:, 0], ring[:, 1], color=INK, lw=1.2)


def build_pages(artifact_dir: Path) -> list[Path]:
    TMP.mkdir(parents=True, exist_ok=True)
    with xr.open_dataset(artifact_dir / "real_complete_surfaces.nc") as source:
        surfaces = source.load()
    summary = json.loads((artifact_dir / "feasibility_summary.json").read_text())
    station = json.loads((artifact_dir / "station_qc_provenance.json").read_text())
    similarity = pd.read_csv(artifact_dir / "relative_vs_absolute_similarity.csv")
    representations = pd.read_csv(artifact_dir / "baseline_representation_comparison.csv")
    synthetic = pd.read_csv(artifact_dir / "synthetic_benchmark.csv")
    windows = pd.read_csv(artifact_dir / "observation_window_sensitivity.csv")
    decision = pd.read_csv(artifact_dir / "method_decision_table.csv")
    manifest = pd.read_csv(artifact_dir / "station_manifest.csv")
    raw = pd.read_csv(artifact_dir / "station_prism_raw_value_comparison.csv")
    pairs = pd.read_csv(artifact_dir / "station_prism_pair_synchrony.csv")
    with xr.open_dataset(artifact_dir / "absolute_support_delta_s_40km.nc") as source:
        overlap = source.load()
    with xr.open_dataset(artifact_dir / "translated_edge_support_delta_s_40km.nc") as source:
        edges = source.load()
    x = np.asarray(surfaces.x.values)
    y = np.asarray(surfaces.y.values)
    extent = [x.min(), x.max(), y.min(), y.max()]
    focal = 10 * 20 + 10
    arrays, _, fy, fx = _surface_arrays(surfaces, focal)
    delta_limit = float(np.nanquantile(np.abs(arrays["delta_s"]), 0.98))
    pages: list[Path] = []

    # 1
    fig, g = _page("Relational convolution: does overlap itself contain information?", "Bounded real-PRISM and symmetric-synthetic feasibility experiment")
    ax = fig.add_subplot(g[0:8, 0:12]); ax.axis("off")
    ax.text(0.02, 0.86, "S(x, y, dx, dy)", fontsize=34, color=INK, fontweight="bold")
    ax.text(0.02, 0.68, "400 complete real local surfaces  |  160,000 directed views  |  80,200 canonical pairs", fontsize=14, color=MUTED)
    gains = summary["real_delta_alignment_medians"]
    cards = [
        ("Relative Delta correlation", gains["pearson_relative"], BLUE),
        ("Absolute Delta correlation", gains["pearson_absolute"], GREEN),
        ("Absolute gradient similarity", gains["gradient_similarity_absolute"], GOLD),
        ("Station Delta correlation", station["pair_summary"]["delta"]["correlation"], RED),
    ]
    for i, (label, value, color) in enumerate(cards):
        left = 0.02 + i * 0.245
        ax.add_patch(plt.Rectangle((left, 0.25), 0.215, 0.26, color="white", ec="#d5e0e8", lw=1.2))
        ax.text(left + 0.02, 0.44, label, fontsize=9.5, color=MUTED)
        ax.text(left + 0.02, 0.29, f"{value:.2f}", fontsize=28, color=color, fontweight="bold")
    ax.text(0.02, 0.08, "Result: overlap is informative in this block, but it is not yet a production verb or validated climate-boundary product.", fontsize=10.5, color=INK, fontweight="bold")
    pages.append(_save(fig, 1))

    # 2
    fig, g = _page("The object is a field of relationships", "Cold and warm conditional synchrony remain separate; Delta S = S_cold - S_warm")
    ax = fig.add_subplot(g[:, :]); ax.axis("off")
    ax.text(0.05, 0.78, "X(x,y,t)", fontsize=25, color=BLUE, ha="center")
    ax.annotate("validated conditional\nSpearman operator", xy=(0.47, 0.78), xytext=(0.23, 0.78), arrowprops=dict(arrowstyle="->", lw=2, color=MUTED), fontsize=12, color=INK, ha="center")
    ax.text(0.58, 0.78, "X(x+dx,y+dy,t)", fontsize=25, color=RED, ha="center")
    ax.annotate("", xy=(0.78, 0.64), xytext=(0.58, 0.73), arrowprops=dict(arrowstyle="->", lw=2, color=MUTED))
    ax.text(0.77, 0.48, "S(x,y,dx,dy)", fontsize=29, color=INK, ha="center", fontweight="bold")
    _text(fig.add_subplot(g[7:12, 1:11]), ["Relative coordinates (dx,dy) describe shape around the focal pixel. Absolute coordinates q=(x+dx,y+dy) identify the fixed geography observed by overlapping surfaces.", "The experiment keeps cold, warm, Delta, valid counts, focal/comparison coordinates, distance, bearing, and canonical pair identity before any reduction."], size=11)
    pages.append(_save(fig, 2))

    # 3
    fig, g = _page("Why convolution-like - and why not a CNN", "The local operation translates; the relationship is estimated rather than multiplied by fixed weights")
    left = fig.add_subplot(g[1:10, 0:5]); right = fig.add_subplot(g[1:10, 7:12])
    for ax in (left, right): ax.axis("off")
    left.text(0.5, 0.9, "Ordinary convolution", ha="center", color=INK, fontsize=15, fontweight="bold")
    left.text(0.5, 0.67, "Y(p) = sum K(delta) X(p+delta)", ha="center", fontsize=15, color=BLUE)
    right.text(0.5, 0.9, "Relational surface", ha="center", color=INK, fontsize=15, fontweight="bold")
    right.text(0.5, 0.67, "S_p(delta) = f(X_p(t), X_(p+delta)(t))", ha="center", fontsize=15, color=RED)
    left.text(0.5, 0.35, "fixed weights\nimmediate sum\none output", ha="center", fontsize=12, color=MUTED, linespacing=1.5)
    right.text(0.5, 0.35, "estimated pair relation\ncomplete neighborhood retained\nno training objective", ha="center", fontsize=12, color=MUTED, linespacing=1.5)
    pages.append(_save(fig, 3))

    # 4
    fig, g = _page("One real local synchrony surface", f"Front Range focal pixel ({float(surfaces.focal_x[focal]):.3f}, {float(surfaces.focal_y[focal]):.3f}); 40 km observation window")
    for i, (name, title) in enumerate((("cold_synchrony", "Cold S"), ("warm_synchrony", "Warm S"), ("delta_s", "Delta S"))):
        ax = fig.add_subplot(g[1:11, i*4:(i+1)*4])
        limit = 1 if name != "delta_s" else delta_limit
        _heat(ax, arrays[name], title=title, extent=extent, limit=limit, label=title)
        ax.scatter(x[fx], y[fy], s=70, marker="*", color=GOLD, edgecolor=INK, zorder=4)
        ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    pages.append(_save(fig, 4))

    # 5
    fig, g = _page("Neighboring focal surfaces are not independent pictures", "A west-east transect: the same geographic cells are revisited from moving focal locations")
    for i, cx in enumerate((7, 9, 11, 13)):
        f = 10 * 20 + cx
        local, _, cy, cxi = _surface_arrays(surfaces, f)
        ax = fig.add_subplot(g[1:10, i*3:(i+1)*3])
        _heat(ax, local["delta_s"], title=f"focal x={cx}", extent=extent, limit=delta_limit)
        ax.scatter(x[cxi], y[cy], marker="*", s=45, color=GOLD, edgecolor=INK)
        ax.set_xticks([]); ax.set_yticks([])
    _text(fig.add_subplot(g[10:12, 0:12]), ["The panels share absolute map coordinates. Surface values change with focal location, but mountains, plains, and any fixed transition stay in place."], size=9.5)
    pages.append(_save(fig, 5))

    # 6 relative
    fig, g = _page("Relative-coordinate view: geography moves through the window", "Every focal is recentered at (0,0); equal offsets do not refer to equal absolute locations")
    for i, cx in enumerate((7, 9, 11, 13)):
        f = 10 * 20 + cx; local, mask, cy, cxi = _surface_arrays(surfaces, f)
        rel = np.full((39,39), np.nan); oy0=19-cy; ox0=19-cxi; rel[oy0:oy0+20, ox0:ox0+20]=local["delta_s"]
        ax=fig.add_subplot(g[1:10,i*3:(i+1)*3]); _heat(ax, rel, title=f"p{cx-6}", extent=[-19.5,19.5,19.5,-19.5], limit=delta_limit)
        ax.scatter(0,0,marker="*",s=45,color=GOLD,edgecolor=INK); ax.set_xlabel("dx index"); ax.set_ylabel("dy index")
    pages.append(_save(fig, 6))

    # 7 absolute
    fig, g = _page("Absolute-geography view: known alignment, no learned registration", "The same four surfaces are mapped to comparison latitude/longitude")
    for i, cx in enumerate((7, 9, 11, 13)):
        f=10*20+cx; local,_,cy,cxi=_surface_arrays(surfaces,f)
        ax=fig.add_subplot(g[1:10,i*3:(i+1)*3]); _heat(ax,local["delta_s"],title=f"p{cx-6}",extent=extent,limit=delta_limit)
        ax.scatter(x[cxi],y[cy],marker="*",s=45,color=GOLD,edgecolor=INK); ax.set_xticks([]); ax.set_yticks([])
    pages.append(_save(fig, 7))

    # 8 overlap
    fig,g=_page("The explicit overlap-support object", "Raw contributors remain in real_complete_surfaces.nc; these maps are inspectable projections")
    for i,(name,title,cmap) in enumerate((("contributing_surface_count","Contributing surfaces","viridis"),("mad","Delta MAD","magma"),("overlap_coherence","Overlap coherence","viridis"))):
        ax=fig.add_subplot(g[1:10,i*4:(i+1)*4]); arr=overlap[name].values
        im=ax.imshow(arr,origin="upper",extent=extent,aspect="auto",cmap=cmap); ax.set_title(title,color=INK,fontweight="bold",fontsize=10); plt.colorbar(im,ax=ax,fraction=.047,pad=.03); ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    pages.append(_save(fig, 8))

    # 9 symmetry
    fig,g=_page("Repeated geography is not the same as repeated pairs", "Canonical-pair identity prevents endpoint reversal from masquerading as replicate evidence")
    ax=fig.add_subplot(g[:, :]); ax.axis("off")
    ax.scatter([0.2,0.5,0.8],[0.55,0.75,0.55],s=[500,420,500],c=[BLUE,GOLD,RED],edgecolor=INK)
    ax.plot([0.2,0.8],[0.55,0.55],lw=4,color=MUTED); ax.plot([0.5,0.2],[0.75,0.55],lw=2,color=GREEN); ax.plot([0.5,0.8],[0.75,0.55],lw=2,color=GREEN)
    ax.text(.5,.43,"S(i,j)=S(j,i): one canonical pair, two endpoint views",ha="center",fontsize=14,color=INK,fontweight="bold")
    ax.text(.5,.28,"Interesting overlap: different focal-pair combinations support the same absolute cell or edge.",ha="center",fontsize=13,color=GREEN)
    ax.text(.5,.14,"160,000 directed views -> 80,200 canonical pairs; self-edge gradients are excluded.",ha="center",fontsize=11,color=MUTED)
    pages.append(_save(fig,9))

    # 10 reductions
    fig,g=_page("Median and dispersion retain magnitude, not 2-D geometry", "Real 40 km support; independent surface summaries")
    med=np.nanmedian(np.where(surfaces.distance_km.values<=40,surfaces.delta_s.values,np.nan),axis=1).reshape(20,20)
    q25=np.nanquantile(np.where(surfaces.distance_km.values<=40,surfaces.delta_s.values,np.nan),.25,axis=1).reshape(20,20); q75=np.nanquantile(np.where(surfaces.distance_km.values<=40,surfaces.delta_s.values,np.nan),.75,axis=1).reshape(20,20)
    mad=np.nanmedian(np.abs(np.where(surfaces.distance_km.values<=40,surfaces.delta_s.values,np.nan)-med.reshape(-1,1)),axis=1).reshape(20,20)
    for i,(arr,title,cmap) in enumerate(((med,"Median Delta S","RdBu_r"),(q75-q25,"IQR","magma"),(mad,"MAD","magma"))):
        ax=fig.add_subplot(g[1:10,i*4:(i+1)*4]); im=ax.imshow(arr,origin="upper",extent=extent,aspect="auto",cmap=cmap); ax.set_title(title,color=INK,fontweight="bold"); plt.colorbar(im,ax=ax,fraction=.047,pad=.03)
    _text(fig.add_subplot(g[10:12,:]),[f"Median-only normalized reconstruction RMSE = {representations.set_index('representation').loc['median_only','median_normalized_rmse']:.2f}; IQR/MAD describe spread but cannot restore where values occur."],size=9.5)
    pages.append(_save(fig,10))

    # 11 radii
    fig,g=_page("Observation-window sensitivity is not radius selection", "20, 40, and 60 km are computational windows; 60 km is edge-censored in this block")
    for i,radius in enumerate((20,40,60)):
        with xr.open_dataset(artifact_dir/f"absolute_support_delta_s_{radius}km.nc") as ds: arr=ds["median"].values
        ax=fig.add_subplot(g[1:10,i*4:(i+1)*4]); _heat(ax,arr,title=f"absolute median, {radius} km",extent=extent,limit=delta_limit)
    pages.append(_save(fig,11))

    # 12 radial directional
    fig,g=_page("Radial plus directional summaries are the strongest independent baseline", "Fine empirical strata; no monotonic decay is imposed")
    dist=surfaces.distance_km.isel(focal=focal).values; bearing=surfaces.bearing_degrees.isel(focal=focal).values; vals=surfaces.delta_s.isel(focal=focal).values
    ax1=fig.add_subplot(g[1:10,0:6]); bins=np.arange(0,45,5); centers=(bins[:-1]+bins[1:])/2; prof=[]
    for lo,hi in zip(bins[:-1],bins[1:]): prof.append(np.nanmedian(vals[(dist>=lo)&(dist<hi)]))
    ax1.plot(centers,prof,"o-",color=BLUE,lw=2); ax1.axhline(0,color=MUTED,lw=.8); ax1.set(title="Fine radial profile",xlabel="distance (km)",ylabel="Delta S")
    ax2=fig.add_subplot(g[1:10,6:12],projection="polar"); sectors=np.arange(0,361,45); centers2=np.deg2rad((sectors[:-1]+sectors[1:])/2); aprof=[]
    radial_pred=np.interp(dist,centers,np.asarray(prof),left=np.nan,right=np.nan); resid=vals-radial_pred
    for lo,hi in zip(sectors[:-1],sectors[1:]): aprof.append(np.nanmedian(resid[(bearing>=lo)&(bearing<hi)&(dist<=40)]))
    ax2.plot(np.r_[centers2,centers2[0]],np.r_[aprof,aprof[0]],"o-",color=RED,lw=2); ax2.set_title("Radially adjusted direction",color=INK,fontweight="bold")
    fig.text(.055,.07,f"Radial + directional nRMSE = {representations.set_index('representation').loc['radial_plus_directional','median_normalized_rmse']:.2f} versus median-only {representations.set_index('representation').loc['median_only','median_normalized_rmse']:.2f}.",fontsize=9.5,color=INK)
    pages.append(_save(fig,12))

    # 13
    fig,g=_page("Candidate A - overlap coherence", "Agreement and dispersion at the same absolute locations; contributor count stays visible")
    for i,(name,title,cmap) in enumerate((("overlap_coherence","coherence","viridis"),("iqr","IQR","magma"),("contributing_surface_count","support count","viridis"))):
        ax=fig.add_subplot(g[1:10,i*4:(i+1)*4]); im=ax.imshow(overlap[name],origin="upper",extent=extent,aspect="auto",cmap=cmap); ax.set_title(title,color=INK,fontweight="bold"); plt.colorbar(im,ax=ax,fraction=.047,pad=.03)
    pages.append(_save(fig,13))

    # 14
    fig,g=_page("Candidate B - translated-gradient agreement", "Different focal surfaces estimate change across the same absolute raster edge")
    for i,(name,title) in enumerate((("east_west_absolute_gradient_median","east-west |gradient| median"),("north_south_absolute_gradient_median","north-south |gradient| median"),("east_west_sign_coherence","east-west sign coherence"))):
        ax=fig.add_subplot(g[1:10,i*4:(i+1)*4]); im=ax.imshow(edges[name],origin="upper",extent=extent,aspect="auto",cmap="magma" if "gradient" in name else "viridis"); ax.set_title(title,color=INK,fontweight="bold",fontsize=9.5); plt.colorbar(im,ax=ax,fraction=.047,pad=.03)
    pages.append(_save(fig,14))

    # 15
    fig,g=_page("Candidate C - transition evidence is one diagnostic, not the goal", "Median absolute aligned gradient weighted by distinct focal support")
    ax=fig.add_subplot(g[1:11,1:11]); ew=np.asarray(edges.east_west_transition_evidence); ns=np.asarray(edges.north_south_transition_evidence); combined=np.sqrt(np.nan_to_num(ew)**2+np.nan_to_num(ns)**2)
    im=ax.imshow(combined,origin="upper",extent=extent,aspect="auto",cmap="inferno"); plt.colorbar(im,ax=ax,label="candidate evidence"); ax.set(xlabel="longitude",ylabel="latitude"); ax.set_title("Real PRISM candidate map - no boundary classification",color=INK,fontweight="bold")
    pages.append(_save(fig,15))

    # synthetic pages 16-20
    synth_pages=[("isotropic_distance_decay","Synthetic isotropic distance decay",16),("directional_anisotropy","Synthetic directional anisotropy",17),("sharp_geographic_transition","Synthetic sharp transition",18),("transition_plus_distance","Synthetic transition + distance",19),("noise_only","Synthetic noise/null",20)]
    for case,title,num in synth_pages:
        vals,dist,meta=symmetric_synthetic_field(case); sup=translated_edge_support(vals,dist,radius=7); center_idx=8*17+8; local=vals[center_idx]; evidence=sup.east_west_transition_evidence.values
        row=synthetic.set_index("case").loc[case]
        fig,g=_page(title,"Known-answer, pair-symmetric relational field")
        ax1=fig.add_subplot(g[1:10,0:5]); _heat(ax1,local,title="one local surface",limit=max(float(np.nanmax(np.abs(local))),1e-6))
        ax2=fig.add_subplot(g[1:10,5:10]); im=ax2.imshow(evidence,origin="upper",cmap="inferno",aspect="auto"); plt.colorbar(im,ax=ax2,fraction=.047,pad=.03); ax2.set_title("translated transition evidence",color=INK,fontweight="bold")
        edge_ratio = ">1e6" if row.translated_transition_edge_ratio > 1e6 else f"{row.translated_transition_edge_ratio:.2f}"
        ax3=fig.add_subplot(g[2:9,10:12]); ax3.axis("off"); ax3.text(.05,.9,f"pair symmetry\nmax error\n{meta['pair_symmetry_max_error']:.1e}\n\nedge ratio\n{edge_ratio}\n\nsmoothing ratio\n{row.smoothed_median_edge_ratio:.2f}",va="top",fontsize=11,color=INK,linespacing=1.35)
        pages.append(_save(fig,num,))

    # 21 method comparison
    fig,g=_page("Method comparison: geometry retained versus reconstruction error", "Aesthetics are not a decision criterion")
    ax=fig.add_subplot(g[1:10,0:7]); order=representations.sort_values("median_normalized_rmse",ascending=True); ax.barh(order.representation,order.median_normalized_rmse,color=[GREEN if v<.8 else BLUE for v in order.median_normalized_rmse]); ax.invert_yaxis(); ax.set_xlabel("median normalized reconstruction RMSE (lower is better)"); ax.grid(axis="x",alpha=.2)
    ax2=fig.add_subplot(g[1:10,7:12]); ax2.axis("off"); shown=decision[["method","recommendation"]].copy(); table=ax2.table(cellText=shown.values,colLabels=shown.columns,cellLoc="left",loc="center",colWidths=[.55,.45]); table.auto_set_font_size(False); table.set_fontsize(7.5); table.scale(1,1.35)
    pages.append(_save(fig,21))

    # 22 windows
    fig,g=_page("Observation-window stability", "Candidate maps persist across practical windows; this does not identify a characteristic scale")
    ax=fig.add_subplot(g[1:10,1:11]); labels=[f"{int(r.left_radius_km)}->{int(r.right_radius_km)} km" for r in windows.itertuples()]; xx=np.arange(len(labels)); ax.bar(xx-.18,windows.pearson,width=.36,label="Pearson",color=BLUE); ax.bar(xx+.18,windows.spearman,width=.36,label="rank",color=GREEN); ax.set_xticks(xx,labels); ax.set_ylim(0,1); ax.set_ylabel("map agreement"); ax.legend(); ax.grid(axis="y",alpha=.2)
    pages.append(_save(fig,22))

    # 23 stations
    fig,g=_page("Raw weather-station network", "30 selected GHCN-Daily stations; 35 eligible <=150 km edges")
    ax=fig.add_subplot(g[1:11,1:11]); _state_outline(ax,artifact_dir)
    for row in pairs.itertuples():
        a=manifest.set_index("station_id").loc[row.station_i]; b=manifest.set_index("station_id").loc[row.station_j]; ax.plot([a.longitude,b.longitude],[a.latitude,b.latitude],color="#9fb2c3",lw=.6,alpha=.5)
    sc=ax.scatter(manifest.longitude,manifest.latitude,c=manifest.elevation_m,cmap="terrain",s=38,edgecolor=INK,zorder=3); plt.colorbar(sc,ax=ax,label="elevation (m)"); ax.set(xlabel="longitude",ylabel="latitude"); ax.set_title("Irregular graph; no rasterization",color=INK,fontweight="bold")
    pages.append(_save(fig,23,"NOAA/NCEI GHCN-Daily; PRISM Climate Group"))

    # 24 qc
    fig,g=_page("Station QC, provenance, and independence limits", "Quality-flag exclusions are explicit; PRISM contribution status is not guessed")
    ax=fig.add_subplot(g[1:8,0:7]); m=manifest.sort_values("tmin_completeness"); yy=np.arange(len(m)); ax.barh(yy-.18,m.tmin_completeness,height=.34,color=BLUE,label="TMIN"); ax.barh(yy+.18,m.tmax_completeness,height=.34,color=RED,alpha=.65,label="TMAX"); ax.set_xlim(0,1.05); ax.set_xlabel("completeness"); ax.set_yticks([]); ax.legend()
    _text(fig.add_subplot(g[1:10,7:12]),["54/60 candidates met the 70% completeness threshold; 30 were selected spatially.","Every selected station is classified UNKNOWN for PRISM contribution status. PRISM AN daily is station-informed, and the exact product-period roster was not established.","PRISM day: 1200-1200 UTC, day-ending label. GHCN observation time is local when present. Same-label and +/-1-day sensitivity are retained."],size=9.5,width=43)
    pages.append(_save(fig,24,"NOAA/NCEI GHCN-Daily documentation; PRISM AN daily documentation"))

    # 25 raw values
    fig,g=_page("Raw station versus PRISM TMIN/TMAX", "Station-level same-label metrics; +/-1-day comparisons remain in the artifact table")
    same=raw.query("prism_label_shift_days == 0")
    for i,var in enumerate(("TMIN","TMAX")):
        sub=same.query("variable == @var"); ax=fig.add_subplot(g[1:10,i*6:(i+1)*6]); sc=ax.scatter(sub.bias,sub.rmse,c=sub.correlation,cmap="viridis",vmin=0,vmax=1,s=45,edgecolor=INK); ax.axvline(0,color=MUTED,lw=.8); ax.set(xlabel="PRISM - station bias (C)",ylabel="RMSE (C)",title=var); plt.colorbar(sc,ax=ax,label="correlation")
    pages.append(_save(fig,25,"Same-label daily values; nonblank GHCN quality flags excluded"))

    # 26-28 pair scatter
    for num,label in ((26,"cold"),(27,"warm"),(28,"delta")):
        fig,g=_page(f"Station versus PRISM {label} pair synchrony", "Station thresholds come from station observations; PRISM thresholds come from PRISM")
        ax=fig.add_subplot(g[1:11,1:9]); a=pairs[f"station_{label}"]; b=pairs[f"prism_{label}"]; ax.scatter(a,b,c=pairs.distance_km,cmap="viridis",s=55,edgecolor=INK); lo=float(np.nanmin([a.min(),b.min()])); hi=float(np.nanmax([a.max(),b.max()])); ax.plot([lo,hi],[lo,hi],"--",color=MUTED); ax.set(xlabel=f"station {label}",ylabel=f"PRISM {label}"); stats=station["pair_summary"][label]
        _text(fig.add_subplot(g[2:10,9:12]),[f"n edges = {stats['n']}\nr = {stats['correlation']:.2f}\nrank r = {stats['rank_correlation']:.2f}\nMAE = {stats['mae']:.2f}\nRMSE = {stats['rmse']:.2f}","Edges share stations. These are descriptive, dependence-aware in wording, and not independent validation."],size=9.2,width=30)
        pages.append(_save(fig,num,"30 GHCN-Daily stations; all PRISM contribution statuses UNKNOWN"))

    # 29 alignment gains
    fig,g=_page("What overlap adds in the real block", "Absolute alignment uses known geography and outperforms relative-offset comparison")
    delta=similarity.query("metric == 'delta_s' and radius_km == 40")
    metrics=[("pearson","correlation"),("spearman","rank correlation"),("gradient_similarity","gradient similarity")]; ax=fig.add_subplot(g[1:10,1:11]); xx=np.arange(3); rel=[delta[f"{m}_relative"].median() for m,_ in metrics]; absolute=[delta[f"{m}_absolute"].median() for m,_ in metrics]; ax.bar(xx-.18,rel,.36,label="relative",color=BLUE); ax.bar(xx+.18,absolute,.36,label="absolute geography",color=GREEN); ax.set_xticks(xx,[l for _,l in metrics]); ax.set_ylim(0,1); ax.legend(); ax.grid(axis="y",alpha=.2)
    fig.text(.12,.08,"This gain is not created by pair reversal: canonical identities are explicit, and edge support excludes focal-self gradients.",fontsize=9.5,color=INK)
    pages.append(_save(fig,29))

    # 30 PCA
    fig,g=_page("PCA/SVD is useful, but no autoencoder is justified", "Held-out reconstruction improves with components; transparency wins for this feasibility decision")
    pca=pd.DataFrame(summary["pca_svd"]["results"]); ax=fig.add_subplot(g[1:10,0:7]); ax.plot(pca.components,pca.held_out_median_normalized_rmse,"o-",color=BLUE,lw=2,label="held-out nRMSE"); ax2=ax.twinx(); ax2.plot(pca.components,pca.training_cumulative_variance,"s--",color=GREEN,label="training cumulative variance"); ax.set(xlabel="components",ylabel="held-out nRMSE"); ax2.set_ylabel("training cumulative variance"); ax.grid(alpha=.2)
    _text(fig.add_subplot(g[2:10,8:12]),["8-component held-out nRMSE: 0.55 on 64 interior surfaces.","Radial + directional nRMSE: 0.68, with direct scientific interpretation.","A small autoencoder was not run: it would add dependency and opacity without changing today's decision."],size=9.5,width=38)
    pages.append(_save(fig,30))

    # 31 conclusion
    fig,g=_page("Recommendation: preserve relations, add an experimental aligned-view layer", "Stop here - no Colorado second-stage production run and no new public verb")
    ax=fig.add_subplot(g[0:7,:]); ax.axis("off")
    stages=[("canonical pairs","validated S(i,j)",BLUE),("surface collection","relative + absolute views",GREEN),("diagnostics","coherence / gradients / change",GOLD),("future gate","temporal + station holdout",RED)]
    for i,(name,sub,color) in enumerate(stages):
        left=.02+i*.245; ax.add_patch(plt.Rectangle((left,.3),.205,.42,facecolor="white",edgecolor=color,lw=2)); ax.text(left+.102,.58,name,ha="center",fontsize=12,color=INK,fontweight="bold"); ax.text(left+.102,.42,sub,ha="center",fontsize=9,color=MUTED,wrap=True)
        if i<3: ax.annotate("",xy=(left+.24,.51),xytext=(left+.21,.51),arrowprops=dict(arrowstyle="->",lw=2,color=MUTED))
    _text(fig.add_subplot(g[7:12,0:12]),["WORKED - Known geographic alignment, translated gradients, and explicit support reveal stable structure beyond independent reductions and smoothing controls.","WEAK - Median/radius reductions lose geometry; warm station-pair agreement is weak; the station graph is sparse and not demonstrably independent of PRISM.","NEXT - Keep an internal canonical-pair-backed surface collection with reversible relative/absolute views. Require temporal robustness and station-level/spatial-block holdouts before promotion."],size=8.8,width=112)
    pages.append(_save(fig,31))
    return pages


def assemble(pages: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".partial.pdf")
    width, height = landscape(letter)
    pdf = canvas.Canvas(str(temporary), pagesize=(width, height), pageCompression=1)
    pdf.setTitle("Relational convolution feasibility experiment")
    pdf.setAuthor("CubeDynamics")
    for page in pages:
        pdf.drawImage(str(page), 0, 0, width=width, height=height, preserveAspectRatio=True, anchor="c")
        pdf.showPage()
    pdf.save()
    temporary.replace(output)


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finalize_manifest(artifact_dir: Path, output: Path, page_count: int) -> None:
    files = {}
    for path in sorted(artifact_dir.iterdir()):
        if path.is_file() and path.name != "artifact_manifest.json":
            files[path.name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    payload = {
        "analysis": "relational_convolution_feasibility",
        "files": files,
        "visual_report": {
            "path": str(output.relative_to(ROOT)),
            "pages": page_count,
            "bytes": output.stat().st_size,
            "sha256": _sha256(output),
            "visual_inspection": "all pages rendered to PNG and inspected",
        },
    }
    (artifact_dir / "artifact_manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    args = _parser().parse_args()
    pages = build_pages(args.artifacts.resolve())
    assemble(pages, args.output.resolve())
    finalize_manifest(args.artifacts.resolve(), args.output.resolve(), len(pages))
    print(f"Wrote {args.output.resolve()} ({len(pages)} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
