"""Optional offline stress and evidence lookup, no hosted LLM or automatic actions."""

import random
import re
from dataclasses import replace

from .contracts import ModelError
from .finance import model


def monte_carlo(case, assumptions, samples=500, seed=20261111):
    """Illustrative triangular growth/margin uncertainty, not market-calibrated risk.

    Draws are independent and bounded; no deal portfolio or empirical probabilities
    are inferred. Negative-cash samples are reported instead of silently discarded.
    """
    if not 10 <= samples <= 10000:
        raise ModelError("Use 10..10000 samples")
    rng = random.Random(seed)
    values = []
    negative_cash = 0
    for _ in range(samples):
        growth = rng.triangular(
            max(0, assumptions.growth - 0.04), assumptions.growth + 0.04, assumptions.growth
        )
        margin = rng.triangular(
            max(0.08, assumptions.terminal_margin - 0.03),
            min(0.5, assumptions.terminal_margin + 0.03),
            assumptions.terminal_margin,
        )
        result = model(case, replace(assumptions, growth=growth, terminal_margin=margin))
        values.append(result["valuation"]["ev"])
        negative_cash += bool(result["warnings"])
    values.sort()
    return {
        "seed": seed,
        "samples": samples,
        "p10": values[int(0.1 * (samples - 1))],
        "p50": values[int(0.5 * (samples - 1))],
        "p90": values[int(0.9 * (samples - 1))],
        "negative_cash_samples": negative_cash,
        "distribution": "Independent illustrative triangular growth/margin",
        "limitation": "Uncalibrated model sensitivity, not investment probabilities",
    }


def evidence_lookup(run: dict, query: str, limit=10) -> list:
    """Deterministic registry search. No generated narrative or unsupported numbers."""
    tokens = [t for t in re.split(r"[^a-z0-9_]+", query.lower()) if len(t) > 2]
    if not tokens:
        return []
    scored = []
    for key, entry in run["metrics"].items():
        score = sum(token in key.lower() for token in tokens)
        if score:
            scored.append((score, key, entry))
    return [
        {"evidence_id": key, **entry} for _, key, entry in sorted(scored, key=lambda x: (-x[0], x[1]))[:limit]
    ]
