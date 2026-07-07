"""Stream the full PRISM temperature record and calculate climate synchrony."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import time

import dask
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.viz.qa_plots import plot_tail_dependence_over_time


DEFAULT_BBOX = (-105.75, 39.50, -104.75, 40.50)
WINDOW_DAYS = 90
MIN_T = 10
STREAM_CHUNKS = {"time": 31, "y": 64, "x": 64}
PRISM_GRID_STEP_DEGREES = 1.0 / 24.0


def last_complete_year() -> str:
    return str(date.today().replace(month=1, day=1) - timedelta(days=1))


def render_outputs(synchrony, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 4.5))
    plot_tail_dependence_over_time(
        synchrony["bottom_synchrony"],
        synchrony["top_synchrony"],
        synchrony["bottom_minus_top"],
        ax=ax,
        title="PRISM 4 km climate synchrony through the full record",
        ylabel="Spatial median Spearman synchrony",
        labels=("below-median tmin", "above-median tmax", "cold - hot"),
    )
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    fig.tight_layout()
    fig.savefig(output_dir / "real_prism_synchrony_timeseries.png", dpi=160)
    plt.close(fig)

    viewer = (
        pipe(synchrony["bottom_minus_top"].clip(-2, 2))
        | v.plot(
            title="PRISM 4 km cold minus hot synchrony",
            cmap="RdBu_r",
            clim=(-2, 2),
            thin_time_factor=1,
        )
    ).unwrap()
    viewer.save(str(output_dir / "real_prism_synchrony_cube.html"))
    synchrony.to_netcdf(output_dir / "real_prism_synchrony.nc", engine="scipy")


def _load_temperature(start: str, end: str, bbox: tuple[float, float, float, float]):
    return cd.load_prism_cube(
        variables=["tmin", "tmax"],
        start=start,
        end=end,
        bbox=bbox,
        freq="D",
        chunks=STREAM_CHUNKS,
        prefer_streaming=True,
        show_progress=False,
        allow_synthetic=False,
    )


def _iter_batches(values: pd.DatetimeIndex, batch_size: int):
    for start_idx in range(0, len(values), batch_size):
        yield values[start_idx : start_idx + batch_size]


def _normalize_piece_coords(piece: xr.Dataset) -> xr.Dataset:
    coords = {}
    for dim in ("y", "x"):
        if dim in piece.coords:
            values = piece[dim].values.astype("float64")
            coords[dim] = np.round(
                np.round(values / PRISM_GRID_STEP_DEGREES) * PRISM_GRID_STEP_DEGREES,
                6,
            )
    if coords:
        piece = piece.assign_coords(coords)
    return piece


def compute_synchrony_batches(
    *,
    output_dir: Path,
    start: str,
    end: str,
    bbox: tuple[float, float, float, float],
    output_stride: int,
    output_batch_size: int,
    workers: int,
):
    if output_batch_size < 1:
        raise ValueError("output_batch_size must be at least 1")

    record_times = pd.date_range(start, end, freq="D")
    target_times = record_times[::output_stride]
    if not len(target_times):
        raise ValueError("No output times available for the requested range")

    checkpoint_dir = output_dir / "batches"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    pieces = []
    source_attrs = {}
    input_shape = {"time": len(record_times)}
    record_start = pd.Timestamp(start)

    for batch_index, batch_times in enumerate(
        _iter_batches(target_times, output_batch_size), start=1
    ):
        checkpoint_path = checkpoint_dir / f"synchrony_batch_{batch_index:03d}.nc"
        if checkpoint_path.exists():
            with xr.open_dataset(checkpoint_path, engine="scipy") as saved:
                piece = _normalize_piece_coords(saved.load())
            pieces.append(piece)
            if not source_attrs:
                source_attrs = {
                    key: piece.attrs[key]
                    for key in (
                        "source",
                        "source_provider",
                        "streaming_service",
                        "streaming_protocol",
                        "is_synthetic",
                    )
                    if key in piece.attrs
                }
                input_shape.update(
                    {
                        "y": piece.sizes.get("y"),
                        "x": piece.sizes.get("x"),
                    }
                )
            print(
                "loaded checkpoint batch {0}: {1} to {2} ({3} outputs)".format(
                    batch_index,
                    batch_times[0].date(),
                    batch_times[-1].date(),
                    piece.sizes.get("time_window_end", 0),
                ),
                flush=True,
            )
            continue

        subset_start = max(
            record_start,
            pd.Timestamp(batch_times[0]) - pd.Timedelta(days=WINDOW_DAYS),
        )
        subset_end = pd.Timestamp(batch_times[-1])
        temperature = _load_temperature(
            subset_start.strftime("%Y-%m-%d"),
            subset_end.strftime("%Y-%m-%d"),
            bbox,
        )
        if temperature.attrs.get("is_synthetic") is not False:
            raise RuntimeError("Refusing to run without verified real-data provenance")
        if not source_attrs:
            source_attrs = dict(temperature.attrs)
            input_shape.update(
                {
                    "y": temperature.sizes.get("y"),
                    "x": temperature.sizes.get("x"),
                }
            )

        lazy_piece = (
            pipe(temperature)
            | v.rolling_median_split_synchrony(
                lower_var="tmin",
                upper_var="tmax",
                window_days=WINDOW_DAYS,
                min_t=MIN_T,
                split_quantile=0.5,
                output_stride=output_stride,
                output_times=batch_times,
            )
        ).unwrap()

        with dask.config.set(scheduler="threads", num_workers=workers):
            piece = _normalize_piece_coords(lazy_piece.compute())
        if piece.sizes.get("time_window_end", 0):
            piece.attrs.update(source_attrs)
            piece.to_netcdf(checkpoint_path, engine="scipy")
            pieces.append(piece)
        print(
            "computed batch {0}: {1} to {2} ({3} outputs)".format(
                batch_index,
                batch_times[0].date(),
                batch_times[-1].date(),
                piece.sizes.get("time_window_end", 0),
            ),
            flush=True,
        )

    if not pieces:
        raise RuntimeError("No synchrony outputs were produced")

    synchrony = xr.concat(pieces, dim="time_window_end", join="outer")
    if "y" in synchrony.coords:
        synchrony = synchrony.sortby("y", ascending=False)
    if "x" in synchrony.coords:
        synchrony = synchrony.sortby("x")
    input_shape.update(
        {
            "y": synchrony.sizes.get("y"),
            "x": synchrony.sizes.get("x"),
        }
    )
    return synchrony, source_attrs, input_shape


def main(
    output_dir: Path,
    *,
    start: str,
    end: str,
    bbox: tuple[float, float, float, float],
    output_stride: int,
    output_batch_size: int,
    workers: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    synchrony, source_attrs, input_shape = compute_synchrony_batches(
        output_dir=output_dir,
        start=start,
        end=end,
        bbox=bbox,
        output_stride=output_stride,
        output_batch_size=output_batch_size,
        workers=workers,
    )
    synchrony.attrs.update(source_attrs)
    synchrony.attrs.update(
        {
            "analysis": "rolling_median_split_synchrony",
            "window_days": WINDOW_DAYS,
            "output_stride": output_stride,
            "output_batch_size": output_batch_size,
            "requested_bbox": bbox,
        }
    )
    render_outputs(synchrony, output_dir)

    manifest_path = output_dir / "real_prism_manifest.json"
    elapsed_minutes = round((time.monotonic() - started) / 60, 2)
    if manifest_path.exists():
        try:
            previous_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            elapsed_minutes = max(
                elapsed_minutes,
                float(previous_manifest.get("elapsed_minutes", 0.0)),
            )
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass

    manifest = {
        "source": source_attrs.get("source"),
        "streaming_service": source_attrs.get("streaming_service"),
        "streaming_protocol": source_attrs.get("streaming_protocol"),
        "is_synthetic": False,
        "start": start,
        "end": end,
        "bbox": bbox,
        "input_shape": input_shape,
        "output_shape": dict(synchrony.sizes),
        "window_days": WINDOW_DAYS,
        "output_stride": output_stride,
        "output_batch_size": output_batch_size,
        "elapsed_minutes": elapsed_minutes,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    final = synchrony.isel(time_window_end=-1).median(("y", "x"), skipna=True)
    print(json.dumps(manifest, indent=2))
    print("final spatial medians:")
    for name, value in final.data_vars.items():
        print(f"  {name}: {float(value):.4f}")
    print("real PRISM streamed full-record run passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start", default="1981-01-01")
    parser.add_argument("--end", default=last_complete_year())
    parser.add_argument("--bbox", nargs=4, type=float, default=DEFAULT_BBOX)
    parser.add_argument(
        "--output-stride",
        type=int,
        default=30,
        help="Evaluate every Nth daily timestamp (30 is approximately monthly)",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--output-batch-size",
        type=int,
        default=24,
        help="Number of rolling window outputs to compute per streamed batch",
    )
    args = parser.parse_args()
    main(
        args.output_dir,
        start=args.start,
        end=args.end,
        bbox=tuple(args.bbox),
        output_stride=args.output_stride,
        output_batch_size=args.output_batch_size,
        workers=args.workers,
    )
