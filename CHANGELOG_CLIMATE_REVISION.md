# Climate Revision Changelog

Generated: 2026-07-22T20:51:36.624694+00:00

## Added or elevated

- Population-wide daily centroid gridMET maximum temperature, minimum temperature, VPD, and wind speed are now the main climate basis.
- Extreme-day fractions for hot, high-VPD, and windy days were derived from population 90th percentile daily-slice thresholds.
- Early, middle, and late developmental-time climate summaries were added.
- Region-month fire-season anomaly diagnostics were added and clearly labeled as observed-population diagnostics, not true local normals.
- Leakage-safe state-dependent next-day growth models were added.
- Empirical composite VASEs and difference VASEs were added to the main figure grammar.

## Removed or weakened

- The manuscript no longer treats the low-dimensional coordinate system as the final discovery.
- Claims that climate determines fire form were weakened to probabilistic opportunity language.
- Perimeter, active-edge, and perimeter-extension climate are not used as main evidence because the current table covers only 25 fires.
- Wind presence was removed from substantive interpretation because the complete event table has no variation in `wind_present_fraction`.

## Moved to supplement

- Defensive PCA and null-model diagnostics.
- Full feature-ablation and prediction audits.
- Perimeter/active-edge climate extraction appears as a pilot/limitation figure.

## Model summary

- Best transferable event-level climate representation: event means (0.349 median conservative blocked R2).
- Best state model: climate-state interaction (0.353 median conservative blocked R2).
- Anomalies outperform raw event means: False.
- Temporally resolved exposure outperforms event means: False.
- Climate-state interactions survive blocking: True.

## Analyses that could not be completed from current data

- Population-wide active-edge, newly burned area, and perimeter-extension climate attribution.
- True local climate anomalies relative to independent long-term normals.
- Humidity, precipitation, soil moisture, fuel moisture, topography, vegetation, suppression, ignition cause, wind direction, or gust analyses.
