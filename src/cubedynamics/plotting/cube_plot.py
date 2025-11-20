"""Lightweight CubePlot object model with theming and caption support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import html

import xarray as xr

from cubedynamics.plotting.cube_viewer import cube_from_dataarray


@dataclass
class CubeTheme:
    """Theme configuration for cube plots."""

    bg_color: str = "#ffffff"
    panel_color: str = "#ffffff"
    shadow_strength: float = 0.15
    lighting_style: str = "studio"

    title_font_family: str = (
        "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    )
    title_font_size: int = 18
    axis_scale: float = 0.6
    legend_scale: float = 0.55

    title_color: str = "cornflowerblue"
    axis_color: str = "firebrick"
    legend_color: str = "limegreen"

    caption_font_scale: float = 0.8


def theme_cube_studio() -> CubeTheme:
    """Return the default "studio" theme."""

    return CubeTheme()


def _derive_legend_title(da: xr.DataArray, legend_title: str | None) -> str | None:
    if legend_title is not None:
        return legend_title
    if da.name:
        return str(da.name)
    for attr in ("long_name", "standard_name"):
        if attr in da.attrs:
            return str(da.attrs[attr])
    return None


def _build_caption(caption: Optional[Dict[str, Any]]) -> str:
    if not caption:
        return ""

    fig_id = caption.get("id")
    fig_title = caption.get("title")
    fig_text = caption.get("text")

    parts = ["<div class=\"cube-caption\">"]
    if fig_id is not None:
        parts.append(f"<div class='cube-caption-label'>Figure {html.escape(str(fig_id))}.</div>")
    if fig_title:
        parts.append(f"<div class='cube-caption-title'><strong>{html.escape(str(fig_title))}</strong></div>")
    if fig_text:
        text_html = html.escape(str(fig_text)).replace("\n", "<br />")
        parts.append(f"<div class='cube-caption-text'>{text_html}</div>")
    parts.append("</div>")
    return "".join(parts)


@dataclass
class CubePlot:
    """Internal object model for cube visualizations."""

    data: Any
    title: Optional[str] = None
    legend_title: Optional[str] = None
    theme: CubeTheme = field(default_factory=theme_cube_studio)
    caption: Optional[Dict[str, Any]] = None
    size_px: int = 260
    cmap: str = "viridis"
    thin_time_factor: int = 4
    time_label: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    time_dim: Optional[str] = None
    show_progress: bool = True
    progress_style: str = "bar"
    out_html: str = "cube_da.html"

    def to_html(self) -> str:
        da = self.data
        if not isinstance(da, xr.DataArray):
            raise TypeError("CubePlot expects an xarray.DataArray")

        legend_title = _derive_legend_title(da, self.legend_title)

        viewer_obj = cube_from_dataarray(
            da,
            out_html=self.out_html,
            cmap=self.cmap,
            size_px=self.size_px,
            thin_time_factor=self.thin_time_factor,
            title=self.title,
            time_label=self.time_label,
            x_label=self.x_label,
            y_label=self.y_label,
            legend_title=legend_title,
            theme=self.theme,
            show_progress=self.show_progress,
            progress_style=self.progress_style,
            time_dim=self.time_dim,
            return_html=False,
        )

        viewer_html = viewer_obj if isinstance(viewer_obj, str) else viewer_obj._repr_html_()

        caption_html = _build_caption(self.caption)

        theme_vars = {
            "--cube-title-font-size": f"{self.theme.title_font_size}px",
            "--cube-title-color": self.theme.title_color,
            "--cube-axis-color": self.theme.axis_color,
            "--cube-legend-color": self.theme.legend_color,
            "--cube-axis-font-size": f"{self.theme.title_font_size * self.theme.axis_scale}px",
            "--cube-legend-font-size": f"{self.theme.title_font_size * self.theme.legend_scale}px",
            "--cube-bg-color": self.theme.bg_color,
            "--cube-panel-color": self.theme.panel_color,
            "--cube-shadow-strength": str(self.theme.shadow_strength),
            "--cube-caption-font-size": f"{self.theme.title_font_size * self.theme.axis_scale * self.theme.caption_font_scale}px",
            "--cube-font-family": self.theme.title_font_family,
        }

        figure_style = " ".join(f"{k}: {v};" for k, v in theme_vars.items())

        return (
            "<div class='cube-figure' style="
            f"font-family:{self.theme.title_font_family}; background:{self.theme.bg_color}; padding:12px; border-radius:12px; box-shadow:0 16px 40px rgba(0,0,0,{self.theme.shadow_strength});"
            f" color:{self.theme.axis_color};" + "'>"
            "<style>"
            ".cube-legend-title{font-size: var(--cube-axis-font-size,12px); color: var(--cube-legend-color, #222); margin-bottom:6px;}"
            ".cube-caption{margin-top:12px; color: var(--cube-axis-color,#222); font-size: var(--cube-caption-font-size,12px);}"
            ".cube-caption-label{display:inline-block; margin-right:6px; color: var(--cube-axis-color,#222);}"
            ".cube-caption-title{display:inline-block; margin-right:8px; color: var(--cube-title-color,#222);}"
            ".cube-caption-text{margin-top:4px; color: var(--cube-axis-color,#222);}"
            "</style>"
            f"<div class='cube-viewer' style='{figure_style}'>{viewer_html}</div>"
            f"{caption_html}"
            "</div>"
        )

    def _repr_html_(self) -> str:  # pragma: no cover - exercised in notebooks
        return self.to_html()


__all__ = ["CubePlot", "CubeTheme", "theme_cube_studio"]
