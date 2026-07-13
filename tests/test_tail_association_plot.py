from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from cubedynamics.plotting.tail_association import (
    ghosh_partial_spearman,
    normalized_ranks,
    plot_tail_association_from_cube,
    plot_tail_association_grid,
    plot_tail_association_triptych,
    tail_association_stats,
)


def test_normalized_ranks_use_average_ties() -> None:
    ranks = normalized_ranks(np.array([20.0, 10.0, 20.0, 30.0]))

    assert np.allclose(ranks, np.array([2.5, 1.0, 2.5, 4.0]) / 5.0)


def test_ghosh_partial_spearman_uses_diagonal_band_and_full_variance() -> None:
    u = np.array([0.1, 0.2, 0.8, 0.9])
    v = np.array([0.1, 0.2, 0.2, 0.1])

    value, count = ghosh_partial_spearman(u, v, lower_bound=0.0, upper_bound=1.0 / 3.0)

    u_centered = u - u.mean()
    v_centered = v - v.mean()
    mask = u + v < 2.0 / 3.0
    expected = np.sum(u_centered[mask] * v_centered[mask]) / (
        (u.size - 1) * np.sqrt(np.var(u, ddof=1) * np.var(v, ddof=1))
    )
    assert count == 2
    assert np.isclose(value, expected)


def test_tail_association_stats_drop_paired_missing_values() -> None:
    stats, x, y, u, v = tail_association_stats(
        np.array([1.0, 2.0, np.nan, 4.0]),
        np.array([1.0, np.nan, 3.0, 4.0]),
    )

    assert stats.n == 2
    assert x.tolist() == [1.0, 4.0]
    assert y.tolist() == [1.0, 4.0]
    assert np.allclose(u, [1.0 / 3.0, 2.0 / 3.0])
    assert np.allclose(v, [1.0 / 3.0, 2.0 / 3.0])


def test_plot_tail_association_triptych_saves_png_and_pdf(tmp_path) -> None:
    x = np.linspace(-2.0, 2.0, 30)
    y = x + np.sin(x) * 0.1
    outpath = tmp_path / "tail_association_demo"

    fig = plot_tail_association_triptych(x, y, outpath=outpath)

    assert len(fig.axes) == 3
    assert outpath.with_suffix(".png").exists()
    assert outpath.with_suffix(".pdf").exists()
    plt.close(fig)


def test_plot_tail_association_grid_draws_two_by_three() -> None:
    x = np.linspace(-2.0, 2.0, 40)
    y = x + np.sin(x)

    fig = plot_tail_association_grid(
        [(x, y), (-x, -y)],
        row_titles=("Left-tail pair", "Right-tail pair"),
    )

    assert len(fig.axes) == 6
    assert fig.axes[0].get_title() == "Raw paired values"
    assert fig.axes[2].get_title() == "Tail bands"
    plt.close(fig)


def test_plot_tail_association_from_cube_extracts_indexed_series() -> None:
    time = np.arange(8)
    y = np.array([10.0, 20.0])
    x = np.array([100.0, 200.0])
    data = np.arange(time.size * y.size * x.size, dtype=float).reshape(time.size, y.size, x.size)
    ds = xr.Dataset(
        {
            "sync": xr.DataArray(
                data,
                dims=("time", "y", "x"),
                coords={"time": time, "y": y, "x": x},
            )
        }
    )

    fig = plot_tail_association_from_cube(
        ds,
        "sync",
        selector_a=(0, 0),
        selector_b={"sel": {"y": 20.0, "x": 200.0}},
        preprocess="anomaly",
    )

    assert len(fig.axes) == 3
    assert "anomaly" in fig.axes[0].get_title()
    plt.close(fig)
