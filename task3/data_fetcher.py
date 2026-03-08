import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CustomerContext:
    phone: str
    account_info: Optional[Dict[str, Any]]
    billing_info: Optional[Dict[str, Any]]
    ticket_history: Optional[List[Dict[str, Any]]]
    data_complete: bool
    fetch_time_ms: float


async def fetch_crm(phone: str) -> Dict[str, Any]:
    await asyncio.sleep(random.uniform(0.2, 0.4))
    return {
        "phone": phone,
        "customer_id": "CUST-102938",
        "name": "Aarav Mehta",
        "plan": "Fiber 300 Mbps",
        "is_vip": random.choice([True, False]),
    }


async def fetch_billing(phone: str) -> Dict[str, Any]:
    await asyncio.sleep(random.uniform(0.15, 0.35))
    if random.random() < 0.10:
        raise TimeoutError(f"Billing timeout for {phone}")
    return {
        "phone": phone,
        "status": random.choice(["paid", "overdue"]),
        "last_payment_date": "2026-02-24",
        "outstanding_amount": random.choice([0, 499, 899]),
    }


async def fetch_ticket_history(phone: str) -> List[Dict[str, Any]]:
    await asyncio.sleep(random.uniform(0.1, 0.3))
    intents = ["slow_internet", "billing_issue", "router_restart", "service_cancellation"]
    return [
        {"ticket_id": f"TKT-{1000+i}", "intent": random.choice(intents), "status": "closed"}
        for i in range(5)
    ]


async def fetch_sequential(phone: str) -> CustomerContext:
    start = time.perf_counter()
    crm = await fetch_crm(phone)
    try:
        billing = await fetch_billing(phone)
    except TimeoutError as exc:
        logger.warning("Sequential fetch warning: billing failed: %s", exc)
        billing = None
    tickets = await fetch_ticket_history(phone)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return CustomerContext(
        phone=phone,
        account_info=crm,
        billing_info=billing,
        ticket_history=tickets,
        data_complete=all(item is not None for item in (crm, billing, tickets)),
        fetch_time_ms=elapsed_ms,
    )


async def fetch_parallel(phone: str) -> CustomerContext:
    start = time.perf_counter()
    results = await asyncio.gather(
        fetch_crm(phone),
        fetch_billing(phone),
        fetch_ticket_history(phone),
        return_exceptions=True,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    crm_result, billing_result, ticket_result = results

    crm = crm_result if not isinstance(crm_result, Exception) else None
    billing = billing_result if not isinstance(billing_result, Exception) else None
    tickets = ticket_result if not isinstance(ticket_result, Exception) else None

    for source_name, result in [("crm", crm_result), ("billing", billing_result), ("tickets", ticket_result)]:
        if isinstance(result, Exception):
            logger.warning("Parallel fetch warning: %s failed: %s", source_name, result)

    return CustomerContext(
        phone=phone,
        account_info=crm,
        billing_info=billing,
        ticket_history=tickets,
        data_complete=all(item is not None for item in (crm, billing, tickets)),
        fetch_time_ms=elapsed_ms,
    )


async def run_timing_demo(phone: str = "+91-9876543210", runs: int = 5) -> Dict[str, float]:
    sequential_times = []
    parallel_times = []

    for i in range(runs):
        # Keep run-to-run random values comparable while still using random latency.
        random.seed(100 + i)
        sequential_context = await fetch_sequential(phone)
        random.seed(100 + i)
        parallel_context = await fetch_parallel(phone)
        sequential_times.append(sequential_context.fetch_time_ms)
        parallel_times.append(parallel_context.fetch_time_ms)

    avg_sequential = sum(sequential_times) / len(sequential_times)
    avg_parallel = sum(parallel_times) / len(parallel_times)
    speedup = avg_sequential / avg_parallel if avg_parallel > 0 else 0.0

    print(f"Average sequential time ({runs} runs): {avg_sequential:.2f} ms")
    print(f"Average parallel time   ({runs} runs): {avg_parallel:.2f} ms")
    print(f"Average speedup:                   {speedup:.2f}x")

    return {
        "sequential_ms": avg_sequential,
        "parallel_ms": avg_parallel,
        "speedup_x": speedup,
    }


if __name__ == "__main__":
    asyncio.run(run_timing_demo())
