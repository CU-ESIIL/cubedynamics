from __future__ import annotations

"""Lightweight multi-cube viewer used by ``v.plot_mean``.

The class mirrors :class:`~cubedynamics.plotting.cube_plot.CubePlot`'s HTML
emission pattern so notebook outputs stay self contained: the template embeds
the JS viewer (``CubePlotScene``) and bootstraps it with a JSON configuration.
"""

import json
from typing import Iterable, List

from IPython.display import HTML, display
import xarray as xr

from cubedynamics.plotting.cube_plot import _CUBEPLOT_HTML_TEMPLATE
from cubedynamics.plotting.cube_viewer import _new_cubeplot_dom_id

__all__: List[str] = ["MultiCubePlot"]


class MultiCubePlot:
    """A paired cube viewer that renders multiple cubes in a single scene."""

    def __init__(
        self,
        cubes: Iterable[xr.DataArray],
        labels: Iterable[str] | None = None,
        *,
        title: str = "Mean / Variance",
        width: int = 1000,
        height: int = 500,
        **options,
    ) -> None:
        self.cubes = list(cubes)
        self.labels = list(labels) if labels is not None else [f"Cube {i + 1}" for i in range(len(self.cubes))]
        self.title = title
        self.width = width
        self.height = height
        self.options = options

    def _to_config(self) -> dict:
        def da_to_payload(da: xr.DataArray) -> dict:
            return {
                "name": da.name or "",
                "shape": list(da.shape),
                "dims": list(da.dims),
                "values": da.values.tolist(),
                "attrs": dict(getattr(da, "attrs", {})),
            }

        return {
            "mode": "paired",
            "title": self.title,
            "cubes": [
                {"label": label, "data": da_to_payload(da)}
                for label, da in zip(self.labels, self.cubes)
            ],
            "options": self.options,
        }

    def _repr_html_(self) -> str:  # pragma: no cover - exercised in notebooks
        dom_id = _new_cubeplot_dom_id("cubeplot-paired")
        config_json = json.dumps(self._to_config())
        return _CUBEPLOT_HTML_TEMPLATE.substitute(
            dom_id=dom_id,
            width=self.width,
            height=self.height,
            config_json=config_json,
        )

    def show(self) -> "MultiCubePlot":
        display(HTML(self._repr_html_()))
        return self

