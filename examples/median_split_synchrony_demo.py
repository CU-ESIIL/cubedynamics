"""Run a small, offline median-split climate synchrony example."""

from __future__ import annotations

import argparse
from pathlib import Path

import dask.array as da
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.viz.qa_plots import plot_tail_dependence_over_time


def synthetic_prism_temperature() -> xr.Dataset:
    """Create deterministic, Dask-backed PRISM-like tmin/tmax cubes."""

    rng = np.random.default_rng(12)
    time = np.datetime64("2024-01-01") + np.arange(24).astype("timedelta64[D]")
    y = np.linspace(39.5, 40.5, 4)
    x = np.linspace(-105.75, -104.75, 5)
    cold_signal = np.linspace(-12.0, 3.0, time.size)
    hot_signal = np.linspace(8.0, 29.0, time.size)
    tmin = np.empty((time.size, y.size, x.size), dtype=np.float32)
    tmax = np.empty_like(tmin)

    for yi in range(y.size):
        for xi in range(x.size):
            offset = yi * 0.4 - xi * 0.2
            tmin[:, yi, xi] = cold_signal + offset + rng.normal(0.0, 0.25, time.size)
            tmax[:, yi, xi] = hot_signal + offset + rng.normal(0.0, 0.75, time.size)

    chunks = (8, 2, 3)
    coords = {"time": time, "y": y, "x": x}
    return xr.Dataset(
        {
            "tmin": xr.DataArray(
                da.from_array(tmin, chunks=chunks),
                dims=("time", "y", "x"),
                coords=coords,
                attrs={"units": "degC", "source": "synthetic-prism"},
            ),
            "tmax": xr.DataArray(
                da.from_array(tmax, chunks=chunks),
                dims=("time", "y", "x"),
                coords=coords,
                attrs={"units": "degC", "source": "synthetic-prism"},
            ),
        }
    )


def render_plots(synchrony: xr.Dataset, output_dir: Path) -> None:
    """Write a flat time-series plot and interactive cube viewer."""

    output_dir.mkdir(parents=True, exist_ok=True)
    flat_path = output_dir / "median_split_synchrony_timeseries.png"
    cube_path = output_dir / "median_split_synchrony_cube.html"
    diagnostic_path = output_dir / "median_split_synchrony_diagnostic.png"

    fig, ax = plt.subplots(figsize=(10, 4))
    plot_tail_dependence_over_time(
        synchrony["bottom_synchrony"],
        synchrony["top_synchrony"],
        synchrony["bottom_minus_top"],
        ax=ax,
        title="Median climate synchrony through time",
        ylabel="Spatial median Spearman synchrony",
        labels=("below-median tmin", "above-median tmax", "cold - hot"),
    )
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    fig.tight_layout()
    fig.savefig(flat_path, dpi=160)
    plt.close(fig)

    cube = (
        pipe(synchrony["bottom_minus_top"].clip(-2, 2))
        | v.plot(
            title="Cold minus hot climate synchrony",
            cmap="RdBu_r",
            clim=(-2, 2),
            thin_time_factor=1,
        )
    ).unwrap()
    cube.save(str(cube_path))
    diagnostic = v.diagnostic_panel(
        synchrony,
        title="Median split climate synchrony diagnostic",
        output_path=diagnostic_path,
        cmap="RdBu_r",
    )
    plt.close(diagnostic)
    print("flat plot:", flat_path)
    print("cube viewer:", cube_path)
    print("diagnostic panel:", diagnostic_path)


def main(output_dir: Path | None = None) -> None:
    temperature = synthetic_prism_temperature()
    synchrony = (
        pipe(temperature)
        | v.rolling_median_split_synchrony(
            lower_var="tmin",
            upper_var="tmax",
            window_days=20,
            min_t=5,
            split_quantile=0.5,
        )
    ).unwrap()

    assert all(variable.chunks is not None for variable in synchrony.data_vars.values())
    assert synchrony["bottom_synchrony"].attrs["source_variable"] == "tmin"
    assert synchrony["top_synchrony"].attrs["source_variable"] == "tmax"

    final_slice = synchrony.isel(time_window_end=-1).compute()
    center = final_slice.isel(y=temperature.sizes["y"] // 2, x=temperature.sizes["x"] // 2)
    np.testing.assert_allclose(center["bottom_synchrony"], 1.0)
    np.testing.assert_allclose(center["top_synchrony"], 1.0)
    np.testing.assert_allclose(center["bottom_minus_top"], 0.0, atol=1e-7)

    spatial_median = final_slice.median(dim=("y", "x"), skipna=True)
    print("input chunks:", temperature["tmin"].chunks)
    print("output variables:", list(synchrony.data_vars))
    print("output dims:", dict(synchrony.sizes))
    print("final spatial medians:")
    for name, value in spatial_median.data_vars.items():
        print(f"  {name}: {float(value):.4f}")
    if output_dir is not None:
        render_plots(synchrony, output_dir)
    print("mini-container synchrony example passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    main(args.output_dir)
