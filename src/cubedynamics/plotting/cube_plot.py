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

import html
import os
import string

import xarray as xr

from cubedynamics.plotting.cube_viewer import cube_from_dataarray


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


def theme_cube_studio() -> CubeTheme:
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
        finite_min = float(data.min(skipna=True))
        finite_max = float(data.max(skipna=True))
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


@dataclass
class CubePlot:
    """Internal object model for cube visualizations.

    The class glues the grammar-of-graphics pieces together while keeping the
    streaming pipeline intact. It powers both pipe-style usage (``v.plot``) and
    advanced layering/faceting examples used throughout the docs.
    """

    data: Any
    aes: Optional[CubeAes] = None
    layers: List[CubeLayer] = field(default_factory=list)
    title: Optional[str] = None
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
        ) -> str:
            base, ext = os.path.splitext(self.out_html)
            panel_path = f"{base}_facet{facet_idx}{ext or '.html'}" if self.facet else self.out_html
            viewer_obj = cube_from_dataarray(
                stat_data,
                out_html=panel_path,
                cmap=fill_scale.resolved_cmap(),
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
                show_legend=show_legend,
            )
            return viewer_obj if isinstance(viewer_obj, str) else viewer_obj._repr_html_()

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
            viewer_html = _render_viewer(stat_data, fill_scale, legend_title)
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
            viewer_html = _render_viewer(stat_data, fill_scale, legend_title, facet_idx=idx, show_legend=idx == 0)
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
        return self.to_html()


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
