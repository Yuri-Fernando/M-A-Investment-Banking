# End-to-end deal execution — sell-side and buy-side

## Sell-side process gates

| Stage | Entry gate | Analyst deliverables | Exit gate |
|---|---|---|---|
| 0 Mandate readiness | synthetic engagement thesis approved | timeline, valuation outline, information request | scope documented |
| 1 Financial preparation | historical data | reconciled DRE/BP/DFC, QoE, NWC, normalized EBITDA | quality signoff |
| 2 Initial valuation | reasonable forecasts | DCF, market comps, valuation football field | valuation committee review |
| 3 Marketing prep | approved numbers and narrative | anonymous teaser, CIM, management presentation, buyer longlist | partner/client simulation approval |
| 4 Initial outreach simulation | sanitized materials | anonymous buyer log, NDA status, Q&A | IOIs received (fictional) |
| 5 Bids and exclusivity | IOIs | bid matrix: price vs conditions vs financing | preferred buyer/LOI |
| 6 Confirmatory DD | permitted simulated VDR | DD log, QoE issues, NWC peg, net debt schedule | red flags adjudicated |
| 7 Documentation | LOI economics | SPA price mechanism checklist, escrow/earnout illustration | mock signoff (NOT legal contract) |
| 8 Closing simulation | all stage checks | funds-flow illustration, final price bridge, checklist | `CLOSED_SIMULATED` only |

## Buy-side process gates

`Acquisition thesis -> industry mapping/target shortlist -> screening scorecard -> standalone and synergy models -> investment committee -> IOI/LOI -> confirmatory diligence -> financial structuring -> approvals -> simulated close/post-merger integration plan`.

Buy-side target score examples: strategic fit (30%), recurring revenue quality (20%), margin/cash conversion (20%), valuation (15%), operational/integration risk (15%). Weights are *hypothetical analyst choices* and must be configurable. Scoring missing info as zero biases the rank: use `unknown` and confidence bands.

## Buyer funnel — synthetic illustrative counts only

Longlist 24, priority shortlist 10, simulated NDA 6, indicative offers 3, LOIs 2, final mock selection 1. Counts are not real outreach results. For each simulated buyer track sector fit, geography, source/counterparty type, likely synergies, financing constraints, status and confidentiality gate. No real email addresses.

## States

`DRAFT -> REVIEW_REQUIRED -> APPROVED -> DISTRIBUTED_SIMULATED -> ARCHIVED`, artifact lifecycle. Deal states include `SCREENING`, `VAL_DRAFT`, `MARKETING_SIMULATED`, `IOI_SIMULATED`, `LOI_SIMULATED`, `DD_SIMULATED`, `SPA_NEGOTIATION_SIMULATED`, `CLOSED_SIMULATED` and `STOPPED_SIMULATED`. Invalid state transitions must fail. Every stage change logs actor, date, rationale and evidence ID.

## Decision register at each gate

Partner review should answer: why does buyer care? what could destroy valuation? is cash conversion real? which adjustments are still disputed? what exactly is paid at closing? which assumptions drive range? Is price justified by standalone value or only synergy? Evidence table, approval and a conditional recommendation mandatory.

## Deal structuring illustrations

- 100% cash buyout vs 70% primary/secondary vs founder rollover — distinguish injected cash into company from seller cash proceeds.
- Earn-out tied to defined net revenue/EBITDA, audited on schedule; qualitative accounting/manipulation protections to be reviewed by counsel.
- Acquisition debt versus target debt; target-level EV is distinct from buyer financing/cash requirements.
- SPA economic terms: cash-free/debt-free, normalized NWC, working capital true-up vs locked-box, leakage, seller fees, warranties/indemnities, escrow, reps and conditions precedent; the mock cannot make these legally valid.
- M&A merger control: keep CADE screening as a legal gate based on economic group turnover and transaction structure; no automatic conclusion from target revenue alone.

## Closing packet (simulation)

Approved IC memo; clean source pack/checks; legal/financial/tax DD flags matrix; final offer version; price waterfall and funds-flow; conditions checklist; no-live-signatures placeholder; post-close 100-day plan. Stamp all with `SIMULATED — NOT A REAL TRANSACTION`.
