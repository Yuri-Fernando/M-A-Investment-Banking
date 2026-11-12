"""Integrated forecast and dated FCFF valuation. All amounts are full BRL."""

from dataclasses import replace
from math import isfinite

from .contracts import AS_OF, Assumptions, ModelError
from .ingestion import ASSETS, LIABILITIES, balance_check, close, debt, nwc


def forecast(case: dict, a: Assumptions) -> list[dict]:
    """Q4 2026 then FY2027-31. Debt stays fixed, dividends follow payout policy.

    NWC uses a ratio, allocated across AR/inventory/prepaids and AP/accruals.
    Tax payable is held flat, avoiding a tax cash-flow double count. Cash is
    derived from CF; negative cash is a warning/block, never a balancing plug.
    """
    bs = dict(case["balance"][AS_OF])
    previous_revenue = case["income"][AS_OF]["net_revenue"] + a.q4_revenue
    rows = []
    for step, year in enumerate(range(2026, 2032)):
        stub = step == 0
        fraction = 0.25 if stub else 1.0
        opening = dict(bs)
        revenue = (
            a.q4_revenue if stub else previous_revenue * (1 + max(a.growth - a.deceleration * (step - 1), 0))
        )
        margin = a.q4_margin if stub else a.q4_margin + (a.terminal_margin - a.q4_margin) * step / 5
        cogs = revenue * 0.54
        ebitda = revenue * margin
        cash_opex = revenue - cogs - ebitda
        da = revenue * a.da_ratio
        ebit = ebitda - da
        interest = debt(opening) * a.debt_cost * fraction
        ebt = ebit - interest
        tax = max(ebt, 0) * a.tax_rate
        ni = ebt - tax
        capex = revenue * a.capex_ratio
        annual_revenue = previous_revenue if stub else revenue
        target_nwc = annual_revenue * a.nwc_ratio
        # Construct accounts from an explicit operating balance policy.
        # Financial NWC includes fixed income tax payable.
        bs["inventory"] = annual_revenue * 0.03
        bs["other_operating_current_assets"] = annual_revenue * 0.035
        bs["accounts_payable"] = annual_revenue * 0.12
        bs["operating_accruals"] = annual_revenue * 0.045
        bs["accounts_receivable"] = (
            target_nwc
            + bs["accounts_payable"]
            + bs["operating_accruals"]
            + bs["income_tax_payable"]
            - bs["inventory"]
            - bs["other_operating_current_assets"]
        )
        delta_nwc = nwc(bs) - nwc(opening)
        cfo = ni + da - delta_nwc
        cfi = -capex
        dividends = max(ni, 0) * a.dividend_ratio
        cff = -dividends
        bs["net_ppe"] = opening["net_ppe"] + capex - da
        bs["equity"] = opening["equity"] + ni - dividends
        bs["cash"] = opening["cash"] + cfo + cfi + cff
        fcff = ebit * (1 - a.tax_rate) + da - capex - delta_nwc
        row = {
            "year": year,
            "period": "Q4E" if stub else "FYF",
            "fraction": fraction,
            "discount_year": 0.25 + step,
            "net_revenue": revenue,
            "recurring_revenue": revenue * a.recurring_share,
            "project_revenue": revenue * (1 - a.recurring_share),
            "margin": margin,
            "cogs": cogs,
            "cash_opex": cash_opex,
            "ebitda": ebitda,
            "depreciation_amortization": da,
            "ebit": ebit,
            "net_interest_expense": interest,
            "pretax_income": ebt,
            "income_taxes": tax,
            "net_income": ni,
            "capex": capex,
            "nwc": nwc(bs),
            "contract_nwc": nwc(bs, True),
            "delta_nwc": delta_nwc,
            "cfo": cfo,
            "cfi": cfi,
            "cff": cff,
            "dividends": dividends,
            "opening_cash": opening["cash"],
            "cash": bs["cash"],
            "debt": debt(bs),
            "opening_ppe": opening["net_ppe"],
            "opening_equity": opening["equity"],
            "fcff": fcff,
            "bs": dict(bs),
            "bs_residual": balance_check(bs),
            "assets": sum(bs[k] for k in ASSETS),
            "liabilities": sum(bs[k] for k in LIABILITIES),
        }
        close(row["bs_residual"], 0, f"forecast BS {year}")
        close(row["cash"] - row["opening_cash"], cfo + cfi + cff, f"forecast CF {year}")
        if bs["net_ppe"] < 0:
            raise ModelError("Negative PPE: D&A exceeds available capital")
        rows.append(row)
        if not stub:
            previous_revenue = revenue
    return rows


def dcf(rows: list[dict], wacc: float, g: float, exit_multiple: float = 8.0) -> dict:
    """End-period convention: Q4 at t=.25, FY2027 at 1.25, FY2031 at 5.25.

    TV uses a normalized terminal FCFF: NOPAT + DA - capex - g*NWC.
    This replaces final explicit-year delta NWC with terminal growth investment.
    """
    if not all(isfinite(v) for v in (wacc, g, exit_multiple)) or wacc <= g or g < 0 or exit_multiple < 0:
        raise ModelError("WACC_CHECK: finite WACC > g >= 0 and exit multiple >= 0 required")
    if not rows:
        raise ModelError("No forecast")
    last = rows[-1]
    tax_rate = last["model_tax_rate"]
    terminal_fcff = (last["ebit"] * (1 - tax_rate) + last["depreciation_amortization"] - last["capex"]) * (
        1 + g
    ) - last["nwc"] * g
    if terminal_fcff <= 0:
        raise ModelError("NEGATIVE_TERMINAL_FCFF: revise sustainable margins/reinvestment")
    tv = terminal_fcff / (wacc - g)
    periods = [
        {
            "year": r["year"],
            "t": r["discount_year"],
            "fcff": r["fcff"],
            "factor": (1 + wacc) ** -r["discount_year"],
            "pv": r["fcff"] / (1 + wacc) ** r["discount_year"],
        }
        for r in rows
    ]
    pv_explicit = sum(p["pv"] for p in periods)
    pv_tv = tv / (1 + wacc) ** last["discount_year"]
    exit_ev = pv_explicit + last["ebitda"] * exit_multiple / (1 + wacc) ** last["discount_year"]
    return {
        "ev": pv_explicit + pv_tv,
        "terminal_fcff": terminal_fcff,
        "tv": tv,
        "pv_terminal": pv_tv,
        "pv_explicit": pv_explicit,
        "terminal_share": pv_tv / (pv_explicit + pv_tv),
        "exit_ev": exit_ev,
        "wacc": wacc,
        "g": g,
        "periods": periods,
        "terminal_policy": "Normalized reinvestment: delta NWC = g * final NWC",
    }


def model(case: dict, a: Assumptions) -> dict:
    """Run scenario, including FY2026E summary; negative cash blocks export."""
    rows = forecast(case, a)
    for row in rows:
        row["model_tax_rate"] = a.tax_rate
    valuation = dcf(rows, a.wacc, a.terminal_g, a.exit_multiple)
    actual = case["income"][AS_OF]
    annual_2026 = {key: actual[key] + rows[0][key] for key in actual}
    return {
        "forecast": rows,
        "fy2026e": annual_2026,
        "valuation": valuation,
        "warnings": [f"FINANCING_REQUIRED {r['year']}: negative cash" for r in rows if r["cash"] < 0],
        "assumptions": a,
    }


def sensitivity(rows: list[dict], a: Assumptions) -> list[dict]:
    """WACC +/- 3pp, g +/- 1pp. Invalid cells remain explicitly unavailable."""
    result = []
    for dw in (-0.03, -0.02, -0.01, 0, 0.01, 0.02, 0.03):
        for dg in (-0.01, -0.005, 0, 0.005, 0.01):
            w, g = a.wacc + dw, a.terminal_g + dg
            result.append(
                {"wacc": w, "g": g, "ev": dcf(rows, w, g, a.exit_multiple)["ev"] if w > g >= 0 else None}
            )
    return result


def operating_stress(case: dict, a: Assumptions) -> list[dict]:
    """Independent operating changes with all other assumptions fixed."""
    cases = [
        ("growth -3pp", replace(a, growth=max(a.growth - 0.03, 0))),
        ("growth +3pp", replace(a, growth=a.growth + 0.03)),
        ("margin -2pp", replace(a, terminal_margin=max(a.terminal_margin - 0.02, 0))),
        ("margin +2pp", replace(a, terminal_margin=min(a.terminal_margin + 0.02, 1))),
        ("NWC +2pp", replace(a, nwc_ratio=a.nwc_ratio + 0.02)),
        ("capex +2pp", replace(a, capex_ratio=a.capex_ratio + 0.02)),
    ]
    return [{"driver": label, "ev": model(case, changed)["valuation"]["ev"]} for label, changed in cases]


def synergies(rows: list[dict], a: Assumptions) -> dict:
    """Separate finite-horizon expected after-tax FCFF, with upfront integration cost.

    No terminal synergy assumed; integration cost paid regardless of realization.
    """
    flows = [
        {
            "year": r["year"],
            "expected_fcff": r["net_revenue"]
            * a.synergy_revenue_ratio
            * (1 - a.tax_rate)
            * a.synergy_probability,
            "t": r["discount_year"],
        }
        for r in rows
    ]
    pv = sum(r["expected_fcff"] / (1 + a.synergy_discount) ** r["t"] for r in flows) - a.integration_cost
    return {
        "pv": pv,
        "integration_cost": a.integration_cost,
        "probability": a.synergy_probability,
        "discount_rate": a.synergy_discount,
        "flows": flows,
    }
