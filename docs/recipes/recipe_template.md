# Recipe structure upgrade

Use this template as the starting point for new recipes and how-to guides. It emphasizes reproducibility, clarity, and links to the cube grammar.

![Recipe workflow](../assets/diagrams/recipe_workflow.png)

## Title
A concise name that highlights the objective (e.g., "Compute NDVI anomalies for fire events").

## Objective
- What question does the recipe answer?
- What cube(s) or datasets are required?
- What time span and spatial extent are expected?

## Prerequisites
- Environment setup (e.g., `pip install cubedynamics`)
- Data access assumptions (local files, cloud endpoints, authentication)
- References to [Datasets](../datasets/index.md) and [Capabilities](../capabilities.md)

## Steps
1. **Load or define the cube**: include dimension names and resolution checks.
2. **Construct the pipeline**: list verbs with short rationales and parameter choices.
3. **Inspect intermediate results**: plots, summaries, or assertions that validate semantics.
4. **Summarize outputs**: describe expected products (arrays, figures, derived cubes).

## Interpretation and caveats
- Notes on uncertainty, resolution mismatch, or assumptions
- Links to [Methods & Citation](../methods_and_citation.md) for reporting
- Suggestions for extending the recipe with additional verbs

## Reproducibility notes
- Record software versions and verb parameters
- Mention any external data lineage requirements
- Provide links back to the [Concepts](../concepts/index.md) page for terminology
