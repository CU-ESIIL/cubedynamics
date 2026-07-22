#!/usr/bin/env python3
"""Create a science-paper-style PDF draft for the Fire VASE manuscript."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image as PILImage
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
FIGURE_DIR = ROOT / "tmp/pdfs/fire_vase_manuscript_figures"
MAIN_FIGURE_DIR = ROOT / "figures/main"

PAGE_W, PAGE_H = letter
MARGIN_X = 1.0 * inch
MARGIN_Y = 1.0 * inch
TEXT_H = PAGE_H - 2 * MARGIN_Y
ACCENT = colors.HexColor("#9f241c")
INK = colors.HexColor("#171717")
MUTED = colors.HexColor("#5d6268")
RULE = colors.HexColor("#d9d9d9")


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
            fontSize=8.7,
            leading=11.6,
            alignment=TA_LEFT,
            textColor=INK,
            spaceBefore=6,
            spaceAfter=8,
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
    max_h = 5.25 * inch
    if img_h > max_h:
        img_h = max_h
        img_w = img_h * w_px / h_px
    image = Image(str(image_path), width=img_w, height=img_h)
    image.hAlign = "CENTER"
    cap = p(f"<b>Figure {number}.</b> {caption}", st["caption"])
    return KeepTogether([image, cap])


def prepare_figure_images() -> dict[str, Path]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    source_images = {
        "figure_1": MAIN_FIGURE_DIR / "Figure_1.png",
        "figure_2": MAIN_FIGURE_DIR / "Figure_2.png",
        "figure_3": MAIN_FIGURE_DIR / "Figure_3.png",
        "figure_4": MAIN_FIGURE_DIR / "Figure_4.png",
        "figure_5": MAIN_FIGURE_DIR / "Figure_5.png",
    }
    out: dict[str, Path] = {}
    for name, source in source_images.items():
        if not source.exists():
            raise FileNotFoundError(f"Missing main figure image: {source}")
        target = FIGURE_DIR / f"{name}.png"
        with PILImage.open(source) as im:
            im.convert("RGB").save(target)
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
            "Wildfire histories are usually compared as final area, perimeter, or daily growth, leaving whole-fire development without a compact coordinate system. We introduce Fire VASE, a geometry-first representation that converts each observed daily fire history into a single developmental object. Across 278,569 FIRED events from 2000-2021, geometry-only VASE features occupy a constrained morphospace: five principal components explain 96.3% of variance. Real-fire medoids and transects reveal recurrent forms arranged along continuous gradients rather than fixed classes. Projecting gridMET climate onto 237,235 climate-complete fires shows alignment, especially along the dominant axis, but matched examples and blocked validation show that climate and morphology are not equivalent. Fire VASE provides a common coordinate system for testing how climate, fuels, topography, and suppression act through developmental state.",
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
            "The central hypothesis is simple. If whole-fire development is arbitrary, then VASEs should fill feature space diffusely and require many axes to summarize. If development is constrained, then independent fires should repeatedly occupy a low-dimensional, structured morphospace. The discovery sought here is therefore representation-first: a reproducible coordinate system for fire development that can later be coupled to mechanistic covariates. We test this hypothesis using the current CubeDynamics Fire VASE workflow applied to FIRED event histories and gridMET climate attribution for 2000-2021.",
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
            "The geometry-only feature space is strongly constrained (Fig. 1). Across all events, the first five principal components explain 96.3% of standardized VASE-feature variance. PC1 alone explains 81.0%, followed by PC2 at 6.6%, PC3 at 3.5%, PC4 at 3.3%, and PC5 at 1.8%. A stratified bootstrap using 60 repeated 12,000-fire subsamples gives a PC1-PC5 median of 96.3% with a 95% interval of 96.2-96.4% and near-perfect five-dimensional subspace overlap. This concentration of variance supports the hypothesis that fire development repeatedly occupies a structured region of morphospace rather than an unorganized cloud of unrelated forms.",
            "The validation hierarchy is uneven but informative. The result is strongest against a feature-wise permutation null, which breaks covariance among VASE features and reduces five-PC variance to about 42.6%. The result is weaker against a within-fire growth-profile permutation null, which remains close to the observed value at about 95.7%. That caveat is important: part of the apparent constraint reflects the monotone and redundant structure of cumulative growth histories. Duration sensitivity also weakens the concentration for long fires, with five-PC variance falling to 78.5% for fires lasting at least 10 days. The primary result is therefore not that all fire histories have identical geometry, but that the full observed population occupies a highly concentrated, reproducible developmental coordinate system.",
        ],
        st,
    )

    add_subsection(
        story,
        "Representative Forms Are Landmarks, Not Classes",
        [
            "Thirty-six real medoid fires were selected by farthest-point coverage in PC1-PC3 morphospace, and the main atlas displays the 18 highest-occupancy medoids over the full density field (Fig. 2). These medoids are not idealized shapes. They are observed fires that serve as landmarks for densely and sparsely occupied parts of the developmental space. Coverage improves rapidly as more medoids are added, showing that a modest set of real events can summarize large regions of the occupied space while still preserving continuity.",
            "The current descriptive labels are therefore provisional landmarks. Single-flash fires form the largest group (161,073 events), followed by skinny persistent fires (38,094), compact steady fires (23,815), multi-pulse complex fires (21,254), front-loaded plateau fires (17,396), and late-surge fires (16,937). Local neighborhood purity is high relative to class-frequency expectation, but the categories also overlap across nearby regions of morphospace. The stronger result is not the discovery of hard classes; it is the recurrence of recognizable developmental neighborhoods embedded in a continuous space.",
        ],
        st,
    )

    add_subsection(
        story,
        "Major Axes Encode Interpretable Developmental Gradients",
        [
            "The axes should be interpreted as descriptive coordinates rather than final mechanisms (Fig. 3). Transects through PC1, PC2, and PC3 show gradual changes in real Fire VASEs and their cumulative area histories, making the axes legible as developmental gradients. PC1 is dominated by growth-profile structure and temporal concentration, separating histories with narrow persistent growth from broad or rapidly allocated histories. PC2 mixes taper, duration, late growth, pulse structure, and scale. PC3 emphasizes pulse/reactivation and timing structure.",
            "Grouped loadings and raw-history regression proxies support this reading while also showing why mechanistic interpretation must remain cautious. Profile features carry much of PC1 and contribute strongly to PC2 and PC3, whereas pulse and timing features become more important in later axes. These relationships make the morphospace interpretable enough for biological and operational hypotheses, but they do not assign causes. Fuels, topography, suppression, ignition context, and active-edge climate are needed before the axes can be treated as mechanisms.",
        ],
        st,
    )

    add_subsection(
        story,
        "Climate Aligns With Morphology But Does Not Define It",
        [
            "Daily gridMET climate was available for 237,235 climate-complete fires. The remaining 41,334 fires have missing centroid climate values for one or more daily slices in the current extraction and are retained in the geometry-only population but excluded from climate-coupled models. Climate variables include maximum temperature and minimum temperature in degrees C, vapor pressure deficit (VPD) in kPa, and wind speed in m/s.",
            "Because the VASE coordinate system is geometry-first, climate can be treated as an attribute of development rather than as an axis used to define development (Fig. 4). Temperature, VPD, and wind surfaces vary across morphospace, indicating that development is climate aligned. In held-out linear baselines, climate predicts some morphology, especially the dominant axis, but performance is lower and less stable under region-blocked validation than under random splits. Conversely, morphology recovers only limited information about average centroid climate. These values should not be read as causal estimates. They are a first-pass information proxy for how much average centroid climate and developmental morphology recover from each other.",
            "Matched examples expose the same non-equivalence. Some fires have nearly identical morphology but strongly different climate summaries, whereas others have similar climate summaries but very different VASE geometry. Population-level nearest-neighbor matching shows the same pattern in aggregate. Climate is therefore not absent from the morphospace; it is projected onto a developmental coordinate system that also encodes other unmodeled constraints.",
        ],
        st,
    )

    add_subsection(
        story,
        "Fixed-Day Prediction Provides A Leakage-Audited Benchmark",
        [
            "A final benchmark asks how much of final morphospace position can be recovered from partial histories observed by fixed days 1, 2, 4, and 8 (Fig. 5). This analysis intentionally replaces an older fractional-stage table whose normalized stage width, normalized growth fraction, and full-event pulse count used information unavailable at prediction time. The revised benchmark uses only cumulative area, growth, active days, and climate observed up to each fixed day.",
            "The conservative result is weak under blocked validation. Region- and year-blocked held-out R2 values for final PC1-PC3 are near zero and sometimes negative, although geometry-plus-climate models show small, stage-dependent gains over geometry-only models. This does not mean early development is uninformative in principle. It means that, with the current fixed-day linear features and strict blocked validation, the manuscript should not claim strong early prediction. Figure 5 is therefore a leakage audit and benchmark for future model development rather than a major affirmative prediction result.",
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
            "This representation-first contribution creates several testable next hypotheses. Fires in the same developmental neighborhood should share some combination of meteorological exposure, fuel condition, landscape structure, ignition context, or management history. Fires that are climate-similar but morphologically different should identify missing controls. Fires that are morphologically similar under contrasting climates should identify compensating pathways. The morphospace is useful precisely because it turns these questions into comparisons among nearby and distant developmental forms.",
            "The current analysis also reframes classification. The labels used here are field-guide terms for recurring neighborhoods, not fixed classes. That distinction matters because a continuous morphospace can support both typology and gradient analysis. The goal is not to force all fires into bins, but to make local neighborhoods, extremes, transitions, and analogs visible for comparison.",
            "Several caveats define the next stage of the work. Climate attribution is daily and centroid-based, not active-edge, newly burned area, or within-perimeter climate exposure. The analysis does not yet include humidity, precipitation, fuel moisture, topography, vegetation, suppression, ignition cause, or climate anomalies relative to local normals. The coupling and prediction values are linear information baselines rather than optimized predictive models or causal estimates. The temporal-order null and duration sensitivity show that the low-dimensional result is partly shaped by profile redundancy and the prevalence of short fires. These limitations sharpen rather than erase the claim: Fire VASE reveals a reproducible coordinate system for fire development, not a completed mechanistic theory of every fire.",
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
            "Directional coupling was evaluated with held-out linear baseline models. One direction predicts morphospace coordinates from climate summaries, written informally as P(morphology | climate). The reverse predicts climate summaries from morphospace coordinates, written as P(climate | morphology). Models were evaluated under random, region-blocked, and year-blocked folds. These are not causal estimates and are not mutual-information estimates; they are linear proxies for recoverable structure under a simple model.",
            "Partial-history prediction was evaluated with a leakage-audited fixed-day table. For days 1, 2, 4, and 8, predictors were restricted to quantities available by that day: cumulative burned area so far, growth observed so far, active-day summaries, and climate observed so far. Final morphospace position was represented by the first three developmental coordinates. Region- and year-blocked folds are treated as the conservative benchmark because they test whether the relationship transfers across broad spatial or temporal partitions. The older fractional-stage table is not used for the main prediction claim because several stage variables were normalized by final fire size or counted future pulses, making them unavailable at early prediction time.",
        ],
        st,
    )

    add_subsection(
        story,
        "Validation Analyses",
        [
            "PCA stability was assessed with stratified bootstrap resampling by duration, area, year, and region. Null analyses compared the observed PCA against feature-wise permutation and within-fire growth-profile permutation. Sensitivity analyses repeated the PCA after duration filtering and feature ablation. Medoid coverage was quantified by nearest-medoid distance in PC1-PC3, and shape-label overlap was quantified by local nearest-neighbor purity relative to class-frequency expectation.",
            "Matched examples were generated to expose two contrasts: similar morphology under different climate and similar climate under different morphology. Population-level matching used nearest-neighbor searches in one standardized space followed by distance measurement in the other. The current matched analysis is a diagnostic for non-equivalence rather than a completed causal or mechanistic test.",
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
    story.append(p("<b>Supplementary materials:</b> Supplementary validation summaries, derived statistics, figure legends, a data dictionary, and a reproducible figure manifest are packaged under figures/main and figures/supplement in this repository.", st["small"]))

    story.append(NextPageTemplate("Figure"))
    story.append(PageBreak())
    figure_paths = prepare_figure_images()
    figures = [
        (
            1,
            figure_paths["figure_1"],
            "Whole-fire histories collapse into a common developmental coordinate system. Fire VASE converts each real FIRED event into a comparable developmental object by mapping event time from bottom to top and normalized cumulative burned area to ring width. Panel A shows five observed fires, pairing each daily cumulative-area history with its corresponding VASE glyph; labels give the descriptive shape name, duration in days, and final burned area in square kilometers. Panel B shows the geometry-only morphospace for all 278,569 fires along the first two developmental gradients. The gray density field is the fire population, darker tones indicate higher density, and red points are high-occupancy real representative fires used as atlas landmarks. Panels C and D evaluate low dimensionality: the scree plot shows individual and cumulative explained variance for the first ten axes, while the null comparison places the observed five-axis variance against feature-wise and within-fire growth-timing permutation nulls. Panel E repeats the PCA after excluding increasingly short fires, showing that the low-dimensional structure persists but weakens for longer-duration subsets.",
        ),
        (
            2,
            figure_paths["figure_2"],
            "Wildfire occupies a continuous atlas of recurring developmental forms. Panel A places the 18 highest-occupancy real representative Fire VASEs over the full geometry-only density field. Each representative is an observed fire, not an idealized or synthetic glyph; leader lines connect displaced glyphs to their true coordinates along the first two developmental gradients. Panel B ranks representatives by the number of fires closest to each one in the first three gradients, illustrating that some developmental neighborhoods are common whereas others are rare. Panel C shows the coverage curve: as the number of representative fires increases, median and 90th-percentile distance to the nearest representative decline, indicating that a compact atlas can summarize occupied morphospace. Panel D shows real-fire transects through gradients 1, 2, and 3, with glyph shape changing gradually along each axis. Panel E compares local shape-label purity with a class-frequency reference, supporting the use of labels as soft landmarks within a continuous morphospace rather than as sharply separated classes.",
        ),
        (
            3,
            figure_paths["figure_3"],
            "The major axes encode interpretable dimensions of fire development. Panels A-C show five observed fires sampled along developmental gradients 1, 2, and 3. For each example, the upper glyph is the Fire VASE and the lower mini-plot is the normalized cumulative-area history, allowing the reader to see how coordinate score corresponds to developmental shape. Gradient 1 primarily tracks growth allocation and temporal concentration, gradient 2 mixes taper, duration, late growth, and scale, and gradient 3 emphasizes pulse/reactivation and timing structure. Panel D groups feature contributions by domain, showing which families of VASE features contribute to each axis. Panel E validates the axis interpretation with simple raw-history regression proxies, controlling for duration, final area, and observation count. These panels interpret the coordinate system descriptively; they do not by themselves identify fuels, climate, suppression, or topography as mechanisms.",
        ),
        (
            4,
            figure_paths["figure_4"],
            "Climate aligns with developmental geometry but does not uniquely determine it. Panel A projects median maximum vapor pressure deficit (VPD, kPa) onto the geometry-first morphospace for 237,235 climate-complete fires; the axes remain the geometry-only developmental gradients from Figure 1. Panel B repeats the projection for average daily high temperature in degrees C, average VPD in kPa, and average wind speed in m/s, showing that broad climate gradients are visible after the morphospace has been defined. Panel C summarizes held-out linear coupling models comparing climate predicting shape and shape predicting climate under random and region-blocked folds. Error bars show fold variation and blocked results are treated as the conservative comparison. Panel D shows matched real-fire examples that separate similar shape from similar climate. Panel E summarizes population-level matched distances, reinforcing that climate and morphology are associated but not interchangeable.",
        ),
        (
            5,
            figure_paths["figure_5"],
            "Fixed-day partial histories provide a leakage-audited developmental benchmark. Panel A illustrates the prediction task with one real fire truncated at fixed observed-day stages. For each stage, the partial VASE contains only information available by that day, while the adjacent final VASE shows the complete event. Panel B compares region-blocked prediction accuracy for final shape using trivial stage summaries, climate-only predictors, geometry-only predictors, and geometry-plus-climate predictors. Values near or below zero mean that the fixed-day linear model does not generalize beyond the held-out mean under blocked validation. Panel C shows the accuracy gain from adding climate to geometry at each observed-day stage. Panel D compares observed and predicted final main shape score for the day-4 region-blocked model, illustrating the weak conservative benchmark. Panel E documents the leakage audit: older fractional-stage variables normalized by final area or counted future pulses are excluded, and only fixed-day safe predictors are used here.",
        ),
    ]
    for fig_no, img, caption in figures:
        story.append(figure_flowable(fig_no, img, caption, st))
        if fig_no != figures[-1][0]:
            story.append(PageBreak())
    return story


def build_pdf() -> dict:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = make_doc(OUTPUT)
    story = build_story()
    doc.build(story)
    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "pdf": OUTPUT.as_posix(),
        "source_figures": MAIN_FIGURE_DIR.as_posix(),
        "figures": [
            (FIGURE_DIR / "figure_1.png").as_posix(),
            (FIGURE_DIR / "figure_2.png").as_posix(),
            (FIGURE_DIR / "figure_3.png").as_posix(),
            (FIGURE_DIR / "figure_4.png").as_posix(),
            (FIGURE_DIR / "figure_5.png").as_posix(),
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
