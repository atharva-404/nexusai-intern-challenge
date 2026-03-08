import asyncio
import json
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI


ALLOWED_CHANNELS = {"voice", "whatsapp", "chat"}


@dataclass
class MessageResponse:
    response_text: str
    confidence: float
    suggested_action: str
    channel_formatted_response: str
    error: Optional[str]


SYSTEM_PROMPT = """
You are a senior telecom support agent for NexusAI Telecom.
Your goals:
1) Resolve customer issue quickly and clearly.
2) Be empathetic, concise, and policy-safe.
3) Never invent account actions you did not perform.
4) When risk is high (billing dispute, fraud, cancellation), suggest escalation.

Output strict JSON with keys:
- response_text (string)
- confidence (number between 0 and 1)
- suggested_action (string)

Style rules:
- If channel is voice, keep response_text to max 2 sentences and speak naturally.
- If channel is whatsapp, use short paragraphs and action-oriented language.
- If channel is chat, you may provide a longer, structured answer.
""".strip()


def _channel_format(text: str, channel: str) -> str:
    if channel == "voice":
        sentences = [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]
        return ". ".join(sentences[:2]) + ("." if sentences else "")
    if channel == "whatsapp":
        return text.replace(". ", ".\n")
    return text


def _safe_parse_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "response_text": content.strip() or "I am sorry, I could not understand the request fully.",
            "confidence": 0.5,
            "suggested_action": "clarify_customer_issue",
        }


def _is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "rate limit" in message or "429" in message


async def handle_message(customer_message: str, customer_id: str, channel: str) -> MessageResponse:
    """
    Process an inbound customer message and return a structured AI response.
    """
    if channel not in ALLOWED_CHANNELS:
        return MessageResponse(
            response_text="",
            confidence=0.0,
            suggested_action="validate_channel",
            channel_formatted_response="",
            error=f"invalid_channel:{channel}",
        )

    if not customer_message or customer_message.strip() == "":
        return MessageResponse(
            response_text="",
            confidence=0.0,
            suggested_action="request_valid_message",
            channel_formatted_response="",
            error="empty_input",
        )

    client = AsyncOpenAI()
    user_prompt = (
        f"Customer ID: {customer_id}\n"
        f"Channel: {channel}\n"
        f"Customer message: {customer_message}\n\n"
        "Respond only with JSON."
    )

    async def _call_api() -> dict:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = completion.choices[0].message.content or ""
        return _safe_parse_json(content)

    try:
        parsed = await asyncio.wait_for(_call_api(), timeout=10.0)
    except asyncio.TimeoutError:
        return MessageResponse(
            response_text="",
            confidence=0.0,
            suggested_action="retry_later",
            channel_formatted_response="",
            error="api_timeout_10s",
        )
    except Exception as exc:
        if _is_rate_limit_error(exc):
            try:
                await asyncio.sleep(2)
                parsed = await asyncio.wait_for(_call_api(), timeout=10.0)
            except Exception as retry_exc:
                return MessageResponse(
                    response_text="",
                    confidence=0.0,
                    suggested_action="retry_later",
                    channel_formatted_response="",
                    error=f"api_rate_limit_retry_failed:{retry_exc}",
                )
        else:
            return MessageResponse(
                response_text="",
                confidence=0.0,
                suggested_action="investigate_error",
                channel_formatted_response="",
                error=f"api_error:{exc}",
            )

    response_text = str(parsed.get("response_text", "")).strip()
    confidence_raw = parsed.get("confidence", 0.0)
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    suggested_action = str(parsed.get("suggested_action", "follow_up")).strip() or "follow_up"

    return MessageResponse(
        response_text=response_text,
        confidence=confidence,
        suggested_action=suggested_action,
        channel_formatted_response=_channel_format(response_text, channel),
        error=None,
    )
