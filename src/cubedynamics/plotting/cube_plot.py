"""Lightweight CubePlot object model with theming and caption support.

This module now hosts a minimal grammar-of-graphics core for cube plotting,
including aesthetics, layers/geoms, scales, stats, coordinates, and simple
annotations. The goal is to keep the API small and streaming-friendly while
expanding the expressiveness of cube visualizations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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


@dataclass
class CubeAes:
    """Aesthetic mapping for cube plots."""

    fill: Optional[str] = None
    alpha: Optional[str] = None
    slice: Optional[str] = None
    facet: Optional[str] = None


def _infer_aes_from_data(data: Any) -> CubeAes:
    """Infer a simple aesthetic mapping from a DataArray."""

    if isinstance(data, xr.DataArray):
        return CubeAes(fill=data.name)
    return CubeAes()


@dataclass
class CubeLayer:
    """A plotting layer pairing a geom with data and stat."""

    geom: str
    data: Any = None
    aes: Optional[CubeAes] = None
    stat: Optional[str] = "identity"
    params: Dict[str, Any] = field(default_factory=dict)


def geom_cube(**params: Any) -> CubeLayer:
    return CubeLayer(geom="cube", stat="identity", params=params)


def geom_slice(**params: Any) -> CubeLayer:
    return CubeLayer(geom="slice", stat="identity", params=params)


def geom_outline(**params: Any) -> CubeLayer:
    return CubeLayer(geom="outline", stat="identity", params=params)


def geom_path3d(**params: Any) -> CubeLayer:
    return CubeLayer(geom="path3d", stat="identity", params=params)


@dataclass
class ScaleFillContinuous:
    cmap: str = "viridis"
    limits: Optional[tuple[float, float]] = None
    breaks: Optional[list[float]] = None
    labels: Optional[list[str]] = None
    center: Optional[float] = None
    transform: Optional[str] = None
    name: Optional[str] = None

    def infer_limits(self, data: xr.DataArray) -> tuple[float, float]:
        if self.limits is not None:
            return self.limits
        finite_min = float(data.min(skipna=True))
        finite_max = float(data.max(skipna=True))
        if finite_min == finite_max:
            finite_min -= 1.0
            finite_max += 1.0
        return finite_min, finite_max

    def infer_breaks(self, limits: tuple[float, float]) -> list[float]:
        if self.breaks is not None:
            return self.breaks
        lo, hi = limits
        step = (hi - lo) / 4.0 if hi != lo else 1.0
        return [round(lo + step * i, 2) for i in range(5)]


@dataclass
class ScaleAlphaContinuous:
    limits: Optional[tuple[float, float]] = None
    range: tuple[float, float] = (0.1, 1.0)
    name: Optional[str] = None


@dataclass
class CoordCube:
    view: str = "iso"
    elev: float = 30.0
    azim: float = 45.0
    zoom: float = 1.0
    aspect: tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass
class CubeAnnotation:
    kind: str
    axis: Optional[str] = None
    value: Optional[float] = None
    text: Optional[str] = None
    coord: Optional[tuple] = None


def stat_identity(data: xr.DataArray, aes: CubeAes, params: Dict[str, Any]) -> xr.DataArray:
    return data


def stat_time_mean(data: xr.DataArray, aes: CubeAes, params: Dict[str, Any]) -> xr.DataArray:
    time_dim = params.get("time_dim") or aes.slice or "time"
    if time_dim not in data.dims:
        return data
    return data.mean(time_dim)


def stat_time_anomaly(
    data: xr.DataArray, aes: CubeAes, params: Dict[str, Any]
) -> xr.DataArray:
    time_dim = params.get("time_dim") or aes.slice or "time"
    if time_dim not in data.dims:
        return data
    mean = data.mean(time_dim)
    std = data.std(time_dim)
    return (data - mean) / std


def stat_space_mean(data: xr.DataArray, aes: CubeAes, params: Dict[str, Any]) -> xr.DataArray:
    space_dims = params.get("space_dims") or params.get("dims") or ("y", "x")
    dims_to_use = [d for d in space_dims if d in data.dims]
    if not dims_to_use:
        return data
    return data.mean(dim=dims_to_use)


_STAT_REGISTRY = {
    "identity": stat_identity,
    "time_mean": stat_time_mean,
    "time_anomaly": stat_time_anomaly,
    "space_mean": stat_space_mean,
}


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
    aes: Optional[CubeAes] = None
    layers: List[CubeLayer] = field(default_factory=list)
    title: Optional[str] = None
    legend_title: Optional[str] = None
    theme: CubeTheme = field(default_factory=theme_cube_studio)
    caption: Optional[Dict[str, Any]] = None
    size_px: int = 260
    cmap: str = "viridis"
    fill_scale: Optional[ScaleFillContinuous] = None
    alpha_scale: Optional[ScaleAlphaContinuous] = None
    thin_time_factor: int = 4
    time_label: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    time_dim: Optional[str] = None
    show_progress: bool = True
    progress_style: str = "bar"
    coord: CoordCube = field(default_factory=CoordCube)
    annotations: List[CubeAnnotation] = field(default_factory=list)
    out_html: str = "cube_da.html"

    def __post_init__(self) -> None:
        if self.aes is None:
            self.aes = _infer_aes_from_data(self.data)
        if not self.layers:
            self.layers.append(geom_cube())
        if self.fill_scale is None:
            self.fill_scale = ScaleFillContinuous(cmap=self.cmap, name=self.legend_title)
        if self.alpha_scale is None:
            self.alpha_scale = ScaleAlphaContinuous()

    def scale_fill_continuous(self, **kwargs: Any) -> "CubePlot":
        self.fill_scale = ScaleFillContinuous(**kwargs)
        return self

    def scale_alpha_continuous(self, **kwargs: Any) -> "CubePlot":
        self.alpha_scale = ScaleAlphaContinuous(**kwargs)
        return self

    def coord_cube(self, **kwargs: Any) -> "CubePlot":
        for key, val in kwargs.items():
            if hasattr(self.coord, key) and val is not None:
                setattr(self.coord, key, val)
        return self

    def annot_plane(self, axis: str, value: float, text: Optional[str] = None) -> "CubePlot":
        self.annotations.append(CubeAnnotation(kind="plane", axis=axis, value=value, text=text))
        return self

    def annot_text(self, coord: tuple, text: str) -> "CubePlot":
        self.annotations.append(CubeAnnotation(kind="text", coord=coord, text=text))
        return self

    def add_layer(self, layer: CubeLayer) -> "CubePlot":
        self.layers.append(layer)
        return self

    def to_html(self) -> str:
        da = self.data
        if not isinstance(da, xr.DataArray):
            raise TypeError("CubePlot expects an xarray.DataArray")

        primary_layer = self.layers[0] if self.layers else geom_cube()
        layer_data = primary_layer.data if primary_layer.data is not None else da
        layer_aes = primary_layer.aes if primary_layer.aes is not None else self.aes
        stat_fn = _STAT_REGISTRY.get(primary_layer.stat or "identity", stat_identity)
        stat_data = stat_fn(layer_data, layer_aes or CubeAes(), primary_layer.params)

        fill_scale = self.fill_scale or ScaleFillContinuous(cmap=self.cmap)
        fill_limits = fill_scale.infer_limits(stat_data)
        legend_title = fill_scale.name or _derive_legend_title(stat_data, self.legend_title)

        viewer_obj = cube_from_dataarray(
            stat_data,
            out_html=self.out_html,
            cmap=fill_scale.cmap,
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
            fill_limits=fill_limits,
            fill_breaks=fill_scale.infer_breaks(fill_limits),
            fill_labels=fill_scale.labels,
            coord=self.coord,
            annotations=self.annotations,
            return_html=False,
        )

        viewer_html = viewer_obj if isinstance(viewer_obj, str) else viewer_obj._repr_html_()

        caption_html = _build_caption(self.caption)

        if self.annotations:
            annot_html_parts = ["<div class=\"cube-annotations\">"]
            for annot in self.annotations:
                if annot.kind == "plane":
                    annot_html_parts.append(
                        f"<div class='cube-annot'>Plane {html.escape(str(annot.axis))}={html.escape(str(annot.value))}"
                        + (f" — {html.escape(str(annot.text))}" if annot.text else "")
                        + "</div>"
                    )
                elif annot.kind == "text":
                    annot_html_parts.append(
                        f"<div class='cube-annot'>Text @ {html.escape(str(annot.coord))}: {html.escape(str(annot.text or ''))}</div>"
                    )
            annot_html_parts.append("</div>")
            caption_html += "".join(annot_html_parts)

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
            ".cube-annotations{margin-top:8px; font-size: var(--cube-caption-font-size,12px); color: var(--cube-axis-color,#222);}"
            ".cube-annot{margin-top:2px;}"
            "</style>"
            f"<div class='cube-viewer' style='{figure_style}'>{viewer_html}</div>"
            f"{caption_html}"
            "</div>"
        )

    def _repr_html_(self) -> str:  # pragma: no cover - exercised in notebooks
        return self.to_html()


__all__ = [
    "CubePlot",
    "CubeTheme",
    "theme_cube_studio",
    "CubeAes",
    "CubeLayer",
    "CubeAnnotation",
    "ScaleFillContinuous",
    "ScaleAlphaContinuous",
    "CoordCube",
    "geom_cube",
    "geom_slice",
    "geom_outline",
    "geom_path3d",
]
