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
    """

    face_map = {**DEFAULT_FACES, **(faces or {})}
    size = int(size_px)
    half = size / 2

    colorbar = (
        f'<img class="colorbar-img" src="data:image/png;base64,{colorbar_b64}" alt="colorbar" />'
        if colorbar_b64
        else ""
    )

    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <title>Cube Viewer</title>
  <style>
    :root {{
      --cube-size: {size}px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background: #000;
      color: #f7f7f7;
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      user-select: none;
    }}
    #container {{
      width: 100vw;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      perspective: 1200px;
    }}
    #cube {{
      position: relative;
      width: var(--cube-size);
      height: var(--cube-size);
      transform-style: preserve-3d;
      transform: translateZ(0px) rotateX(var(--rotX, 15deg)) rotateY(var(--rotY, -25deg)) scale(var(--zoom, 1));
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
    .label {{
      position: absolute;
      top: 10px;
      left: 10px;
      font-size: 14px;
      letter-spacing: 0.06em;
    }}
    .colorbar-wrapper {{
      position: absolute;
      left: 50%;
      bottom: 25px;
      transform: translateX(-50%);
      width: 55%;
      max-width: 520px;
    }}
    .colorbar-img {{
      width: 100%;
      height: 14px;
      border-radius: 4px;
      border: 1px solid rgba(255,255,255,0.6);
      display: block;
    }}
    .colorbar-labels {{
      position: absolute;
      left: 50%;
      bottom: 8px;
      transform: translateX(-50%);
      width: 55%;
      max-width: 520px;
      display: flex;
      justify-content: space-between;
      font-size: 10px;
    }}
  </style>

</head>
<body>

<div class=\"label\">DataArray cube (drag to rotate, wheel to zoom)</div>

<div id=\"container\">
  <div id=\"cube\">
    <div id=\"front\"  class=\"face\"></div>
    <div id=\"back\"   class=\"face\"></div>
    <div id=\"right\"  class=\"face\"></div>
    <div id=\"left\"   class=\"face\"></div>
    <div id=\"top\"    class=\"face\"></div>
    <div id=\"bottom\" class=\"face\"></div>
  </div>
</div>

<div class=\"colorbar-wrapper\">
  {colorbar}
</div>
<div class=\"colorbar-labels\">
  <span id=\"cb-min\"></span>
  <span id=\"cb-max\"></span>
</div>

<script>
let rotX = 15;
let rotY = -25;
let zoom = 1.0;

let dragging = false;
let lastX = 0;
let lastY = 0;

const cube = document.getElementById("cube");
cube.style.setProperty("--rotX", rotX + "deg");
cube.style.setProperty("--rotY", rotY + "deg");
cube.style.setProperty("--zoom", zoom);

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

document.addEventListener("wheel", e => {{
  e.preventDefault();
  zoom *= (e.deltaY > 0) ? 0.92 : 1.08;
  zoom = Math.min(Math.max(zoom, 0.25), 6.0);
  cube.style.setProperty("--zoom", zoom);
}}, {{ passive: false }});

// Colorbar labels
const cbMin = document.body.getAttribute("data-cb-min");
const cbMax = document.body.getAttribute("data-cb-max");
if (cbMin !== null) document.getElementById("cb-min").innerText = cbMin;
if (cbMax !== null) document.getElementById("cb-max").innerText = cbMax;

</script>

</body>
</html>
"""

    out_path = Path(out_html)
    out_path.write_text(html, encoding="utf-8")
    return out_path


__all__ = ["write_css_cube_static", "DEFAULT_FACES"]
