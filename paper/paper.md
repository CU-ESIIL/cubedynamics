# CubeDynamics: Composable, streaming-first workflows for spatiotemporal environmental data cubes

## Summary

Environmental data science increasingly relies on large, gridded, spatiotemporal datasets describing climate, ecosystems, and Earth system processes. While the past decade has seen major advances in array-oriented data models and scalable computation, researchers still face substantial friction when expressing, reusing, and communicating analysis workflows that operate across space and time. *CubeDynamics* is a Python library that addresses this gap by providing a lightweight, streaming-first framework for constructing composable workflows over spatiotemporal data cubes. Built on top of established array and parallel computing libraries, CubeDynamics introduces a *VirtualCube* abstraction and a small grammar of operations that allow users to express environmental analyses as transparent, inspectable pipelines rather than monolithic scripts. The goal is not to replace existing data models or platforms, but to provide a reusable methods layer that standardizes common spatiotemporal operations and lowers the barrier to reproducible, scalable analysis.

## Statement of Need

The volume, resolution, and diversity of environmental data have expanded dramatically, driven by remote sensing, reanalysis products, ecological monitoring networks, and Earth system models. As a result, many scientific questions now require operating on multi-dimensional data cubes that span space, time, and multiple variables. In principle, modern array libraries and parallel computing frameworks enable such analyses at scale. In practice, however, much of environmental analysis remains organized around bespoke scripts that interleave data access, transformation logic, and visualization in ways that are difficult to reuse, audit, or extend.

This fragmentation is not primarily a computational limitation, but a semantic one. Researchers repeatedly implement similar patterns—spatial subsetting, temporal windowing, rolling summaries, anomaly calculations, aggregation across regions—using ad hoc code that varies subtly across projects and labs. These differences can obscure methodological assumptions, hinder comparison across studies, and increase the cost of onboarding new collaborators. Even when analyses are technically reproducible, the underlying workflows are often opaque and tightly coupled to specific datasets or execution environments.

At the same time, significant community effort has been devoted to improving data access and scalability. Cloud-optimized storage formats, analysis-ready data publishing pipelines, and virtual dataset technologies have transformed how environmental data are stored and accessed. These advances address the *where* and *how* of computation, but leave open the question of *how analyses themselves are expressed*. There remains a gap between low-level array operations and full-featured data cube platforms: a need for reusable, domain-aware workflow semantics that allow scientists to describe what they want to compute, rather than how to orchestrate each step procedurally.

CubeDynamics is designed to fill this gap. It provides a methods-focused framework for expressing spatiotemporal environmental analyses as composable pipelines, emphasizing clarity, reusability, and scalability. By codifying common analytical patterns as explicit operations on virtual data cubes, CubeDynamics reduces the amount of glue code required for typical workflows and supports more transparent, communicable science.

## Conceptual Framework and Design Philosophy

At the core of CubeDynamics is the idea that spatiotemporal environmental analysis should be organized around *virtual* representations of data cubes rather than eagerly materialized arrays. A VirtualCube represents a conceptual cube defined by a spatial domain, a temporal support, and one or more variables, without requiring immediate loading or computation. This abstraction decouples data access from analytical intent, allowing workflows to be constructed independently of the specific data source or execution environment.

CubeDynamics adopts a streaming-first design philosophy. Operations on cubes are defined lazily and composed into pipelines that can be evaluated when results are requested. This approach aligns naturally with large environmental datasets, where eager loading is often infeasible, and supports execution across a range of environments from local laptops to cloud-based or high-performance computing systems. Importantly, streaming-first computation is treated as a design constraint rather than an optimization layered on after the fact.

To make workflows explicit and reusable, CubeDynamics introduces a grammar of operations organized around *verbs* and a pipe-based composition model. Each verb represents a well-defined transformation or reduction on a cube, such as subsetting, aggregation, or summarization. Pipelines composed of these verbs read as declarative descriptions of analysis intent, making it easier to reason about, modify, and share workflows. This grammar-of-operations approach draws inspiration from other successful compositional paradigms in scientific computing, while remaining grounded in the specific needs of spatiotemporal environmental analysis.

## Core Functionality

CubeDynamics provides tools for constructing and manipulating VirtualCubes that represent spatiotemporal environmental data. Users define cubes in terms of spatial extent, temporal range, and variables of interest, while deferring decisions about data loading and execution. This separation allows the same analytical pipeline to be applied across different datasets that share compatible spatiotemporal structure.

Once a cube is defined, users apply a sequence of operations drawn from a standardized set of verbs. These operations include spatial and temporal subsetting, temporal windowing, rolling and aggregated statistics, and other common transformations used in climate and ecological analysis. Because these operations are expressed at the level of cube semantics rather than raw array manipulation, they can be composed consistently and reused across projects.

Pipelines constructed in CubeDynamics remain explicit objects that can be inspected, modified, and re-executed. This explicitness supports reproducibility by making analytical steps visible and auditable, and enables incremental development where components of a workflow can be swapped or extended without rewriting entire scripts. Visualization and output generation are treated as first-class operations within the same framework, ensuring that figures and summaries are directly tied to the underlying analysis pipeline.

## Example Workflow

A typical CubeDynamics workflow begins by defining a VirtualCube that represents a spatiotemporal domain and one or more environmental variables. The user then composes a sequence of operations that subset the cube to a region of interest, aggregate values over specified temporal windows, and compute summary statistics. Because the pipeline is defined declaratively, it can be inspected and shared before execution, and evaluated lazily when results or visualizations are requested. This approach encourages exploratory analysis while maintaining a clear record of analytical intent.

## Positioning Within the Environmental Data Science Ecosystem

CubeDynamics is intentionally scoped to complement, rather than replace, existing tools in the environmental data science ecosystem. It builds on established array data models and parallel computing frameworks, relying on them for labeled data representation and scalable execution. It does not introduce a new storage format, manage data catalogs, or perform data ingestion and indexing.

Unlike full-featured data cube platforms, CubeDynamics does not attempt to provide an end-to-end system for data publication, discovery, and serving. Instead, it focuses on the methods layer: how spatiotemporal analyses are expressed once data are accessible through array-oriented interfaces. Similarly, CubeDynamics is not a curated library of climate or ecological indicators. While it supports common analytical operations, it leaves domain-specific metric definitions to higher-level libraries and user code.

This positioning allows CubeDynamics to serve as connective tissue between diverse datasets and analysis contexts. By standardizing workflow semantics without imposing heavy infrastructure requirements, it supports a wide range of use cases while remaining lightweight and adaptable.

## Reuse, Extensibility, and Community

CubeDynamics is designed to be extensible. New data providers can be integrated by defining how VirtualCubes map onto underlying data sources, and new verbs can be added to represent additional analytical operations. Because pipelines are composed from small, well-defined components, extensions can be introduced incrementally without disrupting existing workflows.

The grammar-based design also supports reuse and teaching. Pipelines serve as executable descriptions of analysis methods, making it easier to communicate approaches across teams and to onboard new users. By elevating common spatiotemporal patterns into shared abstractions, CubeDynamics encourages convergence toward more consistent and transparent environmental data science practices.

## Acknowledgements

CubeDynamics has been developed in the context of collaborative environmental data science efforts, with an emphasis on open, reproducible research. The project reflects broader community investments in scalable computation, open-source tooling, and shared methodological infrastructure for studying Earth system processes.
