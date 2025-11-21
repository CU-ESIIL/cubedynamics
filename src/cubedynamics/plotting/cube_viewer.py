from __future__ import annotations

import base64
import io
from typing import Any, Dict, Optional, TYPE_CHECKING

import numpy as np
import pandas as pd
import xarray as xr
from matplotlib import colormaps, colors as mcolors
from PIL import Image
from IPython.display import IFrame

from cubedynamics.utils import _infer_time_y_x_dims, write_css_cube_static
from cubedynamics.plotting.progress import _CubeProgress

if TYPE_CHECKING:  # pragma: no cover - typing only
    from cubedynamics.plotting.cube_plot import CoordCube, CubeAnnotation


def cube_from_dataarray(
    da: xr.DataArray,
    out_html: str = "cube_da.html",
    cmap: str = "viridis",
    size_px: int = 260,
    thin_time_factor: int = 4,
    title: str | None = None,
    time_label: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    *,
    legend_title: str | None = None,
    theme: Any | None = None,
    show_progress: bool = True,
    progress_style: str = "bar",
    time_dim: str | None = None,
    fill_limits: tuple[float, float] | None = None,
    fill_breaks: list[float] | None = None,
    fill_labels: list[str] | None = None,
    coord: "CoordCube" | None = None,
    annotations: list["CubeAnnotation"] | None = None,
    return_html: bool = False,
    show_legend: bool = True,
):
    """
    Build an interactive 3D CSS cube from a (time, y, x) DataArray.

    - Infers time/y/x dims robustly.
    - Optionally thins the time axis for very long series.
    - Extracts six oriented faces (front/back spatial, time walls, top/bottom)
      as NumPy arrays.
    - Encodes them as PNGs and writes a static HTML file with a CSS cube that
      includes axis labels and a title.
    - Injects colorbar metadata and a simple loading overlay.

    Returns
    -------
    iframe : IPython.display.IFrame
        An iframe pointing to the generated HTML, suitable for Jupyter notebooks.

    Additional Parameters
    ---------------------
    title, time_label, x_label, y_label : str, optional
        Text used for the viewer title and axis annotations. Defaults fall back to
        the DataArray ``name`` and dimension names when omitted.
    """

    # ---------------------
    # 1. Infer dims safely
    # ---------------------
    if time_dim:
        if time_dim not in da.dims:
            raise ValueError(f"Specified time_dim '{time_dim}' not found in DataArray dims {da.dims}")
        remaining_dims = [d for d in da.dims if d != time_dim]
        if len(remaining_dims) < 2:
            raise ValueError("Need at least two spatial dimensions when providing time_dim")
        t_dim = time_dim
        y_dim, x_dim = remaining_dims[-2], remaining_dims[-1]
    else:
        t_dim, y_dim, x_dim = _infer_time_y_x_dims(da)
    if t_dim is None:
        raise ValueError("cube_from_dataarray expects a time dimension for 3D cubes.")
    da = da.transpose(t_dim, y_dim, x_dim)

    nt, ny, nx = da.sizes[t_dim], da.sizes[y_dim], da.sizes[x_dim]

    # ---------------------------------------
    # 1b. Build axis labels and tick helpers
    # ---------------------------------------
    time_tick_count = getattr(coord, "time_ticks", 4) if coord is not None else 4
    space_tick_count = getattr(coord, "space_ticks", 3) if coord is not None else 3
    time_format = getattr(coord, "time_format", "%Y-%m-%d") if coord is not None else "%Y-%m-%d"

    time_ticks = _infer_axis_ticks(da, t_dim, n_ticks=time_tick_count, time_format=time_format)
    x_ticks = _infer_axis_ticks(da, x_dim, n_ticks=space_tick_count)
    y_ticks = _infer_axis_ticks(da, y_dim, n_ticks=space_tick_count)

    axis_info = {
        "time": {
            "name": _guess_axis_name(da, t_dim),
            "range": _axis_range_from_ticks(time_ticks),
            "ticks": [label for _, label in time_ticks],
        },
        "x": {
            "name": _guess_axis_name(da, x_dim),
            "range": _axis_range_from_ticks(x_ticks),
            "ticks": [label for _, label in x_ticks],
        },
        "y": {
            "name": _guess_axis_name(da, y_dim),
            "range": _axis_range_from_ticks(y_ticks),
            "ticks": [label for _, label in y_ticks],
        },
    }

    # ----------------------------
    # 2. Reduce time if needed
    # ----------------------------
    t_indices = list(range(0, nt, max(1, thin_time_factor)))
    nt_eff = len(t_indices)

    progress = _CubeProgress(total=nt_eff, enabled=show_progress, style=progress_style)

    # ---------------------------------
    # 3. Extract raw numpy face arrays
    # ---------------------------------
    front_spatial: Optional[np.ndarray] = None
    back_spatial: Optional[np.ndarray] = None
    left_time_y = np.zeros((ny, nt_eff), dtype="float32")
    right_time_y = np.zeros((ny, nt_eff), dtype="float32")
    top_time_x = np.zeros((nx, nt_eff), dtype="float32")
    bottom_time_x = np.zeros((nx, nt_eff), dtype="float32")

    for idx, t_idx in enumerate(t_indices):
        frame = da.isel({t_dim: t_idx}).transpose(y_dim, x_dim)
        arr = frame.values  # 2D slice only

        if idx == 0:
            back_spatial = np.flip(arr, axis=1)
        front_spatial = arr

        left_time_y[:, idx] = arr[:, 0]
        right_time_y[:, idx] = arr[:, -1]
        top_time_x[:, idx] = arr[-1, :]
        bottom_time_x[:, idx] = arr[0, :]

        progress.step()

    progress.done()

    assert front_spatial is not None and back_spatial is not None

    # -----------------------------
    # 4. Merge values for vmin/vmax
    # -----------------------------
    all_vals = np.concatenate(
        [
            front_spatial.astype("float32").ravel(),
            back_spatial.astype("float32").ravel(),
            left_time_y.astype("float32").ravel(),
            right_time_y.astype("float32").ravel(),
            top_time_x.astype("float32").ravel(),
            bottom_time_x.astype("float32").ravel(),
        ]
    )

    if fill_limits is not None:
        vmin, vmax = fill_limits
    else:
        mask = np.isfinite(all_vals)
        if mask.any():
            vmin = float(np.nanpercentile(all_vals[mask], 2))
            vmax = float(np.nanpercentile(all_vals[mask], 98))
        else:
            vmin, vmax = -1.0, 1.0

        if vmin == vmax:
            vmin -= 1.0
            vmax += 1.0

    # --------------------------------
    # 5. Helper to encode NumPy → PNG
    # --------------------------------
    def arr_to_b64(arr: np.ndarray) -> str:
        arr = arr.astype("float32")
        mask = np.isfinite(arr)
        if mask.any():
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        else:
            norm = mcolors.Normalize(vmin=-1, vmax=1)
        cmap_obj = colormaps.get_cmap(cmap)
        rgba = cmap_obj(norm(arr))
        img = (rgba * 255).astype("uint8")
        buf = io.BytesIO()
        Image.fromarray(img).save(buf, format="PNG", compress_level=1)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    front_b64 = arr_to_b64(front_spatial)
    back_b64 = arr_to_b64(back_spatial)
    left_b64 = arr_to_b64(left_time_y)
    right_b64 = arr_to_b64(right_time_y)
    top_b64 = arr_to_b64(top_time_x)
    bottom_b64 = arr_to_b64(bottom_time_x)

    # -------------------------
    # 6. Build cube face dict
    # -------------------------
    faces = {
        "front": f"data:image/png;base64,{front_b64}",
        "back": f"data:image/png;base64,{back_b64}",
        "left": f"data:image/png;base64,{left_b64}",
        "right": f"data:image/png;base64,{right_b64}",
        "top": f"data:image/png;base64,{top_b64}",
        "bottom": f"data:image/png;base64,{bottom_b64}",
    }

    # -------------------------
    # 7. Render cube HTML
    # -------------------------
    # Build a simple colorbar that matches the selected colormap
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    grad_rgba = colormaps.get_cmap(cmap)(gradient)
    grad_img = (grad_rgba * 255).astype("uint8")
    colorbar_b64 = None
    if show_legend:
        buf_cb = io.BytesIO()
        Image.fromarray(grad_img).save(buf_cb, format="PNG")
        colorbar_b64 = base64.b64encode(buf_cb.getvalue()).decode("ascii")

    derived_title = title or da.name or f"{t_dim} × {y_dim} × {x_dim} cube"
    legend_title = legend_title or derived_title
    if not show_legend:
        legend_title = None

    def _axis_label(axis_key: str, fallback: str) -> str:
        axis_meta = axis_info.get(axis_key, {})
        axis_name = axis_meta.get("name") or fallback
        axis_range = axis_meta.get("range")
        if axis_range:
            return f"{axis_name}: {axis_range}"
        return axis_name

    axis_time_label = time_label or _axis_label("time", t_dim or "time")
    axis_x_label = x_label or _axis_label("x", x_dim)
    axis_y_label = y_label or _axis_label("y", y_dim)

    css_vars: Dict[str, str] = {
        "--cube-bg-color": getattr(theme, "bg_color", "#000"),
        "--cube-panel-color": getattr(theme, "panel_color", "#000"),
        "--cube-shadow-strength": str(getattr(theme, "shadow_strength", 0.2)),
        "--cube-title-color": getattr(theme, "title_color", "#f7f7f7"),
        "--cube-axis-color": getattr(theme, "axis_color", "#f7f7f7"),
        "--cube-legend-color": getattr(theme, "legend_color", "#f7f7f7"),
        "--cube-title-font-size": f"{getattr(theme, 'title_font_size', 18)}px",
        "--cube-axis-font-size": f"{getattr(theme, 'title_font_size', 18) * getattr(theme, 'axis_scale', 0.6)}px",
        "--cube-legend-font-size": f"{getattr(theme, 'title_font_size', 18) * getattr(theme, 'legend_scale', 0.55)}px",
        "--cube-font-family": getattr(
            theme,
            "title_font_family",
            "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        ),
    }

    write_css_cube_static(
        out_html=out_html,
        size_px=size_px,
        faces=faces,
        colorbar_b64=colorbar_b64,
        title=derived_title,
        time_label=axis_time_label,
        x_label=axis_x_label,
        y_label=axis_y_label,
        legend_title=legend_title,
        css_vars=css_vars,
        colorbar_breaks=fill_breaks,
        colorbar_labels=fill_labels,
        coord=coord,
        annotations=annotations,
        axis_info=axis_info,
    )

    # -------------------------
    # 8. Inject colorbar + loader
    # -------------------------
    with open(out_html, "r") as f:
        html = f.read()

    # Add data attributes + loading overlay + JS to hide it on load.
    injection = f'''
<body data-cb-min="{vmin:.2f}" data-cb-max="{vmax:.2f}" data-rot-x="{getattr(coord, 'elev', 15.0)}" data-rot-y="{getattr(coord, 'azim', -25.0)}" data-zoom="{getattr(coord, 'zoom', 1.0)}">
  <div id="cube-loading-overlay">
    <div class="cube-spinner"></div>
    <div class="cube-loading-text">Loading cube…</div>
  </div>
  <script>
    window.addEventListener("load", function() {{
      var overlay = document.getElementById("cube-loading-overlay");
      if (overlay) overlay.style.display = "none";
    }});
  </script>
'''

    # Simple CSS for overlay + spinner
    css_injection = """
<style>
#cube-loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  z-index: 9999;
  font-family: system-ui, sans-serif;
}

.cube-spinner {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 6px solid rgba(255,255,255,0.3);
  border-top-color: white;
  animation: cube-spin 0.9s linear infinite;
  margin-bottom: 12px;
}

.cube-loading-text {
  color: white;
  font-size: 14px;
}

@keyframes cube-spin {
  to { transform: rotate(360deg); }
}
</style>
"""

    # Inject CSS right after <head> if possible
    if "<head>" in html:
        html = html.replace("<head>", "<head>" + css_injection, 1)
    else:
        # Fallback: prepend CSS
        html = css_injection + html

    # Replace first <body> tag with our enhanced body tag
    html = html.replace("<body>", injection, 1)

    with open(out_html, "w") as f:
        f.write(html)

    print(f"✓ Cube viewer written to: {out_html}")
    if return_html:
        return html
    return IFrame(out_html, width=900, height=900)


def _guess_axis_name(da: xr.DataArray, dim: str) -> str:
    name = str(dim).lower()
    if "lat" in name:
        return "latitude"
    if "lon" in name or "lng" in name:
        return "longitude"
    return dim


def _infer_axis_ticks(
    da: xr.DataArray, dim: str, n_ticks: int = 3, time_format: str = "%Y-%m-%d"
):
    if dim not in da.dims:
        return []
    coords = da.coords[dim].values
    if coords.size == 0:
        return []

    idxs = np.linspace(0, coords.size - 1, num=min(n_ticks, coords.size), dtype=int)
    values = coords[idxs]

    if np.issubdtype(values.dtype, np.datetime64):
        times = pd.to_datetime(values)
        labels = [t.strftime(time_format) for t in times]
    else:
        units = da.coords[dim].attrs.get("units", "") if dim in da.coords else ""
        units_str = f" {units}" if units else ""
        labels = [f"{float(v):.2f}{units_str}" for v in values]

    return list(zip(values, labels))


def _axis_range_from_ticks(ticks):
    if not ticks:
        return ""
    if len(ticks) == 1:
        return ticks[0][1]
    return f"{ticks[0][1]} \u2192 {ticks[-1][1]}"


__all__ = [
    "cube_from_dataarray",
    "_guess_axis_name",
    "_infer_axis_ticks",
    "_axis_range_from_ticks",
]

