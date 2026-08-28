"""Range/coverage failure controls and native feature semantics."""
import io
import json

import numpy as np
import pytest
from rasterio.transform import from_origin
from rasterio.windows import bounds

from cubedynamics.data import three_dep, roads
from cubedynamics.data._ranges import RangeFile
from cubedynamics.data._transport import ReadLimits, SourceBudgetError, SourceSchemaError
from test_source_project_roads import osm, overture, BBOX


class Client:
    limits=ReadLimits(bytes=100)
    bytes=0
    etag='"v1"'
    content_range=None
    def __init__(self): self.trace=[]; self.calls=[]
    def get(self,url,*,headers,max_bytes):
        self.calls.append(headers)
        interval=headers["Range"].split("=")[1]
        self.trace.append({"status":206,"headers":{"Content-Range":self.content_range or f"bytes {interval}/1000","ETag":self.etag}})
        raw=b"x"*max_bytes
        self.bytes+=len(raw)
        return raw


def test_ranges_pin_every_read_to_original_object():
    client=Client()
    with RangeFile("https://example.test/data",client) as remote:
        assert remote.read(10)==b"x"*10
        assert client.calls[-1]["If-Match"]=='"v1"'
        remote.seek(-2,io.SEEK_END)
        assert remote.read(10)==b"xx"
        assert remote.read(10)==b""
        with pytest.raises(ValueError): remote.seek(0,99)


@pytest.mark.parametrize("fault",["etag","range","missing_etag","weak_etag"])
def test_changed_or_unverifiable_range_object_rejected(fault):
    client=Client()
    if fault in ("missing_etag","weak_etag"):
        client.etag=None if fault=="missing_etag" else 'W/"v1"'
        with pytest.raises(SourceSchemaError): RangeFile("https://example.test/data",client)
    else:
        remote=RangeFile("https://example.test/data",client)
        if fault=="etag": client.etag='"v2"'
        else: client.content_range="bytes 10-19/1000"
        with pytest.raises(SourceSchemaError): remote.read(10)


def test_whole_object_and_budget_reads_fail_before_request():
    client=Client(); remote=RangeFile("https://example.test/data",client)
    for size in (-1,1000,100):
        with pytest.raises(SourceBudgetError): remote.read(size)
    assert len(client.calls)==1


def test_prefetched_columns_do_not_issue_individual_requests():
    client = Client()
    with RangeFile("https://example.test/data", client) as remote:
        remote.prefetch(100, 50)
        assert remote.tell() == 0
        for offset in (100, 110, 140):
            remote.seek(offset)
            assert remote.read(10) == b"x" * 10
        assert len(client.calls) == 2  # One probe and one coalesced span.
        remote.seek(150)
        remote.read(10)
        assert len(client.calls) == 3


def test_native_cells_exact_edges_and_no_silent_tile_clipping():
    transform=from_origin(-106,40,.001,.001)
    bbox=(-105.99,39.98,-105.98,39.99)
    window,_=three_dep.pixel_window(bbox,"EPSG:4326",transform,1000,1000)
    assert tuple(window.flatten())==(10,10,10,10)
    np.testing.assert_allclose(bounds(window,transform),bbox)
    with pytest.raises(SourceSchemaError,match="partial"):
        three_dep.pixel_window((-106.001,39.999,-105.999,40.001),"EPSG:4326",transform,10,10)


def test_elevation_query_limits_before_network(monkeypatch):
    monkeypatch.setattr(three_dep,"SourceClient",lambda **kw:pytest.fail("network constructed"))
    for bbox in ((-180,-90,180,90),(-105,40,-104,41),(0,0,.01,.01)):
        with pytest.raises(ValueError): three_dep.elevation(bbox=bbox)


def test_elevation_decoder_capability_fails_before_network(monkeypatch):
    monkeypatch.setattr(three_dep.rasterio,"__version__","1.3.11")
    monkeypatch.setattr(three_dep,"SourceClient",lambda **kw:pytest.fail("network constructed"))
    with pytest.raises(ImportError,match="no uncapped"):
        three_dep.elevation(bbox=(-105.30,39.985,-105.291,39.994))


def test_roads_release_and_scope_before_network(monkeypatch):
    monkeypatch.setattr(roads,"SourceClient",lambda **kw:pytest.fail("network constructed"))
    with pytest.raises(ValueError,match="explicit release"): roads.roads(source="overture",bbox=BBOX)
    with pytest.raises(ValueError): roads.roads(source="overture",bbox=BBOX,release="../../latest")
    with pytest.raises(ValueError,match="rolling"): roads.roads(source="osm",bbox=BBOX,release="2026-08-19.0")


@pytest.mark.parametrize("source,records",[("osm",[osm()]),("overture",[overture()])])
def test_roads_preserve_native_metadata_and_do_not_clip(source,records):
    frame=roads.normalize(records,source,BBOX,{"release_status":"candidate"})
    assert frame.source_feature_id.notna().all()
    assert frame.source_classification.iloc[0]=="residential"
    assert json.loads(frame.native.iloc[0])
    assert str(frame.crs)=="EPSG:4326"


def test_osm_bbox_intersection_cannot_claim_query_completeness():
    # The normalizer can retain a crossing segment; Overpass's node selection
    # may never return it. Keep that distinction explicit in API documentation.
    record=osm()
    record["geometry"]=[{"lon":BBOX[0]-.001,"lat":40.01},{"lon":BBOX[2]+.001,"lat":40.01}]
    assert len(roads.normalize([record],"osm",BBOX,{}))==1
    assert "node" in roads.roads.__doc__ and "absent" in roads.roads.__doc__


def test_overture_release_mismatch_before_partition_reads():
    pytest.importorskip("pyarrow")
    class Wrong:
        def json(self,*a,**kw): return {"release:version":"unexpected"}
    with pytest.raises(SourceSchemaError,match="release"):
        roads._overture(Wrong(),BBOX,"2026-08-19.0",{})
