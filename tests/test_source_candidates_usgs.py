"""Runtime candidate contracts plus small reviewed real-response replay."""
import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from cubedynamics import data, pipe, verbs as v
from cubedynamics.data import usgs
from cubedynamics.data._transport import SourceSchemaError, SourceBudgetError
from test_source_project_usgs import payload, SITE, START, END


def normalized(payload):
    body, location, meta = payload
    return usgs._normalize(body["features"], location, meta, site=SITE,
                           first=pd.Timestamp(START), last=pd.Timestamp(END), trace=[])


def test_native_status_and_null_presence_are_distinct(payload,tmp_path):
    cube=normalized(payload)
    assert cube.approval_status.values.tolist()==["Approved","Provisional"]
    assert cube.qualifier.values.tolist()==["","e"]
    assert cube.qualifier_is_null.values.tolist()==[1,0]
    assert cube.qualifier_present.values.tolist()==[1,1]
    del payload[0]["features"][0]["properties"]["qualifier"]
    missing=normalized(payload)
    assert missing.qualifier_present.values.tolist()==[0,1]
    assert missing.qualifier_is_null.values.tolist()==[0,0]
    cube.to_netcdf(tmp_path/"sample.nc",engine="h5netcdf")
    with xr.open_dataset(tmp_path/"sample.nc",engine="h5netcdf") as restored:
        xr.testing.assert_equal(cube,restored.load())
    assert (pipe(cube)|v.mean(dim="time")).unwrap().streamflow.item()==10.5
    assert pipe(cube).semantic_state.dimensions==("time","station")
    assert not pipe(cube).semantic_state.spatial


@pytest.mark.parametrize("field,value",[("value","NaN"),("value","inf"),("value","Ice"),
    ("time","2026-08-26"),("time","2020-01-01T00:00Z"),("approval_status",["Approved"]),
    ("unit_of_measure","m^3/s"),("statistic_id","00003"),("parameter_code","00065")])
def test_invalid_provider_semantics_fail(payload,field,value):
    payload[0]["features"][0]["properties"][field]=value
    with pytest.raises(SourceSchemaError): normalized(payload)


def test_refresh_audit_ignores_uuids_but_records_status_value_changes(payload):
    before=normalized(payload)
    payload[0]["features"][0]["id"]="refreshed-record-uuid"
    payload[0]["features"][0]["properties"]["last_modified"]="2026-08-28T00:00Z"
    after=normalized(payload)
    assert usgs.compare_observations(before,after)=={"added":0,"removed":0,"changed":0,"unchanged":2}
    payload[0]["features"][1]["properties"]["approval_status"]="Approved"
    assert usgs.compare_observations(before,normalized(payload))["changed"]==1


class Pages:
    def __init__(self,pages): self.pages,self.calls=pages,[]
    def json(self,url,**kwargs):
        self.calls.append((url,kwargs))
        return self.pages.pop(0)


def params():
    return {"f":"json","monitoring_location_id":SITE,"parameter_code":"00060",
            "time":f"{START}/{END}","limit":2000}


def test_pagination_follows_exact_scope(payload):
    features=payload[0]["features"]
    query=params()
    url=usgs.BASE+"/continuous/items?"+urlencode({**query,"offset":1})
    client=Pages([{"features":features[:1],"numberMatched":2,"links":[{"rel":"next","href":url}]},
                  {"features":features[1:],"numberMatched":2}])
    assert usgs._pages(client,query)==features
    assert len(client.calls)==2


def test_modern_usgs_cursor_pagination(payload):
    features=payload[0]["features"]
    query=params()
    # Real endpoint uses opaque cursor tokens rather than the offset shown in
    # older prose documentation. Never decode/reinterpret the provider token.
    url=usgs.BASE+"/continuous/items?"+urlencode({**query,"cursor":"YTM2Yjk1ZWY4ZjcxNDBh"})
    client=Pages([{"features":features[:1],"links":[{"rel":"next","href":url}]},
                  {"features":features[1:]}])
    assert usgs._pages(client,query)==features


def test_repeating_cursor_cannot_loop(payload):
    query=params()
    url=usgs.BASE+"/continuous/items?"+urlencode({**query,"cursor":"opaque-cursor"})
    page={"features":payload[0]["features"][:1],"links":[{"rel":"next","href":url}]}
    with pytest.raises(SourceSchemaError,match="repeating"):
        usgs._pages(Pages([page,page]),query)


@pytest.mark.parametrize("kind",["origin","station","limit","offset","partial","empty","changed_count"])
def test_pagination_never_returns_partial_or_changes_scope(payload,kind):
    query=params(); second={"features":payload[0]["features"][1:],"numberMatched":2}
    changed={**query,"offset":1}
    if kind=="station": changed["monitoring_location_id"]="USGS-00000000"
    if kind=="limit": changed["limit"]=1000000
    if kind=="offset": changed["offset"]=0
    url=usgs.BASE+"/continuous/items?"+urlencode(changed)
    if kind=="origin": url=url.replace("api.waterdata.usgs.gov","evil.test")
    page={"features":payload[0]["features"][:1],"numberMatched":2,"links":[{"rel":"next","href":url}]}
    if kind=="partial": page["links"]=[]
    if kind=="empty": page["features"]=[]
    if kind=="changed_count": second["numberMatched"]=3
    with pytest.raises(SourceSchemaError): usgs._pages(Pages([page,second]),query)


def test_row_budget_before_next_request(payload):
    body=payload[0]; body["numberMatched"]=10001
    with pytest.raises(SourceBudgetError): usgs._pages(Pages([body]),params())


def test_public_loader_batches_and_deduplicates_only_exact_shared_boundary(monkeypatch,payload):
    first=pd.Timestamp(START); last=first+pd.Timedelta(days=8)
    original=payload[0]["features"][0]
    def feature(time,ident):
        item=copy.deepcopy(original); item["properties"]["time"]=time.isoformat(); item["id"]=ident
        return item
    boundary=feature(first+pd.Timedelta(days=7),"boundary")
    batches=[[feature(first,"start"),boundary],[copy.deepcopy(boundary),feature(last,"end")]]
    class Client(Pages):
        trace=[]
        def __init__(self,**kwargs): super().__init__([payload[1],payload[2]])
        def __enter__(self): return self
        def __exit__(self,*args): pass
    monkeypatch.setattr(usgs,"SourceClient",Client)
    calls=[]
    def pages(client,query): calls.append(query); return batches.pop(0)
    monkeypatch.setattr(usgs,"_pages",pages)
    cube=usgs.streamflow(site=SITE,start=START,end=last.isoformat())
    assert cube.sizes["time"]==3 and len(calls)==2
    assert calls[0]["time"].endswith(boundary["properties"]["time"])


@pytest.mark.parametrize("site,start,end",[("*",START,END),(SITE,"2026-08-26",END),
    (SITE,START,"2026-10-01T00:00Z"),(SITE,END,START)])
def test_invalid_scope_before_network(monkeypatch,site,start,end):
    monkeypatch.setattr(usgs,"SourceClient",lambda **kw:pytest.fail("network client constructed"))
    with pytest.raises(ValueError): usgs.streamflow(site=site,start=start,end=end)


def test_candidate_is_installed_but_not_falsely_catalog_certified():
    assert "streamflow" not in data.list_sources()
    assert usgs.streamflow.__module__=="cubedynamics.data.usgs"


FIXTURE=Path(__file__).parent/"fixtures/real_data/usgs_streamflow"


def test_streamflow_notebook_is_generated_offline_and_each_step_plots():
    notebook_path = Path(__file__).parents[1] / "docs/vignettes/streamflow_snapshots.ipynb"
    notebook = json.loads(notebook_path.read_text())
    metadata = notebook["metadata"]["cubedynamics"]
    assert metadata["network"] is False
    assert metadata["minimum_plot_outputs"] == 3
    assert metadata["data_fixture"] == "tests/fixtures/real_data/usgs_streamflow"
    analysis = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert len(analysis) == 3
    for cell in analysis:
        assert cell["metadata"]["visual_example"]["kind"] == "figure"
        assert "plt.show()" in "".join(cell["source"])
    text = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "offline=True" in text
    assert "supported scope, quality checks, and limits" in text
    assert "library/nouns/streamflow.md" in text


@pytest.mark.parametrize("name",["boulder","potomac","lees_ferry"])
def test_real_snapshot_replay_and_provenance(name,monkeypatch):
    import requests
    monkeypatch.setattr(requests.Session,"get",lambda *a,**kw:pytest.fail("offline fixture used network"))
    provenance=json.loads((FIXTURE/"provenance.json").read_text())
    for relative,digest in provenance["files"].items():
        assert hashlib.sha256((FIXTURE/relative).read_bytes()).hexdigest()==digest
    cube=usgs.streamflow(site=provenance["sites"][name], start=provenance["start"],end=provenance["end"],
                         snapshot_dir=FIXTURE/name,offline=True)
    assert cube.sizes["time"]>0 and cube.streamflow.attrs["parameter_code"]=="00060"
    assert all(row["cache"]=="offline" for row in json.loads(cube.attrs["provenance"]))
    assert cube.attrs["release_status"]=="candidate_not_certified"
