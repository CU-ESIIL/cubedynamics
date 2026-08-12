"""Project-owned verbs for the custom-verb vignette."""

from __future__ import annotations

import xarray as xr


def heat_stress(*, threshold: float = 35.0):
    """Return a verb classifying values at or above ``threshold``.

    The state and exceedance magnitude are kept separate so downstream project
    verbs can operate on either the event occurrence or its severity.
    """

    def _op(cube: xr.DataArray) -> xr.Dataset:
        if not isinstance(cube, xr.DataArray):
            raise TypeError("heat_stress expects an xarray.DataArray")
        if "time" not in cube.dims:
            raise ValueError("heat_stress requires a 'time' dimension")

        state = (cube >= threshold).rename("state")
        magnitude = (cube - threshold).where(state, 0).rename("magnitude")
        result = xr.Dataset({"state": state, "magnitude": magnitude})
        result.attrs.update(cube.attrs)
        result.attrs.update(
            {
                "project_verb": "heat_stress",
                "threshold": float(threshold),
            }
        )
        return result

    return _op


__all__ = ["heat_stress"]
