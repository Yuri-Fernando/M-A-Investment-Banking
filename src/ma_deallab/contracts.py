"""Typed assumptions; engine currency is full BRL, presentation is BRL millions."""

from dataclasses import asdict, dataclass
from datetime import date
from enum import Enum
from math import isfinite

M = 1_000_000
AS_OF = "2026-09-30"
DISCLAIMER = (
    "SYNTHETIC - SIMULATED - NOT A REAL TRANSACTION. Illustrative analysis; not investment or legal advice."
)


class ModelError(ValueError):
    """Invalid financial input; calculation/export must stop."""


class DataClass(str, Enum):
    SYNTHETIC = "SYNTHETIC"
    PUBLIC_OFFICIAL = "PUBLIC_OFFICIAL"
    PUBLIC_THIRD_PARTY = "PUBLIC_THIRD_PARTY"
    ANALYST_ASSUMPTION = "ANALYST_ASSUMPTION"
    DERIVED = "DERIVED"


@dataclass(frozen=True)
class Assumptions:
    """Nominal BRL drivers. Rates are fractions; money is full BRL.

    Local total ERP includes country risk, so there is no added CRP.
    Tax is cash tax on positive EBT; no deferred tax or loss carryforward.
    D&A is assigned to PPE; intangible balance held constant in this case.
    """

    scenario: str = "base"
    as_of: str = AS_OF
    q4_revenue: float = 26 * M
    q4_margin: float = 0.22
    growth: float = 0.12
    deceleration: float = 0.015
    terminal_margin: float = 0.22
    capex_ratio: float = 0.06
    nwc_ratio: float = 0.09
    da_ratio: float = 0.04
    tax_rate: float = 0.34
    rf_brl: float = 0.10
    beta: float = 1.0
    total_erp: float = 0.07
    debt_cost: float = 0.13
    debt_weight: float = 0.20
    terminal_g: float = 0.04
    exit_multiple: float = 8.0
    bid_ev: float = 160 * M
    recurring_share: float = 0.65
    dividend_ratio: float = 0.30
    synergy_revenue_ratio: float = 0.02
    synergy_probability: float = 0.60
    integration_cost: float = 3 * M
    synergy_discount: float = 0.18

    def __post_init__(self):
        date.fromisoformat(self.as_of)
        if self.as_of != AS_OF:
            raise ModelError("SCOPE_MISMATCH: synthetic case supports 2026-09-30 only")
        for key, value in asdict(self).items():
            if isinstance(value, (int, float)) and not isfinite(value):
                raise ModelError(f"Non-finite assumption: {key}")
        for key in (
            "q4_margin",
            "terminal_margin",
            "capex_ratio",
            "nwc_ratio",
            "da_ratio",
            "tax_rate",
            "debt_weight",
            "recurring_share",
            "dividend_ratio",
            "synergy_probability",
        ):
            if not 0 <= getattr(self, key) <= 1:
                raise ModelError(f"Invalid fraction: {key}")
        if self.q4_revenue <= 0 or self.growth <= -1 or self.deceleration < 0:
            raise ModelError("Invalid revenue drivers")
        if (
            min(
                self.rf_brl,
                self.beta,
                self.total_erp,
                self.debt_cost,
                self.terminal_g,
                self.exit_multiple,
                self.bid_ev,
                self.integration_cost,
                self.synergy_discount,
                self.synergy_revenue_ratio,
            )
            < 0
        ):
            raise ModelError("Negative valuation assumption")
        if self.wacc <= self.terminal_g:
            raise ModelError("WACC_CHECK: WACC must exceed terminal growth")

    @property
    def ke(self) -> float:
        return self.rf_brl + self.beta * self.total_erp

    @property
    def wacc(self) -> float:
        return (1 - self.debt_weight) * self.ke + self.debt_weight * self.debt_cost * (1 - self.tax_rate)
