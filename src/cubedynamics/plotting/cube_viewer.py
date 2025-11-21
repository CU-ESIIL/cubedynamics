from __future__ import annotations

import base64
import io
from typing import Any, Dict, Optional, TYPE_CHECKING

import numpy as np
import pandas as pd
import xarray as xr
from matplotlib import colormaps, colors as mcolors
from PIL import Image
from IPython.display import HTML, IFrame, display, update_display

from cubedynamics.utils import _infer_time_y_x_dims
from cubedynamics.plotting.progress import _CubeProgress

if TYPE_CHECKING:  # pragma: no cover - typing only
    from cubedynamics.plotting.cube_plot import CoordCube, CubeAnnotation


def _apply_vase_tint(rgb_arr: np.ndarray, mask_2d: np.ndarray, color_rgb: tuple[int, int, int], alpha: float) -> np.ndarray:
    """
    Apply an overlay color to ``rgb_arr`` wherever ``mask_2d`` is True.

    This mutates a copy of the input and returns the tinted array.
    """

    overlay = np.zeros_like(rgb_arr, dtype=np.float32)
    overlay[..., 0] = color_rgb[0]
    overlay[..., 1] = color_rgb[1]
    overlay[..., 2] = color_rgb[2]

    mask_exp = np.broadcast_to(mask_2d[..., None], rgb_arr.shape)
    blended = rgb_arr.astype(np.float32)
    blended[mask_exp] = (1 - alpha) * blended[mask_exp] + alpha * overlay[mask_exp]
    return blended.astype(np.uint8)


def _colormap_to_rgba(arr: np.ndarray, *, cmap: str, fill_limits: tuple[float, float]) -> np.ndarray:
    arr = arr.astype("float32")
    mask = np.isfinite(arr)
    if mask.any():
        norm = mcolors.Normalize(vmin=fill_limits[0], vmax=fill_limits[1])
    else:
        norm = mcolors.Normalize(vmin=-1, vmax=1)
    cmap_obj = colormaps.get_cmap(cmap)
    rgba = cmap_obj(norm(arr))
    return (rgba * 255).astype("uint8")


def _rgba_to_png_base64(rgba: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(rgba).save(buf, format="PNG", compress_level=1)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _array_to_png_base64(
    arr: np.ndarray, *, cmap: str, fill_limits: tuple[float, float]
) -> str:
    rgba = _colormap_to_rgba(arr, cmap=cmap, fill_limits=fill_limits)
    return _rgba_to_png_base64(rgba)


def _colorbar_labels(breaks, labels) -> str:
    if not breaks:
        return "<span id=\"cb-min\"></span><span id=\"cb-max\"></span>"
    spans = []
    for idx, val in enumerate(breaks):
        label = labels[idx] if labels and idx < len(labels) else f"{val:.2f}"
        spans.append(f"<span class=\"cb-tick\" data-tick=\"{val:.2f}\">{label}</span>")
    return "".join(spans)


def _axis_section(axis: Dict[str, Any] | None) -> str:
    if not axis:
        return ""
    name = axis.get("name")
    if not name:
        return ""
    range_text = axis.get("range") or ""
    ticks = axis.get("ticks") or []
    ticks_html = ""
    if ticks:
        tick_labels = " \u00b7 ".join(str(t) for t in ticks)
        ticks_html = f"<div class='axis-ticks'>{tick_labels}</div>"
    range_html = f"<span class='axis-range'>{range_text}</span>" if range_text else ""
    return (
        "<div class='axis-row'>"
        f"<span class='axis-title'>{name}:</span>"
        f"{range_html}"
        f"{ticks_html}"
        "</div>"
    )


def _build_axis_info_html(axis_info: Dict[str, Any]) -> str:
    axis_rows = [
        _axis_section(axis_info.get("time")),
        _axis_section(axis_info.get("y")),
        _axis_section(axis_info.get("x")),
    ]
    if not any(axis_rows):
        return ""
    return "<div class=\"cube-axis-info\">" + "".join([row for row in axis_rows if row]) + "</div>"


def _build_legend_html(
    *,
    legend_title: str | None,
    colorbar_b64: str | None,
    fill_breaks: list[float] | None,
    fill_labels: list[str] | None,
) -> str:
    if not legend_title or not colorbar_b64:
        return ""
    tick_block = _colorbar_labels(fill_breaks, fill_labels)
    return (
        "<div class=\"cube-legend-panel\">"
        "  <div class=\"cube-legend-card\">"
        f"    <div class=\"colorbar-title\">{legend_title}</div>"
        f"    <div class=\"colorbar-wrapper\"><img class=\"colorbar-img\" src=\"data:image/png;base64,{colorbar_b64}\" alt=\"colorbar\" /></div>"
        f"    <div class=\"colorbar-labels\">{tick_block}</div>"
        "  </div>"
        "</div>"
    )


def _interior_plane_transform(axis: str, index: int, meta: Dict[str, int], size_px: int) -> str:
    half = size_px / 2
    nt = max(meta.get("nt", 1) - 1, 1)
    ny = max(meta.get("ny", 1) - 1, 1)
    nx = max(meta.get("nx", 1) - 1, 1)
    if axis == "time":
        frac = index / nt
        z = -half + frac * size_px
        return f"translate3d(0px, 0px, {z:.2f}px)"
    if axis == "x":
        frac = index / nx
        x_off = -half + frac * size_px
        return f"rotateY(90deg) translateZ({x_off:.2f}px)"
    if axis == "y":
        frac = index / ny
        y_off = -half + frac * size_px
        return f"rotateX(90deg) translateZ({y_off:.2f}px)"
    return ""


def _render_cube_html(
    *,
    front: str,
    back: str,
    left: str,
    right: str,
    top: str,
    bottom: str,
    interior_planes: list[tuple[str, int, str, Dict[str, int]]] | None,
    theme: Dict[str, str],
    coord: "CoordCube" | None,
    legend_html: str,
    title_html: str,
    axes_html: str,
    size_px: int,
    axis_labels: Dict[str, str],
    color_limits: tuple[float, float],
    interior_meta: Dict[str, int],
) -> str:
    half = size_px / 2
    face_style = {
        "front": front,
        "back": back,
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom,
    }
    def _face_css(uri: str) -> str:
        base = "background: rgba(255,255,255,0.05);"
        if uri.lower() == "none":
            return base
        return (
            "background-image: url('{0}'); background-size: cover; "
            "background-position: center;"
        ).format(uri)

    interior_html_parts = []
    if interior_planes:
        for axis, idx, b64, meta in interior_planes:
            transform = _interior_plane_transform(axis, idx, meta or interior_meta, size_px)
            interior_html_parts.append(
                "<div class=\"interior-plane\" "
                f"style=\"transform: {transform}; background-image: url('data:image/png;base64,{b64}');\"></div>"
            )
    interior_html = "".join(interior_html_parts)

    css_vars = " ".join(f"{k}: {v};" for k, v in theme.items())
    elev = getattr(coord, "elev", 15.0)
    azim = getattr(coord, "azim", -25.0)
    zoom = getattr(coord, "zoom", 1.0)

    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <style>
    :root {{
      --cube-size: {size_px}px;
      {css_vars}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 28px 14px 32px 14px;
      width: 100%;
      height: 100%;
      background: var(--cube-bg-color);
      color: var(--cube-axis-color);
      font-family: var(--cube-font-family);
      display: flex;
      align-items: flex-start;
      justify-content: center;
      overflow: hidden;
      user-select: none;
    }}
    .cube-figure {{
      width: min(1180px, 100%);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
    }}
    .cube-title {{
      font-size: var(--cube-title-font-size);
      letter-spacing: 0.04em;
      font-weight: 700;
      text-align: center;
      color: var(--cube-title-color);
      margin-bottom: 4px;
    }}
    .cube-main {{
      width: 100%;
      display: flex;
      justify-content: center;
    }}
    .cube-inner {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
    }}
    .cube-scene {{
      position: relative;
      width: 900px;
      height: 680px;
      display: flex;
      align-items: center;
      justify-content: center;
      perspective: 1600px;
      transform: scale(var(--cube-zoom, 1));
      transform-origin: center center;
      transition: transform 120ms ease-out;
    }}
    #cube {{
      position: relative;
      width: var(--cube-size);
      height: var(--cube-size);
      transform-style: preserve-3d;
      transform: translateZ(0px) rotateX(var(--rotX, 20deg)) rotateY(var(--rotY, -30deg));
    }}
    .face {{
      position: absolute;
      width: var(--cube-size);
      height: var(--cube-size);
      background-size: cover;
      background-position: center;
      border: 1px solid #222;
      box-sizing: border-box;
      background-color: rgba(255,255,255,0.02);
    }}
    #front  {{ transform: translateZ({half}px); {_face_css(face_style['front'])} }}
    #back   {{ transform: rotateY(180deg) translateZ({half}px); {_face_css(face_style['back'])} }}
    #right  {{ transform: rotateY(90deg) translateZ({half}px); {_face_css(face_style['right'])} }}
    #left   {{ transform: rotateY(-90deg) translateZ({half}px); {_face_css(face_style['left'])} }}
    #top    {{ transform: rotateX(90deg) translateZ({half}px); {_face_css(face_style['top'])} }}
    #bottom {{ transform: rotateX(-90deg) translateZ({half}px); {_face_css(face_style['bottom'])} }}
    .interior-plane {{
      position: absolute;
      width: var(--cube-size);
      height: var(--cube-size);
      background-size: cover;
      background-position: center;
      opacity: 0.65;
      mix-blend-mode: normal;
      will-change: transform;
      border: 1px solid rgba(255,255,255,0.08);
    }}
    .cube-outline {{
      position: absolute;
      inset: 0;
      width: var(--cube-size);
      height: var(--cube-size);
      transform-style: preserve-3d;
      border: 1px solid rgba(255,255,255,0.15);
      pointer-events: none;
    }}
    .cube-label {{
      position: absolute;
      font-size: var(--cube-axis-font-size);
      letter-spacing: 0.04em;
      padding: 4px 8px;
      border-radius: 6px;
      border: 1px solid rgba(0,0,0,0.08);
      pointer-events: none;
      color: var(--cube-axis-color);
      background: rgba(255,255,255,0.08);
      transform-style: preserve-3d;
      backdrop-filter: blur(3px);
    }}
    .cube-label-time {{
      transform: translate3d(-44px, 50%, {half}px) rotateY(90deg) rotateX(90deg);
    }}
    .cube-label-y {{
      transform: translate3d({half}px, -46px, 0px) rotateX(90deg);
    }}
    .cube-label-x {{
      transform: translate3d(0px, {half + 14}px, {half}px) rotateY(0deg);
    }}
    .cube-axis-info {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      align-items: center;
      color: var(--cube-axis-color);
      font-size: var(--cube-axis-font-size);
    }}
    .axis-row {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
    }}
    .axis-title {{
      font-weight: 700;
      color: var(--cube-axis-color);
      text-transform: lowercase;
    }}
    .axis-range {{
      opacity: 0.95;
    }}
    .axis-ticks {{
      font-size: calc(var(--cube-axis-font-size) * 0.95);
      opacity: 0.85;
    }}
    .cube-legend-panel {{
      width: 100%;
      display: flex;
      justify-content: center;
      margin-top: 6px;
    }}
    .cube-legend-card {{
      background: #ffffff;
      padding: 8px 12px;
      border-radius: 10px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.08);
      min-width: min(420px, 90%);
    }}
    .colorbar-wrapper {{
      width: 100%;
    }}
    .colorbar-title {{
      font-size: var(--cube-legend-font-size);
      font-weight: 600;
      color: var(--cube-legend-color);
      text-align: center;
      margin-bottom: 6px;
      font-family: var(--cube-font-family);
    }}
    .colorbar-img {{
      width: 100%;
      height: 14px;
      border-radius: 4px;
      border: 1px solid rgba(0,0,0,0.2);
      display: block;
    }}
    .colorbar-labels {{
      width: 100%;
      display: flex;
      justify-content: space-between;
      font-size: var(--cube-legend-font-size);
      margin-top: 6px;
      align-self: center;
      color: var(--cube-legend-color);
      gap: 6px;
    }}
    .cb-tick {{
      flex: 1;
      text-align: center;
    }}
    #cube-loading-overlay {{
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      z-index: 9999;
      font-family: system-ui, sans-serif;
    }}
    .cube-spinner {{
      width: 48px;
      height: 48px;
      border-radius: 50%;
      border: 6px solid rgba(255,255,255,0.3);
      border-top-color: white;
      animation: cube-spin 0.9s linear infinite;
      margin-bottom: 12px;
    }}
    .cube-loading-text {{
      color: white;
      font-size: 14px;
    }}
    @keyframes cube-spin {{
      to {{ transform: rotate(360deg); }}
    }}
  </style>
</head>
<body data-cb-min=\"{color_limits[0]:.2f}\" data-cb-max=\"{color_limits[1]:.2f}\" data-rot-x=\"{elev}\" data-rot-y=\"{azim}\" data-zoom=\"{zoom}\">\n\
  <div id=\"cube-loading-overlay\">\n    <div class=\"cube-spinner\"></div>\n    <div class=\"cube-loading-text\">Loading cube…</div>\n  </div>\n
  <div class=\"cube-figure\" id=\"cube-figure\">{title_html}
    <div class=\"cube-main\">
      <div class=\"cube-inner\" id=\"cube-inner\">
        <div class=\"cube-scene\" id=\"cube-scene\">
          <div id=\"cube\">\n\
            <div id=\"front\"  class=\"face\"></div>\n\
            <div id=\"back\"   class=\"face\"></div>\n\
            <div id=\"right\"  class=\"face\"></div>\n\
            <div id=\"left\"   class=\"face\"></div>\n\
            <div id=\"top\"    class=\"face\"></div>\n\
            <div id=\"bottom\" class=\"face\"></div>\n\
            {interior_html}
            <div class=\"cube-outline\"></div>
            <div class=\"cube-label cube-label-time\">{axis_labels.get('time','time')}</div>
            <div class=\"cube-label cube-label-y\">{axis_labels.get('y','y')}</div>
            <div class=\"cube-label cube-label-x\">{axis_labels.get('x','x')}</div>
          </div>
        </div>
        {axes_html}
      </div>
    </div>
    {legend_html}
  </div>

  <script>
    window.addEventListener("load", function() {{
      var overlay = document.getElementById("cube-loading-overlay");
      if (overlay) overlay.style.display = "none";
    }});

    class CubeScene {{
      constructor() {{
        this.cube = document.getElementById("cube");
        this.scene = document.getElementById("cube-scene");
        this.rotX = parseFloat(document.body.getAttribute("data-rot-x") || 20);
        this.rotY = parseFloat(document.body.getAttribute("data-rot-y") || -30);
        this.zoom = parseFloat(document.body.getAttribute("data-zoom") || 1.0);
        this.dragging = false;
        this.lastX = 0;
        this.lastY = 0;
        this.apply();
        this.bind();
      }}

      apply() {{
        this.cube.style.setProperty("--rotX", this.rotX + "deg");
        this.cube.style.setProperty("--rotY", this.rotY + "deg");
        this.scene.style.setProperty("--cube-zoom", this.zoom);
      }}

      bind() {{
        document.addEventListener("mousedown", e => {{
          this.dragging = true;
          this.lastX = e.clientX;
          this.lastY = e.clientY;
        }});
        document.addEventListener("mouseup", () => {{ this.dragging = false; }});
        document.addEventListener("mousemove", e => {{
          if (!this.dragging) return;
          const dx = e.clientX - this.lastX;
          const dy = e.clientY - this.lastY;
          this.lastX = e.clientX;
          this.lastY = e.clientY;
          this.rotY += dx * 0.4;
          this.rotX -= dy * 0.4;
          this.apply();
        }});

        this.scene.addEventListener("wheel", e => {{
          e.preventDefault();
          this.zoom += (e.deltaY > 0) ? -0.08 : 0.08;
          this.zoom = Math.min(Math.max(this.zoom, 0.3), 3.0);
          this.apply();
        }}, {{ passive: false }});
      }}
    }}

    const cbMin = document.body.getAttribute("data-cb-min");
    const cbMax = document.body.getAttribute("data-cb-max");
    if (cbMin !== null) {{
      const minEl = document.getElementById("cb-min");
      if (minEl) minEl.innerText = cbMin;
    }}
    if (cbMax !== null) {{
      const maxEl = document.getElementById("cb-max");
      if (maxEl) maxEl.innerText = cbMax;
    }}

    new CubeScene();
  </script>
</body>
</html>
"""
    return html


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
    fill_mode: str = "shell",
    volume_density: Dict[str, int] | None = None,
    volume_downsample: Dict[str, int] | None = None,
    vase_mask: xr.DataArray | None = None,
    vase_outline: Any | None = None,
):
    volume_density = volume_density or {"time": 6, "x": 2, "y": 2}
    volume_downsample = volume_downsample or {"time": 4, "space": 4}

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

    t_indices = list(range(0, nt, max(1, thin_time_factor)))
    nt_eff = len(t_indices)

    progress = _CubeProgress(total=nt_eff, enabled=show_progress, style=progress_style)

    front_spatial: Optional[np.ndarray] = None
    back_spatial: Optional[np.ndarray] = None
    left_time_y = np.zeros((ny, nt_eff), dtype="float32")
    right_time_y = np.zeros((ny, nt_eff), dtype="float32")
    top_time_x = np.zeros((nx, nt_eff), dtype="float32")
    bottom_time_x = np.zeros((nx, nt_eff), dtype="float32")

    for idx, t_idx in enumerate(t_indices):
        frame = da.isel({t_dim: t_idx}).transpose(y_dim, x_dim)
        arr = frame.values

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

    apply_vase_overlay = vase_mask is not None and vase_outline is not None
    mask_slices: Dict[str, np.ndarray] = {}
    vase_color_rgb: tuple[int, int, int] | None = None
    if apply_vase_overlay:
        if not all(dim in vase_mask.dims for dim in (t_dim, y_dim, x_dim)):
            raise ValueError(
                "vase_mask must include the cube dimensions for time, y, and x"
            )
        from matplotlib.colors import to_rgb

        vase_color_rgb = tuple(int(255 * c) for c in to_rgb(vase_outline.color))
        mask_slices["front"] = np.asarray(
            vase_mask.isel({t_dim: t_indices[-1]}).transpose(y_dim, x_dim).values,
            dtype=bool,
        )
        mask_slices["back"] = np.flip(
            np.asarray(
                vase_mask.isel({t_dim: t_indices[0]}).transpose(y_dim, x_dim).values,
                dtype=bool,
            ),
            axis=1,
        )
        mask_slices["left"] = np.asarray(
            vase_mask.isel({x_dim: 0, t_dim: t_indices}).transpose(y_dim, t_dim).values,
            dtype=bool,
        )
        mask_slices["right"] = np.asarray(
            vase_mask.isel({x_dim: -1, t_dim: t_indices}).transpose(y_dim, t_dim).values,
            dtype=bool,
        )
        mask_slices["top"] = np.asarray(
            vase_mask.isel({y_dim: -1, t_dim: t_indices}).transpose(x_dim, t_dim).values,
            dtype=bool,
        )
        mask_slices["bottom"] = np.asarray(
            vase_mask.isel({y_dim: 0, t_dim: t_indices}).transpose(x_dim, t_dim).values,
            dtype=bool,
        )

    face_kwargs = {"cmap": cmap, "fill_limits": (vmin, vmax)}

    def _face_to_png(arr: np.ndarray, mask_key: str | None) -> str:
        rgba = _colormap_to_rgba(arr, **face_kwargs)
        if apply_vase_overlay and vase_color_rgb is not None and mask_key:
            mask_slice = mask_slices.get(mask_key)
            if mask_slice is not None:
                tinted_rgb = _apply_vase_tint(
                    rgba[..., :3],
                    mask_slice.astype(bool),
                    vase_color_rgb,
                    vase_outline.alpha,
                )
                rgba = np.concatenate([tinted_rgb, rgba[..., 3:4]], axis=2)
        return _rgba_to_png_base64(rgba)

    front_b64 = _face_to_png(front_spatial, "front")
    back_b64 = _face_to_png(back_spatial, "back")
    left_b64 = _face_to_png(left_time_y, "left")
    right_b64 = _face_to_png(right_time_y, "right")
    top_b64 = _face_to_png(top_time_x, "top")
    bottom_b64 = _face_to_png(bottom_time_x, "bottom")

    faces = {
        "front": f"data:image/png;base64,{front_b64}",
        "back": f"data:image/png;base64,{back_b64}",
        "left": f"data:image/png;base64,{left_b64}",
        "right": f"data:image/png;base64,{right_b64}",
        "top": f"data:image/png;base64,{top_b64}",
        "bottom": f"data:image/png;base64,{bottom_b64}",
    }

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

    axis_labels = {
        "time": time_label or _axis_label("time", t_dim or "time"),
        "x": x_label or _axis_label("x", x_dim),
        "y": y_label or _axis_label("y", y_dim),
    }

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

    legend_html = _build_legend_html(
        legend_title=legend_title,
        colorbar_b64=colorbar_b64,
        fill_breaks=fill_breaks,
        fill_labels=fill_labels,
    )
    axes_html = _build_axis_info_html(axis_info)
    title_html = f"<div class=\"cube-title\">{derived_title}</div>"

    interior_meta = {"nt": nt, "ny": ny, "nx": nx}
    if fill_mode in ("shell", "progressive"):
        shell_html = _render_cube_html(
            front=faces["front"],
            back=faces["back"],
            left=faces["left"],
            right=faces["right"],
            top=faces["top"],
            bottom=faces["bottom"],
            interior_planes=None,
            theme=css_vars,
            coord=coord,
            legend_html=legend_html,
            title_html=title_html,
            axes_html=axes_html,
            size_px=size_px,
            axis_labels=axis_labels,
            color_limits=(vmin, vmax),
            interior_meta=interior_meta,
        )
        handle = display(HTML(shell_html), display_id=True)
        display_id = getattr(handle, "display_id", None)
        if fill_mode == "shell":
            with open(out_html, "w", encoding="utf-8") as f:
                f.write(shell_html)
            return shell_html if return_html else handle

    ts = volume_density.get("time", 6)
    xs = volume_density.get("x", 2)
    ys = volume_density.get("y", 2)

    t_factor = volume_downsample.get("time", 4)
    s_factor = volume_downsample.get("space", 4)

    d_da = da.coarsen({t_dim: t_factor, y_dim: s_factor, x_dim: s_factor}, boundary="trim").mean()

    nt_down = d_da.sizes[t_dim]
    time_indices = np.linspace(1, nt_down - 2, ts, dtype=int) if ts > 0 and nt_down > 2 else []

    ny_down = d_da.sizes[y_dim]
    nx_down = d_da.sizes[x_dim]
    x_indices = np.linspace(1, nx_down - 2, xs, dtype=int) if xs > 0 and nx_down > 2 else []
    y_indices = np.linspace(1, ny_down - 2, ys, dtype=int) if ys > 0 and ny_down > 2 else []

    total_planes = len(time_indices) + len(x_indices) + len(y_indices)
    progress2 = _CubeProgress(total_planes, enabled=show_progress)

    interior_planes = []

    for i in time_indices:
        frame = d_da.isel({t_dim: i})
        arr = frame.values
        b64 = _array_to_png_base64(arr, **face_kwargs)
        interior_planes.append(("time", int(i), b64, {"nt": nt_down, "nx": nx_down, "ny": ny_down}))
        progress2.step()

    for i in x_indices:
        frame = d_da.isel({x_dim: i})
        arr = frame.values
        b64 = _array_to_png_base64(arr, **face_kwargs)
        interior_planes.append(("x", int(i), b64, {"nt": nt_down, "nx": nx_down, "ny": ny_down}))
        progress2.step()

    for i in y_indices:
        frame = d_da.isel({y_dim: i})
        arr = frame.values
        b64 = _array_to_png_base64(arr, **face_kwargs)
        interior_planes.append(("y", int(i), b64, {"nt": nt_down, "nx": nx_down, "ny": ny_down}))
        progress2.step()

    progress2.done()

    interior_meta = {"nt": nt_down, "ny": ny_down, "nx": nx_down}
    full_html = _render_cube_html(
        front=faces["front"],
        back=faces["back"],
        left=faces["left"],
        right=faces["right"],
        top=faces["top"],
        bottom=faces["bottom"],
        interior_planes=interior_planes,
        theme=css_vars,
        coord=coord,
        legend_html=legend_html,
        title_html=title_html,
        axes_html=axes_html,
        size_px=size_px,
        axis_labels=axis_labels,
        color_limits=(vmin, vmax),
        interior_meta=interior_meta,
    )

    if fill_mode == "progressive":
        if display_id:
            update_display(HTML(full_html), display_id=display_id)
        else:
            handle = display(HTML(full_html))
    else:
        handle = display(HTML(full_html))

    with open(out_html, "w", encoding="utf-8") as f:
        f.write(full_html)

    if return_html:
        return full_html
    return handle if fill_mode == "progressive" else IFrame(out_html, width=900, height=900)


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
