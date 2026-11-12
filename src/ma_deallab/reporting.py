"""Draft investor materials generated from the shared frozen metrics registry."""

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from .contracts import DISCLAIMER, M

NAVY = colors.HexColor("#142D4E")


def metric(run: dict, path: str, money: bool = True) -> str:
    """Resolve report numeric claims through the registry; includes evidence path."""
    v = run["metrics"][path]["value"]
    return f"{v / M:,.2f}" if money else f"{v:.2%}"


def table_data(run: dict, scenario: str = "base") -> list:
    """Display-only rounding; all source calculations stay full precision."""
    return [
        ["Metric (R$ mi)", "Value", "Evidence path"],
        ["Revenue LTM", metric(run, "ltm.net_revenue"), "ltm.net_revenue"],
        ["EBITDA LTM", metric(run, "ltm.ebitda"), "ltm.ebitda"],
        ["Financial net debt", metric(run, "net_debt"), "net_debt"],
        [
            "Standalone DCF EV",
            metric(run, f"scenarios.{scenario}.valuation.ev"),
            f"scenarios.{scenario}.valuation.ev",
        ],
        ["Bid EV", metric(run, "bridge.ev"), "bridge.ev"],
        ["Equity at bid", metric(run, "bridge.equity"), "bridge.equity"],
    ]


def sections(run: dict, kind: str) -> list:
    """Content for IC/DD/valuation/closing; each page has a distinct analytical purpose."""
    base = run["scenarios"]["base"]
    common = (
        "All private-company observations are synthetic. Forecast and discount assumptions "
        "are analyst illustrations, not contemporaneous market observations. "
        f"Metrics registry and exact source hashes accompany run {run['run_id']}."
    )
    summary = table_data(run)
    scenarios = [["Scenario", "Standalone EV R$ mi", "Decision"]] + [
        [name, metric(run, f"scenarios.{name}.valuation.ev"), s["decision"]]
        for name, s in run["scenarios"].items()
    ]
    risk_table = [["Issue", "Severity / status", "Next step"]] + [
        [r["issue_id"], r["severity"] + " / " + r["status"], r["recommended_action"]] for r in run["risks"]
    ]
    forecast = [["Period", "Revenue", "EBITDA", "FCFF", "End cash"]] + [
        [str(row["year"]) + " " + row["period"]]
        + [
            metric(run, f"scenarios.base.forecast.{i}.{key}")
            for key in ("net_revenue", "ebitda", "fcff", "cash")
        ]
        for i, row in enumerate(base["forecast"])
    ]
    provenance = [["Source", "SHA256 prefix", "Available at"]] + [
        [name, s["sha256"][:20], s["available_at"]] for name, s in run["sources"].items()
    ]
    if kind == "ic":
        return [
            (
                "Investment committee | decision",
                [
                    "Recommendation: " + base["decision"] + " (case-specific analytical rule; unapproved).",
                    f"Base standalone DCF EV: R$ {metric(run, 'scenarios.base.valuation.ev')} mi; "
                    f"illustrative bid: R$ {metric(run, 'bridge.ev')} mi.",
                    "Do not justify the bid by silently adding buyer synergies. Require re-pricing or a separately approved thesis.",
                    common,
                ],
                summary,
            ),
            (
                "Scenario challenge and acquisition thesis",
                [
                    "Strategic thesis: industrial analytics IP and cross-selling; test customer retention and integration feasibility.",
                    "Financial sponsor thesis: recurring revenue and cash conversion; acquisition financing is not committed.",
                    "Negative cash requires explicit financing; no automatic debt or cash balancing plug.",
                    "Decision rule: EV < 80% of bid = WALK_AWAY; below bid = RENEGOTIATE; otherwise PROCEED_CONDITIONAL.",
                ],
                scenarios,
            ),
            (
                "Diligence and negotiation conditions",
                [
                    "No final approval while high-severity DD remains unresolved.",
                    "Monthly NWC is unavailable: agree a defensible peg after monthly evidence, not a fabricated average.",
                    "QoE items are proposed by default. FY2025 acceptance never changes LTM automatically.",
                    "Tax exposure remains a legal review item, not an automatic R$ deduction.",
                ],
                risk_table,
            ),
            (
                "Price, funding and evidence",
                [
                    f"Equity at bid: R$ {metric(run, 'bridge.equity')} mi; seller cash now: "
                    f"R$ {metric(run, 'consideration.seller_cash_now')} mi.",
                    f"Earnout expected PV R$ {metric(run, 'consideration.earnout_pv')} mi is included in the price; "
                    f"maximum nominal payout R$ {metric(run, 'consideration.earnout_cap')} mi.",
                    "Escrow is withheld consideration. Simulated closing is blocked pending IC, legal, tax, funding, DD and NWC terms.",
                    "Approval request: review the frozen assumptions, downside and price before any simulated advancement.",
                ],
                provenance,
            ),
        ]
    if kind == "dd":
        q = [["Issue", "Amount R$ mi", "Review", "Evidence"]] + [
            [
                i["issue_id"],
                f"{i['accepted_brl'] / M:,.2f}",
                "ACCEPTED" if i["accepted"] else "PROPOSED / RISK",
                i["evidence_id"],
            ]
            for i in run["qoe"]["items"]
        ]
        return [
            (
                "Financial DD | scope and limitations",
                [common, "No audit opinion or actual client diligence is asserted."],
                summary,
            ),
            (
                "Quality of Earnings",
                [
                    f"FY2025 reported EBITDA R$ {metric(run, 'qoe.reported')} mi; "
                    f"accepted adjusted EBITDA R$ {metric(run, 'qoe.adjusted')} mi.",
                    "ERP add-back requires non-recurrence evidence. Founder compensation requires replacement-cost support.",
                    "Customer concentration affects forecast risk, not an arbitrary EBITDA add-back.",
                ],
                q,
            ),
            (
                "Cash conversion and capital expenditure",
                [
                    "Indirect CF is recalculated from NI, D&A and operating NWC changes.",
                    "PPE = opening PPE + capex - D&A. Capitalized software treatment remains an open policy review.",
                    "No 2023 cash-flow claim without 2022 opening balance sheet.",
                ],
                forecast,
            ),
            (
                "Working capital and net debt",
                [
                    f"Operating NWC: R$ {metric(run, 'operating_nwc')} mi; contract illustration excluding tax: "
                    f"R$ {metric(run, 'contract_nwc')} mi.",
                    "Completion accounts require closing NWC and an agreed peg together. Locked-box uses a separate fixed-price mechanism.",
                    "No monthly NWC history is available. No seasonal peg or tax liability reclassification is inferred.",
                    "Cash/debt amounts are as-of balances, not verified closing balances.",
                ],
                [
                    ["Control", "Status"],
                    ["NWC peg", "UNAGREED"],
                    ["Debt-like", "None verified; conditional tax review"],
                    ["Price true-up", "Not applied"],
                ],
            ),
            (
                "Red flags and required evidence",
                [
                    "Assign financial/commercial/legal owners. Request customer contracts, AR aging, tax opinion and IP assignments.",
                    "High or unknown material risks block a no-conditions simulated close.",
                ],
                risk_table,
            ),
            (
                "Evidence appendix",
                [
                    "Local CSV row/account/date keys identify original financial facts. Metrics registry identifies transformations.",
                    "All materials remain drafts for reviewer signoff.",
                ],
                provenance,
            ),
        ]
    if kind == "valuation":
        return [
            (
                "Valuation | standalone economics",
                [common, "FCFF excludes interest, while WACC includes financing costs."],
                summary,
            ),
            (
                "Forecast and discount convention",
                [
                    f"Nominal BRL WACC {metric(run, 'scenarios.base.valuation.wacc', False)}; "
                    f"terminal growth {metric(run, 'scenarios.base.valuation.g', False)}.",
                    "Q4 2026 discounted at 0.25 years; complete 2027 at 1.25; complete 2031 at 5.25.",
                    "Terminal FCFF normalizes NWC reinvestment to g times final NWC; no cash flow after 2031 is assumed without terminal normalization.",
                ],
                forecast,
            ),
            (
                "Scenario range, synergy and comparables",
                [
                    f"Separate finite-horizon expected synergy PV: R$ {metric(run, 'scenarios.base.synergies.pv')} mi.",
                    "Integration cost is paid upfront regardless of realization; no perpetual synergy is assumed.",
                    "Trading comps: "
                    + run["comps"]["status"]
                    + ". Executed transaction comps: "
                    + run["comps"]["transaction_comps"],
                    "Do not interpret the scenario range as a confidence interval or real bid recommendation.",
                ],
                scenarios,
            ),
            (
                "Inputs, limitations and provenance",
                [
                    "Risk-free, beta, total local ERP, debt cost and target weights are explicit illustrative assumptions.",
                    "Country risk is already included in total local ERP; there is no additional CRP.",
                    "Historical fixtures available at synthetic cutoff; report generation date is separate from valuation date.",
                ],
                provenance,
            ),
        ]
    if kind == "closing":
        return [
            (
                "Closing packet | BLOCKED simulation",
                [
                    DISCLAIMER,
                    run["closing_status"],
                    "Economic illustration only. No legal signatures, real approvals or actual closing.",
                ],
                summary,
            ),
            (
                "Funds flow and contingent consideration",
                [
                    "EV, equity consideration, cash at closing and maximum nominal payout are distinct.",
                    "Only a 100% secondary share acquisition is illustrated by the default packet.",
                    "No acquisition debt financing is assumed committed.",
                ],
                [["Component", "R$ mi"]]
                + [[k, f"{v / M:,.2f}"] for k, v in run["consideration"].items() if k != "stake"],
            ),
            (
                "Conditions and integration plan",
                [
                    "IC / legal / tax / funding / DD / NWC terms: pending reviewer evidence.",
                    "Days 1-30: customer retention and founder/IP continuity.",
                    "Days 31-60: validate finance/technology integration and synergy costs.",
                    "Days 61-100: compare retention, cash conversion and realized synergy against approved plan.",
                ],
                [["Condition", "Status"]]
                + [[k, "PENDING"] for k in ("IC", "Legal", "Tax", "Funding", "DD", "NWC terms")],
            ),
        ]
    raise ValueError(kind)


def write_pdf(run: dict, path: Path, kind: str):
    """ReportLab paginated PDF with repeated source/run footnotes and editable source JSON."""
    styles = getSampleStyleSheet()
    styles["Title"].textColor = NAVY
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 15
    doc = SimpleDocTemplate(
        str(path),
        pagesize=(21 * cm, 29.7 * cm),
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.6 * cm,
        bottomMargin=2.0 * cm,
        title=f"Project Aurora - {kind} - SYNTHETIC",
        author="DealLab analyst demo",
    )
    story = []
    for i, (title, paragraphs, rows) in enumerate(sections(run, kind)):
        if i:
            story.append(PageBreak())
        story.append(Paragraph(escape(title), styles["Title"]))
        story.append(Paragraph(f"SYNTHETIC | as-of {run['as_of']} | DRAFT | R$ mi", styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))
        for p in paragraphs:
            story.append(Paragraph(escape(p), styles["BodyText"]))
            story.append(Spacer(1, 0.3 * cm))
        if rows:
            cells = [[Paragraph(escape(str(v)), styles["BodyText"]) for v in row] for row in rows]
            width = 17.8 * cm / len(rows[0])
            tab = Table(cells, colWidths=[width] * len(rows[0]), repeatRows=1, hAlign="LEFT")
            tab.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE7F2")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, NAVY),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5F8")]),
                    ]
                )
            )
            story.append(tab)

    def footer(canvas, document):
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(NAVY)
        canvas.drawString(
            1.6 * cm,
            1.3 * cm,
            f"Run {run['run_id']} | DRAFT - reviewer approval pending | page {document.page}",
        )
        canvas.drawString(
            1.6 * cm,
            0.9 * cm,
            "SYNTHETIC - SIMULATED - NOT A REAL TRANSACTION. Not investment or legal advice.",
        )

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def write_teaser(run: dict, path: Path):
    """Anonymous buyer-facing one-page PDF; no target or fictional buyer identities."""
    styles = getSampleStyleSheet()
    story = [
        Paragraph("PROJECT AURORA", styles["Title"]),
        Paragraph("Brazilian industrial analytics | anonymous opportunity illustration", styles["Heading2"]),
        Spacer(1, 20),
    ]
    for p in [
        "Synthetic B2B software and integration services case. Potential secondary share sale, subject to review.",
        f"LTM revenue R$ {metric(run, 'ltm.net_revenue')} mi | EBITDA R$ {metric(run, 'ltm.ebitda')} mi.",
        "Investment thesis: analytics capability, recurring business mix and cross-selling potential.",
        "Risks: customer concentration, receivables collectability, founder retention and IP.",
        "Process: approved teaser, simulated NDA, CIM review, indicative offers, diligence and conditional negotiation.",
        "DRAFT - Not approved for simulated distribution. Financial evidence: ltm.net_revenue and ltm.ebitda.",
        "Source run: " + run["run_id"] + "; numerical evidence in accompanying metrics registry.",
        DISCLAIMER,
    ]:
        story += [Paragraph(escape(p), styles["BodyText"]), Spacer(1, 15)]
    # Deliberately omit target name and original source filenames; run hash preserves lineage.
    SimpleDocTemplate(str(path), title="Project Aurora anonymous synthetic teaser").build(story)


def write_markdown(run: dict, path: Path, kind: str):
    lines = [
        f"# Project Aurora | {kind}",
        "",
        DISCLAIMER,
        "",
        f"As-of {run['as_of']} | Run {run['run_id']} | DRAFT_REVIEW_REQUIRED",
        "",
    ]
    for title, paragraphs, rows in sections(run, kind):
        lines += ["## " + title, ""] + [p + "\n" for p in paragraphs]
        if rows:
            lines += [
                "| " + " | ".join(str(v) for v in rows[0]) + " |",
                "| " + " | ".join("---" for _ in rows[0]) + " |",
            ]
            lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in rows[1:]]
        lines += [""]
    path.write_text("\n".join(lines), encoding="utf-8")
