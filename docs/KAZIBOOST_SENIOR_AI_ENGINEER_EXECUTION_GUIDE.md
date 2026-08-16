# KaziBoost Senior AI Engineer Execution Guide

Prepared: 2026-08-16  
Branch: `sol/kaziboost-senior-upgrade-20260805`  
Source: Senior AI Engineer Execution Plan supplied on 2026-08-16

## 1. Executive decision

KaziBoost will be built as a measured, durable, approval-aware lead-to-payment platform for Kenyan service SMEs. We will not add broad live-LLM behavior before the platform can identify tenants, persist business state, enforce permissions, trace outcomes, and fail safely.

The first measurable loop is:

`onboarding -> publish site -> capture attributed lead -> WhatsApp handoff -> qualified/booked outcome -> M-Pesa reconciliation -> funnel report`

AI will assist this loop only through a provider-neutral runtime with typed contracts, safety checks, quotas, trace metadata, and human approval where content can affect a customer or public site.

## 2. Counter-thinking and refined recommendations

### Recommendation: migrate directly to PostgreSQL

**Counterpoint:** A direct rewrite from `InMemoryStore` would preserve accidental coupling and make rollback difficult. It could create a durable version of the wrong aggregate boundaries.

**Refinement:** First define repository interfaces, tenant-scoped query contracts, lifecycle states, idempotency rules, and transaction boundaries. Keep the in-memory implementation as a test double. Then introduce PostgreSQL behind those interfaces with additive migrations and restart/two-worker tests.

### Recommendation: add live LLM calls early

**Counterpoint:** This would increase cost, latency, privacy exposure, prompt-injection risk, and support burden before quality can be measured. Deterministic behavior currently provides a safe fallback.

**Refinement:** Build the AI runtime boundary, capability schemas, prompt registry, safety policies, evaluation fixtures, and telemetry first. Run providers in test/shadow mode before enabling tenant-facing generation.

### Recommendation: finish every dashboard module

**Counterpoint:** More screens can create the appearance of progress while the publish-to-payment journey remains incomplete.

**Refinement:** Replace static assumptions only where they support the activation loop. Prioritize authenticated API reads, truthful empty/loading/error states, and one complete vertical journey over broad UI coverage.

### Recommendation: optimize before production evidence

**Counterpoint:** Query/index and model-routing changes without volume, p95, error, or cost baselines can optimize the wrong path.

**Refinement:** Instrument events and request timing first. Set budgets from observed traffic, then optimize by query plan, funnel drop-off, and cost per activated tenant.

### Recommendation: autonomous WhatsApp replies

**Counterpoint:** Ungrounded replies can make unsupported promises or mishandle sensitive requests.

**Refinement:** Ship human handoff first. Permit autonomous replies only for grounded FAQ classes with confidence, safety, escalation, and audit behavior.

## 3. Agent allocation

These are accountable workstream roles. Each role must review the acceptance criteria and rollback impact before a build is committed.

| Agent role | Responsibility | Required review |
|---|---|---|
| Principal Integrator | Sequence builds, protect branch, run gates, commit/push, maintain roadmap | Every build |
| Product/Activation Agent | Launch segment, activation event, funnel definitions, UX priority | Product-facing builds |
| Backend/Data Agent | Aggregates, repositories, migrations, transactions, tenant scoping | Persistence/API builds |
| Identity/Security Agent | Passwords, sessions, MFA, RBAC, secrets, webhook trust, abuse controls | Auth/security builds |
| Principal AI Agent | Capability contracts, provider adapter, prompt/policy registry, evals, quotas | AI builds |
| Privacy/Compliance Agent | Data classification, retention, redaction, export/deletion, audit safety | Data/AI builds |
| Frontend/UX Agent | Authenticated API client, mobile states, accessibility, journey completion | Web builds |
| Platform/DevOps Agent | CI, environments, queues, readiness, backups, release/rollback | Infrastructure builds |
| Quality/Evaluation Agent | Failing tests first, regression matrix, contract/eval harness, coverage | Every build |
| Independent Senior Reviewer | Counter-argue scope, detect hidden coupling, challenge acceptance claims | Before each push |

## 4. Mandatory build loop

For every build:

1. State user outcome, failure mode, and non-goals.
2. Inspect the current code and previous commits; do not assume the plan matches the repository.
3. Write or update the API, data, error, event, and rollback contract.
4. Add a focused failing test or a measurable baseline artifact.
5. Implement the smallest vertical slice.
6. Add safe audit/metric behavior without logging personal data or secrets.
7. Run focused tests and then the relevant full suite.
8. Run security, tenancy, UX, migration, and rollback review.
9. Reconsider the design using the counterpoint questions below.
10. Commit one coherent build.
11. Push the build and verify local/remote hashes match.
12. Update this guide and the roadmap with evidence.
13. Only then begin the next build.

Counterpoint questions before every push:

- Does this make the activation loop more reliable, or only add surface area?
- Can a tenant access another tenant's record through every new path?
- What happens on retry, timeout, duplicate callback, restart, and partial failure?
- Does a generated result have a typed schema, policy outcome, trace, and review state?
- Can the change be rolled back without data loss or a destructive migration?
- Is the UI truthful for loading, empty, denied, failed, and degraded states?
- What evidence would prove this build improved quality, cost, latency, or conversion?

## 5. Gated build plan

### Build 0 — Baseline, scope lock, and execution guide

**Outcome:** A clean checkout can reproduce the current state and the team has one launch segment and one activation metric.

**Scope:** Baseline commands/results, data inventory, event dictionary, launch decision, agent ownership, and this execution guide.

**Acceptance:** API tests/coverage, web typecheck/build, dependency audits, preview route status, and known warnings are recorded. No implementation begins from an unverified baseline.

**Rollback:** Revert documentation-only commit.

### Build 1 — Repository and domain contract seam

**Outcome:** Domain services can depend on tenant-scoped repository contracts rather than `InMemoryStore` internals.

**Scope:** Typed protocols/interfaces for tenants/users, sites/pages, contacts, conversations, payments, generated content, and audit events; in-memory adapters; contract tests for tenant isolation, not-found behavior, ordering, and idempotency keys.

**Non-goal:** Do not pretend an interface is durable persistence. No blind PostgreSQL copy.

**Exit:** Existing routes remain green; at least one vertical slice uses a repository interface; contracts define transaction/idempotency requirements.

### Build 2 — Durable identity and tenant foundation

**Outcome:** Restart and multi-worker behavior no longer loses identity/session state.

**Scope:** PostgreSQL schema/migrations for tenant/user/session/MFA records, password-hash upgrade path, durable token/session policy, role checks, disposable database tests, and tenant isolation at repository plus HTTP layers.

**Exit:** Two workers observe the same records; restart preserves records; test-mode MFA is explicit; production never exposes test codes.

### Build 3 — Durable activation-loop records

**Outcome:** Sites, leads, conversations, payments, and audit events survive restart with safe lifecycle state.

**Scope:** Aggregates, foreign keys, unique constraints, soft-delete/retention rules, transaction boundaries, provider event IDs, idempotency keys, and reconciliation tests.

**Exit:** Duplicate lead/payment callbacks are harmless; every funnel transition is traceable to a tenant and request/trace ID.

### Build 4 — Provider-neutral AI runtime

**Outcome:** AI capability code cannot call providers directly from route handlers.

**Scope:** `AiProvider`, capability context, prompt/policy registry, typed result validation, timeout/retry/allow-list, redacted telemetry, quota decisions, deterministic fallback, and explicit `blocked`, `needs_review`, `failed`, and `not_ready` states.

**Exit:** A provider can be swapped without route changes; every response has schema, prompt/model/policy versions, trace ID, latency, token estimate, and safety outcome.

### Build 5 — AI evaluation and approval release gate

**Outcome:** Prompt/model changes are tested against Kenyan-language and safety fixtures before release.

**Scope:** English, Swahili, scoped Sheng, grounding, unsupported claims, injection, PII/secrets, regulated advice, FAQ handoff, length, tone, schema, and cost fixtures; review workflow integration.

**Exit:** Evaluation results are reported by capability/language/model/prompt version; unsafe or low-confidence output fails closed or routes to review.

### Build 6 — Authenticated activation-loop UX

**Outcome:** One test tenant can complete the publish -> lead -> WhatsApp -> payment journey through the product UI.

**Scope:** Authenticated API client, session/error handling, site publish, attributed lead capture, handoff-first WhatsApp, M-Pesa reconciliation, next-action onboarding, and mobile workflow checks.

**Exit:** No manual database edits; each transition has a durable record and actionable retry/degraded UI state.

### Build 7 — Measurement and outcome optimization

**Outcome:** The team can connect product work to activation and cost evidence.

**Scope:** Event dictionary implementation, funnel dashboard, p50/p95/error budgets, AI cost per capability/tenant, query plans, cursor pagination/async exports, caching and model routing only where evidence supports it.

**Exit:** Every optimization names a metric movement or risk reduction; cost per activated tenant is visible.

### Build 8 — Production readiness and controlled release

**Outcome:** The first segment can be released with operational ownership and rollback.

**Scope:** Secret rotation, backup/restore drill, migration rollback, privacy workflows, security review, staging parity, provider/queue/payment/AI incident runbooks, release gates, and clean-tenant activation rehearsal.

**Exit:** No unowned P0/P1 risks; support can diagnose top failures without engineering intervention.

## 6. Phase 0 deliverable definitions

### Launch segment

Initial segment: Kenyan service SMEs with inquiry, appointment, quote, or WhatsApp-led sales flows, beginning with salons, clinics, tutors, repair providers, and local service retailers.

### Activation event

`activated_tenant` occurs when a tenant has:

1. Published a site with a lead-capable page.
2. Captured at least one attributed lead.
3. Recorded a WhatsApp handoff or follow-up action.
4. Recorded a qualified/booked outcome, or a payment attempt where applicable.

A page visit, content generation, or signup alone is not activation.

### Initial outcome metric

Primary: percentage of new tenants reaching `activated_tenant` within 14 days.  
Secondary: time-to-publish, lead qualification rate, median response time, payment reconciliation success, and cost per activated tenant.

### Data classification baseline

| Record | Classification | Required controls |
|---|---|---|
| Tenant/business profile | Internal/business | Tenant scope, role access, audit mutations |
| User identity/session/MFA | Confidential | Strong hashing, durable sessions, secret protection, retention |
| Contact name/phone/email/consent | Personal data | Least privilege, export/delete, redacted logs, retention policy |
| Conversation/message/note | Personal/free text | Access control, redaction/anonymization, no unsafe AI context reuse |
| Payment/provider IDs | Financial/operational | Idempotency, state machine, audit, reconciliation |
| Generated content/prompt metadata | Business/AI governance | Versioning, safety result, review state, no secrets/PII in prompts |
| Audit/request/trace data | Operational | Integrity, safe metadata, retention, no raw personal content |

## 7. Current execution status

Build 0 is complete and pushed as `bca6683`. Build 1 is complete and pushed as `30c5b4f`: the generated-content vertical slice now depends on a tenant-scoped repository contract and adapter, with contract tests for isolation and review lifecycle. Build 2 identity increment is complete and pushed as `bf1b930`: password storage now uses versioned PBKDF2 hashes, verifies legacy hashes, and automatically rehashes on successful login. The remaining Build 2 work is durable sessions/MFA and a tested database migration boundary; it must begin with schema contracts, not a blind in-memory rewrite.

## 8. Required evidence per build

Each roadmap update must include:

- build number and user outcome;
- changed paths and contract summary;
- focused test command/result;
- full relevant suite/result;
- security/tenant/privacy review result;
- performance/cost impact or explicit not-applicable statement;
- commit hash and push verification;
- next build and rollback path.
