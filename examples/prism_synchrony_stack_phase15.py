"""Analyze the exact Phase 1 observed-PRISM stack for scientific meaning.

This Phase 1.5 workflow does not recalculate climate correlations and does not
run a national or 100 by 100 experiment. It reads the validated Phase 1 stack,
writes machine-readable diagnostics, creates standardized figures, and builds
the Phase 1.5 decision report.

Run from the repository root::

    MPLCONFIGDIR=/tmp/cubedynamics-mpl XDG_CACHE_HOME=/tmp/cubedynamics-cache \
      .venv/bin/python examples/prism_synchrony_stack_phase15.py
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.stats import gaussian_kde, rankdata, spearmanr

# ReportLab is supplied by the Codex workspace runtime. Append its location so
# compiled scientific packages continue to come from the repository venv.
_WORKSPACE_SITE_PACKAGES = Path(
    "/Users/tuff/.cache/codex-runtimes/codex-primary-runtime/dependencies/"
    "python/lib/python3.12/site-packages"
)
if _WORKSPACE_SITE_PACKAGES.exists():
    sys.path.append(str(_WORKSPACE_SITE_PACKAGES))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
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


EXPECTED_FINGERPRINT = (
    "sha256:4b4a3c30fbd5ccb2a4f8b5cefc2ca2b127e7bf31d646b27091b354b447df9acb"
)
DEFAULT_STACK = Path("artifacts/synchrony-stack-phase1/prism_20x20_synchrony_stack.nc")
DEFAULT_OUTPUT = Path("artifacts/synchrony-stack-phase15")
DEFAULT_REPORT = Path("output/pdf/cubedynamics_synchrony_stack_phase15_report.pdf")

COLD = "#1565c0"
WARM = "#c62828"
DELTA = "#6a1b9a"
INK = "#15324b"
GOLD = "#f9a825"


def _save(figure: plt.Figure, path: Path) -> None:
    figure.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def _map(axis, data, title, *, cmap="RdBu", vmin=None, vmax=None, star=None):
    image = axis.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, origin="upper")
    if star is not None:
        axis.scatter(star[1], star[0], marker="*", s=90, c="#ffd54f", edgecolor="black")
    axis.set_title(title, fontsize=10)
    axis.set_xlabel("x index")
    axis.set_ylabel("y index")
    return image


def _incident_map(panel: xr.Dataset, variable: str) -> np.ndarray:
    result = np.zeros((20, 20), dtype=float)
    count = np.zeros((20, 20), dtype=float)
    for row in range(panel.sizes["comparison"]):
        value = float(panel[variable].values[row])
        for side in ("a", "b"):
            yi = int(panel[f"center_{side}_y_index"].values[row])
            xi = int(panel[f"center_{side}_x_index"].values[row])
            if np.isfinite(value):
                result[yi, xi] += value
                count[yi, xi] += 1
    return np.divide(result, count, out=np.full_like(result, np.nan), where=count > 0)


def _write_panel_csv(panel: xr.Dataset, path: Path) -> None:
    fields = [
        "comparison", "center_A", "center_B", "center_A_y", "center_A_x",
        "center_B_y", "center_B_x", "distance_between_centers_km", "direction_code",
        "cold_spearman", "warm_spearman", "delta_spearman",
        "cold_rmse", "warm_rmse", "delta_rmse", "delta_mae",
        "delta_normalized_rmse", "delta_sign_disagreement", "delta_wasserstein",
        "delta_gradient_vector_rmse", "delta_gradient_magnitude_rmse",
        "delta_left_robust_range", "delta_right_robust_range",
        "delta_left_near_tie_fraction", "delta_right_near_tie_fraction",
    ]
    mapping = {
        "center_A": "center_a", "center_B": "center_b",
        "center_A_y": "center_a_y_index", "center_A_x": "center_a_x_index",
        "center_B_y": "center_b_y_index", "center_B_x": "center_b_x_index",
        "distance_between_centers_km": "center_distance_km",
        "direction_code": "center_direction_code",
    }
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in range(panel.sizes["comparison"]):
            record = {"comparison": row}
            for field in fields[1:]:
                variable = mapping.get(field, field)
                value = panel[variable].values[row]
                record[field] = value.item() if hasattr(value, "item") else value
            writer.writerow(record)


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _metric_disagreements(panel: xr.Dataset) -> list[dict[str, object]]:
    s = np.asarray(panel.delta_spearman.values)
    r = np.asarray(panel.delta_rmse.values)
    sign = np.asarray(panel.delta_sign_disagreement.values)
    water = np.asarray(panel.delta_wasserstein.values)
    grad = np.asarray(panel.delta_gradient_vector_rmse.values)

    def pick(score, mask):
        candidates = np.flatnonzero(mask & np.isfinite(score))
        return int(candidates[np.nanargmax(score[candidates])])

    cases = [
        ("lowest Spearman among below-median RMSE", pick(-s, r <= np.nanmedian(r))),
        ("highest RMSE among top-quartile Spearman", pick(r, s >= np.nanquantile(s, 0.75))),
        ("highest RMSE among bottom-quartile sign change", pick(r, sign <= np.nanquantile(sign, 0.25))),
        ("highest sign change among below-median RMSE", pick(sign, r <= np.nanmedian(r))),
        ("highest Wasserstein among below-median gradient change", pick(water, grad <= np.nanmedian(grad))),
    ]
    rows = []
    for label, index in cases:
        rows.append(
            {
                "case": label,
                "comparison": index,
                "center_A": int(panel.center_a.values[index]),
                "center_B": int(panel.center_b.values[index]),
                "delta_spearman": float(s[index]),
                "delta_rmse": float(r[index]),
                "delta_sign_disagreement": float(sign[index]),
                "delta_wasserstein": float(water[index]),
                "delta_gradient_vector_rmse": float(grad[index]),
            }
        )
    return rows


def _typology(stack: xr.Dataset, reduced: xr.Dataset, structure: xr.Dataset) -> list[dict[str, object]]:
    roles = [
        ("Type 1 - low variance / spatially uniform", (17, 5), True),
        ("Type 2 - distance structured", tuple(np.unravel_index(np.nanargmax(structure.distance_bin_eta_squared), (20, 20))), True),
        ("Type 3 - directionally structured", tuple(np.unravel_index(np.nanargmax(structure.direction_eta_squared), (20, 20))), True),
        ("Type 4 - broad continuous", (1, 5), True),
        ("Type 5 - candidate spatial partition", (9, 13), True),
        ("Type 6 - edge / incomplete support", (0, 0), True),
    ]
    records = []
    for role, (yi, xi), observed in roles:
        records.append(
            {
                "role": role,
                "observed": observed,
                "y_index": int(yi),
                "x_index": int(xi),
                "latitude": float(stack.y.values[yi]),
                "longitude": float(stack.x.values[xi]),
                "delta_median": float(reduced["median"].values[yi, xi]),
                "delta_iqr": float(reduced.iqr.values[yi, xi]),
                "distance_eta_squared": float(structure.distance_bin_eta_squared.values[yi, xi]),
                "direction_eta_squared": float(structure.direction_eta_squared.values[yi, xi]),
                "kde_modes_scott": int(structure.kde_mode_count.values[yi, xi]),
                "kde_multimodal_bandwidth_consensus": bool(structure.kde_multimodal_bandwidth_consensus.values[yi, xi]),
                "two_group_neighbor_agreement_excess": float(structure.two_group_neighbor_agreement_excess.values[yi, xi]),
                "two_group_component_coverage": float(structure.two_group_component_coverage.values[yi, xi]),
            }
        )
    return records


def _figure_hierarchy(path: Path) -> None:
    figure, axis = plt.subplots(figsize=(12, 4.5))
    axis.axis("off")
    labels = [
        ("PAIR", "S(c,p)\none undirected edge"),
        ("LANDSCAPE", "M_c = S(c,.)\none center, all focal pixels"),
        ("STACK", "Stack(p) = {S(c,p)}\none focal pixel, all centers"),
        ("REDUCTION", "median / IQR / radius / direction\nsummary, not the original object"),
    ]
    x = np.linspace(0.12, 0.88, len(labels))
    for position, (title, body) in zip(x, labels):
        axis.text(position, 0.55, title + "\n\n" + body, ha="center", va="center", fontsize=11,
                  bbox=dict(boxstyle="round,pad=.65", fc="#eef5fb", ec="#2c6e9b", lw=1.5))
    for left, right in zip(x[:-1], x[1:]):
        axis.annotate("", (right - .09, .55), (left + .09, .55), arrowprops=dict(arrowstyle="->", lw=2, color=INK))
    axis.text(.5, .12, "Panel comparison Q(A,B) is second-order: it compares two complete edge patterns.", ha="center", fontsize=12, color=DELTA)
    axis.set_title("Phase 1 hierarchy: related views of the same pairwise field, not interchangeable quantities", fontsize=15, weight="bold")
    _save(figure, path)


def _figure_similar_medians(stack: xr.Dataset, radius: xr.Dataset, path: Path) -> dict[str, object]:
    a, b = (1, 5), (8, 14)
    figure, axes = plt.subplots(2, 3, figsize=(12, 7), constrained_layout=True)
    for row, (yi, xi) in enumerate((a, b)):
        values = np.asarray(stack.delta_s[:, yi, xi].values)
        image = _map(axes[row, 0], values.reshape(20, 20), f"center geography at focal ({yi},{xi})", cmap="RdBu", vmin=-.45, vmax=.45, star=(yi, xi))
        figure.colorbar(image, ax=axes[row, 0], shrink=.8, label="Delta S")
        axes[row, 1].hist(values, bins=24, color=DELTA, alpha=.75)
        axes[row, 1].axvline(np.median(values), color="black", lw=2)
        axes[row, 1].set_title(f"median={np.median(values):.3f}; IQR={np.subtract(*np.quantile(values,[.75,.25])):.3f}")
        axes[row, 1].set_xlabel("Delta S")
        r = radius.radius_km.values
        axes[row, 2].plot(r, radius.delta_median[:, yi, xi], color=DELTA, label="median")
        axes[row, 2].fill_between(r, radius.delta_q25[:, yi, xi], radius.delta_q75[:, yi, xi], color=DELTA, alpha=.2, label="IQR")
        axes[row, 2].set_title("nested support")
        axes[row, 2].set_xlabel("radius (km)")
        axes[row, 2].set_ylabel("Delta S")
        axes[row, 2].legend(fontsize=8)
    figure.suptitle("Similar medians can hide radically different stack structure", fontsize=15, weight="bold")
    _save(figure, path)
    return {"a": a, "b": b, "median_difference": float(abs(np.median(stack.delta_s[:,a[0],a[1]])-np.median(stack.delta_s[:,b[0],b[1]])))}


def _figure_panel_break(stack: xr.Dataset, panel: xr.Dataset, path: Path) -> dict[str, object]:
    index = int(np.nanargmin(panel.delta_spearman.values))
    ca, cb = int(panel.center_a.values[index]), int(panel.center_b.values[index])
    a = np.asarray(stack.delta_s.isel(center=ca).values)
    b = np.asarray(stack.delta_s.isel(center=cb).values)
    figure, axes = plt.subplots(2, 4, figsize=(14, 7.2), constrained_layout=True)
    for axis, data, title in ((axes[0,0],a,"Delta A"),(axes[0,1],b,"Delta B"),(axes[0,2],a-b,"A - B")):
        image = _map(axis, data, title, cmap="RdBu", vmin=-.3, vmax=.3)
        figure.colorbar(image, ax=axis, shrink=.72)
    axes[0,3].scatter(a.ravel(), b.ravel(), s=12, alpha=.55, c=np.hypot(*np.indices(a.shape)), cmap="viridis")
    axes[0,3].set(xlabel="A Delta S", ylabel="B Delta S", title="value scatter")
    axes[1,0].scatter(rankdata(a.ravel()), rankdata(b.ravel()), s=12, alpha=.55, color=DELTA)
    axes[1,0].set(xlabel="rank(A)", ylabel="rank(B)", title="rank scatter")
    axes[1,1].hist(a.ravel(), bins=25, alpha=.55, label="A", color=COLD)
    axes[1,1].hist(b.ravel(), bins=25, alpha=.55, label="B", color=WARM)
    axes[1,1].legend(); axes[1,1].set(title="value distributions", xlabel="Delta S")
    axes[1,2].hist(np.diff(np.sort(a.ravel())), bins=25, alpha=.65, label="A gaps", color=COLD)
    axes[1,2].hist(np.diff(np.sort(b.ravel())), bins=25, alpha=.65, label="B gaps", color=WARM)
    axes[1,2].set(title="near-tie rank gaps", xlabel="adjacent sorted gap"); axes[1,2].legend(fontsize=8)
    text = (
        f"Spearman {panel.delta_spearman.values[index]:.3f}\n"
        f"RMSE {panel.delta_rmse.values[index]:.3f}\n"
        f"normalized RMSE {panel.delta_normalized_rmse.values[index]:.3f}\n"
        f"sign disagreement {panel.delta_sign_disagreement.values[index]:.3f}\n"
        f"near ties A/B {panel.delta_left_near_tie_fraction.values[index]:.3f}/{panel.delta_right_near_tie_fraction.values[index]:.3f}\n"
        f"cold/warm Spearman {panel.cold_spearman.values[index]:.3f}/{panel.warm_spearman.values[index]:.3f}"
    )
    axes[1,3].axis("off"); axes[1,3].text(.03,.95,text,va="top",fontsize=12,bbox=dict(boxstyle="round",fc="#f7f4ed",ec=GOLD))
    figure.suptitle(f"Strongest rank break: adjacent centers {ca} and {cb}", fontsize=15, weight="bold")
    _save(figure, path)
    return {"comparison": index, "center_a": ca, "center_b": cb}


def _figure_metric_comparison(panel: xr.Dataset, disagreements: list[dict[str, object]], path: Path) -> dict[str, float]:
    names = ["delta_spearman", "delta_rmse", "delta_normalized_rmse", "delta_sign_disagreement", "delta_wasserstein", "delta_gradient_vector_rmse"]
    short = ["Spearman", "RMSE", "nRMSE", "sign", "Wasserstein", "gradient"]
    matrix = np.column_stack([panel[name].values for name in names])
    corr = np.corrcoef(matrix, rowvar=False)
    figure, axes = plt.subplots(2, 3, figsize=(13, 7.5), constrained_layout=True)
    image = axes[0,0].imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    axes[0,0].set_xticks(range(6), short, rotation=45, ha="right"); axes[0,0].set_yticks(range(6), short)
    axes[0,0].set_title("Pearson correlation among metrics"); figure.colorbar(image, ax=axes[0,0], shrink=.75)
    pairs = [("delta_spearman","delta_rmse"),("delta_spearman","delta_normalized_rmse"),("delta_rmse","delta_sign_disagreement"),("delta_rmse","delta_wasserstein"),("delta_rmse","delta_gradient_vector_rmse")]
    for axis, (xname,yname) in zip(axes.flat[1:], pairs):
        axis.scatter(panel[xname], panel[yname], s=12, alpha=.5, color="#2c6e9b")
        for row in disagreements:
            index=int(row["comparison"]); axis.scatter(panel[xname][index],panel[yname][index],s=30,facecolor="none",edgecolor=GOLD)
        axis.set_xlabel(xname.replace("delta_","")); axis.set_ylabel(yname.replace("delta_",""))
    figure.suptitle("Candidate panel-change metrics measure related but nonidentical behavior", fontsize=15, weight="bold")
    _save(figure, path)
    return {f"{short[i]}__{short[j]}": float(corr[i,j]) for i in range(6) for j in range(i+1,6)}


def _figure_panel_maps(panel: xr.Dataset, path: Path) -> dict[str, np.ndarray]:
    variables = [
        ("delta_spearman","mean incident Spearman","viridis",0,1),
        ("delta_rmse","mean incident RMSE","magma",0,None),
        ("delta_normalized_rmse","mean incident normalized RMSE","magma",0,None),
        ("delta_sign_disagreement","mean incident sign disagreement","magma",0,None),
        ("delta_wasserstein","mean incident Wasserstein","magma",0,None),
        ("delta_gradient_vector_rmse","mean incident gradient RMSE","magma",0,None),
    ]
    maps={}; figure,axes=plt.subplots(2,3,figsize=(12,7.5),constrained_layout=True)
    for axis,(name,title,cmap,vmin,vmax) in zip(axes.flat,variables):
        maps[name]=_incident_map(panel,name); image=_map(axis,maps[name],title,cmap=cmap,vmin=vmin,vmax=vmax); figure.colorbar(image,ax=axis,shrink=.75)
    figure.suptitle("Panel change is attached to center-landscape transitions",fontsize=15,weight="bold")
    _save(figure,path); return maps


def _figure_radius(radius: xr.Dataset, focal: tuple[int,int], label: str, path: Path) -> None:
    yi,xi=focal; r=radius.radius_km.values
    figure,axes=plt.subplots(2,3,figsize=(12,7),constrained_layout=True)
    for axis,prefix,color in zip(axes[0],("cold","warm","delta"),(COLD,WARM,DELTA)):
        axis.plot(r,radius[f"{prefix}_median"][:,yi,xi],color=color,lw=2,label="median")
        axis.fill_between(r,radius[f"{prefix}_q25"][:,yi,xi],radius[f"{prefix}_q75"][:,yi,xi],color=color,alpha=.2,label="IQR")
        axis.plot(r,radius[f"{prefix}_q05"][:,yi,xi],color=color,ls="--",alpha=.6); axis.plot(r,radius[f"{prefix}_q95"][:,yi,xi],color=color,ls="--",alpha=.6)
        axis.set(title=f"{prefix}: median, IQR, 5-95%",xlabel="radius (km)"); axis.legend(fontsize=8)
    axes[1,0].plot(r,radius.delta_iqr[:,yi,xi],label="IQR",color=DELTA); axes[1,0].plot(r,radius.delta_standard_deviation[:,yi,xi],label="SD",color=INK); axes[1,0].plot(r,radius.delta_mad[:,yi,xi],label="MAD",color=GOLD); axes[1,0].legend(); axes[1,0].set(title="Delta spread",xlabel="radius (km)")
    axes[1,1].plot(r,radius.eligible_center_count[:,yi,xi],color=INK); axes[1,1].set(title="eligible centers",xlabel="radius (km)",ylabel="count")
    axes[1,2].plot(r[1:],np.abs(np.diff(radius.delta_median[:,yi,xi])),label="|median step|",color=DELTA); axes[1,2].plot(r[1:],np.abs(np.diff(radius.delta_iqr[:,yi,xi])),label="|IQR step|",color=GOLD); axes[1,2].legend(); axes[1,2].set(title="descriptive stabilization",xlabel="radius (km)")
    figure.suptitle(f"{label} focal ({yi},{xi}): nested support growth",fontsize=15,weight="bold"); _save(figure,path)


def _figure_stack_structure(stack: xr.Dataset, structure: xr.Dataset, focal: tuple[int,int], title: str, path: Path, *, partition=False) -> None:
    yi,xi=focal; delta=np.asarray(stack.delta_s[:,yi,xi]); cold=np.asarray(stack.cold_synchrony[:,yi,xi]); warm=np.asarray(stack.warm_synchrony[:,yi,xi]); dist=np.asarray(stack.distance_km[:,yi,xi]); bearing=np.asarray(stack.bearing_degrees[:,yi,xi]); labels=np.asarray(structure.two_group_label[:,yi,xi]);
    figure,axes=plt.subplots(2,3,figsize=(12,7.5),constrained_layout=True)
    group_cmap="coolwarm" if partition else "RdBu"
    map_values=labels.reshape(20,20) if partition else delta.reshape(20,20)
    image=_map(axes[0,0],map_values,"candidate groups on center geography" if partition else "Delta S on center geography",cmap=group_cmap,star=focal); figure.colorbar(image,ax=axes[0,0],shrink=.75)
    axes[0,1].hist(delta,bins=28,density=True,color=DELTA,alpha=.45); grid=np.linspace(delta.min(),delta.max(),250); axes[0,1].plot(grid,gaussian_kde(delta)(grid),color=INK,lw=2); axes[0,1].set(title="stack distribution",xlabel="Delta S")
    colors_by=labels if partition else bearing
    axes[0,2].scatter(dist,delta,c=colors_by,cmap=group_cmap,s=18,alpha=.7); axes[0,2].set(title="value vs distance",xlabel="distance (km)",ylabel="Delta S")
    axes[1,0].scatter(bearing,delta,c=dist,cmap="viridis",s=18,alpha=.7); axes[1,0].set(title="value vs bearing",xlabel="bearing (degrees)",ylabel="Delta S")
    axes[1,1].scatter(cold,warm,c=colors_by,cmap=group_cmap,s=18,alpha=.7); axes[1,1].plot([-.2,1],[-.2,1],color="black",ls="--",lw=1); axes[1,1].set(title="cold and warm components",xlabel="cold synchrony",ylabel="warm synchrony")
    stats=(f"median {np.median(delta):.3f}\nIQR {np.subtract(*np.quantile(delta,[.75,.25])):.3f}\n"
           f"distance eta2 {structure.distance_bin_eta_squared.values[yi,xi]:.3f}\n"
           f"direction eta2 {structure.direction_eta_squared.values[yi,xi]:.3f}\n"
           f"KDE modes (Scott) {structure.kde_mode_count.values[yi,xi]:.0f}\n"
           f"3-band consensus {bool(structure.kde_multimodal_bandwidth_consensus.values[yi,xi])}\n"
           f"neighbor excess {structure.two_group_neighbor_agreement_excess.values[yi,xi]:.3f}\n"
           f"component coverage {structure.two_group_component_coverage.values[yi,xi]:.3f}")
    axes[1,2].axis("off"); axes[1,2].text(.03,.96,stats,va="top",fontsize=11,bbox=dict(boxstyle="round",fc="#f7f4ed",ec=GOLD))
    figure.suptitle(title,fontsize=15,weight="bold"); _save(figure,path)


def _figure_components(stack: xr.Dataset, focal: tuple[int,int], path: Path) -> None:
    yi,xi=focal; figure,axes=plt.subplots(2,3,figsize=(12,7),constrained_layout=True)
    items=[("cold_synchrony",COLD,"cold"),("warm_synchrony",WARM,"warm"),("delta_s",DELTA,"Delta")]
    for col,(name,color,label) in enumerate(items):
        values=np.asarray(stack[name][:,yi,xi]); image=_map(axes[0,col],values.reshape(20,20),f"{label} center geography",cmap="RdBu_r" if name!="delta_s" else "RdBu",star=focal); figure.colorbar(image,ax=axes[0,col],shrink=.75)
        axes[1,col].hist(values,bins=28,color=color,alpha=.7); axes[1,col].axvline(np.median(values),color="black",lw=2); axes[1,col].set(title=f"median {np.median(values):.3f}; IQR {np.subtract(*np.quantile(values,[.75,.25])):.3f}",xlabel=label)
    figure.suptitle(f"High-IQR focal ({yi},{xi}): cold and warm contributions remain distinct",fontsize=15,weight="bold"); _save(figure,path)


def _figure_heterogeneity(reduced: xr.Dataset, structure: xr.Dataset, path: Path) -> None:
    panels=[(reduced.iqr,"Delta IQR"),(reduced.standard_deviation,"Delta SD"),(structure.distance_residual_iqr,"residual IQR after distance bins"),(structure.distance_bin_eta_squared,"distance eta2"),(structure.direction_eta_squared,"direction eta2"),(structure.kde_multimodal_bandwidth_consensus,"KDE multimodal consensus")]
    figure,axes=plt.subplots(2,3,figsize=(12,7.5),constrained_layout=True)
    for axis,(data,title) in zip(axes.flat,panels):
        image=_map(axis,data,title,cmap="magma",vmin=0); figure.colorbar(image,ax=axis,shrink=.75)
    figure.suptitle("Heterogeneity, distance, direction, and modality are not one map",fontsize=15,weight="bold"); _save(figure,path)


def _figure_radius_maps(radius: xr.Dataset, path: Path) -> None:
    panels=[("delta_median_radius_range","median range"),("delta_iqr_radius_range","IQR range"),("delta_maximum_absolute_median_step","max median step"),("delta_maximum_absolute_iqr_step","max IQR step"),("delta_experimental_median_stable_radius_km","experimental median stable radius"),("delta_experimental_iqr_stable_radius_km","experimental IQR stable radius")]
    figure,axes=plt.subplots(2,3,figsize=(12,7.5),constrained_layout=True)
    for axis,(name,title) in zip(axes.flat,panels):
        image=_map(axis,radius[name],title,cmap="magma",vmin=0); figure.colorbar(image,ax=axis,shrink=.75)
    figure.suptitle("Support-radius sensitivity is strongly spatially variable",fontsize=15,weight="bold"); _save(figure,path)


def _figure_relationship(reduced: xr.Dataset, radius: xr.Dataset, panel_maps: dict[str,np.ndarray], path: Path) -> dict[str,float]:
    x=np.asarray(reduced.iqr).ravel(); variables=[("incident RMSE",panel_maps["delta_rmse"].ravel()),("incident Spearman",panel_maps["delta_spearman"].ravel()),("incident sign disagreement",panel_maps["delta_sign_disagreement"].ravel()),("incident gradient RMSE",panel_maps["delta_gradient_vector_rmse"].ravel()),("IQR radius range",np.asarray(radius.delta_iqr_radius_range).ravel())]
    figure,axes=plt.subplots(2,3,figsize=(12,7),constrained_layout=True); results={}
    for axis,(label,y) in zip(axes.flat,variables):
        valid=np.isfinite(x)&np.isfinite(y); rho=float(spearmanr(x[valid],y[valid]).statistic); results[label]=rho
        axis.scatter(x[valid],y[valid],s=14,alpha=.55,color="#2c6e9b"); axis.set(xlabel="stack IQR",ylabel=label,title=f"Spearman rho={rho:.3f}")
    axes.flat[-1].axis("off"); axes.flat[-1].text(.05,.9,"Stack heterogeneity:\ncenter dependence at one focal pixel\n\nPanel change:\nwhole-landscape change as center moves\n\nRelated, not equivalent.",va="top",fontsize=12,bbox=dict(boxstyle="round",fc="#eef5fb",ec="#2c6e9b"))
    figure.suptitle("Stack heterogeneity and adjacent-panel change only correspond modestly",fontsize=15,weight="bold"); _save(figure,path); return results


def _figure_signature(path: Path) -> None:
    figure,axis=plt.subplots(figsize=(12,6)); axis.axis("off")
    fields=[("Cold magnitude","KEEP",COLD),("Warm magnitude","KEEP",WARM),("Delta asymmetry","KEEP",DELTA),("Stack IQR","KEEP",GOLD),("Radius sensitivity","DIAGNOSTIC","#00897b"),("Direction eta2","DIAGNOSTIC","#5e35b1"),("Spatial partition","EXPERIMENTAL","#6d4c41")]
    angles=np.linspace(0,2*np.pi,len(fields),endpoint=False)
    for angle,(name,status,color) in zip(angles,fields):
        x=.5+.37*np.cos(angle); y=.5+.37*np.sin(angle); axis.text(x,y,f"{name}\n{status}",ha="center",va="center",fontsize=11,color="white",bbox=dict(boxstyle="round,pad=.5",fc=color,ec="white")); axis.plot([.5,x],[.5,y],color="#aab7c4",zorder=-1)
    axis.text(.5,.5,"Synchrony\nSignature",ha="center",va="center",fontsize=16,weight="bold",bbox=dict(boxstyle="circle,pad=.7",fc="#eef5fb",ec=INK,lw=2)); axis.set_title("Proposed compact representation: evidence-ranked fields, not one scalar",fontsize=15,weight="bold"); _save(figure,path)


def _figure_typology(stack: xr.Dataset, radius: xr.Dataset, structure: xr.Dataset, record: dict[str,object], path: Path) -> None:
    yi,xi=int(record["y_index"]),int(record["x_index"]); delta=np.asarray(stack.delta_s[:,yi,xi]); cold=np.asarray(stack.cold_synchrony[:,yi,xi]); warm=np.asarray(stack.warm_synchrony[:,yi,xi]); dist=np.asarray(stack.distance_km[:,yi,xi]); bearing=np.asarray(stack.bearing_degrees[:,yi,xi]); labels=np.asarray(structure.two_group_label[:,yi,xi]); r=radius.radius_km.values
    fig,ax=plt.subplots(2,5,figsize=(16,6.2),constrained_layout=True)
    ax[0,0].imshow(np.zeros((20,20)),cmap="Greys",vmin=0,vmax=1); ax[0,0].scatter(xi,yi,marker="*",s=130,c=GOLD,edgecolor="black"); ax[0,0].set_title("A. focal location")
    im=ax[0,1].imshow(delta.reshape(20,20),cmap="RdBu",vmin=-.45,vmax=.45); ax[0,1].scatter(xi,yi,marker="*",s=75,c=GOLD,edgecolor="black"); ax[0,1].set_title("B. center-location Delta"); fig.colorbar(im,ax=ax[0,1],shrink=.65)
    ax[0,2].hist(delta,bins=25,density=True,color=DELTA,alpha=.45); grid=np.linspace(delta.min(),delta.max(),200); ax[0,2].plot(grid,gaussian_kde(delta)(grid),color=INK); ax[0,2].set_title("C. distribution")
    ax[0,3].scatter(dist,delta,c=labels,cmap="coolwarm",s=13); ax[0,3].set(title="D. value vs distance",xlabel="km")
    ax[0,4].scatter(bearing,delta,c=dist,cmap="viridis",s=13); ax[0,4].set(title="E. value vs bearing",xlabel="degrees")
    for axis,values,title,color in zip(ax[1,:3],(cold,warm,delta),("F. cold stack","G. warm stack","H. Delta stack"),(COLD,WARM,DELTA)):
        axis.hist(values,bins=22,color=color,alpha=.7); axis.axvline(np.median(values),color="black"); axis.set_title(title)
    summary=(f"I. summary\nmedian {record['delta_median']:.3f}\nIQR {record['delta_iqr']:.3f}\n"
             f"distance eta2 {record['distance_eta_squared']:.3f}\ndirection eta2 {record['direction_eta_squared']:.3f}\n"
             f"KDE modes {record['kde_modes_scott']}\nconsensus {record['kde_multimodal_bandwidth_consensus']}")
    ax[1,3].axis("off"); ax[1,3].text(.04,.95,summary,va="top",fontsize=10,bbox=dict(boxstyle="round",fc="#f7f4ed",ec=GOLD))
    ax[1,4].plot(r,radius.delta_median[:,yi,xi],color=DELTA,label="median"); ax[1,4].fill_between(r,radius.delta_q25[:,yi,xi],radius.delta_q75[:,yi,xi],color=DELTA,alpha=.2,label="IQR"); ax[1,4].set(title="J. radius growth",xlabel="km"); ax[1,4].legend(fontsize=8)
    fig.suptitle(str(record["role"]),fontsize=15,weight="bold"); _save(fig,path)


def _decision_rows() -> list[dict[str, object]]:
    return [
        {"Diagnostic":"cold/warm/Delta median","Scientific question":"magnitude and tail asymmetry","Mathematical definition":"median over pair values by focal pixel","Robustness in Phase 1.5":"stable, directly interpretable","Redundant with":"none","Computational cost":"streamable quantile","Nationally scalable?":"yes with bounded support","Interpretability":"high","Recommendation":"KEEP"},
        {"Diagnostic":"Delta IQR","Scientific question":"center dependence / heterogeneity","Mathematical definition":"q75-q25 over focal stack","Robustness in Phase 1.5":"large spatial contrast; robust","Redundant with":"SD partially","Computational cost":"streamable/sketchable quantile","Nationally scalable?":"yes","Interpretability":"high","Recommendation":"KEEP"},
        {"Diagnostic":"Delta SD","Scientific question":"stack dispersion","Mathematical definition":"standard deviation over centers","Robustness in Phase 1.5":"similar role to IQR; tail sensitive","Redundant with":"IQR","Computational cost":"online moments","Nationally scalable?":"yes","Interpretability":"high","Recommendation":"KEEP AS DIAGNOSTIC"},
        {"Diagnostic":"panel Spearman","Scientific question":"rank-pattern change","Mathematical definition":"rank correlation of adjacent landscapes","Robustness in Phase 1.5":"near ties can destabilize ranks","Redundant with":"none","Computational cost":"panel materialization/ranking","Nationally scalable?":"sample/tile boundaries","Interpretability":"conditional","Recommendation":"KEEP AS DIAGNOSTIC"},
        {"Diagnostic":"panel normalized RMSE","Scientific question":"relative magnitude change","Mathematical definition":"RMSE / pooled q95-q05","Robustness in Phase 1.5":"complements absolute RMSE","Redundant with":"RMSE partly","Computational cost":"linear in panel pixels","Nationally scalable?":"yes by neighboring centers","Interpretability":"high with denominator","Recommendation":"KEEP"},
        {"Diagnostic":"panel sign disagreement","Scientific question":"tail-asymmetry class change","Mathematical definition":"fraction of deadbanded signs unequal","Robustness in Phase 1.5":"deadband avoids zero noise","Redundant with":"none","Computational cost":"linear","Nationally scalable?":"yes","Interpretability":"high","Recommendation":"KEEP"},
        {"Diagnostic":"panel gradient RMSE","Scientific question":"spatial reorganization","Mathematical definition":"RMSE of x/y gradient-vector differences","Robustness in Phase 1.5":"useful but grid-resolution dependent","Redundant with":"RMSE correlated","Computational cost":"linear","Nationally scalable?":"yes","Interpretability":"moderate","Recommendation":"KEEP AS DIAGNOSTIC"},
        {"Diagnostic":"Wasserstein distance","Scientific question":"distribution shift only","Mathematical definition":"1D transport distance between panel values","Robustness in Phase 1.5":"ignores spatial arrangement; RMSE correlation high","Redundant with":"RMSE/MAE","Computational cost":"sorting","Nationally scalable?":"yes","Interpretability":"moderate","Recommendation":"DROP"},
        {"Diagnostic":"radius ranges/steps","Scientific question":"support sensitivity","Mathematical definition":"range and maximum step across nested radii","Robustness in Phase 1.5":"strongly spatially variable","Redundant with":"none","Computational cost":"nested accumulators","Nationally scalable?":"yes at fixed rings","Interpretability":"high","Recommendation":"KEEP AS DIAGNOSTIC"},
        {"Diagnostic":"experimental stable radius","Scientific question":"descriptive convergence scale","Mathematical definition":"first supported radius with remaining range <=0.02","Robustness in Phase 1.5":"threshold dependent","Redundant with":"radius ranges","Computational cost":"small after ring summaries","Nationally scalable?":"yes","Interpretability":"conditional","Recommendation":"EXPERIMENTAL"},
        {"Diagnostic":"distance eta2 / bins","Scientific question":"distance-associated variation","Mathematical definition":"between-bin variance / total variance","Robustness in Phase 1.5":"descriptive, bin dependent","Redundant with":"distance Spearman partly","Computational cost":"ring summaries","Nationally scalable?":"yes","Interpretability":"high","Recommendation":"KEEP AS DIAGNOSTIC"},
        {"Diagnostic":"direction eta2","Scientific question":"directional organization","Mathematical definition":"between-bearing-bin variance / total variance","Robustness in Phase 1.5":"clear signal; block sensitive","Redundant with":"none","Computational cost":"8-bin summaries","Nationally scalable?":"yes","Interpretability":"high","Recommendation":"KEEP AS DIAGNOSTIC"},
        {"Diagnostic":"KDE modes + coherent groups","Scientific question":"candidate spatial partition","Mathematical definition":"3-bandwidth modes plus mapped 2-group coherence","Robustness in Phase 1.5":"22 candidates, edge confounding remains","Redundant with":"none","Computational cost":"requires retained/sample stacks","Nationally scalable?":"not yet","Interpretability":"experimental","Recommendation":"EXPERIMENTAL"},
    ]


def _signature_dataset(stack, cold, warm, delta, radius, structure) -> xr.Dataset:
    ds=xr.Dataset(coords={"y":stack.y,"x":stack.x})
    for name,data in {
        "cold_median":cold["median"],"warm_median":warm["median"],"delta_median":delta["median"],
        "cold_iqr":cold.iqr,"warm_iqr":warm.iqr,"delta_iqr":delta.iqr,
        "delta_standard_deviation":delta.standard_deviation,
        "delta_median_radius_range":radius.delta_median_radius_range,
        "delta_iqr_radius_range":radius.delta_iqr_radius_range,
        "delta_experimental_median_stable_radius_km":radius.delta_experimental_median_stable_radius_km,
        "delta_experimental_iqr_stable_radius_km":radius.delta_experimental_iqr_stable_radius_km,
        "distance_bin_eta_squared":structure.distance_bin_eta_squared,
        "direction_eta_squared":structure.direction_eta_squared,
        "kde_multimodal_bandwidth_consensus":structure.kde_multimodal_bandwidth_consensus,
        "two_group_neighbor_agreement_excess":structure.two_group_neighbor_agreement_excess,
        "two_group_component_coverage":structure.two_group_component_coverage,
    }.items(): ds[name]=data
    ds.attrs.update({"analysis":"synchrony_signature_phase15_candidate","semantic_kind":"summary","status":"experimental schema; not a production product","source_analysis_fingerprint":stack.attrs["analysis_fingerprint"],"schema":"schemas/synchrony_signature_phase15.schema.json"})
    return ds


def _report(target: Path, figures: dict[str,Path], stack: xr.Dataset, findings: dict[str,object], typology: list[dict[str,object]], decisions: list[dict[str,object]]) -> None:
    target.parent.mkdir(parents=True,exist_ok=True)
    styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name="TitleX",parent=styles["Title"],fontName="Helvetica-Bold",fontSize=23,leading=27,textColor=colors.HexColor(INK),spaceAfter=12)); styles.add(ParagraphStyle(name="H1X",parent=styles["Heading1"],fontName="Helvetica-Bold",fontSize=16,leading=19,textColor=colors.HexColor("#174a70"),spaceBefore=5,spaceAfter=8)); styles.add(ParagraphStyle(name="H2X",parent=styles["Heading2"],fontSize=12.5,leading=15,textColor=colors.HexColor(DELTA),spaceBefore=5,spaceAfter=5)); styles.add(ParagraphStyle(name="BodyX",parent=styles["BodyText"],fontSize=9.2,leading=12.3,spaceAfter=6)); styles.add(ParagraphStyle(name="CalloutX",parent=styles["BodyText"],fontSize=10,leading=13,backColor=colors.HexColor("#eef5fb"),borderColor=colors.HexColor("#2c6e9b"),borderWidth=.8,borderPadding=8,spaceAfter=8)); styles.add(ParagraphStyle(name="SmallX",parent=styles["BodyText"],fontSize=7.5,leading=9.3));
    def p(text,style="BodyX"): return Paragraph(str(text).replace("&","&amp;"),styles[style])
    def image(path,width=7.0): return ReportImage(str(path),width=width*inch,height=width*inch*0.56)
    def table(rows,widths,small=True):
        converted=[[p(cell,"SmallX" if small else "BodyX") for cell in row] for row in rows]; item=Table(converted,colWidths=[w*inch for w in widths],repeatRows=1); item.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#174a70")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.3,colors.HexColor("#bdc3c7")),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),(colors.white,colors.HexColor("#f4f7f9"))),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4)])); return item
    def footer(canvas,doc):
        canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#d5d8dc")); canvas.line(.7*inch,.55*inch,7.8*inch,.55*inch); canvas.setFont("Helvetica",7.5); canvas.setFillColor(colors.HexColor("#5d6d7e")); canvas.drawString(.7*inch,.36*inch,"CubeDynamics - synchrony stack Phase 1.5"); canvas.drawRightString(7.8*inch,.36*inch,f"Page {doc.page}"); canvas.restoreState()
    doc=SimpleDocTemplate(str(target),pagesize=letter,leftMargin=.68*inch,rightMargin=.68*inch,topMargin=.62*inch,bottomMargin=.7*inch,title="CubeDynamics synchrony stack Phase 1.5",author="CubeDynamics")
    story=[p("Spatial synchrony stacks: Phase 1.5","TitleX"),p("What the validated stack means, which diagnostics survive, and the bounded Phase 2 decision","H2X"),p("Decision: GO WITH CHANGES for the 100 by 100 bounded benchmark. Retain separate cold, warm, and Delta pair values; robust focal magnitude/heterogeneity; nested radius rings; and a multidimensional adjacent-panel signature. Do not promote a universal radius, KDE regime map, or a scalar Q.","CalloutX"),p("Evidence base","H1X"),table([["Input","Exact Phase 1 observed experiment"],["Artifact",str(DEFAULT_STACK)],["Fingerprint",stack.attrs["analysis_fingerprint"]],["Repository base commit",findings["cube_dynamics_commit"]],["Working-tree qualifier",findings["working_tree_state"]],["PRISM interval",f"{stack.attrs['window_start']} through {stack.attrs['window_end']} (91 labels)"],["Grid / centers / pairs","20 by 20 / 400 / 80,200 canonical pairs"],["Settings","90-day window; min_t=10; median split q=0.5"],["Climate recomputation","None in Phase 1.5"]],[1.55,5.35],small=False),PageBreak(),p("1. Scientific hierarchy","H1X"),image(figures["hierarchy"]),p("A focal stack is the set of incident edge values at one node. A center landscape is the same undirected edge field viewed outward from a center. Panel comparison is second-order: it compares two vectors of incident edge patterns. Pair calculation benefits from graph symmetry and sparse finite-radius storage; focal summaries, radius rings, direction bins, and maps remain clearer as raster operations."),PageBreak(),p("2. Median alone fails","H1X"),image(figures["similar_medians"]),p("The two real focal pixels differ in median by only 0.0015, yet their IQRs are approximately 0.242 and 0.062. A median map therefore needs at least one robust heterogeneity field."),PageBreak(),p("3. Why the strongest Spearman break looks modest","H1X"),image(figures["panel_break"]),p("Q=0.088 is not a software error. The two Delta panels have narrow robust ranges (about 0.209 and 0.151) and almost every value has a neighbor within 0.005, so modest perturbations reorder many pixels. Absolute RMSE is 0.080, normalized RMSE is 0.429, and deadbanded sign disagreement is 0.535. Warm ranks remain very stable (0.986); cold changes dominate (cold Spearman 0.590). The evidence supports rank instability plus real local/sign change, not a wholesale spatial translation or a single causal boundary."),PageBreak(),p("4. Panel-change metrics","H1X"),image(figures["metric_comparison"]),p("Spearman is useful for rank structure but unsafe alone. Retain a compact signature: normalized or absolute magnitude change, rank structure with dynamic-range context, deadbanded sign change, and gradient-vector change. Wasserstein ignores geography and is strongly redundant with RMSE in this block."),PageBreak(),p("5. Where panel change occurs","H1X"),image(figures["panel_maps"]),p("Each map averages comparisons incident to a center. These are properties of landscape transitions, not focal-stack reductions."),PageBreak(),p("6. Low-IQR radius growth","H1X"),image(figures["radius_low"]),p("At focal (17,5), Delta IQR is about 0.056 and the experimental median/IQR stable radii are both 15 km. This is a narrow, comparatively uniform stack in this bounded window."),PageBreak(),p("7. High-IQR radius growth","H1X"),image(figures["radius_high"]),p("At focal (1,5), Delta IQR is about 0.242. The experimental median and IQR criteria do not settle until about 80 km. Curves can be nonmonotonic; the criterion is descriptive, not a validated synchrony radius."),PageBreak(),p("8. The high-IQR focal stack","H1X"),image(figures["high_structure"]),p("This broad stack is KDE-unimodal at all three tested bandwidths. Distance-bin eta-squared is about 0.10, direction eta-squared about 0.29, and distance residual IQR remains about 0.185. It is best described as broad continuous, directionally organized structure—not a validated multimodal transition."),PageBreak(),p("9. Cold/warm decomposition","H1X"),image(figures["components"]),p("At the high-IQR focal, cold IQR (about 0.218) exceeds warm IQR (about 0.175), but both components vary. Delta cannot be interpreted without preserving both inputs; the Delta median remains the median of pairwise cold-minus-warm values."),PageBreak(),p("10. Candidate spatial partition","H1X"),image(figures["partition"]),p("The interior focal (9,13) retains two KDE modes across 0.75x, 1.0x, and 1.25x Scott bandwidth. Its candidate groups occupy coherent center geography rather than being randomly intermixed. Across the block, 22 of 400 focals meet this bandwidth-consensus screen, many near margins. This is candidate structure only: one season, bounded support, forced two-group labels, and edge confounding preclude a climate-regime claim."),PageBreak(),p("11. Stack typology","H1X"),p("All six requested descriptive types have real examples in this block, but the names are selection roles rather than inferred climate classes."),table([["Type","Focal","IQR","distance eta2","direction eta2","modes","consensus"]]+[[r["role"],f"({r['y_index']},{r['x_index']})",f"{r['delta_iqr']:.3f}",f"{r['distance_eta_squared']:.3f}",f"{r['direction_eta_squared']:.3f}",str(r["kde_modes_scott"]),str(r["kde_multimodal_bandwidth_consensus"])] for r in typology],[2.3,.55,.55,.75,.75,.45,.7]),p("Standardized ten-panel figures are written as separate reusable PNG artifacts and included in the appendix."),PageBreak(),p("12. Heterogeneity and organization","H1X"),image(figures["heterogeneity"]),p("High IQR is neither multimodality nor spatial partitioning. Distance, direction, residual spread, and bandwidth-stable modes preserve different evidence."),PageBreak(),p("13. Radius sensitivity","H1X"),image(figures["radius_maps"]),p("Experimental stable median radii span 15-80 km (median 35 km); IQR radii span 15-100 km (median 40 km). Delta median radius ranges span about 0.027-0.282; IQR ranges span about 0.056-0.311. One fixed support radius is not equally representative everywhere in this block."),PageBreak(),p("14. Heterogeneity versus panel change","H1X"),image(figures["relationship"]),p("Correspondence is modest and sometimes counterintuitive. Stack IQR versus incident RMSE is positive but not strong; normalized RMSE and sign change can be weakly negative. The two objects answer different questions and must not be substituted for each other."),PageBreak(),p("15. Proposed SynchronySignature","H1X"),image(figures["signature"]),p("The candidate schema is machine-readable. Robust magnitude and IQR fields are ready; radius and direction are diagnostic; spatial partitioning remains experimental. No universal scalar preserves all axes."),PageBreak(),p("16. Phase 1.5 decision table","H1X")]
    headers=list(decisions[0]); compact=[[row[h] for h in headers] for row in decisions]
    for start in range(0,len(compact),5):
        story += [table([headers]+compact[start:start+5],[.8,1.0,1.15,.9,.75,.75,.65,.75,.75]),Spacer(1,.08*inch)]
        if start+5<len(compact): story.append(PageBreak()); story.append(p("Decision table (continued)","H1X"))
    answers=[
        ("1. Why Q about 0.088?","Narrow dynamic range and dense near-ties make ranks unstable; there is also real cold-driven local/sign change. RMSE 0.080 is modest absolutely but 0.429 of the pooled robust range."),
        ("2. Is Spearman useful?","Yes, as a rank-structure axis with range/tie context; not as a universal boundary scalar."),
        ("3. What accompanies it?","Normalized RMSE, deadbanded sign disagreement, and gradient-vector RMSE; retain cold/warm/Delta decomposition."),
        ("4. Do stacks stabilize?","Many do descriptively, but curves can be nonmonotonic and stabilization is not uniform."),
        ("5. At what scales here?","Experimental median stable radius: 15-80 km, median 35 km. IQR: 15-100 km, median 40 km."),
        ("6. Spatially variable?","Yes, strongly."),
        ("7. Fixed radius defensible?","Not as a universal scientific radius from this evidence. A common benchmark cap is defensible only with nested-ring sensitivity."),
        ("8. Distance explanation?","Distance-bin eta-squared has median about 0.10 and maximum about 0.45; distance alone usually leaves substantial residual spread."),
        ("9. Direction evident?","Yes. Direction eta-squared has median about 0.285 and reaches about 0.629, while remaining a descriptive block-sensitive statistic."),
        ("10. High-IQR modes?","The Phase 1 high-IQR example is broad continuous and bandwidth-stable unimodal. A minority of other stacks are candidate multimodal."),
        ("11. Modes geographically organized?","For the 22 screened candidates, mapped two-group labels can be strongly coherent; many candidates are near block margins, so none establishes a regime."),
        ("12. High-IQR transition?","No: it is not a multimodal transition under these tests; it is broad and directionally organized."),
        ("13. Cold/warm contributions?","Both vary, with larger cold than warm spread at the high-IQR focal. The strongest panel-rank break is mainly cold-driven while warm ranks remain stable."),
        ("14. Same phenomenon?","No. Associations are modest; focal center-dependence and whole-landscape transition are distinct."),
        ("15. Smallest nonredundant set?","Cold median, warm median, pairwise-Delta median, Delta IQR, nested radius sensitivity, direction eta-squared, and the four-axis panel-change signature. Partition fields remain experimental."),
        ("16. National maps?","Cold, warm, Delta medians; Delta IQR; bounded-radius sensitivity; and selected panel-change axes after the benchmark."),
        ("17. Diagnostics only?","SD, distance/direction profiles, experimental stable radius, KDE modes/group coherence, Pearson, and gradient details beyond the retained transition axis."),
        ("18. Preserve before discarding pairs?","Cold/warm/Delta values and valid counts by bounded edge or exact mergeable summaries; distance/bearing; nested-ring accumulators/quantile sketches; adjacent-center panels or sufficient tile halos; sampled full stacks for audit."),
        ("19. Phase 2 radius strategy?","Benchmark nested 25, 50, 75, and 100 km rings with halos; compare convergence and edge bias rather than selecting one radius beforehand."),
        ("20. Ready for 100 by 100?","GO WITH CHANGES: yes for a bounded observed benchmark with nested support and retained diagnostics; no for a national run or regime product."),
    ]
    story += [PageBreak(),p("17. Required answers and final gate","H1X")]
    for title,answer in answers: story += [p(title,"H2X"),p(answer)]
    story += [PageBreak(),p("18. Phase 2 bounded benchmark contract","H1X"),p("Accumulate: separate cold, warm, and Delta pair values, joint-tail counts, distance and bearing, and canonical pair identity. Retain: medians, Delta IQR, nested-ring summaries, panel normalized RMSE/Spearman/sign/gradient signature, audit samples, fingerprints, and exact support metadata. Test: 25/50/75/100 km with tile halos and explicit edge checks. Discard only after equivalence: redundant MAE/Wasserstein fields and complete dense pair arrays outside audit samples. Experimental: stable-radius threshold, KDE modes, forced groups, and any regime label.","CalloutX"),p("Graph interpretation","H1X"),p("Pair computation and storage benefit from an undirected sparse graph. A focal stack is a node's incident edges; a center landscape is those edges rasterized by the other endpoint. Panel comparison compares two such edge-pattern rasters. Distance rings, bearing bins, neighborhood coherence, and final products remain spatial-raster operations because that form preserves geography and support."),p("Limitations","H1X"),p("One observed Colorado winter block cannot establish seasonal or national invariance. The 20 by 20 domain truncates support and can create edge-associated structure. Eta-squared depends on bins, gradient metrics depend on resolution, and the stability threshold is exploratory. KDE consensus and spatially coherent forced groups flag candidates; they do not identify causal or climatological regimes."),PageBreak(),p("Appendix: standardized typology figures","H1X")]
    for record in typology:
        key=f"typology_{record['y_index']}_{record['x_index']}"; story += [p(str(record["role"]),"H2X"),image(figures[key])]
        if record is not typology[-1]: story.append(PageBreak())
    doc.build(story,onFirstPage=footer,onLaterPages=footer)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--stack",type=Path,default=DEFAULT_STACK); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); parser.add_argument("--report",type=Path,default=DEFAULT_REPORT); args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True); figure_dir=args.output/"figures"; figure_dir.mkdir(parents=True,exist_ok=True)
    with xr.open_dataset(args.stack) as opened: stack=opened.load()
    if stack.attrs.get("analysis_fingerprint") != EXPECTED_FINGERPRINT: raise ValueError("Phase 1.5 requires the exact validated Phase 1 stack fingerprint")
    timings={}
    started=time.perf_counter(); panel=(pipe(stack)|v.panel_change_diagnostics(deadband=.02,near_tie_epsilon=.005)).unwrap(); timings["panel_change_seconds"]=time.perf_counter()-started
    started=time.perf_counter(); radius=(pipe(stack)|v.stack_radius_diagnostics(stable_tolerance=.02,stable_min_centers=25)).unwrap(); timings["radius_seconds"]=time.perf_counter()-started
    structures={}
    for metric in ("cold_synchrony","warm_synchrony","delta_s"):
        started=time.perf_counter(); structures[metric]=(pipe(stack)|v.stack_structure_diagnostics(metric=metric)).unwrap(); timings[f"structure_{metric}_seconds"]=time.perf_counter()-started
    cold=v.reduce_synchrony_stack(metric="cold_synchrony")(stack); warm=v.reduce_synchrony_stack(metric="warm_synchrony")(stack); delta=v.reduce_synchrony_stack(metric="delta_s")(stack); structure=structures["delta_s"]
    panel.to_netcdf(args.output/"panel_change_diagnostics.nc"); _write_panel_csv(panel,args.output/"panel_change_table.csv"); radius.to_netcdf(args.output/"stack_radius_diagnostics.nc")
    for metric,data in structures.items(): data.to_netcdf(args.output/f"stack_structure_{metric}.nc")
    signature=_signature_dataset(stack,cold,warm,delta,radius,structure); signature.to_netcdf(args.output/"synchrony_signature_phase15_candidate.nc")
    decisions=_decision_rows(); _write_rows(args.output/"phase15_decision_table.csv",decisions); (args.output/"phase15_decision_table.json").write_text(json.dumps(decisions,indent=2)+"\n",encoding="utf-8")
    typology=_typology(stack,delta,structure); (args.output/"stack_typology.json").write_text(json.dumps(typology,indent=2)+"\n",encoding="utf-8")
    disagreements=_metric_disagreements(panel); _write_rows(args.output/"panel_metric_disagreement_examples.csv",disagreements)
    figures={name:figure_dir/f"{name}.png" for name in ["hierarchy","similar_medians","panel_break","metric_comparison","panel_maps","radius_low","radius_high","high_structure","components","partition","heterogeneity","radius_maps","relationship","signature"]}
    _figure_hierarchy(figures["hierarchy"]); similar=_figure_similar_medians(stack,radius,figures["similar_medians"]); boundary=_figure_panel_break(stack,panel,figures["panel_break"]); metric_correlations=_figure_metric_comparison(panel,disagreements,figures["metric_comparison"]); panel_maps=_figure_panel_maps(panel,figures["panel_maps"]); _figure_radius(radius,(17,5),"low-IQR",figures["radius_low"]); _figure_radius(radius,(1,5),"high-IQR",figures["radius_high"]); _figure_stack_structure(stack,structure,(1,5),"High-IQR Phase 1 focal: broad, continuous, directional",figures["high_structure"]); _figure_components(stack,(1,5),figures["components"]); _figure_stack_structure(stack,structure,(9,13),"Interior candidate partition: groups mapped back to center geography",figures["partition"],partition=True); _figure_heterogeneity(delta,structure,figures["heterogeneity"]); _figure_radius_maps(radius,figures["radius_maps"]); relationship=_figure_relationship(delta,radius,panel_maps,figures["relationship"]); _figure_signature(figures["signature"])
    for record in typology:
        key=f"typology_{record['y_index']}_{record['x_index']}"; figures[key]=figure_dir/f"{key}.png"; _figure_typology(stack,radius,structure,record,figures[key])
    stable_median=np.asarray(radius.delta_experimental_median_stable_radius_km); stable_iqr=np.asarray(radius.delta_experimental_iqr_stable_radius_km)
    try:
        commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
        dirty=bool(subprocess.check_output(["git","status","--porcelain"],text=True).strip())
    except (OSError,subprocess.CalledProcessError):
        commit="unavailable"; dirty=True
    findings={"phase2_decision":"GO WITH CHANGES","phase1_stack":str(args.stack),"phase1_fingerprint":stack.attrs["analysis_fingerprint"],"cube_dynamics_commit":commit,"working_tree_state":"base commit plus uncommitted Phase 1/1.5 changes" if dirty else "clean checkout","source":"observed PRISM tmin/tmax","window":{"start":stack.attrs["window_start"],"end":stack.attrs["window_end"],"labels":91},"settings":{"grid":"20x20","centers":400,"canonical_pairs":80200,"window_days":90,"min_t":10,"split_quantile":.5},"diagnostic_runtimes_seconds":timings,"strongest_panel_break":boundary,"similar_median_example":similar,"metric_correlations":metric_correlations,"heterogeneity_panel_relationships":relationship,"experimental_stable_radius_km":{"median":{"minimum":float(np.nanmin(stable_median)),"median":float(np.nanmedian(stable_median)),"maximum":float(np.nanmax(stable_median))},"iqr":{"minimum":float(np.nanmin(stable_iqr)),"median":float(np.nanmedian(stable_iqr)),"maximum":float(np.nanmax(stable_iqr))}},"bandwidth_consensus_multimodal_focals":int(np.nansum(structure.kde_multimodal_bandwidth_consensus)),"interpretation":"Candidate multimodality and two-group coherence are experimental and do not establish climate regimes.","no_climate_recomputation":True,"no_100x100_or_national_run":True}
    (args.output/"phase15_findings.json").write_text(json.dumps(findings,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    _report(args.report,figures,stack,findings,typology,decisions)
    print(json.dumps({"report":str(args.report),"output":str(args.output),"figures":len(figures),"decision":"GO WITH CHANGES","timings":timings},indent=2))


if __name__ == "__main__":
    main()
