#!/usr/bin/env python3
"""Run the bounded relational-convolution feasibility experiment offline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from relational_convolution_feasibility import (
    METRICS,
    RADII_KM,
    absolute_overlap_support,
    complete_surface_object,
    load_phase1_stack,
    long_relationship_table,
    neighboring_surface_similarity,
    representation_comparison,
    sha256_file,
    synthetic_benchmark,
    translated_edge_support,
    window_stability,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STACK = ROOT / "artifacts/synchrony-stack-phase1/prism_20x20_synchrony_stack.nc"
DEFAULT_OUTPUT = ROOT / "artifacts/relational-convolution-feasibility"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stack", type=Path, default=DEFAULT_STACK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    return parser


def _write_netcdf(dataset, path: Path) -> None:
    temporary = path.with_suffix(".partial.nc")
    dataset.to_netcdf(temporary)
    temporary.replace(path)


def _decision_table(
    representation: pd.DataFrame,
    synthetic: pd.DataFrame,
    similarity: pd.DataFrame,
    stability: pd.DataFrame,
) -> pd.DataFrame:
    delta = similarity.query("metric == 'delta_s' and radius_km == 40")
    alignment_gain = float(delta.pearson_alignment_gain.median())
    gradient_gain = float(delta.gradient_similarity_alignment_gain.median())
    stable = float(stability.spearman.min())
    transition = synthetic.query("case == 'sharp_geographic_transition'").iloc[0]
    false_anisotropy = synthetic.query("case == 'anisotropy_no_transition'").iloc[0]
    noise = synthetic.query("case == 'noise_only'").iloc[0]
    by_name = representation.set_index("representation")

    def rmse(name: str) -> str:
        return f"{by_name.loc[name, 'median_normalized_rmse']:.2f} nRMSE"

    rows = [
        ["median only", "no", "no", "no", "high", "no", "baseline", "n/a", "low", "low", "pending", "KEEP AS DIAGNOSTIC", rmse("median_only")],
        ["median + IQR/MAD", "no", "no", "no", "high", "no", "baseline", "n/a", "low", "low", "pending", "KEEP AS DIAGNOSTIC", rmse("median_iqr_mad")],
        ["nested radii", "partial", "no", "no fixed law", "high", "weak", "partial", "n/a", "low", "low", "pending", "KEEP AS DIAGNOSTIC", rmse("nested_radii")],
        ["radial profile", "partial", "no", "empirical strata", "high", "no", "distance cases", "n/a", "medium", "medium", "pending", "KEEP", rmse("fine_radial_profile")],
        ["radial + directional", "partial", "no", "empirical strata", "high", "partial", "distance/anisotropy", "n/a", "medium", "medium", "pending", "KEEP", rmse("radial_plus_directional")],
        ["PCA/SVD", "yes", "no", "no", "medium", "learned indirectly", "held-out reconstruction", "not tested across windows", "medium", "medium", "pending", "EXPERIMENTAL", rmse("pca_svd")],
        ["overlap coherence", "yes", "yes", "no", "high", "partial", "all ten cases", f"min rho {stable:.2f}", "medium", "high", "pending", "KEEP AS DIAGNOSTIC", "retains dispersion and support"],
        ["translated gradient", "yes", "yes", "no", "high", "yes", "all ten cases", f"min rho {stable:.2f}", "medium", "high", "pending", "EXPERIMENTAL", f"real median corr gain {gradient_gain:+.2f}"],
        ["surface-change operator", "yes", "yes", "no", "high", "partial", "alignment controls", f"min rho {stable:.2f}", "medium", "medium", "pending", "KEEP AS DIAGNOSTIC", f"real median corr gain {alignment_gain:+.2f}"],
        ["transition operator", "yes", "yes", "no", "medium", "yes", "transition plus null controls", f"min rho {stable:.2f}", "medium", "high", "pending", "EXPERIMENTAL", f"transition ratio {transition.translated_transition_edge_ratio:.2f}; anisotropy {false_anisotropy.translated_transition_edge_ratio:.2f}; noise {noise.translated_transition_edge_ratio:.2f}"],
        ["learned representation", "yes", "potentially", "no", "low", "unknown", "not tested", "not tested", "high", "high", "none", "DROP", "not justified beyond SVD today"],
    ]
    columns = [
        "method",
        "preserves_2d_geometry",
        "uses_overlap",
        "assumes_distance_relationship",
        "interpretable",
        "distinguishes_anisotropy_transition",
        "synthetic_recovery",
        "observation_window_stability",
        "computational_cost",
        "storage_cost",
        "station_support",
        "recommendation",
        "evidence",
    ]
    return pd.DataFrame(rows, columns=columns)


def main() -> int:
    args = _parser().parse_args()
    stack_path = args.stack.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    stack = load_phase1_stack(stack_path)
    surfaces = complete_surface_object(stack)
    surface_path = output / "real_complete_surfaces.nc"
    if args.force or not surface_path.exists():
        _write_netcdf(surfaces, surface_path)
    relationships_path = output / "real_relationship_support.csv.gz"
    if args.force or not relationships_path.exists():
        long_relationship_table(surfaces).to_csv(
            relationships_path, index=False, compression="gzip"
        )

    similarity_parts = []
    for metric in METRICS:
        similarity_parts.append(neighboring_surface_similarity(surfaces, metric=metric))
        for radius in RADII_KM:
            overlap = absolute_overlap_support(surfaces, metric=metric, radius_km=radius)
            _write_netcdf(overlap, output / f"absolute_support_{metric}_{int(radius)}km.nc")
            values = np.asarray(surfaces[metric].values).reshape(
                surfaces.sizes["focal"], surfaces.sizes["y"], surfaces.sizes["x"]
            )
            distance = np.asarray(surfaces.distance_km.values).reshape(values.shape)
            edge = translated_edge_support(
                values,
                distance,
                radius=radius,
                y=np.asarray(surfaces.y.values),
                x=np.asarray(surfaces.x.values),
            )
            edge.attrs["metric"] = metric
            _write_netcdf(edge, output / f"translated_edge_support_{metric}_{int(radius)}km.nc")
    similarity = pd.concat(similarity_parts, ignore_index=True)
    similarity.to_csv(output / "relative_vs_absolute_similarity.csv", index=False)
    representation, pca = representation_comparison(surfaces)
    representation.to_csv(output / "baseline_representation_comparison.csv", index=False)
    write_json(output / "pca_svd_experiment.json", pca)
    synthetic = synthetic_benchmark()
    synthetic.to_csv(output / "synthetic_benchmark.csv", index=False)
    stability = window_stability(surfaces)
    stability.to_csv(output / "observation_window_sensitivity.csv", index=False)
    decision = _decision_table(representation, synthetic, similarity, stability)
    decision.to_csv(output / "method_decision_table.csv", index=False)

    delta40 = similarity.query("metric == 'delta_s' and radius_km == 40")
    comparison_summary = {
        column: float(delta40[column].median())
        for column in (
            "pearson_relative",
            "pearson_absolute",
            "pearson_alignment_gain",
            "spearman_relative",
            "spearman_absolute",
            "spearman_alignment_gain",
            "rmse_relative",
            "rmse_absolute",
            "rmse_alignment_gain",
            "gradient_similarity_relative",
            "gradient_similarity_absolute",
            "gradient_similarity_alignment_gain",
        )
    }
    summary = {
        "analysis": "relational_convolution_feasibility",
        "status": "bounded experiment; no production verb",
        "source_stack": str(stack_path.relative_to(ROOT)),
        "source_stack_sha256": sha256_file(stack_path),
        "source_analysis_fingerprint": surfaces.attrs["source_analysis_fingerprint"],
        "window_start": surfaces.attrs["window_start"],
        "window_end": surfaces.attrs["window_end"],
        "focal_surface_count": surfaces.sizes["focal"],
        "directed_relationship_count": int(
            surfaces.sizes["focal"] * surfaces.sizes["comparison"]
        ),
        "canonical_pair_count": int(
            surfaces.sizes["focal"] * (surfaces.sizes["focal"] + 1) // 2
        ),
        "observation_windows_km": list(RADII_KM),
        "primary_real_comparison_radius_km": 40.0,
        "real_delta_alignment_medians": comparison_summary,
        "representation_comparison": representation.to_dict(orient="records"),
        "pca_svd": pca,
        "synthetic_results": synthetic.to_dict(orient="records"),
        "window_sensitivity": stability.to_dict(orient="records"),
        "autoencoder_tested": False,
        "pair_symmetry_policy": surfaces.attrs["pair_symmetry_policy"],
        "runtime_seconds": float(time.perf_counter() - started),
        "limitations": [
            "one 90-day PRISM window",
            "20 by 20 Front Range block; 60 km support is edge-censored",
            "candidate transition evidence is not a climate-boundary product",
            "station evaluation is a separately frozen downstream branch",
        ],
    }
    write_json(output / "feasibility_summary.json", summary)
    manifest = {
        "analysis": summary["analysis"],
        "source_stack_sha256": summary["source_stack_sha256"],
        "files": {},
    }
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "artifact_manifest.json":
            manifest["files"][path.name] = {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    write_json(output / "artifact_manifest.json", manifest)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
