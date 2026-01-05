# Project Scope

Climate Cube Math focuses on representing and analyzing spatiotemporal data cubes with a consistent grammar. The goal is to make cube-based analysis explicit, reproducible, and scalable.

## What this package does
- Provides a grammar (pipes and verbs) for spatiotemporal analysis
- Supplies ready-to-use verbs for common climate and ecological operations
- Supports streaming through large datasets via VirtualCubes
- Documents semantic expectations for spatial and temporal dimensions

## What this package does not do
- Replace xarray, dask, or the broader scientific Python stack
- Serve as a catalog for every dataset; it assumes you bring or point to data sources
- Provide interactive dashboards; visualization hooks focus on inspection and figure generation
- Guarantee statistical interpretation; domain expertise is required for appropriate use of verbs
- Enforce data governance or access controls

If your workflow needs capabilities outside this scope, consider composing CubeDynamics with other tools that specialize in those areas.
