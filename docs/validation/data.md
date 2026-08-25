---
description: "Provenance and acceptance checks for the observational PRISM data used by every publication vignette."
---

# Real-data validation

Every supported vignette uses the same observational teaching extract:
`data/vignettes/prism_boulder_january_2024.nc`.

| Field | Reviewed value |
| --- | --- |
| Provider | PRISM Group, Oregon State University |
| Product | AN91d daily 4 km time series |
| Variables | daily minimum temperature, daily maximum temperature, derived daily range |
| Time | 1–30 January 2024, complete daily sequence |
| Bounds | −105.75 to −104.75 longitude; 39.50 to 40.50 latitude |
| Grid | 30 dates × 24 latitude rows × 24 longitude columns |
| CRS | EPSG:4269 |
| Accessed | 2026-08-25 |

![PRISM data diagnostic](../assets/validation/data/diagnostic.png)

## Acceptance checks

The validation module rejects the fixture unless:

- its SHA-256 matches the provenance record;
- the provider and non-generated-data flag are explicit;
- dates are complete and ordered, longitude increases, and latitude decreases;
- all 51,840 stored cells are finite;
- minimum temperature never exceeds maximum temperature;
- daily range equals `tmax - tmin` within the float32 storage tolerance; and
- all 60 official daily archives have URL, byte-count, and SHA-256 evidence.

The fixture provenance is machine readable at
[`data/vignettes/prism_boulder_january_2024.provenance.json`](https://github.com/CU-ESIIL/cubedynamics/blob/main/data/vignettes/prism_boulder_january_2024.provenance.json).

Source: [PRISM Group](https://prism.oregonstate.edu/),
[dataset documentation](https://www.prism.oregonstate.edu/documents/PRISM_datasets.pdf),
and [terms of use](https://prism.oregonstate.edu/terms/).

## Rebuild

```bash
python scripts/build_vignette_data.py --download-missing
python scripts/run_validation.py
```

Downloads are never implicit in the lessons or offline CI. The rebuild flag is
an explicit request to retrieve the 60 recorded official archives; each is
verified before the extract is written.
