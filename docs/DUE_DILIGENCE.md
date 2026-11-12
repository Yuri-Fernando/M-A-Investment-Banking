# Due diligence, QoE and deal-risk manual

## Workstreams and example requests

**Financial:** historical income/BP/CF, monthly trial balance, audit notes, bank statements, AR/AP aging, invoices, contracts, earnings adjustments, forecast driver assumptions, capex capitalization, cash/debt facilities, customer-level revenue, inventory.

**Tax:** filings and liabilities, tax incentives, contingent exposures, unrecognized liabilities; a qualified advisor evaluates actual liability.

**Legal/Corporate:** articles, equity ownership/cap table, change-of-control clauses, liens, contingent litigation, customer/supplier contract restrictions, IP ownership.

**Commercial:** customers, concentration, retention/churn, unit economics, TAM thesis with verified sources, revenue quality, management forecast credibility.

**Operational/IT:** product architecture, IP dependencies, cybersecurity, data rights, technical debt, key person risk, employee/contractor dependencies, integration costs.

**ESG/Compliance/Labor:** licenses, environment, anti-bribery, labor obligations, data privacy and litigation; simulate open issues without real persons' data.

## QoE workflow

1. Start from reported EBITDA per defined period (FY and LTM separately).
2. Propose adjustments with sign, original account, period, recurrence, invoice/evidence ID, tax/cash effect, management view and analyst view.
3. Accept only after reviewer signoff. Show gross proposed vs accepted adjustments; no automatic add-back.
4. Reconcile EBITDA quality to operating cash conversion, recurring revenue and customer concentration.
5. Translate findings into valuation scenario, NWC peg, debt-like schedule or contractual protections **exactly once**.

## NWC peg methodology

Derive from 12–24 monthly observations when available; account for seasonality and growth. Example contractual NWC = trade AR + inventory + operating prepaids − trade AP − operating accruals; exclude cash and financial debt, document taxes and deferred revenue choices. `closing NWC − agreed peg` creates true-up under completion accounts; show payable/receivable direction and no double count of receivable impairment already priced through normalized earnings or debt-like.

## Net debt/debt-like items

Start cash, bank debt, overdrafts, shareholder loans, leasing (policy consistent with enterprise value), unpaid acquisition expenses, unpaid tax liabilities/contingencies *if and as contract defines*; escrow restrictions, trapped cash, deferred obligations. Categorize as `cash`, `financial debt`, `debt-like`, `NWC`, `operating liability`, `excluded/other` with no overlapping inclusion.

## Red flag matrix

Each issue: `issue_id, materiality_R$, likelihood, evidence_grade (A/B/C), purchase_price_effect, earnout_or_indemnity_effect, legal_gate, owner, next_step, decision_status`. Do not monetize qualitative items without a modelled rationale. High-severity/unknown status blocks final no-conditions-close.

## Data room (simulated only)

Sections: Corporate, Finance, Taxes, Commercial, Legal, HR, IT, ESG, Transaction. Documents use fictional text and no real identifiers. Version IDs, document watermark `DEMO`, reviewer roles, access log and due date. Private actual data may not be uploaded to a public demo.

## Deal review deliverables

QoE report with reported/adjusted EBITDA bridges, working capital analysis, net-debt schedule, cash conversion, revenue quality/customer concentration, forecast challenge, red flags and conditional recommendation. Use claims qualified by evidence coverage.
