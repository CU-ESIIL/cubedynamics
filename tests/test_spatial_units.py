"""Tests for AOI-as-spatial-unit comparison helpers."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.stats.spatial_units import (
    aoi_signature,
    block_signature,
    collect_blocks,
    compare_aoi_signatures,
    compare_blocks,
)


def _sync_cube(scale: float = 1.0, offset: float = 0.0) -> xr.Dataset:
    time = np.datetime64("2024-01-01") + np.arange(6).astype("timedelta64[D]")
    y = np.array([40.0, 39.95])
    x = np.array([-105.1, -105.05])
    base = np.arange(time.size, dtype="float32")[:, None, None]
    spatial = np.array([[0.0, 0.2], [0.4, 0.6]], dtype="float32")
    values = base * scale + spatial + offset
    coords = {"time_window_end": time, "y": y, "x": x}
    return xr.Dataset(
        {
            "bottom_synchrony": xr.DataArray(
                values,
                dims=("time_window_end", "y", "x"),
                coords=coords,
            ),
            "top_synchrony": xr.DataArray(
                values + 1.0,
                dims=("time_window_end", "y", "x"),
                coords=coords,
            ),
            "bottom_minus_top": xr.DataArray(
                values - 1.0,
                dims=("time_window_end", "y", "x"),
                coords=coords,
            ),
        }
    )


def test_aoi_signature_reduces_space_and_names_unit() -> None:
    signature = aoi_signature(_sync_cube(), unit_id="boulder")

    assert signature.sizes["unit"] == 1
    assert signature.sizes["time_window_end"] == 6
    assert "y" not in signature.dims
    assert "x" not in signature.dims
    assert str(signature["unit"].values[0]) == "boulder"
    assert signature.attrs["analysis"] == "aoi_signature"
    assert "y_center" in signature.coords
    np.testing.assert_allclose(
        signature["bottom_synchrony"].isel(unit=0),
        _sync_cube()["bottom_synchrony"].median(("y", "x")),
    )


def test_compare_aoi_signatures_returns_pairwise_metrics() -> None:
    left = aoi_signature(_sync_cube(), unit_id="a")
    right = aoi_signature(_sync_cube(offset=2.0), unit_id="b")

    comparison = compare_aoi_signatures(left, right)

    assert comparison.attrs["left_unit"] == "a"
    assert comparison.attrs["right_unit"] == "b"
    assert set(comparison.data_vars) == {"pearson_r", "mean_difference", "rmse", "n"}
    assert comparison.sizes["variable"] == 3
    np.testing.assert_allclose(comparison["pearson_r"], 1.0, atol=1e-7)
    np.testing.assert_allclose(comparison["mean_difference"], -2.0, atol=1e-7)
    np.testing.assert_allclose(comparison["rmse"], 2.0, atol=1e-7)
    np.testing.assert_array_equal(comparison["n"], [6, 6, 6])


def test_aoi_signature_and_compare_are_pipe_ready() -> None:
    left = (pipe(_sync_cube()) | v.aoi_signature(unit_id="left")).unwrap()
    right = (pipe(_sync_cube(scale=2.0)) | v.aoi_signature(unit_id="right")).unwrap()

    comparison = (pipe(left) | v.compare_aoi_signature(right)).unwrap()

    assert comparison.attrs["analysis"] == "pairwise_aoi_signature_compare"
    np.testing.assert_allclose(comparison["pearson_r"], 1.0, atol=1e-7)


def test_block_signature_uses_block_language() -> None:
    block = block_signature(_sync_cube(), block_id="front-range")

    assert block.sizes["block"] == 1
    assert str(block["block"].values[0]) == "front-range"
    assert block.attrs["analysis"] == "block_signature"
    assert block.attrs["block_id"] == "front-range"
    assert block.attrs["block_dim"] == "block"


def test_collect_blocks_and_compare_all_pairs() -> None:
    first = block_signature(_sync_cube(), block_id="a")
    second = block_signature(_sync_cube(offset=2.0), block_id="b")
    third = block_signature(_sync_cube(scale=2.0), block_id="c")

    blocks = collect_blocks(first, second, third)
    comparison = compare_blocks(blocks)

    assert blocks.sizes["block"] == 3
    assert blocks.attrs["analysis"] == "block_collection"
    assert comparison.sizes["pair"] == 3
    assert comparison.sizes["variable"] == 3
    assert comparison.attrs["analysis"] == "block_pairwise_compare"
    assert "left_unit" not in comparison.attrs
    assert "right_unit" not in comparison.attrs
    assert set(comparison["pair"].values) == {"a__b", "a__c", "b__c"}
    np.testing.assert_allclose(comparison["pearson_r"], 1.0, atol=1e-7)


def test_block_verbs_are_pipe_ready_for_groups() -> None:
    first = (pipe(_sync_cube()) | v.block_signature(block_id="a")).unwrap()
    second = (pipe(_sync_cube(offset=2.0)) | v.block_signature(block_id="b")).unwrap()
    third = (pipe(_sync_cube(scale=2.0)) | v.block_signature(block_id="c")).unwrap()

    comparison = (
        pipe(first)
        | v.collect_blocks(second, third)
        | v.compare_blocks()
    ).unwrap()

    assert comparison.sizes["pair"] == 3
    assert set(comparison.data_vars) == {"pearson_r", "mean_difference", "rmse", "n"}
