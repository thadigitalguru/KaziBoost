# KaziBoost Senior Engineering Roadmap

Last updated: 2026-08-05
Branch: `sol/kaziboost-senior-upgrade-20260805`
Remote: `origin` -> `https://github.com/thadigitalguru/KaziBoost.git`
Default branch: `main`

## 1. Executive Summary

KaziBoost is a well-covered prototype for a Kenyan SME growth platform, but it is not yet production-ready. The strongest product wedge is the Kenyan SME lead-to-payment growth loop: publish a mobile-first site, capture first-party leads, follow up through WhatsApp, close or reconcile through M-Pesa, and prove ROI through analytics.

The current backend has broad FastAPI coverage and 104 passing API tests, but most state is held in a process-local `InMemoryStore`. The frontend is a coherent Next.js dashboard shell, but it mostly renders static arrays and inert controls. The AI-branded SEO and WhatsApp paths are deterministic templates and lexical matching, not a governed AI runtime. Security risks are concentrated in missing role authorization on sensitive operations, demo-grade MFA, default webhook secrets, and unescaped generated site HTML.

This roadmap selects exactly 10 incremental improvements that reduce the highest production risks without replacing the core framework, provisioning paid infrastructure, or force-pushing. Each item is designed to be implemented, reviewed, tested, committed, and pushed independently.

## 2. Current KaziBoost Product Proposition

Repository evidence:

- `README.md` describes KaziBoost as an AI-powered local business growth platform for Kenyan SMEs.
- `PRD.md` defines the product as an integrated stack for websites, localized SEO/content, CRM, WhatsApp commerce, M-Pesa payments, analytics, and training.
- `requirements.md` defines the desired production baseline: multi-tenant data isolation, OAuth/OIDC-style auth, PostgreSQL, Redis/job queues, observability, tests, and compliance readiness.
- `plan.md` shows many completed vertical slices and identifies operational settings, dashboard data fetching, and onboarding polish as next work.

Product inference:

- The most defensible wedge is not a generic AI website builder. It is a localized operating loop for Kenyan service and commerce SMEs where WhatsApp, M-Pesa, first-party CRM, and local SEO are naturally connected.
- The first beachhead should be service businesses with appointment, inquiry, or quote flows: salons, clinics, tutors, repair/service providers, and local retailers with WhatsApp-led sales.
- "Affordable AI growth platform" remains under-specified until pricing limits, usage caps, support model, and cost-to-serve are documented.

## 3. Current Architecture

Backend:

- FastAPI app entry point: `apps/api/kaziboost_api/main.py`.
- Routers: auth, sites, CRM, SEO, WhatsApp, payments, analytics, audit, onboarding, and training.
- Data model: dataclasses and mutable dictionaries in `apps/api/kaziboost_api/store.py`.
- Persistence: SEO keywords and generated content use SQLite through `apps/api/kaziboost_api/seo_persistence.py`; most other state is in memory.
- Tests: API coverage under `tests/api` spans auth, RBAC, CRM, WhatsApp, payments, SEO, analytics, observability, contracts, and hardening.

Frontend:

- Next.js App Router under `apps/web/app`.
- Static dashboard routes for sites, CRM, WhatsApp, payments, analytics, SEO, and training.
- No visible API client, route-level loading/error states, or auth/session wiring.

Delivery:

- GitHub Actions workflow runs Python 3.11 tests only.
- No frontend CI gate, no dependency/security gate, no coverage threshold, no deployment manifest, and no environment example.

## 4. Repository Health Assessment

Strengths:

- Clear product docs and incremental implementation history.
- Broad API regression test suite; read-only audit verified `104 passed`.
- Security headers, request IDs, health/readiness/metrics endpoints, auth flows, tenant scoping tests, and webhook signature tests already exist.
- Good vertical-slice coverage across the planned product modules.

Weaknesses:

- Monolithic `InMemoryStore` couples domains and blocks durability, multi-worker deployment, and database-level integrity.
- Many list/export endpoints are unbounded and scan in-memory collections.
- Sensitive mutations often require authentication but not role-specific authorization.
- Webhook helpers fall back to public development secrets.
- Site-rendered HTML interpolates tenant-controlled fields without escaping.
- Frontend displays static sample data and has a localhost API health link.
- CI does not enforce frontend build/typecheck, coverage, or dependency scanning.

## 5. AI Engineering Assessment

Implemented:

- SEO keyword suggestions, deterministic content generation, topic maps, content history, and calendar routes.
- WhatsApp FAQ bot based on lexical overlap.
- Pydantic response schemas for many AI-adjacent responses.
- Basic unsafe keyword blocking for a small hardcoded term set.

Missing:

- Model/provider abstraction.
- Prompt registry and prompt versioning.
- Structured AI output validation beyond API response schemas.
- AI evaluations for SEO quality, bilingual quality, FAQ grounding, refusals, prompt injection, and safety.
- Review/approval workflow for generated content.
- AI cost, latency, token, model, and safety telemetry.
- AI data retention/deletion/redaction controls.

Current recommendation: build governance scaffolding before adding live LLM calls. Do not introduce provider lock-in or paid inference until prompts, evals, quotas, privacy controls, and approval boundaries exist.

## 6. Product and Market Assessment

External evidence supports the product thesis:

- The Communications Authority of Kenya reported continued growth in mobile subscriptions, mobile money, and digital services in Q3 FY 2024/2025.
- Safaricom Daraja positions M-Pesa APIs as a bridge between payment integration and web/mobile apps.
- WhatsApp Business Platform materials position WhatsApp as a business messaging platform with webhooks, automation, and customer engagement.
- Wix and Zoho/Bigin show the comparable product categories: business website builders with CRM/payments/SEO, and small-business CRM with WhatsApp integration.

Strategic risks:

- The target segment is broad. A first launch segment should be explicit.
- Pricing is a set of labels, not a testable plan.
- The repo does not contain customer interview evidence, alpha cohort evidence, or acquisition/retention proof.
- The product spans many modules; shallow breadth could outrun one complete activation loop.

## 7. Security and Privacy Assessment

Highest-risk findings:

- Missing role authorization on sensitive endpoints: refunds, provider management, contact export/anonymization, campaign sending, site publishing/deletion/domain changes, and WhatsApp mutation.
- MFA is not enforced at login and challenge responses expose test codes.
- M-Pesa and WhatsApp webhook secrets fall back to deterministic development defaults.
- Rendered site HTML does not escape tenant-controlled fields.
- `npm audit` found high-severity frontend dependency advisories during the security subagent audit.
- Contact anonymization masks contact fields but may leave PII in timeline messages and notes.

External guidance alignment:

- OWASP Top 10 2025 lists broken access control, security misconfiguration, software supply chain failures, cryptographic failures, injection, authentication failures, and logging/alerting failures as major web risks.
- OWASP Authorization guidance emphasizes least privilege, deny-by-default, and validating permissions on every request.
- OWASP Password Storage guidance recommends slow, modern password hashing such as Argon2id/bcrypt/PBKDF2 instead of fast hashes such as SHA-256.
- ODPC Kenya guidance and FAQs make personal-data governance, registration, consent, and data-subject rights central to Kenya privacy readiness.

## 8. Scalability Assessment

Main blockers:

- Process-local dictionaries for most state.
- One global store instance at import time.
- Unbounded list/export endpoints.
- Analytics aggregates recompute by scanning hot stores.
- SEO SQLite schema lacks visible secondary indexes for generated-content history queries.
- Readiness always reports storage as OK.
- Metrics expose only three counters.

Near-term approach:

- Add limits, indexes, readiness checks, and observability while preserving current behavior.
- Introduce repository and migration planning before full PostgreSQL conversion.
- Avoid paid infrastructure or destructive migrations until explicitly approved.

## 9. Testing and Delivery Assessment

Current evidence:

- API suite: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -p no:cacheprovider -o addopts=` returned `104 passed`.
- Frontend typecheck was reported passing by the frontend subagent: `./apps/web/node_modules/.bin/tsc -p apps/web/tsconfig.json --noEmit --incremental false`.
- CI only runs `pytest`.

Gaps:

- No frontend CI build/typecheck.
- No coverage threshold.
- No dependency scan gate.
- No security scan gate.
- No deployment/runbook/rollback documentation.
- No E2E journey tests.

## 10. Key Risks and Constraints

- Do not push to `main`.
- Do not force-push or rewrite history.
- Do not commit secrets, `.env`, `.omx`, local caches, generated credentials, or machine-specific files.
- Do not provision paid infrastructure.
- Do not introduce new dependencies unless the improvement explicitly justifies the tradeoff.
- Do not perform destructive migrations or irreversible data transforms.
- Keep changes focused and independently reversible.
- GitHub CLI auth currently reports no logged-in hosts, but Git push to the dedicated branch succeeds.

## 11. Research Sources

Accessed on 2026-08-05.

- Office of the Data Protection Commissioner, Kenya, "Guidelines" - relevance: Kenya privacy/MSME/data protection guidance. https://www.odpc.go.ke/guidelines-2/
- Office of the Data Protection Commissioner, Kenya, "FAQs" - relevance: data controller/processor registration, personal data, data subject rights. https://www.odpc.go.ke/faqs/
- Communications Authority of Kenya, "Mobile, Data, and Digital Services on the Rise, CA Report Shows" - relevance: Kenya mobile, mobile money, and digital-services market context. https://www.ca.go.ke/index.php/mobile-data-and-digital-services-rise-ca-report-shows
- Safaricom Developers Portal, Daraja - relevance: M-Pesa API integration context. https://developer.safaricom.co.ke/
- WhatsApp Business Developer Hub - relevance: WhatsApp Business Platform capabilities and developer resources. https://whatsappbusiness.com/developers/developer-hub/
- WhatsApp Business Platform webhooks/Postman documentation - relevance: webhook setup and event delivery expectations. https://www.postman.com/meta/whatsapp-business-platform/folder/lboq68h/webhooks
- OWASP Top 10 2025 - relevance: current web application security risk taxonomy. https://owasp.org/Top10/
- OWASP Authorization Cheat Sheet - relevance: least privilege and per-request authorization. https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP Password Storage Cheat Sheet - relevance: password hash algorithm selection and legacy hash migration. https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- NIST SP 800-63B - relevance: authenticator and memorized-secret expectations. https://pages.nist.gov/800-63-3/sp800-63b.html
- FastAPI security documentation - relevance: OAuth2/Bearer dependency patterns. https://fastapi.tiangolo.com/tutorial/security/
- FastAPI SQL databases documentation - relevance: relational database patterns and production database direction. https://fastapi.tiangolo.com/tutorial/sql-databases/
- Alembic documentation - relevance: database migration planning. https://alembic.sqlalchemy.org/en/latest/index.html
- PostgreSQL row security documentation - relevance: tenant isolation options for future PostgreSQL migration. https://www.postgresql.org/docs/17/ddl-rowsecurity.html
- Next.js App Router documentation - relevance: current frontend framework conventions. https://nextjs.org/docs/app
- Next.js data fetching documentation - relevance: server/client data loading and loading states. https://nextjs.org/docs/app/getting-started/fetching-data
- Google Search Central SEO Starter Guide - relevance: SEO content quality and search fundamentals. https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Google Search Central LocalBusiness structured data - relevance: local SEO structured data for Kenyan SMEs. https://developers.google.com/search/docs/appearance/structured-data/local-business
- OpenAI structured outputs/function calling help - relevance: schema-bound AI generation patterns. https://help.openai.com/en/articles/8555517
- OpenAI data controls documentation - relevance: AI privacy and retention controls. https://platform.openai.com/docs/models/default-usage-policies-by-endpoint
- OpenAI prompt injection safety article - relevance: AI prompt-injection threat model. https://openai.com/safety/prompt-injections/
- GitHub dependency review documentation - relevance: dependency security gates. https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review
- Wix business website/business software pages - relevance: comparable website/CRM/payments/SEO product scope. https://www.wix.com/business/website and https://www.wix.com/business-software
- Bigin by Zoho CRM and WhatsApp integration docs - relevance: comparable SMB CRM and WhatsApp integration positioning. https://www.bigin.com/en-us/ and https://help.zoho.com/portal/en/kb/bigin/integration/articles/integrating-with-whatsapp

## 12. Exactly 10 Prioritized Improvements

Score legend: PI product impact, EI engineering impact, UI user impact, SI scalability impact, Sec security impact, Ur urgency, Eff implementation effort, Risk delivery risk, Conf confidence. Higher Eff/Risk means harder/riskier.

| # | Improvement | PI | EI | UI | SI | Sec | Ur | Eff | Risk | Conf |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Escape tenant-controlled site-rendered HTML | 7 | 8 | 8 | 3 | 10 | 10 | 2 | 2 | 10 |
| 2 | Add centralized role authorization for sensitive mutations | 8 | 9 | 8 | 4 | 10 | 10 | 4 | 4 | 9 |
| 3 | Fail closed on production webhook secrets with explicit dev/test mode | 7 | 8 | 7 | 4 | 10 | 9 | 3 | 3 | 9 |
| 4 | Redact contact-linked timeline and notes during anonymization | 8 | 7 | 8 | 3 | 9 | 9 | 3 | 3 | 9 |
| 5 | Add pagination/limits to high-volume list endpoints | 7 | 8 | 7 | 9 | 5 | 8 | 5 | 5 | 8 |
| 6 | Add SEO persistence indexes and real storage readiness checks | 6 | 8 | 6 | 8 | 5 | 8 | 4 | 4 | 8 |
| 7 | Add AI governance metadata, safety outcomes, and audit events | 8 | 9 | 8 | 5 | 8 | 8 | 5 | 5 | 8 |
| 8 | Add generated-content review workflow before publish/schedule | 8 | 8 | 8 | 5 | 8 | 7 | 5 | 5 | 8 |
| 9 | Replace local/static frontend assumptions with API-aware UX states | 9 | 8 | 9 | 5 | 5 | 8 | 6 | 6 | 8 |
| 10 | Expand CI quality gates and dependency security checks | 7 | 9 | 7 | 6 | 9 | 8 | 5 | 6 | 8 |

## 13. Execution Order and Dependencies

1. Site HTML escaping is first because it fixes a high-confidence injection risk with a narrow diff.
2. Role authorization comes next because it reduces broad access-control risk before deeper workflows.
3. Webhook secret fail-closed behavior hardens provider trust boundaries before webhook expansion.
4. Privacy redaction closes a compliance gap before broader data export/governance work.
5. Pagination/limits reduce scalability risk without changing persistence technology.
6. SEO indexes/readiness improves the only durable storage seam and deployment signal.
7. AI governance metadata creates the foundation for safe future LLM integration.
8. Generated-content review workflow builds on AI metadata and strengthens human approval boundaries.
9. Frontend API-aware UX can then surface the safer backend states and remove static/local assumptions.
10. CI gates are last because earlier changes define what must be tested and may require dependency updates. Until this lands, each improvement must still run its local quality gate before commit: focused regression tests, full API tests when backend code changes, frontend typecheck/build when web code changes, and dependency/security checks when manifests change.

## 14. Improvement Details

### 1. Escape tenant-controlled site-rendered HTML

Current problem: Rendered site HTML interpolates tenant-controlled values directly.
Evidence: security audit cited `apps/api/kaziboost_api/sites.py` render paths around generated HTML.
Proposed solution: Escape the tenant-controlled values currently emitted by the renderer: page title, page language, site name, site template key, hreflang href, hreflang slug, and hreflang language. Do not add body-block rendering in this improvement.
Better than alternatives: A small standard-library `html.escape` patch avoids a sanitizer dependency and preserves current output shape.
Scope: `apps/api/kaziboost_api/sites.py`, focused XSS regression tests.
Dependencies: none.
Risks: tests may need to assert encoded output rather than raw title strings.
Migration: none.
Acceptance criteria: script tags, angle brackets, quotes, and event-handler-like content are encoded in rendered title, metadata, language attributes, alternate links, language switcher links, heading text, and template text. Body blocks remain outside scope because the current renderer does not emit them.
Tests: add API test for malicious title, language, site name, template key, and hreflang-producing variants. Run `pytest tests/api/test_site_rendering_security.py` or the new focused file, then full `pytest`.
Observability: no new metrics needed.
Rollback: revert one commit; rendered HTML returns to previous behavior.
Estimated complexity: low.
Assigned builder agent: Backend and Data Agent.
Assigned reviewers: Security and Privacy Agent, Quality Engineering Agent, Independent Senior Reviewer.

### 2. Add centralized role authorization for sensitive mutations

Current problem: Most sensitive endpoints accept any authenticated tenant user.
Evidence: security audit cited payment providers/refunds, CRM campaign/export/anonymize, site publish/delete/domain, and WhatsApp mutation routes.
Proposed solution: Add a reusable role dependency and apply least-privilege role gates to sensitive mutating routes.
Better than alternatives: Central dependency keeps policy visible and testable without replacing auth.
Scope: `auth.py`, `payments.py`, `crm.py`, `sites.py`, `whatsapp.py`, tests.
Dependencies: item 1 can run independently; this item should precede frontend/admin controls.
Risks: existing tests may use owner tokens and keep passing; new tests must cover viewer/support denial.
Migration: none.
Acceptance criteria: viewer/support tokens cannot perform privileged sensitive mutations; owner/manager/appropriate roles can.
Role policy matrix:

| Surface | Actions/routes | Allowed roles |
|---|---|---|
| Sites content | create sites, add pages, publish, unpublish | owner, manager, marketer |
| Sites administration | attach custom domain, delete site | owner, manager |
| CRM forms and segmentation | create forms, create/update/delete segments, update tags | owner, manager, marketer |
| CRM support notes | create contact notes | owner, manager, marketer, support |
| CRM consent | update contact consent | owner, manager, support |
| CRM campaigns | send campaigns | owner, manager, marketer |
| CRM privacy/export | CSV export, single-contact export, contact anonymization/delete | owner, manager |
| Payments checkout | initiate M-Pesa payment | owner, manager, support |
| Payments provider setup | create/update/delete payment providers | owner |
| Payments refunds | create refunds | owner, manager |
| Payments reports/export | reconciliation, payment export, failure reports, refund reports | owner, manager |
| WhatsApp FAQ content | create/delete FAQs | owner, manager, marketer |
| WhatsApp service actions | human reply, handoff, assign, close, reopen, reminder scheduling, mark reminder sent, bot-reply trigger | owner, manager, support |
| Read-only dashboard/listing endpoints | non-sensitive GETs for tenant-scoped operational views | owner, manager, marketer, support, viewer |

Provider webhook callbacks are intentionally excluded from role authorization because improvement 3 will move them toward provider-secret trust boundaries rather than human bearer sessions.

Tests: add role-denial tests for representative routes in each matrix row and run the focused RBAC test file plus full `pytest`.
Observability: access-denied errors should use existing error response and request IDs.
Rollback: revert one commit; old broad authenticated access returns.
Estimated complexity: medium.
Assigned builder agent: Security and Privacy Agent.
Assigned reviewers: Backend and Data Agent, Quality Engineering Agent, Independent Senior Reviewer.

### 3. Fail closed on production webhook secrets with explicit dev/test mode

Current problem: M-Pesa and WhatsApp HMAC helpers use public dev defaults when env vars are missing.
Evidence: `payments_security.py` and `whatsapp_security.py` default to `dev-mpesa-secret` and `dev-whatsapp-secret`.
Proposed solution: Add environment-aware secret loading. Allow defaults only in explicit local/test mode; fail closed otherwise.
Better than alternatives: Preserves tests/dev ergonomics while preventing accidental production deployment with public secrets.
Scope: security helper modules, tests, `.env.example` if added.
Dependencies: none.
Risks: test environment must set or default to safe local mode.
Migration: production must set real webhook secrets.
Acceptance criteria: production-like environment without secrets raises a controlled configuration error; test/local mode remains deterministic.
Tests: valid configured secret, missing production secret failure, default local test signature behavior.
Observability: readiness should later expose missing-secret state without printing values.
Rollback: revert one commit; previous fallback returns.
Estimated complexity: low/medium.
Assigned builder agent: Security and Privacy Agent.
Assigned reviewers: Backend and Data Agent, Platform and DevOps Agent, Independent Senior Reviewer.

### 4. Redact contact-linked timeline and notes during anonymization

Current problem: Contact anonymization masks contact fields but may leave PII in free-text timeline messages and notes.
Evidence: security audit cited `store.py` anonymization and CRM export/timeline routes.
Proposed solution: During anonymization, replace linked interaction messages and notes with a fixed redaction marker and prevent future exports from leaking old PII.
Better than alternatives: Immediate privacy improvement without destructive deletion or schema changes.
Scope: `store.py`, CRM compliance tests.
Dependencies: role authorization should already protect anonymization access.
Risks: historical message content is intentionally lost for anonymized contacts. This is privacy-preserving and reversible only by commit revert, not data restore.
Migration: none for current in-memory data.
Acceptance criteria: after anonymization, contact export, timeline, and notes no longer include original names, phone numbers, emails, or message text.
Tests: add lead message/note PII regression test. Run full pytest.
Observability: optional audit event metadata should not include redacted PII.
Rollback: revert one commit; old behavior returns for new operations.
Estimated complexity: low/medium.
Assigned builder agent: Backend and Data Agent.
Assigned reviewers: Security and Privacy Agent, Quality Engineering Agent, Independent Senior Reviewer.

### 5. Add pagination/limits to high-volume list endpoints

Current problem: Many list/export paths return all tenant records or scan unbounded collections.
Evidence: performance audit cited contacts, WhatsApp conversations/reminders, payments, training, and analytics scans.
Proposed solution: Add consistent `limit`/`offset` or capped `limit` query parameters to high-volume list routes while preserving defaults.
Better than alternatives: Reduces immediate performance risk without a database migration.
Scope: CRM, WhatsApp, payments, training, SEO calendar, and related tests.
Dependencies: role/privacy work should precede broad list changes.
Risks: API response totals and ordering must remain stable; clients may rely on all records by default.
Migration: document default/max limits.
Acceptance criteria: affected routes enforce a documented default and maximum limit; existing small-data tests pass.
Tests: pagination contract tests for each touched route, full pytest.
Observability: later metrics can track capped responses.
Rollback: revert one commit; unbounded responses return.
Estimated complexity: medium.
Assigned builder agent: Performance and Cost Agent.
Assigned reviewers: Backend and Data Agent, Quality Engineering Agent, Independent Senior Reviewer.

### 6. Add SEO persistence indexes and real storage readiness checks

Current problem: SEO generated-content history queries lack secondary indexes, and `/ready` always reports storage OK.
Evidence: `seo_persistence.py` creates tables but no indexes; `main.py` readiness is static.
Proposed solution: Add SQLite indexes for tenant/history query shapes and a store readiness method that probes SEO persistence.
Better than alternatives: Improves the only durable persistence seam without adding PostgreSQL yet.
Scope: `seo_persistence.py`, `store.py`, `main.py`, readiness tests.
Dependencies: none, but best after pagination.
Risks: index creation runs on startup; must be idempotent.
Migration: SQLite `CREATE INDEX IF NOT EXISTS`.
Acceptance criteria: readiness reflects storage probe results; indexes exist for generated-content history.
Tests: readiness success/failure tests and SEO persistence tests.
Observability: `/ready` reports storage check result without secrets.
Rollback: revert one commit; indexes remain harmless in local DB unless manually removed.
Estimated complexity: medium.
Assigned builder agent: Platform and DevOps Agent.
Assigned reviewers: Backend and Data Agent, Quality Engineering Agent, Independent Senior Reviewer.

### 7. Add AI governance metadata, safety outcomes, and audit events

Current problem: Generated content lacks prompt/version/safety metadata and AI operations are not audited.
Evidence: AI audit cited deterministic generation, weak safety list, and no audit events for AI generation/bot replies.
Proposed solution: Add metadata fields for prompt version, generation mode, safety outcome, and policy violations. Record audit events for SEO generation and WhatsApp bot replies.
Better than alternatives: Builds governance without adding a live model provider or dependency.
Scope: `models.py`, `ai_seo.py`, `store.py`, `whatsapp.py`, tests.
Dependencies: privacy and readiness work should precede broader AI tracking.
Risks: content history schema needs additive fields or default metadata.
Migration: SQLite additive migration or compatibility defaults.
Acceptance criteria: content history includes governance metadata; unsafe requests record safe audit outcomes without storing unsafe content.
Tests: AI metadata and audit-event tests, existing safety tests, full pytest.
Observability: extend metrics with AI generation/safety counters if feasible.
Rollback: revert one commit; metadata no longer emitted.
Estimated complexity: medium.
Assigned builder agent: Principal AI Engineering Agent.
Assigned reviewers: Security and Privacy Agent, Backend and Data Agent, Independent Senior Reviewer.

### 8. Add generated-content review workflow before publish/schedule

Current problem: UI mentions review/approval, but backend generated content has no review state.
Evidence: SEO UI copy describes review, while backend calendar states are only scheduled/published/cancelled and generated content is saved immediately.
Proposed solution: Add generated content statuses such as `needs_review`, `approved`, and `rejected`, plus endpoints to update generated-content status. Add an optional `generated_content_id` relationship on calendar items so AI-generated drafts can be scheduled only after approval. Manual calendar items without a generated-content reference keep the existing schedule behavior.
Better than alternatives: Human approval boundary is explicit before live AI integration.
Scope: SEO persistence/store/models/routes/tests.
Dependencies: item 7 metadata should land first.
Risks: schema compatibility for existing generated rows.
Migration: default existing rows to `needs_review` or compatible status.
Review data and transition model:

- Generated content records get `status`, `reviewed_by`, `reviewed_at`, and optional `review_note`.
- New generated content starts as `needs_review`.
- Allowed generated-content transitions: `needs_review -> approved`, `needs_review -> rejected`, `rejected -> needs_review` only through regeneration or explicit reopen.
- Calendar items may include `generated_content_id`.
- Manual calendar items with no `generated_content_id` may still be created as `scheduled`.
- Calendar items linked to generated content may be created as `draft` or `needs_review`, but cannot become `scheduled` or `published` until the generated content is `approved`.
- `published` remains terminal except for existing `cancelled` behavior if already supported by the current route.

Acceptance criteria: new generated content starts as `needs_review`; approve/reject endpoint works; calendar items linked to unapproved generated content cannot be scheduled or published; manual calendar items preserve existing behavior.
Tests: generation status tests, approval transition tests, linked-calendar gating tests, manual-calendar backward-compatibility tests, full `pytest`.
Observability: audit approval/rejection events.
Rollback: revert one commit; old content history behavior returns.
Estimated complexity: medium.
Assigned builder agent: Principal AI Engineering Agent.
Assigned reviewers: Product Strategy Agent, Security and Privacy Agent, Independent Senior Reviewer.

### 9. Replace local/static frontend assumptions with API-aware UX states

Current problem: Dashboard pages use static arrays and a public localhost health link.
Evidence: frontend audit cited no `fetch`, no `loading.tsx`, no `error.tsx`, no empty states, and `http://localhost:8000/health` on homepage.
Proposed solution: Remove the localhost CTA, add environment-aware API base configuration, add route loading/error/empty states, and connect at least the dashboard overview or analytics summary to a typed API client where auth constraints allow.
Better than alternatives: Gives users truthful state before building a full auth frontend.
Scope: `apps/web/app`, `apps/web/package.json` scripts if needed, tests/build.
Dependencies: backend readiness and safer API contracts should precede this.
Risks: no browser-auth flow yet; API-backed pages must handle unauthenticated state honestly.
Migration: environment variable documentation for API base.
Acceptance criteria: no localhost public link; dashboard has loading/error/empty states; API fetch failures render safe fallback; build passes.
Tests: TypeScript no-emit, Next build, optional smoke tests.
Observability: none beyond user-visible error state.
Rollback: revert one commit; static shell returns.
Estimated complexity: medium/high.
Assigned builder agent: Frontend and UX Agent.
Assigned reviewers: Product Strategy Agent, Quality Engineering Agent, Independent Senior Reviewer.

### 10. Expand CI quality gates and dependency security checks

Current problem: CI only runs Python tests; frontend and dependency/security checks are not enforced.
Evidence: `.github/workflows/ci.yml` runs only install and pytest. Security audit ran `npm audit --audit-level=moderate` in `apps/web` and found two high-severity vulnerable dependency paths involving `next` and bundled `postcss`; `pip-audit` was not installed.
Proposed solution: Add Python coverage gate, frontend install/typecheck/build gate, npm audit high gate, and documented Python dependency audit path where tooling is available. Upgrade vulnerable frontend dependencies if required.
Better than alternatives: Prevents regressions from entering the branch after the first nine improvements.
Scope: CI workflow, package manifests/lockfile as needed, docs.
Dependencies: item 9 should define frontend scripts.
Risks: dependency upgrades can affect Next build; network/install requirements may be slower.
Migration: none.
Acceptance criteria: CI workflow includes API tests with coverage, web typecheck/build, npm audit high, and dependency review guidance. Local checks pass before commit.
Tests: run `pytest`, frontend typecheck/build, and audit commands locally where network permits.
Observability: CI status is the gate.
Rollback: revert one commit; old CI returns.
Estimated complexity: medium/high.
Assigned builder agent: Platform and DevOps Agent.
Assigned reviewers: Security and Privacy Agent, Quality Engineering Agent, Independent Senior Reviewer.

## 15. Expected Product and Engineering Outcome

After these 10 improvements:

- The customer-facing site renderer is safer.
- Sensitive operations have explicit role boundaries.
- Provider webhooks cannot silently run with public default secrets in production.
- Contact anonymization is more privacy-aligned.
- High-volume endpoints have initial scalability controls.
- Storage readiness reflects actual persistence health.
- AI work has governance metadata before live provider integration.
- Generated content has an explicit review boundary.
- Frontend UX stops presenting local/static assumptions as product truth.
- CI catches more regressions and supply-chain risk before merge.

Deferred larger efforts:

- Full PostgreSQL/Alembic migration.
- Redis/job queue integration.
- Real WhatsApp/Daraja provider adapters.
- Live LLM provider integration.
- End-to-end browser tests for authenticated customer journeys.
- Formal pricing and billing behavior.

## 16. Progress Log

| Time | Event | Commit | Push status |
|---|---|---|---|
| 2026-08-05 | Loaded workspace/OMX instructions and project docs. | n/a | n/a |
| 2026-08-05 | Backed up pre-existing `.gitignore` change to `/private/tmp/KaziBoost-uncommitted-20260805-232052.patch`. | n/a | n/a |
| 2026-08-05 | Fetched remote state and verified `origin/main` at `614ad6b90db49c0aa19ca7db569a7699dba76ee9`. | n/a | n/a |
| 2026-08-05 | Created branch `sol/kaziboost-senior-upgrade-20260805`. | `614ad6b90db49c0aa19ca7db569a7699dba76ee9` | Pushed and upstream set |
| 2026-08-05 | Read-only audits completed by Repository Intelligence, Product Strategy, Principal AI Engineering, Backend/Data, Frontend/UX, Security/Privacy, Platform/Quality, and Performance/Cost agents. | n/a | n/a |
| 2026-08-05 | External research completed from sources listed above. | n/a | n/a |
| 2026-08-05 | Committed Phase 3 roadmap artifact and `.omx/` ignore safety rule. | `72d754a73ce963693eaa15b6067dd59b35d9b7ca` | Pushed to `origin/sol/kaziboost-senior-upgrade-20260805`; local, upstream, and `ls-remote` hashes match |
| 2026-08-05 | Improvement 1: Escape tenant-controlled site-rendered HTML; implementation, tests, and reviews passed. | `06c4041e466debfcf42dafa9a46d1ee2b6011961` | Pushed to `origin/sol/kaziboost-senior-upgrade-20260805`; local, upstream, and `ls-remote` hashes match |
| 2026-08-05 | Improvement 2: Centralized role authorization; implementation, tests, and reviews passed. | `2d39d141addea3963914b380802a69044951d84f` | Pushed to `origin/sol/kaziboost-senior-upgrade-20260805`; local, upstream, and `ls-remote` hashes match |
| 2026-08-06 | Improvement 3: Production webhook secret fail-closed behavior; implementation, tests, and reviews passed. | `5cb3c3fbff22668e4cea2045885f7eef236f6e6d` | Pushed to `origin/sol/kaziboost-senior-upgrade-20260805`; local, upstream, and `ls-remote` hashes match |
| pending | Improvement 4: Privacy redaction during anonymization. | pending | pending |
| pending | Improvement 5: Pagination and list limits. | pending | pending |
| pending | Improvement 6: SEO indexes and readiness checks. | pending | pending |
| pending | Improvement 7: AI governance metadata and audit events. | pending | pending |
| pending | Improvement 8: Generated-content review workflow. | pending | pending |
| pending | Improvement 9: API-aware frontend UX states. | pending | pending |
| pending | Improvement 10: CI quality/security gates. | pending | pending |

## 17. Remote Repository Notes

- `git remote -v` resolves `origin` to `https://github.com/thadigitalguru/KaziBoost.git`.
- `origin/HEAD` points to `origin/main`.
- Local `main` and `origin/main` were aligned at `614ad6b90db49c0aa19ca7db569a7699dba76ee9` before branch creation.
- Dedicated branch `sol/kaziboost-senior-upgrade-20260805` was pushed and tracks `origin/sol/kaziboost-senior-upgrade-20260805`.
- `gh auth status` currently reports no logged-in GitHub hosts, but Git push succeeded through Git's credential path.
- GitHub public API read attempts were rate-limited without a healthy authenticated `gh` token; repository metadata available from prior `gh repo view` showed public repo `thadigitalguru/KaziBoost`, default branch `main`, no description, and last pushed at 2026-06-02T18:40:57Z.

## 18. Agent Allocation Plan

- Sol: final integrator, sequencing owner, Git safety, quality gates, push verification.
- Repository Intelligence Agent: codebase and git evidence mapping.
- Product Strategy Agent: market/product wedge, packaging, adoption, retention.
- Principal AI Engineering Agent: AI runtime, safety, evals, prompt contracts, governance.
- Backend and Data Agent: API, data integrity, persistence, multi-tenancy.
- Frontend and UX Agent: Next.js UX, accessibility, state, mobile behavior.
- Security and Privacy Agent: auth, authorization, secrets, XSS, privacy.
- Platform and DevOps Agent: CI, readiness, deployment, observability.
- Quality Engineering Agent: tests, coverage, regression strategy.
- Performance and Cost Agent: pagination, indexes, latency, AI cost controls.
- Independent Senior Reviewer: challenges each design and reviews implementation before commit.
