"""Economic LOI, SPA checklist and buyer comparison; not executable legal contracts."""

import json
from pathlib import Path

from .contracts import DISCLAIMER, M
from .reporting import metric


def write_transaction_materials(run: dict, destination: Path):
    """Write drafts directly from frozen transaction values; no signatures or outreach."""
    intro = (
        f"# Project Aurora | SYNTHETIC ECONOMIC DRAFT\n\n{DISCLAIMER}\n\n"
        f"Run {run['run_id']} | as-of {run['as_of']} | DRAFT_REVIEW_REQUIRED\n\n"
    )
    loi = intro + "## LOI economic illustration\n\n"
    loi += (
        f"Illustrative enterprise value: R$ {metric(run, 'bridge.ev')} mi [bridge.ev].\n\n"
        f"Equity before NWC true-up: R$ {metric(run, 'bridge.equity')} mi [bridge.equity].\n\n"
        f"Financial debt: R$ {metric(run, 'bridge.financial_debt')} mi; unrestricted cash assumption: "
        f"R$ {metric(run, 'bridge.cash')} mi. These are as-of balances, not verified closing accounts.\n\n"
        f"Seller cash now R$ {metric(run, 'consideration.seller_cash_now')} mi; "
        f"escrow R$ {metric(run, 'consideration.escrow')} mi; "
        f"expected earnout PV R$ {metric(run, 'consideration.earnout_pv')} mi. "
        "Evidence: consideration.*; PV included in all-in equity price.\n\n"
        "Perimeter: 100% secondary shares in the default example; no primary cash injection assumed.\n\n"
        "Pricing mechanism: completion accounts illustration. Peg, debt-like classification, fees, "
        "closing balances and leakage provisions require review. Locked-box is a separate alternative.\n\n"
        "Conditions: acceptable confirmatory DD, IC, legal/tax review, funding evidence, "
        "founder/IP continuity, and agreed working-capital definitions. All remain pending.\n\n"
        "Exclusivity, timetable, enforceability and legal terms are not agreed. "
        "This file does not constitute an offer, binding LOI or legal advice.\n"
    )
    (destination / "loi_economics.md").write_text(loi, encoding="utf-8")
    spa = intro + "## SPA economics and conditions checklist\n\n"
    for item in (
        "Define target shares, share classes and secondary versus primary consideration.",
        "Agree cash eligibility, financial debt and debt-like definitions without NWC overlap.",
        "Use completion-account true-up OR a fixed locked-box price and leakage controls.",
        "Agree monthly-supported normalized NWC peg and closing evidence.",
        "Define earnout metric, threshold/target/cap, horizon, accounting consistency and dispute process.",
        "Separate maximum nominal earnout from probability-weighted PV and closing funding.",
        "Treat escrow as withheld price; separately define releases and indemnity mechanics.",
        "Obtain financial/legal/tax/funding/IC approvals and resolution of high DD issues.",
        "Require counsel review for actual transaction documentation and merger-control analysis.",
    ):
        spa += "- [ ] " + item + "\n"
    spa += "\nStatus: BLOCKED. No real approvals or signatures. See closing.pdf and vdr/index.json.\n"
    (destination / "spa_economic_checklist.md").write_text(spa, encoding="utf-8")
    bids = (
        intro
        + "## Fictional bid comparison\n\nAll offers below are analyst scenarios, not received bids.\n\n"
    )
    bids += "| Buyer | EV R$ mi | Equity R$ mi | Funded upfront R$ mi | Seller cash now R$ mi | Financing / conditions |\n"
    bids += "| --- | ---: | ---: | ---: | ---: | --- |\n"
    for bid in run["bids"]:
        bids += (
            f"| {bid['buyer']} | {bid['bridge']['ev'] / M:,.2f} | {bid['bridge']['equity'] / M:,.2f} | "
            f"{bid['consideration']['upfront_funded'] / M:,.2f} | "
            f"{bid['consideration']['seller_cash_now'] / M:,.2f} | {bid['conditions']} |\n"
        )
    bids += "\nNo preferred-buyer approval is inferred from headline price. Score intervals preserve missing information.\n"
    (destination / "buyer_bid_comparison.md").write_text(bids, encoding="utf-8")
    (destination / "transaction_terms.json").write_text(
        json.dumps(
            {
                "run_id": run["run_id"],
                "status": "DRAFT_REVIEW_REQUIRED",
                "bridge": run["bridge"],
                "consideration": run["consideration"],
                "bids": run["bids"],
                "disclaimer": DISCLAIMER,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
