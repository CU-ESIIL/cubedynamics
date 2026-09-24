#!/usr/bin/env python3
"""Audit location-specific temperature ranks against current synchrony semantics.

This is a mandatory decision gate.  It does not run Colorado when the explicit
rank representation is equivalent to the existing local-quantile + Spearman
calculation on the real complete-support sample grid.
"""

from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
from scipy.stats import rankdata, spearmanr
import xarray as xr

from cubedynamics.serialization import sanitize_netcdf_attrs
from cubedynamics.stats.tails import one_tail_spearman


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "rank-rescaled-synchrony-gate"
SAMPLE_INPUT = ROOT / "artifacts" / "center-pixel-synchrony-walkthrough" / "intermediate" / "prism_boulder_2023-11-01_2024-01-30.nc"
SAMPLE_STACK = ROOT / "artifacts" / "synchrony-stack-phase1" / "prism_20x20_synchrony_stack.nc"
COLORADO_INPUT = ROOT / "artifacts" / "synchrony-stack-phase2" / "prism_colorado_plus_100km_20231101_20240130.nc"
COLORADO_BASELINE = ROOT / "artifacts" / "nonstacked-colorado-baseline" / "colorado_nonstacked_synchrony.nc"
Q = 0.5
MIN_T = 10
FOCAL_Y = 10
FOCAL_X = 10


def empirical_rank_coordinates(values: np.ndarray) -> np.ndarray:
    """Return average empirical ranks divided by ``n + 1`` for finite values."""

    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError("empirical_rank_coordinates expects a one-dimensional array")
    result = np.full(array.shape, np.nan, dtype=float)
    finite = np.isfinite(array)
    count = int(np.count_nonzero(finite))
    if count:
        result[finite] = rankdata(array[finite], method="average") / float(count + 1)
    return result


def tail_membership(values: np.ndarray, *, tail: str, q: float = Q) -> np.ndarray:
    """Select a tail from rank coordinates using the current split inequalities."""

    if tail not in {"lower", "upper"}:
        raise ValueError("tail must be lower or upper")
    ranks = empirical_rank_coordinates(values)
    threshold_q = q if tail == "lower" else 1.0 - q
    threshold = np.nanquantile(ranks, threshold_q)
    return np.isfinite(ranks) & (ranks <= threshold if tail == "lower" else ranks > threshold)


def rank_rescaled_tail_spearman(
    x: np.ndarray,
    y: np.ndarray,
    *,
    tail: str,
    q: float = Q,
    min_t: int = MIN_T,
) -> tuple[float, int, np.ndarray, np.ndarray, np.ndarray]:
    """Rank each marginal, select its tail, then retain current Spearman semantics."""

    x_rank = empirical_rank_coordinates(x)
    y_rank = empirical_rank_coordinates(y)
    valid = np.isfinite(x_rank) & np.isfinite(y_rank)
    threshold_q = q if tail == "lower" else 1.0 - q
    x_threshold = np.nanquantile(x_rank, threshold_q)
    y_threshold = np.nanquantile(y_rank, threshold_q)
    if tail == "lower":
        selected = valid & (x_rank <= x_threshold) & (y_rank <= y_threshold)
    elif tail == "upper":
        selected = valid & (x_rank > x_threshold) & (y_rank > y_threshold)
    else:
        raise ValueError("tail must be lower or upper")
    count = int(np.count_nonzero(selected))
    if count < min_t:
        return float("nan"), count, selected, x_rank, y_rank
    selected_x = rankdata(x_rank[selected], method="average")
    selected_y = rankdata(y_rank[selected], method="average")
    denominator = np.sqrt(
        np.sum((selected_x - selected_x.mean()) ** 2)
        * np.sum((selected_y - selected_y.mean()) ** 2)
    )
    value = (
        float(np.sum((selected_x - selected_x.mean()) * (selected_y - selected_y.mean())) / denominator)
        if denominator > 0 else float("nan")
    )
    return value, count, selected, x_rank, y_rank


def raw_tail_membership(x: np.ndarray, y: np.ndarray, *, tail: str, q: float = Q) -> np.ndarray:
    """Return the current pair-valid raw-value tail membership on original indices."""

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    selected = np.zeros(x.shape, dtype=bool)
    if not np.any(valid):
        return selected
    threshold_q = q if tail == "lower" else 1.0 - q
    x_threshold = np.quantile(x[valid], threshold_q)
    y_threshold = np.quantile(y[valid], threshold_q)
    if tail == "lower":
        selected[valid] = (x[valid] <= x_threshold) & (y[valid] <= y_threshold)
    elif tail == "upper":
        selected[valid] = (x[valid] > x_threshold) & (y[valid] > y_threshold)
    else:
        raise ValueError("tail must be lower or upper")
    return selected


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.json")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _netcdf(path: Path, dataset: xr.Dataset) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.nc")
    clean = sanitize_netcdf_attrs(dataset, copy=True)
    for name in clean.variables:
        clean[name].encoding = {}
    clean.to_netcdf(temporary, engine="scipy")
    temporary.replace(path)


def _load_sample() -> tuple[xr.Dataset, xr.Dataset]:
    with xr.open_dataset(SAMPLE_INPUT, engine="scipy") as opened:
        source = opened.load()
    with xr.open_dataset(SAMPLE_STACK) as opened:
        stack = opened.load()
    sample = source.sel(y=stack.y, x=stack.x)
    if sample.sizes["y"] != 20 or sample.sizes["x"] != 20:
        raise RuntimeError("Failed to recover the exact 20 by 20 sample grid")
    if int(sample.tmin.isnull().sum()) or int(sample.tmax.isnull().sum()):
        raise RuntimeError("The audited real sample unexpectedly contains missing observations")
    return sample, stack


def _calculate_surface(sample: xr.Dataset, stack: xr.Dataset) -> tuple[xr.Dataset, list[dict[str, object]]]:
    shape = (sample.sizes["y"], sample.sizes["x"])
    arrays = {
        name: np.full(shape, np.nan, dtype=float)
        for name in (
            "old_cold", "rank_cold", "old_hot", "rank_hot", "old_delta", "rank_delta",
            "cold_difference", "hot_difference", "delta_difference",
        )
    }
    counts = {
        name: np.zeros(shape, dtype=np.int16)
        for name in (
            "old_cold_count", "rank_cold_count", "old_hot_count", "rank_hot_count",
            "cold_membership_changes", "hot_membership_changes",
        )
    }
    center_cold = np.asarray(sample.tmin[:, FOCAL_Y, FOCAL_X].values, dtype=float)
    center_hot = np.asarray(sample.tmax[:, FOCAL_Y, FOCAL_X].values, dtype=float)
    pair_rows: list[dict[str, object]] = []
    center_lat = float(sample.y.values[FOCAL_Y])
    center_lon = float(sample.x.values[FOCAL_X])

    for yi in range(shape[0]):
        for xi in range(shape[1]):
            other_cold = np.asarray(sample.tmin[:, yi, xi].values, dtype=float)
            other_hot = np.asarray(sample.tmax[:, yi, xi].values, dtype=float)
            old_cold, old_cold_count = one_tail_spearman(center_cold, other_cold, tail="lower", b=Q, min_t=MIN_T)
            old_hot, old_hot_count = one_tail_spearman(center_hot, other_hot, tail="upper", b=Q, min_t=MIN_T)
            rank_cold, rank_cold_count, rank_cold_mask, _, _ = rank_rescaled_tail_spearman(center_cold, other_cold, tail="lower")
            rank_hot, rank_hot_count, rank_hot_mask, _, _ = rank_rescaled_tail_spearman(center_hot, other_hot, tail="upper")
            raw_cold_mask = raw_tail_membership(center_cold, other_cold, tail="lower")
            raw_hot_mask = raw_tail_membership(center_hot, other_hot, tail="upper")
            arrays["old_cold"][yi, xi] = old_cold
            arrays["rank_cold"][yi, xi] = rank_cold
            arrays["old_hot"][yi, xi] = old_hot
            arrays["rank_hot"][yi, xi] = rank_hot
            arrays["old_delta"][yi, xi] = old_cold - old_hot
            arrays["rank_delta"][yi, xi] = rank_cold - rank_hot
            arrays["cold_difference"][yi, xi] = rank_cold - old_cold
            arrays["hot_difference"][yi, xi] = rank_hot - old_hot
            arrays["delta_difference"][yi, xi] = arrays["rank_delta"][yi, xi] - arrays["old_delta"][yi, xi]
            counts["old_cold_count"][yi, xi] = old_cold_count
            counts["rank_cold_count"][yi, xi] = rank_cold_count
            counts["old_hot_count"][yi, xi] = old_hot_count
            counts["rank_hot_count"][yi, xi] = rank_hot_count
            counts["cold_membership_changes"][yi, xi] = np.count_nonzero(raw_cold_mask != rank_cold_mask)
            counts["hot_membership_changes"][yi, xi] = np.count_nonzero(raw_hot_mask != rank_hot_mask)
            if (yi, xi) in {(0, 0), (4, 15), (10, 15), (19, 19)}:
                distance = float(stack.distance_km.sel(center=FOCAL_Y * 20 + FOCAL_X).values[yi, xi])
                pair_rows.append({
                    "label": f"y{yi}_x{xi}", "y_index": yi, "x_index": xi,
                    "latitude": float(sample.y.values[yi]), "longitude": float(sample.x.values[xi]),
                    "distance_km": distance, "cold_count": rank_cold_count, "hot_count": rank_hot_count,
                    "rank_cold": rank_cold, "rank_hot": rank_hot, "rank_delta": rank_cold-rank_hot,
                    "tail_membership_changes": int(np.count_nonzero(raw_cold_mask != rank_cold_mask) + np.count_nonzero(raw_hot_mask != rank_hot_mask)),
                })

    dataset = xr.Dataset(
        {
            **{name: (("y", "x"), values) for name, values in arrays.items()},
            **{name: (("y", "x"), values) for name, values in counts.items()},
        },
        coords={"y": sample.y, "x": sample.x},
        attrs={
            "analysis": "rank_rescaling_sample_grid_gate",
            "source": sample.attrs.get("source", "unknown"),
            "time_start": str(sample.time.values[0]), "time_end": str(sample.time.values[-1]),
            "time_observations": sample.sizes["time"], "split_quantile": Q,
            "rank_convention": "average_rank / (n + 1)",
            "cold_inequality": "rank <= its exact 0.5 quantile", "hot_inequality": "rank > its exact 0.5 quantile",
            "focal_y_index": FOCAL_Y, "focal_x_index": FOCAL_X,
            "focal_latitude": center_lat, "focal_longitude": center_lon,
            "stacking": "none", "statewide_status": "stopped_before_colorado_if_equivalent",
        },
    )
    checkpoint_center = FOCAL_Y * 20 + FOCAL_X
    checkpoint_errors = {
        "cold": float(np.nanmax(np.abs(dataset.old_cold.values - stack.cold_synchrony.sel(center=checkpoint_center).values))),
        "hot": float(np.nanmax(np.abs(dataset.old_hot.values - stack.warm_synchrony.sel(center=checkpoint_center).values))),
        "delta": float(np.nanmax(np.abs(dataset.old_delta.values - stack.delta_s.sel(center=checkpoint_center).values))),
    }
    dataset.attrs["maximum_checkpoint_error"] = max(checkpoint_errors.values())
    return dataset, pair_rows


def _one_pair_audit(sample: xr.Dataset, surface: xr.Dataset) -> dict[str, object]:
    a = (FOCAL_Y, FOCAL_X)
    b = (0, 0)
    record: dict[str, object] = {"location_a": a, "location_b": b, "tails": {}}
    audit_rows = []
    for label, variable, tail in (("cold", "tmin", "lower"), ("hot", "tmax", "upper")):
        x = np.asarray(sample[variable][:, a[0], a[1]].values, dtype=float)
        y = np.asarray(sample[variable][:, b[0], b[1]].values, dtype=float)
        old, old_count = one_tail_spearman(x, y, tail=tail, b=Q, min_t=MIN_T)
        new, new_count, new_mask, x_rank, y_rank = rank_rescaled_tail_spearman(x, y, tail=tail)
        old_mask = raw_tail_membership(x, y, tail=tail)
        record["tails"][label] = {
            "old_synchrony": old, "rank_synchrony": new, "difference": new-old,
            "old_joint_count": old_count, "rank_joint_count": new_count,
            "membership_changes": int(np.count_nonzero(old_mask != new_mask)),
            "location_a_raw_threshold": float(np.quantile(x, Q)),
            "location_b_raw_threshold": float(np.quantile(y, Q)),
            "location_a_rank_threshold": float(np.quantile(x_rank, Q)),
            "location_b_rank_threshold": float(np.quantile(y_rank, Q)),
        }
        for index, date in enumerate(sample.time.values):
            audit_rows.append({
                "date": str(date), "tail": label, "a_raw": x[index], "b_raw": y[index],
                "a_rank": x_rank[index], "b_rank": y_rank[index],
                "old_selected": bool(old_mask[index]), "rank_selected": bool(new_mask[index]),
            })
    record["old_delta"] = record["tails"]["cold"]["old_synchrony"] - record["tails"]["hot"]["old_synchrony"]
    record["rank_delta"] = record["tails"]["cold"]["rank_synchrony"] - record["tails"]["hot"]["rank_synchrony"]
    record["delta_difference"] = record["rank_delta"] - record["old_delta"]
    record["location_a_coordinates"] = [float(sample.y.values[a[0]]), float(sample.x.values[a[1]])]
    record["location_b_coordinates"] = [float(sample.y.values[b[0]]), float(sample.x.values[b[1]])]
    record["row_count"] = len(audit_rows)
    with (OUTPUT / "one_pair_observations.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=audit_rows[0].keys())
        writer.writeheader(); writer.writerows(audit_rows)
    return record


def _collapse(surface: xr.Dataset) -> dict[str, object]:
    valid = np.ones((20, 20), dtype=bool)
    valid[FOCAL_Y, FOCAL_X] = False
    output = {"self_pair_excluded": True, "nonself_pairs": int(valid.sum()), "old": {}, "rank": {}, "difference": {}}
    for metric in ("cold", "hot", "delta"):
        old = np.asarray(surface[f"old_{metric}"].values, dtype=float)[valid]
        new = np.asarray(surface[f"rank_{metric}"].values, dtype=float)[valid]
        output["old"][metric] = float(np.nanmedian(old))
        output["rank"][metric] = float(np.nanmedian(new))
        output["difference"][metric] = output["rank"][metric] - output["old"][metric]
        ranks = empirical_rank_coordinates(new[np.isfinite(new)])
        output.setdefault("within_neighborhood_rank_median", {})[metric] = float(np.median(ranks))
    output["old"]["delta_medians"] = output["old"]["cold"] - output["old"]["hot"]
    output["rank"]["delta_medians"] = output["rank"]["cold"] - output["rank"]["hot"]
    return output


def _figures(sample: xr.Dataset, surface: xr.Dataset, pair: dict[str, object], pair_rows: list[dict[str, object]]) -> list[str]:
    figure_dir = OUTPUT / "figures"; figure_dir.mkdir(parents=True, exist_ok=True)
    dates = sample.time.values
    a = (FOCAL_Y, FOCAL_X); b = (0, 0)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    for ax, variable, title in ((axes[0,0], "tmin", "Raw TMIN (cold calculation)"), (axes[0,1], "tmax", "Raw TMAX (hot calculation)")):
        ax.plot(dates, sample[variable][:,a[0],a[1]], label="A focal", lw=1.5)
        ax.plot(dates, sample[variable][:,b[0],b[1]], label="B comparison", lw=1.2)
        ax.axhline(float(np.quantile(sample[variable][:,a[0],a[1]], .5)), color="#1f77b4", ls="--", alpha=.6)
        ax.axhline(float(np.quantile(sample[variable][:,b[0],b[1]], .5)), color="#ff7f0e", ls="--", alpha=.6)
        ax.set_title(title); ax.set_ylabel("°C"); ax.legend(); ax.tick_params(axis="x", rotation=25)
    for ax, variable, tail, title in ((axes[1,0], "tmin", "lower", "Location-specific ranks: cold"), (axes[1,1], "tmax", "upper", "Location-specific ranks: hot")):
        x = sample[variable][:,a[0],a[1]].values; y = sample[variable][:,b[0],b[1]].values
        _, _, selected, xranks, yranks = rank_rescaled_tail_spearman(x, y, tail=tail)
        ax.plot(dates, xranks, label="A rank", lw=1.3); ax.plot(dates, yranks, label="B rank", lw=1.1)
        ax.scatter(dates[selected], xranks[selected], color="#264653", s=22, label="joint selected")
        ax.axhline(float(np.quantile(xranks, .5)), color="#1f77b4", ls="--", lw=1)
        ax.axhline(float(np.quantile(yranks, .5)), color="#ff7f0e", ls=":", lw=1)
        ax.set_ylim(0,1); ax.set_title(title); ax.set_ylabel("average rank / (n+1)"); ax.tick_params(axis="x", rotation=25); ax.legend()
    fig.suptitle("One real pair: raw temperatures and explicit rank-tail membership", fontsize=16, weight="bold")
    one_pair = figure_dir / "one_pair_rank_audit.png"; fig.savefig(one_pair, dpi=190, facecolor="white"); plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(13.5, 8), constrained_layout=True)
    for row, prefix, row_title in ((0, "rank", "Explicit rank-rescaled"), (1, "old", "Current raw-quantile + Spearman")):
        for col, (metric, title) in enumerate((("cold", "COLD"), ("hot", "HOT"), ("delta", "DELTA = COLD - HOT"))):
            values = surface[f"{prefix}_{metric}"].values
            limit = max(float(np.nanpercentile(np.abs(values), 99)), .01)
            im = axes[row,col].imshow(values, cmap="RdBu", norm=TwoSlopeNorm(0,-limit,limit))
            axes[row,col].scatter([FOCAL_X],[FOCAL_Y], marker="*", s=110, c="#f4b942", edgecolor="black")
            for point in pair_rows: axes[row,col].scatter([point["x_index"]],[point["y_index"]], s=25, facecolor="none", edgecolor="black")
            axes[row,col].set(title=f"{row_title}: {title}", xticks=[], yticks=[]); fig.colorbar(im, ax=axes[row,col], shrink=.72)
    fig.suptitle("20×20 center-reference surfaces before immediate collapse", fontsize=16, weight="bold")
    surfaces = figure_dir / "sample_grid_surfaces.png"; fig.savefig(surfaces, dpi=190, facecolor="white"); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    for ax, metric, title in zip(axes, ("cold", "hot", "delta"), ("Cold", "Hot", "Delta")):
        old = surface[f"old_{metric}"].values.ravel(); new = surface[f"rank_{metric}"].values.ravel()
        ax.scatter(old, new, s=12, alpha=.55); lo=min(np.nanmin(old),np.nanmin(new)); hi=max(np.nanmax(old),np.nanmax(new)); ax.plot([lo,hi],[lo,hi],color="black",ls="--")
        ax.set(title=f"{title}: old vs rank", xlabel="Current method", ylabel="Explicit rank method")
        ax.text(.04,.94,f"max |Δ| = {np.nanmax(np.abs(new-old)):.1e}", transform=ax.transAxes, va="top")
    comparison = figure_dir / "old_vs_rank_sample_grid.png"; fig.savefig(comparison,dpi=190,facecolor="white"); plt.close(fig)

    with xr.open_dataset(COLORADO_INPUT, engine="scipy") as opened: colorado = opened.load()
    with xr.open_dataset(COLORADO_BASELINE, engine="scipy") as opened: mask = opened.output_mask.load().values.astype(bool)
    mean_temp = ((colorado.tmin + colorado.tmax) / 2).mean("time").values
    indices = np.argwhere(mask)
    order = np.argsort(mean_temp[mask])
    choices = [indices[order[i]] for i in (0, len(order)//3, 2*len(order)//3, -1)]
    fig, axes = plt.subplots(2, 2, figsize=(12,7), constrained_layout=True)
    rows=[]
    for number, (yi,xi) in enumerate(choices):
        values=((colorado.tmin[:,yi,xi]+colorado.tmax[:,yi,xi])/2).values.astype(float)
        ranks=empirical_rank_coordinates(values)
        label=f"Site {number+1}: {float(colorado.y[yi]):.2f}°N, {abs(float(colorado.x[xi])):.2f}°W"
        axes[0,0].plot(dates,values,lw=1,label=label); axes[0,1].plot(dates,ranks,lw=1,label=label)
        axes[1,0].hist(values,bins=15,histtype="step",lw=1.5,label=label); axes[1,1].hist(ranks,bins=np.linspace(0,1,12),histtype="step",lw=1.5,label=label)
        rows.append({"site":number+1,"latitude":float(colorado.y[yi]),"longitude":float(colorado.x[xi]),"raw_median_c":float(np.median(values)),"raw_p10_c":float(np.quantile(values,.1)),"raw_p90_c":float(np.quantile(values,.9)),"rank_median":float(np.median(ranks))})
    for ax,title,ylabel in ((axes[0,0],"Raw local temperatures","°C"),(axes[0,1],"Location-specific empirical ranks","rank / (n+1)"),(axes[1,0],"Different absolute distributions","days"),(axes[1,1],"Comparable relative-position distributions","days")):
        ax.set_title(title); ax.set_ylabel(ylabel); ax.legend(fontsize=7)
    scaling=figure_dir/"global_scaling_diagnostic.png"; fig.savefig(scaling,dpi=190,facecolor="white"); plt.close(fig)
    with (OUTPUT/"scaling_sites.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    return [str(path.relative_to(ROOT)) for path in (one_pair,surfaces,comparison,scaling)]


def main() -> None:
    started=time.perf_counter(); OUTPUT.mkdir(parents=True,exist_ok=True)
    sample, stack=_load_sample()
    surface, pair_rows=_calculate_surface(sample,stack)
    _netcdf(OUTPUT/"sample_grid_rank_gate.nc",surface)
    pair=_one_pair_audit(sample,surface); _json(OUTPUT/"one_pair_audit.json",pair)
    collapse=_collapse(surface); _json(OUTPUT/"sample_grid_collapse.json",collapse)
    with (OUTPUT/"sample_grid_example_pairs.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=pair_rows[0].keys()); writer.writeheader(); writer.writerows(pair_rows)
    figures=_figures(sample,surface,pair,pair_rows)
    comparison={}
    for metric in ("cold","hot","delta"):
        old=surface[f"old_{metric}"].values.ravel(); new=surface[f"rank_{metric}"].values.ravel(); finite=np.isfinite(old)&np.isfinite(new); difference=new[finite]-old[finite]
        comparison[metric]={"valid_pairs":int(finite.sum()),"pearson":float(np.corrcoef(old[finite],new[finite])[0,1]),"spearman":float(spearmanr(old[finite],new[finite]).statistic),"rmse":float(np.sqrt(np.mean(difference**2))),"median_difference":float(np.median(difference)),"difference_iqr":float(np.quantile(difference,.75)-np.quantile(difference,.25)),"maximum_absolute_difference":float(np.max(np.abs(difference)))}
    membership_changes=int(surface.cold_membership_changes.sum()+surface.hot_membership_changes.sum())
    maximum_difference=max(value["maximum_absolute_difference"] for value in comparison.values())
    equivalent=membership_changes==0 and maximum_difference < 1e-12
    decision={
        "status":"STOP_BEFORE_COLORADO" if equivalent else "PASS_TO_COLORADO",
        "scientifically_interpretable":True,
        "mathematically_nonredundant":not equivalent,
        "tail_membership_changes_across_400_sample_pairs":membership_changes,
        "comparison":comparison,
        "collapse":collapse,
        "answers":{
            "tail_membership":"unchanged" if not membership_changes else "changed",
            "cold_synchrony":"unchanged to floating precision" if equivalent else "changed",
            "hot_synchrony":"unchanged to floating precision" if equivalent else "changed",
            "delta":"unchanged to floating precision" if equivalent else "changed",
            "cause":"current per-series local median tails plus Spearman already provide the same monotone-rank invariance on complete shared support",
            "behaving_as_intended":True,
            "redundant_with_current_implementation":equivalent,
        },
        "colorado_run":{
            "performed":False if equivalent else None,
            "reason":"mandatory stop gate: statewide rank-labelled rasters would duplicate the completed baseline" if equivalent else "gate passed",
            "existing_baseline_preserved":str(COLORADO_BASELINE.relative_to(ROOT)),
        },
        "spatial_rank_warning":"within-neighborhood rank medians are approximately 0.5 by construction; no spatial-rank map was created",
    }
    _json(OUTPUT/"decision_gate.json",decision)
    with (OUTPUT/"summary.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=("scope","metric","old","rank","difference","pearson","spearman","rmse","difference_iqr"))
        writer.writeheader()
        for metric in ("cold","hot","delta"):
            writer.writerow({"scope":"one_pair","metric":metric,"old":pair["old_delta"] if metric=="delta" else pair["tails"][metric]["old_synchrony"],"rank":pair["rank_delta"] if metric=="delta" else pair["tails"][metric]["rank_synchrony"],"difference":pair["delta_difference"] if metric=="delta" else pair["tails"][metric]["difference"]})
            writer.writerow({"scope":"sample_grid_collapsed","metric":metric,"old":collapse["old"][metric],"rank":collapse["rank"][metric],"difference":collapse["difference"][metric]})
            writer.writerow({"scope":"sample_grid_pairs","metric":metric,"difference":comparison[metric]["median_difference"],"pearson":comparison[metric]["pearson"],"spearman":comparison[metric]["spearman"],"rmse":comparison[metric]["rmse"],"difference_iqr":comparison[metric]["difference_iqr"]})
    provenance={
        "real_observations":True,"source":sample.attrs.get("source"),"source_provider":sample.attrs.get("source_provider"),
        "input":str(SAMPLE_INPUT.relative_to(ROOT)),"input_sha256":sha256(SAMPLE_INPUT.read_bytes()).hexdigest(),
        "existing_stack":str(SAMPLE_STACK.relative_to(ROOT)),"existing_stack_fingerprint":stack.attrs["analysis_fingerprint"],
        "dates":[str(sample.time.values[0]),str(sample.time.values[-1])],"time_observations":sample.sizes["time"],
        "missing_tmin":int(sample.tmin.isnull().sum()),"missing_tmax":int(sample.tmax.isnull().sum()),
        "rank_convention":"average_rank / (n + 1)","tail_probability":Q,"cold_inequality":"U <= quantile(U, 0.5)","hot_inequality":"U > quantile(U, 0.5)",
        "dependence_statistic":"unchanged Spearman after tail selection","temporal_reference":"same 90-day inclusive window as current baseline",
        "figures":figures,"runtime_seconds":time.perf_counter()-started,"network_bytes":0,"failures":0,"retries":0,
        "reproduction_command":"MPLCONFIGDIR=/tmp/cubedynamics-mpl .venv/bin/python scripts/run_rank_rescaling_gate.py",
    }
    _json(OUTPUT/"provenance.json",provenance)
    (OUTPUT/"REPRODUCE.md").write_text("# Reproduce the rank-rescaling decision gate\n\n```bash\nMPLCONFIGDIR=/tmp/cubedynamics-mpl .venv/bin/python scripts/run_rank_rescaling_gate.py\n```\n\nThe script uses existing real PRISM checkpoints, performs no network access, and intentionally stops before Colorado when equivalence is established.\n",encoding="utf-8")
    print(json.dumps(decision,indent=2))


if __name__=="__main__":
    main()
