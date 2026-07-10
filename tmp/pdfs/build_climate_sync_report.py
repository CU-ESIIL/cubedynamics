from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "pdf" / "climate_synchrony_recipe_report.pdf"
MANIFEST = ROOT / "artifacts" / "prism-full-record" / "real_prism_manifest.json"
STATS = Path("/tmp/climate_sync_stats.json")
TIMESERIES = ROOT / "artifacts" / "prism-full-record" / "real_prism_synchrony_timeseries.png"


def p(text: str, style):
    return Paragraph(text, style)


def bullet(items, style):
    return ListFlowable(
        [ListItem(Paragraph(item, style), leftIndent=12) for item in items],
        bulletType="bullet",
        leftIndent=16,
        bulletFontSize=8,
    )


def table(data, widths=None, header=True):
    tbl = Table(data, colWidths=widths, hAlign="LEFT")
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 10.5),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d5d9df")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eef5")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f2a3d")),
            ]
        )
    tbl.setStyle(TableStyle(style))
    return tbl


def wrapped_table(data, styles, widths=None, header=True):
    wrapped = []
    for row_idx, row in enumerate(data):
        style = styles["TableHeader"] if row_idx == 0 and header else styles["TableCell"]
        wrapped.append([Paragraph(str(cell), style) for cell in row])
    return table(wrapped, widths=widths, header=header)


def code_block(text: str, styles):
    rows = [[Paragraph(line.replace(" ", "&nbsp;"), styles["CodeBlock"]) ] for line in text.strip().splitlines()]
    tbl = Table(rows, colWidths=[6.85 * inch], hAlign="LEFT")
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8fa")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tbl


def fmt(value, digits=3):
    return f"{value:.{digits}f}"


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#687385"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "CubeDynamics climate synchrony recipe report")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    stats = json.loads(STATS.read_text(encoding="utf-8"))

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "TitleBig",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=colors.HexColor("#182233"),
            alignment=TA_CENTER,
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#46556b"),
            alignment=TA_CENTER,
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            "H1Custom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#182233"),
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            "H2Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=15,
            textColor=colors.HexColor("#25344a"),
            spaceBefore=8,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontSize=9.8,
            leading=13.6,
            textColor=colors.HexColor("#26313f"),
            alignment=TA_LEFT,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontSize=8.4,
            leading=11,
            textColor=colors.HexColor("#4c596b"),
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "TableCell",
            parent=styles["BodyText"],
            fontSize=8.0,
            leading=10,
            textColor=colors.HexColor("#26313f"),
            splitLongWords=True,
        )
    )
    styles.add(
        ParagraphStyle(
            "TableHeader",
            parent=styles["TableCell"],
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1f2a3d"),
        )
    )
    styles.add(
        ParagraphStyle(
            "CodeBlock",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=7.4,
            leading=9,
            textColor=colors.HexColor("#24292f"),
        )
    )
    styles.add(
        ParagraphStyle(
            "Callout",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#16243a"),
            backColor=colors.HexColor("#eef6ff"),
            borderColor=colors.HexColor("#b6d7ff"),
            borderWidth=0.6,
            borderPadding=8,
            spaceBefore=4,
            spaceAfter=10,
        )
    )

    story = []
    story.append(Spacer(1, 0.65 * inch))
    story.append(p("Climate Synchrony Recipe", styles["TitleBig"]))
    story.append(
        p(
            "A full report on the CubeDynamics median-split climate synchrony workflow, "
            "including what it measures, how the recipe works, and how to interpret the PRISM full-record example.",
            styles["Subtitle"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        wrapped_table(
            [
                ["Recipe", "Rolling climate synchrony vs center pixel"],
                ["Primary verb", "v.rolling_median_split_synchrony(...)"],
                ["Climate variables", "PRISM tmin for cold-side synchrony; PRISM tmax for hot-side synchrony"],
                ["Example record", f"{manifest['start']} to {manifest['end']}"],
                ["Example AOI", str(manifest["bbox"])],
                ["Output", "Three synchrony cubes: bottom_synchrony, top_synchrony, bottom_minus_top"],
            ],
            styles,
            widths=[1.6 * inch, 5.0 * inch],
            header=False,
        )
    )
    story.append(Spacer(1, 0.35 * inch))
    story.append(
        p(
            "Plain-language thesis: the recipe asks whether cold days and hot days are spatially coordinated "
            "across a region, and whether that coordination differs between the cold tail and the hot tail.",
            styles["Callout"],
        )
    )
    story.append(PageBreak())

    story.append(p("1. Executive Summary", styles["H1Custom"]))
    story.append(
        p(
            "The climate synchrony recipe measures how similarly each grid cell behaves relative to a reference "
            "cell through time. In the current recipe, the reference is the center pixel of the cube. The method "
            "runs in rolling time windows, splits each window into lower and upper halves by each series' own "
            "median, and computes Spearman synchrony separately for cold-side minimum temperature and hot-side "
            "maximum temperature.",
            styles["Body"],
        )
    )
    story.append(
        p(
            "The result is a compact spatiotemporal summary of whether unusually cold conditions and unusually "
            "hot conditions are more or less synchronized across the area. The most interpretable output is "
            "bottom_minus_top: positive values mean stronger below-median tmin synchrony; negative values mean "
            "stronger above-median tmax synchrony.",
            styles["Body"],
        )
    )
    story.append(
        wrapped_table(
            [
                ["Question", "How the recipe answers it"],
                [
                    "Are cold conditions coordinated across space?",
                    "Compute below-median synchrony from daily minimum temperature in each rolling window.",
                ],
                [
                    "Are hot conditions coordinated across space?",
                    "Compute above-median synchrony from daily maximum temperature in each rolling window.",
                ],
                [
                    "Which side is more synchronized?",
                    "Subtract hot-side synchrony from cold-side synchrony at each grid cell and output time.",
                ],
                [
                    "How does this change through time?",
                    "Repeat the calculation for rolling windows and summarize the resulting cube through time.",
                ],
            ],
            styles,
            widths=[2.15 * inch, 4.55 * inch],
        )
    )

    story.append(p("2. What the Recipe Is Trying To Do", styles["H1Custom"]))
    story.append(
        p(
            "Climate synchrony is about shared timing and rank-order behavior, not just mean climate. Two places "
            "can have different absolute temperatures but still be synchronous if their warm and cold periods "
            "rise and fall together. The recipe therefore focuses on correlation structure through time, computed "
            "locally for every grid cell against the cube's center cell.",
            styles["Body"],
        )
    )
    story.append(
        p(
            "The median split is the central design choice. Instead of averaging minimum and maximum temperature "
            "into a single mean-temperature signal, the recipe treats cold-side and hot-side dynamics as separate "
            "objects. For cold synchrony it uses tmin and keeps dates where both the cell and reference are at or "
            "below their own window medians. For hot synchrony it uses tmax and keeps dates where both are above "
            "their own medians.",
            styles["Body"],
        )
    )
    story.append(
        bullet(
            [
                "Cold-side result: bottom_synchrony, built from below-median tmin dates.",
                "Hot-side result: top_synchrony, built from above-median tmax dates.",
                "Difference result: bottom_minus_top, equal to cold-side synchrony minus hot-side synchrony.",
                "Reference geometry: each grid cell is compared with the center pixel of the same cube.",
            ],
            styles["Body"],
        )
    )
    story.append(PageBreak())

    story.append(p("3. How the Workflow Works", styles["H1Custom"]))
    workflow = [
        ["Step", "Operation", "Why it matters"],
        ["1", "Load daily tmin and tmax climate cubes.", "Keeps cold and hot climate information separate."],
        ["2", "Choose a rolling window, usually 90 days.", "Defines the period over which synchrony is estimated."],
        ["3", "For each cell and reference series, compute each series' window median.", "Creates local thresholds instead of using one regional cutoff."],
        ["4", "Select lower-tail dates for tmin and upper-tail dates for tmax.", "Separates cold-side and hot-side climate behavior."],
        ["5", "Compute Spearman synchrony against the center cell.", "Measures rank-order co-movement rather than absolute equality."],
        ["6", "Output cold, hot, and difference cubes.", "Supports both spatial cube viewing and flat time summaries."],
    ]
    story.append(wrapped_table(workflow, styles, widths=[0.45 * inch, 2.45 * inch, 3.8 * inch]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(p("Conceptual algorithm", styles["H2Custom"]))
    story.append(
        code_block(
            """
temperature = load_prism_cube(variables=["tmin", "tmax"], freq="D")

sync = pipe(temperature) | v.rolling_median_split_synchrony(
    lower_var="tmin",
    upper_var="tmax",
    window_days=90,
    min_t=10,
    split_quantile=0.5,
    output_stride=30,
)

cold_sync = sync["bottom_synchrony"]
hot_sync = sync["top_synchrony"]
cold_minus_hot = sync["bottom_minus_top"]
""",
            styles,
        )
    )
    story.append(
        p(
            "The implementation is pipe-friendly, so the synchrony operation can be composed with loaders, plotting "
            "verbs, spatial block comparison verbs, and diagnostic report verbs.",
            styles["Body"],
        )
    )
    story.append(PageBreak())

    story.append(p("4. Full-Record PRISM Example", styles["H1Custom"]))
    dims = stats["dims"]
    story.append(
        p(
            "The saved full-record example uses real PRISM daily temperature streamed through the NCSCO THREDDS "
            "NetCDF Subset Service. It avoids downloading the full archive by requesting AOI-cropped daily data, "
            "then checkpointing rolling-window synchrony batches.",
            styles["Body"],
        )
    )
    run_table = [
        ["Field", "Value"],
        ["Source", manifest["source"]],
        ["Streaming service", manifest["streaming_service"]],
        ["Protocol", manifest["streaming_protocol"]],
        ["Synthetic data", str(manifest["is_synthetic"])],
        ["Input period", f"{manifest['start']} through {manifest['end']}"],
        ["Output window endpoints", f"{stats['time_start']} through {stats['time_end']}"],
        ["Bounding box", str(manifest["bbox"])],
        ["Input shape", f"{manifest['input_shape']['time']} daily steps by {manifest['input_shape']['y']} by {manifest['input_shape']['x']} cells"],
        ["Output shape", f"{dims['time_window_end']} windows by {dims['y']} by {dims['x']} cells"],
        ["Cells per time slice", f"{stats['cell_count_per_timestep']:,}"],
        ["Voxels per variable", f"{stats['voxels_per_variable']:,}"],
        ["Values across three variables", f"{stats['values_all_variables']:,}"],
        ["Window and stride", f"{manifest['window_days']} day window, {manifest['output_stride']} day output stride"],
        ["Observed run time", f"{manifest['elapsed_minutes']} minutes"],
    ]
    story.append(wrapped_table(run_table, styles, widths=[2.0 * inch, 4.7 * inch]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        p(
            "For this run, the output time resolution is approximately monthly: the input is daily, each estimate "
            "summarizes the previous 90 days, and a new output is emitted every 30 input days.",
            styles["Callout"],
        )
    )
    story.append(PageBreak())

    story.append(p("5. Summary Plot and Results", styles["H1Custom"]))
    if TIMESERIES.exists():
        img = Image(str(TIMESERIES))
        img._restrictSize(6.85 * inch, 3.05 * inch)
        story.append(img)
        story.append(
            p(
                "Figure 1. Spatial median synchrony through time for the PRISM full-record example. "
                "Blue is below-median tmin synchrony, orange is above-median tmax synchrony, and green is cold minus hot.",
                styles["Small"],
            )
        )
    result_rows = [
        ["Metric", "Mean", "Median", "Min", "Max", "Std dev"],
    ]
    label_map = {
        "bottom_synchrony": "Cold-side tmin synchrony",
        "top_synchrony": "Hot-side tmax synchrony",
        "bottom_minus_top": "Cold minus hot",
    }
    for key in ["bottom_synchrony", "top_synchrony", "bottom_minus_top"]:
        row = stats[key]
        result_rows.append(
            [
                label_map[key],
                fmt(row["spatial_median_mean"]),
                fmt(row["spatial_median_median"]),
                fmt(row["spatial_median_min"]),
                fmt(row["spatial_median_max"]),
                fmt(row["spatial_median_std"]),
            ]
        )
    story.append(table(result_rows, widths=[2.25 * inch, 0.82 * inch, 0.82 * inch, 0.82 * inch, 0.82 * inch, 0.82 * inch]))
    story.append(
        p(
            f"Across rolling-window spatial medians, cold-side synchrony was greater than hot-side synchrony in "
            f"{stats['cold_greater_fraction'] * 100:.1f}% of output windows. The median cold-minus-hot value was "
            f"{fmt(stats['bottom_minus_top']['spatial_median_median'])}, so the example area usually shows slightly "
            "stronger hot-side synchrony than cold-side synchrony.",
            styles["Body"],
        )
    )
    story.append(
        bullet(
            [
                "Both cold and hot synchrony are high for much of the record.",
                "Hot-side tmax synchrony is usually a little higher than cold-side tmin synchrony.",
                "The difference curve stays near zero, with short departures in both directions.",
                "The recipe is therefore detecting a contrast in synchrony structure, not a large mean-temperature trend.",
            ],
            styles["Body"],
        )
    )
    story.append(PageBreak())

    story.append(p("6. Interpreting the Cubes", styles["H1Custom"]))
    story.append(
        p(
            "Each synchrony cube has axes of time_window_end, y, and x. A single time slice is a map of how every "
            "cell's recent climate ranks moved with the reference cell. Moving along the time axis shows how this "
            "spatial relationship changes from window to window.",
            styles["Body"],
        )
    )
    story.append(
        wrapped_table(
            [
                ["Value", "Interpretation"],
                ["Near +1 in bottom_synchrony", "The cell and reference have very similar cold-side rank behavior."],
                ["Near +1 in top_synchrony", "The cell and reference have very similar hot-side rank behavior."],
                ["Positive bottom_minus_top", "Cold-side synchrony is stronger than hot-side synchrony."],
                ["Negative bottom_minus_top", "Hot-side synchrony is stronger than cold-side synchrony."],
                ["Near 0 difference", "Cold and hot synchrony are similar, even if both are high."],
                ["Missing or unstable values", "There were not enough paired observations in that tail set, or the local window was degenerate."],
            ],
            styles,
            widths=[2.35 * inch, 4.35 * inch],
        )
    )
    story.append(p("Important interpretation guardrails", styles["H2Custom"]))
    story.append(
        bullet(
            [
                "Synchrony is a relationship measure. It does not say whether temperatures are high or low in absolute terms.",
                "The center pixel is the current reference. Different references can produce different synchrony fields.",
                "The median split is local to each rolling window and each series, so it compares relative cold and hot states.",
                "The PRISM example is regional. PRISM is a US product and is not the global backend for whole-globe analysis.",
            ],
            styles["Body"],
        )
    )
    story.append(PageBreak())

    story.append(p("7. Scaling From One Cube To Panels and Blocks", styles["H1Custom"]))
    story.append(
        p(
            "The recipe naturally extends from one AOI to many. Each AOI or block can produce its own synchrony cube. "
            "Those cubes can then be stacked along a comparison dimension such as block, scenario, or region, and "
            "displayed as a faceted panel of interactive cubes.",
            styles["Body"],
        )
    )
    story.append(
        code_block(
            """
cubes = []
for block_name, temperature in temperature_cubes.items():
    sync = pipe(temperature) | v.rolling_median_split_synchrony(
        lower_var="tmin",
        upper_var="tmax",
        window_days=90,
        output_stride=30,
    )
    cubes.append(sync["bottom_minus_top"].clip(-2, 2))

panel_cube = xr.concat(cubes, dim=xr.IndexVariable("block", list(temperature_cubes)))
CubePlot(panel_cube, time_dim="time_window_end").facet_wrap("block", ncol=3)
""",
            styles,
        )
    )
    story.append(
        p(
            "This block-panel structure is the bridge from pairwise AOI comparisons toward meta-analysis. The current "
            "implementation is useful for small to medium panels. For global work, the important engineering step is "
            "tiling the planet into bounded blocks and streaming or checkpointing one block at a time.",
            styles["Body"],
        )
    )
    story.append(p("Performance notes", styles["H2Custom"]))
    story.append(
        bullet(
            [
                "The full-record PRISM example uses server-side AOI streaming, not full archive downloads.",
                "Checkpoint batches keep long runs resumable and avoid one huge Dask graph.",
                "The present full-record example wrote a compact NetCDF output of the computed synchrony, not the raw full PRISM archive.",
                "Future global runs should use a cloud-native global climate backend rather than PRISM.",
            ],
            styles["Body"],
        )
    )
    story.append(PageBreak())

    story.append(p("8. Reproducibility", styles["H1Custom"]))
    story.append(
        p(
            "The report is based on the current CubeDynamics recipe and the saved full-record artifact under "
            "artifacts/prism-full-record. The key commands are below.",
            styles["Body"],
        )
    )
    story.append(p("Full-record PRISM run", styles["H2Custom"]))
    story.append(
        code_block(
            """
python examples/real_prism_median_split_synchrony.py \\
  --output-dir artifacts/prism-full-record
""",
            styles,
        )
    )
    story.append(p("Offline demonstration run", styles["H2Custom"]))
    story.append(
        code_block(
            """
python examples/median_split_synchrony_demo.py \\
  --output-dir artifacts/median-split-demo
""",
            styles,
        )
    )
    story.append(p("Panel of multiple synchrony cubes", styles["H2Custom"]))
    story.append(
        code_block(
            """
python examples/climate_synchrony_cube_panel_demo.py \\
  --output docs/assets/figures/climate_synchrony_cube_panel.html
""",
            styles,
        )
    )
    story.append(p("Primary files used for this report", styles["H2Custom"]))
    story.append(
        wrapped_table(
            [
                ["File", "Role"],
                ["docs/recipes/climate_tail_dep_center.md", "Recipe documentation and user-facing explanation."],
                ["src/cubedynamics/verbs/stats.py", "Implementation of v.rolling_median_split_synchrony."],
                ["examples/real_prism_median_split_synchrony.py", "Full-record PRISM streaming example."],
                ["artifacts/prism-full-record/real_prism_manifest.json", "Run configuration and dimensions."],
                ["artifacts/prism-full-record/real_prism_synchrony.nc", "Saved synchrony dataset used for numeric summaries."],
                ["artifacts/prism-full-record/real_prism_synchrony_timeseries.png", "Summary plot included in this report."],
            ],
            styles,
            widths=[3.1 * inch, 3.6 * inch],
        )
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.7 * inch,
        title="Climate Synchrony Recipe Report",
        author="CubeDynamics",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    build()
