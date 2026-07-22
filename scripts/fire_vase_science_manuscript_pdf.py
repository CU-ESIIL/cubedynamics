#!/usr/bin/env python3
"""Create a science-paper-style PDF draft for the Fire VASE manuscript."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image as PILImage, ImageChops
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/fire_vase_developmental_morphology_manuscript.pdf"
MANIFEST = ROOT / "output/pdf/fire_vase_developmental_morphology_manuscript_manifest.json"
COMPLIANCE_NOTE = ROOT / "docs/manuscripts/fire_vase_developmental_morphology/science_author_guidelines_compliance.md"
ATLAS = ROOT / "output/pdf/fire_vase_developmental_morphology_atlas.pdf"
RENDER_DIR = ROOT / "tmp/pdfs/fire_vase_developmental_morphology_render"
FIGURE_DIR = ROOT / "tmp/pdfs/fire_vase_manuscript_figures"

PAGE_W, PAGE_H = letter
MARGIN_X = 1.0 * inch
MARGIN_Y = 1.0 * inch
TEXT_H = PAGE_H - 2 * MARGIN_Y
ACCENT = colors.HexColor("#9f241c")
INK = colors.HexColor("#171717")
MUTED = colors.HexColor("#5d6268")
RULE = colors.HexColor("#d9d9d9")


def render_atlas_pages() -> None:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    expected = [RENDER_DIR / f"page-{i:02d}.png" for i in range(1, 11)]
    if all(path.exists() for path in expected):
        return
    for path in RENDER_DIR.glob("page-*.png"):
        path.unlink()
    subprocess.run(
        ["pdftoppm", "-png", "-r", "180", str(ATLAS), str(RENDER_DIR / "page")],
        check=True,
        cwd=ROOT,
    )


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    out = {
        "title": ParagraphStyle(
            "PaperTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=20,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "abstract_head": ParagraphStyle(
            "AbstractHead",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=24,
            textColor=INK,
            alignment=TA_LEFT,
            spaceBefore=6,
            spaceAfter=0,
        ),
        "abstract": ParagraphStyle(
            "Abstract",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=12,
            leading=24,
            alignment=TA_LEFT,
            textColor=INK,
            spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=24,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=0,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=24,
            textColor=INK,
            spaceBefore=6,
            spaceAfter=0,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=12,
            leading=24,
            alignment=TA_LEFT,
            textColor=INK,
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=10,
            leading=18,
            alignment=TA_LEFT,
            textColor=INK,
            spaceAfter=5,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
            textColor=INK,
            spaceBefore=6,
            spaceAfter=10,
        ),
    }
    return out


def draw_line_numbers(canvas, doc) -> None:
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(MUTED)
    y = PAGE_H - MARGIN_Y - 5
    line = 1
    while y > MARGIN_Y:
        if line % 5 == 0:
            canvas.drawRightString(MARGIN_X - 0.22 * inch, y, str(line))
        y -= 24
        line += 1


def page_header(canvas, doc) -> None:
    canvas.saveState()
    canvas.setTitle("Wildfire Occupies a Continuous Developmental Morphospace")
    canvas.setAuthor("CubeDynamics Fire VASE manuscript draft")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.35)
    canvas.line(MARGIN_X, PAGE_H - 0.55 * inch, PAGE_W - MARGIN_X, PAGE_H - 0.55 * inch)
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN_X, PAGE_H - 0.43 * inch, "Fire VASE developmental morphospace - Science initial-submission style")
    canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 0.43 * inch, str(doc.page))
    draw_line_numbers(canvas, doc)
    canvas.restoreState()


def make_doc(path: Path) -> BaseDocTemplate:
    full = Frame(MARGIN_X, MARGIN_Y, PAGE_W - 2 * MARGIN_X, TEXT_H, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    return BaseDocTemplate(
        str(path),
        pagesize=letter,
        pageTemplates=[
            PageTemplate(id="First", frames=[full], onPage=page_header),
            PageTemplate(id="Text", frames=[full], onPage=page_header),
            PageTemplate(id="Figure", frames=[full], onPage=page_header),
        ],
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_Y,
        bottomMargin=MARGIN_Y,
    )


def p(text: str, style: ParagraphStyle) -> Paragraph:
    text = text.replace("R2", "R<super>2</super>")
    return Paragraph(text, style)


def add_section(story, title: str, paragraphs: list[str], st: dict[str, ParagraphStyle]) -> None:
    story.append(p(title, st["h1"]))
    for para in paragraphs:
        story.append(p(para, st["body"]))


def add_subsection(story, title: str, paragraphs: list[str], st: dict[str, ParagraphStyle]) -> None:
    story.append(p(title, st["h2"]))
    for para in paragraphs:
        story.append(p(para, st["body"]))


def figure_flowable(number: int, image_path: Path, caption: str, st: dict[str, ParagraphStyle]) -> KeepTogether:
    usable_w = PAGE_W - 2 * MARGIN_X
    with PILImage.open(image_path) as im:
        w_px, h_px = im.size
    img_w = usable_w
    img_h = img_w * h_px / w_px
    max_h = 6.15 * inch
    if img_h > max_h:
        img_h = max_h
        img_w = img_h * w_px / h_px
    image = Image(str(image_path), width=img_w, height=img_h)
    image.hAlign = "CENTER"
    cap = p(f"<b>Figure {number}.</b> {caption}", st["caption"])
    return KeepTogether([image, cap])


def prepare_figure_images() -> dict[str, Path]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    crop_pages = {
        "morphospace": RENDER_DIR / "page-02.png",
        "field_guide": RENDER_DIR / "page-04.png",
        "climate": RENDER_DIR / "page-08.png",
        "matched": RENDER_DIR / "page-09.png",
        "control": RENDER_DIR / "page-10.png",
    }
    out: dict[str, Path] = {}
    for name, source in crop_pages.items():
        target = FIGURE_DIR / f"{name}.png"
        with PILImage.open(source) as im:
            w, h = im.size
            crop = im.crop((int(w * 0.02), int(h * 0.115), int(w * 0.99), int(h * 0.99)))
            white = PILImage.new("RGB", crop.size, "white")
            diff = ImageChops.difference(crop.convert("RGB"), white)
            mask = diff.convert("L").point(lambda value: 255 if value > 8 else 0)
            bbox = mask.getbbox()
            if bbox is not None:
                pad = 24
                left, top, right, bottom = bbox
                left = max(0, left - pad)
                top = max(0, top - pad)
                right = min(crop.width, right + pad)
                bottom = min(crop.height, bottom + pad)
                crop = crop.crop((left, top, right, bottom))
            crop.save(target)
        out[name] = target
    return out


def build_story() -> list:
    st = styles()
    story: list = []
    story.append(p("Wildfire Occupies a Continuous Developmental Morphospace", st["title"]))
    story.append(p("Article type: Research Article | Initial-submission style draft | 22 July 2026", st["subtitle"]))
    story.append(p("Authors", st["abstract_head"]))
    story.append(p("Tuff et al.", st["abstract"]))
    story.append(p("Affiliations", st["abstract_head"]))
    story.append(p("Author affiliations, corresponding author email, and ORCID identifiers to be finalized before submission.", st["abstract"]))
    story.append(p("Abstract", st["abstract_head"]))
    story.append(
        p(
            "Wildfire histories are usually compared as final area, perimeter, or daily growth, leaving whole-fire development without a compact coordinate system. We introduce Fire VASE, a geometry-first representation that converts each observed daily fire history into a single developmental object. Across 278,569 FIRED events from 2000-2021, geometry-only VASE features occupy a constrained morphospace: five principal components explain 96.3% of variance. Projecting gridMET climate onto 237,235 climate-complete fires shows asymmetric coupling. Centroid climate explains part of the dominant morphospace axis, whereas developmental geometry carries far more stage-wise information about final morphospace position. Fire VASE provides a common coordinate system for testing how climate, fuels, topography, and suppression act through developmental state.",
            st["abstract"],
        )
    )
    story.append(p("One Sentence Summary", st["abstract_head"]))
    story.append(p("Wildfire histories form a constrained developmental morphospace.", st["abstract"]))
    story.append(NextPageTemplate("Text"))
    story.append(PageBreak())

    add_section(
        story,
        "Introduction",
        [
            "Wildfire science has become extraordinarily successful at measuring fire. Satellite burned-area products delineate events over continental domains, event-delineation algorithms assemble those observations into fire histories, and gridded meteorological data provide spatially consistent descriptions of the atmospheric setting in which fires burn [1-3]. Fire behavior models and empirical fire-climate studies have also shown that fire spread and burned area are shaped by weather, fuels, topography, aridity, and human intervention [4-9].",
            "These advances have transformed fire from an episodic disturbance observed after the fact into a spatially and temporally resolved phenomenon. Yet a representational problem remains. The field has many event representations, but fewer compact, comparable, whole-history developmental representations. A fire can be summarized by a final perimeter, a total area, a duration, a sequence of daily perimeters, a daily growth curve, or the weather it experienced. Each is useful, but none alone makes the entire developmental history of one fire directly comparable with that of hundreds of thousands of others.",
            "This gap matters because fire development is not only an outcome. Fast daily growth, early bursts, late reactivations, pauses, and termination all affect ecological impact, exposure, carbon release, and management opportunity. Recent work on the fastest-growing and most destructive fires underscores that daily timing is not incidental [7]. If the timing of growth matters, then the geometry of whole-fire development should be treated as an object of analysis rather than as a nuisance collapsed into final area.",
            "Many fields confront similar problems by constructing morphospaces. A morphospace is not merely a visualization; it is a coordinate system in which complex forms become comparable observations [10,11]. Such spaces allow investigators to estimate constraint, select representative forms, and evaluate external drivers relative to intrinsic geometry. We use that logic here, asking whether wildfire histories occupy an unstructured cloud or a constrained developmental morphospace.",
            "The Fire VASE is designed to make this test possible. For each fire, daily cumulative burned area is mapped to width and developmental time is mapped to vertical position, producing a vase-like object whose rings record the progression of the event. The representation is deliberately geometry-first. Climate and other environmental variables are projected onto the VASE only after geometry has defined the coordinate system. This separation lets us ask whether fire development has its own structure before asking how climate aligns with it.",
            "The central hypothesis is simple. If whole-fire development is arbitrary, then VASEs should fill feature space diffusely and require many axes to summarize. If development is constrained, then independent fires should repeatedly occupy a low-dimensional, structured morphospace. We test this hypothesis using the current CubeDynamics Fire VASE workflow applied to FIRED event histories and gridMET climate attribution for 2000-2021.",
        ],
        st,
    )

    story.append(p("Results", st["h1"]))

    add_subsection(
        story,
        "Fire VASE Converts Histories Into Developmental Objects",
        [
            "The current analysis includes 278,569 FIRED events and 626,102 daily VASE slices spanning 2000-2021. Each VASE is derived from the observed daily event history rather than from a simulated or synthetic fire. The resulting object preserves the sequence of development while making events comparable through shared geometry features.",
            "The population is dominated by short fires, which is both a result and an important caveat. The median event lasts 1 day; the 75th percentile lasts 4 days, the 90th percentile lasts 8 days, the 99th percentile lasts 18 days, and the longest event in the current table lasts 85 days. Final burned area is similarly skewed: the median event reaches 0.43 km2, while the 99th percentile reaches 27.48 km2 and the maximum reaches 3503.87 km2. The morphospace therefore describes the fire population as observed, including the many short-duration events that structure its dense core.",
        ],
        st,
    )

    add_subsection(
        story,
        "Wildfire Occupies a Low-Dimensional Morphospace",
        [
            "The geometry-only feature space is strongly constrained (Fig. 1). Across all events, the first five principal components explain 96.3% of standardized VASE-feature variance. PC1 alone explains 81.0%, followed by PC2 at 6.6%, PC3 at 3.5%, PC4 at 3.3%, and PC5 at 1.8%. This concentration of variance supports the hypothesis that fire development repeatedly occupies a structured region of morphospace rather than an unorganized cloud of unrelated forms.",
            "The axes should be interpreted as descriptive coordinates rather than final mechanisms. PC1 is dominated by growth-profile structure and growth entropy, separating fires by broad developmental allocation through time. PC2 emphasizes terminal taper, peak growth, late growth, observation count, pulse/reactivation structure, final area, and developmental velocity. PC3 captures pulse/reactivation, peak timing, late and terminal growth, entropy, and slenderness. These axes provide a first coordinate system for comparison; mechanistic interpretation will require fuels, topography, suppression, and active-edge climate attribution.",
        ],
        st,
    )

    add_subsection(
        story,
        "Representative Forms Are Landmarks, Not Classes",
        [
            "Thirty-six real medoid fires were selected by farthest-point coverage in PC1-PC3 morphospace (Fig. 2). These medoids are not idealized shapes. They are observed fires that serve as landmarks for densely and sparsely occupied parts of the developmental space. This is important because the morphospace is continuous: categories help the reader navigate it, but they are not imposed as discrete biological or operational types.",
            "The current descriptive labels are therefore provisional landmarks. Single-flash fires form the largest group (161,073 events), followed by skinny persistent fires (38,094), compact steady fires (23,815), multi-pulse complex fires (21,254), front-loaded plateau fires (17,396), and late-surge fires (16,937). These counts describe how the present rule-based labels partition the population, not immutable classes. The stronger result is that recognizable developmental neighborhoods recur across independent fire histories.",
        ],
        st,
    )

    add_subsection(
        story,
        "Climate Projects Onto Morphology Asymmetrically",
        [
            "Daily gridMET climate was available for 237,235 climate-complete fires. The remaining 41,334 fires have missing centroid climate values for one or more daily slices in the current extraction and are retained in the geometry-only population but excluded from climate-coupled models. Climate variables include maximum temperature and minimum temperature in degrees C, vapor pressure deficit (VPD) in kPa, and wind speed in m/s.",
            "Because the VASE coordinate system is geometry-first, climate can be treated as an attribute of development rather than as an axis used to define development (Fig. 3). In the current linear baseline, climate explains a modest amount of morphology: held-out R2 is 0.509 for PC1, 0.062 for PC2, 0.001 for PC3, and 0.191 on average across the modeled morphospace axes. The dominant developmental axis is therefore partly climate aligned, but later axes are weakly explained by these centroid daily climate summaries.",
            "The reverse direction is weaker. Morphology retains little linear information about mean maximum temperature (R2 = 0.004), mean minimum temperature (R2 = 0.009), mean VPD (R2 = 0.006), or mean wind (R2 = 0.010), although it retains more information about maximum VPD (R2 = 0.071). These values should not be read as causal estimates. They are a first-pass linear information proxy for how much average centroid climate and developmental morphology recover from each other.",
        ],
        st,
    )

    add_subsection(
        story,
        "Developmental State Dominates The Linear Baseline",
        [
            "Stage-wise models ask whether partial development already contains information about the final morphospace position (Fig. 4). We divide each event into early, expansion, mature, and terminal stages and compare climate-only, geometry-only, and geometry-plus-climate predictors. Climate-only models explain little of final morphospace position across stages: mean R2 is 0.005 early, 0.014 during expansion, 0.004 at maturity, and 0.004 at terminal development.",
            "Geometry-only stage features are much more informative. Mean R2 is 0.653 early, 0.714 during expansion, 0.846 at maturity, and 0.733 at terminal development. Adding centroid climate to geometry changes the baseline only modestly, with mean R2 values of 0.653, 0.725, 0.849, and 0.732 across the same stages. This pattern does not imply that climate is unimportant. It implies that, in this linear baseline, the current geometry of the fire is the dominant summary of where the fire is headed in morphospace.",
        ],
        st,
    )

    add_subsection(
        story,
        "Matched Comparisons Expose Non-Equivalence",
        [
            "Matched comparisons provide a diagnostic for separating similarity in form from similarity in climate (Fig. 5). The current atlas includes pairs of fires with similar morphology under different climate conditions and pairs with similar climate summaries but different morphology. These examples are useful because they prevent the morphospace from being read as a simple climate map.",
            "At this stage, the matched pairs are illustrative rather than a completed statistical test. A submission-ready version should expand this analysis into distributional comparisons across matched neighborhoods, including uncertainty in match quality and sensitivity to fire duration. The current result is enough to motivate the claim that climate and morphology are coupled but not equivalent.",
        ],
        st,
    )

    add_section(
        story,
        "Discussion",
        [
            "The Fire VASE results support a developmental view of wildfire. A fire is not only a final footprint or a sequence of perimeters; it is a trajectory through a constrained space of possible histories. The low dimensionality of the geometry-only morphospace suggests that many fires, despite enormous environmental and geographic heterogeneity, repeatedly use similar developmental pathways.",
            "This framing complements rather than replaces fire-climate and fire behavior research. The existing literature establishes that aridity, VPD, fuels, topography, and wind strongly influence fire activity and spread [4-9]. Fire VASE adds a coordinate system for asking how those influences are expressed through whole-fire development. The current results suggest that wildfire development is neither arbitrary nor fully reducible to average centroid climate conditions.",
            "The key conceptual implication is state dependence. Climate matters, but a given climate value does not have a single meaning independent of developmental state. A hot, dry, windy day may affect a newly emerging fire differently than a front-loaded plateau, a persistent narrow fire, or a late-reactivating fire. Developmental geometry is therefore not a rival explanation to climate. It is a state variable through which climate, fuels, topography, and suppression are expressed.",
            "The current analysis also reframes classification. The labels used here are field-guide terms for recurring neighborhoods, not fixed classes. That distinction matters because a continuous morphospace can support both typology and gradient analysis. The goal is not to force all fires into bins, but to make local neighborhoods, extremes, transitions, and analogs visible for comparison.",
            "Several caveats define the next stage of the work. Climate attribution is daily and centroid-based, not active-edge, newly burned area, or within-perimeter climate exposure. The analysis does not yet include humidity, precipitation, fuel moisture, topography, vegetation, suppression, ignition cause, or climate anomalies relative to local normals. The coupling values are linear information baselines rather than optimized predictive models or causal estimates. Finally, the prevalence of one-day events means that sensitivity analyses separating single-day, short multi-day, and long-duration fires will be essential before submission.",
            "Despite these limits, the present result is a useful foundation. It shows that a continental fire archive can be re-expressed as a population of developmental forms, that those forms occupy a strongly structured morphospace, and that climate can be projected onto that space without using climate to define it. Fire VASE is therefore best understood as an instrument for organizing fire history before building richer mechanistic explanations.",
        ],
        st,
    )

    story.append(p("Materials and Methods", st["h1"]))

    add_subsection(
        story,
        "Event Records",
        [
            "Fire events and daily progression were derived from FIRED-style event products in the current CubeDynamics workflow [1]. The analysis table contains 278,569 events and 626,102 daily VASE slices from 2000-2021. Each event is represented as an ordered daily sequence with event identifier, date, cumulative area, daily growth, duration, and centroid coordinates where available.",
            "Climate-complete status was evaluated after gridMET extraction. A fire is climate complete when all required daily centroid samples are present for the variables used here. This yields 237,235 climate-complete fires. Fires with missing centroid climate remain part of the geometry-only morphospace but are excluded from climate-coupled analyses.",
        ],
        st,
    )

    add_subsection(
        story,
        "VASE Construction",
        [
            "For each fire, developmental time is mapped to vertical position and cumulative burned area is mapped to radial width. The object is rendered as stacked rings so that each ring corresponds to one observed daily slice. The VASE geometry is therefore a compact whole-history representation: broad rings indicate larger cumulative burned area, abrupt changes in ring width indicate rapid growth, and thin or tapered regions indicate persistence or termination.",
            "Geometry is constructed before climate attribution. This prevents meteorology from defining the morphospace and allows climate to be studied as an external projection. The same geometric object can later carry temperature, VPD, wind, fuels, topography, suppression, or other slice-level covariates.",
        ],
        st,
    )

    add_subsection(
        story,
        "Morphospace Features",
        [
            "Geometry-only features summarize scale, time, pulse structure, taper, entropy, and profile shape. Features include final area, duration, peak daily growth, observation count, pulse count, reactivation count, peak timing, front-loaded growth fraction, late growth fraction, terminal taper, growth entropy, developmental velocity, developmental acceleration, slenderness, and interpolated cumulative-width and daily-growth profiles.",
            "Features were standardized before principal component analysis. PCA was fit on geometry-only features to define a shared morphospace. The first five PCs explain 96.3% of standardized feature variance and are used as descriptive developmental coordinates. The current interpretation of PC axes is based on loadings and should be treated as descriptive until tested against independent environmental and operational covariates.",
        ],
        st,
    )

    add_subsection(
        story,
        "Medoids And Shape Labels",
        [
            "Representative VASEs were selected as real medoid fires using farthest-point coverage in PC1-PC3. This procedure samples the occupied morphospace without creating synthetic examples. Medoids are used as visual landmarks in the atlas and manuscript figures.",
            "Rule-based shape labels were assigned from geometry features to provide a field-guide vocabulary. Labels include single flash, skinny persistent, compact steady, multi-pulse complex, front-loaded plateau, and late surge. These labels are interpretive summaries used for communication and exploratory counting; the primary analysis treats morphospace as continuous.",
        ],
        st,
    )

    add_subsection(
        story,
        "Climate Attribution",
        [
            "Daily gridMET variables were extracted at the event centroid for each VASE slice [3]. Variables include maximum temperature in degrees C, minimum temperature in degrees C, vapor pressure deficit in kPa, and wind speed in m/s. Wind is represented in the simplest current form as presence and average speed; richer directional and gust structure is deferred.",
            "Centroid extraction is a first-pass continental proxy. It does not necessarily represent the active flaming edge, newly burned cells, within-fire heterogeneity, or local topographic exposure. For this reason, climate results are interpreted as baseline associations between broad daily meteorological context and VASE morphology.",
        ],
        st,
    )

    add_subsection(
        story,
        "Coupling And Stage Models",
        [
            "Directional coupling was evaluated with held-out linear baseline models. One direction predicts morphospace coordinates from climate summaries, written informally as P(morphology | climate). The reverse predicts climate summaries from morphospace coordinates, written as P(climate | morphology). These are not causal estimates and are not mutual-information estimates; they are linear proxies for recoverable structure under a simple model.",
            "Developmental control profiles were evaluated by splitting each fire into early, expansion, mature, and terminal stages. For each stage, geometry-only, climate-only, and geometry-plus-climate predictors were compared for their ability to recover final morphospace position. This establishes how much information is already present in partial developmental state relative to centroid climate summaries.",
        ],
        st,
    )

    add_subsection(
        story,
        "Matched Comparisons",
        [
            "Matched examples were generated to expose two contrasts: similar morphology under different climate and similar climate under different morphology. The manuscript figure presents these as diagnostic examples rather than as a final inferential test. A future version should quantify these contrasts across neighborhoods with explicit matching tolerances, uncertainty, and duration-stratified sensitivity.",
        ],
        st,
    )

    story.append(NextPageTemplate("Text"))
    story.append(PageBreak())
    story.append(p("References and Notes", st["h1"]))
    refs = [
        "Balch, J. K. et al. FIRED (Fire Events Delineation): An open, flexible algorithm and database of US fire events derived from the MODIS burned area product (2001-2019). Remote Sensing 12, 3498 (2020).",
        "Mahood, A. L. et al. Country-level fire perimeter datasets (2001-2021). Scientific Data 9, 458 (2022).",
        "Abatzoglou, J. T. Development of gridded surface meteorological data for ecological applications and modelling. International Journal of Climatology 33, 121-131 (2013).",
        "Abatzoglou, J. T. & Williams, A. P. Impact of anthropogenic climate change on wildfire across western US forests. Proceedings of the National Academy of Sciences 113, 11770-11775 (2016).",
        "Williams, A. P. et al. Observed impacts of anthropogenic climate change on wildfire in California. Earth's Future 7, 892-910 (2019).",
        "He, Q. et al. Influence of time-averaging of climate data on estimates of atmospheric vapor pressure deficit and inferred relationships with wildfire area in the western United States. Geophysical Research Letters 52, e2024GL113708 (2025).",
        "Balch, J. K. et al. The fastest growing and most destructive fires in the U.S. (2001-2020). Science 386, 425-431 (2024).",
        "Holsinger, L. M., Parks, S. A. & Miller, C. Weather, fuels, and topography impede wildland fire spread in western US landscapes. Forest Ecology and Management 380, 59-69 (2016).",
        "Povak, N. A. et al. Evidence for scale-dependent topographic controls on wildfire spread. Ecosphere 9, e02443 (2018).",
        "Bookstein, F. L. Morphometric Tools for Landmark Data: Geometry and Biology. Cambridge University Press (1991).",
        "Mitteroecker, P. & Gunz, P. Advances in geometric morphometrics. Evolutionary Biology 36, 235-247 (2009).",
    ]
    for i, ref in enumerate(refs, start=1):
        story.append(p(f"{i}. {ref}", st["small"]))

    story.append(p("Acknowledgments", st["h1"]))
    story.append(p("The author list, acknowledgments, funding sources, and institutional affiliations are placeholders in this draft and must be finalized before submission.", st["small"]))
    story.append(p("<b>Funding:</b> Funding sources to be finalized.", st["small"]))
    story.append(p("<b>Author contributions:</b> Author contribution roles to be finalized.", st["small"]))
    story.append(p("<b>Competing interests:</b> The authors declare no competing interests, pending author confirmation.", st["small"]))
    story.append(p("<b>Data and materials availability:</b> This draft was generated from CubeDynamics Fire VASE workflow artifacts. Public archival links for FIRED-derived inputs, gridMET extraction products, derived analysis tables, and reproducible figure scripts must be added before submission.", st["small"]))
    story.append(p("<b>Supplementary materials:</b> Supplementary methods, sensitivity analyses, derived tables, and additional atlas panels are planned but not yet packaged.", st["small"]))

    story.append(NextPageTemplate("Figure"))
    story.append(PageBreak())
    figure_paths = prepare_figure_images()
    figures = [
        (
            1,
            figure_paths["morphospace"],
            "Geometry-first developmental morphospace with representative Fire VASE medoids. Points are real FIRED events positioned by geometry-only VASE features. Red medoids summarize neighborhoods in PC1-PC3 morphospace.",
        ),
        (
            2,
            figure_paths["field_guide"],
            "Field-guide examples of representative developmental forms. Each VASE is a real medoid fire; rings are observed developmental slices and colors show maximum temperature where available.",
        ),
        (
            3,
            figure_paths["climate"],
            "Climate projected onto the geometry-first morphospace. Temperature, VPD, and wind are mapped after the morphospace is constructed, so climate does not define the axes.",
        ),
        (
            4,
            figure_paths["control"],
            "Developmental control profile. Stage-wise geometry-only models carry far more information about final morphospace position than climate-only models in the current linear baseline.",
        ),
        (
            5,
            figure_paths["matched"],
            "Matched comparisons showing similar morphology under different climate and similar climate with different morphology. These pairs illustrate that morphology and climate are coupled but not equivalent.",
        ),
    ]
    for fig_no, img, caption in figures:
        story.append(figure_flowable(fig_no, img, caption, st))
        if fig_no != figures[-1][0]:
            story.append(PageBreak())
    return story


def build_pdf() -> dict:
    render_atlas_pages()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = make_doc(OUTPUT)
    story = build_story()
    doc.build(story)
    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "pdf": OUTPUT.as_posix(),
        "source_atlas": ATLAS.as_posix(),
        "figures": [
            (FIGURE_DIR / "morphospace.png").as_posix(),
            (FIGURE_DIR / "field_guide.png").as_posix(),
            (FIGURE_DIR / "climate.png").as_posix(),
            (FIGURE_DIR / "control.png").as_posix(),
            (FIGURE_DIR / "matched.png").as_posix(),
        ],
        "format": "Science initial-submission-style draft: single column, double spaced, line numbered, figures grouped after text",
        "compliance_note": COMPLIANCE_NOTE.as_posix(),
    }
    MANIFEST.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    print(json.dumps(build_pdf(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
