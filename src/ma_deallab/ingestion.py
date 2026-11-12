"""Strict local CSV ingestion and accounting validation. No network on import."""

import csv
import hashlib
import json
import math
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .contracts import AS_OF, M, ModelError

IS_ACCOUNTS = {
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
}
ASSETS = (
    "cash",
    "accounts_receivable",
    "inventory",
    "other_operating_current_assets",
    "net_ppe",
    "intangible_assets",
    "other_noncurrent_assets",
)
LIABILITIES = (
    "accounts_payable",
    "operating_accruals",
    "income_tax_payable",
    "short_term_debt",
    "long_term_debt",
    "other_noncurrent_liabilities",
)
BS_ACCOUNTS = set(ASSETS + LIABILITIES + ("equity",))
CF_ACCOUNTS = {
    "net_income",
    "depreciation_amortization",
    "increase_operating_nwc",
    "cash_from_operations",
    "capex_ppe",
    "investments_other_noncurrent_assets",
    "cash_from_investing",
    "change_financial_debt",
    "dividends_paid",
    "cash_from_financing",
    "change_in_cash",
    "cash_begin",
    "cash_end",
}
TOL = 0.001  # BRL: stricter than specification's 1 BRL / 1e-6 BRL million.


def digest(data: bytes) -> str:
    """SHA256 of exact input bytes."""
    return hashlib.sha256(data).hexdigest()


def canonical_hash(value) -> str:
    """Stable hash, rejecting NaN/infinity."""
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def amount_brl(text: str, unit: str = "BRL_millions", locale: str = "en") -> float:
    """Parse explicit unit/locale. Example: amount_brl('1.234,56', 'BRL', 'pt_BR')."""
    scales = {"BRL": 1, "BRL_thousands": 1000, "BRL_millions": M}
    if unit not in scales or locale not in ("en", "pt_BR"):
        raise ModelError("Unsupported unit/locale")
    if locale == "pt_BR":
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        raise ModelError("Ambiguous decimal separator; specify pt_BR")
    try:
        value = float(Decimal(text) * scales[unit])
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ModelError("Invalid numeric value") from exc
    if not math.isfinite(value):
        raise ModelError("Non-finite amount")
    return value


def close(actual, expected, label):
    """Accounting comparison in full BRL; raises, never silently plugs."""
    if not math.isfinite(actual) or abs(actual - expected) > TOL:
        raise ModelError(f"RECONCILIATION_ERROR {label}: {actual} != {expected}")


def nwc(bs: dict, contract: bool = False) -> float:
    """Operating NWC includes income tax payable; SPA illustration excludes taxes."""
    value = (
        bs["accounts_receivable"]
        + bs["inventory"]
        + bs["other_operating_current_assets"]
        - bs["accounts_payable"]
        - bs["operating_accruals"]
    )
    return value if contract else value - bs["income_tax_payable"]


def debt(bs: dict) -> float:
    return bs["short_term_debt"] + bs["long_term_debt"]


def balance_check(bs: dict) -> float:
    """Assets less liabilities and equity, in BRL."""
    return sum(bs[a] for a in ASSETS) - sum(bs[a] for a in LIABILITIES) - bs["equity"]


def default_data_dir() -> Path:
    """Source fixtures in checkout; packaged identical fixtures in an installed wheel."""
    checkout = Path(__file__).resolve().parents[2] / "examples"
    return checkout if checkout.is_dir() else Path(__file__).parent / "data"


def load_case(data_dir: Path | None = None, as_of: str = AS_OF) -> dict:
    """Load seven immutable fixture CSVs and reject missing, duplicate or future facts."""
    data_dir = Path(data_dir) if data_dir else default_data_dir()
    case = {"sources": {}, "rows": {}, "income": {}, "balance": {}, "cashflow": {}, "checks": []}
    files = (
        "synthetic_income_statement.csv",
        "synthetic_balance_sheet.csv",
        "synthetic_cash_flow.csv",
        "synthetic_qoe_adjustments.csv",
        "scenario_assumptions.csv",
        "risk_register.csv",
        "synthetic_deal_events.csv",
    )
    for name in files:
        raw = (data_dir / name).read_bytes()
        case["sources"][name] = {
            "sha256": digest(raw),
            "source": f"examples/{name}",
            "classification": ("ANALYST_ASSUMPTION" if name.startswith("scenario") else "SYNTHETIC"),
            "available_at": AS_OF,
            "unit": "BRL_millions in fixtures",
            "scope": "SYN",
            "entity_id": "NEXAOPS_SYNTH",
        }
        rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
        if not rows:
            raise ModelError(f"Empty dataset: {name}")
        case["rows"][name] = rows
    for kind, name, required in (
        ("income", files[0], IS_ACCOUNTS),
        ("balance", files[1], BS_ACCOUNTS),
        ("cashflow", files[2], CF_ACCOUNTS),
    ):
        for row in case["rows"][name]:
            if row.get("entity_id") != "NEXAOPS_SYNTH" or row.get("data_class") != "SYNTHETIC":
                raise ModelError("SCOPE_MISMATCH: fixture requires synthetic target only")
            if not row.get("source_id"):
                raise ModelError("MISSING_SOURCE")
            end = row.get("balance_date", row.get("period_end"))
            date.fromisoformat(end)
            if end > as_of or row.get("available_at", AS_OF) > as_of:
                raise ModelError("DATA_FUTURE_LEAK")
            period = row.get("period_type", "AT_DATE")
            if kind != "balance":
                expected = "FY" if end.endswith("12-31") else "9M" if end.endswith("09-30") else None
                if period != expected:
                    raise ModelError("SCOPE_MISMATCH: FY vs cumulative 9M")
            elif period != "AT_DATE":
                raise ModelError("Stock must be AT_DATE")
            if row.get("unit", "BRL_millions") != "BRL_millions":
                raise ModelError("SCALE_MISMATCH")
            group = case[kind].setdefault(end, {})
            account = row["account_code"]
            if account not in required or account in group:
                raise ModelError("DUPLICATE_OR_UNKNOWN_ACCOUNT")
            value = amount_brl(row["amount_brl_millions"])
            if kind != "cashflow" and value < 0:
                raise ModelError("Sign convention requires positive magnitudes")
            group[account] = value
        for end, facts in case[kind].items():
            if set(facts) != required:
                raise ModelError(f"MISSING_REQUIRED_LINE: {kind} {end}: {required - set(facts)}")
    expected_dates = {
        "income": {"2023-12-31", "2024-12-31", "2025-12-31", "2025-09-30", AS_OF},
        "balance": {"2023-12-31", "2024-12-31", "2025-12-31", AS_OF},
        "cashflow": {"2024-12-31", "2025-12-31", AS_OF},
    }
    for kind, dates in expected_dates.items():
        if set(case[kind]) != dates:
            raise ModelError(f"MISSING_PERIOD: {kind}")
    validate_case(case)
    return case


def validate_case(case: dict) -> None:
    """Recalculate IS, BS, CF, PPE, debt and retained earnings from source facts."""
    checks = []
    for end, s in case["income"].items():
        close(s["ebitda"], s["net_revenue"] - s["cogs"] - s["cash_opex"], f"EBITDA {end}")
        close(s["ebit"], s["ebitda"] - s["depreciation_amortization"], f"EBIT {end}")
        close(s["pretax_income"], s["ebit"] - s["net_interest_expense"], f"EBT {end}")
        close(s["net_income"], s["pretax_income"] - s["income_taxes"], f"NI {end}")
        checks.append({"check": f"IS {end}", "residual_brl": 0.0, "status": "PASS"})
    for end, bs in case["balance"].items():
        residual = balance_check(bs)
        close(residual, 0, f"BS {end}")
        checks.append({"check": f"BS {end}", "residual_brl": residual, "status": "PASS"})
    pairs = (("2023-12-31", "2024-12-31"), ("2024-12-31", "2025-12-31"), ("2025-12-31", AS_OF))
    for start, end in pairs:
        old, new = case["balance"][start], case["balance"][end]
        cf, s = case["cashflow"][end], case["income"][end]
        for key in ("net_income", "depreciation_amortization"):
            close(cf[key], s[key], f"{key} {end}")
        close(cf["increase_operating_nwc"], nwc(old) - nwc(new), f"NWC {end}")
        close(
            cf["cash_from_operations"],
            cf["net_income"] + cf["depreciation_amortization"] + cf["increase_operating_nwc"],
            f"CFO {end}",
        )
        close(
            cf["cash_from_investing"],
            cf["capex_ppe"] + cf["investments_other_noncurrent_assets"],
            f"CFI {end}",
        )
        close(cf["change_financial_debt"], debt(new) - debt(old), f"debt {end}")
        close(cf["cash_from_financing"], cf["change_financial_debt"] + cf["dividends_paid"], f"CFF {end}")
        close(
            cf["change_in_cash"],
            sum(cf[k] for k in ("cash_from_operations", "cash_from_investing", "cash_from_financing")),
            f"cash delta {end}",
        )
        close(cf["cash_begin"], old["cash"], f"opening cash {end}")
        close(cf["cash_end"], new["cash"], f"ending cash {end}")
        close(new["cash"] - old["cash"], cf["change_in_cash"], f"cash {end}")
        close(new["equity"], old["equity"] + s["net_income"] + cf["dividends_paid"], f"equity {end}")
        close(
            new["net_ppe"], old["net_ppe"] - cf["capex_ppe"] - cf["depreciation_amortization"], f"PPE {end}"
        )
        close(
            new["other_noncurrent_assets"],
            old["other_noncurrent_assets"] - cf["investments_other_noncurrent_assets"],
            f"other assets {end}",
        )
        checks.append({"check": f"CF/debt/PPE/equity {end}", "residual_brl": 0.0, "status": "PASS"})
    case["checks"] = checks


def ltm(case: dict, account: str | None = None):
    """FY2025 - 9M2025 + 9M2026, flow accounts only; stock requests fail."""
    if account is not None and account not in IS_ACCOUNTS:
        raise ModelError("STOCK_LTM_DISALLOWED")
    s = case["income"]
    values = {key: s["2025-12-31"][key] - s["2025-09-30"][key] + s[AS_OF][key] for key in IS_ACCOUNTS}
    return values[account] if account else values


def qoe(case: dict, accepted: dict | None = None, period: str = "2025-12-31") -> dict:
    """Only explicit reviewer/evidence acceptance changes earnings; FY and LTM never mix."""
    accepted = accepted or {}
    if period not in case["income"]:
        raise ModelError("QoE needs a source income period")
    items = []
    known = {row["issue_id"] for row in case["rows"]["synthetic_qoe_adjustments.csv"]}
    if set(accepted) - known:
        raise ModelError("Unknown QoE issue")
    for row in case["rows"]["synthetic_qoe_adjustments.csv"]:
        decision = accepted.get(row["issue_id"])
        value = 0.0
        if decision:
            if row["period_end"] != period or row["sign"] not in ("+", "-"):
                raise ModelError("QoE period/sign mismatch")
            if not decision.get("reviewer") or decision.get("evidence_id") != row["evidence_id"]:
                raise ModelError("QoE reviewer/evidence required")
            value = amount_brl(row["amount_brl_millions"]) * (1 if row["sign"] == "+" else -1)
        items.append(
            {
                **row,
                "accepted": bool(decision),
                "accepted_brl": value,
                "reviewer": decision.get("reviewer") if decision else None,
            }
        )
    reported = case["income"][period]["ebitda"]
    return {
        "period": period,
        "reported": reported,
        "adjusted": reported + sum(i["accepted_brl"] for i in items),
        "items": items,
    }
