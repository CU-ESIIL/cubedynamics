"""I/O helpers for pipe chains."""

from __future__ import annotations

import xarray as xr

from ..serialization import prepare_netcdf_output


def to_netcdf(path: str, **to_netcdf_kwargs):
    """Factory for a pipeable, metadata-safe NetCDF side-effect operation.

    A shallow write-only copy receives deterministic NetCDF-safe attributes.
    Boolean state variables are encoded as int8 with flag metadata because
    NetCDF has no native Boolean type. The original pipe value is returned
    unchanged.
    """

    def _inner(da: xr.DataArray | xr.Dataset):
        prepared = prepare_netcdf_output(da)
        prepared.to_netcdf(path, **to_netcdf_kwargs)
        return da

    return _inner


__all__ = ["to_netcdf"]
