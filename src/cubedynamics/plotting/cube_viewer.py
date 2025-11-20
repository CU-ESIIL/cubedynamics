from __future__ import annotations

import base64
import io

import numpy as np
import xarray as xr
from matplotlib import colormaps, colors as mcolors
from PIL import Image
from IPython.display import IFrame

from cubedynamics.utils import _infer_time_y_x_dims, write_css_cube_static


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
    t_dim, y_dim, x_dim = _infer_time_y_x_dims(da)
    if t_dim is None:
        raise ValueError("cube_from_dataarray expects a time dimension for 3D cubes.")
    da = da.transpose(t_dim, y_dim, x_dim)

    nt, ny, nx = da.sizes[t_dim], da.sizes[y_dim], da.sizes[x_dim]

    # ----------------------------
    # 2. Reduce time if very long
    # ----------------------------
    if thin_time_factor > 1 and nt > 300:
        da = da.isel({t_dim: slice(0, None, thin_time_factor)})
        nt = da.sizes[t_dim]

    # ---------------------------------
    # 3. Extract raw numpy face arrays
    # ---------------------------------
    # Lazy Dask compute is OK; only reads three slices
    first_t = da.isel({t_dim: 0})
    last_t = da.isel({t_dim: nt - 1})

    front_spatial = last_t.values  # (y, x) latest time
    back_spatial = np.flip(first_t.values, axis=1)

    left_time_y = da.isel({x_dim: 0}).transpose(y_dim, t_dim).values
    right_time_y = da.isel({x_dim: nx - 1}).transpose(y_dim, t_dim).values

    top_time_x = da.isel({y_dim: ny - 1}).transpose(x_dim, t_dim).values
    bottom_time_x = da.isel({y_dim: 0}).transpose(x_dim, t_dim).values

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
    buf_cb = io.BytesIO()
    Image.fromarray(grad_img).save(buf_cb, format="PNG")
    colorbar_b64 = base64.b64encode(buf_cb.getvalue()).decode("ascii")

    derived_title = title or da.name or f"{t_dim} × {y_dim} × {x_dim} cube"
    write_css_cube_static(
        out_html=out_html,
        size_px=size_px,
        faces=faces,
        colorbar_b64=colorbar_b64,
        title=derived_title,
        time_label=time_label or t_dim or "time",
        x_label=x_label or x_dim,
        y_label=y_label or y_dim,
    )

    # -------------------------
    # 8. Inject colorbar + loader
    # -------------------------
    with open(out_html, "r") as f:
        html = f.read()

    # Add data attributes + loading overlay + JS to hide it on load.
    injection = f'''
<body data-cb-min="{vmin:.2f}" data-cb-max="{vmax:.2f}">
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
    return IFrame(out_html, width=900, height=900)


__all__ = ["cube_from_dataarray"]
