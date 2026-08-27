"""Executable editorial examples shared by reference pages and a vignette.

This is not a data registry or notebook runner. Code strings below are shown
verbatim to readers, executed by build_visual_docs.py, and copied into the
existing supported-notebook builder.
"""
from dataclasses import dataclass
from html import escape
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/assets/generated/visual"
FIXTURES = ("prism_boulder_january_2024", "gridmet_badlands_july_2001")
STYLE = {"font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 13,
         "axes.labelsize": 12, "figure.facecolor": "white", "axes.facecolor": "white",
         "savefig.facecolor": "white", "figure.dpi": 140}

SETUP = '''from pathlib import Path
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
'''


@dataclass(frozen=True)
class Example:
    title: str
    question: str
    analysis: str
    plot: str
    caption: str
    interpretation: str
    requires: tuple = ()
    fixtures: tuple = (FIXTURES[0],)
    kind: str = "figure"

    @property
    def code(self):
        return self.analysis.strip() + "\n\n" + self.plot.strip()


EXAMPLES = {
    "observed": Example(
        "Start with a temperature field", "Where was the cold outbreak visible on 16 January?",
        'field = cube.sel(time="2024-01-16")',
        '''fig, ax = plt.subplots(figsize=(5.4, 3.8), layout="constrained")
field.plot(ax=ax, cmap="magma", cbar_kwargs={"label": "Daily maximum (°C)"})
ax.set(title="PRISM · Boulder · 16 January 2024",
       xlabel="Longitude (°E)", ylabel="Latitude (°N)")
plt.show()''',
        "Real PRISM daily maximum temperature, Boulder region, 16 January 2024. Selecting a date exposes one spatial face of the cube; north is up.",
        "Each cell is a gridded estimate, not a station reading. This map shows absolute temperature; it does not yet say how unusual the day was."),
    "subset": Example(
        "Choose the time window", "Which observations will define the short-period baseline?",
        '''window = (pipe(cube)
          | v.apply(lambda c: c.sel(time=slice("2024-01-10", "2024-01-20")))).unwrap()
assert window.sizes["time"] == 11''',
        '''fig, ax = plt.subplots(figsize=(5.4, 3.4), layout="constrained")
cube.isel(y=12, x=12).plot(ax=ax, color="0.65", label="Full fixture")
window.isel(y=12, x=12).plot(ax=ax, marker="o", color="#246b70", label="Selected days")
ax.set(title="One grid cell · select 10–20 January", xlabel="Date", ylabel="Daily maximum (°C)")
ax.legend(frameon=False)
plt.show()''',
        "PRISM maximum temperature at one Boulder grid cell. The apply/sel stage retains 10–20 January 2024 (colored markers) without changing their values.",
        "The grey observations remain in cube but not window. Subsequent anomalies use these eleven selected days, not the entire month or a climatology."),
    "anomaly": Example(
        "Remove the local baseline", "Where was 16 January colder than each pixel’s own selected-period mean?",
        'departures = (pipe(window) | v.anomaly(dim="time")).unwrap()',
        '''fig, axes = plt.subplots(2, 1, figsize=(5.4, 6.5), layout="constrained")
window.sel(time="2024-01-16").plot(ax=axes[0], cmap="magma", cbar_kwargs={"label": "°C"})
departures.sel(time="2024-01-16").plot(ax=axes[1], cmap="RdBu_r", center=0,
                                    cbar_kwargs={"label": "Departure (°C)"})
for ax, title in zip(axes, ["Before · absolute temperature", "After anomaly() · local departure"]):
    ax.set(title=title, xlabel="Longitude (°E)", ylabel="Latitude (°N)")
plt.show()''',
        "PRISM, Boulder, 16 January 2024: absolute maximum temperature above and anomaly below. anomaly() subtracts each pixel’s 10–20 January mean; the diverging scale is centered on zero.",
        "Negative departures mean colder than that pixel’s baseline. The coldest absolute location need not have the largest departure. A short event-window baseline is not a long-term climate normal.",
        requires=("subset",)),
    "summary": Example(
        "Summarize region", "When was the selected region cold relative to its local baselines?",
        '''regional_anomaly = (pipe(departures)
                    | v.mean(dim=("y", "x"), keep_dim=False)).unwrap()
assert regional_anomaly.dims == ("time",)''',
        '''fig, ax = plt.subplots(figsize=(5.4, 3.4), layout="constrained")
regional_anomaly.plot(ax=ax, marker="o", color="#246b70")
ax.axhline(0, color="0.5", linewidth=0.8)
ax.set(title="After mean() · grid-cell average anomaly", xlabel="Date", ylabel="Departure (°C)")
plt.show()''',
        "The mean verb reduces PRISM y and x to a daily series for 10–20 January. The plotted quantity is the unweighted mean of grid-cell anomalies, in °C.",
        "Space has disappeared from the result, but time remains. This is an equal-cell average on a latitude/longitude grid, not an area-weighted regional estimate.",
        requires=("anomaly",)),
    "standardize": Example(
        "Compare scales, not units", "Does the pipe compute the same z-score as the explicit formula?",
        '''standardized = (pipe(window) | v.zscore(dim="time")).unwrap()
direct = (window - window.mean("time")) / window.std("time")
np.testing.assert_allclose(standardized, direct, rtol=1e-6, atol=1e-6)
# Standardization is dimensionless; replace the inherited temperature label.
standardized.attrs["units"] = "1"''',
        '''fig, axes = plt.subplots(2, 1, figsize=(5.4, 5.8), layout="constrained")
axes[0].hist(window.values.ravel(), bins=24, color="#246b70")
axes[1].hist(standardized.values.ravel(), bins=24, color="#246b70")
axes[0].set(title="Before · selected PRISM values", xlabel="Daily maximum (°C)", ylabel="Cell-days")
axes[1].set(title="After zscore() · per-pixel scaling", xlabel="Standard deviations (unitless)", ylabel="Cell-days")
plt.show()''',
        "All PRISM grid-cell days in the selected window, before and after per-pixel zscore(). Histograms show distributions on different, explicitly labeled scales; the code asserts equivalence to the direct formula.",
        "Each pixel is centered and scaled by its own temporal variability. The pooled histogram is not fitted to a normal distribution, and its cell-days are not independent samples.",
        requires=("subset",)),
    "export": Example(
        "Check the saved result", "Does explicit NetCDF output preserve the analysis?",
        '''from tempfile import TemporaryDirectory
with TemporaryDirectory() as directory:
    target = Path(directory) / "regional_anomaly.nc"
    saved = (pipe(regional_anomaly) | v.to_netcdf(str(target), engine="scipy")).unwrap()
    with xr.open_dataarray(target, engine="scipy") as reopened:
        restored = reopened.load()
    xr.testing.assert_identical(saved, restored)
output_table = pd.DataFrame({
    "Check": ["Dimensions", "Observations", "Values and metadata"],
    "Before": [str(saved.dims), str(saved.size), "Reference result"],
    "After reopening": [str(restored.dims), str(restored.size), "Identical (asserted)"],
})''',
        'display(output_table)',
        "The PRISM regional-anomaly result is written with to_netcdf() and reopened. An identity assertion checks values, coordinates, names and attributes; the temporary example file is then removed.",
        "Export is an explicit side effect. The compact table is more useful here than another identical curve: it reports the tested round trip.",
        requires=("summary",), kind="table"),
    "threshold": Example(
        "From continuous values to a state", "On which days did a grid cell remain at or below freezing even at its daily maximum?",
        '''cold = (pipe(cube) | v.threshold_state(threshold=0, direction="below")).unwrap()
site = cube.isel(y=12, x=12)
state = cold.state.isel(y=12, x=12)
np.testing.assert_array_equal(state, site <= 0)''',
        '''fig, axes = plt.subplots(2, 1, figsize=(5.4, 5.4), sharex=True, layout="constrained")
site.plot(ax=axes[0], color="#246b70", marker="o")
axes[0].axhline(0, color="0.4", linestyle="--", label="Threshold: 0°C")
axes[0].set(title="Before · PRISM daily maximum", ylabel="Temperature (°C)", xlabel="")
axes[0].legend(frameon=False)
axes[1].step(state.time, state.astype(int), where="mid", color="#246b70")
axes[1].set(title="After threshold_state() · at or below 0°C", xlabel="Date", ylabel="State", yticks=[0, 1], ylim=(-0.1, 1.1))
plt.show()''',
        "One Boulder PRISM grid cell in January 2024: daily maximum temperature becomes a boolean state. direction='below' includes equality (≤ 0°C), verified against the original values.",
        "A true state describes a criterion, not an event duration or an ecological impact. This complete fixture has no missing values; missing-data policy must be checked for other inputs."),
    "sources": Example(
        "Inspect source support before comparing", "Are these two reviewed samples suitable for a paired source comparison?",
        '''gridmet = observed_cube("gridmet_badlands_july_2001", "temperature")
assert gridmet.attrs["units"] == "K"
# No conversion, resampling, or date alignment is hidden here.
assert not np.intersect1d(cube.time.values, gridmet.time.values).size''',
        '''fig, axes = plt.subplots(2, 1, figsize=(5.4, 6.5), layout="constrained")
cube.isel(time=0).plot(ax=axes[0], cmap="magma", cbar_kwargs={"label": "PRISM (°C)"})
gridmet.isel(time=0).plot(ax=axes[1], cmap="magma", cbar_kwargs={"label": "gridMET (K)"})
for ax, title in zip(axes, ["PRISM · Boulder · 1 January 2024", "gridMET · Badlands · 1 July 2001"]):
    ax.set(title=title, xlabel="Longitude (°E)", ylabel="Latitude (°N)")
plt.show()''',
        "Two real, source-QA fixtures in their native temperature units and geographic grids. Their places and dates differ; each panel has its own color scale. This is a support check, not evidence of source bias or agreement.",
        "These samples cannot support a paired temperature comparison. Obtain overlapping AOIs and dates, explicitly convert K to °C, and choose a spatial alignment method before comparing products. Native grid cells are approximately 4 km, not identical spatial support.",
        fixtures=FIXTURES),
}

LESSON = ("observed", "subset", "anomaly", "summary", "standardize", "export")


def prerequisites(keys):
    ordered = []
    def visit(key):
        for parent in EXAMPLES[key].requires:
            visit(parent)
        if key not in ordered:
            ordered.append(key)
    for key in keys:
        visit(key)
    return ordered


def setup_code(keys):
    # Only prerequisites not displayed as their own steps need setup code.
    prior = [key for key in prerequisites(keys) if key not in keys]
    return SETUP + f"\nplt.rcParams.update({STYLE!r})\n" + "\n".join(EXAMPLES[k].analysis for k in prior)


def render_examples(keys, page):
    """Render verbatim code next to its generated result; no code execution."""
    import json
    from PIL import Image
    base = os.path.relpath("assets/generated/visual", Path(page).parent)
    # MkDocs rewrites Markdown links, but leaves raw HTML src attributes alone.
    # All first-pass pages use directory URLs (verbs.md -> verbs/index.html).
    image_base = "../" + base
    source = "https://github.com/CU-ESIIL/cubedynamics/blob/main/scripts/visual_examples.py"
    text = "\nREAL DATA · Reviewed local PRISM observations; no live request.\n\n"
    if "sources" in keys:
        text = "\nREAL DATA · Reviewed PRISM and gridMET extracts; **different places and dates**.\n\n"
    text += '<details class="cd-example-setup" markdown="1">\n<summary>Reproduce: imports, checked data and setup</summary>\n\n'
    text += "Run in a clone after `python -m pip install -e '.[vignettes]'`.\n\n```python\n" + setup_code(keys).strip() + "\n```\n\n</details>\n"
    for key in keys:
        example = EXAMPLES[key]
        text += f'\n<section class="cd-analysis-step" data-example="{key}" markdown="1">\n\n### {example.title}\n\n{example.question}\n\n```python\n{example.code}\n```\n\n'
        if example.kind == "figure":
            # Intrinsic dimensions reserve space before a lazy image decodes.
            with Image.open(OUTPUT / f"{key}.png") as image:
                width, height = image.size
            text += f'<figure class="cd-generated-result"><img src="{image_base}/{key}.png" alt="{escape(example.caption, quote=True)}" width="{width}" height="{height}" loading="lazy" decoding="async"><figcaption>{escape(example.caption)}</figcaption></figure>\n\n'
        else:
            table = json.loads((OUTPUT / f"{key}.json").read_text())
            text += '<div class="cd-generated-result cd-result-table" markdown="1">\n\n'
            text += "| " + " | ".join(table["columns"]) + " |\n| " + " | ".join("---" for _ in table["columns"]) + " |\n"
            text += "\n".join("| " + " | ".join(row) + " |" for row in table["rows"]) + "\n\n</div>\n\n"
            text += f'<p class="cd-result-caption">{escape(example.caption)}</p>\n\n'
        text += f'<p class="cd-interpretation"><strong>What changed?</strong> {escape(example.interpretation)}</p>\n\n'
        text += f'[Generating code]({source}) · [Figure/input provenance]({base}/manifest.json)\n\n</section>\n'
    return text
