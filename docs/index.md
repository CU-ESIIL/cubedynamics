# Climate Cube Dynamics

## Climate Cube Dynamics: A Spatiotemporal Analysis System for Environmental Science

Environmental systems vary simultaneously in space, time, and state. Climate forcing, vegetation response, hydrology, fire regimes, and disturbance recovery all unfold as continuous spatiotemporal fields. Yet most scientific workflows still fragment these systems into stacks of rasters, disconnected time series, or collections of files that must be manually aligned.

A data cube is the simplest object that matches the structure of the real world:

V(lat, lon, time)

This representation preserves the spatial and temporal coherence that ecological and climatic processes require. With cubes, we can ask genuinely spatiotemporal scientific questions:

- How synchronized are droughts across a watershed or region?
- How does vegetation recover after a fire—and where does it fail to recover?
- When do climate anomalies propagate across space, and where do they stop?
- How variable is a climate variable across scales—seasonal, interannual, decadal?
- How do climate drivers interact with NDVI, productivity, or phenology at each location?

These are cube questions, not raster questions.

## Why a cube-native analysis system?

Traditional raster calculators let users compute expressions over 2-D layers:

- (NIR - RED) / (NIR + RED)
- landcover == 5 AND slope > 30

But modern environmental science requires operations that unfold across both space and time:

- NDVI_anomaly = (NDVI - NDVI_climatology) / NDVI_std
- fire_recovery_rate = d(NDVI) / dt after fire
- synchrony = corr(prcp(t), NDVI(t + lag))
- variance_ratio = var(temp_monthly) / var(temp_annual)
- compound_extremes = prcp > 95th AND temp > 90th over 30-year window

These are cube-level transformations, not raster-level operations.

CubeDynamics provides a cube calculator—a grammar of verbs—so that scientists can express spatiotemporal reasoning directly and clearly.

## Streaming, scaling, and VirtualCubes

Environmental datasets have become too large for memory-bound workflows.

VirtualCubes allow CubeDynamics to:

- load climate and remote-sensing data lazily,
- tile and stream data on demand,
- compute across massive spatial domains,
- maintain consistent metadata and alignment, and
- keep code simple for the analyst.

The system handles the logistics; the scientist expresses the question.

## Visualizing cubes in 3D and 2D

CubeDynamics includes interactive visualization tools:

- v.plot(): an interactive 3D cube viewer that shows spatial faces and time faces together.
- v.map(): 2-D map visualizations suitable for snapshots and animations.

These tools make the spatiotemporal structure tangible and support exploratory scientific analysis.

## Getting started

If you are new to CubeDynamics, start with the 10-minute Quickstart:
👉 [Quickstart Guide](quickstart.md)

Then explore:
- [Concepts](concepts/index.md) (What is a cube? How does the pipe & verb grammar work?)
- [How-to Guides](howto/index.md) (task-based examples)
- [Visualization](viz/index.md) (cube viewer and maps)
- [API Reference](api.md)

## Scientific mission

CubeDynamics was developed to support data-intensive environmental science at ESIIL and beyond.
It aims to make spatiotemporal analysis simple, expressive, scalable, and scientifically aligned with how ecological and climate processes operate.
