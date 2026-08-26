# Daymet candidate status

Daymet is a **candidate**, not an implemented `temperature` source flavor.
`data.sources("temperature")` therefore continues to return only reviewed
sources.

The proposed integration maps Daymet V4/V4R1 daily `tmax` to the stable
`temperature` noun and uses the `climate_continuous_daily` QA profile. The
candidate revision is:

```text
temperature.daymet@2026-08-26.1
```

## Why it is blocked

ORNL documents spatially and temporally bounded NCSS requests returning
CF-compliant NetCDF, but ORNL DAAC now requires a NASA Earthdata login for data
downloads. The documented unauthenticated V4 endpoint returned HTTP 401 during
this review. CubeDynamics records that as `BLOCKED` and `UNAVAILABLE`; it does
not fabricate data or promote an unreviewed source.

- [Daymet web services](https://daymet.ornl.gov/web_services.html)
- [Daymet V4 product guide](https://daac.ornl.gov/DAYMET/guides/Daymet_Daily_V4.html)
- [Current ORNL access guidance](https://forum.earthdata.nasa.gov/viewtopic.php?t=7585)
- [Earthdata login requirement](https://daymet.ornl.gov/single-pixel-tool-guide)

## Promotion checklist

1. Supply `EARTHDATA_TOKEN` only in the online certification environment.
2. Run `python scripts/run_live_source_certification.py --source daymet`.
3. Review a tiny bounded NetCDF subset, provider version headers, schema drift,
   numerical QA, and diagnostic plot.
4. Add the checksum-controlled subset under `tests/fixtures/real_data/`.
5. Link its schema fingerprint and QA evidence in serving history.
6. Promote only after `data.validate_promotion()` accepts the complete record.

Daymet must not become the default or silently replace PRISM/gridMET.
