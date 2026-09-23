"""Create a standalone observed-PRISM map of center-reference Delta S.

Each map cell is ``S_cold - S_warm`` for that pixel versus the same center
reference pixel. The calculation calls the public CubeDynamics verb; this file
only selects one rolling-window output and renders it.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.utils.reference import center_pixel_indices


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    REPO_ROOT
    / "artifacts"
    / "center-pixel-synchrony-walkthrough"
    / "intermediate"
    / "prism_boulder_2023-11-01_2024-01-30.nc"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "center-pixel-synchrony-walkthrough"
FOCAL_COORD = (39.875, -105.75)


def coordinate_index(values: np.ndarray, target: float) -> int:
    return int(np.argmin(np.abs(np.asarray(values, dtype=float) - target)))


def build_delta_s_map(input_path: Path, *, output_time: str | None = None) -> xr.DataArray:
    """Calculate one Delta-S map with the production center-pixel recipe."""

    with xr.open_dataset(input_path, engine="scipy") as source:
        temperature = source[["tmin", "tmax"]].load()
    if bool(temperature.attrs.get("is_synthetic", True)):
        raise RuntimeError("Refusing synthetic input; an observed PRISM cube is required")

    end = (
        np.datetime64(output_time)
        if output_time is not None
        else temperature["time"].values[-1]
    )
    synchrony = (
        pipe(temperature)
        | v.rolling_median_split_synchrony(
            lower_var="tmin",
            upper_var="tmax",
            window_days=90,
            min_t=10,
            split_quantile=0.5,
            output_stride=30,
            output_times=[end],
        )
    ).unwrap().compute()
    if synchrony.sizes.get("time_window_end", 0) != 1:
        raise RuntimeError(f"No valid rolling-window output was produced for {end}")

    delta = synchrony["bottom_minus_top"].isel(time_window_end=0, drop=True)
    delta.attrs.update(
        {
            "long_name": "Cold minus warm Spearman synchrony vs center",
            "window_end": str(np.datetime_as_string(end, unit="D")),
            "window_days": 90,
            "minimum_observations_per_tail": 10,
            "split_quantile": 0.5,
            "reference": "center_pixel",
        }
    )
    return delta


def render_map(delta: xr.DataArray, output_path: Path, *, limit: float | None = None) -> None:
    """Render a zero-centered pixel map and mark center and example pixels."""

    center_y, center_x = center_pixel_indices(delta)
    focal_y = coordinate_index(delta["y"].values, FOCAL_COORD[0])
    focal_x = coordinate_index(delta["x"].values, FOCAL_COORD[1])
    finite = np.asarray(delta.values)[np.isfinite(delta.values)]
    if not finite.size:
        raise RuntimeError("Delta-S map has no finite pixels")
    color_limit = float(limit) if limit is not None else float(np.nanmax(np.abs(finite)))
    color_limit = max(color_limit, 0.01)

    fig, ax = plt.subplots(figsize=(9.6, 8.2), facecolor="#F7F5EF")
    ax.set_facecolor("white")
    mesh = ax.pcolormesh(
        delta["x"].values,
        delta["y"].values,
        delta.values,
        cmap="RdBu",
        norm=TwoSlopeNorm(vmin=-color_limit, vcenter=0.0, vmax=color_limit),
        shading="nearest",
        rasterized=True,
    )
    center_lat = float(delta["y"].values[center_y])
    center_lon = float(delta["x"].values[center_x])
    focal_lat = float(delta["y"].values[focal_y])
    focal_lon = float(delta["x"].values[focal_x])
    focal_value = float(delta.isel(y=focal_y, x=focal_x))
    ax.scatter(
        center_lon,
        center_lat,
        marker="*",
        s=280,
        color="#F2B134",
        edgecolor="#183044",
        linewidth=1.4,
        zorder=5,
        label="center reference",
    )
    ax.scatter(
        focal_lon,
        focal_lat,
        marker="D",
        s=95,
        color="#B23A67",
        edgecolor="white",
        linewidth=1.1,
        zorder=5,
        label=f"example focal pixel (Delta S = {focal_value:.3f})",
    )
    ax.annotate(
        "center",
        (center_lon, center_lat),
        xytext=(9, 8),
        textcoords="offset points",
        color="#183044",
        fontsize=11,
        weight="bold",
    )
    ax.annotate(
        f"focal\n{focal_value:.3f}",
        (focal_lon, focal_lat),
        xytext=(9, -22),
        textcoords="offset points",
        color="#B23A67",
        fontsize=10,
        weight="bold",
    )
    colorbar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.035)
    colorbar.set_label("Delta S = S_cold - S_warm", fontsize=12)
    ax.set(
        title=(
            "Center-reference climate-tail synchrony\n"
            f"Observed PRISM | 90-day span ending {delta.attrs['window_end']}"
        ),
        xlabel="longitude",
        ylabel="latitude",
    )
    ax.legend(frameon=False, loc="lower right", fontsize=10)
    ax.text(
        0.0,
        -0.12,
        "Red: stronger warm synchrony (Delta S < 0)    |    "
        "Blue: stronger cold synchrony (Delta S > 0)",
        transform=ax.transAxes,
        fontsize=10.5,
        color="#405565",
    )
    ax.text(
        0.0,
        -0.17,
        "Every pixel is compared with the same center pixel; each series uses its own median.",
        transform=ax.transAxes,
        fontsize=10.5,
        color="#405565",
    )
    fig.tight_layout(rect=(0.02, 0.06, 0.98, 0.98))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-time", help="Rolling-window end date; defaults to final input date")
    parser.add_argument("--limit", type=float, help="Optional symmetric color limit")
    args = parser.parse_args()

    delta = build_delta_s_map(args.input.resolve(), output_time=args.output_time)
    date_label = delta.attrs["window_end"]
    output_dir = args.output_dir.resolve()
    png_path = output_dir / f"delta_s_map_{date_label}.png"
    nc_path = output_dir / "intermediate" / f"delta_s_map_{date_label}.nc"
    render_map(delta, png_path, limit=args.limit)
    delta.to_dataset(name="delta_s").to_netcdf(nc_path, engine="scipy")
    print(f"map: {png_path}")
    print(f"data: {nc_path}")
    print(
        "range: [{:.6f}, {:.6f}] | finite pixels: {}/{}".format(
            float(delta.min()),
            float(delta.max()),
            int(np.isfinite(delta.values).sum()),
            delta.size,
        )
    )


if __name__ == "__main__":
    main()
