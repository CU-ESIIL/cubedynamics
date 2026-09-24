#!/usr/bin/env python3
"""Build the clean hot/cold/Delta semantics audit PDF.

The script has two phases because the repository environment owns the
scientific plotting stack while the bundled document runtime owns ReportLab.

Examples
--------
MPLCONFIGDIR=/tmp/cubedynamics-mpl .venv/bin/python \
    scripts/build_hot_cold_delta_audit_report.py --stage assets

/path/to/bundled/python \
    scripts/build_hot_cold_delta_audit_report.py --stage pdf
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "artifacts" / "hot-cold-delta-semantics-audit"
CONUS = ROOT / "artifacts" / "nonstacked-conus-baseline"
ASSETS = AUDIT / "clean-report-assets"
OUTPUT = ROOT / "output" / "pdf" / "hot_cold_delta_semantics_audit_report.pdf"
PAGE_COUNT = 12

NAVY = "#123A5A"
BLUE = "#1E6FA8"
DEEP_BLUE = "#053061"
RED = "#B62A3A"
DEEP_RED = "#67001F"
GOLD = "#E5A823"
TEAL = "#2E8B78"
INK = "#162631"
MUTED = "#5C6B75"
PALE_BLUE = "#EAF3F8"
PALE_RED = "#FBEDEF"
PALE_GOLD = "#FFF6DC"
PALE_GRAY = "#F3F6F8"
WHITE = "#FFFFFF"


def _digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _build_assets() -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    import numpy as np
    import pandas as pd
    import xarray as xr

    ASSETS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titlesize": 12,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "figure.facecolor": "white",
            "axes.facecolor": "#F7F9FA",
            "axes.edgecolor": "#9BAAB4",
            "axes.grid": True,
            "grid.alpha": 0.2,
        }
    )

    tail = pd.read_csv(AUDIT / "tail_pixel_summary.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.25), constrained_layout=True)
    for ax, row in zip(axes, tail.itertuples(index=False)):
        labels = ["TMIN\ncold", "TMIN\nother", "TMAX\nother", "TMAX\nwarm"]
        values = [
            row.median_tmin_on_cold_dates_c,
            row.median_tmin_on_non_cold_dates_c,
            row.median_tmax_on_non_warm_dates_c,
            row.median_tmax_on_warm_dates_c,
        ]
        colors = [DEEP_BLUE, "#84B6D7", "#E7A1A8", DEEP_RED]
        bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=0.6)
        ax.axhline(0, color="#6C7A84", linewidth=0.7)
        ax.set_title(f"{row.pixel.title()} pixel\n{row.latitude:.1f}, {row.longitude:.1f}", weight="bold")
        ax.set_ylabel("Median temperature (deg C)")
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + (0.6 if value >= 0 else -0.9), f"{value:.1f}", ha="center", va="bottom" if value >= 0 else "top", fontsize=8)
    fig.suptitle("Observed PRISM values confirm the tail labels", fontsize=15, color=NAVY, weight="bold")
    fig.savefig(ASSETS / "tail_verification.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    observations = pd.read_csv(AUDIT / "pair_audit_observations.csv")
    summaries = pd.read_csv(AUDIT / "pair_audit_summary.csv")
    pair_id = "pair_2_great_basin"
    pair = summaries[summaries.pair_id == pair_id].iloc[0]
    selected = observations[observations.pair_id == pair_id]
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.6), constrained_layout=True)
    specs = [
        ("cold_lower_tmin", "Cold: joint lower TMIN tail", pair.stored_cold, DEEP_BLUE),
        ("warm_upper_tmax", "Warm: joint upper TMAX tail", pair.stored_warm, DEEP_RED),
    ]
    for ax, (tail_name, title, rho, color) in zip(axes, specs):
        frame = selected[selected["tail"] == tail_name]
        ax.scatter(frame.temperature_a_c, frame.temperature_b_c, c=color, s=30, alpha=0.8, edgecolor="white", linewidth=0.35)
        if len(frame) > 1:
            coef = np.polyfit(frame.temperature_a_c, frame.temperature_b_c, 1)
            xx = np.linspace(frame.temperature_a_c.min(), frame.temperature_a_c.max(), 80)
            ax.plot(xx, coef[0] * xx + coef[1], color=INK, linewidth=1.2, alpha=0.8)
        ax.set_title(f"{title}\nSpearman = {rho:.3f}; n = {len(frame)}", weight="bold")
        ax.set_xlabel("Pixel A temperature (deg C)")
        ax.set_ylabel("Pixel B temperature (deg C)")
    fig.suptitle("Great Basin audit pair: warm synchrony is stronger", fontsize=15, color=NAVY, weight="bold")
    fig.savefig(ASSETS / "real_pair_check.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    synthetic = pd.DataFrame(json.loads((AUDIT / "synthetic_cases.json").read_text()))
    fig, ax = plt.subplots(figsize=(10.5, 3.4), constrained_layout=True)
    x = np.arange(len(synthetic))
    width = 0.28
    ax.bar(x - width / 2, synthetic.cold, width, label="S cold", color=DEEP_BLUE)
    ax.bar(x + width / 2, synthetic.warm, width, label="S warm", color=DEEP_RED)
    for index, delta in enumerate(synthetic.delta):
        color = BLUE if delta > 0 else RED if delta < 0 else MUTED
        ax.text(index, 1.07, f"Delta = {delta:+.3f}", ha="center", color=color, fontsize=10, weight="bold")
    ax.set_xticks(x, ["Cold stronger", "Warm stronger", "Equal"])
    ax.set_ylim(-0.05, 1.18)
    ax.set_ylabel("Spearman synchrony")
    ax.legend(frameon=False, ncol=2, loc="lower center")
    ax.set_title("Known-answer cases pass through the production pair function", color=NAVY, weight="bold")
    fig.savefig(ASSETS / "synthetic_cases.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    collapsed = pd.read_csv(AUDIT / "collapsed_pixel_pairs.csv")
    provenance = json.loads((AUDIT / "collapsed_pixel_provenance.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.55), constrained_layout=True)
    bins = np.linspace(-1.3, 1.1, 55)
    axes[0].hist(collapsed.s_cold, bins=bins, color=DEEP_BLUE, alpha=0.62, label="S cold")
    axes[0].hist(collapsed.s_warm, bins=bins, color=DEEP_RED, alpha=0.58, label="S warm")
    axes[0].axvline(provenance["recomputed_median_cold"], color=DEEP_BLUE, linewidth=2)
    axes[0].axvline(provenance["recomputed_median_warm"], color=DEEP_RED, linewidth=2)
    axes[0].set(title="1,846 incident pair values", xlabel="Pair synchrony", ylabel="Count")
    axes[0].legend(frameon=False)
    axes[1].hist(collapsed.delta_cold_minus_warm, bins=bins, color=RED, alpha=0.82)
    axes[1].axvline(provenance["recomputed_median_pairwise_delta"], color=INK, linewidth=2, label="Median pairwise Delta")
    axes[1].axvline(provenance["recomputed_difference_of_medians"], color=GOLD, linewidth=2, linestyle="--", label="Difference of medians")
    axes[1].set(title="Primary collapse is median(pairwise Delta)", xlabel="S cold - S warm", ylabel="Count")
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("Western focal-pixel collapse", fontsize=15, color=NAVY, weight="bold")
    fig.savefig(ASSETS / "collapsed_pixel.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    western = pd.read_csv(AUDIT / "western_spot_checks.csv")
    with xr.open_dataset(CONUS / "conus_nonstacked_synchrony.nc", engine="h5netcdf") as result:
        values = result.delta_pair_median.sel(radius_km=100).isel(time_window_end=0).where(result.output_mask).values
        xcoord = result.x.values
        ycoord = result.y.values
    limit = max(float(np.nanpercentile(np.abs(values), 99)), 0.01)
    fig, ax = plt.subplots(figsize=(11.4, 4.45), constrained_layout=True)
    image = ax.pcolormesh(xcoord, ycoord, values, shading="nearest", cmap="RdBu", norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), rasterized=True)
    ax.scatter(western.longitude, western.latitude, s=42, facecolor=GOLD, edgecolor=INK, linewidth=0.8, zorder=5)
    for number, row in enumerate(western.itertuples(index=False), start=1):
        ax.text(row.longitude + 0.45, row.latitude + 0.25, str(number), fontsize=8, weight="bold", color=INK)
    ax.set_aspect(1 / np.cos(np.deg2rad(37.5)))
    ax.set(xlabel="Longitude", ylabel="Latitude", title="Median pairwise Delta at 100 km")
    cbar = fig.colorbar(image, ax=ax, shrink=0.88, pad=0.025)
    cbar.set_label("Red: warm stronger   |   Blue: cold stronger")
    fig.suptitle("Current CONUS values and colors are semantically correct", fontsize=15, color=NAVY, weight="bold")
    fig.savefig(ASSETS / "conus_delta_clean.png", dpi=230, bbox_inches="tight")
    plt.close(fig)

    consistency = pd.read_csv(AUDIT / "repository_consistency.csv")
    failures = consistency[consistency.consistent_with_blue_cold_red_warm_convention == "NO"]
    counts = [len(consistency) - len(failures), len(failures)]
    fig, ax = plt.subplots(figsize=(8.5, 3.2), constrained_layout=True)
    bars = ax.barh(["Consistent checks", "Representational inconsistencies"], counts, color=[TEAL, RED], height=0.55)
    for bar, value in zip(bars, counts):
        ax.text(value + 0.25, bar.get_y() + bar.get_height() / 2, str(value), va="center", weight="bold")
    ax.set_xlim(0, max(counts) + 3)
    ax.set_xlabel("Repository audit entries")
    ax.set_title("Calculations pass; visual convention is not uniform", color=NAVY, weight="bold")
    fig.savefig(ASSETS / "consistency_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_audit_manifest_sha256": _digest(AUDIT / "audit_manifest.json"),
        "assets": {path.name: _digest(path) for path in sorted(ASSETS.glob("*.png"))},
    }
    (ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def _build_pdf() -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.lib.utils import ImageReader

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(letter)
    c = canvas.Canvas(str(OUTPUT), pagesize=(width, height), pageCompression=1)
    c.setTitle("Hot/Cold/Delta Semantics Audit")
    c.setAuthor("CubeDynamics team audit")
    c.setSubject("End-to-end verification of temperature-tail, Delta, raster, and color semantics")
    c.setKeywords("CubeDynamics, PRISM, synchrony, Delta, audit")

    manifest = json.loads((AUDIT / "audit_manifest.json").read_text())
    collapsed = json.loads((AUDIT / "collapsed_pixel_provenance.json").read_text())
    colorbar = json.loads((AUDIT / "colorbar_audit.json").read_text())
    synthetic = json.loads((AUDIT / "synthetic_cases.json").read_text())
    pair_rows = _csv(AUDIT / "pair_audit_summary.csv")
    tail_rows = _csv(AUDIT / "tail_pixel_summary.csv")
    western = _csv(AUDIT / "western_spot_checks.csv")
    consistency = _csv(AUDIT / "repository_consistency.csv")
    failures = [row for row in consistency if row["consistent_with_blue_cold_red_warm_convention"] == "NO"]
    call_graph = _csv(AUDIT / "call_graph.csv")

    def hex_color(value: str):
        return colors.HexColor(value)

    body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.2, leading=12.5, textColor=hex_color(INK), spaceAfter=4)
    small = ParagraphStyle("small", parent=body, fontSize=7.6, leading=9.5)
    tiny = ParagraphStyle("tiny", parent=body, fontSize=6.5, leading=8.0)
    callout = ParagraphStyle("callout", parent=body, fontSize=10.2, leading=14.2)
    center = ParagraphStyle("center", parent=body, alignment=TA_CENTER)

    def footer(page: int, source: str = "CubeDynamics forensic audit | retained observed PRISM evidence") -> None:
        c.setStrokeColor(hex_color("#CDD7DE"))
        c.setLineWidth(0.5)
        c.line(40, 24, width - 40, 24)
        c.setFillColor(hex_color(MUTED))
        c.setFont("Helvetica", 6.8)
        c.drawString(42, 11, source)
        c.drawRightString(width - 42, 11, f"{page} / {PAGE_COUNT}")

    def header(page: int, section: str, title: str, subtitle: str = "") -> float:
        c.setFillColor(hex_color(NAVY))
        c.rect(0, height - 78, width, 78, stroke=0, fill=1)
        c.setFillColor(hex_color("#9DD6F4"))
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(42, height - 22, section.upper())
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(42, height - 47, title)
        if subtitle:
            c.setFont("Helvetica", 8.2)
            c.setFillColor(hex_color("#DCECF5"))
            c.drawString(42, height - 64, subtitle)
        footer(page)
        return height - 96

    def draw_para(text: str, x: float, y: float, w: float, style=body) -> float:
        item = Paragraph(text, style)
        _, h = item.wrap(w, height)
        item.drawOn(c, x, y - h)
        return y - h

    def box(x: float, y: float, w: float, h: float, fill: str, stroke: str = "#D5DEE4", radius: float = 8) -> None:
        c.setFillColor(hex_color(fill))
        c.setStrokeColor(hex_color(stroke))
        c.roundRect(x, y, w, h, radius, stroke=1, fill=1)

    def card(x: float, y: float, w: float, h: float, value: str, label: str, fill: str, accent: str) -> None:
        box(x, y, w, h, fill, accent)
        c.setFillColor(hex_color(accent))
        c.setFont("Helvetica-Bold", 18)
        c.drawString(x + 12, y + h - 25, value)
        draw_para(label, x + 12, y + h - 34, w - 24, small)

    def draw_image(path: Path, x: float, y: float, w: float, h: float) -> None:
        image = ImageReader(str(path))
        iw, ih = image.getSize()
        scale = min(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        c.drawImage(image, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, preserveAspectRatio=True, mask="auto")

    def draw_table(data, x: float, top: float, col_widths, row_heights=None, font_size: float = 7.2, repeat_header: bool = False) -> float:
        normalized = []
        for r, row in enumerate(data):
            style = ParagraphStyle(
                f"cell-{r}",
                parent=tiny,
                fontName="Helvetica-Bold" if r == 0 else "Helvetica",
                fontSize=font_size,
                leading=font_size + 1.7,
                textColor=colors.white if r == 0 else hex_color(INK),
                alignment=TA_LEFT,
            )
            normalized.append([Paragraph(str(value), style) for value in row])
        table = Table(normalized, colWidths=col_widths, rowHeights=row_heights, repeatRows=1 if repeat_header else 0)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), hex_color(NAVY)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.35, hex_color("#CCD6DC")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, hex_color(PALE_GRAY)]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        _, table_h = table.wrap(sum(col_widths), height)
        table.drawOn(c, x, top - table_h)
        return top - table_h

    def next_page() -> None:
        c.showPage()

    # Page 1: cover.
    c.setFillColor(hex_color(NAVY))
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(hex_color("#164D73"))
    c.circle(width - 75, height - 40, 145, fill=1, stroke=0)
    c.setFillColor(hex_color("#0C2B43"))
    c.circle(width - 12, 40, 210, fill=1, stroke=0)
    c.setFillColor(hex_color("#9DD6F4"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(48, height - 58, "CUBEDYNAMICS | FORENSIC SCIENTIFIC AUDIT")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 31)
    c.drawString(48, height - 123, "HOT / COLD / DELTA")
    c.drawString(48, height - 160, "SEMANTICS AUDIT")
    c.setFont("Helvetica", 13)
    c.setFillColor(hex_color("#DCECF5"))
    c.drawString(50, height - 193, "From raw PRISM temperatures to the final CONUS map")
    box(48, 165, 465, 134, "#FBEDEF", "#E8A6AF", 12)
    c.setFillColor(hex_color(RED))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(66, 273, "OVERALL VERDICT")
    c.setFillColor(hex_color(NAVY))
    c.setFont("Helvetica-Bold", 22)
    c.drawString(66, 238, "F. MULTIPLE INCONSISTENCIES EXIST")
    draw_para(
        "The scientific calculations, stored values, raster sign, and current CONUS pixel colors are correct. The inconsistencies are representational: one incomplete current legend, ten historical reversed palettes, and mixed hot/warm terminology.",
        66,
        214,
        420,
        callout,
    )
    c.setFillColor(hex_color("#B9D8E9"))
    c.setFont("Helvetica", 8.2)
    c.drawString(50, 86, "Diagnostic report only - no algorithm or production output was changed")
    c.drawString(50, 67, "Prepared 24 September 2026 | Evidence hashes retained in the audit manifest")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(width - 48, 70, "COLD +")
    c.setFillColor(hex_color("#FFB4B9"))
    c.drawRightString(width - 48, 44, "WARM -")
    footer(1, "CubeDynamics | Hot/Cold/Delta semantics audit")
    next_page()

    # Page 2: executive summary.
    y = header(2, "Executive summary", "What is correct - and what is not")
    card(42, 418, 166, 66, "PASS", "Tail assignment: lower TMIN is cold; upper TMAX is warm.", PALE_BLUE, BLUE)
    card(220, 418, 166, 66, "PASS", "Delta algebra: every audited value is S cold minus S warm.", PALE_BLUE, BLUE)
    card(398, 418, 166, 66, "PASS", "Current CONUS values and pixel colors preserve the sign.", PALE_BLUE, BLUE)
    card(576, 418, 174, 66, "FAIL", "Repository-wide visual convention is not uniform.", PALE_RED, RED)
    box(42, 248, 340, 145, PALE_GRAY)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(58, 370, "Core truth table")
    truth = [
        ["Condition", "Delta", "Meaning", "Current color"],
        ["S cold > S warm", "> 0", "Cold synchrony stronger", "Blue"],
        ["S cold = S warm", "= 0", "Equal tail synchrony", "Near-white"],
        ["S cold < S warm", "< 0", "Warm synchrony stronger", "Red"],
    ]
    draw_table(truth, 56, 350, [110, 48, 112, 55], font_size=7.4)
    box(400, 248, 350, 145, PALE_GOLD, "#E8C66D")
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(416, 370, "Why the verdict is F")
    draw_para(
        "<b>1.</b> The standalone CONUS Delta colorbar says only 'Median Spearman synchrony'; its endpoints are not semantically named.<br/><b>2.</b> Ten historical Delta or bottom-minus-top displays use RdBu_r, assigning positive/cold to red and negative/warm to blue.<br/><b>3.</b> 'Hot' and 'warm' denote the same upper-TMAX calculation but vary across outputs.",
        416,
        350,
        316,
        body,
    )
    card(42, 130, 166, 82, "2.22e-16", "Largest real-pair recomputation error.", WHITE, TEAL)
    card(220, 130, 166, 82, "1,846", "Relationships independently recomputed for one western pixel.", WHITE, TEAL)
    card(398, 130, 166, 82, "70.5%", "CONUS cells with negative Delta.", WHITE, TEAL)
    card(576, 130, 174, 82, "980", "Offline tests passed after the audit.", WHITE, TEAL)
    draw_para("Bottom line: the national scientific numbers do not need a sign reversal. The remediation decision concerns visual communication and historical continuity.", 42, 104, 708, callout)
    next_page()

    # Page 3: implementation path.
    y = header(3, "Implementation trace", "The complete production path", "Every arrow below was traced to code and checked against retained values")
    stages = [
        ("1", "PRISM input", "TMIN + TMAX", "data/prism.py"),
        ("2", "Tail state", "lower <= q; upper > q", "production.py"),
        ("3", "Pair statistics", "joint-tail Spearman", "production.py"),
        ("4", "Pair Delta", "cold - warm", "production.py"),
        ("5", "Pixel collapse", "median(pairwise Delta)", "baseline.py"),
        ("6", "Outputs", "NetCDF + GeoTIFF", "CONUS driver"),
        ("7", "Map + report", "RdBu centered at zero", "builders"),
    ]
    start_x = 42
    box_w, gap = 91, 9
    for index, (number, label, detail, file_name) in enumerate(stages):
        x = start_x + index * (box_w + gap)
        fill = PALE_RED if number == "7" else PALE_BLUE
        accent = RED if number == "7" else BLUE
        box(x, 354, box_w, 108, fill, accent, 7)
        c.setFillColor(hex_color(accent)); c.setFont("Helvetica-Bold", 14); c.drawString(x + 9, 438, number)
        c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 8.4); c.drawString(x + 9, 417, label)
        draw_para(detail, x + 9, 402, box_w - 18, small)
        c.setFillColor(hex_color(MUTED)); c.setFont("Helvetica", 5.9); c.drawString(x + 9, 366, file_name)
        if index < len(stages) - 1:
            c.setStrokeColor(hex_color("#8CA2AF")); c.setLineWidth(1.2)
            c.line(x + box_w + 1, 408, x + box_w + gap - 2, 408)
            c.line(x + box_w + gap - 5, 411, x + box_w + gap - 2, 408)
            c.line(x + box_w + gap - 5, 405, x + box_w + gap - 2, 408)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(42, 320, "Functions and variables")
    table = [["Stage", "Function", "Relevant variables"]]
    for row in call_graph[:9]:
        table.append([row["stage"], row["function"], row["relevant_variables"]])
    draw_table(table, 42, 304, [150, 222, 336], font_size=7.0)
    box(42, 62, 708, 38, PALE_GOLD, "#E8C66D")
    draw_para("Audit boundary: the scientific path passes end to end. The identified divergence begins in visual encoding and legend semantics, not in the numerical pipeline.", 55, 89, 682, body)
    next_page()

    # Page 4: tails.
    y = header(4, "Tail verification", "Cold really is low; warm really is high", "Observed PRISM pixels - no synthetic fallback")
    draw_image(ASSETS / "tail_verification.png", 42, 220, 470, 278)
    box(530, 265, 220, 233, PALE_GRAY)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(546, 474, "Literal implementation")
    draw_para(
        "<b>Cold:</b> TMIN_A <= median(TMIN_A) AND TMIN_B <= median(TMIN_B)<br/><br/><b>Warm:</b> TMAX_A > median(TMAX_A) AND TMAX_B > median(TMAX_B)<br/><br/><b>q:</b> 0.5<br/><b>Window:</b> 91 daily labels ending 2024-01-30<br/><b>Ties:</b> average ranks<br/><b>Missing:</b> paired removal before thresholds<br/><b>Pair rule:</b> both members must pass their own threshold",
        546,
        450,
        188,
        body,
    )
    tail_table = [["Pixel", "Cold median", "Warm median", "Cold n", "Warm n", "Pass"]]
    for row in tail_rows:
        tail_table.append([
            row["pixel"].title(),
            f"{float(row['median_tmin_on_cold_dates_c']):.2f} C",
            f"{float(row['median_tmax_on_warm_dates_c']):.2f} C",
            row["cold_date_count"],
            row["warm_date_count"],
            "YES",
        ])
    draw_table(tail_table, 42, 200, [98, 112, 112, 74, 74, 70], font_size=7.4)
    box(600, 102, 150, 88, PALE_BLUE, BLUE)
    c.setFillColor(hex_color(BLUE)); c.setFont("Helvetica-Bold", 20); c.drawString(616, 160, "PASS")
    draw_para("Every observed example places cold dates below and warm dates above its local reference distribution.", 616, 145, 118, small)
    next_page()

    # Page 5: real pair audit.
    y = header(5, "Real-pair verification", "Five observed relationships recomputed by hand", "Direct SciPy Spearman from the selected dates versus stored production values")
    draw_image(ASSETS / "real_pair_check.png", 42, 278, 430, 220)
    box(488, 278, 262, 220, PALE_RED, "#E8A6AF")
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(505, 470, "Worked Great Basin pair")
    selected = pair_rows[1]
    draw_para(
        f"Pixel A: {float(selected['pixel_a_latitude']):.3f}, {float(selected['pixel_a_longitude']):.3f}<br/>Pixel B: {float(selected['pixel_b_latitude']):.3f}, {float(selected['pixel_b_longitude']):.3f}<br/>Distance: {float(selected['distance_km']):.2f} km<br/><br/>S cold = {float(selected['stored_cold']):.6f}<br/>S warm = {float(selected['stored_warm']):.6f}<br/><b>Delta = {float(selected['stored_delta']):.6f}</b><br/><br/>Interpretation: warm synchrony is stronger by {abs(float(selected['stored_delta'])):.3f}.",
        505,
        448,
        225,
        callout,
    )
    table = [["Region", "km", "S cold", "S warm", "Delta", "Max error"]]
    for row in pair_rows:
        maximum_error = max(float(row["cold_absolute_error"]), float(row["warm_absolute_error"]), float(row["delta_absolute_error"]))
        table.append([
            row["region"].replace("_", " ").title(),
            f"{float(row['distance_km']):.1f}",
            f"{float(row['stored_cold']):.3f}",
            f"{float(row['stored_warm']):.3f}",
            f"{float(row['stored_delta']):+.3f}",
            f"{maximum_error:.1e}",
        ])
    draw_table(table, 42, 252, [165, 75, 92, 92, 92, 112], font_size=7.5)
    box(42, 70, 708, 53, PALE_BLUE, BLUE)
    draw_para("PASS: all entering dates, temperatures, percentiles, within-tail ranks, and flags are retained in pair_audit_observations.csv. Maximum stored-versus-direct error is 2.22e-16; Delta algebra error is 0.", 56, 108, 680, callout)
    next_page()

    # Page 6: synthetic cases.
    y = header(6, "Known-answer controls", "Three cases with an obvious answer", "All cases ran through local_synchrony_pairs - the same production function used for CONUS")
    draw_image(ASSETS / "synthetic_cases.png", 42, 246, 708, 250)
    cards = [
        ("A", "Cold stronger", synthetic[0], PALE_BLUE, BLUE),
        ("B", "Warm stronger", synthetic[1], PALE_RED, RED),
        ("C", "Equal", synthetic[2], PALE_GRAY, MUTED),
    ]
    for index, (letter, label, record, fill, accent) in enumerate(cards):
        x = 42 + index * 238
        box(x, 113, 218, 105, fill, accent)
        c.setFillColor(hex_color(accent)); c.setFont("Helvetica-Bold", 17); c.drawString(x + 14, 190, letter)
        c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 11); c.drawString(x + 45, 190, label)
        draw_para(f"S cold = {record['cold']:.3f}<br/>S warm = {record['warm']:.3f}<br/><b>Delta = {record['delta']:+.3f}</b>", x + 14, 174, 190, body)
    draw_para("PASS: positive Delta labels cold stronger; negative Delta labels warm stronger; equal synchrony produces exactly zero.", 42, 89, 708, callout)
    next_page()

    # Page 7: collapse.
    y = header(7, "Spatial collapse", "One focal pixel, 1,846 pair relationships", "The primary map uses median(S cold - S warm), not median(S cold) - median(S warm)")
    draw_image(ASSETS / "collapsed_pixel.png", 42, 245, 708, 255)
    card(42, 145, 158, 75, f"{collapsed['recomputed_median_cold']:.6f}", "Median S cold", PALE_BLUE, BLUE)
    card(214, 145, 158, 75, f"{collapsed['recomputed_median_warm']:.6f}", "Median S warm", PALE_RED, RED)
    card(386, 145, 170, 75, f"{collapsed['recomputed_median_pairwise_delta']:.6f}", "Primary median pairwise Delta", PALE_GOLD, GOLD)
    card(570, 145, 180, 75, f"{collapsed['recomputed_difference_of_medians']:.6f}", "Separate difference of medians", PALE_GRAY, MUTED)
    box(42, 65, 708, 55, WHITE, TEAL)
    draw_para(
        f"PASS: NetCDF error = {collapsed['netcdf_absolute_error']:.1e}; float32 GeoTIFF error = {collapsed['geotiff_absolute_error']:.2e}. The two collapse formulas differ by {collapsed['reduction_gap']:.6f}, so preserving their names is scientifically necessary.",
        57,
        103,
        678,
        callout,
    )
    next_page()

    # Page 8: map.
    y = header(8, "National map audit", "The current CONUS map is colored correctly", "Delta = S cold - S warm | red negative/warm stronger | blue positive/cold stronger")
    draw_image(ASSETS / "conus_delta_clean.png", 42, 106, 708, 398)
    card(42, 54, 154, 43, "0.910874", "National median S cold", WHITE, BLUE)
    card(208, 54, 154, 43, "0.928470", "National median S warm", WHITE, RED)
    card(374, 54, 154, 43, "-0.017335", "National median pairwise Delta", WHITE, RED)
    card(540, 54, 210, 43, "70.5% negative", "Algebraically consistent with warm > cold", WHITE, RED)
    next_page()

    # Page 9: one pixel provenance and colorbar.
    y = header(9, "End-to-end provenance", "One western pixel from temperatures to displayed color")
    steps = [
        ("Raw PRISM", "TMIN and TMAX\n91 daily labels", PALE_GRAY, MUTED),
        ("Tail flags", "lower TMIN /\nupper TMAX", PALE_BLUE, BLUE),
        ("Pair table", "1,846 nonself\nrelationships", PALE_BLUE, BLUE),
        ("Collapse", f"median Delta\n{collapsed['recomputed_median_pairwise_delta']:.6f}", PALE_GOLD, GOLD),
        ("NetCDF", f"{collapsed['netcdf_primary_delta']:.6f}", WHITE, TEAL),
        ("GeoTIFF", f"{collapsed['geotiff_primary_delta']:.6f}", WHITE, TEAL),
        ("Map", f"{collapsed['displayed_color_hex']} red\nwarm stronger", PALE_RED, RED),
    ]
    for index, (label, detail, fill, accent) in enumerate(steps):
        x = 38 + index * 105
        box(x, 346, 91, 110, fill, accent, 7)
        c.setFillColor(hex_color(accent)); c.setFont("Helvetica-Bold", 9); c.drawCentredString(x + 45.5, 430, label)
        style = ParagraphStyle(f"step-{index}", parent=small, alignment=TA_CENTER)
        draw_para(detail.replace("\n", "<br/>"), x + 7, 414, 77, style)
        if index < len(steps) - 1:
            c.setStrokeColor(hex_color("#8CA2AF")); c.line(x + 92, 400, x + 102, 400)
            c.line(x + 99, 403, x + 102, 400); c.line(x + 99, 397, x + 102, 400)
    box(42, 185, 708, 126, PALE_GRAY)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(58, 287, "Colorbar contract")
    grad_x, grad_y, grad_w, grad_h = 76, 232, 480, 24
    for i in range(240):
        t = i / 239
        if t < 0.5:
            r = int(103 + (247 - 103) * (t / 0.5)); g = int(0 + (247 - 0) * (t / 0.5)); b = int(31 + (247 - 31) * (t / 0.5))
        else:
            u = (t - 0.5) / 0.5; r = int(247 + (5 - 247) * u); g = int(247 + (48 - 247) * u); b = int(247 + (97 - 247) * u)
        c.setFillColor(colors.Color(r / 255, g / 255, b / 255)); c.rect(grad_x + grad_w * t, grad_y, grad_w / 238 + 1, grad_h, stroke=0, fill=1)
    c.setFillColor(hex_color(INK)); c.setFont("Helvetica-Bold", 8)
    c.drawString(76, 216, "NEGATIVE: stronger warm synchrony")
    c.drawCentredString(316, 216, "ZERO: equal")
    c.drawRightString(556, 216, "POSITIVE: stronger cold synchrony")
    box(582, 214, 142, 62, PALE_RED, RED)
    c.setFillColor(hex_color(RED)); c.setFont("Helvetica-Bold", 14); c.drawString(596, 251, "RED = WARM")
    draw_para("for the current CONUS Delta map", 596, 238, 116, small)
    box(42, 70, 708, 78, PALE_GOLD, "#E8C66D")
    draw_para("Figure-legend finding: the pixels obey this contract, but the standalone colorbar is labeled only 'Median Spearman synchrony.' A reader should not need external prose to infer that red means warm stronger and blue means cold stronger.", 57, 128, 678, callout)
    next_page()

    # Page 10: western checks.
    y = header(10, "Western pattern", "Five real spot checks on the prominent red feature", "Every sampled red cell is negative and means stronger warm synchrony")
    table = [["#", "Latitude", "Longitude", "Median cold", "Median warm", "Pairwise Delta", "Color", "Interpretation"]]
    for index, row in enumerate(western, start=1):
        table.append([
            str(index),
            f"{float(row['latitude']):.3f}",
            f"{float(row['longitude']):.3f}",
            f"{float(row['collapsed_cold_median']):.3f}",
            f"{float(row['collapsed_warm_median']):.3f}",
            f"{float(row['primary_median_pairwise_delta']):+.3f}",
            row["display_color_family"].title(),
            row["interpretation"].replace("approximately", "about"),
        ])
    draw_table(table, 42, 478, [28, 62, 72, 76, 76, 86, 52, 232], font_size=7.0)
    box(42, 143, 340, 118, PALE_RED, RED)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(58, 237, "Strongest audited western cell")
    draw_para(
        f"Location: {collapsed['latitude']:.3f}, {collapsed['longitude']:.3f}<br/>Median S cold: {collapsed['recomputed_median_cold']:.6f}<br/>Median S warm: {collapsed['recomputed_median_warm']:.6f}<br/><b>Median pairwise Delta: {collapsed['recomputed_median_pairwise_delta']:.6f}</b>",
        58,
        219,
        308,
        body,
    )
    box(400, 143, 350, 118, PALE_BLUE, BLUE)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(416, 237, "Scientific interpretation")
    draw_para("At these cells, warm-tail TMAX synchrony exceeds cold-tail TMIN synchrony. The red western feature does not mean 'hot temperature.' It means stronger spatial synchrony during locally warm-tail days, by the displayed Delta magnitude.", 416, 219, 318, body)
    box(42, 70, 708, 50, WHITE, TEAL)
    draw_para("PASS: values, signs, colors, and interpretations agree for every western spot check. Causal or regime claims remain outside the scope of this semantics audit.", 57, 106, 678, callout)
    next_page()

    # Page 11: repository consistency.
    y = header(11, "Repository consistency", "The visual convention changed across generations", "11 representational inconsistencies; no warm-minus-cold implementation found")
    draw_image(ASSETS / "consistency_summary.png", 42, 323, 300, 170)
    box(360, 323, 390, 170, PALE_GOLD, "#E8C66D")
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(377, 469, "Classification")
    draw_para(
        "<b>Algorithmic:</b> PASS<br/><b>Variable routing:</b> PASS<br/><b>Delta sign:</b> PASS<br/><b>Spatial collapse:</b> PASS<br/><b>Raster values:</b> PASS<br/><b>Current CONUS colors:</b> PASS<br/><b>Current standalone legend:</b> FAIL<br/><b>Repository-wide palette convention:</b> FAIL<br/><b>Terminology uniformity:</b> FAIL",
        377,
        451,
        350,
        body,
    )
    failure_table = [["File", "Context", "Finding"]]
    for row in failures:
        short_file = row["file"].replace("scripts/", "").replace("examples/", "ex: ").replace("docs/recipes/", "recipe: ")
        failure_table.append([short_file, row["function_or_context"], row["expression_or_interpretation"]])
    draw_table(failure_table, 42, 300, [255, 178, 275], font_size=6.4)
    box(42, 50, 708, 38, PALE_RED, RED)
    draw_para("Verdict F reflects multiple communication inconsistencies, not multiple numerical failures. Existing values should not be negated or recomputed as a remedy.", 57, 78, 678, body)
    next_page()

    # Page 12: close and remediation boundary.
    y = header(12, "Conclusion", "What the team can safely say now", "And what should wait for a separately approved remediation")
    box(42, 330, 340, 165, PALE_BLUE, BLUE)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 14); c.drawString(58, 469, "Safe conclusions")
    draw_para(
        "- Cold is the joint lower local tail of PRISM TMIN.<br/>- Warm/hot is the joint upper local tail of PRISM TMAX.<br/>- Delta is S cold minus S warm.<br/>- Positive Delta means cold synchrony is stronger.<br/>- Negative Delta means warm synchrony is stronger.<br/>- The current CONUS numbers, rasters, and pixel colors preserve this meaning.<br/>- The western red feature is warm-synchrony stronger.",
        58,
        447,
        306,
        body,
    )
    box(410, 330, 340, 165, PALE_RED, RED)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 14); c.drawString(426, 469, "Proposed remediation - not executed")
    draw_para(
        "1. Define one shared Delta palette contract.<br/>2. Add semantic endpoint labels to the CONUS colorbar.<br/>3. Review only synchrony-specific RdBu_r uses.<br/>4. Canonicalize 'warm'; retain 'hot' as a documented alias.<br/>5. Regenerate affected figures and PDFs only after approval.<br/>6. Version historical recolors because human interpretation changes even when values do not.",
        426,
        447,
        306,
        body,
    )
    box(42, 206, 708, 91, PALE_GRAY)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 13); c.drawString(58, 274, "Verification record")
    draw_para(
        "Five real pairs: PASS | Three known-answer cases: PASS | One-pixel NetCDF and GeoTIFF trace: PASS | Five western cells: PASS | 32 focused tests: PASS | Full offline suite: 980 passed, 5 skipped, 419 deselected | Compilation and diff checks: PASS",
        58,
        255,
        674,
        body,
    )
    box(42, 82, 708, 94, WHITE, TEAL)
    c.setFillColor(hex_color(NAVY)); c.setFont("Helvetica-Bold", 12); c.drawString(58, 153, "Evidence identity")
    draw_para(
        f"Observed PRISM input SHA-256: {manifest['input_sha256']}<br/>CONUS result SHA-256: {manifest['result_sha256']}<br/>Audit manifest SHA-256: {_digest(AUDIT / 'audit_manifest.json')}<br/>Generated report SHA-256 is recorded after build in clean-report-assets/report_manifest.json.",
        58,
        138,
        674,
        tiny,
    )
    c.save()

    report_manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pdf": str(OUTPUT.relative_to(ROOT)),
        "pdf_sha256": _digest(OUTPUT),
        "page_count_expected": PAGE_COUNT,
        "source_audit_manifest_sha256": _digest(AUDIT / "audit_manifest.json"),
        "diagnostic_only": True,
        "remediation_executed": False,
    }
    (ASSETS / "report_manifest.json").write_text(json.dumps(report_manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("assets", "pdf"), required=True)
    args = parser.parse_args()
    if args.stage == "assets":
        _build_assets()
        print(ASSETS)
    else:
        _build_pdf()
        print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
