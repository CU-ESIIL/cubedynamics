"""Source discovery metadata for CubeDynamics scientific nouns.

The catalog is intentionally small and declarative.  It describes source
flavors that are actually wired into the package; planned sources do not
appear here until their loaders, tests, QA, and documentation exist.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_CATALOG: dict[str, dict[str, dict[str, Any]]] = {
    "temperature": {
        "gridmet": {
            "provider": "gridMET / University of California, Merced",
            "product": "gridMET daily surface meteorology",
            "product_version": "asset status/version supplied by the provider",
            "source_variables": {"maximum": "tmmx", "minimum": "tmmn"},
            "units": {"maximum": "K", "minimum": "K"},
            "coverage": "Contiguous United States",
            "temporal_coverage": "1979-present",
            "temporal_resolution": "daily",
            "spatial_resolution": "4,638.3 m",
            "crs": "EPSG:4326",
            "backend": "annual NetCDF over HTTPS",
            "streaming": "annual retrieval; AOI/time subset exposed as Dask chunks",
            "limitations": "No native daily mean temperature variable; choose maximum or minimum.",
        },
        "prism": {
            "provider": "PRISM Climate Group, Oregon State University",
            "product": "PRISM AN81d/AN91d daily time series",
            "product_version": "current AN81d/AN91d provider revision",
            "source_variables": {
                "maximum": "tmax",
                "minimum": "tmin",
                "mean": "tmean",
            },
            "units": {"maximum": "degC", "minimum": "degC", "mean": "degC"},
            "coverage": "Contiguous United States",
            "temporal_coverage": "1981-present",
            "temporal_resolution": "daily",
            "spatial_resolution": "approximately 4 km",
            "crs": "EPSG:4326",
            "backend": "NCSCO THREDDS NetCDF Subset Service",
            "streaming": "server-side daily AOI subsets, requested lazily with Dask",
            "limitations": "Recent grids are revised as station data and quality control mature.",
        },
    },
    "precipitation": {
        "gridmet": {
            "provider": "gridMET / University of California, Merced",
            "product": "gridMET daily surface meteorology",
            "product_version": "asset status/version supplied by the provider",
            "source_variables": {"default": "pr"},
            "units": {"default": "mm"},
            "coverage": "Contiguous United States",
            "temporal_coverage": "1979-present",
            "temporal_resolution": "daily total",
            "spatial_resolution": "4,638.3 m",
            "crs": "EPSG:4326",
            "backend": "annual NetCDF over HTTPS",
            "streaming": "annual retrieval; AOI/time subset exposed as Dask chunks",
            "limitations": "Recent gridMET assets can be provisional and later replaced.",
        },
        "prism": {
            "provider": "PRISM Climate Group, Oregon State University",
            "product": "PRISM AN81d/AN91d daily time series",
            "product_version": "current AN81d/AN91d provider revision",
            "source_variables": {"default": "ppt"},
            "units": {"default": "mm"},
            "coverage": "Contiguous United States",
            "temporal_coverage": "1981-present",
            "temporal_resolution": "daily total",
            "spatial_resolution": "approximately 4 km",
            "crs": "EPSG:4326",
            "backend": "NCSCO THREDDS NetCDF Subset Service",
            "streaming": "server-side daily AOI subsets, requested lazily with Dask",
            "limitations": "Recent grids are revised as station data and quality control mature.",
        },
    },
    "vpd": {
        "gridmet": {
            "provider": "gridMET / University of California, Merced",
            "product": "gridMET daily surface meteorology",
            "product_version": "asset status/version supplied by the provider",
            "source_variables": {"default": "vpd"},
            "units": {"default": "kPa"},
            "coverage": "Contiguous United States",
            "temporal_coverage": "1979-present",
            "temporal_resolution": "daily mean",
            "spatial_resolution": "4,638.3 m",
            "crs": "EPSG:4326",
            "backend": "annual NetCDF over HTTPS",
            "streaming": "annual retrieval; AOI/time subset exposed as Dask chunks",
            "limitations": "PRISM VPD is not registered until its daily NcSS path is validated.",
        },
    },
    "wind": {
        "gridmet": {
            "provider": "gridMET / University of California, Merced",
            "product": "gridMET daily surface meteorology",
            "product_version": "asset status/version supplied by the provider",
            "source_variables": {"default": "vs"},
            "units": {"default": "m s-1"},
            "coverage": "Contiguous United States",
            "temporal_coverage": "1979-present",
            "temporal_resolution": "daily",
            "spatial_resolution": "4,638.3 m",
            "crs": "EPSG:4326",
            "backend": "annual NetCDF over HTTPS",
            "streaming": "annual retrieval; AOI/time subset exposed as Dask chunks",
            "limitations": "Represents gridMET 10 m wind velocity, not gust speed.",
        },
    },
    "humidity": {
        "gridmet": {
            "provider": "gridMET / University of California, Merced",
            "product": "gridMET daily surface meteorology",
            "product_version": "asset status/version supplied by the provider",
            "source_variables": {"maximum": "rmax", "minimum": "rmin"},
            "units": {"maximum": "%", "minimum": "%"},
            "coverage": "Contiguous United States",
            "temporal_coverage": "1979-present",
            "temporal_resolution": "daily",
            "spatial_resolution": "4,638.3 m",
            "crs": "EPSG:4326",
            "backend": "annual NetCDF over HTTPS",
            "streaming": "annual retrieval; AOI/time subset exposed as Dask chunks",
            "limitations": "Choose maximum or minimum relative humidity explicitly.",
        },
    },
    "radiation": {
        "gridmet": {
            "provider": "gridMET / University of California, Merced",
            "product": "gridMET daily surface meteorology",
            "product_version": "asset status/version supplied by the provider",
            "source_variables": {"default": "srad"},
            "units": {"default": "W m-2"},
            "coverage": "Contiguous United States",
            "temporal_coverage": "1979-present",
            "temporal_resolution": "daily",
            "spatial_resolution": "4,638.3 m",
            "crs": "EPSG:4326",
            "backend": "annual NetCDF over HTTPS",
            "streaming": "annual retrieval; AOI/time subset exposed as Dask chunks",
            "limitations": "Surface downward shortwave radiation, not net radiation.",
        },
    },
    "surface_reflectance": {
        "sentinel2": {
            "provider": "European Union Copernicus Programme / ESA",
            "product": "Sentinel-2 Level-2A surface reflectance",
            "product_version": "processing baseline recorded on each source item",
            "source_variables": {"default": "user-selected Sentinel-2 bands"},
            "units": {"default": "source digital numbers / reflectance scaling"},
            "coverage": "Global land surfaces",
            "temporal_coverage": "2015-present",
            "temporal_resolution": "scene acquisition; nominal five-day constellation revisit",
            "spatial_resolution": "10, 20, or 60 m by band; CubeDynamics default 10 m",
            "crs": "native Sentinel-2 UTM tile CRS",
            "backend": "cubo STAC and cloud-optimized assets",
            "streaming": "STAC search and lazy Dask-backed raster reads",
            "limitations": "Scene-level cloud filtering does not remove every cloudy pixel.",
        },
    },
    "vegetation_index": {
        "sentinel2": {
            "provider": "European Union Copernicus Programme / ESA",
            "product": "NDVI derived from Sentinel-2 Level-2A B08 and B04",
            "product_version": "processing baseline recorded on each source item",
            "source_variables": {"ndvi": ["B08", "B04"]},
            "units": {"ndvi": "1"},
            "coverage": "Global land surfaces",
            "temporal_coverage": "2015-present",
            "temporal_resolution": "scene acquisition; nominal five-day constellation revisit",
            "spatial_resolution": "10 m",
            "crs": "native Sentinel-2 UTM tile CRS",
            "backend": "cubo STAC and cloud-optimized assets",
            "streaming": "lazy band reads and lazy arithmetic",
            "limitations": "NDVI is a greenness index, not a direct measurement of biomass.",
        },
    },
}


def list_sources() -> dict[str, tuple[str, ...]]:
    """Return implemented source flavors grouped by scientific noun."""

    return {noun: tuple(sorted(entries)) for noun, entries in sorted(_CATALOG.items())}


def sources(noun: str) -> tuple[str, ...]:
    """Return implemented source flavors for ``noun``.

    Planned integrations are deliberately omitted.  An unknown noun raises a
    message that lists the vocabulary currently available.
    """

    key = _normalize_name(noun)
    if key not in _CATALOG:
        available = ", ".join(sorted(_CATALOG))
        raise ValueError(f"Unknown scientific noun {noun!r}. Available nouns: {available}.")
    return tuple(sorted(_CATALOG[key]))


def describe(noun: str, source: str | None = None) -> dict[str, Any]:
    """Return human-readable metadata for an implemented noun/source flavor."""

    key = _normalize_name(noun)
    available_sources = sources(key)
    if source is None:
        return {
            "noun": key,
            "sources": {
                flavor: deepcopy(_CATALOG[key][flavor]) for flavor in available_sources
            },
        }

    flavor = _normalize_name(source)
    if flavor not in _CATALOG[key]:
        choices = ", ".join(available_sources)
        raise ValueError(
            f"Source {source!r} does not provide {key!r}. Available sources: {choices}."
        )
    result = deepcopy(_CATALOG[key][flavor])
    result.update({"noun": key, "source": flavor})
    return result


def _source_definition(noun: str, source: str) -> dict[str, Any]:
    """Return one internal source definition after public validation."""

    return describe(noun, source)


def _normalize_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Scientific noun and source names must be non-empty strings.")
    return value.strip().lower().replace("-", "_")


__all__ = ["describe", "list_sources", "sources"]
