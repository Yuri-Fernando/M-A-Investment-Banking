# Project engineering rules

- Runtime: Python 3.10 only. On Windows use `py -3.10` or the existing Python310 executable.
- Read README.md, docs/ARCHITECTURE.md and docs/MODEL_POLICY.md before changing financial behavior.
- The runnable package, tests, scripts and CI live at this repository root.
- Keep finance and transaction calculations in the shared engine; UI and reports consume frozen runs.
- Keep money in full BRL internally; fixtures and presentation use BRL millions explicitly.
- Reconcile IS, BS, CF, PPE, debt and equity. Never use a cash or equity balancing plug.
- Preserve source hashes, as-of/publication dates and synthetic/public/assumption classifications.
- Do not invent market prices, monthly working-capital pegs, received bids or real transaction approvals.
- Exports remain drafts. Workflow roles are simulated and do not provide production authentication.
- Validate financial changes with pytest and workbook parity; update evidence only after execution.
- Keep generated outputs, private planning notes, credentials and raw external datasets outside Git.
