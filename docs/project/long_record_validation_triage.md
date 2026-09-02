# Long-record notebook findings: current-main triage

This triage compares the post-RC showcase notebook evidence with current
`main` at `46c9ab81152ecf13f64310a211f9db3f65b3ec3f`. An older notebook kernel
reporting `0.1.0rc1` is not by itself evidence about current source behavior.

| Finding | Classification | Current-main evidence and decision |
| --- | --- | --- |
| Main install still prints `0.1.0rc1` | **NOTEBOOK / ENVIRONMENT ISSUE** and **DOCUMENTATION / DISCOVERABILITY ISSUE** | Main intentionally retains the release-candidate semantic version. A running kernel can retain an older import, and `--ignore-installed` can churn unrelated dependencies. Add runtime/source identity and safe restart guidance; do not bump the release. |
| Hundreds of detected events look like regional episodes | **REAL CURRENT DEFECT** | `detect_events` creates one row per contiguous run at one grid cell, but `EventResult` does not state that scope. Add first-class scope and row-meaning metadata. |
| Local events need regional consolidation | **GRAMMAR GAP / NEW FEATURE** | No existing verb performs explicit space-time connected-component consolidation. Add a bounded, criteria-controlled semantic verb. |
| Annual event summaries require pandas | **GRAMMAR GAP / NEW FEATURE** | No event-aware metrics verb exists. Add a narrow period/metric operation returning ordinary xarray data. |
| Event-relative life-history trajectories | **GRAMMAR GAP / NEW FEATURE** | Existing synchrony compares event anchors but does not construct event-relative trajectories. Document the required design and defer numerical extraction until support/alignment and overlapping-event policies are explicit. |
| Annual/period signatures | **GRAMMAR GAP / NEW FEATURE** | Event metrics can already produce one explicit row per period. Defer a separate signature verb until multiple metric objects and unit-safe feature assembly have a stable contract. |
| `block_signature(...).explain()` loses `degC` | **REAL CURRENT DEFECT** | The reduced variable preserves `units`, but semantic inference reads only Dataset-level attrs. Infer a unit only when Dataset variables agree. |
| `compare_blocks` gives every metric source units | **REAL CURRENT DEFECT** | Current xarray propagation leaves `pearson_r` and `n` carrying source units. Assign metric-level units and retain per-source-variable units explicitly. |
| Large `EventResult` display overwhelms notebooks | **REAL CURRENT DEFECT** | The dataclass default repr prints the entire catalog. Replace it with a bounded scientific summary and small preview. |
| Long records may scale poorly | **REAL CURRENT DEFECT**, **EXPECTED SCIENTIFIC BEHAVIOR**, and **DOCUMENTATION / DISCOVERABILITY ISSUE** | State creation and overlap are lazy; event catalog construction necessarily materializes the state cube. Seasonal filtering also exposed that index-adjacent observations across a large coordinate gap could be joined as one event; event contiguity must respect coordinate cadence. Add a 20-year small-domain smoke test, document materialization, and use an active-window consolidation algorithm rather than unconditional all-pairs matching. |
| Multi-year `quantile_state(.90)` reference population is unclear | **DOCUMENTATION / DISCOVERABILITY ISSUE** | Current behavior correctly pools the selected `time` dimension. Record that reference population in attrs and explanations; do not add unimplemented climatology modes. |
| `sync_with` positive lag is ambiguous | **ALREADY FIXED ON MAIN** with a discoverability follow-up | Current code and an asymmetric regression define `+5D` as comparing left at `t` with right at `t+5D`; the right-hand condition occurs later. Strengthen output attrs, docs, and negative-lag coverage. |
| Rolling median-split output is not self-describing | **REAL CURRENT DEFECT** | Core variable labels and unitless attrs exist, but output-coordinate, edge, split, and reference descriptions are incomplete. Complete them without changing values. |
| Negative rolling tail values look invalid | **EXPECTED SCIENTIFIC BEHAVIOR** and **DOCUMENTATION / DISCOVERABILITY ISSUE** | The public verb is a signed upper-tail variance minus full-window variance contrast, not a probability. Negative values are valid. Preserve numerical behavior, declare squared units and an unbounded real range, and distinguish it from median-split Spearman synchrony. |
| Trend verb | **GRAMMAR GAP / NEW FEATURE** | Defer pending a stable independent-variable/unit and uncertainty contract. |
| Change-point verb | **GRAMMAR GAP / NEW FEATURE** | Defer; method choice, uncertainty, and multiple candidates need a design decision before a public verb. |
| Event classification | **GRAMMAR GAP / NEW FEATURE** | Defer opaque clustering. First stabilize scope, episode construction, metrics, and trajectory features. |
| Event-specific default plots | **DOCUMENTATION / DISCOVERABILITY ISSUE** and potential **GRAMMAR GAP / NEW FEATURE** | Existing plotting remains valid. Defer specialized defaults until the new event objects and metrics have settled; documentation will show concise ordinary plots. |

The implementation must preserve exact spatial alignment, explicit temporal
support policy, ordinary xarray interoperability, and existing numerical
behavior unless a row above identifies a current defect.
