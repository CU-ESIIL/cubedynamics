"""Compatibility wrapper for :mod:`cubedynamics.data.prism`."""

from __future__ import annotations

from typing import Mapping, Sequence

from cubedynamics.data import prism as _prism_mod

_LEGACY_KEYS = {"min_lon", "max_lon", "min_lat", "max_lat"}


def _coerce_legacy_aoi(aoi: Mapping[str, float]) -> Sequence[float]:
    missing = sorted(_LEGACY_KEYS.difference(aoi))
    if missing:
        raise ValueError(f"AOI mapping missing keys: {missing}")
    return [aoi["min_lon"], aoi["min_lat"], aoi["max_lon"], aoi["max_lat"]]


_open_prism_streaming = _prism_mod._open_prism_streaming
_open_prism_download = _prism_mod._open_prism_download


def load_prism_cube(*args, **kwargs):
    """Compatibility wrapper allowing the legacy ``aoi`` keyword."""

    if "aoi" in kwargs and "bbox" not in kwargs:
        kwargs["bbox"] = _coerce_legacy_aoi(kwargs.pop("aoi"))

    original_stream = _prism_mod._open_prism_streaming
    try:
        if original_stream is not _open_prism_streaming:
            _prism_mod._open_prism_streaming = _open_prism_streaming
        return _prism_mod.load_prism_cube(*args, **kwargs)
    finally:
        _prism_mod._open_prism_streaming = original_stream


__all__ = list(_prism_mod.__all__) + [
    "_open_prism_streaming",
    "_open_prism_download",
]
