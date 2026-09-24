#!/usr/bin/env python3
"""Build the short PDF walkthrough for the non-stacked Colorado baseline."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "nonstacked-colorado-baseline"
OUTPUT = ROOT / "output" / "pdf" / "colorado_nonstacked_synchrony_baseline.pdf"
PAGE = landscape(letter)
BLUE = colors.HexColor("#123F70")
RED = colors.HexColor("#A5282D")
INK = colors.HexColor("#18212B")
LIGHT = colors.HexColor("#EAF2F8")


def _load(name: str):
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def _fitted(path: Path, width: float, height: float) -> Image:
    with PILImage.open(path) as image:
        ratio = min(width / image.width, height / image.height)
        return Image(str(path), width=image.width * ratio, height=image.height * ratio)


def _table(rows, widths=None, *, header=True, font_size=9):
    table = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AAB7C4")),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, colors.HexColor("#F6F8FA")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    table.setStyle(TableStyle(commands))
    return table


def _footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CFD8E1"))
    canvas.line(0.55 * inch, 0.43 * inch, PAGE[0] - 0.55 * inch, 0.43 * inch)
    canvas.setFillColor(colors.HexColor("#52606D"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.58 * inch, 0.22 * inch, "CubeDynamics • non-stacked Colorado synchrony baseline • observed PRISM")
    canvas.drawRightString(PAGE[0] - 0.58 * inch, 0.22 * inch, str(document.page))
    canvas.restoreState()


def build() -> Path:
    geometry = _load("geometry.json")
    findings = _load("findings.json")
    qc = _load("qc.json")
    performance = _load("performance.json")
    provenance = _load("provenance.json")
    gates = _load("engineering_gates.json")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=31, textColor=BLUE, alignment=TA_CENTER, spaceAfter=12)
    subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=14, leading=18, textColor=INK, alignment=TA_CENTER)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=BLUE, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=INK, spaceAfter=4)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10.2, leading=14, textColor=INK, spaceAfter=7)
    small = ParagraphStyle("Small", parent=body, fontSize=8.7, leading=11)
    callout = ParagraphStyle("Callout", parent=body, fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=RED, alignment=TA_CENTER, borderColor=RED, borderWidth=1, borderPadding=8, backColor=colors.HexColor("#FFF4F2"))
    code = ParagraphStyle("Code", parent=body, fontName="Courier", fontSize=9, leading=12, backColor=colors.HexColor("#F2F4F6"), borderPadding=7)

    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=PAGE, leftMargin=0.55 * inch, rightMargin=0.55 * inch,
        topMargin=0.48 * inch, bottomMargin=0.55 * inch,
        title="Non-stacked Colorado synchrony baseline",
        author="CubeDynamics project",
        subject="Immediate per-focal reduction of observed PRISM synchrony surfaces",
    )
    story = []

    state = findings["statewide_100km"]
    story.extend([
        Spacer(1, 0.35 * inch),
        Paragraph("Simple non-stacked Colorado synchrony", title),
        Paragraph("One focal pixel → one local surface → one scalar map cell", subtitle),
        Spacer(1, 0.25 * inch),
        Paragraph("NO STACKING • NO OVERLAP ALIGNMENT • NO SECOND CONVOLUTION", callout),
        Spacer(1, 0.28 * inch),
        _table([
            ["Result", "Observed statewide value", "Interpretation"],
            ["Median cold map", f"{state['cold_median_across_focal_pixels']:.3f}", "Strong positive cold-tail synchrony; pronounced geographic texture."],
            ["Median warm map", f"{state['warm_median_across_focal_pixels']:.3f}", "Higher and more spatially uniform than cold."],
            ["Median pairwise Delta", f"{state['delta_pair_median_across_focal_pixels']:.3f}", f"Cold − warm; {100*state['delta_negative_fraction']:.1f}% of focal pixels are negative."],
            ["Completed output", f"{qc['output_pixels']:,} pixels", "Every selected Colorado focal pixel has all three primary values."],
        ], widths=(1.65*inch, 1.65*inch, 5.9*inch)),
        Spacer(1, 0.2 * inch),
        Paragraph(
            "This is the simplest defensible comparator for later relational stacking: each local relationship field is reduced immediately, written to its focal cell, and discarded.",
            body,
        ),
        PageBreak(),
    ])

    pixel = geometry["approximate_pixel_resolution_km_at_colorado_mean_latitude"]
    diameter = geometry["approximate_diameter_pixels"]
    story.extend([
        Paragraph("1. What “100 × 100” means in the current implementation", h1),
        Paragraph(
            "Repository inspection resolves the apparent even-window ambiguity: production synchrony uses a <b>100 km great-circle radius</b>, not a literal 100 × 100 array. The earlier “100 × 100” label names an engineering-gate computation grid.", body),
        _table([
            ["Geometry item", "Current source-of-truth value"],
            ["PRISM grid", f"0.041667°; ≈ {pixel['east_west']:.2f} km E–W × {pixel['north_south']:.2f} km N–S at mean Colorado latitude"],
            ["Observation support", "All cell centers at great-circle distance ≤ 100 km"],
            ["Approximate diameter", f"200 km; ≈ {diameter['east_west']:.1f} × {diameter['north_south']:.1f} pixels"],
            ["Footprint", "Circular/irregular on the latitude–longitude grid; not exactly 100 × 100 pixels"],
            ["Center convention", "Exact focal grid-cell center; no half-pixel shift and no even-window centering rule"],
            ["Political boundary", "Colorado is the output mask; the observed-PRISM input extends into surrounding states as a halo"],
        ], widths=(2.15*inch, 7.1*inch)),
        Spacer(1, 0.16 * inch),
        Paragraph("Validated semantics", h2),
        Paragraph(
            "Cold uses joint lower-tail Spearman on PRISM TMIN; warm uses joint upper-tail Spearman on PRISM TMAX; Delta = cold − warm. The pair-valid median split, minimum ten points per tail, 90-day window ending 2024-01-30, canonical undirected pair symmetry, and current halo logic are reused without reimplementation.", body),
        Paragraph("The self-pair S(p,p) is removed before every count, fraction, median, quantile, or dispersion calculation.", callout),
        PageBreak(),
    ])

    story.extend([
        Paragraph("2. One center, one surface, immediate collapse", h1),
        _fitted(ARTIFACTS / "figures" / "pedagogical_reduction.png", 9.65*inch, 5.7*inch),
        Paragraph(
            f"The shown real focal pixel is at {findings['example_focal_surface']['focal_latitude']:.3f}°N, "
            f"{abs(findings['example_focal_surface']['focal_longitude']):.3f}°W. Its "
            f"{findings['example_focal_surface']['nonself_valid_delta_pairs']:,} nonself Delta pairs reduce to median "
            f"{findings['example_focal_surface']['delta_median']:+.3f}. The surface is not retained in the statewide product.", small),
        PageBreak(),
    ])

    story.extend([
        Paragraph("3. Colorado result", h1),
        _fitted(ARTIFACTS / "figures" / "primary_three_panel.png", 9.65*inch, 4.65*inch),
        Paragraph(
            "Cold and warm panels share the same symmetric color scale; Delta uses its own symmetric diverging scale centered exactly at zero. Blue is positive and red is negative. Because Delta is cold minus warm, red indicates stronger warm-tail synchrony—not cold temperature.", small),
        PageBreak(),
    ])

    dispersion = findings["local_surface_dispersion_medians"]
    gap = findings["delta_reduction_comparison"]
    story.extend([
        Paragraph("4. The two Delta reductions are close, but not identical", h1),
        _table([
            ["Quantity", "Statewide result"],
            ["Median[pairwise (cold − warm)]", f"{state['delta_pair_median_across_focal_pixels']:+.4f}"],
            ["Median absolute gap from median(cold) − median(warm)", f"{gap['median_absolute_gap']:.4f}"],
            ["95th percentile absolute gap", f"{gap['p95_absolute_gap']:.4f}"],
            ["Maximum absolute gap", f"{gap['maximum_absolute_gap']:.4f}"],
            ["Rank correlation between the two Delta maps", f"{gap['spearman_between_maps']:.4f}"],
        ], widths=(5.4*inch, 2.2*inch)),
        Spacer(1, 0.18*inch),
        Paragraph("Within-surface heterogeneity at 100 km", h2),
        _table([
            ["Metric", "Cold", "Warm", "Pairwise Delta"],
            ["Median local IQR", f"{dispersion['cold_iqr']:.3f}", f"{dispersion['warm_iqr']:.3f}", f"{dispersion['delta_iqr']:.3f}"],
            ["Median local MAD", f"{dispersion['cold_mad']:.3f}", f"{dispersion['warm_mad']:.3f}", f"{dispersion['delta_mad']:.3f}"],
        ], widths=(2.6*inch, 1.6*inch, 1.6*inch, 1.8*inch)),
        Spacer(1, 0.18*inch),
        Paragraph(
            "Cold surfaces are more heterogeneous than warm surfaces in this 90-day sample. Delta retains meaningful internal spread even though the production baseline collapses it to one median per focal cell.", body),
        _fitted(ARTIFACTS / "figures" / "qc_maps.png", 5.5*inch, 2.45*inch),
        PageBreak(),
    ])

    support = provenance["figures"]["support_spearman_correlations"]
    story.extend([
        Paragraph("5. Support and quality control", h1),
        Table([
            [_fitted(ARTIFACTS / "figures" / "support_sensitivity.png", 5.0*inch, 2.0*inch), _fitted(ARTIFACTS / "figures" / "qc_maps.png", 4.5*inch, 3.15*inch)]
        ], colWidths=(5.05*inch, 4.55*inch)),
        Spacer(1, 0.12*inch),
        _table([
            ["QC question", "Evidence"],
            ["Missing primary pixels?", "No: 0 missing among 16,235 focal pixels."],
            ["Valid fraction?", f"1.000 everywhere; counts range {qc['support']['valid_pair_count_min']:,}–{qc['support']['valid_pair_count_max']:,}."],
            ["Count dependence?", f"Weak rank associations: cold {support['cold_median']:.3f}, warm {support['warm_median']:.3f}, Delta {support['delta_pair_median']:.3f}."],
            ["Tile seams?", "No variable exceeded the predeclared 1.5× seam-jump flag; ratios are 1.02–1.04."],
            ["Border artifacts?", "No abrupt political-boundary truncation is visible; border neighborhoods use the acquired out-of-state halo."],
        ], widths=(2.15*inch, 7.1*inch)),
        PageBreak(),
    ])

    windows = provenance["figures"]["window_spearman_correlations_against_100km"]
    adjacent = findings["adjacent_pixel_pearson"]
    story.extend([
        Paragraph("6. Window sensitivity and geographic organization", h1),
        _fitted(ARTIFACTS / "figures" / "window_sensitivity.png", 9.65*inch, 2.55*inch),
        Spacer(1, 0.12*inch),
        _table([
            ["Comparison", "Rank correlation with 100 km Delta"],
            ["25 km", f"{windows['25_vs_100km']:.3f}"],
            ["50 km", f"{windows['50_vs_100km']:.3f}"],
            ["75 km", f"{windows['75_vs_100km']:.3f}"],
        ], widths=(2.2*inch, 2.7*inch)),
        Spacer(1, 0.15*inch),
        Paragraph(
            f"The baseline already has substantial local spatial organization: adjacent-pixel Pearson correlations are "
            f"{adjacent['cold_median']:.2f} cold, {adjacent['warm_median']:.2f} warm, and {adjacent['delta_pair_median']:.2f} Delta. "
            "This does not establish climate boundaries or a characteristic scale. The 25 km map is materially less rank-stable than 75 km, so the chosen observation radius remains scientifically consequential.", body),
        PageBreak(),
    ])

    gate25, gate100 = gates["gates"]
    story.extend([
        Paragraph("7. Engineering evidence and performance", h1),
        _table([
            ["Check", "25 × 25 focal gate", "Established 100 × 100 computation gate"],
            ["Real focal pixels", f"{gate25['focal_pixel_count']:,}", f"{gate100['focal_pixel_count']:,} (central 50 × 50 output)"],
            ["Tiled vs untiled max error", f"{gate25['max_tiled_absolute_error']:.1e}", f"{gate100['max_tiled_absolute_error']:.1e}"],
            ["Direct local-surface max error", f"{gate25['max_manual_surface_absolute_error']:.1e}", f"{gate100['max_manual_surface_absolute_error']:.1e}"],
            ["Self pairs excluded", f"{gate25['self_pairs_excluded_from_reduction']:,}", f"{gate100['self_pairs_excluded_from_reduction']:,}"],
            ["Wall time", f"{gate25['wall_seconds']:.1f} s", f"{gate100['wall_seconds']:.1f} s"],
        ], widths=(2.65*inch, 2.55*inch, 4.0*inch)),
        Spacer(1, 0.18*inch),
        _table([
            ["Statewide execution", "Recorded value"],
            ["Output", f"{performance['output_pixels']:,} Colorado focal pixels in {performance['tile_count']} tiles"],
            ["Nonself pair calculations", f"{performance['nonself_pair_calculations_with_tile_recompute']:,}"],
            ["Checkpoint compute span", f"{performance['checkpoint_compute_span_seconds']:.1f} s (from first to last durable tile)"],
            ["Pair-kernel CPU-stage sum", f"{performance['pair_kernel_seconds_sum']:.1f} s"],
            ["Exact reduction sum", f"{performance['exact_reduction_seconds_sum']:.1f} s"],
            ["Peak resident memory", f"{performance['process_peak_rss_bytes']/1024**3:.2f} GiB during resume/finalization; gate peak {max(gate25['process_peak_rss_bytes'], gate100['process_peak_rss_bytes'])/1024**3:.2f} GiB"],
            ["Network transfer", "0 bytes; reused the saved observed-PRISM snapshot"],
        ], widths=(2.65*inch, 6.55*inch)),
        PageBreak(),
    ])

    story.extend([
        Paragraph("8. What this baseline does—and does not—show", h1),
        _table([
            ["Supported by this run", "Not answered by this run"],
            [Paragraph("Typical cold, warm, and pairwise-Delta synchrony within a fixed 100 km neighborhood", small), Paragraph("Where synchrony boundaries are", small)],
            [Paragraph("Substantial geographic organization without stacking", small), Paragraph("Whether neighboring relational surfaces align", small)],
            [Paragraph("Exact local IQR/MAD and support diagnostics", small), Paragraph("Whether overlapping neighborhoods share geographic structure", small)],
            [Paragraph("Sensitivity across nested 25/50/75/100 km supports", small), Paragraph("A characteristic synchrony distance or the correct process scale", small)],
            [Paragraph("A reproducible one-value-per-focal-pixel comparator", small), Paragraph("Anisotropy, overlap consensus, or a second-stage convolution", small)],
        ], widths=(4.65*inch, 4.65*inch)),
        Spacer(1, 0.2*inch),
        Paragraph("What a future aligned-overlap method could add", h2),
        Paragraph(
            "It could test whether features inside neighboring local surfaces recur at the same absolute locations, preserve directional and multimodal structure discarded by the median, and identify coherent changes between relational fields. Those are hypotheses for direct comparison—not evidence that stacking is better.", body),
        Paragraph("Exact reproduction command", h2),
        Paragraph(".venv/bin/python scripts/run_nonstacked_colorado_baseline.py", code),
        Spacer(1, 0.14*inch),
        Paragraph(
            "Primary machine-readable products: artifacts/nonstacked-colorado-baseline/colorado_nonstacked_synchrony.nc, 15 GeoTIFF rasters, summary.csv, findings.json, qc.json, performance.json, provenance.json, engineering_gates.json, and fingerprint-bound tile checkpoints.", small),
    ])

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return OUTPUT


if __name__ == "__main__":
    print(build())
