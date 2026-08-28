# Assets

Place supporting images for the documentation inside this folder.

- Use `docs/assets/diagrams/` for diagrams and schematic figures referenced throughout the docs.
- Use `docs/assets/figures/` for illustrative figures or photos.

Filenames are referenced directly in Markdown pages, so update links when
replacing or renaming an asset.

Recommended formats: PNG or SVG for clarity in the MkDocs theme.

Do not add empty files or text placeholders with image extensions. Use a clear
text explanation until a reviewed diagram or real-data figure is available.
The [browser QA suite](../dev/ci_testing.md#website-browser-qa) decodes displayed
images and fails on corrupt or missing assets, including inside cube viewers.

## Homepage example gallery

`scripts/hero_examples.py` owns the dropdown inventory. It includes all variables
and bands in the four reviewed spatiotemporal raster fixtures (PRISM Boulder,
PRISM Working Lands, gridMET Badlands and Sentinel-2 Badlands), derived NDVI,
and cube-shaped results from the array, anomaly, z-score and cold-state lessons.
The existing FIRED/gridMET VASE is listed separately as a Plotly hull, not a
raster cube. All choices link to their lesson or source QA notes.

Historical synthetic synchrony/fire demos and the older NDVI export without a
fixture-bound reproduction record are not promoted into this real-data gallery.
Elevation, roads, station series, and spatial/temporal summaries remain in their
lessons: no time slices or measurements are invented to turn them into cubes.

Rebuild the small standalone HTML assets and their integrity manifest offline:

```bash
python scripts/build_real_data_assets.py
python scripts/build_real_data_assets.py --check
```

Each input NetCDF is checked against its existing provenance checksum before
rendering. The builder checks time order, finite values, units and color limits;
`hero_examples.json` binds the source files and outputs to hashes. This is
reproducible fixture evidence, not fresh scientific certification. PRISM is
shown in Celsius, gridMET in its native kelvin, and Sentinel-2 on its native UTM
grid with provider-scaled bands. The two Sentinel-2 acquisitions are not a
one-year record or a cloud-masked product; NDVI follows the existing source QA
ratio on retained band values.

MkDocs renders the options and no-JavaScript fallback links at build time.
Only the selected iframe is loaded. Switching examples updates its accessible
title, explanation, full-view link, and lesson link without downloading the
remaining viewers. The light styling and year-bearing dates stay consistent.
