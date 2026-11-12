# Golden synthetic fixtures (all invented; R$ millions)

These fixtures create a *coherent* historical 3-statement baseline. Expenses in `synthetic_income_statement.csv` are stored as positive **magnitudes** and subtracted by formulas. Cash flow movements carry algebraic +/- signs. `synthetic_balance_sheet.csv` is a stock snapshot at the corresponding date. `2026-09-30` income/cash flow covers 9 months, while the corresponding balance sheet is AT_DATE.

Expected sanity values:

- Balance sheet assets = liabilities + equity: FY2023 **35.0**, FY2024 **41.5**, FY2025 **50.0**, Sep2026 **58.0**.
- Cash: 2023 **6.0**, 2024 **8.0**, 2025 **9.0**, Sep2026 **11.0**.
- Cash flow Δcash: 2024 **+2.0**, 2025 **+1.0**, 9M2026 **+2.0**.
- 2024 CFO **7.60**, 2025 CFO **10.08**, 9M2026 CFO **9.06**.
- NWC used for cash flow (includes income tax payable, unlike some deal definitions): 2023 **3.0**, 2024 **5.0**, 2025 **7.0**, Sep2026 **8.0**.
- 2025 QoE 19.0 + 0.8 − 0.6 = **19.2 EBITDA**, *only after approval*.
- 9M2026 and 9M2025 are used to compute LTM income statement, not stock values.

Note that the 2025 **investment in other noncurrent assets** of R$0.5 mi belongs in investing cash flow; this is why PPE capex of 5.5 plus other investment of 0.5 reconciles the cash movement. 2023 cash flow is not supplied because 2022 opening balance sheet is not supplied. The 2024/2025 statements' retained earnings changes reflect distributions; 9M2026 likewise.

All source IDs beginning `SYNTH_` are clearly simulated, not actual CVM or B3 information. Future observed public data must live in another source namespace.
