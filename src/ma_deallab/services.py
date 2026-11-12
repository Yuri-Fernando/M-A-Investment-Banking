"""Single orchestration service used by CLI, dashboard and every report."""

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .contracts import AS_OF, DISCLAIMER, M, Assumptions
from .finance import model, operating_stress, sensitivity, synergies
from .ingestion import canonical_hash, debt, default_data_dir, digest, load_case, ltm, nwc, qoe
from .public_data import trading_comps
from .transaction import consideration, equity_bridge, score_buyer

ENGINE_VERSION = "1.0.0"


def scenario_assumptions(case: dict, name: str) -> Assumptions:
    """Load CSV assumptions, including shared tax/bid; fixed extra policy disclosed."""
    if name not in ("base", "downside", "upside"):
        raise ValueError("Unknown scenario")
    values = {}
    for row in case["rows"]["scenario_assumptions.csv"]:
        key = (row["scenario"], row["driver"])
        if key in values:
            raise ValueError("Duplicate assumption")
        values[key] = float(row["value"])
    return Assumptions(
        scenario=name,
        growth=values[name, "fy2027_revenue_growth_pct"] / 100,
        deceleration={"downside": 0.01, "base": 0.015, "upside": 0.02}[name],
        terminal_margin=values[name, "ebitda_margin_terminal_pct"] / 100,
        capex_ratio=values[name, "capex_revenue_pct"] / 100,
        nwc_ratio=values[name, "nwc_revenue_pct"] / 100,
        tax_rate=values["base", "simplified_tax_pct"] / 100,
        bid_ev=values["base", "illustrative_bid_ev_brl_millions"] * M,
    )


def code_fingerprint() -> dict:
    """Exact package sources used by this run."""
    root = Path(__file__).parent
    return {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in sorted(root.rglob("*.py"))}


def build_run(
    data_dir: Path | None = None,
    overrides: dict | None = None,
    accepted_qoe: dict | None = None,
    peers: list | None = None,
) -> dict:
    """Build all scenarios from a validated immutable input snapshot.

    overrides maps scenario name to assumption keys; all values are in engine units.
    No source files, existing runs or approvals are modified.
    """
    case = load_case(data_dir)
    overrides = overrides or {}
    if set(overrides) - {"base", "downside", "upside"}:
        raise ValueError("Unknown scenario override")
    scenarios = {}
    for name in ("downside", "base", "upside"):
        a = Assumptions(**{**asdict(scenario_assumptions(case, name)), **overrides.get(name, {})})
        result = model(case, a)
        result["synergies"] = synergies(result["forecast"], a)
        result["sensitivity"] = sensitivity(result["forecast"], a)
        result["stress"] = operating_stress(case, a)
        result["assumptions"] = asdict(a)
        result["wacc_build"] = {
            "ke": a.ke,
            "wacc": a.wacc,
            "currency": "BRL_NOMINAL",
            "erp_policy": "total local ERP includes country risk; no additional CRP",
            "source_type": "ANALYST_ASSUMPTION",
        }
        scenarios[name] = result
    bs = case["balance"][AS_OF]
    bridge = equity_bridge(scenarios["base"]["assumptions"]["bid_ev"], bs["cash"], debt(bs))
    price = consideration(bridge["equity"], earnout_cap=15 * M)
    qoe_result = qoe(case, accepted_qoe)
    lt = ltm(case)
    risks = case["rows"]["risk_register.csv"]
    for name, result in scenarios.items():
        ev = result["valuation"]["ev"]
        bid = result["assumptions"]["bid_ev"]
        result["decision"] = (
            "WALK_AWAY" if ev < bid * 0.8 else "RENEGOTIATE" if ev < bid else "PROCEED_CONDITIONAL"
        )
        result["decision_reason"] = (
            "Standalone EV versus illustrative bid; all unresolved DD gates remain. "
            "This is a case-specific analytical rule, not an approved investment."
        )
        result["standalone_equity"] = equity_bridge(ev, bs["cash"], debt(bs))["equity"]
    bids = []
    for buyer, discount, cap, condition in (
        (
            "Atlas Industrial Systems S.A. (SYNTHETIC)",
            1.0,
            15 * M,
            "Funding uncommitted; IP/customer DD pending",
        ),
        (
            "Pontal Growth Capital (SYNTHETIC)",
            0.925,
            10 * M,
            "Funding uncommitted; leverage and management DD pending",
        ),
    ):
        bid_bridge = equity_bridge(bridge["ev"] * discount, bs["cash"], debt(bs))
        bids.append(
            {
                "buyer": buyer,
                "ev_factor_assumption": discount,
                "bridge": bid_bridge,
                "consideration": consideration(bid_bridge["equity"], earnout_cap=cap),
                "conditions": condition,
                "classification": "SYNTHETIC",
                "status": "ILLUSTRATIVE_NOT_RECEIVED",
            }
        )
    run = {
        "engine_version": ENGINE_VERSION,
        "as_of": AS_OF,
        "currency": "BRL",
        "unit": "BRL",
        "display_unit": "BRL_millions",
        "disclaimer": DISCLAIMER,
        "sources": case["sources"],
        "code_hashes": code_fingerprint(),
        "income": case["income"],
        "balance": case["balance"],
        "cashflow": case["cashflow"],
        "ltm": lt,
        "net_debt": debt(bs) - bs["cash"],
        "operating_nwc": nwc(bs),
        "contract_nwc": nwc(bs, True),
        "qoe": qoe_result,
        "checks": case["checks"],
        "scenarios": scenarios,
        "bridge": bridge,
        "consideration": price,
        "risks": risks,
        "planned_events": case["rows"]["synthetic_deal_events.csv"],
        "bids": bids,
        "deal_stage": "VAL_DRAFT",
        "closing_status": "BLOCKED_UNRESOLVED_DD_AND_NWC_TERMS",
        "comps": trading_comps(peers or [], AS_OF),
        "buyer_screening": [
            {
                "name": "Atlas Industrial Systems S.A. (SYNTHETIC)",
                **score_buyer({"fit": 5, "recurring": 4, "cash": 4, "valuation": 3, "integration": 3}),
            },
            {
                "name": "Pontal Growth Capital (SYNTHETIC)",
                **score_buyer({"fit": 3, "recurring": 4, "cash": 4, "valuation": None, "integration": 3}),
            },
        ],
        "policy": {
            "nwc_peg": "Unavailable: no monthly observations; no invented peg",
            "qoe": "FY2025 accepted reviewer decisions only; never applied automatically to LTM",
            "closing": "No auto approval; unresolved high DD blocks simulated close",
            "artifact_status": "DRAFT_REVIEW_REQUIRED",
            "scenario_comparison": "Frozen per-scenario runs, not market probabilities",
        },
    }
    run["run_id"] = canonical_hash(run)[:20]
    run["metrics"] = metric_registry(run)
    return run


def metric_registry(run: dict) -> dict:
    """Every exported model numeric leaf resolves to a run path and input/assumption lineage.

    Dates/years are identifiers. Detailed numerical transforms are source-controlled
    and tied by exact source hashes; metrics preserve full BRL without display rounding.
    """
    registry = {}

    def walk(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                if key not in ("code_hashes", "sources"):
                    walk(item, f"{path}.{key}" if path else key)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, f"{path}.{i}")
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            is_rate = any(
                path.endswith("." + k)
                for k in (
                    "wacc",
                    "g",
                    "margin",
                    "probability",
                    "terminal_share",
                    "factor",
                    "coverage",
                    "ke",
                    "stake",
                    "recurring_share",
                    "dividend_ratio",
                    "tax_rate",
                    "growth",
                    "deceleration",
                    "terminal_margin",
                    "capex_ratio",
                    "nwc_ratio",
                    "da_ratio",
                    "debt_weight",
                    "debt_cost",
                    "rf_brl",
                    "total_erp",
                    "terminal_g",
                    "synergy_revenue_ratio",
                    "synergy_probability",
                    "synergy_discount",
                    "discount_rate",
                    "q4_margin",
                    "model_tax_rate",
                    "ev_factor_assumption",
                )
            )
            registry[path] = {
                "value": value,
                "unit": "fraction"
                if is_rate
                else "identifier_or_ratio"
                if path.endswith(
                    (
                        ".year",
                        ".t",
                        ".fraction",
                        ".discount_year",
                        ".exit_multiple",
                        ".beta",
                        ".lower",
                        ".upper",
                        ".known_score",
                        ".ev_ebitda",
                        ".ev_revenue",
                    )
                )
                else "BRL",
                "classification": "ANALYST_ASSUMPTION"
                if ".assumptions." in path
                else "SYNTHETIC"
                if path.startswith(("income.", "balance.", "cashflow."))
                else "DERIVED",
                "as_of": run["as_of"],
                "run_id": run["run_id"],
                "source_hashes": {k: v["sha256"] for k, v in run["sources"].items()},
                "formula_reference": formula_reference(path),
                "engine_code_hashes": run["code_hashes"],
            }

    walk({k: v for k, v in run.items() if k not in ("metrics",)}, "")
    return registry


def formula_reference(path: str) -> str:
    if path.startswith("ltm."):
        return "FY2025 - 9M2025 + 9M2026; ingestion.ltm"
    if path.startswith("bridge."):
        return "EV + cash - debt - debt_like + NWC adjustment - fees; transaction.equity_bridge"
    if path.startswith("consideration."):
        return "all_in = upfront_funded + earnout_PV + rollover; transaction.consideration"
    if ".valuation." in path or ".sensitivity." in path:
        return "PV(FCFF) + normalized terminal FCFF/(WACC-g)/(1+WACC)^5.25; finance.dcf"
    if ".forecast." in path:
        return "Integrated IS/BS/CF schedules; finance.forecast; assumptions at scenarios.<name>.assumptions"
    if path.startswith("qoe."):
        return "reported EBITDA + accepted signed period-specific adjustments; ingestion.qoe"
    return "Source fact or derived transform; source-controlled ingestion/finance/services with exact code hashes"


def manifest(run: dict) -> dict:
    return {
        "run_id": run["run_id"],
        "as_of": run["as_of"],
        "sources": run["sources"],
        "engine_version": ENGINE_VERSION,
        "code_hashes": run["code_hashes"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": DISCLAIMER,
        "artifact_status": "DRAFT_REVIEW_REQUIRED",
        "currency": "BRL",
        "unit": "BRL",
        "data_dir": str(default_data_dir()),
        "formula_cache": "XlsxWriter reference-engine caches",
        "recalculation": "Cached Python values verified; independent Excel/LibreOffice recalc reported separately",
    }
