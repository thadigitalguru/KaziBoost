# Skill: WhatsApp Commerce + M-Pesa Reliability

## Purpose
Design robust conversational commerce and payment workflows for Kenyan SMEs.

## Core Heuristics
1. Webhooks are unreliable by nature: implement retries and idempotency.
2. Payment success only after verified callback.
3. Always provide human-handoff path from bot interactions.
4. Preserve conversation context in CRM timeline.
5. Expose clear operational states for staff (pending, paid, failed, needs follow-up).

## Outputs
- Conversation state machine definitions
- Payment state and reconciliation logic
- Failure-mode and incident playbooks
