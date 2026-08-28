"""Acquire one bounded anonymous modern-USGS response for semantic inspection."""
import json
from pathlib import Path
from examples.source_projects._evidence import json_get, AccessBlocked, save_report

BASE = "https://api.waterdata.usgs.gov/ogcapi/v0/collections"
SITE = "USGS-06730200"
START = "2026-08-26T00:00:00Z"
END = "2026-08-26T23:59:59Z"


def acquire(output):
    output.mkdir(parents=True, exist_ok=True)
    evidence = {"http": []}
    try:
        body = json_get(BASE+"/continuous/items", params={"f":"json", "monitoring_location_id":SITE,
            "parameter_code":"00060", "time":f"{START}/{END}", "limit":2000}, evidence=evidence["http"])
        (output/"observations.json").write_text(json.dumps(body,indent=2))
        if any(link.get("rel") == "next" for link in body.get("links", [])):
            raise ValueError("Pagination detected; do not silently accept a partial series")
        location = json_get(BASE+f"/monitoring-locations/items/{SITE}",params={"f":"json"},evidence=evidence["http"])
        (output/"site.json").write_text(json.dumps(location,indent=2))
        series = {f["properties"]["time_series_id"] for f in body["features"]}
        if len(series) != 1:
            raise ValueError("Expected one unambiguous discharge time series")
        series_id = next(iter(series))
        metadata = json_get(BASE+f"/time-series-metadata/items/{series_id}",params={"f":"json"},evidence=evidence["http"])
        (output/"series.json").write_text(json.dumps(metadata,indent=2))
        evidence["site"], evidence["series_id"] = SITE, series_id
        (output/"acquisition.json").write_text(json.dumps(evidence,indent=2))
        print(json.dumps({"observations":len(body["features"]),"first":body["features"][:1],
                          "site":location,"series":metadata},indent=2))
    except AccessBlocked as exc:
        evidence["blocker"] = str(exc)
        save_report(output/"report.json",gates={"retrieval":"BLOCKED", "numerical_qa":"NOT_TESTED",
                    "visual_qa":"NOT_TESTED"},evidence=evidence)
        print(str(exc))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(acquire(Path("artifacts/source_qa/usgs")))
