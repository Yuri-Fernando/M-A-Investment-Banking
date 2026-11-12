"""Economic terms and simulated permissions/state gates, never real approvals."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite

from .contracts import ModelError


def equity_bridge(
    ev: float,
    cash: float,
    financial_debt: float,
    debt_like: float = 0,
    closing_nwc: float | None = None,
    peg: float | None = None,
    seller_fees: float = 0,
    mechanism: str = "completion_accounts",
) -> dict:
    """EV to equity in BRL. No NWC peg is invented when monthly evidence is absent."""
    vals = (cash, financial_debt, debt_like, seller_fees)
    if not isfinite(ev) or any(not isfinite(v) or v < 0 for v in vals):
        raise ModelError("Invalid bridge input")
    if mechanism not in ("completion_accounts", "locked_box"):
        raise ModelError("Unknown pricing mechanism")
    if (closing_nwc is None) != (peg is None):
        raise ModelError("NWC requires both closing balance and agreed peg")
    if closing_nwc is not None and not all(isfinite(v) for v in (closing_nwc, peg)):
        raise ModelError("Non-finite NWC")
    if mechanism == "locked_box" and (closing_nwc is not None or peg is not None):
        raise ModelError("Locked box cannot stack completion-account true-up")
    adjustment = 0 if peg is None else closing_nwc - peg
    return {
        "ev": ev,
        "cash": cash,
        "financial_debt": financial_debt,
        "debt_like": debt_like,
        "nwc_adjustment": adjustment,
        "seller_fees": seller_fees,
        "mechanism": mechanism,
        "equity": ev + cash - financial_debt - debt_like + adjustment - seller_fees,
        "nwc_status": "UNAGREED_NO_MONTHLY_DATA" if peg is None else "ANALYST_ASSUMPTION",
    }


def earnout_payout(metric: float, threshold: float, target: float, cap: float) -> float:
    """Linear payout between threshold and target, capped; all monetary amounts BRL."""
    if not all(isfinite(x) for x in (metric, threshold, target, cap)) or target <= threshold or cap < 0:
        raise ModelError("Invalid earnout thresholds/cap")
    return max(0, min(cap, cap * (metric - threshold) / (target - threshold)))


def consideration(
    equity: float,
    earnout_cap: float = 0,
    probability: float = 0.5,
    discount: float = 0.15,
    years: float = 2,
    escrow_ratio: float = 0.05,
    rollover_ratio: float = 0,
    stake: float = 1,
) -> dict:
    """All-in expected equity value allocation; earnout PV is already in the price.

    Acquisition stake is secondary shares only. Escrow is funded at close and
    withheld from seller receipts. Rollover is retained seller equity, not cost.
    """
    values = (equity, earnout_cap, probability, discount, years, escrow_ratio, rollover_ratio, stake)
    if not all(isfinite(v) for v in values) or equity < 0 or earnout_cap < 0 or years <= 0 or discount < 0:
        raise ModelError("Invalid consideration")
    if not 0 < stake <= 1 or not all(0 <= v <= 1 for v in (probability, escrow_ratio, rollover_ratio)):
        raise ModelError("Invalid allocation fraction")
    total = equity * stake
    pv = earnout_cap * probability / (1 + discount) ** years
    rollover = total * rollover_ratio
    upfront = total - pv - rollover
    if upfront < 0:
        raise ModelError("Contingent/rollover value exceeds all-in equity consideration")
    escrow = upfront * escrow_ratio
    return {
        "all_in_equity": total,
        "earnout_cap": earnout_cap,
        "earnout_pv": pv,
        "rollover": rollover,
        "upfront_funded": upfront,
        "escrow": escrow,
        "seller_cash_now": upfront - escrow,
        "maximum_nominal_consideration": upfront + rollover + earnout_cap,
        "stake": stake,
        "retained_equity": equity * (1 - stake),
        "allocation_residual": total - upfront - pv - rollover,
    }


STAGES = (
    "SCREENING",
    "VAL_DRAFT",
    "MARKETING_SIMULATED",
    "IOI_SIMULATED",
    "LOI_SIMULATED",
    "DD_SIMULATED",
    "SPA_NEGOTIATION_SIMULATED",
    "CLOSED_SIMULATED",
)
CLOSING_GATES = {"financial_checks", "ic", "legal", "tax", "funding", "nwc_terms", "dd"}


@dataclass
class Workflow:
    """In-memory state machine. Events can be persisted in run outputs; no identity security."""

    stage: str = "SCREENING"
    events: list = field(default_factory=list)

    def advance(
        self,
        target: str,
        role: str,
        actor: str,
        evidence_id: str,
        rationale: str,
        approvals: dict | None = None,
        unresolved_high: int = 0,
    ) -> None:
        if role != "reviewer" or not actor or not evidence_id or not rationale:
            raise ModelError("Reviewer, actor, rationale and evidence required")
        if (
            self.stage not in STAGES
            or target not in STAGES
            or STAGES.index(target) != STAGES.index(self.stage) + 1
        ):
            raise ModelError("INVALID_TRANSITION")
        approvals = approvals or {}
        if target == "LOI_SIMULATED" and not approvals.get("shortlist"):
            raise ModelError("Shortlist approval required before LOI")
        if target == "CLOSED_SIMULATED" and (
            unresolved_high or not all(approvals.get(k) for k in CLOSING_GATES)
        ):
            raise ModelError("CLOSING_BLOCKED: unresolved diligence or approvals")
        self.events.append(
            {
                "prior": self.stage,
                "new": target,
                "actor": actor,
                "evidence_id": evidence_id,
                "rationale": rationale,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "approvals": dict(approvals),
            }
        )
        self.stage = target


@dataclass
class ArtifactReview:
    """Draft lifecycle for simulated distribution; export as draft is allowed."""

    state: str = "DRAFT"

    def transition(self, target: str, role: str):
        allowed = {
            "DRAFT": ("REVIEW_REQUIRED", "analyst"),
            "REVIEW_REQUIRED": ("APPROVED", "reviewer"),
            "APPROVED": ("DISTRIBUTED_SIMULATED", "reviewer"),
            "DISTRIBUTED_SIMULATED": ("ARCHIVED", "reviewer"),
        }
        if allowed.get(self.state) != (target, role):
            raise ModelError("EXPORT_NOT_APPROVED")
        self.state = target


def vdr_access(role: str, approved: bool, allowed_roles: tuple = ("analyst", "reviewer", "viewer")) -> bool:
    """Demo role policy only; no authentication or production confidentiality claim."""
    return role in allowed_roles and (approved or role in ("analyst", "reviewer"))


def score_buyer(scores: dict, weights: dict | None = None) -> dict:
    """Unknown scores produce a confidence interval, never silently become zero."""
    weights = weights or {
        "fit": 0.30,
        "recurring": 0.20,
        "cash": 0.20,
        "valuation": 0.15,
        "integration": 0.15,
    }
    if abs(sum(weights.values()) - 1) > 1e-9 or any(v < 0 for v in weights.values()):
        raise ModelError("Buyer weights must sum to one")
    known, coverage = 0.0, 0.0
    for key, weight in weights.items():
        value = scores.get(key)
        if value is not None:
            if not isfinite(value) or not 0 <= value <= 5:
                raise ModelError("Buyer score outside 0..5")
            known += value / 5 * weight * 100
            coverage += weight
    return {
        "lower": known,
        "upper": known + (1 - coverage) * 100,
        "coverage": coverage,
        "known_score": known / coverage if coverage else None,
    }
