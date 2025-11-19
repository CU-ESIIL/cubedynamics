"""Compatibility wrapper for :mod:`cubedynamics.data.gridmet`."""

from cubedynamics.data import gridmet as _gridmet_mod

_open_gridmet_streaming = _gridmet_mod._open_gridmet_streaming
_open_gridmet_download = _gridmet_mod._open_gridmet_download


def load_gridmet_cube(*args, **kwargs):
    """Compatibility wrapper that respects patched streaming helpers."""

    original_stream = _gridmet_mod._open_gridmet_streaming
    try:
        if original_stream is not _open_gridmet_streaming:
            _gridmet_mod._open_gridmet_streaming = _open_gridmet_streaming
        return _gridmet_mod.load_gridmet_cube(*args, **kwargs)
    finally:
        _gridmet_mod._open_gridmet_streaming = original_stream


__all__ = list(_gridmet_mod.__all__) + [
    "_open_gridmet_streaming",
    "_open_gridmet_download",
]
