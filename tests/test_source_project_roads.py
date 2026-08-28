"""Tiny artificial geometry controls, not scientific evidence."""
import json
import pytest
from shapely.geometry import LineString
from cubedynamics import pipe
from examples.source_projects.roads.proof import (
    BBOX, CLASSES, MAX_FEATURES, normalize, osm_query, roads, within_aoi_length,
    validate_bbox, row_group_intersects, ParquetRanges,
)


def osm(highway="residential",ident=1):
    return {"type":"way","id":ident,"tags":{"highway":highway,"surface":"asphalt","name":"Test"},
            "geometry":[{"lon":-105.28,"lat":40.01},{"lon":-105.27,"lat":40.015}]}


def overture(kind="residential"):
    return {"id":"native-id","subtype":"road","class":kind,"names":{"primary":"Test"},
            "geometry":LineString([(-105.28,40.01),(-105.27,40.015)]).wkb,
            "connectors":[{"connector_id":"c1","at":0}],"access_restrictions":[{"access_type":"denied"}]}


@pytest.mark.parametrize("source,records",[("osm",[osm(),osm("footway",2)]),("overture",[overture(),overture("path")])])
def test_common_contract_preserves_source_native_fields(source,records):
    frame=normalize(records,source,BBOX,{"retrieved_at":"test"})
    assert len(frame)==1
    assert frame.source.iloc[0]==source
    assert frame.source_classification.iloc[0]=="residential"
    native=json.loads(frame.native.iloc[0])
    assert (native["tags"]["surface"]=="asphalt") if source=="osm" else native["connectors"][0]["connector_id"]=="c1"
    assert frame.attrs["source_mode"]==("rolling" if source=="osm" else "snapshot")
    json.dumps(frame.attrs)


def test_link_classes_remain_native_not_crosswalked():
    frame=normalize([osm("primary_link")],"osm",BBOX,{})
    assert frame.source_classification.iloc[0]=="primary_link"
    assert "primary_link" not in CLASSES


@pytest.mark.parametrize("bbox",[(-180,-90,180,90),(0,0,1,1),(1,1,0,0),(float("nan"),1,2,3)])
def test_large_invalid_bbox_rejected_before_network(bbox):
    with pytest.raises(ValueError): validate_bbox(bbox)


def test_query_is_small_bounded_way_request():
    q=osm_query(BBOX)
    assert "way[" in q and "[timeout:25]" in q and "out body geom 5001" in q
    assert "40.008,-105.285,40.02,-105.27" in q
    assert "footway" not in q and "track" not in q


def test_bad_ids_or_geometry_never_silently_dropped():
    with pytest.raises(ValueError,match="Duplicate"):
        normalize([osm(),osm()],"osm",BBOX,{})
    bad=osm(); bad["geometry"]=[]
    with pytest.raises(ValueError): normalize([bad],"osm",BBOX,{})
    with pytest.raises(ValueError,match="cap"):
        normalize([osm()]*(MAX_FEATURES+1),"osm",BBOX,{})


def test_explicit_clip_length_verb_composes_without_mutation():
    frame=normalize([osm()],"osm",BBOX,{})
    before=frame.geometry.copy()
    direct=within_aoi_length()(frame)
    piped=(pipe(frame)|within_aoi_length()).unwrap()
    assert direct.equals(piped) and (piped>0).all()
    assert frame.geometry.equals(before)


def test_dispatch_rejects_unknown_source():
    with pytest.raises(ValueError,match="source"):
        roads(source="imaginary")


def test_missing_row_group_statistics_refuse_unpruned_scan():
    class Group: num_columns=0
    with pytest.raises(ValueError,match="bbox"):
        row_group_intersects(Group(),BBOX)


def test_parquet_ranges_refuse_whole_object_before_network(monkeypatch):
    from examples.source_projects.roads import proof
    def fake_fetch(url,**kwargs):
        kwargs["evidence"].append({"status":206,"headers":{"Content-Range":"bytes 0-0/1000"}})
        return b"P"
    monkeypatch.setattr(proof,"fetch",fake_fetch)
    remote=ParquetRanges("https://example.test",[],[100])
    with pytest.raises(ValueError,match="Unbounded"): remote.read()
    with pytest.raises(ValueError,match="budget"): remote.read(100)
    assert remote.tell()==0


@pytest.mark.online
@pytest.mark.integration
@pytest.mark.parametrize("source",["overture","osm"])
def test_real_roads_independently(source):
    if source=="overture": pytest.importorskip("pyarrow")
    evidence={}
    frame=roads(source=source,evidence=evidence)
    assert 0<len(frame)<=MAX_FEATURES
    assert frame.is_valid.all()
    if source=="overture":
        assert evidence["parquet_bytes"]<32_000_000
        assert evidence["partitions_opened"]<=3
        assert evidence["release"]["release:version"]
    else:
        assert frame.source_feature_id.str.startswith("way/").all()
        assert sum(r["bytes"] for r in evidence["http"])<4_000_000
