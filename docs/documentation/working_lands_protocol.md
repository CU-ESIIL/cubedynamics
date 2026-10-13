# Working Lands protocol

The canonical executable protocol is the
[Working Lands notebook](../decision_vignettes/working_lands.ipynb). Its builder
owns the question, code, figures, interpretation, input record and reproduction
instructions. [Decision validation](../decision_vignettes/validation.md) owns
fixture checksum, query, units and acceptance criteria. These pages replace a
duplicate handwritten protocol.

The question combines July 2024 PRISM maximum temperature at each cell's
empirical 0.75 quantile with daily precipitation at or below 0.1 mm in a bounded
central South Dakota window. It is a within-month weather screen, not evidence
of drought, ecological stress, agricultural impact, fire risk or causality.
Thresholds are analytical choices, and the reported fully finite fixture avoids
the missing-as-false denominator problem for this example.

[Branch provenance](../concepts/trace_and_workflow_provenance.md) explains the
separate records needed for both branches; percent conversion after unwrapping
remains outside the trace. [Reproducibility](../reproducibility.md) separates
current notebook replay from a final archived submission bundle.

Main §4 and SI S12 remain preserved in the
[manuscript archive](overview_manuscript.md). Their historical result and
archive caveats are not relabeled as a new empirical evaluation.
