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
        Name for the returned condition Dataset.

    Returns
    -------
    callable
        Pipe-ready verb producing a condition Dataset containing Boolean
        ``state``. Boolean overlap has no implicit magnitude or threshold.

    Notes
    -----
    ``overlap`` does not perform vector intersection and does not establish
    causation or risk. It only records where two aligned conditions are true.
    """

    right = _select_state(other, variable=right_variable, side="right")
    right_condition = _condition_name(other, right)

    def _op(obj: xr.DataArray | xr.Dataset) -> xr.Dataset:
        left = _select_state(obj, variable=left_variable, side="left")
        aligned_left, aligned_right = _align_exact(left, right)

        conjunction = (aligned_left.astype(bool) & aligned_right.astype(bool)).rename(name)
        conjunction.attrs = {
            "long_name": name.replace("_", " "),
            "semantic_name": name,
            "semantic_kind": "condition",
            "semantic_category": "state",
            "semantic_units": "boolean",
            "condition_operation": "aligned_boolean_overlap",
            "left_condition": _condition_name(obj, left),
            "right_condition": right_condition,
            "left_variable": str(left.name or left_variable or "value"),
            "right_variable": str(right.name or right_variable or "value"),
            "alignment": "exact",
        }
        result = xr.Dataset({"state": conjunction})
        result.attrs.update(conjunction.attrs)
        result.attrs.update({"analysis": "state_cube", "state_name": name})
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


def _condition_name(obj: xr.DataArray | xr.Dataset, selected: xr.DataArray) -> str:
    attrs = getattr(obj, "attrs", {}) or {}
    return str(
        attrs.get("semantic_name")
        or attrs.get("state_name")
        or selected.attrs.get("semantic_name")
        or selected.name
        or "condition"
    )


def _alignment_kind(dim: Hashable, left: xr.DataArray, right: xr.DataArray) -> str:
    name = str(dim).casefold()
    if name in {"time", "t", "date", "datetime"}:
        return "temporal"
    for obj in (left, right):
        coord = obj.coords.get(dim)
        if coord is not None and getattr(coord.dtype, "kind", None) == "M":
            return "temporal"
    if name in {"x", "y", "lon", "lat", "longitude", "latitude"}:
        return "spatial"
    return "dimension"


def _align_exact(
    left: xr.DataArray,
    right: xr.DataArray,
) -> tuple[xr.DataArray, xr.DataArray]:
    """Normalize harmless axis order and reject every coordinate mismatch."""

    if set(left.dims) != set(right.dims):
        raise ValueError(
            "overlap dimension names differ: "
            f"left {left.dims!r}, right {right.dims!r}. "
            "Align or rename dimensions explicitly before combining them."
        )
    if right.dims != left.dims:
        right = right.transpose(*left.dims)

    for dim in left.dims:
        if left.sizes[dim] != right.sizes[dim] or not left.get_index(dim).equals(
            right.get_index(dim)
        ):
            kind = _alignment_kind(dim, left, right)
            if kind == "temporal":
                detail = f"temporal coordinates differ along {str(dim)!r}"
            elif kind == "spatial":
                detail = f"spatial coordinates differ along {str(dim)!r}"
            else:
                detail = f"coordinates differ along dimension {str(dim)!r}"
            raise ValueError(
                f"overlap {detail}; exact coordinate alignment is required. "
                "Align or reproject the inputs explicitly before combining them."
            )

    return xr.align(left, right, join="exact")


__all__ = ["overlap"]
