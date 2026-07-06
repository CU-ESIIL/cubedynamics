from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from cubedynamics.viz.qa_plots import plot_tail_dependence_over_time


def test_plot_tail_dependence_over_time_draws_tail_synchrony_traces() -> None:
    time = np.datetime64("2024-01-05") + np.arange(4).astype("timedelta64[D]")
    coords = {"time_window_end": time, "y": [0, 1], "x": [0, 1]}
    dims = ("time_window_end", "y", "x")

    bottom_tail = xr.DataArray(
        np.full((4, 2, 2), 0.4),
        dims=dims,
        coords=coords,
        name="bottom_tail",
    )
    top_tail = xr.DataArray(
        np.full((4, 2, 2), 0.1),
        dims=dims,
        coords=coords,
        name="top_tail",
    )
    diff_tail = bottom_tail - top_tail

    ax = plot_tail_dependence_over_time(bottom_tail, top_tail, diff_tail, ylim=None)

    labels = [line.get_label() for line in ax.lines]
    assert labels == ["bottom half", "top half", "bottom - top"]
    assert ax.get_xlabel() == "time_window_end"
    assert ax.get_ylabel() == "Median tail dependence"
    assert "synchrony" in ax.get_title()

    plt.close(ax.figure)
