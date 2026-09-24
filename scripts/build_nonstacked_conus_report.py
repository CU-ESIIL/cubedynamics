#!/usr/bin/env python3
"""Build the concise CONUS baseline and station-agreement report."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts" / "nonstacked-conus-baseline"
STATIONS = BASE / "station_validation"


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _metric_row(label: str, values: dict) -> str:
    return (
        f"| {label} | {values['n']:,} | {values['bias']:+.3f} | "
        f"{values['mae']:.3f} | {values['rmse']:.3f} | "
        f"{values['pearson']:.3f} | {values['spearman']:.3f} |"
    )


def main() -> int:
    provenance = _read(BASE / "provenance.json")
    findings = _read(BASE / "findings.json")
    qc = _read(BASE / "qc.json")
    validation = _read(STATIONS / "validation_summary.json")
    conus = findings["conus_100km"]
    reduction = findings["delta_reduction_comparison"]
    pair = validation["pair_agreement"]
    mapped = validation["collapsed_map_agreement"]
    daily = validation["daily_same_label_station_median_metrics"]

    lines = [
        "# CONUS non-stacked synchrony baseline and station agreement",
        "",
        "## Outcome",
        "",
        f"The Colorado immediate-reduction method was expanded to all {provenance['output_pixels']:,} "
        "complete native PRISM CONUS cells for 2023-11-01 through 2024-01-30. Each focal cell "
        "was reduced independently over eligible non-self neighbors within 100 km. No stack, "
        "overlap alignment, or second-stage convolution was used.",
        "",
        f"Across focal cells, the median cold map value is {conus['cold_median_across_focal_pixels']:.3f}, "
        f"the median warm map value is {conus['warm_median_across_focal_pixels']:.3f}, and the median "
        f"pairwise Delta (cold - warm) is {conus['delta_pair_median_across_focal_pixels']:+.3f}. "
        f"Delta is negative at {100 * conus['delta_negative_fraction']:.1f}% of cells.",
        "",
        "![CONUS cold, warm, and Delta maps](figures/primary_three_panel.png)",
        "",
        "## Exact method carried forward",
        "",
        "- Real PRISM AN daily TMIN/TMAX on the native 1/24-degree grid.",
        "- Local per-pixel median split (q=0.5), joint-tail selection, and Spearman dependence.",
        "- Nested 25, 50, 75, and 100 km great-circle radii; 100 km is the primary map.",
        "- Center-to-center self relationships excluded before every reduction.",
        "- Pairwise `median(cold - warm)` retained separately from `median(cold) - median(warm)`.",
        "- Only finite PRISM CONUS cells are eligible pair endpoints. Neighborhoods at Canada, "
        "Mexico, and coast boundaries are clipped to product support.",
        "",
        "## Map QC",
        "",
        f"The two Delta reductions have Spearman agreement {reduction['spearman_between_maps']:.3f}; "
        f"their median absolute gap is {reduction['median_absolute_gap']:.4f} and 95th-percentile "
        f"absolute gap is {reduction['p95_absolute_gap']:.4f}. The minimum/median/maximum valid "
        f"100 km support counts are {qc['support']['count_min']:,} / "
        f"{qc['support']['count_median']:.0f} / {qc['support']['count_max']:,}.",
        "",
        "![CONUS support and reduction QC](figures/qc_maps.png)",
        "",
        "## GHCN-Daily observational agreement",
        "",
        f"The validation branch selected {validation['selected_count']:,} quality-controlled, "
        f"spatially balanced GHCN-Daily stations and built {validation['pair_count']:,} non-self "
        "station edges no longer than 100 km. The collapsed map comparison retains "
        f"{validation['eligible_collapsed_station_count']:,} stations with at least "
        f"{validation['minimum_neighbors_for_map_comparison']} finite incident station-pair values "
        "for each of cold, warm, and Delta.",
        "",
        "![Spatially balanced GHCN-Daily validation network](station_validation/figures/station_network.png)",
        "",
        "### Daily temperature agreement at the nearest PRISM cell",
        "",
        "| Variable | Median bias (deg C) | Median MAE (deg C) | Median RMSE (deg C) | Median Pearson | Median Spearman |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *[
            f"| {name} | {daily[name]['bias']:+.3f} | {daily[name]['mae']:.3f} | "
            f"{daily[name]['rmse']:.3f} | {daily[name]['pearson']:.3f} | "
            f"{daily[name]['spearman']:.3f} |"
            for name in ("TMIN", "TMAX")
        ],
        "",
        "The same-date label produced substantially better station agreement than shifting PRISM "
        "by either -1 or +1 day; no silent time shift was applied.",
        "",
        "### Station-pair versus matched PRISM-pixel synchrony",
        "",
        "| Metric | N | Bias | MAE | RMSE | Pearson | Spearman |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        *[_metric_row(name.title(), pair[name]) for name in ("cold", "warm", "delta")],
        "",
        "![Station-pair versus nearest-PRISM-pixel relationships](station_validation/figures/pair_station_vs_prism.png)",
        "",
        "### Collapsed station neighborhoods versus final CONUS raster",
        "",
        "| Metric | N | Bias | MAE | RMSE | Pearson | Spearman |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        *[_metric_row(name.title(), mapped[name]) for name in ("cold", "warm", "delta")],
        "",
        "![Collapsed station neighborhoods versus raster](station_validation/figures/collapsed_station_vs_map.png)",
        "",
        "## Interpretation limits",
        "",
        "This is a national winter-window baseline, not a climatology or proof of a stable climate "
        "regionalization. GHCN is an external measurement route but not a strictly independent "
        "holdout: PRISM AN daily uses all station networks it ingests, and exact product-period "
        "membership for the selected GHCN stations is unavailable. Pair edges also share stations, "
        "and station-neighborhood medians sample a much sparser, irregular graph than the raster. "
        "Accordingly, the report calls the result observational agreement and supplies spatial-block "
        "bootstrap intervals for collapsed comparisons; it does not report independent-edge p-values.",
        "",
        "## Products and reproduction",
        "",
        "- `conus_nonstacked_synchrony.nc`: complete nested-radius statistics.",
        "- `rasters/`: 15 primary/QC GeoTIFFs at 100 km.",
        "- `tiles/`: restartable fingerprint-bound computation checkpoints.",
        "- `station_validation/`: station manifest, QC observations, pair table, collapsed comparison, "
        "uncertainty summary, and figures.",
        "- `provenance.json`, `performance.json`, `findings.json`, `qc.json`, and `summary.csv`: "
        "machine-readable evidence.",
        "",
        "```bash",
        ".venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage acquire",
        ".venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage analyze",
        ".venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage finalize",
        ".venv/bin/python scripts/validate_nonstacked_conus_stations.py --stage acquire",
        ".venv/bin/python scripts/validate_nonstacked_conus_stations.py --stage analyze",
        ".venv/bin/python scripts/build_nonstacked_conus_report.py",
        "```",
        "",
        "Sources: [PRISM datasets](https://www.prism.oregonstate.edu/documents/PRISM_datasets.pdf) "
        "and [NOAA/NCEI GHCN-Daily](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily).",
        "",
    ]
    (BASE / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(BASE / "REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
