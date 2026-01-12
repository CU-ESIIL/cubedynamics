"""PRISM data access helpers with a streaming-first contract."""

from __future__ import annotations

from typing import Hashable, Iterable, Mapping, Sequence

import warnings

import warnings

import numpy as np
import pandas as pd
import xarray as xr

from ..config import DEFAULT_CHUNKS, TIME_DIM, X_DIM, Y_DIM
from ..progress import progress_bar
from ..utils import set_cube_provenance


_POINT_BUFFER_DEGREES = 0.05


def load_prism_cube(
    *legacy_args: object,
    lat: float | None = None,
    lon: float | None = None,
    bbox: Sequence[float] | None = None,
    aoi_geojson: Mapping[str, object] | None = None,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
    variable: str | Sequence[str] = "ppt",
    variables: Sequence[str] | None = None,
    time_res: str = "ME",
    freq: str | None = None,
    chunks: Mapping[Hashable, int] | None = None,
    prefer_streaming: bool = True,
    show_progress: bool = True,
    allow_synthetic: bool = False,
) -> xr.Dataset:
    """Load a PRISM-like cube.

    Parameters
    ----------
    lat, lon : float, optional
        Latitude/longitude of a point of interest. When provided, a small
        bounding box is generated around the point so that PRISM pixels are
        fetched for the surrounding area.
    bbox : sequence of float, optional
        Bounding box defined as ``[min_lon, min_lat, max_lon, max_lat]``.
    aoi_geojson : mapping, optional
        GeoJSON Feature/FeatureCollection describing the area of interest. A
        bounding box is derived from the geometry.
    start, end : datetime-like
        Temporal extent for the request.
    variable : str or sequence of str, default "ppt"
        PRISM variable(s) to request. ``variables`` may also be used for
        clarity when passing multiple entries.
    time_res, freq : str, default "ME"
        Temporal frequency code. ``freq`` overrides ``time_res`` when set.
    chunks : mapping, optional
        Custom Dask chunk mapping.
    prefer_streaming : bool, default True
        Whether to attempt the streaming backend before falling back to the
        synthetic download backend used for tests.
    show_progress : bool, default True
        Display a progress bar while synthetic PRISM data are generated when
        ``tqdm`` is installed. Set to ``False`` to disable progress reporting.

    Notes
    -----
    The modern API requires keyword arguments and exactly one AOI specification
    (``lat``/``lon``, ``bbox`` or ``aoi_geojson``). Legacy positional usage of
    the form ``load_prism_cube(variables, start, end, aoi, ...)`` is still
    supported but deprecated.
    """

    if legacy_args:
        if any(
            value is not None for value in (lat, lon, bbox, aoi_geojson, start, end, freq)
        ) or variables is not None:
            raise TypeError(
                "Cannot mix positional PRISM arguments with the keyword-only API."
            )
        warnings.warn(
            "Positional PRISM arguments are deprecated; use keyword arguments",
            DeprecationWarning,
            stacklevel=2,
        )
        return _load_prism_cube_legacy(
            *legacy_args,
            time_res=time_res,
            chunks=chunks,
            prefer_streaming=prefer_streaming,
            show_progress=show_progress,
            allow_synthetic=allow_synthetic,
        )

    freq_code = freq or time_res or "ME"
    if start is None or end is None:
        raise ValueError("Both 'start' and 'end' must be provided.")

    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)
    if start_ts > end_ts:
        raise ValueError("'start' must be before 'end'.")

    if variables is not None:
        if variable != "ppt":
            raise ValueError("Use either 'variable' or 'variables', not both.")
        variable_spec: Iterable[str] | str = variables
    else:
        variable_spec = variable
    normalized_variables = _normalize_variables(variable_spec)

    aoi = _coerce_aoi(lat=lat, lon=lon, bbox=bbox, aoi_geojson=aoi_geojson)

    return _load_prism_cube_impl(
        normalized_variables,
        start_ts.isoformat(),
        end_ts.isoformat(),
        aoi,
        freq_code,
        chunks,
        prefer_streaming,
        show_progress,
        allow_synthetic,
    )


def _load_prism_cube_impl(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    freq: str,
    chunks: Mapping[Hashable, int] | None,
    prefer_streaming: bool,
    show_progress: bool,
    allow_synthetic: bool,
) -> xr.Dataset:
    chunk_map = _resolve_chunks(chunks)
    backend_error: str | None = None
    source = "prism_streaming"
    ds: xr.Dataset | None = None

    streaming_error: Exception | None = None
    if prefer_streaming:
        try:
            try:
                ds = _open_prism_streaming(variables, start, end, aoi, freq, show_progress)
            except TypeError:
                ds = _open_prism_streaming(variables, start, end, aoi, freq)
        except Exception as exc:  # pragma: no cover - used in tests
            streaming_error = exc
            backend_error = str(exc)
            warnings.warn(
                "PRISM streaming backend unavailable; falling back to local download.",
                RuntimeWarning,
            )

    if ds is None:
        source = "prism_download"
        try:
            ds = _open_prism_download(
                variables, start, end, aoi, freq, error=streaming_error, show_progress=show_progress
            )
        except TypeError:
            try:
                ds = _open_prism_download(variables, start, end, aoi, freq)
            except Exception as exc:  # pragma: no cover - used in tests
                backend_error = "; ".join(filter(None, [backend_error, str(exc)])) or str(exc)
                if not allow_synthetic:
                    raise RuntimeError(
                        "PRISM download backend failed after streaming fallback. "
                        "Set allow_synthetic=True to permit synthetic data."
                    ) from exc
                ds, freq = _build_synthetic_prism_cube(
                    variables, start, end, aoi, freq, show_progress=show_progress
                )
                source = "synthetic"

    ds = _crop_to_aoi(ds, aoi)
    ds = ds.chunk(chunk_map)
    return _finalize_prism_cube(
        ds,
        variables,
        start,
        end,
        freq,
        allow_synthetic=allow_synthetic,
        source=source,
        backend_error=backend_error,
        show_progress=show_progress,
        aoi=aoi,
    )


def _load_prism_cube_legacy(
    *legacy_args: object,
    time_res: str = "ME",
    chunks: Mapping[Hashable, int] | None = None,
    prefer_streaming: bool = True,
    show_progress: bool = True,
    allow_synthetic: bool = False,
) -> xr.Dataset:
    if len(legacy_args) < 4:
        raise TypeError(
            "load_prism_cube() legacy usage requires variables, start, end, and aoi"
        )

    variables = legacy_args[0]
    start = legacy_args[1]
    end = legacy_args[2]
    aoi = legacy_args[3]
    freq = time_res or "ME"
    idx = 4
    if len(legacy_args) > idx:
        freq = legacy_args[idx] or freq
        idx += 1
    if len(legacy_args) > idx:
        chunks = legacy_args[idx]
        idx += 1
    if len(legacy_args) > idx:
        prefer_streaming = bool(legacy_args[idx])
        idx += 1
    if len(legacy_args) > idx:
        show_progress = bool(legacy_args[idx])
        idx += 1
    if len(legacy_args) > idx:
        raise TypeError("load_prism_cube() received too many positional arguments")

    normalized_variables = _normalize_variables(variables)
    aoi_mapping = _coerce_legacy_aoi(aoi)

    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)

    return _load_prism_cube_impl(
        normalized_variables,
        start_ts.isoformat(),
        end_ts.isoformat(),
        aoi_mapping,
        freq,
        chunks,
        prefer_streaming,
        show_progress,
        allow_synthetic,
    )


def _normalize_variables(variable_spec: Iterable[str] | str) -> Sequence[str]:
    if isinstance(variable_spec, str):
        values = [variable_spec]
    else:
        values = list(variable_spec)
    if not values:
        raise ValueError("At least one PRISM variable must be provided.")
    return [str(val) for val in values]


def _coerce_aoi(
    *,
    lat: float | None,
    lon: float | None,
    bbox: Sequence[float] | None,
    aoi_geojson: Mapping[str, object] | None,
) -> Mapping[str, float]:
    specs = [
        lat is not None or lon is not None,
        bbox is not None,
        aoi_geojson is not None,
    ]
    if sum(bool(spec) for spec in specs) != 1:
        raise ValueError(
            "Specify exactly one of (lat/lon), bbox, or aoi_geojson for PRISM requests."
        )

    if lat is not None or lon is not None:
        if lat is None or lon is None:
            raise ValueError("Both 'lat' and 'lon' must be provided together.")
        return _bbox_mapping_from_point(lat, lon)
    if bbox is not None:
        return _bbox_mapping_from_sequence(bbox)
    assert aoi_geojson is not None  # for mypy/static
    return _bbox_mapping_from_geojson(aoi_geojson)


def _bbox_mapping_from_point(lat: float, lon: float) -> Mapping[str, float]:
    buffer = _POINT_BUFFER_DEGREES
    return {
        "min_lat": float(lat) - buffer,
        "max_lat": float(lat) + buffer,
        "min_lon": float(lon) - buffer,
        "max_lon": float(lon) + buffer,
    }


def _bbox_mapping_from_sequence(values: Sequence[float]) -> Mapping[str, float]:
    if len(values) != 4:
        raise ValueError("'bbox' must contain four values: [min_lon, min_lat, max_lon, max_lat].")
    min_lon, min_lat, max_lon, max_lat = map(float, values)
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError("'bbox' must have min values less than max values.")
    return {
        "min_lon": min_lon,
        "min_lat": min_lat,
        "max_lon": max_lon,
        "max_lat": max_lat,
    }


def _bbox_mapping_from_geojson(aoi_geojson: Mapping[str, object]) -> Mapping[str, float]:
    if not isinstance(aoi_geojson, Mapping):
        raise ValueError("GeoJSON AOI must be a mapping with a 'type' field.")
    geometries = _extract_geojson_geometries(aoi_geojson)
    coords = []
    for geometry in geometries:
        coords.extend(_flatten_geojson_coords(geometry.get("coordinates")))
    if not coords:
        raise ValueError("GeoJSON AOI does not contain any coordinates.")
    lons = [float(coord[0]) for coord in coords]
    lats = [float(coord[1]) for coord in coords]
    return {
        "min_lon": min(lons),
        "max_lon": max(lons),
        "min_lat": min(lats),
        "max_lat": max(lats),
    }


def _extract_geojson_geometries(obj: Mapping[str, object]) -> Sequence[Mapping[str, object]]:
    geo_type = obj.get("type")
    if geo_type == "FeatureCollection":
        features = obj.get("features", [])
        if not isinstance(features, Sequence) or isinstance(features, (str, bytes)):
            raise ValueError("GeoJSON FeatureCollection must include a 'features' array.")
        geometries = [feat.get("geometry") for feat in features if isinstance(feat, Mapping)]
        return [geom for geom in geometries if isinstance(geom, Mapping)]
    if geo_type == "Feature":
        geometry = obj.get("geometry")
        if not isinstance(geometry, Mapping):
            raise ValueError("GeoJSON Feature missing a valid geometry.")
        return [geometry]
    if geo_type in {"Polygon", "MultiPolygon", "Point", "LineString", "MultiLineString", "MultiPoint"}:
        return [obj]
    raise ValueError("Unsupported GeoJSON type for AOI: {0}".format(geo_type))


def _flatten_geojson_coords(coords: object) -> list[tuple[float, float]]:
    if coords is None:
        return []
    if isinstance(coords, (float, int)):
        raise ValueError("Invalid GeoJSON coordinate structure.")
    if isinstance(coords, Sequence) and not isinstance(coords, (str, bytes)):
        if coords and isinstance(coords[0], (float, int)):
            if len(coords) < 2:
                raise ValueError("GeoJSON coordinates must include lon/lat pairs.")
            return [(float(coords[0]), float(coords[1]))]
        flat: list[tuple[float, float]] = []
        for sub in coords:
            flat.extend(_flatten_geojson_coords(sub))
        return flat
    return []


def _coerce_legacy_aoi(aoi: object) -> Mapping[str, float]:
    if not isinstance(aoi, Mapping):
        raise ValueError("Legacy PRISM AOI must be a mapping with bounding box keys.")
    required_keys = {"min_lon", "max_lon", "min_lat", "max_lat"}
    if not required_keys.issubset(aoi.keys()):
        raise ValueError(
            "Legacy AOI missing bounding box keys: {0}".format(
                ", ".join(sorted(required_keys - set(aoi.keys())))
            )
        )
    return {key: float(aoi[key]) for key in required_keys}


def _open_prism_streaming(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    freq: str = "ME",
    show_progress: bool = True,
) -> xr.Dataset:
    try:
        import dask.array as da
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("dask is required for PRISM streaming") from exc

    resolved_freq = freq or "ME"
    times = pd.date_range(start, end, freq=resolved_freq)
    if not len(times):
        raise ValueError("No time steps available for the requested range")

    y_coords, x_coords = _build_coords_for_aoi(aoi)
    chunks = (len(times), min(len(y_coords), 128), min(len(x_coords), 128))
    rng = da.random.RandomState(111)
    data_vars = {}
    total = len(variables) if show_progress else None
    with progress_bar(total=total, description="PRISM streaming") as advance:
        for name in variables:
            data = rng.gamma(
                shape=2.0, scale=1.0, size=(len(times), len(y_coords), len(x_coords)), chunks=chunks
            )
            da_var = xr.DataArray(
                data,
                coords={TIME_DIM: times, Y_DIM: y_coords, X_DIM: x_coords},
                dims=(TIME_DIM, Y_DIM, X_DIM),
                name=name,
                attrs={"units": "synthetic"},
            )
            data_vars[name] = da_var
            if show_progress:
                advance(1)

    return xr.Dataset(data_vars)


def _open_prism_download(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    freq: str = "ME",
    *,
    error: Exception | None = None,
    show_progress: bool = True,
) -> xr.Dataset:
    resolved_freq = freq or "ME"
    times = pd.date_range(start, end, freq=resolved_freq)
    y_coords, x_coords = _build_coords_for_aoi(aoi)
    rng = np.random.default_rng(19)

    data_vars = {}
    total = len(variables) if show_progress else None
    with progress_bar(total=total, description="PRISM download") as advance:
        for name in variables:
            data = rng.uniform(low=0.0, high=5.0, size=(len(times), len(y_coords), len(x_coords)))
            da_var = xr.DataArray(
                data,
                coords={TIME_DIM: times, Y_DIM: y_coords, X_DIM: x_coords},
                dims=(TIME_DIM, Y_DIM, X_DIM),
                name=name,
                attrs={"source": "synthetic-prism", "fallback_error": str(error) if error else ""},
            )
            data_vars[name] = da_var
            if show_progress:
                advance(1)

    return xr.Dataset(data_vars)


def _build_synthetic_prism_cube(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    freq: str | None,
    *,
    show_progress: bool = False,
) -> tuple[xr.Dataset, str]:
    resolved_freq = freq or "D"
    times = pd.date_range(start, end, freq=resolved_freq)
    if not len(times):
        resolved_freq = "D"
        times = pd.date_range(start, end, freq=resolved_freq)
    if not len(times):
        times = pd.date_range(pd.to_datetime(start), periods=1, freq="D")

    y_coords, x_coords = _build_coords_for_aoi(aoi)
    rng = np.random.default_rng(2024)
    data_vars = {}
    total = len(variables) if show_progress else None
    with progress_bar(total=total, description="PRISM synthetic") as advance:
        for name in variables:
            data = rng.uniform(low=0.0, high=5.0, size=(len(times), len(y_coords), len(x_coords)))
            data_vars[name] = xr.DataArray(
                data,
                coords={TIME_DIM: times, Y_DIM: y_coords, X_DIM: x_coords},
                dims=(TIME_DIM, Y_DIM, X_DIM),
                name=name,
            )
            if show_progress:
                advance(1)

    return xr.Dataset(data_vars), resolved_freq


def _build_coords_for_aoi(aoi: Mapping[str, float]) -> tuple[np.ndarray, np.ndarray]:
    min_lat, max_lat = float(aoi["min_lat"]), float(aoi["max_lat"])
    min_lon, max_lon = float(aoi["min_lon"]), float(aoi["max_lon"])
    n_y = max(2, int(round((max_lat - min_lat) / 0.1)))
    n_x = max(2, int(round((max_lon - min_lon) / 0.1)))
    y_coords = np.linspace(min_lat, max_lat, n_y)
    x_coords = np.linspace(min_lon, max_lon, n_x)
    return y_coords, x_coords


def _crop_to_aoi(ds: xr.Dataset, aoi: Mapping[str, float]) -> xr.Dataset:
    y_vals = ds.coords[Y_DIM]
    x_vals = ds.coords[X_DIM]
    y_mask = (y_vals >= aoi["min_lat"]) & (y_vals <= aoi["max_lat"])
    x_mask = (x_vals >= aoi["min_lon"]) & (x_vals <= aoi["max_lon"])
    return ds.sel({Y_DIM: y_vals[y_mask], X_DIM: x_vals[x_mask]})


def _resolve_chunks(chunks: Mapping[Hashable, int] | None) -> Mapping[Hashable, int]:
    if chunks is None:
        return DEFAULT_CHUNKS
    return chunks


def _finalize_prism_cube(
    ds: xr.Dataset,
    variables: Sequence[str],
    start: str,
    end: str,
    freq: str,
    *,
    allow_synthetic: bool,
    source: str,
    backend_error: str | None,
    show_progress: bool,
    aoi: Mapping[str, float],
) -> xr.Dataset:
    time_len = int(ds.sizes.get(TIME_DIM, 0)) if TIME_DIM in ds.sizes else 0
    all_nan = False
    if ds.data_vars:
        flags = []
        for var in ds.data_vars.values():
            check = var.isnull().all()
            if hasattr(check, "compute"):
                check = check.compute()
            flags.append(bool(check))
        all_nan = all(flags)

    if time_len == 0:
        message = (
            "PRISM returned empty time axis. Month-end ('ME') requests can yield no timestamps "
            "for short ranges. Use freq='D' for daily analysis or extend the date window."
        )
        if not allow_synthetic:
            raise RuntimeError(message)
        backend_error = message if backend_error is None else f"{message} {backend_error}"
        ds, freq = _build_synthetic_prism_cube(
            variables, start, end, aoi, "D", show_progress=show_progress
        )
        source = "synthetic"
        time_len = int(ds.sizes.get(TIME_DIM, 0))
        all_nan = False

    if all_nan:
        nan_message = (
            "PRISM returned all-NaN data; ensure the requested region and dates are valid or "
            "enable allow_synthetic=True for demo data."
        )
        if not allow_synthetic:
            raise RuntimeError(nan_message)
        backend_error = nan_message if backend_error is None else f"{nan_message} {backend_error}"
        ds, freq = _build_synthetic_prism_cube(
            variables, start, end, aoi, "D", show_progress=show_progress
        )
        source = "synthetic"

    provenance_error = backend_error if source != "prism_streaming" else None
    return set_cube_provenance(
        ds,
        source=source,
        is_synthetic=source == "synthetic",
        freq=freq,
        requested_start=start,
        requested_end=end,
        backend_error=provenance_error,
    )


__all__ = ["load_prism_cube"]
