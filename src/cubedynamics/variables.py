"""Semantic variable loaders for common climate and vegetation variables."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, Literal

import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.data.gridmet import load_gridmet_cube
from cubedynamics.data.prism import load_prism_cube
from cubedynamics.sentinel import (
    load_sentinel2_bands_cube,
    load_sentinel2_ndvi_cube,
    load_sentinel2_ndvi_zscore_cube,
)


TEMP_SOURCES: dict[str, dict[str, str]] = {
    "gridmet": {
        "mean": "tmmx",
        "min": "tmmn",
        "max": "tmmx",
    },
    "prism": {
        "mean": "tmean",
        "min": "tmin",
        "max": "tmax",
    },
}


def _resolve_temp_variable(source: str, kind: str) -> str:
    if source not in TEMP_SOURCES:
        raise ValueError(f"Unsupported temperature source '{source}'. Expected one of {sorted(TEMP_SOURCES)}")
    mapping = TEMP_SOURCES[source]
    if kind not in mapping:
        raise ValueError(
            f"Unsupported temperature kind '{kind}' for source '{source}'. Expected one of {sorted(mapping)}"
        )
    return mapping[kind]


def _load_temperature(
    *,
    kind: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    bbox: Optional[Sequence[float]] = None,
    aoi_geojson: Optional[Mapping[str, Any]] = None,
    start: Any = None,
    end: Any = None,
    source: Literal["gridmet", "prism"] = "gridmet",
    **kwargs: Any,
) -> xr.DataArray:
    var_name = _resolve_temp_variable(source, kind)
    if source == "gridmet":
        ds = load_gridmet_cube(
            variable=var_name,
            lat=lat,
            lon=lon,
            bbox=bbox,
            aoi_geojson=aoi_geojson,
            start=start,
            end=end,
            **kwargs,
        )
    else:
        ds = load_prism_cube(
            variable=var_name,
            lat=lat,
            lon=lon,
            bbox=bbox,
            aoi_geojson=aoi_geojson,
            start=start,
            end=end,
            **kwargs,
        )

    da = ds[var_name]
    da = da.copy()
    da.attrs.setdefault("variable", var_name)
    da.attrs.setdefault("source", source)
    return da


def temperature(
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    bbox: Optional[Sequence[float]] = None,
    aoi_geojson: Optional[Mapping[str, Any]] = None,
    start: Any = None,
    end: Any = None,
    source: Literal["gridmet", "prism"] = "gridmet",
    **kwargs: Any,
) -> xr.DataArray:
    """
    Load a mean temperature cube from the chosen climate provider.

    This is a semantic wrapper around ``load_gridmet_cube`` or ``load_prism_cube``.
    It forwards AOI, time, and additional keyword arguments directly to the
    underlying loader.
    """

    return _load_temperature(
        kind="mean",
        lat=lat,
        lon=lon,
        bbox=bbox,
        aoi_geojson=aoi_geojson,
        start=start,
        end=end,
        source=source,
        **kwargs,
    )


def temperature_min(
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    bbox: Optional[Sequence[float]] = None,
    aoi_geojson: Optional[Mapping[str, Any]] = None,
    start: Any = None,
    end: Any = None,
    source: Literal["gridmet", "prism"] = "gridmet",
    **kwargs: Any,
) -> xr.DataArray:
    """Load a minimum daily temperature cube from the selected source."""

    return _load_temperature(
        kind="min",
        lat=lat,
        lon=lon,
        bbox=bbox,
        aoi_geojson=aoi_geojson,
        start=start,
        end=end,
        source=source,
        **kwargs,
    )


def temperature_max(
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    bbox: Optional[Sequence[float]] = None,
    aoi_geojson: Optional[Mapping[str, Any]] = None,
    start: Any = None,
    end: Any = None,
    source: Literal["gridmet", "prism"] = "gridmet",
    **kwargs: Any,
) -> xr.DataArray:
    """Load a maximum daily temperature cube from the selected source."""

    return _load_temperature(
        kind="max",
        lat=lat,
        lon=lon,
        bbox=bbox,
        aoi_geojson=aoi_geojson,
        start=start,
        end=end,
        source=source,
        **kwargs,
    )


def temperature_anomaly(
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    bbox: Optional[Sequence[float]] = None,
    aoi_geojson: Optional[Mapping[str, Any]] = None,
    start: Any = None,
    end: Any = None,
    source: Literal["gridmet", "prism"] = "gridmet",
    kind: Literal["mean", "min", "max"] = "mean",
    baseline: Optional[xr.DataArray] = None,
    baseline_start: Any = None,
    baseline_end: Any = None,
    **kwargs: Any,
) -> xr.DataArray:
    """
    Compute a temperature anomaly cube along the time dimension.

    Uses the semantic temperature loaders and ``verbs.anomaly``.
    """

    if kind == "mean":
        temp_cube = temperature(
            lat=lat,
            lon=lon,
            bbox=bbox,
            aoi_geojson=aoi_geojson,
            start=start,
            end=end,
            source=source,
            **kwargs,
        )
    elif kind == "min":
        temp_cube = temperature_min(
            lat=lat,
            lon=lon,
            bbox=bbox,
            aoi_geojson=aoi_geojson,
            start=start,
            end=end,
            source=source,
            **kwargs,
        )
    elif kind == "max":
        temp_cube = temperature_max(
            lat=lat,
            lon=lon,
            bbox=bbox,
            aoi_geojson=aoi_geojson,
            start=start,
            end=end,
            source=source,
            **kwargs,
        )
    else:
        raise ValueError("Unsupported temperature anomaly kind: {0}".format(kind))

    if baseline is None and baseline_start is None and baseline_end is None:
        return (pipe(temp_cube) | v.anomaly(dim="time")).unwrap()

    baseline_data: xr.DataArray = baseline if baseline is not None else temp_cube
    if baseline_start is not None or baseline_end is not None:
        baseline_data = baseline_data.sel(time=slice(baseline_start, baseline_end))

    baseline_mean = baseline_data.mean(dim="time", skipna=True, keep_attrs=True)
    baseline_mean = baseline_mean.broadcast_like(temp_cube)
    return temp_cube - baseline_mean


def ndvi(
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    bbox: Optional[Sequence[float]] = None,
    aoi_geojson: Optional[Mapping[str, Any]] = None,
    start: Any = None,
    end: Any = None,
    source: Literal["sentinel2"] = "sentinel2",
    as_zscore: bool = True,
    **kwargs: Any,
) -> xr.DataArray:
    """
    Load an NDVI cube.

    For now, only Sentinel-2 is supported. By default, returns NDVI z-scores
    using ``load_sentinel2_ndvi_cube``, but can optionally return raw NDVI.
    """

    if source != "sentinel2":
        raise ValueError("Only the 'sentinel2' source is supported for NDVI.")

    if as_zscore:
        return load_sentinel2_ndvi_zscore_cube(
            lat=lat,
            lon=lon,
            start=start,
            end=end,
            **kwargs,
        )

    bands = load_sentinel2_bands_cube(
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        bands=["B04", "B08"],
        **kwargs,
    )
    return (pipe(bands) | v.ndvi_from_s2(nir_band="B08", red_band="B04")).unwrap()


__all__ = [
    "temperature",
    "temperature_min",
    "temperature_max",
    "temperature_anomaly",
    "ndvi",
]
