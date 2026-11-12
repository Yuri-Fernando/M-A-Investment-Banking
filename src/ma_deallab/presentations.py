"""Native editable PowerPoint financial presentations, rendered from frozen run metrics."""

from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.util import Inches, Pt

from .contracts import M
from .reporting import metric


def slide_content(run: dict) -> list[tuple]:
    """16 substantive CIM slides. Market/cohort gaps are stated, never invented."""
    s = run["scenarios"]["base"]
    return [
        (
            "Project Aurora",
            [
                "NexaOps Analytics Ltda. - synthetic industrial analytics case",
                "Confidential Information Memorandum | DRAFT",
                "Independent financial and transaction process simulation",
            ],
        ),
        (
            "Decision requires a price challenge",
            [
                "Base decision: " + s["decision"],
                f"Standalone EV R$ {metric(run, 'scenarios.base.valuation.ev')} mi versus bid R$ {metric(run, 'bridge.ev')} mi",
                "Open financial, commercial, tax and IP diligence conditions",
            ],
        ),
        (
            "Investment thesis",
            [
                "Industrial analytics capability and installed customer relationships",
                "Cross-selling is buyer-specific and outside standalone valuation",
                "Recurring mix remains a disclosed modelling assumption",
            ],
        ),
        (
            "Industry and competition",
            [
                "No verified TAM or market-share estimates included",
                "Public-company peer selection requires business-model comparability",
                "CVM data is separate from synthetic private-company facts",
            ],
        ),
        (
            "Business model",
            [
                "B2B analytics subscriptions plus implementation and project services",
                "Revenue split controlled by recurring_share assumption",
                "Customer-level churn/cohorts unavailable: do not infer retention",
            ],
        ),
        (
            "Commercial concentration",
            [
                "Top customer concentration is a synthetic risk-register observation",
                "Validate contract duration, renewal and change-of-control clauses",
                "Run downside before negotiating exclusivity",
            ],
        ),
        (
            "Financial history | R$ mi",
            [
                "FY statements and cumulative 9M kept separate",
                "Balance sheet, CF, debt, PPE and equity reconciled",
                "Source: synthetic_income_statement.csv",
            ],
            "history",
        ),
        (
            "LTM bridge",
            [
                f"Revenue R$ {metric(run, 'ltm.net_revenue')} mi",
                f"EBITDA R$ {metric(run, 'ltm.ebitda')} mi",
                "LTM = FY2025 - 9M2025 + 9M2026; never used on balance-sheet stocks",
            ],
        ),
        (
            "Quality of Earnings",
            [
                f"FY2025 reported R$ {metric(run, 'qoe.reported')} mi; accepted adjusted R$ {metric(run, 'qoe.adjusted')} mi",
                "Default proposed adjustments remain unaccepted",
                "Reviewer/evidence signoff is mandatory; FY adjustments do not silently change LTM",
            ],
        ),
        (
            "Cash, debt and working capital",
            [
                f"Financial net debt R$ {metric(run, 'net_debt')} mi",
                "Contract NWC excludes tax; cash-flow NWC includes tax payable",
                "No monthly history: normalized NWC peg remains unagreed",
            ],
        ),
        (
            "Business plan | R$ mi",
            [
                "Q4/2026 forecast is added to observed synthetic 9M",
                "Fixed target debt; explicit dividends and capex",
                "Full 2027-2031 forecast driven by one scenario contract",
            ],
            "forecast",
        ),
        (
            "DCF valuation and scenarios",
            [
                f"Nominal BRL WACC {metric(run, 'scenarios.base.valuation.wacc', False)}",
                f"Terminal growth {metric(run, 'scenarios.base.valuation.g', False)}",
                "Terminal FCFF normalizes NWC reinvestment; sensitivity available in workbook",
            ],
            "valuation",
        ),
        (
            "Buyer-specific synergy",
            [
                f"Expected finite-horizon synergy PV R$ {metric(run, 'scenarios.base.synergies.pv')} mi",
                "After-tax incremental FCFF, probability and separate discount rate",
                "Upfront integration cost paid regardless of realization; no terminal synergy",
            ],
        ),
        (
            "Price and contingent consideration",
            [
                f"Equity at bid R$ {metric(run, 'bridge.equity')} mi",
                f"Seller cash now R$ {metric(run, 'consideration.seller_cash_now')} mi",
                "Earnout PV is included in total consideration; escrow is withheld, not additive",
            ],
        ),
        (
            "Process and conditions",
            [
                "Two fictional buyer perspectives; no real outreach",
                "Stage: VAL_DRAFT; future timeline entries are planned simulations",
                "Closing blocked pending IC, DD, legal, tax, funding and NWC approvals",
            ],
        ),
        (
            "Sources and model limitations",
            [
                "All source hashes, metrics and exact engine version in run.json",
                "Public trading comps insufficient; executed deal comps unavailable",
                "No audit opinion, legal contract, financing commitment or real transaction",
            ],
        ),
    ]


def export_presentation(run: dict, path: Path, kind: str = "cim"):
    """Write editable shapes/text/chart PPTX. Management deck uses ten selected slides."""
    items = slide_content(run)
    if kind == "management":
        items = [items[i] for i in (0, 2, 4, 5, 6, 8, 10, 11, 14, 15)]
        cover_title, cover_body = items[0]
        items[0] = (
            cover_title,
            [
                line.replace("Confidential Information Memorandum", "Management Presentation")
                for line in cover_body
            ],
        )
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    navy = RGBColor.from_string("142D4E")
    teal = RGBColor.from_string("087E8B")
    muted = RGBColor.from_string("52657A")

    def box(slide, x, y, w, h, text, size=22, bold=False, color=navy):
        shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = shape.text_frame
        tf.word_wrap = True
        for i, line in enumerate(text.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            p.font.name = "Aptos"
            p.font.size = Pt(size)
            p.font.bold = bold
            p.font.color.rgb = color
            p.space_after = Pt(16)
        return shape

    for i, item in enumerate(items):
        title, body = item[:2]
        chart_type = item[2] if len(item) > 2 else None
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        sl.background.fill.solid()
        sl.background.fill.fore_color.rgb = RGBColor.from_string("F5F7FA")
        box(sl, 0.65, 0.25, 12, 0.4, "DEALLAB / PROJECT AURORA / SYNTHETIC", 12, True, teal)
        box(sl, 0.65, 1, 12, 1, title, 32, True)
        box(sl, 0.65, 2.2, 5.5 if chart_type else 11.8, 3.8, "\n".join(body), 22)
        if chart_type:
            chartdata = CategoryChartData()
            if chart_type == "history":
                years = ["2023-12-31", "2024-12-31", "2025-12-31"]
                chartdata.categories = ["FY2023", "FY2024", "FY2025"]
                chartdata.add_series("Revenue", [run["income"][y]["net_revenue"] / M for y in years])
                chartdata.add_series("EBITDA", [run["income"][y]["ebitda"] / M for y in years])
            elif chart_type == "forecast":
                rows = run["scenarios"]["base"]["forecast"]
                chartdata.categories = [str(r["year"]) + " " + r["period"] for r in rows]
                chartdata.add_series("Revenue", [r["net_revenue"] / M for r in rows])
                chartdata.add_series("EBITDA", [r["ebitda"] / M for r in rows])
            else:
                chartdata.categories = list(run["scenarios"])
                chartdata.add_series(
                    "Standalone EV", [s["valuation"]["ev"] / M for s in run["scenarios"].values()]
                )
            chart = sl.shapes.add_chart(
                XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(6.6), Inches(2.2), Inches(6), Inches(3.8), chartdata
            ).chart
            chart.has_legend = True
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
            chart.legend.include_in_layout = False
            chart.chart_style = 10
        box(
            sl,
            0.65,
            6.35,
            12,
            0.35,
            f"As-of {run['as_of']} | R$ mi | run {run['run_id']} | DRAFT - reviewer pending",
            11,
            False,
            muted,
        )
        box(
            sl,
            0.65,
            6.82,
            11.5,
            0.3,
            "SYNTHETIC - SIMULATED - NOT A REAL TRANSACTION. Not investment or legal advice.",
            10,
            False,
            muted,
        )
        box(sl, 12.2, 6.8, 0.5, 0.3, str(i + 1), 11, True, teal)
        sl.notes_slide.notes_text_frame.text = (
            f"Source run: {run['run_id']}. Refer to metrics_registry.json and input source hashes. "
            "Model results are illustrative assumptions, not market observations."
        )
    prs.core_properties.title = f"Project Aurora | {kind} | SYNTHETIC"
    prs.core_properties.subject = "Draft simulated investor materials"
    prs.save(path)
