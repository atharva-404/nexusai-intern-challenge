# NexusAI Intern Challenge

This repository contains all required tasks:

- `task1/` AI Message Handler
- `task2/` PostgreSQL Schema + Async Repository
- `task3/` Parallel Data Fetcher
- `task4/` Escalation Decision Engine + pytest tests
- `ANSWERS.md` Written design answers

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Task 1: AI Message Handler

File: `task1/message_handler.py`

### What is implemented
- Async function `handle_message(customer_message, customer_id, channel)`.
- Returns dataclass `MessageResponse` with required fields.
- Uses OpenAI API (`AsyncOpenAI`) with telecom-specific system prompt.
- Explicit error handling:
  - Empty input -> immediate error response without API call.
  - Timeout after 10s using `asyncio.wait_for`.
  - Rate limit -> waits 2s and retries once.
- Channel formatting logic:
  - `voice`: max 2 sentences
  - `whatsapp`: line-broken short style
  - `chat`: standard text

## Task 2: Database Schema and Repository

Files:
- `task2/schema.sql`
- `task2/repository.py`

### What is implemented
- `CREATE TABLE call_records` with:
  - customer phone, channel, transcript, AI response, outcome
  - confidence score (0 to 1 constraint)
  - CSAT score (nullable, 1 to 5 constraint)
  - timestamp (`created_at`) and duration (`duration_seconds`)
  - `intent_type` for analytics query support
- 3 indexes with inline reason comments.
- Async repository class `CallRecordRepository`:
  - `save(call_data: dict)`
  - `get_recent(phone: str, limit: int = 5) -> list`
- All SQL uses parameterized queries.
- Analytics function `get_lowest_resolution_intents(pool)` to return top 5 lowest-resolution intents in last 7 days with avg CSAT.

## Task 3: Parallel Data Fetcher

File: `task3/data_fetcher.py`

### What is implemented
- Async mocks with realistic latency and data:
  - `fetch_crm` (200-400ms)
  - `fetch_billing` (150-350ms, 10% timeout chance)
  - `fetch_ticket_history` (100-300ms)
- `fetch_sequential(phone)` and `fetch_parallel(phone)` with timing.
- Parallel uses `asyncio.gather(..., return_exceptions=True)` and does not crash on failures.
- Failed source returns `None`, warning is logged.
- Results merged into `CustomerContext` dataclass with:
  - `data_complete` boolean
  - `fetch_time_ms` float

### Timing output (sample)

Run:
```bash
python task3/data_fetcher.py
```

Observed sample:
```text
Average sequential time (5 runs): 798.90 ms
Average parallel time   (5 runs): 336.44 ms
Average speedup:                   2.37x
```

## Task 4: Escalation Decision Engine

Files:
- `task4/decision_engine.py`
- `task4/test_decision_engine.py`

### What is implemented
- Function `should_escalate(customer_context, confidence_score, sentiment_score, intent) -> (bool, str)`.
- Implements all 6 rules exactly.
- Added deterministic precedence where `service_cancellation` is absolute and evaluated first.
- 8 pytest tests included:
  - 6 rule tests
  - 2 edge tests
- Every test has a docstring explaining purpose and relevance.


Run tests:
```bash
python -m pytest task4/ -v
```

## Rule Conflict Reasoning (Task 4 README requirement)

When multiple rules are true, this implementation applies deterministic priority by evaluation order. `service_cancellation` is treated as a hard safety/business override and is checked first, because cancellation intent has the highest churn and compliance sensitivity. After that, low confidence and customer risk signals are checked before business-priority checks. This means in a conflict such as confidence `0.90` with intent `service_cancellation`, escalation still happens because cancellation is intentionally dominant. The main benefit is predictable behavior: every agent and developer can explain why the same input always gives the same escalation result.
