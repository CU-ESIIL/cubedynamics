"""Small deterministic API controls; no invented values in live QA evidence."""
import copy
import json
import numpy as np
import pytest
from cubedynamics import pipe, verbs as v
from cubedynamics.data.lifecycle import SourceChange, SourceMode, decide_source_change
from cubedynamics.data.schema import schema_fingerprint
from examples.source_projects.usgs.proof import query, normalize, complete_features, streamflow, MAX_ROWS

SITE="USGS-06730200"
START="2026-08-26T00:00:00Z"
END="2026-08-26T23:59:59Z"


@pytest.fixture
def payload():
    rows=[]
    for i,status in enumerate(("Approved","Provisional")):
        rows.append({"id":f"record-{i}","properties":{"monitoring_location_id":SITE,
            "parameter_code":"00060","time_series_id":"a"*32,"statistic_id":"00011",
            "unit_of_measure":"ft^3/s","time":f"2026-08-26T00:{i*15:02}:00Z","value":str(10+i),
            "approval_status":status,"qualifier":"e" if i else None,"last_modified":"2026-08-27T00:00:00Z"}})
    body={"features":rows,"links":[],"numberMatched":2}
    site={"id":SITE,"geometry":{"type":"Point","coordinates":[-105.178333,40.051667]},
          "properties":{"monitoring_location_name":"Unit test control"}}
    meta={"id":"a"*32,"properties":{"monitoring_location_id":SITE,"parameter_code":"00060",
          "unit_of_measure":"ft^3/s","statistic_id":"00011"}}
    return body,site,meta


def normalized(payload):
    return normalize(*payload,site=SITE,start=START,end=END,provenance={"retrieved_at":"test"})


def test_query_has_single_site_parameter_time_and_limit():
    params=query(SITE,START,END)
    assert params["monitoring_location_id"]==SITE
    assert params["parameter_code"]=="00060"
    assert params["limit"]==MAX_ROWS
    assert "/" in params["time"] and ".." not in params["time"]


@pytest.mark.parametrize("site,start,end",[("*",START,END),(SITE,"2020-01-01T00:00Z",END),
    (SITE,END,START),(SITE,"2026-08-26",END),(SITE,START,START),(SITE,"NaT",END)])
def test_unbounded_or_invalid_request_rejected(site,start,end):
    with pytest.raises(ValueError): query(site,start,end)


def test_units_status_qualifier_identity_provenance_and_pipe(payload):
    with pytest.warns(UserWarning,match="provisional"):
        cube=normalized(payload)
    assert cube.streamflow.attrs["units"]=="ft^3/s"
    assert cube.time_series_id.item()=="a"*32
    assert [json.loads(s) for s in cube.approval_status.values]==["Approved","Provisional"]
    assert [json.loads(s) for s in cube.qualifier.values]==[None,"e"]
    assert cube.station.item()==SITE
    assert json.loads(cube.attrs["provenance"])["retrieved_at"]=="test"
    mean=(pipe(cube)|v.mean(dim="time")).unwrap()
    assert mean.streamflow.item()==10.5
    json.dumps(cube.attrs)


def test_reorders_without_dropping_and_preserves_utc(payload):
    payload[0]["features"].reverse()
    cube=normalized(payload)
    assert (np.diff(cube.time.values)>np.timedelta64(0,"s")).all()
    assert cube.coords["time"].attrs["timezone"]=="UTC"
    assert cube.streamflow.values[:,0].tolist()==[10,11]


@pytest.mark.parametrize("field,value",[("parameter_code","00065"),("monitoring_location_id","USGS-00000000"),
    ("unit_of_measure","m3/s"),("time_series_id","b"*32),("time","2020-01-01T00:00Z"),
    ("value","Ice"),("value","inf"),("statistic_id","00003")])
def test_invalid_or_ambiguous_observations_fail_closed(payload,field,value):
    payload[0]["features"][0]["properties"][field]=value
    with pytest.raises(ValueError): normalized(payload)


def test_duplicate_timestamp_not_silently_averaged(payload):
    payload[0]["features"][1]["properties"]["time"]=payload[0]["features"][0]["properties"]["time"]
    with pytest.raises(ValueError,match="duplicate"): normalized(payload)


def test_missing_status_remains_null_not_approved(payload):
    del payload[0]["features"][0]["properties"]["approval_status"]
    cube=normalized(payload)
    assert json.loads(cube.approval_status.values[0]) is None


def test_missing_value_not_fabricated(payload):
    payload[0]["features"][0]["properties"]["value"]=None
    cube=normalized(payload)
    assert np.isnan(cube.streamflow.values[0,0])


@pytest.mark.parametrize("kind",["next","empty","too_many","incomplete"])
def test_pagination_safety(payload,kind):
    body=payload[0]
    if kind=="next": body["links"]=[{"rel":"next","href":"https://other.example/escape"}]
    elif kind=="empty": body["features"]=[]
    elif kind=="too_many": body["features"]*=MAX_ROWS
    else: body["numberMatched"]=MAX_ROWS
    with pytest.raises(ValueError): complete_features(body)


def test_rolling_approval_content_changes_do_not_change_interpretation_schema(payload):
    cube=normalized(payload)
    modified=copy.deepcopy(payload)
    for feature in modified[0]["features"]:
        feature["properties"]["approval_status"]="Approved"
        feature["properties"]["qualifier"]="different-length-qualifier"
        feature["properties"]["value"]="12.5"
        feature["id"]="new-record-version-identifier"
    updated=normalized(modified)
    assert schema_fingerprint(cube)==schema_fingerprint(updated)
    decision=decide_source_change(SourceChange.CONTENT_EXTENSION,source_mode=SourceMode.ROLLING)
    assert not decision.creates_candidate_revision
    assert cube.attrs["source_mode"]=="rolling"
    assert "serving_revision" not in cube.attrs
    refresh=decide_source_change(SourceChange.OBSERVATION_UPDATE,source_mode=SourceMode.ROLLING)
    assert not refresh.creates_candidate_revision and refresh.compare_history
    snapshot=decide_source_change(SourceChange.OBSERVATION_UPDATE,source_mode=SourceMode.SNAPSHOT)
    assert snapshot.creates_candidate_revision


@pytest.mark.online
@pytest.mark.integration
def test_usgs_one_day_real():
    cube=streamflow(site=SITE,start=START,end=END)
    assert 0<cube.sizes["time"]<=MAX_ROWS
    assert cube.station.item()==SITE
    assert cube.streamflow.attrs["units"]
    assert np.isfinite(cube.streamflow.values).all()
    assert "approval_status" in cube.coords and "qualifier" in cube.coords
