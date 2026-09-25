#!/usr/bin/env python3
"""Build the 37-page four-round adaptive synchrony walkthrough."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/adaptive-synchrony-four-round"
FIGURES = ARTIFACTS / "figures"
OUTPUT = ROOT / "output/pdf/four_round_adaptive_synchrony_walkthrough.pdf"
PAGE = landscape(letter)
WIDTH, HEIGHT = PAGE

NAVY = colors.HexColor("#123F70")
BLUE = colors.HexColor("#2878B5")
RED = colors.HexColor("#B63A3A")
GOLD = colors.HexColor("#F0B43C")
GREEN = colors.HexColor("#3A8D6D")
PURPLE = colors.HexColor("#7451A6")
INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#66737F")
PALE = colors.HexColor("#EEF4F8")
HOLD = colors.HexColor("#FFF1E2")

BODY = ParagraphStyle(
    "body",
    fontName="Helvetica",
    fontSize=10.3,
    leading=14.0,
    textColor=INK,
    alignment=TA_LEFT,
    spaceAfter=5,
)
SMALL = ParagraphStyle(
    "small",
    parent=BODY,
    fontSize=8.3,
    leading=10.8,
    textColor=MUTED,
)


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _draw_header(c: canvas.Canvas, section: str, page_number: int) -> None:
    c.setFillColor(NAVY)
    c.rect(0, HEIGHT - 34, WIDTH, 34, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(28, HEIGHT - 22, section.upper())
    c.drawRightString(WIDTH - 28, HEIGHT - 22, f"FOUR-ROUND ADAPTIVE SYNCHRONY  |  {page_number}/37")


def _paragraph(c: canvas.Canvas, text: str, x: float, y: float, w: float, h: float, style=BODY) -> None:
    paragraph = Paragraph(text, style)
    _, required = paragraph.wrap(w, h)
    paragraph.drawOn(c, x, y + h - required)


def _image(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float) -> None:
    reader = ImageReader(str(path))
    iw, ih = reader.getSize()
    scale = min(w / iw, h / ih)
    draw_w, draw_h = iw * scale, ih * scale
    c.drawImage(reader, x + (w - draw_w) / 2, y + (h - draw_h) / 2, draw_w, draw_h, preserveAspectRatio=True, mask="auto")


def _status_banner(c: canvas.Canvas, text: str, *, color=HOLD) -> None:
    c.setFillColor(color)
    c.roundRect(38, 40, WIDTH - 76, 31, 8, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString(WIDTH / 2, 51, text)


def _circle_domain(c: canvas.Canvas, *, adaptive: bool, unresolved: bool = False) -> None:
    cx, cy = WIDTH * 0.63, HEIGHT * 0.45
    c.setStrokeColor(MUTED)
    c.setDash(5, 4)
    c.circle(cx, cy, 150, stroke=1, fill=0)
    c.setDash()
    c.setFillColor(PALE)
    c.circle(cx, cy, 150, stroke=0, fill=1)
    if adaptive:
        c.setFillColor(colors.Color(0.22, 0.55, 0.43, alpha=0.22))
        c.circle(cx, cy, 75, stroke=0, fill=1)
        c.setStrokeColor(GREEN)
        c.setLineWidth(3)
        c.circle(cx, cy, 75, stroke=1, fill=0)
    else:
        c.setStrokeColor(GOLD)
        c.setLineWidth(3)
        c.circle(cx, cy, 105, stroke=1, fill=0)
    c.setFillColor(NAVY)
    c.circle(cx, cy, 7, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(cx + 12, cy - 4, "focal pixel")
    c.setFont("Helvetica", 9)
    c.drawString(cx + 112, cy + 112, "1000 km observation domain")
    if unresolved:
        c.setFillColor(RED)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(cx, cy - 190, "R* unresolved - do not substitute 1000 km")


def _flow(c: canvas.Canvas, labels: list[str], active: int) -> None:
    x0, y = 120, HEIGHT * 0.39
    box_w, gap = 130, 42
    for index, label in enumerate(labels):
        x = x0 + index * (box_w + gap)
        c.setFillColor(GREEN if index == active else PALE)
        c.setStrokeColor(NAVY)
        c.roundRect(x, y, box_w, 72, 10, fill=1, stroke=1)
        c.setFillColor(colors.white if index == active else INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + box_w / 2, y + 40, label)
        if index < len(labels) - 1:
            c.setStrokeColor(MUTED)
            c.setLineWidth(2)
            c.line(x + box_w, y + 36, x + box_w + gap - 10, y + 36)
            c.line(x + box_w + gap - 18, y + 41, x + box_w + gap - 10, y + 36)
            c.line(x + box_w + gap - 18, y + 31, x + box_w + gap - 10, y + 36)


def _strength_scale(c: canvas.Canvas) -> None:
    c.setFillColor(PALE)
    c.roundRect(85, 170, 275, 210, 14, fill=1, stroke=0)
    c.roundRect(430, 170, 275, 210, 14, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(222, 340, "SYNCHRONY STRENGTH")
    c.setFillColor(GREEN)
    c.drawCentredString(567, 340, "SYNCHRONY SCALE")
    c.setFillColor(INK)
    c.setFont("Helvetica", 13)
    c.drawCentredString(222, 285, "How strongly does the focal")
    c.drawCentredString(222, 264, "pixel covary with neighbors?")
    c.drawCentredString(567, 285, "Where is the first reproducible")
    c.drawCentredString(567, 264, "local-to-regional transition?")
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(222, 215, "S(x, y, t)")
    c.drawCentredString(567, 215, "R*(x, y, t)")


def _temporal_stack(c: canvas.Canvas) -> None:
    x, y = 205, 155
    for index in range(5):
        c.setFillColor(colors.Color(0.18, 0.48, 0.68, alpha=0.14 + index * 0.08))
        c.setStrokeColor(NAVY)
        c.rect(x + index * 35, y + index * 28, 300, 150, fill=1, stroke=1)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + index * 35 + 8, y + index * 28 + 130, f"time window {index + 1}")
    c.setFont("Helvetica-Bold", 15)
    c.drawString(555, 320, "median_t R*(x,y,t)")
    c.drawString(555, 280, "IQR_t R*(x,y,t)")
    c.drawString(555, 240, "trend_t R*(x,y,t)")


def _page(
    c: canvas.Canvas,
    *,
    number: int,
    section: str,
    title: str,
    subtitle: str,
    bullets: list[str],
    image: Path | None = None,
    concept: str | None = None,
    banner: str | None = None,
) -> None:
    _draw_header(c, section, number)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(38, HEIGHT - 72, title)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10.5)
    c.drawString(39, HEIGHT - 91, subtitle)
    if image is not None:
        _image(c, image, 298, 96, WIDTH - 330, HEIGHT - 210)
        body_w = 235
    else:
        body_w = 285 if concept else WIDTH - 76
    body = "<br/>".join(f"<b>{index + 1}.</b> {item}" for index, item in enumerate(bullets))
    _paragraph(c, body, 42, 95, body_w, HEIGHT - 218)
    if concept == "fixed":
        _circle_domain(c, adaptive=False)
    elif concept == "adaptive":
        _circle_domain(c, adaptive=True)
    elif concept == "unresolved":
        _circle_domain(c, adaptive=True, unresolved=True)
    elif concept == "flow-discover":
        _flow(c, ["DISCOVER", "RECALCULATE", "COMPARE", "MAP SCALE"], 0)
    elif concept == "flow-recalculate":
        _flow(c, ["DISCOVER", "RECALCULATE", "COMPARE", "MAP SCALE"], 1)
    elif concept == "flow-compare":
        _flow(c, ["DISCOVER", "RECALCULATE", "COMPARE", "MAP SCALE"], 2)
    elif concept == "flow-map":
        _flow(c, ["DISCOVER", "RECALCULATE", "COMPARE", "MAP SCALE"], 3)
    elif concept == "strength-scale":
        _strength_scale(c)
    elif concept == "temporal":
        _temporal_stack(c)
    if banner:
        _status_banner(c, banner)
    c.showPage()


def build() -> Path:
    gate = json.loads((ARTIFACTS / "representative_gate.json").read_text(encoding="utf-8"))
    preflight = json.loads((ARTIFACTS / "preflight_estimate.json").read_text(encoding="utf-8"))
    performance = json.loads((ARTIFACTS / "performance.json").read_text(encoding="utf-8"))
    sampled = _load_rows(ARTIFACTS / "representative_sampled.csv")
    exhaustive = _load_rows(ARTIFACTS / "representative_exhaustive.csv")
    exact_resolved = sum(int(row["common_break_status_code"]) in (5, 6) for row in exhaustive)
    sampled_resolved = sum(int(row["common_break_status_code"]) in (5, 6) for row in sampled)
    pair_total = sum(int(item["exhaustive_nonself_pairs"]) for item in gate["performance"])
    fixed_mae = gate["sampling_validation"]["fixed_500km_delta_mae"]
    sampling_agreement = gate["sampling_validation"]["break_agreement_fraction"]
    peak_gb = performance["process_peak_rss_bytes"] / 1e9

    diag = FIGURES / "diagnostic_colorado_mountains.png"
    primary = FIGURES / "representative_primary_four_panel.png"
    secondary = FIGURES / "representative_scale_four_panel.png"
    sampling = FIGURES / "sampling_validation.png"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=PAGE, pageCompression=1)
    c.setTitle("Four-round adaptive synchrony experiment")
    c.setAuthor("CubeDynamics")
    c.setSubject("Bounded real-PRISM 1000 km empirical synchrony-scale gate")

    pages = [
        ("DISCOVERY", "1. Existing fixed-radius method", "The validated baseline stays intact.", ["Each focal pixel uses one imposed distance.", "Cold is lower-tail TMIN; warm is strict upper-tail TMAX.", "Primary Delta is the median of pairwise cold-minus-warm values."], None, "fixed", None),
        ("DISCOVERY", "2. Why one universal distance may be limiting", "A fixed domain can mix different geographic regimes.", ["A short local regime can be diluted by far-field relationships.", "A broad regime can be truncated by a small radius.", "The experiment tests variation; it does not assume adaptation is better."], None, "flow-discover", None),
        ("DISCOVERY", "3. One focal pixel", "Start with one location and preserve pair identity.", ["Every neighbor retains focal ID, neighbor ID, coordinates, and distance.", "Cold, warm, and Delta are calculated once per canonical edge.", "Self-pairs are excluded before reduction."], None, "adaptive", None),
        ("DISCOVERY", "4. The 1000 km observation domain", "D_max is support, not the answer.", ["D_max = 1000 km standardizes the maximum view.", "R* is estimated inside that view or remains unresolved.", "The workflow never substitutes 1000 km for a missing R*."], None, "unresolved", None),
        ("DISCOVERY", "5. Pairwise synchrony versus distance", "Real PRISM pairs reveal non-monotonic structure.", [f"Five exhaustive focal runs retained {pair_total:,} nonself relationships.", "Raw pairs, annular medians, IQR, and smoothed placement curves remain visible.", "Distance is great-circle kilometers."], diag, None, None),
        ("DISCOVERY", "6. Cold empirical decay curve", "Lower-tail TMIN is evaluated independently.", ["The raw annular curve is not forced to be monotonic.", "The first break is separated from the final background approach.", "Near and far robust slopes must differ enough to support a break."], diag, None, None),
        ("DISCOVERY", "7. Warm empirical decay curve", "Strict upper-tail TMAX keeps the validated semantics.", ["Warm uses observations strictly above pair-valid medians.", "Warm break validity is not borrowed from cold.", "An ambiguous or censored warm result blocks the common radius."], diag, None, None),
        ("DISCOVERY", "8. Local, regional, and broad-scale structure", "Multiple scales are retained rather than compressed silently.", ["The segmented candidate targets the first steep-to-flatter transition.", "A later transition is recorded as multiple-break structure.", "Final background approach remains a separate diagnostic."], diag, None, None),
        ("DISCOVERY", "9. Detect cold R*", "A robust two-segment candidate must beat one robust line.", ["Candidate placement uses a three-bin centered median only.", "Raw annular medians and IQR remain the evidence.", "Near-field decay, slope change, improvement, ambiguity, and boundary support are checked."], diag, None, None),
        ("DISCOVERY", "10. Detect warm R*", "The same estimator and thresholds are applied to warm synchrony.", ["No method is selected because it produces more valid pixels.", "d50, knee, derivative, and background-approach distances remain comparison candidates.", "Sampling-induced status changes count as failures."], diag, None, None),
        ("DISCOVERY", "11. Define common R*", "Cold and warm use one shared adaptive neighbor set.", ["Default rule: max(R*_cold, R*_warm).", "The rule is configurable but not changed post hoc.", f"Only {sampled_resolved}/5 sampled representatives had a valid common R*."], secondary, None, "REPRESENTATIVE GATE FAILED - COLORADO STAGE WITHHELD"),
        ("ADAPTIVE RECALCULATION", "12. Fixed 500 km neighborhood", "The comparison control comes from the same 1000 km pair product.", ["No pair correlation is recalculated for the 500 km baseline.", "Design-weighted medians estimate the complete relationship population.", f"Sampled fixed-Delta MAE versus exhaustive was {fixed_mae:.6f}."], None, "fixed", None),
        ("ADAPTIVE RECALCULATION", "13. Adaptive R* neighborhood", "Adaptive reduction is allowed only when both tails resolve.", ["Neighbors satisfy distance <= R*_common.", "Cold and warm use the identical neighbor identities.", "Unresolved, unstable, or ambiguous results remain missing."], None, "adaptive", "ONLY VALID REPRESENTATIVE PIXELS ADVANCE"),
        ("ADAPTIVE RECALCULATION", "14. Adaptive cold collapse", "Reduce cold pair values inside the common radius.", ["The estimator uses the same robust empirical median as the fixed control.", "Inverse inclusion probabilities correct the stratified far-field sample.", "Observed and estimated pair counts are retained."], primary, None, "COLORADO MAP WITHHELD BY REPRESENTATIVE GATE"),
        ("ADAPTIVE RECALCULATION", "15. Adaptive warm collapse", "Warm strength changes only through neighbor inclusion.", ["The tail definition, correlation statistic, and reduction do not change.", "The same common radius avoids strength-versus-extent confounding.", "Invalid common breaks produce no adaptive warm estimate."], primary, None, "COLORADO MAP WITHHELD BY REPRESENTATIVE GATE"),
        ("ADAPTIVE RECALCULATION", "16. Adaptive Delta collapse", "Pair identity is preserved through the final contrast.", ["For each retained neighbor: Delta_ij = S_cold,ij - S_warm,ij.", "Primary Delta is the weighted median of those paired differences.", "The reduction gap remains a separate QC field."], primary, None, "COLORADO MAP WITHHELD BY REPRESENTATIVE GATE"),
        ("ADAPTIVE RECALCULATION", "17. Repeat across pixels", "The staged gate prevents an unsupported scale field.", [f"Exhaustive common breaks resolved at {exact_resolved}/5 representatives.", f"Sampled common breaks resolved at {sampled_resolved}/5 representatives.", "The required 4/5 representative threshold was not met."], sampling, None, "STOP: NO 25-SITE COLORADO OR FULL-STATE RUN"),
        ("FIXED VS ADAPTIVE", "18. Fixed 500 km cold", "Available at all five representative pixels.", ["This is a strength summary, not a scale estimate.", "It is calculated from relationships within 500 km.", "The figure shows representative points only."], primary, None, None),
        ("FIXED VS ADAPTIVE", "19. Adaptive cold", "Available only where the common break is valid.", ["Missing symbols are scientific results, not plotting omissions.", "The sampled estimator advanced only one common site.", "No spatial interpolation is used to hide missing support."], primary, None, "PRODUCTION MAP WITHHELD"),
        ("FIXED VS ADAPTIVE", "20. Cold difference", "Adaptive minus fixed requires both estimates.", ["The intended scale is zero-centered and diverging.", "Representative sparsity prevents a defensible geographic surface.", "The output schema and calculation are implemented and tested."], primary, None, "PRODUCTION MAP WITHHELD"),
        ("FIXED VS ADAPTIVE", "21. Fixed 500 km warm", "Strict upper-tail TMAX remains unchanged.", ["The fixed warm control is complete at the representatives.", "Sampling error is small for the fixed collapse.", "This does not validate sampled break classification."], primary, None, None),
        ("FIXED VS ADAPTIVE", "22. Adaptive warm", "A valid common radius is required.", ["Cold and warm are not allowed to use different neighbor sets.", "Ambiguous warm breaks block the common result.", "This conservative rule prevents artificial Delta changes."], primary, None, "PRODUCTION MAP WITHHELD"),
        ("FIXED VS ADAPTIVE", "23. Warm difference", "Adaptive minus fixed is retained where calculable.", ["Thresholds of 0.01, 0.025, and 0.05 are implemented in comparison statistics.", "Too few common results exist for a stable spatial summary.", "No visual claim is made from unavailable pixels."], primary, None, "PRODUCTION MAP WITHHELD"),
        ("FIXED VS ADAPTIVE", "24. Fixed 500 km Delta", "Red means warm stronger; blue means cold stronger.", ["Delta > 0 means cold synchrony is stronger.", "Delta < 0 means warm synchrony is stronger.", "The red-white-blue convention is preserved."], primary, None, None),
        ("FIXED VS ADAPTIVE", "25. Adaptive Delta", "The paired contrast uses the common adaptive domain.", ["No difference-of-marginal-medians substitution occurs.", "The sign is scientifically interpretable only where R* is valid.", "Adaptive Delta is not extrapolated into unresolved pixels."], primary, None, "PRODUCTION MAP WITHHELD"),
        ("FIXED VS ADAPTIVE", "26. Delta difference", "A zero-centered comparison is ready but under-supported.", ["Difference = Delta_adaptive - Delta_500.", "A positive difference is not automatically better.", "The experiment asks where inference changes, not whether it improves."], primary, None, "PRODUCTION MAP WITHHELD"),
        ("FIXED VS ADAPTIVE", "27. Delta sign-change map", "Qualitative inference changes require valid paired estimates.", ["A sign change switches cold-stronger versus warm-stronger interpretation.", "There were zero sites with comparable exhaustive and sampled adaptive Delta.", "A sign-change fraction is therefore not reported as a map result."], primary, None, "INSUFFICIENT VALID COMMON BREAKS"),
        ("MAP THE SCALE", "28. R*_cold", "Cold characteristic distance is a separate scientific output.", ["Resolved, ambiguous, censored, and multiple-break states remain explicit.", "The sequential palette represents kilometers, not synchrony strength.", "The five-point panel is diagnostic, not a continuous map."], secondary, None, None),
        ("MAP THE SCALE", "29. R*_warm", "Warm characteristic distance is estimated independently.", ["Warm cannot inherit a cold break.", "Many warm curves were ambiguous or boundary-limited.", "That failure is central evidence for the HOLD decision."], secondary, None, None),
        ("MAP THE SCALE", "30. R*_common", "The maximum is formed only when both components are valid.", ["R*_common is not set to 1000 km when unresolved.", "Only valid common distances can drive adaptive reductions.", "No statewide scale surface was produced."], secondary, None, "COLORADO SCALE MAP WITHHELD"),
        ("MAP THE SCALE", "31. Cold-minus-warm distance contrast", "Delta_R is not Delta_S.", ["Delta_R > 0 means cold synchrony extends farther.", "Delta_R < 0 means warm synchrony extends farther.", "The contrast remains missing unless both distances are valid."], secondary, None, None),
        ("MAP THE SCALE", "32. Unresolved and stability status", "QC is mapped separately from continuous distance.", ["Status codes distinguish insufficient, flat, censored, unstable, ambiguous, resolved, and multiple breaks.", "Crosses in the representative panels identify missing continuous values.", "Unresolved areas are never hidden inside the sequential palette."], secondary, None, "BREAK CLASSIFICATION AGREEMENT = 30%"),
        ("INTERPRETATION", "33. Synchrony strength versus synchrony scale", "These answer different scientific questions.", ["Strength summarizes covariance within a chosen domain.", "Scale locates a reproducible transition in the distance response.", "Neither is automatically a dispersal kernel, natural radius, or correlation length."], None, "strength-scale", None),
        ("INTERPRETATION", "34. Where fixed 500 km was adequate", "Sampling reproduced the fixed collapse much better than it reproduced R*.", [f"Fixed 500 km Delta sampling MAE was {fixed_mae:.6f}.", "All five representative fixed summaries were available.", "This supports reuse of sampled pairs for fixed summaries, not for break classification."], sampling, None, None),
        ("INTERPRETATION", "35. Where the fixed radius mattered", "The adaptive comparison cannot be generalized yet.", ["Only common-valid sites can answer adaptive-versus-fixed questions.", "No comparable exhaustive/sampled adaptive Delta sites remained.", "The scientifically correct result is under-identification, not a forced difference map."], sampling, None, "ADAPTIVE COMPARISON UNDER-SUPPORTED"),
        ("INTERPRETATION", "36. Spatial variation in characteristic scale", "The observed candidates vary, but status instability dominates.", [f"Only {sampling_agreement:.0%} of tail classifications agreed under sampling.", f"Peak process memory was {peak_gb:.2f} GB during the bounded run.", f"A sampled full-Colorado raster is projected near {preflight['full_colorado_sampled_pairs_upper_approx']:,} pair evaluations."], secondary, None, "HOLD BEFORE COLORADO OR CONUS SCALE-UP"),
        ("INTERPRETATION", "37. Future R*(x,y,t) extension", "The data model already carries a time-window identifier.", ["Repeat the bounded method by independent time windows.", "Then estimate median, IQR, and trend of R* through time.", "Temporal work should wait until spatial break and sampling gates pass."], None, "temporal", "NEXT STEP: IMPROVE BREAK IDENTIFIABILITY, NOT SCALE-UP"),
    ]

    for number, item in enumerate(pages, start=1):
        section, title, subtitle, bullets, image, concept, banner = item
        _page(
            c,
            number=number,
            section=section,
            title=title,
            subtitle=subtitle,
            bullets=bullets,
            image=image,
            concept=concept,
            banner=banner,
        )
    c.save()
    return OUTPUT


if __name__ == "__main__":
    print(build())
