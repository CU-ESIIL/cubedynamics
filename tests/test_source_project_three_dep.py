"""Deterministic synthetic unit controls; never live certification evidence."""
import numpy as np
import pytest
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds
from rasterio.windows import bounds

from examples.source_projects.three_dep.proof import pixel_window, range_evidence


def test_exact_edges_do_not_add_cells():
    transform = from_origin(-106,40,.001,.001)
    bbox = (-105.99,39.98,-105.98,39.99)
    window, _ = pixel_window(bbox,"EPSG:4326",transform,1000,1000)
    assert tuple(window.flatten()) == (10,10,10,10)
    np.testing.assert_allclose(bounds(window,transform),bbox)


def test_fractional_edges_expand_and_y_stays_north_up():
    transform = from_origin(-106,40,.001,.001)
    window, _ = pixel_window((-105.9899,39.9801,-105.9801,39.9899),"EPSG:4326",transform,1000,1000)
    assert tuple(window.flatten()) == (10,10,10,10)
    assert transform.e < 0


def test_clips_partial_edge_but_rejects_no_overlap():
    transform = from_origin(-106,40,.001,.001)
    window, _ = pixel_window((-106.001,39.999,-105.999,40.001),"EPSG:4326",transform,10,10)
    assert tuple(window.flatten()) == (0,0,1,1)
    with pytest.raises(ValueError,match="overlap"):
        pixel_window((-106.02,39.999,-106.01,40),"EPSG:4326",transform,10,10)


def test_projected_bbox_translation_covers_requested_extent():
    bbox=(-105.28,40,-105.279,40.001)
    w,s,e,n=transform_bounds("EPSG:4326","EPSG:32613",*bbox)
    transform=from_origin(w-3,n+3,10,10)
    window,native=pixel_window(bbox,"EPSG:32613",transform,100,100)
    x0,y0,x1,y1=bounds(window,transform)
    assert x0<=w and x1>=e and y0<=s and y1>=n
    np.testing.assert_allclose(native,(w,s,e,n))


@pytest.mark.parametrize("bbox",[(-180,-90,180,90),(0,0,0,1),(1,2,0,3),(float("nan"),0,1,1)])
def test_refuses_unsafe_bounds(bbox):
    with pytest.raises(ValueError):
        pixel_window(bbox,"EPSG:4326",from_origin(-106,40,.001,.001),1000,1000)


def test_actual_http_range_diagnostic_counts_repeated_bytes():
    log="Range: bytes=0-9\n< HTTP/1.1 206 Partial Content\nRange: bytes=0-9\n< HTTP/2 206"
    evidence=range_evidence(log)
    assert evidence["requested_bytes_upper_bound"]==20
    assert evidence["range_response_count"]==2


@pytest.mark.online
@pytest.mark.integration
def test_three_dep_tiny_real_window(tmp_path):
    from examples.source_projects.three_dep.proof import run
    report=run(tmp_path)
    cert=report["certification"]
    assert cert["outcome"]=="PASS_WITH_CAVEATS", cert
    assert cert["gates"]["bounded_access"]=="PASS"
    assert max(cert["evidence"]["numerical"]["shape"])<=256
