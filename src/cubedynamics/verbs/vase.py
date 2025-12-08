from __future__ import annotations

import xarray as xr

from ..vase import VaseDefinition, build_vase_mask
from .plot import plot as plot_verb


def vase_mask(
    cube: xr.DataArray,
    vase: VaseDefinition,
    time_dim: str = "time",
    y_dim: str = "y",
    x_dim: str = "x",
) -> xr.DataArray:
    """Compute a boolean vase mask for a time-varying polygon hull.

    This verb wraps :func:`cubedynamics.vase.build_vase_mask` so it can be used
    inline with ``pipe(...)``. It only inspects coordinate arrays and streams
    over time slices, leaving dask-backed cubes lazy.

    Parameters match the cube's dimension names and default to ``("time", "y", "x")``.
    """
    return build_vase_mask(
        cube,
        vase,
        time_dim=time_dim,
        y_dim=y_dim,
        x_dim=x_dim,
    )


def vase_extract(
    cube: xr.DataArray,
    vase: VaseDefinition,
    time_dim: str = "time",
    y_dim: str = "y",
    x_dim: str = "x",
) -> xr.DataArray:
    """Mask a cube so that values outside the vase become ``NaN``.

    Under the hood this computes the same boolean mask as :func:`vase_mask`
    (via :func:`cubedynamics.vase.build_vase_mask`) and applies ``cube.where``
    to preserve laziness. Use it when you want a cube restricted to the vase
    volume while keeping the streaming-first pipeline intact.
    """
    mask = build_vase_mask(
        cube,
        vase,
        time_dim=time_dim,
        y_dim=y_dim,
        x_dim=x_dim,
    )
    da_out = cube.where(mask)

    # Attach the vase definition so plotting helpers can auto-detect it later
    da_out.attrs["vase"] = vase

    return da_out


def vase(vase=None, outline: bool = True, **plot_kwargs):
    """High-level vase plotting verb.

    Usage
    -----
    >>> pipe(cube) | v.vase()
    >>> pipe(cube) | v.vase(vase=my_vase_def)
    >>> pipe(cube) | v.vase(elev=45, azim=35)

    Parameters
    ----------
    vase : VaseDefinition, optional
        If provided, attach this VaseDefinition to ``attrs["vase"]`` and use it
        to build the vase mask. If not provided, an existing ``attrs["vase"]``
        is used.
    outline : bool, default True
        If True, keep the ``attrs["vase"]`` metadata so the downstream plot verb
        can render a vase outline overlay. When False, the cube is still
        restricted to the vase volume but the overlay is suppressed.
    **plot_kwargs :
        Additional keyword arguments forwarded to the underlying ``v.plot``
        implementation (e.g., ``elev``, ``azim``, ``alpha``, etc.).
    """

    def _inner(da):
        # Attach vase definition if provided
        if vase is not None:
            da = da.copy()
            da.attrs["vase"] = vase

        # Ensure we have a vase to work with
        if "vase" not in da.attrs:
            raise ValueError(
                "v.vase() requires a VaseDefinition, either via the `vase=` argument "
                "or stored on the DataArray as attrs[\"vase\"]."
            )

        # Apply mask using existing helper
        masked = vase_extract(da, da.attrs["vase"])

        # Optionally suppress vase overlay while keeping the mask
        if not outline:
            masked = masked.copy()
            masked.attrs.pop("vase", None)

        # Delegate to standard plot verb
        return plot_verb(**plot_kwargs)(masked)

    return _inner
