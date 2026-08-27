# Write an analysis vignette

Use this shell for a real-data story, not an API reference. Keep the analytical
pipe short; put acquisition, checks and plotting around it. See the
[collection contract](../vignettes/structure.md) for notebook heading equivalents.

## Question

Ask one question that the available observations can address. State whether this
is an executable notebook, a live-data recipe, or a dependency design.

## Grammar / pipeline

Show the short pipe, with links to the canonical [nouns](../library/index.md) and
[verbs](../reference/verbs/index.md). Do not duplicate their parameter tables.

## Plain-language interpretation

Read the pipe left to right. Explain what each step means for this question.

## Analysis

Supply complete setup, acquisition and analysis code. Declare optional
dependencies and network requirements. Check units, dimensions, CRS, missing
values and temporal coverage before combining data. Never invent observations.

## Result

Plot the computed result, label units and axes, and explain the pattern.
Distinguish a descriptive statistic from causal inference or a decision rule.
If execution is blocked, say so instead of presenting an expected plot as output.

## Data used

Record provider/product, variable, location, dates, resolution, processing,
source revision or snapshot checksum, and limitations. Link to canonical source
facts and [citation guidance](../methods_and_citation.md).

## Reproduce

Give exact setup and run commands, expected outputs and verification steps.
Declare what was actually executed, including whether live access was checked.
For supported notebooks, run `python scripts/run_vignettes.py` and
`mkdocs build --strict`.

## See also

Link the relevant noun, source, verb and next analysis story. Keep extension
ideas separate from the result that was actually produced.
