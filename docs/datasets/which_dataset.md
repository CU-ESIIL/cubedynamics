# Which dataset should I use?

Choose a dataset based on spatial coverage, revisit cadence, and the variables you need:
- **gridMET**: Daily CONUS meteorology (precipitation, temperature, humidity, wind) at ~4 km; best for climate summaries and anomalies.
- **PRISM**: High-quality CONUS precipitation and temperature with long-term consistency; ideal for climatology and terrain-aware normals.
- **Sentinel-2 NDVI**: 10 m vegetation condition with 5-day revisit; best when spatial detail matters and cloud filtering is acceptable.
- **Landsat 8 (MPC)**: 30 m multispectral reflectance with long archive; use when temporal depth and surface reflectance are key.
- **FIRED**: Event and daily fire perimeters; pair with climate cubes to build fire-aware analyses and visualizations.

When in doubt, start with gridMET or PRISM to prototype verbs, then graduate to Sentinel-2 or Landsat once you know the AOI and date ranges.

---
Back to [Datasets Overview](index.md)  
Next recommended page: [Compatibility matrix](compatibility.md)
