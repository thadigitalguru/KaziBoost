# KaziBoost Implementation Plan (Approval Required Before Code)

## Status
- [x] PRD drafted
- [x] Requirements drafted
- [x] Repository constitution/guidelines drafted
- [x] Agent skills + subagent/model routing drafted
- [x] **User approval received**
- [x] Project scaffolding (tests first)
- [x] Initial implementation (Auth + Tenant bootstrap slice)
- [x] Initial implementation (Slice B baseline: site create, page add, publish, SEO artifacts)
- [x] Initial implementation (Slice C baseline: CRM forms, lead capture, filtering, timeline, CSV export)
- [x] Initial implementation (Slice D baseline: keyword suggestions, keyword workspace save, AI content generation)
- [x] Initial implementation (Slice E baseline: WhatsApp inbound threads, FAQ bot replies, human handoff)
- [x] Initial implementation (Slice F baseline: M-Pesa initiation, callbacks, idempotency, reconciliation)
- [x] Initial implementation (Slice 8 baseline: analytics dashboard, CSV export, report scheduling)
- [x] Hardening pass (auth security controls, M-Pesa input validation, request-id trace header middleware)
- [x] Hardening build extension (OpenAPI error contracts, response schemas, security headers)
- [x] Hardening build extension (auth no-store headers, RBAC teammate/role management, logout revocation, readiness endpoint)
- [x] Post-hardening build set (audit events feed, report schedule lifecycle, SEO safety guardrails, hreflang map, onboarding checklist)
- [x] Expansion build set (CRM segments, WhatsApp status transitions, refunds, analytics funnel, training knowledge base)
- [x] Growth ops build set (CRM campaigns, WhatsApp reminders, payments summary, SEO calendar, training management)
- [x] Scale-up build set (CRM campaigns engine, WhatsApp reminders lifecycle, payments intelligence summary, SEO calendar workflows, training lifecycle management)
- [x] Optimization build set (campaign analytics, WhatsApp overdue queue, monthly payments reporting, SEO calendar status lifecycle, training list/delete lifecycle)
- [x] Execution build set (segment lifecycle mgmt, WhatsApp SLA visibility, refund reason reporting, SEO calendar filtering, featured training content)
- [x] Next execution build set (CRM notes, WhatsApp assignment mgmt, failed-payment reason logs, SEO workspace deletion, training views/top content)
- [x] Latest execution set (lead source analytics, reminder sent lifecycle, payments CSV export, due-content calendar view, dashboard trend snapshot)
- [x] Current execution set (CRM tag analytics, WhatsApp FAQ listing, reconciliation status filters, SEO calendar deletion, training category filters)

---

## Phase 0 — Alignment & Foundations
**Goal:** Lock requirements, architecture direction, and quality gates.

Tasks:
1. Review PRD and requirements with stakeholder.
2. Confirm tech stack selection (Next.js + backend framework choice).
3. Finalize MVP scope (vertical slice order).
4. Confirm compliance baseline (Kenya DPA + GDPR readiness).

Deliverables:
- Approved `PRD.md`
- Approved `requirements.md`
- Approved `plan.md`

Exit Criteria:
- Explicit user sign-off.

---

## Phase 1 — Repo Bootstrap (Tests First)
**Goal:** Scaffold monorepo/services, CI, and testing harness before feature code.

Tasks:
1. Initialize repository structure:
   - `apps/web`
   - `apps/api`
   - `packages/shared`
   - `packages/contracts`
2. Set up test tooling:
   - unit (Vitest/Pytest/Jest)
   - integration tests
   - contract tests
   - E2E skeleton (Playwright/Cypress)
3. Add first failing tests for auth + tenant bootstrap contracts.
4. Set up lint/format/typecheck/CI pipelines.

Deliverables:
- Scaffolding + failing tests committed first.

Exit Criteria:
- CI runs and reports failing tests as expected.

---

## Phase 2 — Vertical Slice A: Auth + Tenant + Basic Dashboard
**Goal:** First deployable core app shell.

Scope:
- Signup/login/logout
- RBAC skeleton
- Tenant creation
- Basic dashboard shell

Tests first:
- auth flows
- role checks
- tenant isolation checks

---

## Phase 3 — Vertical Slice B: Website Builder + Publish + SEO Artifacts
**Goal:** Enable first website publishing outcome.

Scope:
- template selection
- page editor blocks
- publish flow
- sitemap/robots/schema generation

Tests first:
- publish endpoint contracts
- SEO artifact generation tests
- mobile rendering smoke checks

---

## Phase 4 — Vertical Slice C: CRM Lead Capture
**Goal:** Convert traffic into first-party lead records.

Scope:
- forms
- lead capture pipeline
- contact timeline
- filtering + export

Tests first:
- form submit -> contact created
- attribution integrity tests

---

## Phase 5 — Vertical Slice D: AI SEO + Content Assistant
**Goal:** Drive discoverability with localized content.

Scope:
- keyword suggestions
- content generation
- bilingual outputs
- editorial workflow

Tests first:
- prompt contract tests
- generation response schema tests
- unsafe output guard tests

---

## Phase 6 — Vertical Slice E: WhatsApp + Chatbot + Handoff
**Goal:** Conversational commerce flow.

Scope:
- WhatsApp webhook adapter
- FAQ bot
- handoff path

Tests first:
- webhook signature + idempotency
- bot fallback/handoff behavior tests

---

## Phase 7 — Vertical Slice F: M-Pesa Payments + Reconciliation
**Goal:** Local checkout and payment-state reliability.

Scope:
- STK push initiation
- callback processing
- CRM/order reconciliation

Tests first:
- payment state machine
- duplicate callback idempotency

---

## Phase 8 — Analytics + Reporting + Knowledge Base
**Goal:** ROI visibility and onboarding enablement.

Scope:
- KPI dashboard
- report export/scheduling
- help center module

Tests first:
- dashboard query contracts
- report generation tests

---

## Commit Strategy
For each phase/slice:
1. `test:` commit with failing tests
2. `feat:` commit(s) for implementation
3. `docs/chore/refactor:` follow-ups

---

## Risks & Countermeasures
- API integration instability -> adapter interfaces, retries, DLQ
- Scope creep -> strict slice acceptance criteria
- AI cost growth -> quotas, caching, model routing controls

---

## Approval Request
Please approve these planning artifacts so I can proceed to:
1. scaffold the repo,
2. add tests first,
3. then implement features incrementally,
4. and commit per the policy above.
