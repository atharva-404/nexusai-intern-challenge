CREATE TABLE IF NOT EXISTS call_records (
    id BIGSERIAL PRIMARY KEY,
    customer_phone VARCHAR(20) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('voice', 'whatsapp', 'chat')),
    intent_type VARCHAR(100) NOT NULL DEFAULT 'unknown',
    transcript TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    outcome VARCHAR(20) NOT NULL CHECK (outcome IN ('resolved', 'escalated', 'failed')),
    confidence_score DOUBLE PRECISION NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    csat_score SMALLINT NULL CHECK (csat_score >= 1 AND csat_score <= 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds >= 0)
);

CREATE INDEX IF NOT EXISTS idx_call_records_phone_created_at
ON call_records (customer_phone, created_at DESC);
-- WHY: Fast retrieval of recent interactions for a specific customer.

CREATE INDEX IF NOT EXISTS idx_call_records_created_at
ON call_records (created_at DESC);
-- WHY: Speeds up time-window analytics (for example, last 7 days).

CREATE INDEX IF NOT EXISTS idx_call_records_intent_outcome
ON call_records (intent_type, outcome);
-- WHY: Optimizes grouping/filtering by intent and resolution outcome for reporting.

