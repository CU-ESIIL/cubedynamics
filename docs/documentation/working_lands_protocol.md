# Working Lands protocol and evidence boundary

This is the detailed protocol retained from main §4 and SI S12, Tables S16–S17.
It accompanies the [executable Working Lands lesson](../decision_vignettes/working_lands.ipynb)
and [decision validation](../decision_vignettes/validation.md). The PDFs report a
repository record reviewed at commit
`862a80aed8a2781b40e6e5293fd6cfbcba887aa4`; this page does not claim a new run.

## Question and input record

Where in the bounded central South Dakota window did daily maximum temperature
meet each cell's July empirical 0.75 quantile while daily precipitation was
at or below 0.1 mm?

| Field | Recorded value in SI Table S16 |
| --- | --- |
| Provider and product | PRISM Climate Group, AN81d/AN91d daily series |
| WGS84 bbox | `[-101.2, 43.7, -100.4, 44.3]` |
| Dates | July 1–31, 2024 |
| Variables and units | Maximum air temperature, degrees Celsius; daily precipitation total, mm |
| Shape of each noun | `31 × 15 × 19` |
| Temperature range | 21.922–40.386 °C |
| Precipitation range | 0–40.260 mm/day |
| Finite values per noun | 8,835 |
| Fixture | `tests/fixtures/real_data/sd_working_lands_july_2024.nc` |
| SHA-256 | `f9f3f0da6c621383b60d4895e661a185d3d58e7393b4f339ee91d36d83228a6a` |
| Generated measurements | None |

These are historical recorded values. Source selection keeps both branches
within one daily product family; identical reported coordinates avoid the
cross-product support problem rather than solving harmonization generally.

## Analytical statement

```python
from cubedynamics import data, pipe, verbs as v

query = dict(
    source="prism", bbox=[-101.2, 43.7, -100.4, 44.3],
    start="2024-07-01", end="2024-07-31",
)
temperature = data.temperature(**query, statistic="maximum")
precipitation = data.precipitation(**query)
warm_branch = (
    pipe(temperature)
    | v.quantile_state(
        quantile=0.75, direction="above", name="warm_july_day"
    )
)
trace_branch = (
    pipe(precipitation)
    | v.threshold_state(
        threshold=0.1, direction="below", name="trace_or_no_rain"
    )
)
analysis = (
    pipe(warm_branch.unwrap())
    | v.overlap(trace_branch.unwrap(), name="warm_and_trace_or_no_rain")
    | v.mean(dim="time", keep_dim=False)
)
frequency = analysis.unwrap()["state"]
frequency_percent = frequency * 100
```

This is the live-loader statement from the SI, not an offline acquisition
recipe. Use the maintained notebook for fixture-based execution. Comparators
are inclusive. Overlap requires exact coordinates, and the mean uses 31 indexed
days. The final percentage multiplication is outside the trace. Preserve
both branch records as well as the final record; see
[local traces](../concepts/trace_and_workflow_provenance.md).

## Interpretation and acceptance

The cited record reports 6.5–22.6% co-occurrence, or 2–7 of 31 days. “Locally
warm” is a within-month, cell-wise rank; without ties approximately one quarter
of days qualify by construction. It is not a long-term climatological anomaly.
The AOI bounds acquisition and execution; it was not selected as an established
impact hotspot. “Trace-or-no-rain” is this protocol's explicit threshold.
The result is an illustrative weather screen, not an impact, drought, causal,
or risk classification.

The documented acceptance checks reject generated measurements, incorrect
dimensions/dates/units, nonfinite or implausible input, unequal coordinates,
missing required source-QA or decision figures, unavailable public operations,
direct/piped disagreement, and failed documentation or link checks. Such checks
establish the bounded object and computational behavior, not management fitness.

The manuscript submission archive still needs the checksum-bound map, exact
serialized inspection outputs, quantile method and dependency versions,
marginal counts, and tie diagnostics. The repository fixture's presence is
distinct from a unified archived submission package. Do not replace those
records with an illustrative map. See [archival requirements](../project/manuscript_evidence_2026_10.md).

Source: [main, pp. 7–9](../assets/manuscripts/2026-10-12/main-39.pdf#page=7)
and [SI, pp. 17–20](../assets/manuscripts/2026-10-12/supplement-11.pdf#page=17).
