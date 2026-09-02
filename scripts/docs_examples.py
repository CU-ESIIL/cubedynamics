"""Editorial examples and semantic notes, not a duplicate scientific catalog."""

FIXTURE_SETUP = '''from pathlib import Path
import xarray as xr
import matplotlib.pyplot as plt
from cubedynamics import pipe, verbs as v

# Frozen, reviewed PRISM observations; run from the repository root.
path = Path("tests/fixtures/real_data/prism_boulder_january_2024.nc")
with xr.open_dataset(path, engine="scipy") as observed:
    cube = observed["tmax"].load()
assert cube.attrs["units"] == "degC"'''

EXAMPLES = {
    "anomaly": 'result = (pipe(cube) | v.anomaly(dim="time")).unwrap()\nresult.isel(time=0).plot()\nplt.show()',
    "mean": 'result = (pipe(cube) | v.mean(dim="time", keep_dim=False)).unwrap()\nresult.plot()\nplt.show()',
    "variance": 'result = (pipe(cube) | v.variance(dim="time", keep_dim=False)).unwrap()\n# CubeDynamics records squared source units (degC^2) on the result.\nassert result.attrs["units"] == "degC^2"\nresult.plot(cbar_kwargs={"label": "Temperature variance (°C²)"})\nplt.show()',
    "zscore": 'result = (pipe(cube) | v.zscore(dim="time")).unwrap()\nresult.isel(time=0).plot()\nplt.show()',
    "apply": 'result = (pipe(cube) | v.apply(lambda x: x.max("time"))).unwrap()\nresult.plot()\nplt.show()',
    "month_filter": 'result = (pipe(cube) | v.month_filter([1])).unwrap()\nresult.mean("time").plot()\nplt.show()',
    "flatten_cube": 'result = (pipe(cube) | v.flatten_cube()).unwrap()\n# Unstack the retained coordinate index to check the original spatial map.\nresult.mean("time").unstack("sample").plot()\nplt.show()',
    "flatten_space": 'result = (pipe(cube) | v.flatten_space()).unwrap()\nresult.mean("time").unstack("pixel").plot()\nplt.show()',
    "threshold_state": 'result = (pipe(cube) | v.threshold_state(threshold=0, direction="below")).unwrap()\nresult.state.mean("time").plot()\nplt.show()',
    "exceedance": 'result = (pipe(cube) | v.exceedance(threshold=0, direction="below")).unwrap()\nresult.state.mean("time").plot()\nplt.show()',
    "quantile_state": 'result = (pipe(cube) | v.quantile_state(quantile=0.2, direction="below")).unwrap()\nresult.state.mean("time").plot()\nplt.show()',
    "binary_state": 'result = (pipe(cube < 0) | v.binary_state()).unwrap()\nresult.state.mean("time").plot()\nplt.show()',
    "change_state": 'result = (pipe(cube) | v.change_state(change="absolute", threshold=5, lag=1)).unwrap()\nresult.state.mean("time").plot()\nplt.show()',
    "detect_events": 'result = (pipe(cube) | v.threshold_state(threshold=0, direction="below") | v.detect_events(min_duration=2)).unwrap()\n# One row is one local-cell run, not one independent regional cold episode.\nprint(result.explain())\nresult.dataset["event_active"].sum("time").plot(cbar_kwargs={"label": "Days in local cold events"})\nplt.show()',
    "consolidate_events": 'local = (pipe(cube) | v.threshold_state(threshold=0, direction="below") | v.detect_events(min_duration=2)).unwrap()\nresult = (pipe(local) | v.consolidate_events(spatial_relation="neighbors", max_gap="1D")).unwrap()\nprint(result.explain())\nresult.catalog.plot.scatter(x="start", y="participating_cell_count")\nplt.show()',
    "event_metrics": 'local = (pipe(cube) | v.threshold_state(threshold=0, direction="below") | v.detect_events(min_duration=2)).unwrap()\nresult = (pipe(local) | v.event_metrics(period="all", metrics=("event_count", "mean_duration", "max_duration"))).unwrap()\nresult[["event_count", "max_duration"]].to_dataframe().plot.bar()\nplt.show()',
    "overlap": 'cold = (pipe(cube) | v.threshold_state(threshold=0, direction="below")).unwrap()\nunusual = (pipe(cube) | v.quantile_state(quantile=0.2, direction="below")).unwrap()\nresult = (pipe(cold) | v.overlap(unusual) | v.mean(dim="time", keep_dim=False)).unwrap()\n# overlap returns a state Dataset; mean turns state into a proportion summary.\nresult["state"].plot(cbar_kwargs={"label": "Fraction of observed days"})\nplt.show()',
    "align_time": 'other = cube.copy(deep=False)\nresult = (pipe(cube) | v.align_time(other, mode="labels")).unwrap()\n# Labels and values are unchanged; inspect the recorded decision.\nprint(result.attrs["temporal_alignment_support"])\nresult.isel(time=0).plot()\nplt.show()',
    "align_cube": 'target = cube.isel(y=slice(0, None, 2), x=slice(0, None, 2))\nresult = (pipe(cube) | v.align_cube(like=target)).unwrap()\nresult.isel(time=0).plot()\nplt.show()',
    "block_signature": 'result = (pipe(cube) | v.block_signature(block_id="boulder")).unwrap()\nresult["tmax"].squeeze().plot()\nplt.show()',
    "aoi_signature": 'result = (pipe(cube) | v.aoi_signature(unit_id="boulder")).unwrap()\nresult["tmax"].squeeze().plot()\nplt.show()',
    "collect_blocks": 'west = (pipe(cube.isel(x=slice(0, 12))) | v.block_signature(block_id="west")).unwrap()\neast = (pipe(cube.isel(x=slice(12, None))) | v.block_signature(block_id="east")).unwrap()\nresult = (pipe(west) | v.collect_blocks(east)).unwrap()\nresult["tmax"].plot.line(x="time", hue="block")\nplt.show()',
    "compare_blocks": 'west = (pipe(cube.isel(x=slice(0, 12))) | v.block_signature(block_id="west")).unwrap()\neast = (pipe(cube.isel(x=slice(12, None))) | v.block_signature(block_id="east")).unwrap()\nblocks = (pipe(west) | v.collect_blocks(east)).unwrap()\nresult = (pipe(blocks) | v.compare_blocks()).unwrap()\nprint(result)\nblocks["tmax"].plot.line(x="time", hue="block")\nplt.show()',
    "rolling_tail_dep_vs_center": 'result = (pipe(cube) | v.rolling_tail_dep_vs_center(window=7)).unwrap()\n# Signed upper-tail variance minus full-window variance; negative values are valid.\nresult.isel(time=-1).plot(cbar_kwargs={"label": result.attrs.get("units", "variance contrast")})\nplt.show()',
    "rolling_median_split_synchrony": 'result = (pipe(cube) | v.rolling_median_split_synchrony(window_days=14, min_t=3)).unwrap()\nresult["bottom_minus_top"].isel(time_window_end=-1).plot()\nplt.show()',
    "diagnostic_panel": 'figure = v.diagnostic_panel(cube, title="Observed PRISM temperature")\nplt.show()',
    "plot": 'condition = (pipe(cube) | v.threshold_state(threshold=0, direction="below")).unwrap()\nresult = pipe(condition) | v.plot(variable="state", title="Observed freezing condition")\n# In Jupyter, display the pipe to interact with its attached HTML viewer.\nfrom IPython.display import display\ndisplay(result)',
}

NOTES = {
    "fit_model": {"status": "Not implemented. Calling this exported placeholder raises NotImplementedError.", "example": "No scientific example is available: this is a reserved API, not an implemented model-fitting verb."},
    "correlation_cube": {"status": "Not implemented. Configuration may raise NotImplementedError; applying a returned stage always does.", "example": "For an explicit xarray calculation on aligned observed cubes, use `xr.corr(left, right, dim='time')`. This is not an implementation of `v.correlation_cube`."},
    "vase_demo": {"status": "Synthetic geometry demonstration only; retained for compatibility, not a real-data analysis.", "example": "Not promoted as an educational scientific example. Use the real FIRED workflow below.", "workflow": "capabilities/fire-vase.md"},
}

EXAMPLES.update({
    "rasterize_observations": 'rows = cube.to_dataframe(name="value").reset_index()\n# Re-grid actual PRISM cell-center observations; this is not a biological survey.\nresult = v.rasterize_observations(rows, template=cube, time_col="time", reducer="mean")\nresult.isel(time=0).plot()\nplt.show()',
    "occurrence_synchrony": 'state = (pipe(cube) | v.threshold_state(threshold=0, direction="below")).unwrap()\nresult = (pipe(state) | v.occurrence_synchrony(spatial_mode="reference", reference="center")).unwrap()\nresult["occurrence_synchrony"].squeeze().plot()\nplt.show()',
    "severity_synchrony": 'state = (pipe(cube) | v.threshold_state(threshold=0, direction="below")).unwrap()\nresult = (pipe(state) | v.severity_synchrony(spatial_mode="reference", reference="center", min_joint_events=3)).unwrap()\nresult["severity_synchrony"].squeeze().plot()\nplt.show()',
    "timing_synchrony": 'events = (pipe(cube) | v.threshold_state(threshold=0, direction="below") | v.detect_events()).unwrap()\nresult = (pipe(events) | v.timing_synchrony(spatial_mode="reference", reference="center")).unwrap()\nresult["timing_synchrony"].squeeze().plot()\nplt.show()',
    "duration_synchrony": 'events = (pipe(cube) | v.threshold_state(threshold=0, direction="below") | v.detect_events()).unwrap()\nresult = (pipe(events) | v.duration_synchrony(spatial_mode="reference", reference="center", min_matched_events=1)).unwrap()\n# A one-month sample can leave correlations undefined; inspect counts as well.\nprint(result)\nresult["duration_similarity"].squeeze().plot()\nplt.show()',
    "sync_with": 'cold = (pipe(cube) | v.threshold_state(threshold=0, direction="below")).unwrap()\nunusual = (pipe(cube) | v.quantile_state(quantile=0.2, direction="below")).unwrap()\nresult = (pipe(cold) | v.sync_with(unusual, lags=("0D",))).unwrap()\nresult["coupling_score"].squeeze().plot()\nplt.show()',
    "to_netcdf": 'from tempfile import TemporaryDirectory\n# Export is an explicit side effect. Use a temporary path for this demonstration.\nwith TemporaryDirectory() as directory:\n    target = Path(directory) / "observed_mean.nc"\n    result = (pipe(cube) | v.mean(dim="time", keep_dim=False) | v.to_netcdf(str(target), engine="scipy")).unwrap()\n    with xr.open_dataarray(target) as restored:\n        xr.testing.assert_allclose(result, restored)\n        restored.plot()\n        plt.show()',
})

for _name in ("anomaly", "mean", "variance", "zscore", "month_filter", "apply", "flatten_cube", "flatten_space"):
    NOTES[_name] = {"accepts": "An xarray DataArray or Dataset with the dimensions required by the selected operation. VirtualCube support is operation-specific; consult the implementation notes.", "returns": "A callable stage. Applying it returns the transformed xarray object (or the supported VirtualCube result).", "order": "Apply before reductions that remove a required dimension. Choose the reduction dimensions explicitly; `keep_dim=False` removes reduced axes."}
for _name in ("extract", "fire_plot", "fire_panel", "fire_vase_panel", "fire_derivative", "climate_hist", "vase", "vase_extract", "vase_mask"):
    NOTES[_name] = {"workflow": "capabilities/fire-vase.md", "accepts": "FireEventDaily / FireHull or VaseDefinition geometry and/or an observed climate cube, as specified by the arguments. Match CRS and event dates before attribution.", "example": "Follow the [real FIRED event and streamed gridMET example](../../capabilities/fire-vase.md). It provides the event acquisition, geometry, climate loading and plots together; a climate cube alone is insufficient for this operation.", "order": "Construct and validate event geometry before attributing climate or rendering. Fire plotting still uses a Plotly hull backend; it is not the general HTML cube viewer."}
for _name in ("landsat8_mpc", "landsat_vis_ndvi", "landsat_ndvi_plot"):
    NOTES[_name] = {"workflow": "examples/landsat8_mpc.md", "example": "Use the [Landsat MPC workflow](../../examples/landsat8_mpc.md) with its optional dependencies and live STAC access. This legacy source helper is not a registered scientific noun.", "accepts": "Location, dates and Landsat-specific options forwarded to the source helper."}
for _name in ("occurrence_synchrony", "severity_synchrony", "timing_synchrony", "duration_synchrony", "sync_with"):
    NOTES[_name] = {"workflow": "vignettes/states_and_events.ipynb"}
NOTES["detect_events"] = {
    "workflow": "concepts/events_and_episodes.md",
    "returns": "An EventResult with event_scope='local_cell'. One catalog row is one contiguous run at one spatial cell, not one regional episode.",
    "order": "Define a time-varying condition first. Event detection materializes the condition cube to construct the catalog and respects gaps in the actual time coordinate.",
}
NOTES["consolidate_events"] = {
    "workflow": "concepts/events_and_episodes.md",
    "accepts": "A local-cell EventResult plus explicit temporal-gap and spatial-connectivity criteria.",
    "returns": "An EventResult with event_scope='regional_episode', episode summaries, source event IDs, and the complete consolidation rule.",
    "order": "Detect local events before consolidation. Matching dates alone never merge spatially unrelated rows.",
}
NOTES["event_metrics"] = {
    "workflow": "concepts/events_and_episodes.md",
    "accepts": "A local-cell or regional-episode EventResult and a bounded metric list.",
    "returns": "An ordinary xarray Dataset grouped by year, month, or all events, with scope-aware counts and metric-level units.",
    "order": "Choose event scope before interpreting counts. Local event-days accumulate across cells; regional episode-days do not.",
}
NOTES["sync_with"] = {
    "workflow": "concepts/long_record_analysis.md",
    "order": "+5D compares left(t) with right(t+5D), so the right-hand condition occurs later. Negative lags mean it occurs earlier. Physical observation support is not shifted.",
}
NOTES["rolling_tail_dep_vs_center"] = {
    "workflow": "concepts/rolling_stats.md",
    "returns": "A signed upper-tail variance minus full-window variance contrast in squared source units. It is not a probability; negative values are valid and the range is unbounded.",
}
NOTES["ndvi_from_s2"] = {"workflow": "recipes/s2_ndvi_zcube.md", "accepts": "A Sentinel-2 cube containing the specified NIR and red bands, not an already-derived NDVI cube.", "example": "The [Sentinel-2 NDVI recipe](../../recipes/s2_ndvi_zcube.md) loads observed bands and applies this transform. Check scaling and cloud limitations in the [source reference](../../library/sources/sentinel2.md)."}
NOTES["tubes"] = {"workflow": "viz/suitability_tubes.md"}
NOTES["rasterize_observations"] = {"workflow": "howto/biological_cubes_and_coupling.md"}
NOTES["threshold_state"] = {
    "accepts": "A continuous or categorical xarray field, or a summary produced by a reduction. Dataset inputs require variable= unless they contain only one data variable.",
    "returns": "A condition Dataset with state, magnitude, and threshold variables plus explicit condition metadata.",
    "order": "Threshold then mean measures condition prevalence; mean then threshold defines a condition from an aggregate. Both are valid and intentionally distinct.",
}
NOTES["overlap"] = {
    "accepts": "Two already aligned condition DataArrays or Datasets. Coordinates must match exactly. Known different observation supports require temporal_alignment='labels' or 'require_exact_support'; no reprojection, resampling, shift, or scientific harmonization is inferred.",
    "returns": "A condition Dataset containing only Boolean state. The state variable is true only where both inputs are true; operand identity and exact-alignment metadata remain inspectable. Overlap does not invent a magnitude or threshold.",
    "order": "Define and align both conditions before overlap. Reduce the returned state variable when the intended result is a frequency or prevalence summary.",
}
NOTES["align_time"] = {
    "workflow": "concepts/temporal_alignment.md",
    "accepts": "Two xarray objects with time coordinates. mode='labels' records label pairing; mode='require_exact_support' also requires identical known observation-support metadata.",
    "returns": "The unchanged left xarray object with metadata describing coordinate and observation-support compatibility. No values or coordinates are shifted, resampled, interpolated, aggregated, or truncated.",
    "order": "Inspect and acknowledge temporal meaning before cross-source composition. Observation-support alignment and event-time matching are separate questions.",
}
NOTES["plot"] = {
    "accepts": "A renderable DataArray, Dataset, VirtualCube, or EventResult. Dataset selection prefers state, then event_active, then a sole variable; otherwise pass variable= explicitly.",
    "returns": "A CubePlot for 3-D time-space cubes, or a notebook-ready StaticPlot for 2-D spatial maps and 1-D temporal lines. Dataset selection preserves laziness and combines Dataset-level semantic metadata with selected-variable metadata.",
    "order": "Plot the semantic product you intend to inspect. Plotting does not alter or certify the underlying analysis.",
}
NOTES["show_cube_lexcube"] = {
    "accepts": "A 3-D DataArray with exactly (time, y, x) dimensions. Lexcube is an optional notebook widget, not the canonical website viewer.",
    "returns": "A pass-through stage that displays a Lexcube widget and leaves the input cube in the pipe.",
    "order": "Install the optional dependency with `python -m pip install \"cubedynamics[viz]\"`, restart the notebook kernel, and call this only while the cube still has time, y, and x dimensions.",
}
