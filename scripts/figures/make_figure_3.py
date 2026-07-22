#!/usr/bin/env python3
"""Render Figure 3: major axes encode interpretable fire development."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from morphospace import fit_pca, geometry_columns, load_data, profiles_for_fire_ids, transect_examples
from statistics import compute_validation_bundle
from style import CHARCOAL, FIREBRICK, MORPH_BLUE, TALL_WIDTH, clean_axis, panel_label, save_figure, set_style
from vase_glyphs import draw_area_history, draw_vase


GROUPS = {
    "scale": ["log_final_area", "log_peak_growth"],
    "duration": ["log_duration", "observation_count"],
    "timing": ["peak_timing", "front_loaded", "late_growth"],
    "persistence": ["slenderness", "developmental_velocity"],
    "pulse": ["pulse_count", "reactivation"],
    "entropy": ["growth_entropy"],
    "taper": ["terminal_taper"],
    "profile": ["width_p", "growth_p"],
}


def _grouped_loading(loadings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group, keys in GROUPS.items():
        cols = [idx for idx in loadings.index if any(key in idx for key in keys)]
        for pc in ["PC1", "PC2", "PC3"]:
            rows.append({"group": group, "pc": pc, "contribution": float(np.sum(loadings.loc[cols, pc].to_numpy(float) ** 2)) if cols else 0.0})
    return pd.DataFrame(rows)


def _independent_gradients(features: pd.DataFrame) -> pd.DataFrame:
    raw = features.copy()
    raw["temporal_gini_proxy"] = 1.0 - raw["growth_entropy"].astype(float)
    raw["active_day_proxy"] = raw["observation_count"].astype(float)
    raw["burstiness_proxy"] = raw["pulse_count"].astype(float) + raw["reactivation_count"].astype(float)
    raw["late_allocation_proxy"] = raw["late_growth_fraction"].astype(float)
    metric_labels = {
        "temporal_gini_proxy": "growth concentrated\nin few days",
        "active_day_proxy": "active days",
        "burstiness_proxy": "growth pulses",
        "late_allocation_proxy": "late growth share",
    }
    cols = ["temporal_gini_proxy", "active_day_proxy", "burstiness_proxy", "late_allocation_proxy", "duration_days", "final_area_km2", "observation_count"]
    rows = []
    for pc in ["morph_pc1", "morph_pc2", "morph_pc3"]:
        for metric in cols[:4]:
            sub = raw[[pc, metric, "duration_days", "final_area_km2", "observation_count"]].replace([np.inf, -np.inf], np.nan).dropna()
            y = sub[pc].to_numpy(float)
            x = sub[[metric, "duration_days", "final_area_km2", "observation_count"]].to_numpy(float)
            x = (x - x.mean(axis=0)) / np.where(x.std(axis=0) == 0, 1, x.std(axis=0))
            coef = np.linalg.pinv(np.c_[np.ones(len(x)), x]).dot(y)
            pred = np.c_[np.ones(len(x)), x].dot(coef)
            ss_res = float(np.sum((y - pred) ** 2))
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            rows.append({"pc": pc.replace("morph_pc", "Gradient "), "metric": metric_labels[metric], "adjusted_r2_proxy": 1 - ss_res / ss_tot if ss_tot > 0 else np.nan})
    return pd.DataFrame(rows)


def _axis_panel(fig, data, pc: str, label: str, y0: float, features: pd.DataFrame):
    rows = transect_examples(features, pc, bins=5, eligible=features["duration_days"] >= 2).reset_index(drop=True)
    profiles = profiles_for_fire_ids(data["slices"], rows["fire_id"].astype(str).tolist())
    fig.text(0.075, y0 + 0.145, label, fontsize=8.6, fontweight="bold", color=CHARCOAL)
    for i, row in rows.iterrows():
        x0 = 0.14 + i * 0.085
        vase_ax = fig.add_axes([x0, y0 + 0.055, 0.044, 0.095])
        hist_ax = fig.add_axes([x0 - 0.004, y0, 0.052, 0.035])
        draw_vase(vase_ax, profiles[row["fire_id"]], color=MORPH_BLUE, linewidth=0.25)
        draw_area_history(hist_ax, profiles[row["fire_id"]], color=MORPH_BLUE)
        fig.text(x0 + 0.022, y0 - 0.018, f"{row[pc]:.1f}", ha="center", va="top", fontsize=6.8)
    fig.text(0.14, y0 - 0.041, "low score", fontsize=7.0, color="#555555")
    fig.text(0.52, y0 - 0.041, "high score", fontsize=7.0, color="#555555", ha="right")


def build(data=None, stats=None):
    set_style()
    data = load_data() if data is None else data
    stats = compute_validation_bundle(data) if stats is None else stats
    features = data["features"]
    columns = geometry_columns(features, data["loadings"])
    pca = fit_pca(features, columns, n_components=5)
    grouped = _grouped_loading(pca.loadings)
    gradients = _independent_gradients(features)

    fig = plt.figure(figsize=(7.1, 7.2))
    fig.text(0.025, 0.880, "A", fontsize=12, fontweight="bold", color=CHARCOAL)
    _axis_panel(fig, data, "morph_pc1", "Gradient 1: growth allocation and concentration", 0.700, features)
    fig.text(0.025, 0.650, "B", fontsize=12, fontweight="bold", color=CHARCOAL)
    _axis_panel(fig, data, "morph_pc2", "Gradient 2: taper, duration, late growth, and scale", 0.470, features)
    fig.text(0.025, 0.420, "C", fontsize=12, fontweight="bold", color=CHARCOAL)
    _axis_panel(fig, data, "morph_pc3", "Gradient 3: pulses and timing structure", 0.240, features)

    ax_d = fig.add_axes([0.64, 0.56, 0.30, 0.30])
    pivot = grouped.pivot(index="group", columns="pc", values="contribution").loc[list(GROUPS.keys())]
    im = ax_d.imshow(pivot.to_numpy(float), cmap="Blues", aspect="auto", vmin=0)
    ax_d.set_xticks(range(3), ["Gradient 1", "Gradient 2", "Gradient 3"])
    ax_d.set_yticks(range(len(pivot)), pivot.index)
    ax_d.tick_params(labelsize=7.5)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            ax_d.text(j, i, f"{pivot.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7, color=CHARCOAL)
    panel_label(ax_d, "D")
    cbar = fig.colorbar(im, ax=ax_d, fraction=0.045)
    cbar.set_label("Feature contribution to axis", fontsize=7.5)
    cbar.ax.tick_params(labelsize=7)

    ax_e = fig.add_axes([0.64, 0.13, 0.30, 0.27])
    show = gradients.pivot(index="metric", columns="pc", values="adjusted_r2_proxy")
    x = np.arange(len(show.index))
    width = 0.24
    for j, pc in enumerate(show.columns):
        ax_e.bar(x + (j - 1) * width, show[pc], width=width, label=pc, color=[MORPH_BLUE, FIREBRICK, "#7b5bbd"][j])
    ax_e.set_xticks(x, show.index, rotation=25, ha="right")
    ax_e.set_ylabel("Adjusted fit to axis score")
    ax_e.legend(frameon=False, ncol=3, loc="upper right", fontsize=6.8)
    clean_axis(ax_e)
    panel_label(ax_e, "E")

    return fig


def main() -> int:
    fig = build()
    save_figure(fig, "Figure_3")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
