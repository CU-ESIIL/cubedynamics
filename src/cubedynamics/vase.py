"""Time-varying vase polygons and masking utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

import numpy as np
import xarray as xr
from shapely.geometry import Point, Polygon
from shapely.prepared import prep

TimeLike = Union[np.datetime64, float, int]


@dataclass
class VaseSection:
    """Single cross-section of a vase at a given time.

    The polygon is defined in `(x, y)` space while ``time`` is a separate axis,
    allowing the same geometry vocabulary across cubes. Sections can be listed
    in any order; ``VaseDefinition`` will sort them by time.
    """

    time: TimeLike
    polygon: Polygon


@dataclass
class VaseDefinition:
    """Collection of vase sections with interpolation rules.

    The sections describe how a 2-D polygon cross-section should evolve through
    time, creating a 3-D "vase volume" once lofted across the cube. ``interp``
    controls whether polygons are snapped to the nearest timestamp or
    interpolated vertex-by-vertex (when shapes share the same vertex layout).
    """

    sections: List[VaseSection]
    interp: str = "nearest"

    def __post_init__(self) -> None:
        if not self.sections:
            raise ValueError("VaseDefinition requires at least one VaseSection")

        for sec in self.sections:
            if not isinstance(sec.polygon, Polygon):
                raise TypeError("Each section polygon must be a shapely Polygon")
            if not sec.polygon.is_valid:
                raise ValueError("Polygon provided in VaseSection is not valid")

        self.sections = sorted(self.sections, key=lambda s: s.time)

    def sorted_sections(self) -> "VaseDefinition":
        """Return a new VaseDefinition with sections sorted by time."""

        sorted_secs = sorted(self.sections, key=lambda s: s.time)
        return VaseDefinition(sorted_secs, interp=self.interp)


def _polygon_at_time(vase: VaseDefinition, t: TimeLike) -> Polygon:
    """Return the polygon cross-section for a target time ``t``.

    For ``nearest`` interpolation the polygon from the nearest section is
    returned. For ``linear`` interpolation, polygons are interpolated vertex by
    vertex between the bracketing sections. When ``t`` is outside the provided
    time range, the nearest section polygon is used. ``t`` can be numeric or
    datetime-like, matching the cube's time coordinate type.
    """

    vase_sorted = vase.sorted_sections()
    sections = vase_sorted.sections
    times = np.array([sec.time for sec in sections])

    if vase_sorted.interp not in {"nearest", "linear"}:
        raise ValueError("interp must be either 'nearest' or 'linear'")

    if vase_sorted.interp == "nearest" or len(sections) == 1:
        idx = int(np.abs(times - t).argmin())
        return sections[idx].polygon

    # linear interpolation
    if t <= times[0]:
        return sections[0].polygon
    if t >= times[-1]:
        return sections[-1].polygon

    idx_upper = int(np.searchsorted(times, t, side="right"))
    idx_lower = idx_upper - 1
    t0 = times[idx_lower]
    t1 = times[idx_upper]
    sec0 = sections[idx_lower].polygon
    sec1 = sections[idx_upper].polygon

    coords0 = np.asarray(sec0.exterior.coords)
    coords1 = np.asarray(sec1.exterior.coords)
    if coords0.shape != coords1.shape:
        raise ValueError("Polygons for linear interpolation must share vertex layout")

    ratio = float((t - t0) / (t1 - t0)) if t1 != t0 else 0.0
    interp_coords = coords0 + ratio * (coords1 - coords0)
    return Polygon(interp_coords)


def build_vase_mask(
    cube: xr.DataArray,
    vase: VaseDefinition,
    time_dim: str = "time",
    y_dim: str = "y",
    x_dim: str = "x",
) -> xr.DataArray:
    """Build a boolean mask for voxels inside a time-varying vase.

    A **vase volume** is formed by lofting time-stamped polygons through the
    cube's time axis. This helper evaluates the appropriate polygon for each
    time coordinate and marks `(y, x)` locations that fall inside it.

    Notes
    -----
    - The mask matches ``cube`` shape over ``(time, y, x)`` and carries the name
      ``"vase_mask"``.
    - Computation streams over time slices using coordinate arrays only (no
      ``cube.values``), keeping memory use low and working with dask-backed
      cubes or ``VirtualCube`` sources.
    """

    for dim in (time_dim, y_dim, x_dim):
        if dim not in cube.dims:
            raise ValueError(f"Dimension {dim!r} not found in cube dims: {cube.dims}")

    times = cube.coords[time_dim].values
    ys = cube.coords[y_dim].values
    xs = cube.coords[x_dim].values

    mask_slices = []
    for t in times:
        polygon = _polygon_at_time(vase, t)
        prepared = prep(polygon)
        slice_mask = np.zeros((len(ys), len(xs)), dtype=bool)
        for j, y in enumerate(ys):
            for k, x in enumerate(xs):
                pt = Point(x, y)
                slice_mask[j, k] = prepared.intersects(pt)
        mask_slices.append(slice_mask)

    mask_np = np.stack(mask_slices, axis=0)
    mask = xr.DataArray(
        data=mask_np,
        coords={time_dim: cube.coords[time_dim], y_dim: cube.coords[y_dim], x_dim: cube.coords[x_dim]},
        dims=(time_dim, y_dim, x_dim),
        name="vase_mask",
    )
    mask.attrs["description"] = "Boolean mask for vase volume"
    return mask
