# Client Communication Agents — Nexora AI

## Goal
Add two separate client-facing agents to the Nexora workflow. This document defines the required behavior and the real integration boundary; it does not claim messaging or telephony is connected yet.

## Agent 1: Client Messaging & Product Value
Responsibilities:
1. Read the full client message and relevant approved product/service information.
2. Classify intent (new enquiry, product question, onboarding, support, complaint, pricing, refund, sales/profit question, or human escalation).
3. Summarize what the client is asking and identify missing facts. Ask one focused question only when needed.
4. Draft a concise, natural, context-aware reply that directly helps the client.
5. Explain how the product may create value or profit using the client's stated use case, measurable assumptions, costs, and possible outcomes.
6. Never guarantee profits, invent case studies, promise unsupported features, or present projections as actual results. Separate known facts from assumptions and show a simple calculation where useful.
7. Detect complaints, payment disputes, security/privacy incidents, legal threats, refunds, or high-stakes requests and route them to a human.
8. Keep conversation history and contact data private; use it only for the stated support/sales purpose.

## Agent 2: Incoming Call Receptionist
Responsibilities:
1. Answer calls only after a supported phone provider, number, webhook, and voice service are configured and tested.
2. Introduce itself transparently as Nexora's virtual assistant; never impersonate a human.
3. Listen, transcribe, and summarize the caller's intent; ask short clarifying questions and speak politely.
4. Give only approved, current product/service information. Do not promise profit, pricing, delivery dates, or capabilities without verified source data.
5. Offer the official WhatsApp or Instagram contact route and, when possible, send the caller the approved link by SMS/WhatsApp only with consent and a configured integration.
6. For complaints, sensitive data, urgent incidents, or questions outside approved knowledge, offer human follow-up and create a callback note.
7. Handle poor audio, language mismatch, silence, and provider failure gracefully; do not pretend to understand speech that was not reliably transcribed.
8. Disclose recording/transcription where applicable, collect only necessary data, and follow local law and provider/platform policies.

## Shared response flow
Incoming message/call -> consent and channel checks -> intent detection -> approved knowledge retrieval -> draft/response -> safety and factuality checks -> send/speak if the channel is configured and the action is authorized -> log outcome -> escalate when needed.

## Send and speak permissions
- Start in draft/review mode. Do not send outbound messages or make calls until the owner approves the final scripts, channel accounts, templates, and operating rules.
- After approval, automate only routine, low-risk replies within a defined allowlist. Require human review for complaints, refunds, contracts, discounts, financial commitments, unusual requests, and any uncertain answer.
- Never ask clients for passwords, OTPs, card details, or private keys.
- Do not claim a message was delivered or a call was answered unless the provider returns a successful event/status.
- Include rate limits, duplicate-event/idempotency handling, audit logs, retry limits, opt-out handling, and a kill switch.

## Product profit/value explanation
Use a transparent structure:
- Client goal and baseline (known facts only)
- How the product changes a process or metric
- Potential benefit formula, for example: incremental monthly contribution = additional completed sales × contribution margin per sale - recurring product cost - additional operating costs
- Clearly labelled assumptions and conservative/base/upside scenarios only when inputs support them
- Risks, limitations, time-to-value, and how results will be measured
Never equate revenue with profit and never guarantee outcomes.

## Required integration work before live operation
- Choose and configure a compliant WhatsApp Business messaging provider and/or approved Instagram messaging integration.
- Configure a telephony provider that supports inbound calls, speech recognition, text-to-speech, webhooks, and escalation/callback handling.
- Store credentials in provider-managed secrets, not source code or logs.
- Confirm official contact links, approved product facts, business hours, supported languages, escalation contact, and retention policy.
- Add integration tests with mocked provider events plus staging tests using a real test number/account.
- Verify consent/opt-out, duplicate webhooks, provider outage, low-confidence transcription, prompt injection in client messages, and complaint escalation.
- Do not enable production auto-send/auto-answer until the owner has approved scripts and the full acceptance checklist passes.

## Audio script input
The owner will supply an audio sample for the phone receptionist. Use it as guidance for tone and wording, not as permission to clone a real person's voice. Until the audio arrives, use a neutral, professional voice and keep the spoken script editable.

## Current status
Specification recorded. This repository's current text-only worker does not by itself receive WhatsApp/Instagram events, send messages, receive phone calls, or speak on a phone line. Those capabilities require the integrations above and successful end-to-end tests.