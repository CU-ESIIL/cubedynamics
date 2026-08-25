# Publication vignette data

The vignette fixture is an observational extract of the PRISM Group at Oregon
State University's AN91d daily 4 km product. It covers 1–30 January 2024 in a
one-degree Boulder-region bounding box (`-105.75, 39.50, -104.75, 40.50`). It
contains official daily minimum and maximum temperature and the exactly derived
daily range (`tmax - tmin`). It contains no generated measurements.

Files:

- `prism_boulder_january_2024.nc` — offline teaching extract.
- `prism_boulder_january_2024.provenance.json` — fixture hash, bounds, units,
  summary ranges, and URL/byte/SHA-256 evidence for all 60 source archives.

Rebuild from cached, checksum-verified source archives:

```bash
python scripts/build_vignette_data.py
```

On a clean checkout, explicitly allow downloading the recorded official
archives first:

```bash
python scripts/build_vignette_data.py --download-missing
```

Rebuilding requires roughly 160 MB of source downloads. The script verifies
every archive before reading it and fails on any source or fixture mismatch.

Source: [PRISM Group, Oregon State University](https://prism.oregonstate.edu/).
See the [PRISM dataset documentation](https://www.prism.oregonstate.edu/documents/PRISM_datasets.pdf)
and [terms of use](https://prism.oregonstate.edu/terms/). Data accessed
2026-08-25.
