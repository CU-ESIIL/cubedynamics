"""Grammar-of-graphics + streaming core for cube plotting.

This module powers the "CubePlot" narrative used throughout the docs:
`pipe(ndvi) | v.plot()` for the simple case, and `CubePlot(...).geom_cube()`
when you want fully controlled layers, scales, captions, and facets. Every
component is designed to stay **streaming-first**: the viewer iterates over
time slices and avoids materializing whole cubes, keeping NEON/Sentinel/PRISM
requests responsive in notebooks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import logging
import html
import json
import os
import string
import uuid
from textwrap import dedent

import xarray as xr

import numpy as np
import pandas as pd

from cubedynamics.plotting.cube_viewer import cube_from_dataarray, _new_cubeplot_dom_id
from cubedynamics.vase import VaseDefinition
from cubedynamics.utils import _infer_time_y_x_dims


logger = logging.getLogger(__name__)


class _CubePlotMeta(type):
    def __instancecheck__(cls, instance: object) -> bool:  # pragma: no cover - lightweight helper
        if type.__instancecheck__(cls, instance):
            return True
        viewer = getattr(instance, "_cd_last_viewer", None)
        if viewer is None:
            viewer = getattr(getattr(instance, "attrs", {}), "_cd_last_viewer", None)
        return viewer is not None and type.__instancecheck__(cls, viewer)


@dataclass
class CubeTheme:
    """Theme configuration for cube plots.

    CSS variables and font sizes flow through to the generated HTML so captions,
    titles, axes, and legends match report-ready styling. Themes are intentionally
    lightweight: adjust only what is needed while leaving streaming behavior
    untouched.
    """

    bg_color: str = "#ffffff"
    panel_color: str = "#ffffff"
    shadow_strength: float = 0.15
    lighting_style: str = "studio"

    title_font_family: str = (
        "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    )
    title_font_size: int = 20
    axis_scale: float = 0.6
    legend_scale: float = 0.6

    title_color: str = "cornflowerblue"
    axis_color: str = "firebrick"
    legend_color: str = "limegreen"

    caption_font_scale: float = 0.8

    panel_padding: int = 10


def theme_cube_studio(tight_axes: bool | None = False, **kwargs: Any) -> CubeTheme:
    """Return the default "studio" theme."""

    return CubeTheme()


@dataclass
class CubeAes:
    """Aesthetic mapping for cube plots.

    Mirrors ggplot's ``aes`` by mapping data variables to visuals. Only the
    fields relevant to the cube viewer are exposed (fill, alpha, and slice
    selection), keeping the API small while matching the grammar-of-graphics
    vocabulary documented on the website.
    """

    fill: Optional[str] = None
    alpha: Optional[str] = None
    slice: Optional[str] = None
    facet: Optional[str] = None


@dataclass
class CubeFacet:
    row: Optional[str] = None
    col: Optional[str] = None
    wrap: Optional[int] = None
    by: Optional[str] = None


def _infer_aes_from_data(data: Any) -> CubeAes:
    """Infer a simple aesthetic mapping from a DataArray."""

    if isinstance(data, xr.DataArray):
        return CubeAes(fill=data.name)
    return CubeAes()


@dataclass
class CubeLayer:
    """A plotting layer pairing a geom with data and stat.

    ``CubePlot`` currently supports a single primary layer but the object model
    mirrors ggplot so additional geoms can be added in the future without
    breaking the streaming renderer.
    """

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
    """Continuous color scale used by the cube viewer.

    Supports palette selection, centered/diverging ramps, and legend metadata.
    ``CubePlot`` infers limits lazily from the streamed slices.
    """
    cmap: str = "cividis"
    palette: str = "sequential"
    limits: Optional[tuple[float, float]] = None
    breaks: Optional[list[float]] = None
    labels: Optional[list[str]] = None
    center: Optional[float] = None
    transform: Optional[str] = None
    name: Optional[str] = None
    units: Optional[str] = None

    def _default_cmap(self) -> str:
        if self.cmap:
            return self.cmap
        if self.palette == "diverging":
            return "coolwarm"
        return "cividis"

    def resolved_cmap(self) -> str:
        return self._default_cmap()

    def infer_limits(self, data: xr.DataArray) -> tuple[float, float]:
        if self.limits is not None:
            return self.limits
        arr = np.asarray(data)
        finite = np.isfinite(arr)
        if finite.any():
            finite_min = float(np.nanmin(arr[finite]))
            finite_max = float(np.nanmax(arr[finite]))
        else:
            finite_min, finite_max = -1.0, 1.0
        if self.center is not None:
            spread = max(abs(finite_min - self.center), abs(finite_max - self.center))
            finite_min = self.center - spread
            finite_max = self.center + spread
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
    """Camera/coordinate configuration for cube plots."""
    view: str = "iso"
    elev: float = 30.0
    azim: float = 45.0
    zoom: float = 1.0
    aspect: tuple[float, float, float] = (1.0, 1.0, 1.0)
    time_ticks: int = 4
    space_ticks: int = 3
    time_format: str = "%Y-%m-%d"


@dataclass
class CubeAnnotation:
    """Simple annotation container for planes/text anchored to cube axes."""
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


def _format_time_label(value: Any) -> str:
    try:
        ts = pd.to_datetime(value)
        return ts.strftime("%d.%m.%Y")
    except Exception:
        return str(value)


def _format_lat(value: Any) -> str:
    try:
        val = float(value)
    except Exception:
        return str(value)
    hemi = "N" if val >= 0 else "S"
    return f"{abs(val):.0f}°{hemi}"


def _format_lon(value: Any) -> str:
    try:
        val = float(value)
    except Exception:
        return str(value)
    hemi = "E" if val >= 0 else "W"
    return f"{abs(val):.0f}°{hemi}"


def _format_numeric(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except Exception:
        return str(value)


def _looks_like_lat(values: np.ndarray, units: str, dim_name: str) -> bool:
    name_lower = dim_name.lower()
    units_lower = units.lower()
    if "lat" in name_lower or "latitude" in name_lower:
        return True
    if name_lower == "y":
        try:
            numeric = values.astype(float)
            finite = np.isfinite(numeric)
            if finite.any():
                within_range = np.nanmin(numeric[finite]) >= -90.5 and np.nanmax(numeric[finite]) <= 90.5
                has_fraction = np.any(np.mod(numeric[finite], 1) != 0)
                if within_range and has_fraction:
                    return True
        except Exception:
            pass
    if any(k in units_lower for k in ["lat", "north", "degrees_north", "deg"]):
        try:
            numeric = values.astype(float)
            finite = np.isfinite(numeric)
            if finite.any():
                return np.nanmin(numeric[finite]) >= -90.5 and np.nanmax(numeric[finite]) <= 90.5
        except Exception:
            return False
    return False


def _looks_like_lon(values: np.ndarray, units: str, dim_name: str) -> bool:
    name_lower = dim_name.lower()
    units_lower = units.lower()
    if "lon" in name_lower or "longitude" in name_lower:
        return True
    if name_lower == "x":
        try:
            numeric = values.astype(float)
            finite = np.isfinite(numeric)
            if finite.any():
                within_range = np.nanmin(numeric[finite]) >= -360.5 and np.nanmax(numeric[finite]) <= 360.5
                has_fraction = np.any(np.mod(numeric[finite], 1) != 0)
                if within_range and has_fraction:
                    return True
        except Exception:
            pass
    if any(k in units_lower for k in ["lon", "east", "west", "degrees_east", "deg"]):
        try:
            numeric = values.astype(float)
            finite = np.isfinite(numeric)
            if finite.any():
                return np.nanmin(numeric[finite]) >= -360.5 and np.nanmax(numeric[finite]) <= 360.5
        except Exception:
            return False
    return False


@dataclass
class CubePlot(metaclass=_CubePlotMeta):
    """Internal object model for cube visualizations.

    The class glues the grammar-of-graphics pieces together while keeping the
    streaming pipeline intact. It powers both pipe-style usage (``v.plot``) and
    advanced layering/faceting examples used throughout the docs.
    """

    data: Any
    aes: Optional[CubeAes] = None
    layers: List[CubeLayer] = field(default_factory=list)
    title: Optional[str] = None
    fig_title: Optional[str] = None
    legend_title: Optional[str] = None
    theme: CubeTheme = field(default_factory=theme_cube_studio)
    caption: Optional[Dict[str, Any]] = None
    size_px: int = 260
    cmap: str = "cividis"
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
    facet: Optional[CubeFacet] = None
    fill_mode: str = "shell"
    volume_density: Dict[str, int] = field(
        default_factory=lambda: {"time": 6, "x": 2, "y": 2}
    )
    volume_downsample: Dict[str, int] = field(
        default_factory=lambda: {"time": 4, "space": 4}
    )
    vase_mask: Optional[xr.DataArray] = None
    vase_outline: Any = None
    axis_meta: Dict[str, Dict[str, str]] = field(default_factory=dict)
    debug: bool = False
    viewer_id: Optional[str] = None
    viewer_width: Optional[int] = None
    viewer_height: Optional[int] = None

    def __post_init__(self) -> None:
        if self.aes is None:
            self.aes = _infer_aes_from_data(self.data)
        if not self.layers:
            self.layers.append(geom_cube())
        if self.fill_scale is None:
            palette = "diverging" if (self.fill_scale and self.fill_scale.center is not None) else "sequential"
            self.fill_scale = ScaleFillContinuous(
                cmap=self.cmap,
                palette=palette,
                name=self.legend_title,
            )
        elif self.fill_scale.center is not None and self.fill_scale.palette == "sequential":
            # Promote palette to diverging when a center is provided.
            self.fill_scale.palette = "diverging"
        if self.alpha_scale is None:
            self.alpha_scale = ScaleAlphaContinuous()
        if self.caption is None and self.fig_title is not None:
            self.caption = {"title": self.fig_title}
        if isinstance(self.data, xr.DataArray):
            self.axis_meta = self.axis_meta or self._build_axis_meta(self.data)

    def _resolve_dims(self, data: xr.DataArray) -> tuple[str | None, str | None, str | None]:
        if self.time_dim:
            t_dim = self.time_dim
            remaining = [d for d in data.dims if d != t_dim]
            y_dim, x_dim = (remaining + [None, None])[-2:]
            return t_dim, y_dim, x_dim
        return _infer_time_y_x_dims(data)

    def _build_axis_meta(self, data: xr.DataArray) -> Dict[str, Dict[str, str]]:
        def _entry(dim: str | None, kind_hint: str, label_override: Optional[str]) -> tuple[str, Dict[str, str]] | None:
            if dim is None:
                return None
            coord = data.coords.get(dim)
            dim_name = str(dim)
            if coord is not None and coord.size > 0:
                values = np.asarray(coord.values)
                units = str(coord.attrs.get("units", ""))
            else:
                values = np.arange(data.sizes.get(dim, 0))
                units = ""

            kind = kind_hint
            if kind_hint == "y":
                if _looks_like_lat(values, units, dim_name):
                    kind = "lat"
                elif _looks_like_lon(values, units, dim_name):
                    kind = "lon"
                else:
                    kind = "generic"
            elif kind_hint == "x":
                if _looks_like_lon(values, units, dim_name):
                    kind = "lon"
                elif _looks_like_lat(values, units, dim_name):
                    kind = "lat"
                else:
                    kind = "generic"
            elif kind_hint == "time":
                kind = "time"

            name_lookup = {"time": "Time", "lat": "Latitude", "lon": "Longitude"}
            base_name = label_override or name_lookup.get(kind) or str(dim).title()

            if values.size == 0:
                min_label = max_label = ""
            else:
                min_val = values.min()
                max_val = values.max()
                if kind == "time":
                    min_label = _format_time_label(min_val)
                    max_label = _format_time_label(max_val)
                elif kind == "lat":
                    min_label = _format_lat(min_val)
                    max_label = _format_lat(max_val)
                elif kind == "lon":
                    min_label = _format_lon(min_val)
                    max_label = _format_lon(max_val)
                else:
                    min_label = _format_numeric(min_val)
                    max_label = _format_numeric(max_val)

            return str(kind_hint), {"name": base_name, "min": min_label, "max": max_label}

        t_dim, y_dim, x_dim = self._resolve_dims(data)
        meta: Dict[str, Dict[str, str]] = {}
        for dim, kind, label in (
            (t_dim, "time", self.time_label),
            (y_dim, "y", self.y_label),
            (x_dim, "x", self.x_label),
        ):
            entry = _entry(dim, kind, label)
            if entry:
                key, value = entry
                meta[key] = value
        return meta

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

    def facet_wrap(self, by: str, ncol: Optional[int] = None) -> "CubePlot":
        self.facet = CubeFacet(col=by, wrap=ncol or None, by=by)
        return self

    def facet_grid(self, row: Optional[str] = None, col: Optional[str] = None) -> "CubePlot":
        self.facet = CubeFacet(row=row, col=col)
        return self

    def theme_cube_studio(self, tight_axes: bool | None = False, **kwargs: Any) -> "CubePlot":
        self.theme = theme_cube_studio(tight_axes=tight_axes, **kwargs)
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

    def geom_cube(self, **params: Any) -> "CubePlot":
        """Explicitly add a cube geometry layer."""

        return self.add_layer(geom_cube(**params))

    def stat_vase(
        self,
        vase: VaseDefinition,
        time_dim: str = "time",
        y_dim: str = "y",
        x_dim: str = "x",
    ) -> "CubePlot":
        """Attach a vase mask and masked cube to this plot via ``StatVase``.

        ``stat_vase`` computes a streaming-safe mask with
        :func:`cubedynamics.vase.build_vase_mask`, replaces ``self.data`` with
        ``cube.where(mask)``, and stores the mask on ``self.vase_mask`` for
        downstream geoms (notably ``geom_vase_outline``) or viewer overlays.
        """

        from .stats import StatVase

        stat = StatVase(
            vase=vase,
            time_dim=time_dim,
            y_dim=y_dim,
            x_dim=x_dim,
        )

        masked_cube, mask = stat.compute(self.data)
        self.data = masked_cube
        self.vase_mask = mask
        return self

    def geom_vase_outline(self, color: str = "limegreen", alpha: float = 0.6) -> "CubePlot":
        from .geom import GeomVaseOutline

        self.vase_outline = GeomVaseOutline(color=color, alpha=alpha)
        return self

    def _to_config(self) -> dict:
        da = self.data
        if not isinstance(da, xr.DataArray):
            raise TypeError("CubePlot expects an xarray.DataArray")

        payload = {
            "name": da.name or "",
            "shape": list(da.shape),
            "dims": list(da.dims),
            "coords": {k: v.values.tolist() for k, v in da.coords.items()},
            "values": da.data.tolist(),
            "attrs": dict(getattr(da, "attrs", {})),
        }

        return {
            "mode": "single",
            "data": payload,
            "title": self.title,
            "options": {
                "size_px": self.size_px,
                "width_px": self.viewer_width,
                "height_px": self.viewer_height,
                "thin_time_factor": self.thin_time_factor,
                "time_label": self.time_label,
                "x_label": self.x_label,
                "y_label": self.y_label,
                "legend_title": self.legend_title,
                "theme": self.theme.to_dict() if hasattr(self.theme, "to_dict") else {},
                "fill_mode": self.fill_mode,
            },
        }

    def to_html(self) -> str:
        da = self.data
        if not isinstance(da, xr.DataArray):
            raise TypeError("CubePlot expects an xarray.DataArray")

        def _apply_stat(data_obj: xr.DataArray) -> xr.DataArray:
            primary_layer = self.layers[0] if self.layers else geom_cube()
            layer_data = primary_layer.data if primary_layer.data is not None else data_obj
            layer_aes = primary_layer.aes if primary_layer.aes is not None else self.aes
            stat_fn = _STAT_REGISTRY.get(primary_layer.stat or "identity", stat_identity)
            return stat_fn(layer_data, layer_aes or CubeAes(), primary_layer.params)

        def _annot_block() -> str:
            if not self.annotations:
                return ""
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
            return "".join(annot_html_parts)

        def _panel_label(idx: int, extra: str | None = None) -> str:
            label = string.ascii_lowercase[idx % len(string.ascii_lowercase)]
            suffix = f" {extra}" if extra else ""
            return f"<div class='cube-facet-label'>({label}){suffix}</div>"

        def _render_viewer(
            stat_data: xr.DataArray,
            fill_scale: ScaleFillContinuous,
            legend_title: Optional[str],
            *,
            facet_idx: int = 0,
            show_legend: bool = True,
            axis_meta: Optional[Dict[str, Dict[str, str]]] = None,
        ) -> str:
            base, ext = os.path.splitext(self.out_html)
            panel_path = f"{base}_facet{facet_idx}{ext or '.html'}" if self.facet else self.out_html
            viewer_obj = cube_from_dataarray(
                stat_data,
                out_html=panel_path,
                cmap=fill_scale.resolved_cmap(),
                size_px=self.size_px,
                width_px=self.viewer_width,
                height_px=self.viewer_height,
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
                return_html=True,
                show_legend=show_legend,
                fill_mode=self.fill_mode,
                volume_density=self.volume_density,
                volume_downsample=self.volume_downsample,
                vase_mask=self.vase_mask,
                vase_outline=self.vase_outline,
                axis_meta=axis_meta,
                fig_id=self.viewer_id,
                debug=self.debug,
            )
            return viewer_obj

        fill_scale = self.fill_scale or ScaleFillContinuous(cmap=self.cmap)

        caption_html = _build_caption(self.caption)
        caption_html += _annot_block()

        theme_vars = {
            "--cube-title-font-size": f"{self.theme.title_font_size}px",
            "--cube-title-color": self.theme.title_color,
            "--cube-axis-color": self.theme.axis_color,
            "--cube-legend-color": self.theme.legend_color,
            "--cube-axis-font-size": f"{max(self.theme.title_font_size * self.theme.axis_scale, 11):.1f}px",
            "--cube-legend-font-size": f"{max(self.theme.title_font_size * self.theme.legend_scale, 11):.1f}px",
            "--cube-bg-color": self.theme.bg_color,
            "--cube-panel-color": self.theme.panel_color,
            "--cube-shadow-strength": str(self.theme.shadow_strength),
            "--cube-caption-font-size": f"{self.theme.title_font_size * self.theme.axis_scale * self.theme.caption_font_scale}px",
            "--cube-font-family": self.theme.title_font_family,
        }

        figure_style = " ".join(f"{k}: {v};" for k, v in theme_vars.items())

        if not self.facet:
            stat_data = _apply_stat(da)
            fill_limits = fill_scale.infer_limits(stat_data)
            if fill_scale.units is None:
                units_attr = getattr(stat_data, "attrs", {}).get("units")
                if isinstance(units_attr, str) and units_attr.strip():
                    fill_scale.units = units_attr.strip()

            base_legend_title = fill_scale.name or _derive_legend_title(stat_data, self.legend_title)
            legend_title = (
                f"{base_legend_title} ({fill_scale.units})"
                if base_legend_title and fill_scale.units
                else base_legend_title
            )
            axis_meta = self.axis_meta or self._build_axis_meta(stat_data)
            viewer_html = _render_viewer(
                stat_data, fill_scale, legend_title, axis_meta=axis_meta
            )
            return (
                "<div class='cube-figure' style="
                f"font-family:{self.theme.title_font_family}; background:{self.theme.bg_color}; padding:16px; border-radius:12px; box-shadow:0 16px 40px rgba(0,0,0,{self.theme.shadow_strength});"
                f" color:{self.theme.axis_color};" + "'>"
                "<style>"
                " .cube-figure{margin:8px auto; max-width: 1200px;}"
                " .cube-viewer{padding:" + str(self.theme.panel_padding) + "px; background:" + self.theme.panel_color + "; border-radius: 14px;}"
                " .cube-legend-title{font-size: var(--cube-axis-font-size,12px); color: var(--cube-legend-color, #222); margin-bottom:6px;}"
                " .cube-caption{margin-top:12px; color: var(--cube-axis-color,#222); font-size: var(--cube-caption-font-size,12px); line-height:1.4;}"
                " .cube-caption-label{display:inline-block; margin-right:6px; color: var(--cube-axis-color,#222);}"
                " .cube-caption-title{display:inline-block; margin-right:8px; color: var(--cube-title-color,#222);}"
                " .cube-caption-text{margin-top:4px; color: var(--cube-axis-color,#222);}"
                " .cube-annotations{margin-top:8px; font-size: var(--cube-caption-font-size,12px); color: var(--cube-axis-color,#222);}"
                " .cube-annot{margin-top:2px;}"
                "</style>"
                f"<div class='cube-viewer' style='{figure_style}'>{viewer_html}</div>"
                f"{caption_html}"
                "</div>"
            )

        # Faceted rendering
        facet_panels: List[Tuple[str, xr.DataArray]] = []
        facet_spec = self.facet
        assert facet_spec is not None

        def _unique_values(coord: xr.DataArray) -> Iterable[Any]:
            seen = []
            for v in coord.values.tolist():
                if v not in seen:
                    seen.append(v)
            return seen

        if facet_spec.by:
            by = facet_spec.by
            if by not in da.coords and by not in da.dims:
                raise ValueError(f"Facet variable '{by}' not found in coordinates or dimensions")
            values = list(_unique_values(da[by]))
            for v in values:
                facet_panels.append((f"{by} = {v}", da.sel({by: v})))
            ncol = facet_spec.wrap or len(values)
        else:
            row_vals = list(_unique_values(da[facet_spec.row])) if facet_spec.row else [None]
            col_vals = list(_unique_values(da[facet_spec.col])) if facet_spec.col else [None]
            for r in row_vals:
                for c in col_vals:
                    sel_dict = {}
                    label_parts = []
                    if facet_spec.row:
                        sel_dict[facet_spec.row] = r
                        label_parts.append(f"{facet_spec.row} = {r}")
                    if facet_spec.col:
                        sel_dict[facet_spec.col] = c
                        label_parts.append(f"{facet_spec.col} = {c}")
                    subset = da.sel(sel_dict) if sel_dict else da
                    facet_panels.append((", ".join(label_parts), subset))
            ncol = len(col_vals)

        stat_arrays = [
            _apply_stat(subset) for _, subset in facet_panels
        ]
        combined = xr.concat(stat_arrays, dim="__facet__") if len(stat_arrays) > 1 else stat_arrays[0]
        fill_limits = fill_scale.infer_limits(combined)
        if fill_scale.units is None:
            units_attr = getattr(combined, "attrs", {}).get("units")
            if isinstance(units_attr, str) and units_attr.strip():
                fill_scale.units = units_attr.strip()

        base_legend_title = fill_scale.name or _derive_legend_title(combined, self.legend_title)
        legend_title = (
            f"{base_legend_title} ({fill_scale.units})"
            if base_legend_title and fill_scale.units
            else base_legend_title
        )

        panel_html = []
        for idx, (label_meta, stat_data) in enumerate(zip(facet_panels, stat_arrays)):
            title_text, _ = label_meta
            axis_meta = self.axis_meta or self._build_axis_meta(stat_data)
            viewer_html = _render_viewer(
                stat_data,
                fill_scale,
                legend_title,
                facet_idx=idx,
                show_legend=idx == 0,
                axis_meta=axis_meta,
            )
            panel_html.append(
                "<div class='cube-facet-panel'>" + _panel_label(idx, title_text) + viewer_html + "</div>"
            )

        grid_style = f"grid-template-columns: repeat({ncol}, minmax(320px, 1fr)); gap: 18px;"

        return (
            "<div class='cube-figure' style="
            f"font-family:{self.theme.title_font_family}; background:{self.theme.bg_color}; padding:18px; border-radius:14px; box-shadow:0 16px 40px rgba(0,0,0,{self.theme.shadow_strength});"  # noqa: E501
            f" color:{self.theme.axis_color};" + "'>"
            "<style>"
            " .cube-figure{margin:10px auto; max-width: 1400px;}"
            " .cube-viewer{padding:" + str(self.theme.panel_padding) + "px; background:" + self.theme.panel_color + "; border-radius: 14px;}"
            " .cube-facets{display:grid;" + grid_style + " align-items:start;}"
            " .cube-facet-panel{position:relative; padding-top:6px;}"
            " .cube-facet-label{position:absolute; top:8px; left:12px; z-index:10; background:rgba(255,255,255,0.8); color:" + self.theme.axis_color + "; font-size: 12px; font-weight:600; padding:2px 6px; border-radius:6px; box-shadow:0 2px 6px rgba(0,0,0,0.08);}"
            " .cube-legend-title{font-size: var(--cube-axis-font-size,12px); color: var(--cube-legend-color, #222); margin-bottom:6px;}"
            " .cube-caption{margin-top:14px; color: var(--cube-axis-color,#222); font-size: var(--cube-caption-font-size,12px);}"
            " .cube-caption-label{display:inline-block; margin-right:6px; color: var(--cube-axis-color,#222);}"
            " .cube-caption-title{display:inline-block; margin-right:8px; color: var(--cube-title-color,#222);}"
            " .cube-caption-text{margin-top:4px; color: var(--cube-axis-color,#222);}"
            " .cube-annotations{margin-top:8px; font-size: var(--cube-caption-font-size,12px); color: var(--cube-axis-color,#222);}"
            " .cube-annot{margin-top:2px;}"
            "</style>"
            f"<div class='cube-facets' style='{figure_style}'>{''.join(panel_html)}</div>"
            f"{caption_html}"
            "</div>"
        )

    def save(self, path: str, format: Optional[str] = None, dpi: int = 150) -> None:
        """Save the cube figure to disk.

        Currently supports HTML output natively. PNG export can be added in
        environments with a headless browser; for now a clear error is raised
        guiding users to HTML snapshots.
        """

        fmt = format or os.path.splitext(path)[1].lstrip(".").lower()
        if fmt == "":
            fmt = "html"

        html_out = self.to_html()

        if fmt == "html":
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_out)
            return
        if fmt == "png":
            raise NotImplementedError(
                "PNG export requires a rasterizer. Export HTML and snapshot it with a headless browser."
            )
        raise NotImplementedError(f"Unsupported export format '{fmt}'. Supported: html, png (stub)")

    def _repr_html_(self) -> str:  # pragma: no cover - exercised in notebooks
        logger.info("CubePlot._repr_html_ called for %s", getattr(self.data, "name", None))
        config_json = json.dumps(self._to_config())
        dom_id = _new_cubeplot_dom_id()
        return _CUBEPLOT_HTML_TEMPLATE.substitute(
            dom_id=dom_id,
            width=self.viewer_width or self.size_px,
            height=self.viewer_height or self.size_px,
            config_json=config_json,
        )


_CUBEPLOT_HTML_TEMPLATE = string.Template(
    dedent(
        """
<div id="${dom_id}"
     class="cubeplot-wrapper"
     style="width: ${width}px; height: ${height}px;">
  <canvas class="cubeplot-canvas"></canvas>

  <div class="cubeplot-overlay">
    <div class="cubeplot-scale-bar">
      <span class="cubeplot-scale-label">scale</span>
    </div>
  </div>
</div>

<style>
.cubeplot-wrapper {
  position: relative;
  display: block;
  overflow: hidden;
}
.cubeplot-canvas {
  width: 100%;
  height: 100%;
  display: block;
}
.cubeplot-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.cubeplot-scale-bar {
  position: absolute;
  bottom: 0.75rem;
  right: 0.75rem;
  pointer-events: none;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}
</style>

<script>
(function(global) {
  if (typeof global.CubePlotScene === "function") return;

  function CubePlotScene(canvas, config) {
    console.log("CubePlotScene config:", config);
    this.canvas = canvas;
    this.config = config || {};
    this.rotationX = 0.7;
    this.rotationY = 0.9;
    this.zoom = 1.1;
    this.zoomMin = 0.35;
    this.zoomMax = 6.0;
    this.dragging = false;
    this.lastX = 0;
    this.lastY = 0;
    this.gl = this.canvas ? this.canvas.getContext("webgl", { antialias: true }) : null;
    this.lines = null;
    this.program = null;
    this._animating = true;
    this._animate = this._animate.bind(this);
    this.cubeOffsets = [];

    this._bindEvents();
    this._initGL();
    this._initScene();
    this.resize();
    requestAnimationFrame(this._animate);
  }

  CubePlotScene.prototype._dimsToScale = function(payload) {
    const dims = payload && Array.isArray(payload.shape) ? payload.shape.slice(-3) : [1, 1, 1];
    const maxDim = Math.max(...dims.map(v => Math.max(1, Math.abs(v))));
    if (!maxDim) return [1, 1, 1];
    return dims.map(v => (v / maxDim) || 1);
  };

  CubePlotScene.prototype._buildWireframe = function(scaleVec) {
    if (!this.gl) return;
    const gl = this.gl;
    const sx = (scaleVec && scaleVec[0]) || 1;
    const sy = (scaleVec && scaleVec[1]) || 1;
    const sz = (scaleVec && scaleVec[2]) || 1;

    const cubeVerts = new Float32Array([
      -sx, -sy, -sz,   sx, -sy, -sz,   sx,  sy, -sz,   -sx,  sy, -sz,
      -sx, -sy,  sz,   sx, -sy,  sz,   sx,  sy,  sz,   -sx,  sy,  sz
    ]);

    this.lines = new Uint16Array([
      0,1, 1,2, 2,3, 3,0,
      4,5, 5,6, 6,7, 7,4,
      0,4, 1,5, 2,6, 3,7
    ]);

    const vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, cubeVerts, gl.STATIC_DRAW);

    const lbo = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, lbo);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, this.lines, gl.STATIC_DRAW);

    const posLoc = gl.getAttribLocation(this.program, "pos");
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 3, gl.FLOAT, false, 0, 0);

    console.log("Added wireframe cube to scene");
  };

  CubePlotScene.prototype._buildSingleCube = function(payload) {
    console.log("CubePlotScene _buildSingleCube payload:", payload);
    this.cubeOffsets = [0];
    const scaleVec = this._dimsToScale(payload || {});
    this._buildWireframe(scaleVec);
  };

  CubePlotScene.prototype._buildPairedCubes = function(cubes) {
    console.log("CubePlotScene _buildPairedCubes payload:", cubes);
    const count = Array.isArray(cubes) ? cubes.length : 0;
    const spacing = 2.4;
    const start = -spacing * (count - 1) / 2;
    this.cubeOffsets = Array.from({ length: count || 1 }, (_, idx) => start + idx * spacing);
    const firstPayload = count > 0 ? (cubes[0].data || cubes[0]) : {};
    const scaleVec = this._dimsToScale(firstPayload || {});
    this._buildWireframe(scaleVec);
  };

  CubePlotScene.prototype._initScene = function() {
    if (this.config && this.config.mode === "paired" && Array.isArray(this.config.cubes)) {
      this._buildPairedCubes(this.config.cubes);
      return;
    }
    const payload = (this.config && (this.config.data || this.config)) || {};
    this._buildSingleCube(payload);
  };

  CubePlotScene.prototype._bindEvents = function() {
    if (!this.canvas) return;
    this.canvas.addEventListener("pointerdown", (ev) => {
      this.dragging = true;
      this.lastX = ev.clientX;
      this.lastY = ev.clientY;
      this.canvas.setPointerCapture(ev.pointerId);
    });

    this.canvas.addEventListener("pointerup", (ev) => {
      this.dragging = false;
      this.canvas.releasePointerCapture(ev.pointerId);
    });

    this.canvas.addEventListener("pointermove", (ev) => {
      if (!this.dragging) return;
      const dx = ev.clientX - this.lastX;
      const dy = ev.clientY - this.lastY;
      this.rotationY += dx * 0.01;
      this.rotationX += dy * 0.01;
      this.lastX = ev.clientX;
      this.lastY = ev.clientY;
    });

    this.canvas.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      const delta = ev.deltaY > 0 ? 0.9 : 1.1;
      this.zoom = Math.min(this.zoomMax, Math.max(this.zoomMin, this.zoom * delta));
    }, { passive: false });
  };

  CubePlotScene.prototype._initGL = function() {
    if (!this.gl) return;
    const gl = this.gl;
    const vertSrc = `
      attribute vec3 pos;
      uniform mat4 mvp;
      void main() {
        gl_Position = mvp * vec4(pos, 1.0);
      }
    `;
    const fragSrc = `
      precision mediump float;
      void main() {
        gl_FragColor = vec4(0.05, 0.32, 0.55, 1.0);
      }
    `;

    function compile(type, src) {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, src);
      gl.compileShader(shader);
      return shader;
    }

    const vs = compile(gl.VERTEX_SHADER, vertSrc);
    const fs = compile(gl.FRAGMENT_SHADER, fragSrc);
    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    this.program = program;
    gl.useProgram(program);

    const cubeVerts = new Float32Array([
      -1,-1,-1,  1,-1,-1,  1,1,-1,  -1,1,-1,
      -1,-1, 1,  1,-1, 1,  1,1, 1,  -1,1, 1
    ]);

    this.lines = new Uint16Array([
      0,1, 1,2, 2,3, 3,0,
      4,5, 5,6, 6,7, 7,4,
      0,4, 1,5, 2,6, 3,7
    ]);

    const vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, cubeVerts, gl.STATIC_DRAW);

    const lbo = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, lbo);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, this.lines, gl.STATIC_DRAW);

    const posLoc = gl.getAttribLocation(this.program, "pos");
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 3, gl.FLOAT, false, 0, 0);
  };

  CubePlotScene.prototype.resize = function(width, height) {
    if (!this.canvas || !this.gl) return;
    if (!width || !height) {
      const rect = this.canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
    }
    this.canvas.width = width;
    this.canvas.height = height;
    this.gl.viewport(0, 0, this.gl.drawingBufferWidth, this.gl.drawingBufferHeight);
  };

  CubePlotScene.prototype._draw = function() {
    if (!this.gl || !this.canvas || !this.program || !this.lines) return;
    const gl = this.gl;
    gl.clearColor(1,1,1,0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    const aspect = this.canvas.width / this.canvas.height;
    const fov = 1.0;
    const near = 0.1;
    const far = 20.0;

    const persp = (a,f,n,r) => {
      const t = n * Math.tan(f/2);
      return new Float32Array([
        n/t,0,0,0,
        0,n/(t/a),0,0,
        0,0,-(r+n)/(r-n),-1,
        0,0,-(2*r*n)/(r-n),0
      ]);
    };

    const rotX = a => new Float32Array([
      1,0,0,0,
      0, Math.cos(a), -Math.sin(a),0,
      0, Math.sin(a), Math.cos(a),0,
      0,0,0,1
    ]);

    const rotY = a => new Float32Array([
      Math.cos(a),0, Math.sin(a),0,
      0,1,0,0,
      -Math.sin(a),0, Math.cos(a),0,
      0,0,0,1
    ]);

    const proj = persp(aspect, fov, near, far);
    const rx = rotX(this.rotationX);
    const ry = rotY(this.rotationY);
    const scale = new Float32Array([
      this.zoom,0,0,0,
      0,this.zoom,0,0,
      0,0,this.zoom,0,
      0,0,0,1
    ]);

    const translate = (x,y,z) => new Float32Array([
      1,0,0,x,
      0,1,0,y,
      0,0,1,z,
      0,0,0,1
    ]);

    const mul = (a,b) => {
      const o=new Float32Array(16);
      for (let i=0;i<4;i++)
      for (let j=0;j<4;j++){
        o[i*4+j]=0;
        for (let k=0;k<4;k++)
          o[i*4+j]+=a[i*4+k]*b[k*4+j];
      }
      return o;
    };
    const baseMvp = mul(proj, mul(scale, mul(ry, rx)));

    const loc = gl.getUniformLocation(this.program,"mvp");
    for (let idx = 0; idx < this.cubeOffsets.length; idx++) {
      const offset = this.cubeOffsets[idx] || 0;
      const mvp = mul(baseMvp, translate(offset, 0, 0));
      gl.uniformMatrix4fv(loc,false,mvp);
      gl.drawElements(gl.LINES, this.lines.length, gl.UNSIGNED_SHORT, 0);
    }
  };

  CubePlotScene.prototype._animate = function() {
    if (!this._animating) return;
    requestAnimationFrame(this._animate);
    this._draw();
  };

  CubePlotScene.prototype.dispose = function() {
    this._animating = false;
  };

  global.CubePlotScene = CubePlotScene;
})(window);
</script>

<script>
(function() {
  window.CUBE_PLOTS = window.CUBE_PLOTS || {};

  const domId = "{dom_id}";
  const root = document.getElementById(domId);
  if (!root) return;

  const canvas = root.querySelector(".cubeplot-canvas");
  if (!canvas) return;

  const config = {config_json};

  const overlayLabel = root.querySelector(".cubeplot-scale-label");
  if (overlayLabel) {
    overlayLabel.textContent = (config && (config.title || (config.options && config.options.title))) || "scale";
  }

  if (typeof window.CubePlotScene !== "function") {
    console.error("CubePlotScene is not defined on window");
    return;
  }

  const scene = new window.CubePlotScene(canvas, config);
  window.CUBE_PLOTS[domId] = scene;

  function handleResize() {
    const rect = root.getBoundingClientRect();
    if (scene && typeof scene.resize === "function") {
      scene.resize(rect.width, rect.height);
    }
  }

  window.addEventListener("resize", handleResize);
  handleResize();
})();
</script>
"""
    )
)


__all__ = [
    "CubePlot",
    "CubeTheme",
    "theme_cube_studio",
    "CubeAes",
    "CubeLayer",
    "CubeAnnotation",
    "CubeFacet",
    "ScaleFillContinuous",
    "ScaleAlphaContinuous",
    "CoordCube",
    "geom_cube",
    "geom_slice",
    "geom_outline",
    "geom_path3d",
]
