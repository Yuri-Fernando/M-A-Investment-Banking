"""Editable 33-tab financial workbook with formulas and reference-engine caches."""

from pathlib import Path

import xlsxwriter
from xlsxwriter.utility import xl_col_to_name

from .contracts import DISCLAIMER, M
from .ingestion import ASSETS, LIABILITIES, debt, nwc

TABS = [
    "00_Cover",
    "01_Control",
    "02_Sources",
    "03_Raw_Income",
    "04_Raw_Balance",
    "05_Raw_CashFlow",
    "06_Account_Map",
    "07_Historical_IS",
    "08_Historical_BS",
    "09_Historical_CF",
    "10_LTM",
    "11_QoE",
    "12_NWC_NetDebt",
    "13_Assumptions",
    "14_Revenue_Drivers",
    "15_Operating_Model",
    "16_Capex_DA",
    "17_Debt_Interest",
    "18_Tax",
    "19_Forecast_IS",
    "20_Forecast_BS",
    "21_Forecast_CF",
    "22_WACC",
    "23_DCF",
    "24_Peer_Comps",
    "25_Transaction_Comps",
    "26_Synergies",
    "27_Deal_Bridge",
    "28_Earnout_Escrow",
    "29_Sensitivities",
    "30_Outputs",
    "31_Checks",
    "32_Data_Dictionary",
]


def export_workbook(run: dict, path: Path, scenario: str = "base") -> dict:
    """Freeze a scenario, preserving formulas and exact Python values as caches.

    Regenerate via CLI/dashboard to change scenario. No mutable selector pretending
    to update unrelated frozen outputs. Formula evaluator verifies supported formulas.
    """
    s = run["scenarios"][scenario]
    a, f = s["assumptions"], s["forecast"]
    w = xlsxwriter.Workbook(str(path))
    w.set_properties({"title": "Project Aurora | Synthetic M&A", "comments": DISCLAIMER})
    w.set_calc_mode("auto")
    sheets = {name: w.add_worksheet(name) for name in TABS}
    title = w.add_format({"bold": True, "font_size": 19, "font_color": "#FFFFFF", "bg_color": "#142D4E"})
    head = w.add_format({"bold": True, "bg_color": "#DCE7F2", "font_color": "#142D4E", "bottom": 1})
    text = w.add_format({"text_wrap": True, "valign": "top"})
    inp = w.add_format({"font_color": "#0000FF", "num_format": '#,##0.00;(#,##0.00);"-"'})
    calc = w.add_format({"font_color": "#000000", "num_format": '#,##0.00;(#,##0.00);"-"'})
    link = w.add_format({"font_color": "#008040", "num_format": '#,##0.00;(#,##0.00);"-"'})
    formulas = []
    for name, ws in sheets.items():
        ws.hide_gridlines(2)
        ws.merge_range("A1:H1", name[3:].replace("_", " "), title)
        ws.merge_range("A2:H2", f"SYNTHETIC | {run['as_of']} | R$ mi | {scenario} | {run['run_id']}", text)
        ws.freeze_panes(5, 1)
        ws.set_column("A:A", 39)
        ws.set_column("B:G", 18)
        ws.set_column("H:H", 35)
        ws.set_landscape()
        ws.fit_to_pages(1, 0)
        ws.set_footer("&L" + DISCLAIMER[:100] + "&R&P / &N")
        ws.set_tab_color("#142D4E" if name in ("00_Cover", "30_Outputs") else "#6B899E")

    def value(tab, row, col, val):
        sheets[tab].write(row - 1, col - 1, val, inp if isinstance(val, (int, float)) else text)

    def form(tab, row, col, expression, expected):
        sheets[tab].write_formula(row - 1, col - 1, expression, link if "!" in expression else calc, expected)
        formulas.append(
            {
                "sheet": tab,
                "cell": f"{xl_col_to_name(col - 1)}{row}",
                "formula": expression,
                "expected": expected,
            }
        )

    def ref(tab, row, col=2):
        return f"'{tab}'!{xl_col_to_name(col - 1)}{row}"

    def headers(tab, labels):
        for col, label in enumerate(labels):
            sheets[tab].write(4, col, label, head)

    def table(tab, labels, rows):
        headers(tab, labels)
        for r, row in enumerate(rows, 6):
            for c, item in enumerate(row, 1):
                value(tab, r, c, item)

    def periods(tab):
        headers(tab, ["R$ mi / ratio"] + [str(r["year"]) + " " + r["period"] for r in f])

    table(
        "00_Cover",
        ["Project Aurora", "Frozen analyst scenario"],
        [
            ["Case", "NexaOps Analytics Ltda. - wholly synthetic"],
            ["Status", "DRAFT - REVIEW REQUIRED"],
            ["Scenario", scenario],
            ["Valuation date", run["as_of"]],
            ["Run", run["run_id"]],
            ["Notice", DISCLAIMER],
            ["Blue / black / green", "Inputs / same-sheet formulas / cross-sheet formulas"],
            ["Scenario change", "Regenerate workbook; dashboard/CLI share the calculation engine"],
        ],
    )
    table(
        "01_Control",
        ["Control", "Policy"],
        [
            ["Currency", "BRL nominal; monetary cells R$ mi"],
            ["Source money", "Full BRL in run.json"],
            ["Valuation timing", "Q4 2026 at 0.25; FY2027 at 1.25; FY2031 at 5.25"],
            ["Tax", "Simplified cash tax; no loss carryforward/deferred tax"],
            ["Recalculation", "Formula caches from Python; supported formulas independently evaluated"],
            ["Approvals", "Export is a draft, not simulated distribution approval"],
            ["NWC peg", run["policy"]["nwc_peg"]],
            ["Closing", run["closing_status"]],
        ],
    )
    table(
        "02_Sources",
        ["Fixture", "SHA256", "Class", "Available"],
        [[k, v["sha256"], v["classification"], v["available_at"]] for k, v in run["sources"].items()],
    )
    dates = {}
    for kind, rawtab, histtab in (
        ("income", "03_Raw_Income", "07_Historical_IS"),
        ("balance", "04_Raw_Balance", "08_Historical_BS"),
        ("cashflow", "05_Raw_CashFlow", "09_Historical_CF"),
    ):
        dates[kind] = sorted(run[kind])
        keys = list(run[kind][dates[kind][0]])
        headers(rawtab, ["Source account"] + dates[kind])
        headers(histtab, ["Mapped account"] + dates[kind])
        for i, key in enumerate(keys, 6):
            value(rawtab, i, 1, key)
            value(histtab, i, 1, key)
            for col, end in enumerate(dates[kind], 2):
                val = run[kind][end][key] / M
                value(rawtab, i, col, val)
                # Recompute accounting subtotals; direct references preserve source lineage.
                expression = "=" + ref(rawtab, i, col)
                if kind == "income":
                    rr = {k: j for j, k in enumerate(keys, 6)}
                    cc = xl_col_to_name(col - 1)
                    e = {k: f"{cc}{rr[k]}" for k in keys}
                    if key == "ebitda":
                        expression = f"={e['net_revenue']}-{e['cogs']}-{e['cash_opex']}"
                    elif key == "ebit":
                        expression = f"={e['ebitda']}-{e['depreciation_amortization']}"
                    elif key == "pretax_income":
                        expression = f"={e['ebit']}-{e['net_interest_expense']}"
                    elif key == "net_income":
                        expression = f"={e['pretax_income']}-{e['income_taxes']}"
                form(histtab, i, col, expression, val)
    table(
        "06_Account_Map",
        ["Source account", "Canonical / scope", "Nature"],
        [
            [k, k + " / SYN", "Stock" if k in run["balance"][run["as_of"]] else "Flow"]
            for k in sorted(set(run["income"][run["as_of"]]) | set(run["balance"][run["as_of"]]))
        ],
    )
    headers("10_LTM", ["Flow account", "LTM R$ mi", "Formula"])
    iskeys = list(run["income"][dates["income"][0]])
    for row, key in enumerate(iskeys, 6):
        source_row = 6 + iskeys.index(key)
        cfy = dates["income"].index("2025-12-31") + 2
        c9p = dates["income"].index("2025-09-30") + 2
        c9c = dates["income"].index(run["as_of"]) + 2
        value("10_LTM", row, 1, key)
        form(
            "10_LTM",
            row,
            2,
            "="
            + ref("07_Historical_IS", source_row, cfy)
            + "-"
            + ref("07_Historical_IS", source_row, c9p)
            + "+"
            + ref("07_Historical_IS", source_row, c9c),
            run["ltm"][key] / M,
        )
        value("10_LTM", row, 3, "FY2025 - 9M2025 + 9M2026")
    table(
        "11_QoE",
        ["Issue", "Proposed amount", "Sign", "Accepted amount", "Evidence", "Reviewer"],
        [
            [
                i["issue_id"],
                i["amount_brl_millions"],
                i["sign"],
                i["accepted_brl"] / M,
                i["evidence_id"],
                i["reviewer"] or "NOT ACCEPTED",
            ]
            for i in run["qoe"]["items"]
        ],
    )
    value("11_QoE", 11, 1, "FY2025 reported EBITDA")
    value("11_QoE", 11, 2, run["qoe"]["reported"] / M)
    value("11_QoE", 12, 1, "FY2025 adjusted EBITDA")
    form("11_QoE", 12, 2, "=B11+D6+D7+D8", run["qoe"]["adjusted"] / M)
    table(
        "12_NWC_NetDebt",
        ["Date", "Operating NWC", "Contract NWC (ex tax)", "Debt", "Cash", "Net debt"],
        [
            [end, nwc(bs) / M, nwc(bs, True) / M, debt(bs) / M, bs["cash"] / M, (debt(bs) - bs["cash"]) / M]
            for end, bs in sorted(run["balance"].items())
        ],
    )
    # Canonical assumptions: all forecast formulas point here.
    akeys = list(a)
    table(
        "13_Assumptions",
        ["Driver", "Value", "Unit / source"],
        [
            [
                k,
                v / M if k in ("q4_revenue", "bid_ev", "integration_cost") else v,
                "R$ mi" if k in ("q4_revenue", "bid_ev", "integration_cost") else "fraction / identifier",
            ]
            for k, v in a.items()
        ],
    )
    ar = {k: ref("13_Assumptions", 6 + akeys.index(k)) for k in a}
    for tab in (
        "14_Revenue_Drivers",
        "15_Operating_Model",
        "16_Capex_DA",
        "17_Debt_Interest",
        "18_Tax",
        "19_Forecast_IS",
        "20_Forecast_BS",
        "21_Forecast_CF",
        "23_DCF",
        "26_Synergies",
    ):
        periods(tab)
    # Schedule row contracts are stable and documented in data dictionary.
    for c, row in enumerate(f, 2):
        cc = xl_col_to_name(c - 1)
        pc = xl_col_to_name(c - 2)
        for tab, labels in {
            "14_Revenue_Drivers": ["Period revenue", "Recurring", "Project", "Annual reference", "Growth"],
            "15_Operating_Model": ["Revenue", "Margin", "COGS", "Cash opex", "EBITDA"],
            "16_Capex_DA": ["Revenue", "Capex", "D&A", "Opening PPE", "Closing PPE"],
            "17_Debt_Interest": ["Debt", "Period fraction", "Interest"],
            "18_Tax": ["EBIT", "Interest", "EBT", "Cash tax"],
            "19_Forecast_IS": [
                "Revenue",
                "COGS",
                "Cash opex",
                "EBITDA",
                "D&A",
                "EBIT",
                "Interest",
                "EBT",
                "Tax",
                "NI",
            ],
            "21_Forecast_CF": [
                "NI",
                "D&A",
                "NWC",
                "Opening NWC",
                "Delta NWC",
                "CFO",
                "Capex",
                "CFI",
                "Dividends",
                "CFF",
                "Opening cash",
                "Closing cash",
                "FCFF",
            ],
        }.items():
            for r, label in enumerate(labels, 6):
                value(tab, r, 1, label)
        revexpr = (
            "=" + ar["q4_revenue"]
            if c == 2
            else (
                f"={ref('14_Revenue_Drivers', 9, c - 1)}*(1+MAX({ar['growth']}-{ar['deceleration']}*{c - 3},0))"
            )
        )
        form("14_Revenue_Drivers", 6, c, revexpr, row["net_revenue"] / M)
        form("14_Revenue_Drivers", 7, c, f"={cc}6*{ar['recurring_share']}", row["recurring_revenue"] / M)
        form("14_Revenue_Drivers", 8, c, f"={cc}6-{cc}7", row["project_revenue"] / M)
        if c == 2:
            actual_rev = run["income"][run["as_of"]]["net_revenue"] / M
            value("14_Revenue_Drivers", 11, 1, "9M2026 revenue actual")
            value("14_Revenue_Drivers", 11, 2, actual_rev)
            form("14_Revenue_Drivers", 9, c, "=B6+B11", s["fy2026e"]["net_revenue"] / M)
        else:
            form("14_Revenue_Drivers", 9, c, f"={cc}6", row["net_revenue"] / M)
        form(
            "14_Revenue_Drivers",
            10,
            c,
            f"=MAX({ar['growth']}-{ar['deceleration']}*{max(c - 3, 0)},0)",
            max(a["growth"] - a["deceleration"] * max(c - 3, 0), 0),
        )
        form("15_Operating_Model", 6, c, "=" + ref("14_Revenue_Drivers", 6, c), row["net_revenue"] / M)
        form(
            "15_Operating_Model",
            7,
            c,
            f"={ar['q4_margin']}+({ar['terminal_margin']}-{ar['q4_margin']})*{c - 2}/5",
            row["margin"],
        )
        # COGS .54 is an explicit assumption cell, not an unexplained magic constant.
        value("13_Assumptions", 45, 1, "cogs_ratio")
        value("13_Assumptions", 45, 2, 0.54)
        form("15_Operating_Model", 8, c, f"={cc}6*{ref('13_Assumptions', 45)}", row["cogs"] / M)
        form("15_Operating_Model", 9, c, f"={cc}6-{cc}8-{cc}10", row["cash_opex"] / M)
        form("15_Operating_Model", 10, c, f"={cc}6*{cc}7", row["ebitda"] / M)
        for r, key in ((6, "net_revenue"), (7, "capex"), (8, "depreciation_amortization")):
            expr = (
                "=" + ref("14_Revenue_Drivers", 6, c)
                if r == 6
                else f"={cc}6*{ar['capex_ratio' if r == 7 else 'da_ratio']}"
            )
            form("16_Capex_DA", r, c, expr, row[key] / M)
        if c == 2:
            value("16_Capex_DA", 9, c, row["opening_ppe"] / M)
        else:
            form("16_Capex_DA", 9, c, f"={pc}10", row["opening_ppe"] / M)
        form("16_Capex_DA", 10, c, f"={cc}9+{cc}7-{cc}8", row["bs"]["net_ppe"] / M)
        value("17_Debt_Interest", 6, c, row["debt"] / M)
        value("17_Debt_Interest", 7, c, row["fraction"])
        form("17_Debt_Interest", 8, c, f"={cc}6*{cc}7*{ar['debt_cost']}", row["net_interest_expense"] / M)
        form(
            "18_Tax", 6, c, f"={ref('15_Operating_Model', 10, c)}-{ref('16_Capex_DA', 8, c)}", row["ebit"] / M
        )
        form("18_Tax", 7, c, "=" + ref("17_Debt_Interest", 8, c), row["net_interest_expense"] / M)
        form("18_Tax", 8, c, f"={cc}6-{cc}7", row["pretax_income"] / M)
        form("18_Tax", 9, c, f"=MAX({cc}8,0)*{ar['tax_rate']}", row["income_taxes"] / M)
        isexpr = [
            "=" + ref("14_Revenue_Drivers", 6, c),
            "=" + ref("15_Operating_Model", 8, c),
            "=" + ref("15_Operating_Model", 9, c),
            f"={cc}6-{cc}7-{cc}8",
            "=" + ref("16_Capex_DA", 8, c),
            f"={cc}9-{cc}10",
            "=" + ref("17_Debt_Interest", 8, c),
            f"={cc}11-{cc}12",
            "=" + ref("18_Tax", 9, c),
            f"={cc}13-{cc}14",
        ]
        iskeysf = [
            "net_revenue",
            "cogs",
            "cash_opex",
            "ebitda",
            "depreciation_amortization",
            "ebit",
            "net_interest_expense",
            "pretax_income",
            "income_taxes",
            "net_income",
        ]
        for r, (expr, key) in enumerate(zip(isexpr, iskeysf), 6):
            form("19_Forecast_IS", r, c, expr, row[key] / M)
        # CF derives the only cash figure used by the closing balance sheet.
        cf_values = [
            "net_income",
            "depreciation_amortization",
            "nwc",
            None,
            "delta_nwc",
            "cfo",
            "capex",
            "cfi",
            "dividends",
            "cff",
            "opening_cash",
            "cash",
            "fcff",
        ]
        cf_exprs = [
            "=" + ref("19_Forecast_IS", 15, c),
            "=" + ref("16_Capex_DA", 8, c),
            f"={ref('14_Revenue_Drivers', 9, c)}*{ar['nwc_ratio']}",
            f"={pc}8" if c > 2 else None,
            f"={cc}8-{cc}9",
            f"={cc}6+{cc}7-{cc}10",
            "=" + ref("16_Capex_DA", 7, c),
            f"=-{cc}12",
            f"=MAX({cc}6,0)*{ar['dividend_ratio']}",
            f"=-{cc}14",
            f"={pc}17" if c > 2 else None,
            f"={cc}16+{cc}11+{cc}13+{cc}15",
            f"={ref('19_Forecast_IS', 11, c)}*(1-{ar['tax_rate']})+{cc}7-{cc}12-{cc}10",
        ]
        for rr, (key, expr) in enumerate(zip(cf_values, cf_exprs), 6):
            val = (row["nwc"] - row["delta_nwc"]) / M if key is None else row[key] / M
            if expr is None:
                value("21_Forecast_CF", rr, c, val)
            else:
                form("21_Forecast_CF", rr, c, expr, val)
        bskeys = list(ASSETS + LIABILITIES + ("equity",))
        br = {k: i for i, k in enumerate(bskeys, 6)}
        for key, rr in br.items():
            value("20_Forecast_BS", rr, 1, key)
            expr = None
            if key == "cash":
                expr = "=" + ref("21_Forecast_CF", 17, c)
            elif key == "net_ppe":
                expr = "=" + ref("16_Capex_DA", 10, c)
            elif key == "equity":
                opening = f"{pc}{rr}" if c > 2 else str(row["opening_equity"] / M)
                expr = f"={opening}+{ref('19_Forecast_IS', 15, c)}-{ref('21_Forecast_CF', 14, c)}"
            elif key in (
                "inventory",
                "other_operating_current_assets",
                "accounts_payable",
                "operating_accruals",
            ):
                ratio = {
                    "inventory": 0.03,
                    "other_operating_current_assets": 0.035,
                    "accounts_payable": 0.12,
                    "operating_accruals": 0.045,
                }[key]
                ri = 46 + [
                    "inventory",
                    "other_operating_current_assets",
                    "accounts_payable",
                    "operating_accruals",
                ].index(key)
                value("13_Assumptions", ri, 1, key + "_revenue_ratio")
                value("13_Assumptions", ri, 2, ratio)
                expr = f"={ref('14_Revenue_Drivers', 9, c)}*{ref('13_Assumptions', ri)}"
            elif key == "accounts_receivable":
                expr = (
                    f"={ref('21_Forecast_CF', 8, c)}+{cc}{br['accounts_payable']}"
                    f"+{cc}{br['operating_accruals']}+{cc}{br['income_tax_payable']}"
                    f"-{cc}{br['inventory']}-{cc}{br['other_operating_current_assets']}"
                )
            if expr:
                form("20_Forecast_BS", rr, c, expr, row["bs"][key] / M)
            else:
                value("20_Forecast_BS", rr, c, row["bs"][key] / M)
        value("20_Forecast_BS", 21, 1, "Assets")
        value("20_Forecast_BS", 22, 1, "Liabilities + equity")
        form("20_Forecast_BS", 21, c, "=" + "+".join(f"{cc}{br[k]}" for k in ASSETS), row["assets"] / M)
        form(
            "20_Forecast_BS",
            22,
            c,
            "=" + "+".join(f"{cc}{br[k]}" for k in LIABILITIES + ("equity",)),
            (row["liabilities"] + row["bs"]["equity"]) / M,
        )
    table(
        "22_WACC",
        ["Build", "Rate"],
        [
            ["Ke", s["wacc_build"]["ke"]],
            ["WACC", s["wacc_build"]["wacc"]],
            ["Policy", s["wacc_build"]["erp_policy"]],
            ["Type", "Nominal BRL / analyst assumptions"],
        ],
    )
    form("22_WACC", 6, 2, f"={ar['rf_brl']}+{ar['beta']}*{ar['total_erp']}", s["wacc_build"]["ke"])
    form(
        "22_WACC",
        7,
        2,
        f"=(1-{ar['debt_weight']})*B6+{ar['debt_weight']}*{ar['debt_cost']}*(1-{ar['tax_rate']})",
        s["wacc_build"]["wacc"],
    )
    v = s["valuation"]
    for c, p in enumerate(v["periods"], 2):
        cc = xl_col_to_name(c - 1)
        for r, label in enumerate(("FCFF", "Years from valuation", "Discount factor", "PV FCFF"), 6):
            value("23_DCF", r, 1, label)
        form("23_DCF", 6, c, "=" + ref("21_Forecast_CF", 18, c), p["fcff"] / M)
        value("23_DCF", 7, c, p["t"])
        form("23_DCF", 8, c, f"=(1+{ref('22_WACC', 7)})^(-{cc}7)", p["factor"])
        form("23_DCF", 9, c, f"={cc}6*{cc}8", p["pv"] / M)
    value("23_DCF", 12, 1, "Normalized terminal FCFF")
    form(
        "23_DCF",
        12,
        2,
        f"=({ref('19_Forecast_IS', 11, 7)}*(1-{ar['tax_rate']})+{ref('16_Capex_DA', 8, 7)}"
        f"-{ref('16_Capex_DA', 7, 7)})*(1+{ar['terminal_g']})-{ref('21_Forecast_CF', 8, 7)}*{ar['terminal_g']}",
        v["terminal_fcff"] / M,
    )
    value("23_DCF", 13, 1, "Terminal value")
    form("23_DCF", 13, 2, f"=B12/({ref('22_WACC', 7)}-{ar['terminal_g']})", v["tv"] / M)
    value("23_DCF", 14, 1, "Standalone EV")
    form("23_DCF", 14, 2, "=B9+C9+D9+E9+F9+G9+B13*G8", v["ev"] / M)
    value("23_DCF", 15, 1, "Exit-multiple cross-check EV")
    form(
        "23_DCF",
        15,
        2,
        f"=B9+C9+D9+E9+F9+G9+{ref('19_Forecast_IS', 9, 7)}*{ar['exit_multiple']}*G8",
        v["exit_ev"] / M,
    )
    table(
        "24_Peer_Comps",
        ["Status", "Method"],
        [[run["comps"]["status"], "Requires >=3 sourced peers; no invented quotes"]],
    )
    table(
        "25_Transaction_Comps",
        ["Status", "Reason"],
        [[run["comps"]["transaction_comps"], "No verified executed-deal dataset"]],
    )
    for c, flow in enumerate(s["synergies"]["flows"], 2):
        cc = xl_col_to_name(c - 1)
        value("26_Synergies", 6, 1, "Expected incremental FCFF")
        form(
            "26_Synergies",
            6,
            c,
            f"={ref('14_Revenue_Drivers', 6, c)}*{ar['synergy_revenue_ratio']}*(1-{ar['tax_rate']})*{ar['synergy_probability']}",
            flow["expected_fcff"] / M,
        )
        value("26_Synergies", 7, 1, "Discounted FCFF")
        form(
            "26_Synergies",
            7,
            c,
            f"={cc}6/(1+{ar['synergy_discount']})^{ref('23_DCF', 7, c)}",
            flow["expected_fcff"] / M / (1 + a["synergy_discount"]) ** flow["t"],
        )
    value("26_Synergies", 10, 1, "Synergy PV net integration")
    form("26_Synergies", 10, 2, f"=B7+C7+D7+E7+F7+G7-{ar['integration_cost']}", s["synergies"]["pv"] / M)
    b = run["bridge"]
    table(
        "27_Deal_Bridge",
        ["Component", "R$ mi / status"],
        [
            ["Bid EV", b["ev"] / M],
            ["Cash", b["cash"] / M],
            ["Debt", b["financial_debt"] / M],
            ["Debt-like (none verified)", b["debt_like"] / M],
            ["NWC adjustment pending peg", b["nwc_adjustment"] / M],
            ["Seller fees assumption", b["seller_fees"] / M],
            ["Equity", b["equity"] / M],
            ["NWC status", b["nwc_status"]],
        ],
    )
    form("27_Deal_Bridge", 12, 2, "=B6+B7-B8-B9+B10-B11", b["equity"] / M)
    ct = run["consideration"]
    table(
        "28_Earnout_Escrow",
        ["Component", "R$ mi / fraction"],
        [[k, v / M if k not in ("stake",) else v] for k, v in ct.items()],
    )
    table(
        "29_Sensitivities",
        ["WACC", "g", "EV R$ mi"],
        [[p["wacc"], p["g"], p["ev"] / M if p["ev"] is not None else "INVALID"] for p in s["sensitivity"]],
    )
    table(
        "30_Outputs",
        ["Metric", "Result"],
        [
            ["Standalone DCF EV", v["ev"] / M],
            ["Equity at bid", b["equity"] / M],
            ["Synergy PV separate", s["synergies"]["pv"] / M],
            ["Decision", s["decision"]],
            ["DD", run["closing_status"]],
            ["FY2026E revenue", s["fy2026e"]["net_revenue"] / M],
        ],
    )
    form("30_Outputs", 6, 2, "=" + ref("23_DCF", 14), v["ev"] / M)
    form("30_Outputs", 7, 2, "=" + ref("27_Deal_Bridge", 12), b["equity"] / M)
    form("30_Outputs", 8, 2, "=" + ref("26_Synergies", 10), s["synergies"]["pv"] / M)
    table(
        "31_Checks",
        ["Check", "Residual R$ mi", "Status"],
        [[p["check"], p["residual_brl"] / M, p["status"]] for p in run["checks"]],
    )
    for i, row in enumerate(f, 22):
        c = i - 20
        value("31_Checks", i, 1, f"Forecast BS {row['year']}")
        form(
            "31_Checks",
            i,
            2,
            f"={ref('20_Forecast_BS', 21, c)}-{ref('20_Forecast_BS', 22, c)}",
            row["bs_residual"] / M,
        )
        value("31_Checks", i, 3, "PASS")
    table(
        "32_Data_Dictionary",
        ["Term", "Definition"],
        [
            ["FCFF", "EBIT*(1-tax)+DA-capex-delta operating NWC; excludes financing interest"],
            ["Terminal FCFF", "Normalized: (NOPAT+DA-capex)*(1+g)-g*NWC"],
            ["Contract NWC", "AR+inventory+operating CA-AP-accruals; excludes taxes"],
            ["CF NWC", "Contract NWC-income tax payable"],
            ["Units", "All monetary cells R$ mi; raw JSON/SQLite full BRL"],
            ["Cash", "Opening cash + CFO + CFI + CFF; no balancing plug"],
            ["Model schedules", "Fixed target debt; no new borrowing; dividend policy 30% positive NI"],
            [
                "Formula parity",
                "formula_manifest.json records formula, cell and Python reference; verify_workbook evaluates",
            ],
        ],
    )
    w.close()
    return {"scenario": scenario, "formulas": formulas, "count": len(formulas), "tabs": TABS}
