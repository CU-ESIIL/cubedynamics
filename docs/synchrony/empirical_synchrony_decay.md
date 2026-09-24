# Empirical synchrony decay

The finite-horizon experiment remains a valid negative result: under its
predeclared rule, most real PRISM curves did not reach a stable background
within 500 km. `v.empirical_synchrony_decay(...)` asks a different question:
which properties of the observed decay curve are identifiable without treating
them as hard neighborhood boundaries?

The reducer consumes an existing `local_synchrony_pairs` Dataset. It reuses
physical distance, lower-tail TMIN synchrony, strictly upper-tail TMAX
synchrony, and pairwise `Delta_S = S_cold - S_warm`. It does not stream source
data, fit a parametric kernel, weight relationships by distance, or force the
empirical curve to be monotonic.

## Returned curve properties

- `d25`, `d50`, and `d75` are robust, interpolated fractional-loss distances
  relative to a near-field level and an empirical distant background. A single
  noisy annulus is not accepted as a crossing. Unreached fractions remain
  right-censored or unresolved.
- Effective synchrony length `L` is the positive area under normalized excess
  synchrony. It is reported in kilometers and retains explicit discovery-
  boundary diagnostics.
- Initial decay rate `beta` is a background-free Theil-Sen slope of supported
  annular medians, expressed per 100 km. Near, middle, and far slopes are
  retained as multiscale diagnostics.
- The fraction of excess synchrony lost by 100 km gives the fixed control a
  direct empirical interpretation.

Cold and warm metrics are estimated independently. Cold-minus-warm contrasts
are produced only where both components are valid. These contrasts describe
spatial extent or rate; they are not `Delta_S`, which remains a synchrony-
strength contrast.

## Bounded real-data result

The retained 25-site Colorado pair table and five representative national pair
tables were reused without pair recomputation. At the primary 500 km / 20 km
configuration, d50 resolved for both tails at all 25 Colorado sites and all five
representative sites, compared with one resolved common finite horizon in the
earlier Colorado experiment. However, warm d50 did not meet the predeclared
discovery-stability gate. Effective length remained strongly boundary
dependent, and cold initial slope was too sensitive to bin width. Therefore all
three candidate metrics remain on **HOLD** for statewide mapping.

The result supports 100 km as a meaningful local-scale summary, not as an
endpoint: the median fraction of local excess lost by 100 km was about 0.35 for
cold synchrony and 0.25 for warm synchrony in the Colorado pilot. Near-field
decay was steeper than far-field decay at 84% of cold sites and 56% of warm
sites, consistent with multiscale structure.

## Reproduce the pilot

```bash
.venv/bin/python scripts/run_empirical_synchrony_decay_pilot.py
```

The command validates checkpoint hashes and fails if a required saved pair
product is missing. It does not silently acquire PRISM data or launch a full
Colorado or CONUS analysis.
