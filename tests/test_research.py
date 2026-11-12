from ma_deallab.research import evidence_lookup, monte_carlo
from ma_deallab.services import scenario_assumptions


def test_evidence_never_invents_answer(run):
    result = evidence_lookup(run, "ltm net_revenue")
    assert result
    assert all(item["evidence_id"] in run["metrics"] for item in result)
    assert evidence_lookup(run, "zzzzunknown") == []


def test_monte_carlo_repeatable(case):
    a = scenario_assumptions(case, "base")
    one = monte_carlo(case, a, samples=30)
    assert one == monte_carlo(case, a, samples=30)
    assert one["p10"] <= one["p50"] <= one["p90"]
