"""General verbs for combining aligned scientific state cubes."""

from __future__ import annotations

from typing import Hashable

import xarray as xr

from ..grammar import infer_semantic_state


def overlap(
    other: xr.DataArray | xr.Dataset,
    *,
    left_variable: Hashable | None = None,
    right_variable: Hashable | None = None,
    name: str = "overlap",
):
    """Return a verb that finds coincident truth in two aligned state cubes.

    This is a deliberately narrow raster operation. Both inputs must already
    use exactly the same coordinates; the verb will not silently reproject,
    resample, or discard unmatched cells. Dataset inputs use their ``state``
    variable by default, which makes outputs from :func:`threshold_state` and
    :func:`quantile_state` compose directly.

    Parameters
    ----------
    other : xr.DataArray | xr.Dataset
        The second aligned boolean or state cube.
    left_variable, right_variable : hashable, optional
        Variables to select from Dataset inputs. If omitted, ``state`` is used
        when present; otherwise a single-variable Dataset is accepted.
    name : str, default "overlap"
        Name for the returned boolean DataArray.

    Returns
    -------
    callable
        Pipe-ready verb producing a boolean DataArray.

    Notes
    -----
    ``overlap`` does not perform vector intersection and does not establish
    causation or risk. It only records where two aligned conditions are true.
    """

    right = _select_state(other, variable=right_variable, side="right")

    def _op(obj: xr.DataArray | xr.Dataset) -> xr.DataArray:
        left = _select_state(obj, variable=left_variable, side="left")
        try:
            aligned_left, aligned_right = xr.align(left, right, join="exact")
        except ValueError as exc:
            raise ValueError(
                "overlap requires identical dimensions and coordinates; align or "
                "reproject the inputs explicitly before combining them"
            ) from exc

        result = (aligned_left.astype(bool) & aligned_right.astype(bool)).rename(name)
        result.attrs = {
            "analysis": "aligned_boolean_overlap",
            "semantic_name": name,
            "semantic_kind": "condition",
            "semantic_category": "state",
            "semantic_units": "boolean",
            "long_name": name.replace("_", " "),
            "left_variable": str(left.name or left_variable or "value"),
            "right_variable": str(right.name or right_variable or "value"),
            "alignment": "exact",
        }
        return result

    _op._cd_semantic_context = {"other": infer_semantic_state(other)}
    return _op


def _select_state(
    obj: xr.DataArray | xr.Dataset,
    *,
    variable: Hashable | None,
    side: str,
) -> xr.DataArray:
    if isinstance(obj, xr.DataArray):
        if variable is not None:
            raise ValueError(f"{side}_variable is only valid for Dataset inputs")
        return obj
    if not isinstance(obj, xr.Dataset):
        raise TypeError("overlap requires xarray DataArray or Dataset inputs")

    selected = variable
    if selected is None and "state" in obj.data_vars:
        selected = "state"
    if selected is None and len(obj.data_vars) == 1:
        selected = next(iter(obj.data_vars))
    if selected is None:
        raise ValueError(
            f"overlap requires {side}_variable= for a Dataset without one 'state' variable"
        )
    if selected not in obj.data_vars:
        raise ValueError(
            f"Variable {selected!r} is not present in the {side} Dataset: "
            f"{list(obj.data_vars)!r}"
        )
    return obj[selected]


__all__ = ["overlap"]
