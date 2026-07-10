"""Generate website assets for the dedicated synchrony documentation section."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.plotting.cube_plot import CubePlot, ScaleFillContinuous


def synthetic_event_temperature() -> xr.DataArray:
    """Create a deterministic climate cube with shared, lagged, and local events."""

    rng = np.random.default_rng(84)
    time = np.datetime64("2024-07-01") + np.arange(44).astype("timedelta64[D]")
    y = np.linspace(39.6, 40.4, 4)
    x = np.linspace(-105.7, -104.9, 5)
    data = np.full((time.size, y.size, x.size), 28.0, dtype=np.float32)
    seasonal = 2.5 * np.sin(np.linspace(0, 2.8 * np.pi, time.size))

    anchors = np.array([5, 17, 31])
    for yi in range(y.size):
        for xi in range(x.size):
            distance = np.sqrt((yi - 1.2) ** 2 + (xi - 2.0) ** 2)
            lag = int(round((xi - 2) * 0.8 + (yi - 1) * 0.4))
            local_duration = 2 + ((yi + xi) % 3)
            local_amp = 8.5 - 0.65 * distance + 0.25 * yi
            series = 28.0 + seasonal + rng.normal(0.0, 0.35, time.size)
            for event_index, anchor in enumerate(anchors):
                start = max(anchor + lag, 0)
                duration = max(2, local_duration + (event_index % 2))
                stop = min(start + duration, time.size)
                series[start:stop] += local_amp + event_index * 0.9
            data[:, yi, xi] = series

    return xr.DataArray(
        data,
        dims=("time", "y", "x"),
        coords={"time": time, "y": y, "x": x},
        name="tmax",
        attrs={"units": "degC", "source": "synthetic synchrony docs"},
    )


def build_outputs(cube: xr.DataArray):
    """Run state, event, synchrony, and coupling verbs for the docs assets."""

    hot = (pipe(cube) | v.threshold_state(threshold=35.0, direction="above")).unwrap()
    events = (pipe(hot) | v.detect_events(min_duration=2, max_gap=0)).unwrap()
    occurrence = (
        pipe(hot)
        | v.occurrence_synchrony(
            spatial_mode="neighbors",
            radius_km=125,
            method="jaccard",
            window="14D",
            stride="4D",
        )
    ).unwrap()
    severity = (
        pipe(hot)
        | v.severity_synchrony(
            spatial_mode="neighbors",
            radius_km=125,
            min_joint_events=2,
            window="14D",
            stride="4D",
        )
    ).unwrap()
    timing = (
        pipe(events)
        | v.timing_synchrony(
            spatial_mode="neighbors",
            radius_km=125,
            match_tolerance="5D",
        )
    ).unwrap()
    duration = (
        pipe(events)
        | v.duration_synchrony(
            spatial_mode="neighbors",
            radius_km=125,
            match_tolerance="5D",
            min_matched_events=2,
        )
    ).unwrap()
    boom = _synthetic_biological_response(cube, hot)
    coupling = (
        pipe(hot)
        | v.sync_with(
            boom,
            synchrony="occurrence",
            spatial_relation="same_pixel",
            lags=["0D", "2D", "4D", "6D", "8D"],
        )
    ).unwrap()
    return hot, events, occurrence, severity, timing, duration, boom, coupling


def _synthetic_biological_response(cube: xr.DataArray, hot: xr.Dataset) -> xr.Dataset:
    """Make a lagged response cube that follows hot-state events."""

    response = hot["state"].shift(time=4, fill_value=False).rename("response_state")
    response.attrs.update(
        {
            "units": "presence",
            "source": "synthetic biology response lagged four days after hot states",
        }
    )
    return (pipe(response) | v.binary_state(name="lagged_biological_response")).unwrap()


def write_interactive_assets(
    occurrence: xr.Dataset,
    severity: xr.Dataset,
    timing: xr.Dataset,
    duration: xr.Dataset,
    output_dir: Path,
) -> None:
    """Write interactive cube HTML files."""

    occurrence_cube = occurrence["occurrence_synchrony"].clip(0, 1)
    occurrence_cube.name = "occurrence_synchrony"
    occurrence_plot = pipe(occurrence_cube) | v.plot(
        title="Occurrence synchrony: shared hot-state histories",
        cmap="viridis",
        clim=(0, 1),
        thin_time_factor=1,
    )
    occurrence_plot.unwrap().save(str(output_dir / "synchrony_occurrence_cube.html"))

    severity_cube = severity["severity_synchrony"].clip(-1, 1)
    severity_cube.name = "severity_synchrony"
    severity_plot = pipe(severity_cube) | v.plot(
        title="Severity synchrony: magnitude co-variation",
        cmap="RdBu_r",
        clim=(-1, 1),
        thin_time_factor=1,
    )
    severity_plot.unwrap().save(str(output_dir / "synchrony_severity_cube.html"))

    timing_cube = timing["timing_synchrony"].clip(0, 1)
    timing_cube.name = "timing_synchrony"
    duration_cube = duration["duration_similarity"].clip(0, 1)
    duration_cube.name = "duration_similarity"
    event_panel = xr.concat(
        [timing_cube, duration_cube],
        dim=xr.IndexVariable("primitive", ["timing", "duration"]),
    )
    event_panel.attrs["units"] = "similarity"
    panel = CubePlot(
        event_panel,
        title="Event synchrony: timing and duration",
        time_dim="time_window_end",
        thin_time_factor=1,
        show_progress=False,
        fill_scale=ScaleFillContinuous(
            cmap="viridis",
            limits=(0.0, 1.0),
            name="event synchrony",
        ),
    ).facet_wrap("primitive", ncol=2)
    panel.save(str(output_dir / "synchrony_event_timing_duration_panel.html"))


def write_static_assets(
    occurrence: xr.Dataset,
    severity: xr.Dataset,
    timing: xr.Dataset,
    duration: xr.Dataset,
    coupling: xr.Dataset,
    output_dir: Path,
) -> None:
    """Write PNG plots for metric comparison and lagged coupling."""

    fig, ax = plt.subplots(figsize=(9, 4.8))
    for label, da in [
        ("occurrence", occurrence["occurrence_synchrony"]),
        ("severity", severity["severity_synchrony"]),
    ]:
        spatial_dims = [dim for dim in da.dims if dim != "time_window_end"]
        median = da.median(dim=spatial_dims, skipna=True)
        ax.plot(da["time_window_end"].values, median.values, marker="o", label=label)
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.5)
    ax.set_title("Spatial median synchrony through rolling windows")
    ax.set_xlabel("window end")
    ax.set_ylabel("synchrony score")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_dir / "synchrony_metric_comparison.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].imshow(
        timing["median_absolute_lag"].isel(time_window_end=0),
        origin="lower",
        cmap="magma_r",
        aspect="auto",
    )
    axes[0].set_title("median absolute lag")
    axes[0].set_xlabel("x")
    axes[0].set_ylabel("y")
    im = axes[1].imshow(
        duration["duration_similarity"].isel(time_window_end=0),
        origin="lower",
        cmap="viridis",
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    axes[1].set_title("duration similarity")
    axes[1].set_xlabel("x")
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.82, label="similarity")
    fig.suptitle("Matched-event diagnostics")
    fig.savefig(output_dir / "synchrony_event_diagnostics.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    median_lag = coupling["coupling_score"].median(dim=("y", "x"), skipna=True)
    ax.plot(coupling["lag"].values, median_lag.values, marker="o", color="#0b4f6c")
    ax.set_title("Climate-biology coupling by lag")
    ax.set_xlabel("biology lag")
    ax.set_ylabel("median same-pixel Jaccard score")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "synchrony_coupling_lag_curve.png", dpi=180)
    plt.close(fig)


def main(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    cube = synthetic_event_temperature()
    _, _, occurrence, severity, timing, duration, _, coupling = build_outputs(cube)
    write_interactive_assets(occurrence, severity, timing, duration, output_dir)
    write_static_assets(occurrence, severity, timing, duration, coupling, output_dir)
    print(f"wrote synchrony section assets to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/assets/figures"),
    )
    args = parser.parse_args()
    main(args.output_dir)
