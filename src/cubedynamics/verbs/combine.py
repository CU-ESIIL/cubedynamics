"""General verbs for combining aligned scientific state cubes."""

from __future__ import annotations

from typing import Hashable

import xarray as xr

from ..grammar import infer_semantic_state
from ..temporal import TemporalAlignmentReport, compare_temporal_support


_TEMPORAL_POLICIES = {"labels", "require_exact_support"}


def align_time(
    other: xr.DataArray | xr.Dataset,
    *,
    mode: str = "require_exact_support",
    time_dim: str = "time",
):
    """Return a verb that records an explicit temporal-alignment decision.

    ``mode='labels'`` acknowledges pairing by unchanged coordinate labels even
    when observation supports differ or are unknown.  ``mode='require_exact_support'``
    requires both exact labels and identical, known support metadata.  Neither
    mode shifts, resamples, interpolates, aggregates, or truncates either input.
    """

    policy = _validate_temporal_policy(mode)

    def _op(obj: xr.DataArray | xr.Dataset) -> xr.DataArray | xr.Dataset:
        if not isinstance(obj, (xr.DataArray, xr.Dataset)):
            raise TypeError("align_time requires xarray DataArray or Dataset inputs")
        report = compare_temporal_support(obj, other, time_dim=time_dim)
        _require_exact_time_labels(report, caller="align_time")
        _enforce_temporal_policy(report, policy, caller="align_time")
        result = obj.copy(deep=False)
        attrs = dict(obj.attrs)
        attrs.update(_alignment_attrs(report, policy))
        attrs.update({"analysis": "temporal_alignment", "temporal_alignment_mode": policy})
        result.attrs = attrs
        return result

    _op._cd_semantic_context = {"other": infer_semantic_state(other)}
    return _op


def overlap(
    other: xr.DataArray | xr.Dataset,
    *,
    left_variable: Hashable | None = None,
    right_variable: Hashable | None = None,
    name: str = "overlap",
    temporal_alignment: str | None = None,
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
    temporal_alignment : {"labels", "require_exact_support"}, optional
        Explicit temporal-support policy. Known, different supports require a
        choice. ``"labels"`` pairs unchanged labels and records the caveat;
        ``"require_exact_support"`` rejects different or unknown support.

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

    policy = (
        _validate_temporal_policy(temporal_alignment)
        if temporal_alignment is not None
        else None
    )
    right = _select_state(other, variable=right_variable, side="right")
    right_condition = _condition_name(other, right)

    def _op(obj: xr.DataArray | xr.Dataset) -> xr.Dataset:
        left = _select_state(obj, variable=left_variable, side="left")
        aligned_left, aligned_right = _align_exact(left, right)
        report = compare_temporal_support(obj, other)
        if report.coordinates not in {"exact", "absent"}:
            # _align_exact normally catches this first; retain an independent
            # semantic diagnostic for nonstandard datetime dimension names.
            _require_exact_time_labels(report, caller="overlap")
        if report.temporal_support == "different" and policy is None:
            raise ValueError(
                "overlap inputs have exact time labels but different known observation "
                "intervals. Choose temporal_alignment='labels' to pair the existing "
                "labels with a recorded caveat, or 'require_exact_support' to reject "
                "the mismatch. CubeDynamics will not shift or resample either input."
            )
        if policy is not None:
            _enforce_temporal_policy(report, policy, caller="overlap")

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
        conjunction.attrs.update(_alignment_attrs(report, policy or "implicit"))
        result = xr.Dataset({"state": conjunction})
        result.attrs.update(getattr(obj, "attrs", {}) or {})
        result.attrs.update(conjunction.attrs)
        result.attrs.update({"analysis": "state_cube", "state_name": name})
        if report.temporal_support != "exact" and report.coordinates != "absent":
            result.attrs.update(
                {
                    "temporal_support_known": 0,
                    "temporal_support_type": "composite",
                    "temporal_label_convention": "paired_by_labels",
                }
            )
        return result

    _op._cd_semantic_context = {"other": infer_semantic_state(other)}
    return _op


def _validate_temporal_policy(value: str | None) -> str:
    policy = str(value)
    if policy not in _TEMPORAL_POLICIES:
        choices = ", ".join(sorted(_TEMPORAL_POLICIES))
        raise ValueError(f"temporal alignment mode must be one of: {choices}")
    return policy


def _require_exact_time_labels(report: TemporalAlignmentReport, *, caller: str) -> None:
    if report.coordinates == "absent":
        raise ValueError(f"{caller} requires both inputs to have a time coordinate")
    if report.coordinates != "exact":
        raise ValueError(
            f"{caller} time-coordinate labels differ; exact labels are required. "
            "CubeDynamics will not shift, resample, interpolate, or truncate them."
        )


def _enforce_temporal_policy(
    report: TemporalAlignmentReport,
    policy: str,
    *,
    caller: str,
) -> None:
    if policy == "labels":
        return
    if report.temporal_support == "unknown":
        raise ValueError(
            f"{caller} mode='require_exact_support' cannot verify observation intervals "
            "because temporal-support metadata is unknown for one or both inputs."
        )
    if report.temporal_support != "exact":
        raise ValueError(
            f"{caller} mode='require_exact_support' found different known observation "
            "intervals. No timestamps or values were changed."
        )


def _alignment_attrs(report: TemporalAlignmentReport, policy: str) -> dict[str, object]:
    support_status = (
        "not_applicable" if report.coordinates == "absent" else report.temporal_support
    )
    return {
        "temporal_alignment_coordinates": report.coordinates,
        "temporal_alignment_support": support_status,
        "temporal_alignment_policy": policy,
        "temporal_alignment_left_source": report.left_source or "not declared",
        "temporal_alignment_right_source": report.right_source or "not declared",
        "temporal_alignment_note": _alignment_note(report, policy),
        "temporal_alignment_modified_coordinates": 0,
        "temporal_alignment_modified_values": 0,
    }


def _alignment_note(report: TemporalAlignmentReport, policy: str) -> str:
    left = report.left_source or "The left input"
    right = report.right_source or "the right input"
    if report.temporal_support == "different":
        return (
            f"{left} and {right} have matching date labels but different declared "
            f"observation intervals; policy {policy!r} does not make those intervals equal."
        )
    if report.temporal_support == "unknown":
        return (
            f"{left} and {right} have matching date labels, but temporal-support "
            "compatibility could not be verified."
        )
    return f"{left} and {right} have exact time labels and declared observation support."


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


__all__ = ["align_time", "overlap"]
