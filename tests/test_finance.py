from dataclasses import replace

import pytest

from ma_deallab.contracts import M, Assumptions, ModelError
from ma_deallab.finance import dcf, forecast, model
from ma_deallab.ingestion import balance_check, debt, ltm, nwc, qoe
from ma_deallab.transaction import consideration, earnout_payout, equity_bridge


def test_f01_balance_all_dates(case):
    assert all(abs(balance_check(s)) < 0.001 for s in case["balance"].values())


def test_f02_03_independent_cash_endpoints(case):
    assert [case["balance"][d]["cash"] / M for d in sorted(case["balance"])] == [6, 8, 9, 11]
    assert [case["cashflow"][d]["cash_from_operations"] / M for d in sorted(case["cashflow"])] == [
        7.6,
        10.08,
        9.06,
    ]


def test_f04_reported_income(case):
    assert case["income"]["2025-12-31"]["ebitda"] == 19 * M
    assert case["income"]["2025-12-31"]["net_income"] == 8.58 * M


@pytest.mark.parametrize(
    "account,expected", [("net_revenue", 99), ("ebitda", 21.6), ("ebit", 17.8), ("net_income", 9.966)]
)
def test_f05_ltm_golden(case, account, expected):
    assert ltm(case, account) == pytest.approx(expected * M, abs=0.001)


def test_f06_stock_ltm_rejected(case):
    with pytest.raises(ModelError, match="STOCK"):
        ltm(case, "cash")


def test_f07_netdebt_nwc(case):
    bs = case["balance"]["2026-09-30"]
    assert debt(bs) - bs["cash"] == 7 * M
    assert nwc(bs) == 8 * M
    assert nwc(bs, True) == 10 * M


def test_f08_qoe_requires_accepted_evidence(case):
    result = qoe(
        case,
        {
            "Q01": {"reviewer": "R", "evidence_id": "DEMO_Q01_INVOICE"},
            "Q02": {"reviewer": "R", "evidence_id": "DEMO_Q02_COMP_BENCH"},
        },
    )
    assert result["adjusted"] == 19.2 * M


def test_f09_no_proposed_addback(case):
    assert qoe(case)["adjusted"] == 19 * M
    with pytest.raises(ModelError, match="reviewer"):
        qoe(case, {"Q01": {"evidence_id": "DEMO_Q01_INVOICE"}})


def test_qoe_period_isolation(case):
    with pytest.raises(ModelError, match="period"):
        qoe(case, {"Q01": {"reviewer": "R", "evidence_id": "DEMO_Q01_INVOICE"}}, "2026-09-30")


def test_f10_stub_and_full_year(run):
    s = run["scenarios"]["base"]
    assert s["fy2026e"]["net_revenue"] == 101 * M
    assert s["forecast"][0]["net_revenue"] == 26 * M
    assert s["forecast"][1]["net_revenue"] == pytest.approx(113.12 * M)
    assert [r["discount_year"] for r in s["forecast"]] == [0.25, 1.25, 2.25, 3.25, 4.25, 5.25]


@pytest.mark.parametrize("name", ["base", "downside", "upside"])
def test_f12_13_forecast_three_statements(run, name):
    for r in run["scenarios"][name]["forecast"]:
        assert abs(r["bs_residual"]) < 0.001
        assert r["cash"] == pytest.approx(r["opening_cash"] + r["cfo"] + r["cfi"] + r["cff"], abs=0.001)
        assert r["bs"]["net_ppe"] == pytest.approx(
            r["opening_ppe"] + r["capex"] - r["depreciation_amortization"]
        )
        assert r["bs"]["equity"] == pytest.approx(r["opening_equity"] + r["net_income"] - r["dividends"])
        assert r["recurring_revenue"] + r["project_revenue"] == pytest.approx(r["net_revenue"])


def test_v01_fail_wacc_g():
    with pytest.raises(ModelError, match="WACC"):
        Assumptions(terminal_g=0.20)


def test_v02_fcff_excludes_interest(case):
    a = Assumptions()
    rows1 = forecast(case, a)
    rows2 = forecast(case, replace(a, debt_cost=0.3))
    assert [r["fcff"] for r in rows1] == pytest.approx([r["fcff"] for r in rows2])
    assert rows1[0]["net_income"] != rows2[0]["net_income"]


def test_dcf_independent_two_period_golden():
    rows = [
        {
            "year": y,
            "discount_year": t,
            "fcff": 100,
            "ebit": 100,
            "depreciation_amortization": 0,
            "capex": 0,
            "nwc": 0,
            "model_tax_rate": 0,
            "ebitda": 100,
        }
        for y, t in [(1, 1), (2, 2)]
    ]
    result = dcf(rows, 0.1, 0.04, 8)
    assert result["ev"] == pytest.approx(1606.060606060606)
    assert result["exit_ev"] == pytest.approx(834.7107438016528)


def test_v04_monotonic_discount(run):
    rows = run["scenarios"]["base"]["forecast"]
    assert dcf(rows, 0.18, 0.04)["ev"] < dcf(rows, 0.15, 0.04)["ev"]


def test_v05_v06_v07_ev_equity():
    assert equity_bridge(160 * M, 11 * M, 18 * M)["equity"] == 153 * M
    assert equity_bridge(160 * M, 12 * M, 18 * M)["equity"] == 154 * M
    assert equity_bridge(160 * M, 11 * M, 19 * M)["equity"] == 152 * M


def test_v08_completion_accounts():
    assert equity_bridge(160 * M, 11 * M, 18 * M, closing_nwc=11 * M, peg=10 * M)["equity"] == 154 * M


def test_v09_locked_box():
    with pytest.raises(ModelError, match="Locked"):
        equity_bridge(160, 11, 18, closing_nwc=10, peg=9, mechanism="locked_box")


@pytest.mark.parametrize("metric,expected", [(-10, 0), (5, 0), (15, 50), (25, 100), (50, 100)])
def test_v10_earnout_bounds(metric, expected):
    assert earnout_payout(metric, 5, 25, 100) == expected


def test_consideration_no_doublecount():
    c = consideration(153 * M, 15 * M)
    assert c["all_in_equity"] == 153 * M
    assert c["upfront_funded"] + c["earnout_pv"] + c["rollover"] == pytest.approx(153 * M)
    assert c["seller_cash_now"] + c["escrow"] == pytest.approx(c["upfront_funded"])
    assert c["maximum_nominal_consideration"] > c["all_in_equity"]


def test_partial_sale_and_rollover():
    c = consideration(100, rollover_ratio=0.2, stake=0.7)
    assert c["all_in_equity"] == 70
    assert c["rollover"] == 14
    assert c["retained_equity"] == pytest.approx(30)


def test_v11_separate_synergy(run):
    s = run["scenarios"]["base"]
    assert s["synergies"]["pv"] > 0
    assert s["valuation"]["ev"] < 160 * M
    assert run["bridge"]["ev"] == 160 * M


def test_v15_negative_cash_no_plug(case):
    result = model(case, Assumptions(q4_revenue=1000 * M, nwc_ratio=0.9))
    assert result["warnings"]
    assert result["forecast"][0]["cash"] < 0
    assert abs(result["forecast"][0]["bs_residual"]) < 0.001


def test_scenario_order(run):
    ev = [run["scenarios"][k]["valuation"]["ev"] for k in ("downside", "base", "upside")]
    assert ev == sorted(ev)
    assert run["scenarios"]["base"]["decision"] == "WALK_AWAY"


@pytest.mark.parametrize("changes", [{"growth": float("nan")}, {"nwc_ratio": 1.2}, {"debt_weight": -0.1}])
def test_invalid_assumptions(changes):
    with pytest.raises(ModelError):
        Assumptions(**changes)
