from task3.data_fetcher import CustomerContext
from task4.decision_engine import should_escalate


def make_context(
    is_vip: bool = False,
    billing_status: str = "paid",
    ticket_history=None,
    data_complete: bool = True,
) -> CustomerContext:
    if ticket_history is None:
        ticket_history = []
    return CustomerContext(
        phone="+91-9000000000",
        account_info={"is_vip": is_vip},
        billing_info={"status": billing_status},
        ticket_history=ticket_history,
        data_complete=data_complete,
        fetch_time_ms=250.0,
    )


def test_rule1_low_confidence():
    """Escalates when confidence is below threshold so uncertain AI output does not reach customers."""
    context = make_context()
    decision, reason = should_escalate(context, confidence_score=0.64, sentiment_score=0.0, intent="billing_issue")
    assert decision is True
    assert reason == "low_confidence"


def test_rule2_angry_customer():
    """Escalates for highly negative sentiment to prioritize de-escalation by a human agent."""
    context = make_context()
    decision, reason = should_escalate(context, confidence_score=0.9, sentiment_score=-0.8, intent="billing_issue")
    assert decision is True
    assert reason == "angry_customer"


def test_rule3_repeat_complaint():
    """Escalates when same intent appears at least three times to avoid repetitive unresolved loops."""
    history = [{"intent": "slow_internet"}, {"intent": "slow_internet"}, {"intent": "slow_internet"}]
    context = make_context(ticket_history=history)
    decision, reason = should_escalate(context, confidence_score=0.95, sentiment_score=0.1, intent="slow_internet")
    assert decision is True
    assert reason == "repeat_complaint"


def test_rule4_service_cancellation_always():
    """Always escalates cancellation intent even when confidence and sentiment look healthy."""
    context = make_context()
    decision, reason = should_escalate(
        context, confidence_score=0.99, sentiment_score=0.8, intent="service_cancellation"
    )
    assert decision is True
    assert reason == "service_cancellation"


def test_rule5_vip_and_overdue():
    """Escalates VIP customers with overdue billing to reduce churn risk and billing disputes."""
    context = make_context(is_vip=True, billing_status="overdue")
    decision, reason = should_escalate(context, confidence_score=0.95, sentiment_score=0.1, intent="billing_issue")
    assert decision is True
    assert reason == "vip_overdue"


def test_rule6_incomplete_data_low_confidence():
    """Escalates when context is incomplete and confidence is below 0.80 to avoid blind automated decisions."""
    context = make_context(data_complete=False)
    decision, reason = should_escalate(context, confidence_score=0.79, sentiment_score=0.1, intent="billing_issue")
    assert decision is True
    assert reason == "incomplete_data_low_confidence"


def test_edge_no_escalation():
    """Does not escalate when all risk checks pass, enabling efficient AI self-service handling."""
    history = [{"intent": "router_restart"}, {"intent": "billing_issue"}]
    context = make_context(ticket_history=history, data_complete=True)
    decision, reason = should_escalate(context, confidence_score=0.90, sentiment_score=0.2, intent="new_connection")
    assert decision is False
    assert reason == "no_escalation"


def test_edge_conflict_cancellation_beats_others():
    """Cancellation intent wins conflicts and escalates even if other signals would not require escalation."""
    context = make_context(is_vip=False, billing_status="paid", data_complete=True)
    decision, reason = should_escalate(
        context, confidence_score=0.95, sentiment_score=0.9, intent="service_cancellation"
    )
    assert decision is True
    assert reason == "service_cancellation"

