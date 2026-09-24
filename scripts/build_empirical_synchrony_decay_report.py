#!/usr/bin/env python3
"""Build the empirical synchrony-decay pilot walkthrough PDF."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PILImage
try:
    import reportlab  # noqa: F401
except ModuleNotFoundError:
    import sys
    sys.path.append(
        "/Users/tuff/.cache/codex-runtimes/codex-primary-runtime/dependencies/"
        "python/lib/python3.12/site-packages"
    )
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts" / "empirical-synchrony-decay"
FIGURES = BASE / "figures"
ASSETS = BASE / "report_assets"
OLD = ROOT / "artifacts" / "empirical-synchrony-range"
OLD_ASSETS = OLD / "report_assets"
OLD_FIGURES = OLD / "figures"
OUTPUT = ROOT / "output" / "pdf" / "empirical_synchrony_decay_pilot_walkthrough.pdf"
PAGE = landscape(letter)

NAVY = "#123F70"
BLUE = "#2878B5"
RED = "#B63A3A"
GOLD = "#F0B43C"
GREEN = "#3A8D6D"
PURPLE = "#6B4C9A"
INK = "#17212B"
MUTED = "#586775"
LIGHT = "#EDF3F7"


def _save(fig: plt.Figure, name: str) -> Path:
    ASSETS.mkdir(parents=True, exist_ok=True)
    path = ASSETS / name
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _assets() -> dict[str, Path]:
    assets: dict[str, Path] = {}
    x = np.linspace(0, 500, 251)
    curve = 0.22 + 0.68 * np.exp(-x / 135) + 0.035 * np.sin(x / 45)
    background = 0.22
    local = curve[0]
    excess = (curve - background) / (local - background)

    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
    ax.plot(x, curve, color=BLUE, lw=3)
    ax.axhline(background, color=GOLD, lw=2, label="Distant background")
    ax.axvline(500, color=INK, ls="--", label="Discovery boundary")
    ax.annotate("The curve can remain structured\nwithout a sharp endpoint", (360, curve[np.searchsorted(x, 360)]), (235, .62), arrowprops=dict(arrowstyle="->", color=PURPLE), color=PURPLE, weight="bold")
    ax.set(xlabel="Physical distance (km)", ylabel="Synchrony", title="Conceptual shift: characterize decay instead of forcing a finite horizon")
    ax.legend(frameon=False); ax.grid(alpha=.15)
    assets["shift"] = _save(fig, "conceptual_shift.png")

    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
    ax.plot(x, curve, color=BLUE, lw=3)
    ax.scatter(x[x <= 45], curve[x <= 45], color=GREEN, s=25, zorder=3)
    ax.axhline(local, color=GREEN, ls=":", label="Robust near-field level S_local")
    ax.axhline(background, color=GOLD, label="Empirical background S_bg")
    ax.annotate("No self-pair", (0, local), (75, .93), arrowprops=dict(arrowstyle="->", color=INK), weight="bold")
    ax.set(xlabel="Physical distance (km)", ylabel="Synchrony", title="Conceptual: local excess is S_local - S_bg")
    ax.legend(frameon=False); ax.grid(alpha=.15)
    assets["local_background"] = _save(fig, "local_background.png")

    for fraction, target in ((25, .75), (50, .50), (75, .25)):
        distance = float(np.interp(target, excess[::-1], x[::-1]))
        fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
        ax.plot(x, excess, color=BLUE, lw=3, label="Normalized excess")
        ax.axhline(target, color=PURPLE, ls="--", label=f"{100 - fraction}% remains")
        ax.axvline(distance, color=PURPLE, lw=2)
        ax.annotate(f"d{fraction} = {distance:.0f} km", (distance, target), (distance + 55, min(.95, target + .18)), arrowprops=dict(arrowstyle="->", color=PURPLE), color=PURPLE, weight="bold")
        ax.set(xlabel="Physical distance (km)", ylabel="Normalized excess", ylim=(-.04, 1.05), title=f"Conceptual: d{fraction} marks {fraction}% loss of local excess")
        ax.legend(frameon=False); ax.grid(alpha=.15)
        assets[f"d{fraction}"] = _save(fig, f"conceptual_d{fraction}.png")

    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
    near = x <= 100
    coefficient = np.polyfit(x[near], curve[near], 1)
    fit = np.polyval(coefficient, x[near])
    ax.plot(x, curve, color="#A8BDD0", lw=2, label="Empirical curve")
    ax.scatter(x[near][::8], curve[near][::8], color=BLUE, label="Near-field annular medians")
    ax.plot(x[near], fit, color=RED, lw=3, label=f"Robust initial slope ({100 * coefficient[0]:.2f} /100 km)")
    ax.axvspan(0, 100, color=GOLD, alpha=.12)
    ax.set(xlabel="Physical distance (km)", ylabel="Synchrony", title="Conceptual: beta measures the local gradient without estimating background")
    ax.legend(frameon=False); ax.grid(alpha=.15)
    assets["beta"] = _save(fig, "conceptual_beta.png")

    with (BASE / "representative_5_site_decay_metrics.csv").open(encoding="utf-8") as stream:
        representatives = list(csv.DictReader(stream))
    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.2), constrained_layout=True)
    labels = [row["label"].replace(" region", "") for row in representatives]
    for ax, field_cold, field_warm, title, ylabel in (
        (axes[0], "cold_d50_km", "warm_d50_km", "d50", "km"),
        (axes[1], "cold_effective_length_km", "warm_effective_length_km", "Effective length", "km"),
        (axes[2], "cold_beta_initial_per_100km", "warm_beta_initial_per_100km", "Initial slope", "change /100 km"),
    ):
        pos = np.arange(len(labels)); width = .36
        ax.bar(pos - width/2, [float(row[field_cold]) for row in representatives], width, color=BLUE, label="Cold")
        ax.bar(pos + width/2, [float(row[field_warm]) for row in representatives], width, color=RED, label="Warm")
        ax.set(xticks=pos, xticklabels=labels, title=title, ylabel=ylabel)
        ax.tick_params(axis="x", rotation=35); ax.grid(axis="y", alpha=.15)
    axes[0].legend(frameon=False)
    fig.suptitle("All five representative pixels yield empirical decay summaries", color=NAVY, weight="bold")
    assets["representatives"] = _save(fig, "representative_metrics.png")
    return assets


class Report:
    def __init__(self, output: Path):
        output.parent.mkdir(parents=True, exist_ok=True)
        self.canvas = canvas.Canvas(str(output), pagesize=PAGE)
        self.canvas.setTitle("Empirical synchrony decay - retained-pair pilot")
        self.canvas.setAuthor("CubeDynamics project")
        self.canvas.setSubject("Fractional decay, effective length, robust slopes, and scale-up gates")
        self.width, self.height = PAGE
        self.page_number = 0
        self.body_style = ParagraphStyle("body", fontName="Helvetica", fontSize=10.4, leading=14.2, textColor=colors.HexColor(INK), alignment=TA_LEFT)

    def _frame(self, title: str, kicker: str) -> None:
        self.page_number += 1
        c = self.canvas
        c.setFillColor(colors.HexColor(NAVY)); c.setFont("Helvetica-Bold", 21); c.drawString(38, self.height - 46, title)
        c.setFillColor(colors.HexColor(MUTED)); c.setFont("Helvetica", 8.7); c.drawString(39, self.height - 63, kicker.upper())
        c.setStrokeColor(colors.HexColor("#CCD7DF")); c.line(38, 34, self.width - 38, 34)
        c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor(MUTED)); c.drawString(38, 20, "CubeDynamics | empirical synchrony-decay pilot | retained real PRISM pairs")
        c.drawRightString(self.width - 38, 20, f"{self.page_number} / 30")

    def page(self, title: str, kicker: str, body: str, *, image: Path | None = None, table_data: list[list[str]] | None = None, image_height: float = 4.45 * inch) -> None:
        self._frame(title, kicker)
        paragraph = Paragraph(body, self.body_style)
        width = self.width - 80
        _, body_height = paragraph.wrap(width, 95)
        body_y = self.height - 82 - body_height
        paragraph.drawOn(self.canvas, 40, body_y)
        content_top = body_y - 12
        if table_data:
            table = Table(table_data, colWidths=[2.7 * inch, 4.4 * inch], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("LEADING", (0, 0), (-1, -1), 10.5),
                ("GRID", (0, 0), (-1, -1), .45, colors.HexColor("#CBD5DD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(LIGHT)]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            _, height = table.wrap(width, content_top - 55)
            table.drawOn(self.canvas, 40, content_top - height)
        elif image:
            self._image(image, 40, 48, width, min(image_height, content_top - 56))
        self.canvas.showPage()

    def _image(self, path: Path, x: float, y: float, width: float, height: float) -> None:
        with PILImage.open(path) as image:
            ratio = min(width / image.width, height / image.height)
            draw_width, draw_height = image.width * ratio, image.height * ratio
        self.canvas.drawImage(str(path), x + (width - draw_width)/2, y + (height - draw_height)/2, width=draw_width, height=draw_height, preserveAspectRatio=True, mask="auto")

    def save(self) -> None:
        if self.page_number != 30:
            raise RuntimeError(f"Expected 30 pages, created {self.page_number}")
        self.canvas.save()


def main() -> None:
    summary = json.loads((BASE / "summary.json").read_text(encoding="utf-8"))
    gates = json.loads((BASE / "metric_gates.json").read_text(encoding="utf-8"))
    questions = json.loads((BASE / "final_questions.json").read_text(encoding="utf-8"))
    assets = _assets()
    report = Report(OUTPUT)

    report.page("Experiment 1: where does synchrony end?", "1. Original question", "The earlier experiment asked whether cold and warm synchrony reached a stable distant background within 500 km. That finite-horizon question remains preserved as a valid negative result.", image=OLD_ASSETS / "why_adaptive.png")
    report.page("The fixed 100 km baseline remains unchanged", "2. Validated control", "The fixed-radius Colorado products retain the audited cold lower-tail TMIN, warm strict upper-tail TMAX, and pairwise Delta_S = S_cold - S_warm semantics. Experiment 2 changes none of these products.", image=OLD_ASSETS / "fixed_colorado_maps.png")
    report.page("Why we tested a finite R*", "3. Experiment 1 rationale", "A focal-specific horizon could in principle distinguish local structure from distant background. The discovery radius was observation support, never an estimate, and unresolved cases were kept missing.", image=OLD_ASSETS / "standalone_focal_discovery.png")
    report.page("The empirical distance curves are real", "4. Retained evidence", "Individual pair values, annular median and IQR, and cumulative median show reproducible spatial structure. The curve is not forced to be monotonic and is not fitted to a parametric kernel.", image=FIGURES / "diagnostic_colorado_mountains.png", image_height=4.35*inch)
    report.page("The hard-horizon criterion", "5. Experiment 1 rule", "R* required a persistent approach to an empirical nonzero background plus cumulative stability and later-shell agreement. Weakening the rule after seeing failures would invalidate the gate.", image=OLD_ASSETS / "standalone_range_criterion.png")
    report.page("Why the horizon often failed", "6. Boundary and long tails", "Real curves commonly continued changing or failed the later-shell safeguard. A discovery limit cannot be assigned as R*: doing so would turn censoring into a false finite estimate.", image=OLD_ASSETS / "standalone_mountain_0_0.png")
    report.page("Only 1 of 25 common Colorado ranges resolved", "7. Experiment 1 result", "Cold and warm each resolved at nine pilot sites, but both resolved together at only one. The common-radius requirement therefore removed 96% of pilot sites.", image=OLD_ASSETS / "status_summary.png")
    report.page("No site stabilized from 400 to 500 km", "8. Discovery sensitivity", "At the primary 20 km bin width, zero of 25 Colorado common ranges stabilized between 400 and 500 km. Five representative national pixels also yielded zero common R* values.", image=OLD_FIGURES / "representative_sensitivity.png")
    report.page("A negative horizon result is scientific information", "9. Interpretation", "The failed gate does not imply an absence of spatial decay. It shows that these curves do not generally support a sharp, finite endpoint within the observed 500 km domain.", table_data=[["Observed", "Meaning"], ["0 of 5 representative common R*", "No robust finite horizon at the national test pixels"], ["1 of 25 Colorado common R*", "Common adaptive cutoff is not map-ready"], ["96% censored or unresolved", "Do not fill with the discovery boundary"], ["0 of 25 discovery-stable", "More support changed the horizon inference"]])
    report.page("Experiment 2: characterize decay", "10. New question", "The same pair relationships can support characteristic curve properties even when they do not support a finite endpoint. Experiment 2 extracts d25/d50/d75, effective length L, and robust local slope beta.", image=assets["shift"])
    report.page("Near-field synchrony", "11. S_local", "S_local is a robust median of the first two well-supported physical annuli. The self-pair remains excluded, so the near-field level is observed from neighboring cells rather than assumed to equal one.", image=assets["local_background"])
    report.page("Distant empirical background", "12. S_bg", "The existing outer-annulus, smoothed-outer, and distant-pair backgrounds are retained. Background sensitivity is measured explicitly instead of choosing whichever definition maximizes coverage.", image=FIGURES / "diagnostic_great_plains.png", image_height=4.35*inch)
    report.page("Normalize local excess synchrony", "13. E(d)", "Normalized excess is [S(d) - S_bg] / [S_local - S_bg]. It is approximately one near the focal pixel and approaches zero near background. Curves with insufficient or nonpositive local excess retain explicit status flags.", image=FIGURES / "pedagogical_d50.png")
    report.page("d25: one quarter of excess has decayed", "14. Fractional distance", "d25 is the interpolated physical distance where 75% of local excess remains. A centered three-annulus median and persistent later agreement prevent a single noisy bin from defining the crossing.", image=assets["d25"])
    report.page("d50: half of local excess has decayed", "15. Primary fractional distance", "d50 is not zero synchrony and not disappearance. It is the distance where half of the locally elevated synchrony relative to the empirical background has been lost.", image=assets["d50"])
    report.page("d75: three quarters of excess has decayed", "16. Farther fractional distance", "d75 targets 25% remaining excess and is expected to censor more often. Any fraction not reached within discovery support stays unresolved rather than being assigned 500 km.", image=assets["d75"])
    report.page("Effective synchrony length L", "17. Integrated scale", "L is the positive area under normalized excess synchrony. It is the width of a height-one rectangle with equal area: a curve property in kilometers, not a hard cutoff, kernel bandwidth, or dispersal distance.", image=FIGURES / "pedagogical_effective_length.png")
    report.page("Initial decay slope beta", "18. Background-free scale", "Beta is a Theil-Sen median slope from supported annular medians in the first 100 km, expressed per 100 km. It tests local decay even when estimating a distant background is difficult.", image=assets["beta"])
    report.page("One real cold example", "19. Retained PRISM pairs", "The Colorado mountain cold curve has a visible local decline and a long broad tail. The figure overlays fractional distances, effective length, beta, and the preserved old R* status on actual pair relationships.", image=FIGURES / "diagnostic_colorado_mountains.png", image_height=4.35*inch)
    report.page("One real warm example", "20. Retained PRISM pairs", "The Great Plains warm curve illustrates why a decay characteristic can resolve even when a stable finite horizon does not. The curve remains empirical and non-monotonic.", image=FIGURES / "diagnostic_great_plains.png", image_height=4.35*inch)
    report.page("Cold and warm remain separate", "21. Paired contrasts", "All metrics are estimated independently for lower-tail TMIN and strict upper-tail TMAX. Cold-minus-warm d50, L, and beta are distinct from Delta_S and are never merged into a synthetic index.", image=FIGURES / "cold_warm_contrasts.png")
    report.page("Sensitivity to 200/300/400/500 km", "22. Discovery support", "d50 is far more identifiable than R*, but warm d50 is stable from 400 to 500 km at only 52% of Colorado sites. L stabilizes at only 12% of cold and 16% of warm sites. Beta is discovery-stable at all sites with support.", image=FIGURES / "discovery_stability.png")
    report.page("Sensitivity to 10/20/40 km bins", "23. Annular resolution", "Cold and warm d50 meet the bin-width gate at 80% and 88% of sites. Effective length meets it at 76% and 92%. Cold beta meets it at only 40%, preventing beta from passing overall.", image=FIGURES / "bin_width_sensitivity.png")
    report.page("Sensitivity to empirical background", "24. Background definition", "d50 and L meet their background-sensitivity tolerances at all 25 sites under the three retained definitions. Beta is exactly background-independent by construction.", image=FIGURES / "background_sensitivity.png")
    report.page("Which metrics resolve?", "25. Coverage", "At 500 km / 20 km, d50 resolves for cold and warm at all 25 Colorado sites and all five representative sites. L is calculable at all sites. Beta meets its fit-quality requirement at 96% of cold and 84% of warm sites.", image=FIGURES / "metric_coverage.png")
    report.page("Which metrics stabilize?", "26. Gate components", "Coverage is not the decision. d50 fails on warm discovery stability; L fails strongly on discovery-boundary dependence; beta fails on cold bin-width sensitivity.", table_data=[["Metric", "Cold", "Warm"], ["d50 discovery stable", "76%", "52%"], ["d50 bin stable", "80%", "88%"], ["L discovery stable", "12%", "16%"], ["Beta discovery stable", "100%", "100%"], ["Beta bin stable", "40%", "84%"]])
    report.page("What does 100 km represent?", "27. Fixed-radius interpretation", f"The median fraction of local excess lost by 100 km is {questions['12_median_fraction_excess_decay_by_100km']['cold']:.2f} for cold and {questions['12_median_fraction_excess_decay_by_100km']['warm']:.2f} for warm. The fixed radius samples meaningful local decay, not a universal half-decay or endpoint.", image=FIGURES / "fixed_100km_interpretation.png")
    report.page("Evidence for multiple spatial scales", "28. Near, middle, and far slopes", "Near-field decline is steeper than the far-field tail at 84% of cold sites and 56% of warm sites. This supports a fast local component plus a broad slower component, explaining why 100 km can be useful while R* remains unresolved.", image=FIGURES / "multiscale_slopes.png")
    report.page("Predeclared pilot decision gate", "29. PASS/HOLD", "A metric must pass coverage, representative-site, discovery, bin-width, and background criteria for both tails. None passes the complete gate; no statewide raster is authorized by this experiment.", table_data=[["Candidate", "Decision and limiting evidence"], ["d50", f"{gates['d50']['overall_decision']}: warm discovery stability 52% < 70%"], ["Effective length L", f"{gates['effective_length']['overall_decision']}: discovery stability 12% cold / 16% warm"], ["Initial beta", f"{gates['beta_initial']['overall_decision']}: cold bin stability 40% < 70%"], ["Full Colorado", "HOLD"], ["CONUS", "HOLD"]])
    report.page("Recommended next experiment", "30. Decision and next step", "The proposition is partly supported: measurable decay properties exist without a sharp horizon, but none is ready for mapping under the complete gate. Next, test warm d50 and cold beta on independent seasonal windows and evaluate a bin-width-robust local-gradient summary. Do not tune thresholds merely to obtain PASS. Reproduce with:<br/><br/><font name='Courier'>.venv/bin/python scripts/run_empirical_synchrony_decay_pilot.py</font>", table_data=[["Question", "Answer"], ["Does d50 resolve more often than R*?", "Yes: 25/25 per tail and 5/5 representatives versus 1/25 common R*"], ["Does L stabilize?", "Usually no; strongly discovery-boundary dependent"], ["Is beta stable?", "Discovery-stable and background-free, but cold is bin-sensitive"], ["Does 100 km remain useful?", "Yes as a local-scale control, not as a horizon"], ["Proceed to statewide or CONUS maps?", "No - HOLD all candidates"]])
    report.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
