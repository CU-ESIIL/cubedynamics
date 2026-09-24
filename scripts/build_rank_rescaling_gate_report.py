#!/usr/bin/env python3
"""Build the visual PDF for the rank-rescaling decision gate."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"artifacts"/"rank-rescaled-synchrony-gate"
OUTPUT=ROOT/"output"/"pdf"/"rank_rescaled_synchrony_decision_gate.pdf"
PAGE=landscape(letter)
BLUE=colors.HexColor("#123F70"); RED=colors.HexColor("#A5282D"); GREEN=colors.HexColor("#287A4B"); INK=colors.HexColor("#18212B")


def load(name): return json.loads((ART/name).read_text(encoding="utf-8"))


def fitted(path,width,height):
    with PILImage.open(path) as image: ratio=min(width/image.width,height/image.height)
    return Image(str(path),width=image.width*ratio,height=image.height*ratio)


def table(rows,widths=None,font=9):
    result=Table(rows,colWidths=widths,repeatRows=1,hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),BLUE),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTNAME",(0,1),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),font),("TEXTCOLOR",(0,1),(-1,-1),INK),
        ("GRID",(0,0),(-1,-1),.35,colors.HexColor("#AAB7C4")),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F6F8FA")]),
        ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ])); return result


def footer(canvas,doc):
    canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#CFD8E1")); canvas.line(.55*inch,.43*inch,PAGE[0]-.55*inch,.43*inch)
    canvas.setFont("Helvetica",8); canvas.setFillColor(colors.HexColor("#52606D")); canvas.drawString(.58*inch,.22*inch,"CubeDynamics - rank-rescaling decision gate - observed PRISM")
    canvas.drawRightString(PAGE[0]-.58*inch,.22*inch,str(doc.page)); canvas.restoreState()


def build():
    decision=load("decision_gate.json"); pair=load("one_pair_audit.json"); provenance=load("provenance.json")
    collapse=decision["collapse"]
    sites=list(csv.DictReader((ART/"scaling_sites.csv").open(encoding="utf-8")))
    examples=list(csv.DictReader((ART/"sample_grid_example_pairs.csv").open(encoding="utf-8")))
    styles=getSampleStyleSheet()
    title=ParagraphStyle("title",parent=styles["Title"],fontName="Helvetica-Bold",fontSize=27,leading=31,textColor=BLUE,alignment=TA_CENTER)
    subtitle=ParagraphStyle("subtitle",parent=styles["Normal"],fontSize=14,leading=18,textColor=INK,alignment=TA_CENTER)
    h1=ParagraphStyle("h1",parent=styles["Heading1"],fontName="Helvetica-Bold",fontSize=19,leading=23,textColor=BLUE,spaceAfter=8)
    h2=ParagraphStyle("h2",parent=styles["Heading2"],fontName="Helvetica-Bold",fontSize=12,leading=15,textColor=INK,spaceAfter=4)
    body=ParagraphStyle("body",parent=styles["BodyText"],fontSize=10.2,leading=14,textColor=INK,spaceAfter=7)
    small=ParagraphStyle("small",parent=body,fontSize=8.6,leading=11)
    stop=ParagraphStyle("stop",parent=body,fontName="Helvetica-Bold",fontSize=16,leading=20,textColor=RED,alignment=TA_CENTER,borderColor=RED,borderWidth=1,borderPadding=9,backColor=colors.HexColor("#FFF4F2"))
    good=ParagraphStyle("good",parent=body,fontName="Helvetica-Bold",fontSize=13,leading=17,textColor=GREEN,alignment=TA_CENTER,borderColor=GREEN,borderWidth=1,borderPadding=7,backColor=colors.HexColor("#F0FAF4"))
    code=ParagraphStyle("code",parent=body,fontName="Courier",fontSize=9,leading=12,backColor=colors.HexColor("#F2F4F6"),borderPadding=7)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(OUTPUT),pagesize=PAGE,leftMargin=.55*inch,rightMargin=.55*inch,topMargin=.48*inch,bottomMargin=.55*inch,title="Rank-rescaled synchrony decision gate",author="CubeDynamics project",subject="Audit of explicit temperature ranks versus current local-quantile Spearman synchrony")
    story=[]

    story += [Spacer(1,.35*inch),Paragraph("Rank-rescaled hot/cold synchrony",title),Paragraph("A mandatory redundancy gate before statewide computation",subtitle),Spacer(1,.25*inch),Paragraph("STOP BEFORE COLORADO",stop),Spacer(1,.25*inch),table([
        ["Gate result","Observed evidence"],
        ["Tail membership","0 changes across 400 real sample-grid pairs"],
        ["Cold / hot / Delta surfaces","Maximum absolute difference = 0.0"],
        ["Collapsed focal summaries","Cold, hot, pairwise Delta, and difference-of-medians all exactly unchanged"],
        ["Statewide decision","Do not create duplicate rank-labelled Colorado rasters"],
    ],widths=(2.5*inch,6.7*inch)),Spacer(1,.18*inch),Paragraph("The proposed location-specific rank representation is scientifically interpretable, but under the current 90-day median-tail and Spearman semantics it adds no new information on complete shared support.",body),PageBreak()]

    story += [Paragraph("1. Two different uses of ranks",h1),table([
        ["Operation","Where it occurs","Scientific role"],
        ["Existing Spearman ranks","After joint-tail dates are selected","Measure monotone dependence without retaining marginal scale"],
        ["Proposed temperature ranks","Before joint-tail dates are selected","Express each observation's relative position in its own location's reference distribution"],
        ["Rejected spatial ranks","Across pair effects before focal collapse","Would force every independently ranked neighborhood median to approximately 0.5"],
    ],widths=(2.1*inch,2.7*inch,4.5*inch)),Spacer(1,.2*inch),Paragraph("Audited empirical-rank convention",h2),Paragraph("U_i(t) = average_rank[T_i(t)] / (n_i + 1). Average ranks handle ties, and n+1 places finite coordinates strictly inside (0,1). Each pixel is transformed independently.",good),Spacer(1,.18*inch),Paragraph("The active temporal reference is the same inclusive 90-day window ending 2024-01-30. Current CubeDynamics does not apply a seasonal climatology in this experiment, so adding one would change a second methodological choice.",body),Paragraph("Cold uses U <= quantile(U, 0.5); hot uses U > quantile(U, 0.5). Applying the quantile to U is essential for preserving the existing tied-median boundary exactly.",body),PageBreak()]

    story += [Paragraph("2. Why the result should be invariant",h1),table([
        ["Step","Current method","Explicit rank method","Consequence"],
        ["Marginal tail threshold","Median of raw values","Median of monotone average-rank coordinates","Same selected dates, including ties"],
        ["Joint selection","Both locations in their own cold/hot set","Same","Same joint counts"],
        ["Dependence","Spearman on selected raw values","Spearman on selected rank coordinates","Same ranks within selected observations"],
        ["Spatial reduction","Median of nonself pair effects","Unchanged","Same focal output"],
    ],widths=(1.45*inch,2.45*inch,2.55*inch,2.8*inch)),Spacer(1,.2*inch),Paragraph("Qualification",h2),Paragraph("If locations had different missing-time masks, current production would recompute pair-valid thresholds. A once-per-pixel rank series over marginal support could then change membership by mixing a missing-data policy change into the experiment. The audited PRISM grid has zero missing TMIN and TMAX values, so this qualification does not apply here.",body),Paragraph("The correct comparison therefore preserves rank quantiles and the current inequalities; using the literal number 0.5 as a cutoff would change tied-median handling and would not isolate rank rescaling.",good),PageBreak()]

    cold=pair["tails"]["cold"]; hot=pair["tails"]["hot"]
    story += [Paragraph("3. One fully auditable real pair",h1),fitted(ART/"figures"/"one_pair_rank_audit.png",9.6*inch,4.8*inch),table([
        ["Tail","Raw thresholds A / B (°C)","Joint dates","Current S","Rank S","Difference"],
        ["Cold",f"{cold['location_a_raw_threshold']:.2f} / {cold['location_b_raw_threshold']:.2f}",str(cold["old_joint_count"]),f"{cold['old_synchrony']:.6f}",f"{cold['rank_synchrony']:.6f}",f"{cold['difference']:.1e}"],
        ["Hot",f"{hot['location_a_raw_threshold']:.2f} / {hot['location_b_raw_threshold']:.2f}",str(hot["old_joint_count"]),f"{hot['old_synchrony']:.6f}",f"{hot['rank_synchrony']:.6f}",f"{hot['difference']:.1e}"],
        ["Delta","cold - hot","-",f"{pair['old_delta']:.6f}",f"{pair['rank_delta']:.6f}",f"{pair['delta_difference']:.1e}"],
    ],widths=(1.05*inch,2.2*inch,1.2*inch,1.4*inch,1.4*inch,1.2*inch)),PageBreak()]

    story += [Paragraph("4. Complete center-reference surfaces before collapse",h1),fitted(ART/"figures"/"sample_grid_surfaces.png",9.65*inch,5.7*inch),Paragraph("Top: explicit per-location temperature ranks. Bottom: the current raw-quantile + Spearman implementation. The focal pixel is starred; audited comparison pixels are circled. The surfaces are visually and numerically identical.",small),PageBreak()]

    rows=[["Point","Distance km","Cold n","Hot n","Cold S","Hot S","Delta"]]
    for item in examples: rows.append([item["label"],f"{float(item['distance_km']):.1f}",item["cold_count"],item["hot_count"],f"{float(item['rank_cold']):.3f}",f"{float(item['rank_hot']):.3f}",f"{float(item['rank_delta']):+.3f}"])
    story += [Paragraph("5. What is being collapsed",h1),table(rows,widths=(1.3*inch,1.2*inch,1.1*inch,1.1*inch,1.2*inch,1.2*inch,1.2*inch)),Spacer(1,.2*inch),Paragraph("Immediate non-stacked reduction",h2),table([
        ["Focal summary","Current","Explicit rank","Difference"],
        ["Median cold",f"{collapse['old']['cold']:.6f}",f"{collapse['rank']['cold']:.6f}",f"{collapse['difference']['cold']:.1e}"],
        ["Median hot",f"{collapse['old']['hot']:.6f}",f"{collapse['rank']['hot']:.6f}",f"{collapse['difference']['hot']:.1e}"],
        ["Median pairwise Delta",f"{collapse['old']['delta']:.6f}",f"{collapse['rank']['delta']:.6f}",f"{collapse['difference']['delta']:.1e}"],
        ["Cold median - hot median",f"{collapse['old']['delta_medians']:.6f}",f"{collapse['rank']['delta_medians']:.6f}","0.0e+00"],
    ],widths=(3.0*inch,1.8*inch,1.8*inch,1.6*inch)),Spacer(1,.18*inch),Paragraph("The center-to-center relationship was excluded: 399 nonself pair effects entered each focal reduction.",good),PageBreak()]

    story += [Paragraph("6. Old versus explicit rank: identity, not rescaling",h1),fitted(ART/"figures"/"old_vs_rank_sample_grid.png",9.65*inch,3.0*inch),table([
        ["Metric","Pearson","Spearman","RMSE","Median difference","Difference IQR","Max |difference|"],
        *[[name.title(),f"{decision['comparison'][name]['pearson']:.6f}",f"{decision['comparison'][name]['spearman']:.6f}",f"{decision['comparison'][name]['rmse']:.1e}",f"{decision['comparison'][name]['median_difference']:.1e}",f"{decision['comparison'][name]['difference_iqr']:.1e}",f"{decision['comparison'][name]['maximum_absolute_difference']:.1e}"] for name in ("cold","hot","delta")]
    ],widths=(1.2*inch,1.2*inch,1.2*inch,1.15*inch,1.45*inch,1.25*inch,1.45*inch)),Spacer(1,.12*inch),Paragraph(f"The recomputed current surface also matches the validated Phase 1 checkpoint to 5.8×10^-8; that residual is only the checkpoint's float32 storage precision.",small),PageBreak()]

    story += [Paragraph("7. Global-scaling motivation: useful interpretation, no new statistic here",h1),fitted(ART/"figures"/"global_scaling_diagnostic.png",9.65*inch,4.65*inch),Paragraph("Four Colorado sites span raw median temperatures from " + f"{min(float(s['raw_median_c']) for s in sites):.1f}°C to {max(float(s['raw_median_c']) for s in sites):.1f}°C, yet every empirical-rank median is 0.5. Ranks make relative extremeness comparable across marginal climates, but current local quantiles already define hot and cold relatively, and Spearman already removes monotone scale in the dependence statistic.",body),Paragraph("Ranks do not preserve absolute climate state: a mountain-site 95th percentile and a warm low-elevation 95th percentile share relative position while representing different temperatures. This remains a reference-frame limitation for CONUS/global work.",small),PageBreak()]

    story += [Paragraph("8. Why pair-effect spatial ranking was not mapped",h1),table([
        ["Within-neighborhood operation","Observed median rank"],
        ["Rank all cold pair effects independently for this focal pixel",f"{collapse['within_neighborhood_rank_median']['cold']:.1f}"],
        ["Rank all hot pair effects independently for this focal pixel",f"{collapse['within_neighborhood_rank_median']['hot']:.1f}"],
        ["Rank all Delta pair effects independently for this focal pixel",f"{collapse['within_neighborhood_rank_median']['delta']:.1f}"],
    ],widths=(6.1*inch,2.2*inch)),Spacer(1,.2*inch),Paragraph("This is true by construction: independently ranking every focal neighborhood makes its median rank approximately 0.5. A statewide map would therefore be constant or nearly constant and scientifically empty.",stop),Spacer(1,.2*inch),Paragraph("A meaningful spatial-rank map would need an external reference population - for example all Colorado pair effects, distance-conditioned effects, or a justified regional distribution. No such reference was specified, so no spatial-rank raster was created.",body),PageBreak()]

    story += [Paragraph("9. Decision and deliverables",h1),Paragraph("STOP BEFORE COLORADO",stop),Spacer(1,.2*inch),table([
        ["Question","Answer"],
        ["Does explicit rank rescaling change tail membership?","No: zero changes across all 400 sample-grid pairs."],
        ["Does it change cold, hot, or Delta?","No: all pair effects and collapsed summaries are exactly identical."],
        ["Why?","Local median tails already use relative position; Spearman already uses ranks."],
        ["Is the implementation scientifically interpretable?","Yes, and it behaves as expected."],
        ["Is it nonredundant?","No. The mandatory statewide gate fails."],
        ["Were Colorado rank rasters created?","No. Relabelling duplicate rasters would add complexity without information."],
    ],widths=(3.0*inch,6.2*inch)),Spacer(1,.18*inch),Paragraph("The completed non-stacked Colorado baseline remains the correct statewide product. A future experiment must change one scientifically meaningful choice - such as seasonal anomaly reference, tail probability, missing-support policy, or an externally referenced spatial rank - and test that choice separately.",body),Paragraph("Reproduce",h2),Paragraph("MPLCONFIGDIR=/tmp/cubedynamics-mpl .venv/bin/python scripts/run_rank_rescaling_gate.py",code),Paragraph("Machine-readable evidence: implementation_note.md, one_pair_observations.csv, one_pair_audit.json, sample_grid_rank_gate.nc, sample_grid_collapse.json, sample_grid_example_pairs.csv, scaling_sites.csv, summary.csv, decision_gate.json, and provenance.json.",small)]

    doc.build(story,onFirstPage=footer,onLaterPages=footer); return OUTPUT


if __name__=="__main__": print(build())
