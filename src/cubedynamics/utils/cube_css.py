"""Helpers for emitting lightweight CSS cube HTML scaffolding."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

DEFAULT_FACES = {
    "front": "none",
    "back": "none",
    "right": "none",
    "left": "none",
    "top": "none",
    "bottom": "none",
}


def _face_style(face_uri: str) -> str:
    base_style = "background: rgba(255, 255, 255, 0.05);"
    if face_uri.lower() == "none":
        return base_style
    return "background-image: url('{0}'); background-size: cover; background-position: center;".format(
        face_uri
    )


def write_css_cube_static(
    *,
    out_html: str = "cube_da.html",
    size_px: int = 260,
    faces: Dict[str, str] | None = None,
    colorbar_b64: str | None = None,
    title: str = "Cube Viewer",
    time_label: str = "time",
    x_label: str = "x",
    y_label: str = "y",
    legend_title: str | None = None,
    css_vars: Dict[str, str] | None = None,
) -> Path:
    """Write a standalone HTML page with a simple CSS-based cube skeleton.

    Parameters
    ----------
    out_html:
        Output HTML path.
    size_px:
        Width/height of the cube in pixels.
    faces:
        Optional mapping of cube face names to data URIs (or ``"none"``).
    colorbar_b64:
        Optional base64-encoded PNG that will be used as the colorbar image.
    title:
        Title text rendered above the cube.
    time_label, x_label, y_label:
        Axis labels placed around the cube to indicate coordinate directions.
    """

    face_map = {**DEFAULT_FACES, **(faces or {})}
    size = int(size_px)
    half = size / 2

    colorbar = (
        f'<img class="colorbar-img" src="data:image/png;base64,{colorbar_b64}" alt="colorbar" />'
        if colorbar_b64
        else ""
    )

    css_vars = css_vars or {}
    bg_color = css_vars.get("--cube-bg-color", "#000")
    panel_color = css_vars.get("--cube-panel-color", "#000")
    shadow_strength = css_vars.get("--cube-shadow-strength", "0.2")
    title_color = css_vars.get("--cube-title-color", "#f7f7f7")
    axis_color = css_vars.get("--cube-axis-color", "#f7f7f7")
    legend_color = css_vars.get("--cube-legend-color", "#f7f7f7")
    title_font_size = css_vars.get("--cube-title-font-size", "18px")
    axis_font_size = css_vars.get("--cube-axis-font-size", "12px")
    legend_font_size = css_vars.get("--cube-legend-font-size", "10px")
    font_family = css_vars.get(
        "--cube-font-family", "system-ui, -apple-system, sans-serif"
    )

    legend_block = (
        f"<div class=\"colorbar-title\">{legend_title}</div>" if legend_title else ""
    )

    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <title>{title}</title>
  <style>
    :root {{
      --cube-size: {size}px;
      --cube-bg-color: {bg_color};
      --cube-panel-color: {panel_color};
      --cube-shadow-strength: {shadow_strength};
      --cube-title-color: {title_color};
      --cube-axis-color: {axis_color};
      --cube-legend-color: {legend_color};
      --cube-title-font-size: {title_font_size};
      --cube-axis-font-size: {axis_font_size};
      --cube-legend-font-size: {legend_font_size};
      --cube-font-family: {font_family};
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 24px 12px 32px 12px;
      width: 100%;
      height: 100%;
      background: var(--cube-bg-color);
      color: var(--cube-axis-color);
      font-family: var(--cube-font-family);
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      user-select: none;
    }}
    .cube-wrapper {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      transform: scale(var(--zoom, 1));
      transform-origin: center center;
      transition: transform 120ms ease-out;
      background: var(--cube-panel-color);
      padding: 12px;
      border-radius: 12px;
      box-shadow: 0 16px 40px rgba(0,0,0,var(--cube-shadow-strength));
    }}
    .cube-title {{
      font-size: var(--cube-title-font-size);
      letter-spacing: 0.04em;
      font-weight: 600;
      text-align: center;
      color: var(--cube-title-color);
    }}
    .scene {{
      position: relative;
      width: 900px;
      height: 700px;
      display: flex;
      align-items: center;
      justify-content: center;
      perspective: 1600px;
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
    #front  {{ transform: translateZ({half}px); { _face_style(face_map['front']) } }}
    #back   {{ transform: rotateY(180deg) translateZ({half}px); { _face_style(face_map['back']) } }}
    #right  {{ transform: rotateY(90deg) translateZ({half}px); { _face_style(face_map['right']) } }}
    #left   {{ transform: rotateY(-90deg) translateZ({half}px); { _face_style(face_map['left']) } }}
    #top    {{ transform: rotateX(90deg) translateZ({half}px); { _face_style(face_map['top']) } }}
    #bottom {{ transform: rotateX(-90deg) translateZ({half}px); { _face_style(face_map['bottom']) } }}
    .axis-label {{
      position: absolute;
      font-size: var(--cube-axis-font-size);
      letter-spacing: 0.04em;
      background: rgba(0,0,0,0.08);
      padding: 6px 10px;
      border-radius: 6px;
      border: 1px solid rgba(0,0,0,0.08);
      pointer-events: none;
      color: var(--cube-axis-color);
    }}
    .axis-time {{
      left: 28px;
      top: 50%;
      transform: translate(-50%, -50%) rotate(-90deg);
      transform-origin: center;
    }}
    .axis-x {{
      bottom: 32px;
      left: 50%;
      transform: translateX(-50%);
    }}
    .axis-y {{
      right: 32px;
      top: 50%;
      transform: translate(50%, -50%) rotate(90deg);
      transform-origin: center;
    }}
    .colorbar-wrapper {{
      width: min(520px, 70vw);
      align-self: center;
    }}
    .colorbar-title {{
      font-size: var(--cube-legend-font-size);
      font-weight: 600;
      color: var(--cube-legend-color);
      text-align: center;
      margin-bottom: 4px;
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
      width: min(520px, 70vw);
      display: flex;
      justify-content: space-between;
      font-size: var(--cube-legend-font-size);
      margin-top: 4px;
      align-self: center;
      color: var(--cube-legend-color);
    }}
  </style>

</head>
<body>

<div class=\"cube-wrapper\" id=\"cube-wrapper\">
  <div class=\"cube-title\">{title}</div>
  <div class=\"scene\" id=\"scene\">
    <div id=\"cube\"> 
      <div id=\"front\"  class=\"face\"></div>
      <div id=\"back\"   class=\"face\"></div>
      <div id=\"right\"  class=\"face\"></div>
      <div id=\"left\"   class=\"face\"></div>
      <div id=\"top\"    class=\"face\"></div>
      <div id=\"bottom\" class=\"face\"></div>
    </div>
    <div class=\"axis-label axis-time\">{time_label} \u2192</div>
    <div class=\"axis-label axis-y\">{y_label} \u2191</div>
    <div class=\"axis-label axis-x\">{x_label} \u2192</div>
  </div>
  <div class=\"colorbar-wrapper\">{legend_block}{colorbar}</div>
  <div class=\"colorbar-labels\">
    <span id=\"cb-min\"></span>
    <span id=\"cb-max\"></span>
  </div>
</div>

<script>
let rotX = 15;
let rotY = -25;
let zoom = 1.0;

let dragging = false;
let lastX = 0;
let lastY = 0;

const cube = document.getElementById("cube");
const wrapper = document.getElementById("cube-wrapper");
const scene = document.getElementById("scene");
cube.style.setProperty("--rotX", rotX + "deg");
cube.style.setProperty("--rotY", rotY + "deg");
wrapper.style.setProperty("--zoom", zoom);

document.addEventListener("mousedown", e => {{
  dragging = true;
  lastX = e.clientX;
  lastY = e.clientY;
}});

document.addEventListener("mouseup", () => {{ dragging = false; }});

document.addEventListener("mousemove", e => {{
  if (!dragging) return;
  const dx = e.clientX - lastX;
  const dy = e.clientY - lastY;
  lastX = e.clientX;
  lastY = e.clientY;

  rotY += dx * 0.4;
  rotX -= dy * 0.4;

  cube.style.setProperty("--rotX", rotX + "deg");
  cube.style.setProperty("--rotY", rotY + "deg");
}});

const applyZoom = () => {{
  wrapper.style.transform = `scale(${{zoom}})`;
}};

scene.addEventListener("wheel", e => {{
  e.preventDefault();
  zoom += (e.deltaY > 0) ? -0.08 : 0.08;
  zoom = Math.min(Math.max(zoom, 0.3), 3.0);
  applyZoom();
}}, {{ passive: false }});

// Colorbar labels
const cbMin = document.body.getAttribute("data-cb-min");
const cbMax = document.body.getAttribute("data-cb-max");
if (cbMin !== null) document.getElementById("cb-min").innerText = cbMin;
if (cbMax !== null) document.getElementById("cb-max").innerText = cbMax;

applyZoom();

</script>

</body>
</html>
"""

    out_path = Path(out_html)
    out_path.write_text(html, encoding="utf-8")
    return out_path


__all__ = ["write_css_cube_static", "DEFAULT_FACES"]
