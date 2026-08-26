"""Human-readable scientific nouns backed by existing source adapters."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Mapping, Sequence

import xarray as xr

from . import gridmet as _gridmet
from . import prism as _prism
from . import sentinel2 as _sentinel2
from .catalog import _source_definition


def temperature(
    *,
    source: str = "gridmet",
    statistic: str = "maximum",
    bbox: Sequence[float] | None = None,
    geometry: Mapping[str, object] | None = None,
    aoi_geojson: Mapping[str, object] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    start: Any = None,
    end: Any = None,
    **kwargs: Any,
) -> xr.DataArray:
    """Load observed gridded air temperature from an implemented source.

    ``statistic`` is explicit because gridMET does not publish a native daily
    mean temperature field.  The default is daily maximum, which is available
    from both current source flavors.
    """

    return _load_climate_noun(
        "temperature",
        source=source,
        variant=statistic,
        bbox=bbox,
        geometry=geometry,
        aoi_geojson=aoi_geojson,
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        **kwargs,
    )


def precipitation(
    *,
    source: str = "gridmet",
    bbox: Sequence[float] | None = None,
    geometry: Mapping[str, object] | None = None,
    aoi_geojson: Mapping[str, object] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    start: Any = None,
    end: Any = None,
    **kwargs: Any,
) -> xr.DataArray:
    """Load daily precipitation from gridMET or PRISM."""

    return _load_climate_noun(
        "precipitation", source=source, bbox=bbox, geometry=geometry,
        aoi_geojson=aoi_geojson, lat=lat, lon=lon, start=start, end=end, **kwargs
    )


def vpd(
    *,
    source: str = "gridmet",
    bbox: Sequence[float] | None = None,
    geometry: Mapping[str, object] | None = None,
    aoi_geojson: Mapping[str, object] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    start: Any = None,
    end: Any = None,
    **kwargs: Any,
) -> xr.DataArray:
    """Load mean daily vapor-pressure deficit (currently gridMET)."""

    return _load_climate_noun(
        "vpd", source=source, bbox=bbox, geometry=geometry,
        aoi_geojson=aoi_geojson, lat=lat, lon=lon, start=start, end=end, **kwargs
    )


def wind(
    *,
    source: str = "gridmet",
    bbox: Sequence[float] | None = None,
    geometry: Mapping[str, object] | None = None,
    aoi_geojson: Mapping[str, object] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    start: Any = None,
    end: Any = None,
    **kwargs: Any,
) -> xr.DataArray:
    """Load 10 m wind velocity (currently gridMET)."""

    return _load_climate_noun(
        "wind", source=source, bbox=bbox, geometry=geometry,
        aoi_geojson=aoi_geojson, lat=lat, lon=lon, start=start, end=end, **kwargs
    )


def humidity(
    *,
    source: str = "gridmet",
    statistic: str = "maximum",
    bbox: Sequence[float] | None = None,
    geometry: Mapping[str, object] | None = None,
    aoi_geojson: Mapping[str, object] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    start: Any = None,
    end: Any = None,
    **kwargs: Any,
) -> xr.DataArray:
    """Load daily relative humidity (currently gridMET)."""

    return _load_climate_noun(
        "humidity", source=source, variant=statistic, bbox=bbox, geometry=geometry,
        aoi_geojson=aoi_geojson, lat=lat, lon=lon, start=start, end=end, **kwargs
    )


def radiation(
    *,
    source: str = "gridmet",
    bbox: Sequence[float] | None = None,
    geometry: Mapping[str, object] | None = None,
    aoi_geojson: Mapping[str, object] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    start: Any = None,
    end: Any = None,
    **kwargs: Any,
) -> xr.DataArray:
    """Load downward shortwave radiation (currently gridMET)."""

    return _load_climate_noun(
        "radiation", source=source, bbox=bbox, geometry=geometry,
        aoi_geojson=aoi_geojson, lat=lat, lon=lon, start=start, end=end, **kwargs
    )


def surface_reflectance(
    *,
    source: str = "sentinel2",
    lat: float,
    lon: float,
    start: Any,
    end: Any,
    variables: Sequence[str] | None = None,
    bands: Sequence[str] | None = None,
    **kwargs: Any,
) -> xr.DataArray:
    """Stream Sentinel-2 Level-2A surface-reflectance bands lazily."""

    definition = _source_definition("surface_reflectance", source)
    _reject_synthetic(kwargs)
    if variables is not None and bands is not None:
        raise ValueError("Use either 'variables' or 'bands' for surface_reflectance, not both.")
    selected = list(variables if variables is not None else bands or ["B04", "B08"])
    if not selected:
        raise ValueError("surface_reflectance requires at least one Sentinel-2 band.")
    try:
        cube = _sentinel2.load_s2_cube(
            lat=lat,
            lon=lon,
            start=str(start),
            end=str(end),
            bands=selected,
            **kwargs,
        )
    except Exception as exc:
        raise RuntimeError(
            "CubeDynamics could not load Sentinel-2 surface reflectance for the "
            "requested place and dates. The remote catalog or assets may be unavailable."
        ) from exc
    return _annotate(
        cube,
        noun="surface_reflectance",
        source=source,
        definition=definition,
        source_variables=selected,
        spatial_query={"lat": lat, "lon": lon},
        temporal_query={"start": str(start), "end": str(end)},
        normalization="dimension ordering and Dask chunking; values otherwise unchanged",
        data_state="raw",
    )


def vegetation_index(
    *,
    source: str = "sentinel2",
    index: str = "ndvi",
    lat: float,
    lon: float,
    start: Any,
    end: Any,
    **kwargs: Any,
) -> xr.DataArray:
    """Load a documented vegetation index; currently Sentinel-2 NDVI."""

    definition = _source_definition("vegetation_index", source)
    index_key = str(index).strip().lower()
    if index_key != "ndvi":
        raise ValueError("vegetation_index currently supports only index='ndvi'.")
    _reject_synthetic(kwargs)
    try:
        cube = _sentinel2.load_s2_ndvi_cube(
            lat=lat, lon=lon, start=str(start), end=str(end), **kwargs
        )
    except Exception as exc:
        raise RuntimeError(
            "CubeDynamics could not load the Sentinel-2 bands needed for NDVI. "
            "The remote catalog or assets may be unavailable."
        ) from exc
    return _annotate(
        cube,
        noun="vegetation_index",
        source=source,
        definition=definition,
        source_variables=["B08", "B04"],
        spatial_query={"lat": lat, "lon": lon},
        temporal_query={"start": str(start), "end": str(end)},
        normalization="NDVI = (B08 - B04) / (B08 + B04 + 1e-6)",
        data_state="derived",
        output_name="ndvi",
    )


def _load_climate_noun(
    noun: str,
    *,
    source: str = "gridmet",
    variant: str = "default",
    bbox: Sequence[float] | None = None,
    geometry: Mapping[str, object] | None = None,
    aoi_geojson: Mapping[str, object] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    start: Any = None,
    end: Any = None,
    **kwargs: Any,
) -> xr.DataArray:
    definition = _source_definition(noun, source)
    _reject_synthetic(kwargs)
    geojson = _resolve_geometry(geometry, aoi_geojson)
    variants = definition["source_variables"]
    variant_key = str(variant).strip().lower()
    if variant_key not in variants:
        choices = ", ".join(sorted(variants))
        raise ValueError(
            f"{noun} from {source} does not support {variant!r}. Available choices: {choices}."
        )
    source_variable = variants[variant_key]
    loader_kwargs = {
        "lat": lat,
        "lon": lon,
        "bbox": bbox,
        "aoi_geojson": geojson,
        "start": start,
        "end": end,
        "variable": source_variable,
        "freq": kwargs.pop("freq", "D"),
        "allow_synthetic": False,
        **kwargs,
    }
    try:
        if source == "gridmet":
            loaded = _gridmet.load_gridmet_cube(**loader_kwargs)
        elif source == "prism":
            loaded = _prism.load_prism_cube(**loader_kwargs)
        else:  # catalog validation makes this defensive rather than user-facing
            raise ValueError(f"No climate adapter is registered for source {source!r}.")
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"CubeDynamics could not load {noun} from {source} for the requested "
            "area and dates. The remote source may be unavailable or its layout may have changed."
        ) from exc

    loaded_is_synthetic = bool(loaded.attrs.get("is_synthetic", False))
    cube = loaded[source_variable] if isinstance(loaded, xr.Dataset) else loaded
    if loaded_is_synthetic or bool(cube.attrs.get("is_synthetic", False)):
        raise RuntimeError(
            f"The {source} adapter returned synthetic data; scientific noun loaders refuse it."
        )
    spatial_query = {
        key: value
        for key, value in {
            "lat": lat,
            "lon": lon,
            "bbox": list(bbox) if bbox is not None else None,
            "geometry": geojson,
        }.items()
        if value is not None
    }
    return _annotate(
        cube,
        noun=noun,
        source=source,
        definition=definition,
        source_variables=[source_variable],
        spatial_query=spatial_query,
        temporal_query={"start": str(start), "end": str(end)},
        normalization=f"renamed {source_variable!r} to scientific noun {noun!r}",
        data_state="normalized",
        output_name=noun,
        variant=variant_key,
    )


def _annotate(
    cube: xr.DataArray,
    *,
    noun: str,
    source: str,
    definition: Mapping[str, Any],
    source_variables: Sequence[str],
    spatial_query: Mapping[str, Any],
    temporal_query: Mapping[str, Any],
    normalization: str,
    data_state: str,
    output_name: str | None = None,
    variant: str = "default",
) -> xr.DataArray:
    result = cube.copy(deep=False)
    original_backend = result.attrs.get("source")
    result.name = output_name or noun
    crs = _infer_crs(result) or definition["crs"]
    units = definition.get("units", {}).get(variant)
    attrs = dict(result.attrs)
    attrs.update(
        {
            "scientific_noun": noun,
            "semantic_name": noun,
            "semantic_kind": "continuous_field",
            "semantic_category": (
                "surface_observation"
                if noun in {"surface_reflectance", "vegetation_index"}
                else "climate"
            ),
            "semantic_temporal": "time" in result.dims,
            "semantic_dimensions": json.dumps(list(result.dims)),
            "source_flavor": source,
            "source_provider": definition["provider"],
            "source_product": definition["product"],
            "product_version": definition["product_version"],
            "source_variables": json.dumps(list(source_variables), sort_keys=True),
            "spatial_query": json.dumps(spatial_query, sort_keys=True, default=str),
            "temporal_query": json.dumps(temporal_query, sort_keys=True, default=str),
            "crs": str(crs),
            "spatial_resolution": definition["spatial_resolution"],
            "temporal_resolution": definition["temporal_resolution"],
            "streaming_protocol": definition["backend"],
            "normalization": normalization,
            "data_state": data_state,
            "access_state": "remote_lazy",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "is_synthetic": False,
        }
    )
    if original_backend is not None:
        attrs["source_backend"] = original_backend
    if units is not None:
        attrs["units"] = units
    result.attrs = attrs
    return result


def _resolve_geometry(
    geometry: Mapping[str, object] | None,
    aoi_geojson: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    if geometry is not None and aoi_geojson is not None:
        raise ValueError("Use either 'geometry' or the compatibility name 'aoi_geojson', not both.")
    return geometry if geometry is not None else aoi_geojson


def _reject_synthetic(kwargs: Mapping[str, Any]) -> None:
    if bool(kwargs.get("allow_synthetic", False)):
        raise ValueError(
            "Scientific noun loaders never return synthetic fallback data. "
            "Use a checked fixture for examples or call a low-level loader explicitly for tests."
        )


def _infer_crs(cube: xr.DataArray) -> str | None:
    if "crs" in cube.attrs:
        return str(cube.attrs["crs"])
    if "epsg" in cube.attrs:
        return f"EPSG:{cube.attrs['epsg']}"
    try:
        rio_crs = cube.rio.crs
    except Exception:
        rio_crs = None
    return str(rio_crs) if rio_crs is not None else None


__all__ = [
    "humidity",
    "precipitation",
    "radiation",
    "surface_reflectance",
    "temperature",
    "vegetation_index",
    "vpd",
    "wind",
]
