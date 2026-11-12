# Deal case — Project Aurora (entirely synthetic)

> None of the following figures or entities are real market/company information. Values are instructional assumptions in **R$ million**. Never attach real company logos.

## Story

**Target: NexaOps Analytics Ltda.** Invented founder-led Brazilian B2B industrial analytics and automation software/service company. Subscription analytics ~65% of revenue; integration/consulting ~35%. Operating across Southeast/South Brazil, serving manufacturing/logistics clients. Growing recurring revenue but with implementation working capital and customer concentration risk.

**Seller:** founder group, 100% ownership, considering sale of 70–100% to fund growth and partial liquidity. **Buyers:** fictitious strategic acquirer `Atlas Industrial Systems S.A.` and fictional PE buyer `Pontal Growth Capital`. No contact, emails or real claims should be generated for these names.

**Mandates:** sell-side advisory to founders; separate internal hypothetical buy-side investment decision as a distinct view. **Do not claim to act for both opposing sides of the same transaction in real life**; for portfolio, these are alternative demonstration perspectives, with no shared confidential real client information.

**Valuation date:** 2026-09-30. `as_of` no later than this for financial data; report generation date may be later. Projection FY2026E: use 9M actual synthetic + projected Q4. Full forecast FY2027–FY2031. Prior period 9M2025 included for LTM.

## Historical synthetic DRE (R$ mi)

| Item | FY2023 | FY2024 | FY2025 | 9M2025 | 9M2026 |
|---|---:|---:|---:|---:|---:|
| Net revenue | 58.00 | 72.00 | 88.00 | 64.00 | 75.00 |
| COGS | (32.00) | (39.00) | (47.00) | (34.60) | (40.80) |
| Operating expenses excl. D&A | (15.00) | (18.00) | (22.00) | (16.20) | (18.40) |
| EBITDA | 11.00 | 15.00 | 19.00 | 13.20 | 15.80 |
| D&A | (2.50) | (3.00) | (3.50) | (2.50) | (2.80) |
| EBIT | 8.50 | 12.00 | 15.50 | 10.70 | 13.00 |
| Net financial expenses | (1.50) | (2.00) | (2.50) | (1.80) | (2.00) |
| Pretax income | 7.00 | 10.00 | 13.00 | 8.90 | 11.00 |
| Simplified synthetic tax at 34% | (2.38) | (3.40) | (4.42) | (3.026) | (3.74) |
| Net income | 4.62 | 6.60 | 8.58 | 5.874 | 7.26 |

LTM ending September 2026: FY2025 − 9M2025 + 9M2026 => **Revenue 99.00; EBITDA 21.60; D&A 3.80; EBIT 17.80; net interest 2.70; net income 9.966**. Not an annualized 9M figure.

## Synthetic balance sheet and cash flow

Files `examples/synthetic_balance_sheet.csv`, `examples/synthetic_cash_flow.csv` and `examples/synthetic_income_statement.csv` are immutable reference fixtures. The model must **recalculate** derived financial metrics and assert identities rather than trust manually-entered EBITDA/CF.

FY2025 short + long term financial debt = 5 + 10 = 15.00; cash = 9.00. At 2026-09-30, financial debt = 6 + 12 = 18.00; cash = 11.00; **initial book net debt = 7.00**. This is NOT yet deal-adjusted debt-like amount, and does not automatically include IFRS16 leases or contingent liabilities.

## Deal-specific QoE issues (all synthetic, amounts and rationales to be challenged)

| ID | Issue | Initial hypothesis | Treatment pending diligence |
|---|---|---|---|
| Q01 | one-time ERP implementation spend in 2025 | +R$0.8 EBITDA adjustment | Only add back if truly non-recurring, evidenced, not needed to sustain business |
| Q02 | founder compensation below market | −R$0.6 EBITDA normalization | Adjust to defensible replacement cost |
| Q03 | customer representing 27% of LTM revenue | downside haircut / scenario risk | Do not manufacture add-back; concentration risk affects forecast |
| Q04 | R$2.0 disputed tax exposure | conditional debt-like classification | Avoid automatic deduction; define probability, legal review and no duplication |
| Q05 | 2026 unusual receivables ageing | possible 0.9 impairment | Review collectability and earnings/price treatment distinctly |
| Q06 | capitalized software development | accounting normalization concern | Evaluate EBITDA/capex consistency and sustained investment |

Default QoE illustrative adjusted FY2025 EBITDA = **19.0 + 0.8 − 0.6 = 19.2**, provided evidence statuses accepted; **not** LTM QoE unless reconciled for dates.

## Hypothetical strategic logic

- Strategic buyer: access industrial analytics IP and installed clients, sales-channel cross-sell; risks: integration, customer concentration, retention of founder engineering team.
- Financial sponsor: scalable recurring revenue and add-on strategy; risks: margin sustainability, leverage, churn, rates.
- Standalone valuation independent of purchaser-specific synergies. Synergies in separate buyer-value and feasibility module; explicit realization probabilities and one-time integration costs.

## Suggested scenario assumptions (analyst illustrative, do not portray as market forecasts)

| Driver | Downside | Base | Upside |
|---|---:|---:|---:|
| FY2027 revenue growth | 5% | 12% | 18% |
| Growth deceleration, pp/year, FY2028–2031 | −1.0 | −1.5 | −2.0 |
| Long-run EBITDA margin convergence | 17% | 22% | 25% |
| Capex/revenue | 8% | 6% | 5% |
| Operating NWC/revenue | 11% | 9% | 7% |
| Tax rate for illustrative analysis | 34% | 34% | 34% |
| Terminal perpetual growth | assumption, validated vs WACC | assumption | assumption |

Model 2026E by adding explicit Q4 assumption to the observed synthetic 9M, not by calling 9M FY. Derive margins, capex, taxes and ΔNWC from coherent schedules; scenario assumptions can be edited independently.

## Deal economics illustrative (not a valuation conclusion)

Proposed hypothetical bid: EV R$160.0 mi. Initial adjusted cash/debt-like bridge at closing: cash 11.0, interest-bearing debt 18.0, other debt-like items **0 until verified**, minority/preferred **0 if verified absent**. Target normalized NWC to be computed using documented historical monthly schedule, not entered as an unsupported numeric fact. Equity consideration before WC true-up/transaction expenses: **R$153.0 mi** (160 − 18 + 11), *only under these assumptions*. Split e.g. R$138.0 upfront + up to R$15.0 earn-out is a **consideration composition**, not an additional R$15 on top of the R$153. Choose how earn-out PV impacts bid economics and clearly separate maximum contingent consideration from expected value. If partial share sale, show dilution/rollover separately.

## Investment committee question

At a proposed EV of R$160.0 mi, does NexaOps create risk-adjusted value for a strategic or financial acquirer after diligence, NWC, founder retention, synergies and closing conditions? Produce a defendable **proceed / renegotiate / walk away** with price sensitivity and explicit unresolved risks. A polished spreadsheet alone is insufficient.
