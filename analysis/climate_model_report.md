# Climate Model Report

Models are exploratory regularized linear baselines. They are descriptive/predictive association tests, not causal estimates.

## Predictor sets

- Event means: mean maximum temperature, mean minimum temperature, mean VPD, maximum VPD, mean wind speed.
- Region-season anomalies: observed value minus region-month fire-season median from the current fire population; not a true local climatological normal.
- Extreme days: fraction of daily slices above the population 90th percentile for maximum temperature, VPD, or wind speed.
- Time-resolved exposure: early, middle, and late mean temperature, VPD, wind speed plus extreme-day fractions.

## Blocked performance

| predictor_set | block | median_r2 | min_r2 | max_r2 | n |
| --- | --- | --- | --- | --- | --- |
| event means | random_fire | 0.3628 | 0.1572 | 0.5596 | 237235.0000 |
| event means | region_block | 0.3448 | 0.1459 | 0.5312 | 237235.0000 |
| event means | region_year_hash | 0.3620 | 0.1567 | 0.5587 | 237235.0000 |
| event means | year_block | 0.3609 | 0.1560 | 0.5570 | 237235.0000 |
| extreme days | random_fire | 0.0002 | 0.0001 | 0.0092 | 237235.0000 |
| extreme days | region_block | -0.0015 | -0.0029 | -0.0000 | 237235.0000 |
| extreme days | region_year_hash | 0.0001 | -0.0001 | 0.0081 | 237235.0000 |
| extreme days | year_block | 0.0001 | -0.0001 | 0.0083 | 237235.0000 |
| region-season anomalies | random_fire | 0.0020 | 0.0006 | 0.0069 | 237235.0000 |
| region-season anomalies | region_block | -0.0006 | -0.0035 | 0.0001 | 237235.0000 |
| region-season anomalies | region_year_hash | 0.0018 | 0.0006 | 0.0060 | 237235.0000 |
| region-season anomalies | year_block | 0.0019 | 0.0006 | 0.0058 | 237235.0000 |
| time-resolved exposure | random_fire | 0.0156 | 0.0026 | 0.0723 | 63840.0000 |
| time-resolved exposure | region_block | 0.0066 | 0.0015 | 0.0547 | 63840.0000 |
| time-resolved exposure | region_year_hash | 0.0143 | 0.0025 | 0.0698 | 63840.0000 |
| time-resolved exposure | year_block | 0.0150 | 0.0025 | 0.0702 | 63840.0000 |

Best transferable event-level representation by median conservative blocked R2: **event means** (0.349).
Anomalies outperform raw event means: **False**.
Temporally resolved exposure outperforms event means: **False**.

Interpretation: climate associations are real enough to shift developmental-neighborhood prevalence and response gradients, but held-out transfer is weak. The manuscript should say climate redistributes developmental opportunity, not that climate uniquely predicts form.
