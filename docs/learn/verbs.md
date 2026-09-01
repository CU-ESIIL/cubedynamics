# 2. Verbs do things

## Concept

A verb factory configures an operation; the returned callable applies it to
data. Run the [shared setup](index.md#shared-setup) first.

## Tiny example

A factory such as `v.mean(dim="time")` configures a callable. A pipe applies
it to data. Here, follow the same temperature cube from a map to a selected
window, local departures, a regional summary, standardization and a saved result.

## Explanation

The pipe changes Python calls to a readable analytical sentence; it does not
change the mathematics. Each figure immediately follows its producing code.
The [mean reference](../reference/verbs/mean.md) documents reduction dimensions.
Run this exact sequence in the [grammar notebook](../vignettes/grammar_basics.ipynb).

## Try it / worked example

<!-- visual-example:start -->

REAL DATA · Reviewed local PRISM observations; no live request.

<details class="cd-example-setup" markdown="1">
<summary>Reproduce: imports, checked data and setup</summary>

Run in a clone after `python -m pip install -e '.[vignettes]'`.

```python
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from IPython.display import display
from cubedynamics import pipe, verbs as v

# Run in the cloned repository or beside a downloaded notebook in the repo.
repo = next(p for p in (Path.cwd(), *Path.cwd().parents)
            if (p / "tests/fixtures/real_data").is_dir())

def observed_cube(stem, variable):
    path = repo / "tests/fixtures/real_data" / (stem + ".nc")
    record = json.loads(path.with_suffix(".provenance.json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record["fixture_sha256"]
    with xr.open_dataset(path, engine="scipy") as dataset:
        assert not dataset.attrs["is_synthetic"]
        result = dataset[variable].load()  # Only this small, reviewed local extract.
        result.attrs = {**dataset.attrs, **result.attrs}
    assert result.dims == ("time", "y", "x")
    assert np.all(np.diff(result.x) > 0) and np.all(np.diff(result.y) < 0)
    assert bool(np.isfinite(result).all())
    return result

cube = observed_cube("prism_boulder_january_2024", "tmax").rename("temperature")
assert cube.attrs["units"] == "degC"

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12, 'axes.titlesize': 13, 'axes.labelsize': 12, 'figure.facecolor': 'white', 'axes.facecolor': 'white', 'savefig.facecolor': 'white', 'figure.dpi': 140})
```

</details>

<section class="cd-analysis-step" data-example="observed" markdown="1">

### Start with a temperature field

Where was the cold outbreak visible on 16 January?

```python
field = cube.sel(time="2024-01-16")

fig, ax = plt.subplots(figsize=(5.4, 3.8), layout="constrained")
field.plot(ax=ax, cmap="magma", cbar_kwargs={"label": "Daily maximum (°C)"})
ax.set(title="PRISM · Boulder · 16 January 2024",
       xlabel="Longitude (°E)", ylabel="Latitude (°N)")
plt.show()
```

<figure class="cd-generated-result"><img src="../../assets/generated/visual/observed.png" alt="Real PRISM daily maximum temperature, Boulder region, 16 January 2024. Selecting a date exposes one spatial face of the cube; north is up." width="756" height="532" loading="lazy" decoding="async"><figcaption>Real PRISM daily maximum temperature, Boulder region, 16 January 2024. Selecting a date exposes one spatial face of the cube; north is up.</figcaption></figure>

<p class="cd-interpretation"><strong>What changed?</strong> Each cell is a gridded estimate, not a station reading. This map shows absolute temperature; it does not yet say how unusual the day was.</p>

[Generating code](https://github.com/CU-ESIIL/cubedynamics/blob/main/scripts/visual_examples.py) · [Figure/input provenance](../assets/generated/visual/manifest.json)

</section>

<section class="cd-analysis-step" data-example="subset" markdown="1">

### Choose the time window

Which observations will define the short-period baseline?

```python
window = (pipe(cube)
          | v.apply(lambda c: c.sel(time=slice("2024-01-10", "2024-01-20")))).unwrap()
assert window.sizes["time"] == 11

fig, ax = plt.subplots(figsize=(5.4, 3.4), layout="constrained")
cube.isel(y=12, x=12).plot(ax=ax, color="0.65", label="Full fixture")
window.isel(y=12, x=12).plot(ax=ax, marker="o", color="#246b70", label="Selected days")
ax.set(title="One grid cell · select 10–20 January", xlabel="Date", ylabel="Daily maximum (°C)")
ax.legend(frameon=False)
plt.show()
```

<figure class="cd-generated-result"><img src="../../assets/generated/visual/subset.png" alt="PRISM maximum temperature at one Boulder grid cell. The apply/sel stage retains 10–20 January 2024 (colored markers) without changing their values." width="756" height="476" loading="lazy" decoding="async"><figcaption>PRISM maximum temperature at one Boulder grid cell. The apply/sel stage retains 10–20 January 2024 (colored markers) without changing their values.</figcaption></figure>

<p class="cd-interpretation"><strong>What changed?</strong> The grey observations remain in cube but not window. Subsequent anomalies use these eleven selected days, not the entire month or a climatology.</p>

[Generating code](https://github.com/CU-ESIIL/cubedynamics/blob/main/scripts/visual_examples.py) · [Figure/input provenance](../assets/generated/visual/manifest.json)

</section>

<section class="cd-analysis-step" data-example="anomaly" markdown="1">

### Remove the local baseline

Where was 16 January colder than each pixel’s own selected-period mean?

```python
departures = (pipe(window) | v.anomaly(dim="time")).unwrap()

fig, axes = plt.subplots(2, 1, figsize=(5.4, 6.5), layout="constrained")
window.sel(time="2024-01-16").plot(ax=axes[0], cmap="magma", cbar_kwargs={"label": "°C"})
departures.sel(time="2024-01-16").plot(ax=axes[1], cmap="RdBu_r", center=0,
                                    cbar_kwargs={"label": "Departure (°C)"})
for ax, title in zip(axes, ["Before · absolute temperature", "After anomaly() · local departure"]):
    ax.set(title=title, xlabel="Longitude (°E)", ylabel="Latitude (°N)")
plt.show()
```

<figure class="cd-generated-result"><img src="../../assets/generated/visual/anomaly.png" alt="PRISM, Boulder, 16 January 2024: absolute maximum temperature above and anomaly below. anomaly() subtracts each pixel’s 10–20 January mean; the diverging scale is centered on zero." width="756" height="910" loading="lazy" decoding="async"><figcaption>PRISM, Boulder, 16 January 2024: absolute maximum temperature above and anomaly below. anomaly() subtracts each pixel’s 10–20 January mean; the diverging scale is centered on zero.</figcaption></figure>

<p class="cd-interpretation"><strong>What changed?</strong> Negative departures mean colder than that pixel’s baseline. The coldest absolute location need not have the largest departure. A short event-window baseline is not a long-term climate normal.</p>

[Generating code](https://github.com/CU-ESIIL/cubedynamics/blob/main/scripts/visual_examples.py) · [Figure/input provenance](../assets/generated/visual/manifest.json)

</section>

<section class="cd-analysis-step" data-example="summary" markdown="1">

### Summarize region

When was the selected region cold relative to its local baselines?

```python
regional_anomaly = (pipe(departures)
                    | v.mean(dim=("y", "x"), keep_dim=False)).unwrap()
assert regional_anomaly.dims == ("time",)

fig, ax = plt.subplots(figsize=(5.4, 3.4), layout="constrained")
regional_anomaly.plot(ax=ax, marker="o", color="#246b70")
ax.axhline(0, color="0.5", linewidth=0.8)
ax.set(title="After mean() · grid-cell average anomaly", xlabel="Date", ylabel="Departure (°C)")
plt.show()
```

<figure class="cd-generated-result"><img src="../../assets/generated/visual/summary.png" alt="The mean verb reduces PRISM y and x to a daily series for 10–20 January. The plotted quantity is the unweighted mean of grid-cell anomalies, in °C." width="756" height="476" loading="lazy" decoding="async"><figcaption>The mean verb reduces PRISM y and x to a daily series for 10–20 January. The plotted quantity is the unweighted mean of grid-cell anomalies, in °C.</figcaption></figure>

<p class="cd-interpretation"><strong>What changed?</strong> Space has disappeared from the result, but time remains. This is an equal-cell average on a latitude/longitude grid, not an area-weighted regional estimate.</p>

[Generating code](https://github.com/CU-ESIIL/cubedynamics/blob/main/scripts/visual_examples.py) · [Figure/input provenance](../assets/generated/visual/manifest.json)

</section>

<section class="cd-analysis-step" data-example="standardize" markdown="1">

### Compare scales, not units

Does the pipe compute the same z-score as the explicit formula?

```python
standardized = (pipe(window) | v.zscore(dim="time")).unwrap()
direct = (window - window.mean("time")) / window.std("time")
np.testing.assert_allclose(standardized, direct, rtol=1e-6, atol=1e-6)
# Standardization is dimensionless; replace the inherited temperature label.
standardized.attrs["units"] = "1"

fig, axes = plt.subplots(2, 1, figsize=(5.4, 5.8), layout="constrained")
axes[0].hist(window.values.ravel(), bins=24, color="#246b70")
axes[1].hist(standardized.values.ravel(), bins=24, color="#246b70")
axes[0].set(title="Before · selected PRISM values", xlabel="Daily maximum (°C)", ylabel="Cell-days")
axes[1].set(title="After zscore() · per-pixel scaling", xlabel="Standard deviations (unitless)", ylabel="Cell-days")
plt.show()
```

<figure class="cd-generated-result"><img src="../../assets/generated/visual/standardize.png" alt="All PRISM grid-cell days in the selected window, before and after per-pixel zscore(). Histograms show distributions on different, explicitly labeled scales; the code asserts equivalence to the direct formula." width="756" height="812" loading="lazy" decoding="async"><figcaption>All PRISM grid-cell days in the selected window, before and after per-pixel zscore(). Histograms show distributions on different, explicitly labeled scales; the code asserts equivalence to the direct formula.</figcaption></figure>

<p class="cd-interpretation"><strong>What changed?</strong> Each pixel is centered and scaled by its own temporal variability. The pooled histogram is not fitted to a normal distribution, and its cell-days are not independent samples.</p>

[Generating code](https://github.com/CU-ESIIL/cubedynamics/blob/main/scripts/visual_examples.py) · [Figure/input provenance](../assets/generated/visual/manifest.json)

</section>

<section class="cd-analysis-step" data-example="export" markdown="1">

### Check the saved result

Does explicit NetCDF output preserve the analysis?

```python
from tempfile import TemporaryDirectory
with TemporaryDirectory() as directory:
    target = Path(directory) / "regional_anomaly.nc"
    saved = (pipe(regional_anomaly) | v.to_netcdf(str(target), engine="scipy")).unwrap()
    with xr.open_dataarray(target, engine="scipy") as reopened:
        restored = reopened.load()
    xr.testing.assert_allclose(saved, restored)
    assert restored.attrs["is_synthetic"] == 0
    assert restored.attrs["cubedynamics_metadata_encoding"] == "netcdf-safe-v1"
output_table = pd.DataFrame({
    "Check": ["Dimensions", "Observations", "Values", "Boolean metadata"],
    "Before": [str(saved.dims), str(saved.size), "Reference result", "False"],
    "After reopening": [str(restored.dims), str(restored.size), "Equal (asserted)", "0 · portable flag"],
})

display(output_table)
```

<div class="cd-generated-result cd-result-table" markdown="1">

| Check | Before | After reopening |
| --- | --- | --- |
| Dimensions | ('time',) | ('time',) |
| Observations | 11 | 11 |
| Values | Reference result | Equal (asserted) |
| Boolean metadata | False | 0 · portable flag |

</div>

<p class="cd-result-caption">The PRISM regional-anomaly result is written with to_netcdf() and reopened. Numerical equality is asserted while Boolean provenance is intentionally encoded as a portable integer flag; the temporary example file is then removed.</p>

<p class="cd-interpretation"><strong>What changed?</strong> Export is an explicit side effect. The compact table is more useful here than another identical curve: it reports the tested round trip.</p>

[Generating code](https://github.com/CU-ESIIL/cubedynamics/blob/main/scripts/visual_examples.py) · [Figure/input provenance](../assets/generated/visual/manifest.json)

</section>

<!-- visual-example:end -->

## What to learn next

[3. Pipes establish order](pipes.md) · [Verb index](../reference/verbs/index.md) ·
[Verb gallery vignette](../vignettes/verbs_gallery.ipynb)
