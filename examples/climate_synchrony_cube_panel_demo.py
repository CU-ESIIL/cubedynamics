"""Create a small interactive panel of climate synchrony cubes for docs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.plotting.cube_plot import CubePlot, ScaleFillContinuous


def _synthetic_temperature_block(seed: int, *, cold_shift: float, hot_shift: float) -> xr.Dataset:
    rng = np.random.default_rng(seed)
    time = np.datetime64("2024-01-01") + np.arange(28).astype("timedelta64[D]")
    y = np.linspace(39.45, 40.45, 5)
    x = np.linspace(-105.75, -104.75, 6)
    cold_signal = np.sin(np.linspace(0.0, 2.7 * np.pi, time.size)) * 5.0 - 4.0
    hot_signal = np.cos(np.linspace(0.0, 2.2 * np.pi, time.size)) * 7.0 + 18.0
    tmin = np.empty((time.size, y.size, x.size), dtype=np.float32)
    tmax = np.empty_like(tmin)

    for yi in range(y.size):
        for xi in range(x.size):
            gradient = yi * 0.35 - xi * 0.18
            local = np.sin((yi + 1) * 0.7 + (xi + 1) * 0.4)
            tmin[:, yi, xi] = (
                cold_signal
                + cold_shift * local
                + gradient
                + rng.normal(0.0, 0.35, time.size)
            )
            tmax[:, yi, xi] = (
                hot_signal
                + hot_shift * local
                + gradient
                + rng.normal(0.0, 0.85, time.size)
            )

    coords = {"time": time, "y": y, "x": x}
    return xr.Dataset(
        {
            "tmin": xr.DataArray(tmin, dims=("time", "y", "x"), coords=coords, attrs={"units": "degC"}),
            "tmax": xr.DataArray(tmax, dims=("time", "y", "x"), coords=coords, attrs={"units": "degC"}),
        },
        attrs={"source": "synthetic docs example"},
    )


def build_panel_cube() -> xr.DataArray:
    """Return a facetable cube with one cold-minus-hot synchrony cube per block."""

    blocks = {
        "Front Range": _synthetic_temperature_block(14, cold_shift=0.5, hot_shift=1.8),
        "San Juans": _synthetic_temperature_block(28, cold_shift=1.6, hot_shift=0.7),
        "High Plains": _synthetic_temperature_block(42, cold_shift=1.0, hot_shift=1.0),
    }
    cubes = []
    for label, temperature in blocks.items():
        synchrony = (
            pipe(temperature)
            | v.rolling_median_split_synchrony(
                lower_var="tmin",
                upper_var="tmax",
                window_days=18,
                min_t=5,
                split_quantile=0.5,
                output_stride=2,
            )
        ).unwrap()
        cube = synchrony["bottom_minus_top"].clip(-2, 2)
        cube.name = "cold_minus_hot_synchrony"
        cubes.append(cube)

    panel_cube = xr.concat(cubes, dim=xr.IndexVariable("block", list(blocks)))
    panel_cube.attrs.update(
        {
            "description": "Cold-minus-hot median-split synchrony for multiple climate blocks",
            "units": "Spearman rho difference",
        }
    )
    return panel_cube


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the docs climate synchrony cube panel sample.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/assets/figures/climate_synchrony_cube_panel.html"),
        help="HTML path for the interactive cube panel.",
    )
    args = parser.parse_args()

    panel_cube = build_panel_cube()
    plot = CubePlot(
        panel_cube,
        title="Climate synchrony cube panel",
        time_dim="time_window_end",
        thin_time_factor=1,
        show_progress=False,
        fill_scale=ScaleFillContinuous(
            cmap="RdBu_r",
            palette="diverging",
            limits=(-2.0, 2.0),
            center=0.0,
            name="cold - hot synchrony",
        ),
    ).facet_wrap("block", ncol=3)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    plot.save(str(args.output))
    print(args.output)


if __name__ == "__main__":
    main()
