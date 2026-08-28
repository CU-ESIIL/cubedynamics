"""Editorial inventory of reproducible real-data cube examples for the home page.

Only raster cubes with real time coordinates belong here. Terrain maps, roads,
station series and historical generated demonstrations are not time cubes.
The already-published FIRED hull is explicitly a different renderer.
"""

PRISM = "prism_boulder_january_2024"
LANDS = "sd_working_lands_july_2024"
GRIDMET = "gridmet_badlands_july_2001"
SENTINEL = "sentinel2_badlands_june_2023"


def example(key, label, fixture, variable, legend, units, limits, *,
            group="Climate observations", cmap="magma", transform=None,
            lesson="data/phase1_qa/", description="", title=None):
    places = {PRISM: "Boulder", LANDS: "Working lands", GRIDMET: "Badlands", SENTINEL: "Badlands"}
    kickers = {PRISM: "PRISM · Colorado · January 2024",
               LANDS: "PRISM · South Dakota · July 2024",
               GRIDMET: "gridMET · South Dakota · July 2001",
               SENTINEL: "Sentinel-2 · South Dakota · June 2023"}
    return dict(id=key, kind="cube", label=label, fixture=fixture,
                variable=variable, legend=legend, units=units, limits=limits,
                group=group, cmap=cmap, transform=transform, lesson=lesson,
                description=description, title=title or f"{places[fixture]}, in space and time",
                kicker=kickers[fixture], path=f"assets/figures/{key}.html")


EXAMPLES = [
    example("prism_boulder_tmax_cube", "Boulder · maximum temperature", PRISM, "tmax",
            "Daily maximum temperature (°C)", "degC", (-25, 20),
            description="Observed PRISM daily maximum temperature",
            lesson="vignettes/cube_from_arrays/"),
    example("prism_boulder_tmin_cube", "Boulder · minimum temperature", PRISM, "tmin",
            "Daily minimum temperature (°C)", "degC", (-35, 5),
            description="Observed PRISM daily minimum temperature", lesson="vignettes/cube_from_dataset/"),
    example("prism_boulder_range_cube", "Boulder · daily temperature range", PRISM, "diurnal_range",
            "Maximum − minimum temperature (°C)", "degC", (0, 30), cmap="viridis",
            description="PRISM daily range: tmax − tmin; not an anomaly", lesson="vignettes/cube_from_dataset/"),
    example("prism_working_lands_temperature_cube", "Working lands · temperature", LANDS, "temperature",
            "Daily maximum temperature (°C)", "degC", (20, 45),
            description="Observed PRISM daily maximum temperature · southwest of Pierre",
            lesson="decision_vignettes/working_lands/"),
    example("prism_working_lands_rain_cube", "Working lands · precipitation", LANDS, "precipitation",
            "Daily precipitation (mm)", "mm", (0, 45), cmap="Blues",
            description="Observed PRISM daily total precipitation · southwest of Pierre",
            lesson="decision_vignettes/working_lands/"),
    example("gridmet_badlands_temperature_cube", "Badlands · gridMET temperature", GRIDMET, "temperature",
            "Daily maximum temperature (K)", "K", (290, 310),
            description="Observed gridMET · 1–10 July 2001 · native kelvin values"),
    example("sentinel_badlands_red_cube", "Badlands · Sentinel-2 red band", SENTINEL, "surface_reflectance",
            "Red B04 (provider-scaled reflectance)", "scaled surface reflectance", (0, 6000),
            group="Satellite observations", cmap="Reds", transform="B04",
            description="Two acquisitions · native 10 m UTM grid · no pixel cloud mask"),
    example("sentinel_badlands_nir_cube", "Badlands · Sentinel-2 near infrared", SENTINEL, "surface_reflectance",
            "Near infrared B08 (provider-scaled reflectance)", "scaled surface reflectance", (0, 6000),
            group="Satellite observations", cmap="Purples", transform="B08",
            description="Two acquisitions · native 10 m UTM grid · no pixel cloud mask"),
    example("sentinel_badlands_ndvi_cube", "Badlands · NDVI (two scenes)", SENTINEL, "surface_reflectance",
            "NDVI (unitless)", "1", (-1, 1),
            group="Satellite observations", cmap="RdYlGn", transform="ndvi",
            description="(B08 − B04) / (B08 + B04) on retained provider-scaled values; no pixel cloud mask"),
    example("prism_array_lesson_cube", "Lesson · build a cube from an array", PRISM, "tmax",
            "Daily maximum temperature (°C)", "degC", (-25, 20),
            group="Grammar lessons", transform="array", title="From an array to a cube",
            description="The array lesson's exact 18-day, 5 × 6 PRISM extract",
            lesson="vignettes/cube_from_arrays/"),
    example("prism_anomaly_lesson_cube", "Lesson · local temperature anomaly", PRISM, "tmax",
            "Departure from 10–20 January mean (°C)", "degC", (-30, 30),
            group="Grammar lessons", cmap="RdBu_r", transform="anomaly", title="Remove the local baseline",
            description="anomaly() · per-pixel 10–20 January mean, not a climate normal",
            lesson="vignettes/grammar_basics/"),
    example("prism_zscore_lesson_cube", "Lesson · standardized temperature", PRISM, "tmax",
            "Per-pixel z-score (unitless)", "1", (-3, 3),
            group="Grammar lessons", cmap="RdBu_r", transform="zscore", title="Compare variation, not units",
            description="zscore() · 10–20 January 2024 · standard deviations from each pixel's mean",
            lesson="vignettes/grammar_basics/"),
    example("prism_cold_state_lesson_cube", "Lesson · severe-cold states", PRISM, "tmax",
            "Below −10 °C: 0 = no, 1 = yes", "1", (0, 1),
            group="Grammar lessons", cmap="Blues", transform="state", title="From measurements to states",
            description="threshold_state() · daily maximum below −10 °C; not an event-duration map",
            lesson="vignettes/states_and_events/"),
    dict(id="fire_vase_gridmet_interactive", kind="hull", group="Specialized viewer",
         label="Fire VASE · FIRED + gridMET", path="assets/figures/fire_vase_gridmet_interactive.html",
         title="Fire VASE with gridMET temperature", lesson="capabilities/fire-vase/",
         description="Published real FIRED/gridMET hull · Plotly viewer (not a raster cube); requires CDN access"),
]
