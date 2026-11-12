import pytest

from ma_deallab.contracts import ModelError
from ma_deallab.transaction import CLOSING_GATES, STAGES, ArtifactReview, Workflow, score_buyer, vdr_access


def test_p01_draft_cannot_distribute():
    with pytest.raises(ModelError):
        ArtifactReview().transition("DISTRIBUTED_SIMULATED", "analyst")


def test_review_lifecycle():
    item = ArtifactReview()
    for status, role in (
        ("REVIEW_REQUIRED", "analyst"),
        ("APPROVED", "reviewer"),
        ("DISTRIBUTED_SIMULATED", "reviewer"),
        ("ARCHIVED", "reviewer"),
    ):
        item.transition(status, role)
    assert item.state == "ARCHIVED"


def test_p02_no_jump_to_loi():
    with pytest.raises(ModelError, match="INVALID_TRANSITION"):
        Workflow().advance("LOI_SIMULATED", "reviewer", "a", "e", "r")


def test_loi_shortlist_gate():
    flow = Workflow(stage="IOI_SIMULATED")
    with pytest.raises(ModelError, match="Shortlist"):
        flow.advance("LOI_SIMULATED", "reviewer", "a", "e", "r")


@pytest.mark.parametrize("role", ["viewer", "counterparty", "analyst"])
def test_reviewer_required(role):
    with pytest.raises(ModelError, match="Reviewer"):
        Workflow().advance("VAL_DRAFT", role, "a", "e", "r")


def test_p03_close_requires_all_gates_and_no_high():
    flow = Workflow(stage="SPA_NEGOTIATION_SIMULATED")
    approvals = dict.fromkeys(CLOSING_GATES, True)
    with pytest.raises(ModelError, match="CLOSING_BLOCKED"):
        flow.advance("CLOSED_SIMULATED", "reviewer", "a", "e", "r", approvals, unresolved_high=1)
    with pytest.raises(ModelError, match="CLOSING_BLOCKED"):
        flow.advance("CLOSED_SIMULATED", "reviewer", "a", "e", "r", {})


def test_simulated_happy_path_with_explicit_fake_approvals():
    flow = Workflow()
    approvals = {**dict.fromkeys(CLOSING_GATES, True), "shortlist": True}
    for stage in STAGES[1:]:
        flow.advance(stage, "reviewer", "fake reviewer", "DEMO_APPROVAL", "test simulation", approvals)
    assert flow.stage == "CLOSED_SIMULATED"
    assert len(flow.events) == 7
    assert all(e["timestamp"] and e["evidence_id"] for e in flow.events)


def test_p04_vdr_permissions():
    assert not vdr_access("viewer", False)
    assert not vdr_access("counterparty", False)
    assert vdr_access("analyst", False)
    assert vdr_access("viewer", True)
    assert not vdr_access("counterparty", True)


def test_missing_buyer_score_interval():
    s = score_buyer({"fit": 5})
    assert s["coverage"] == 0.3
    assert s["lower"] == 30
    assert s["upper"] == 100
