# Task 5: Written Design Answers

## Q1
I would not wait for the full sentence every time, because that adds delay and makes the assistant feel slow in a live call. But I also would not run full DB queries on every 200ms partial transcript, because that can create too much load and noisy results. My approach is a hybrid trigger-based method. First, buffer partial chunks in a short sliding window (for example last 1-2 seconds). Then run lightweight intent scoring on that buffer. Only when confidence crosses a threshold, or when we detect strong keywords like "cancel", "refund", "no internet", we fire early DB lookups in background. Final transcript still does one full authoritative query pass.

Tradeoff wise, early querying improves response speed and can prefetch useful context before the customer finishes speaking. But if we trigger too early, we may fetch wrong context due to incomplete words and changing intent. To control that, I would add debounce (e.g., no repeated query for same intent within 1 second), cache previous results per call session, and cancel stale async tasks when newer transcript chunks arrive. This gives better latency while keeping DB cost and false matches under control.

## Q2
One failure mode is "high CSAT but wrong root cause." Sometimes customers give 4 or 5 just because the agent was polite, even if the technical fix was temporary. If we auto-add those resolutions, after 6 months the knowledge base can fill with shallow fixes like repeated reboot steps that do not solve underlying issues. Prevention: require quality gates beyond CSAT, such as low repeat-contact rate for 7-14 days and no reopen ticket for same intent before promotion.

Second failure mode is data drift and policy risk. A resolution that was valid in month 1 may become invalid after plan changes, backend migration, or new billing policy. Auto-adding without expiration can spread outdated advice. Prevention: add versioning and expiration metadata per article, plus monthly revalidation jobs. If a resolution starts showing high escalation or complaint metrics, auto-demote it and send for human review.

I would also include content deduplication using semantic similarity so near-duplicate answers do not crowd the KB. This keeps quality stable over time and avoids "knowledge base pollution."

## Q3
For this message, the AI should treat it as high-risk immediately. Step 1: detect signals: outage duration (4 days), repeat contacts (3 times), strong negative sentiment, and explicit cancellation intent. Step 2: fetch customer context in parallel (account status, outage tickets, billing, previous complaints). Step 3: run escalation rules. Here at least three rules likely trigger: angry sentiment, repeat complaint, and service cancellation intent. So escalation should be immediate.

What AI says to customer: "I am really sorry you have faced this for 4 days and had to call multiple times. I am escalating you right now to a senior human specialist who can process cancellation or provide a final resolution today."

What AI passes to human agent should be structured:
- customer statement summary
- detected intent: service_cancellation
- sentiment score and reason
- repeat-contact count and ticket IDs
- outage duration extracted from transcript
- any billing/VIP flags
- recommended next action: retention + technical supervisor handoff

Important part is AI should not argue with customer at this stage. It should acknowledge frustration, avoid generic troubleshooting loops, and reduce further effort from customer side.

## Q4
The single most important addition I would make is a "next-best-action policy engine" with feedback learning. Right now escalation logic is rule-based, which is good for safety, but after escalation we still need consistent high-quality actions. This engine would choose from a small set of approved actions like: instant credit offer, senior technical callback slot, proactive outage SMS enrollment, or cancellation retention workflow. Input features would include intent, sentiment, repeat-contact count, outage history, VIP tier, and last action taken.

How I would build it: start with human-defined policy table + guardrails (no unsafe actions), then add an offline ranking model trained on outcomes (resolution rate, CSAT, repeat calls in 7 days). In production, serve top action with confidence and fallback rules. Keep full audit logs for every recommendation.

How I would measure success:
- reduction in repeat calls within 7 days
- increase in first-contact resolution
- CSAT uplift by intent segment
- reduced average handling time for escalated cases

If these metrics improve while complaint rate stays stable, the feature is working. If not, rollback to rules-only for affected intents.
