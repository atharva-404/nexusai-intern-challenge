from typing import Tuple

from task3.data_fetcher import CustomerContext


def _intent_repeat_count(context: CustomerContext, intent: str) -> int:
    if not context.ticket_history:
        return 0
    count = 0
    for item in context.ticket_history:
        if isinstance(item, dict) and item.get("intent") == intent:
            count += 1
    return count


def should_escalate(
    customer_context: CustomerContext,
    confidence_score: float,
    sentiment_score: float,
    intent: str,
) -> Tuple[bool, str]:
    # Rule 4 has absolute priority: always escalate for cancellation intent.
    if intent == "service_cancellation":
        return True, "service_cancellation"

    # Rule 1
    if confidence_score < 0.65:
        return True, "low_confidence"

    # Rule 2
    if sentiment_score < -0.6:
        return True, "angry_customer"

    # Rule 3
    if _intent_repeat_count(customer_context, intent) >= 3:
        return True, "repeat_complaint"

    # Rule 5
    is_vip = bool(customer_context.account_info and customer_context.account_info.get("is_vip"))
    billing_overdue = bool(
        customer_context.billing_info
        and str(customer_context.billing_info.get("status", "")).lower() == "overdue"
    )
    if is_vip and billing_overdue:
        return True, "vip_overdue"

    # Rule 6
    if (not customer_context.data_complete) and confidence_score < 0.80:
        return True, "incomplete_data_low_confidence"

    return False, "no_escalation"

