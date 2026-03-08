from typing import Any, Dict, List

import asyncpg


class CallRecordRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def save(self, call_data: Dict[str, Any]) -> None:
        query = """
        INSERT INTO call_records (
            customer_phone,
            channel,
            intent_type,
            transcript,
            ai_response,
            outcome,
            confidence_score,
            csat_score,
            created_at,
            duration_seconds
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, COALESCE($9, NOW()), $10);
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                call_data["customer_phone"],
                call_data["channel"],
                call_data.get("intent_type", "unknown"),
                call_data["transcript"],
                call_data["ai_response"],
                call_data["outcome"],
                call_data["confidence_score"],
                call_data.get("csat_score"),
                call_data.get("created_at"),
                call_data["duration_seconds"],
            )

    async def get_recent(self, phone: str, limit: int = 5) -> List[Dict[str, Any]]:
        query = """
        SELECT
            id,
            customer_phone,
            channel,
            intent_type,
            transcript,
            ai_response,
            outcome,
            confidence_score,
            csat_score,
            created_at,
            duration_seconds
        FROM call_records
        WHERE customer_phone = $1
        ORDER BY created_at DESC
        LIMIT $2;
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, phone, limit)
        return [dict(row) for row in rows]


async def get_lowest_resolution_intents(pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """
    Returns top 5 intent types with lowest resolution rate in the last 7 days,
    along with average CSAT.
    """
    query = """
    SELECT
        intent_type,
        AVG(CASE WHEN outcome = 'resolved' THEN 1.0 ELSE 0.0 END) AS resolution_rate,
        AVG(csat_score)::FLOAT AS avg_csat
    FROM call_records
    WHERE created_at >= NOW() - INTERVAL '7 days'
    GROUP BY intent_type
    ORDER BY resolution_rate ASC, avg_csat ASC NULLS LAST
    LIMIT 5;
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
    return [dict(row) for row in rows]

