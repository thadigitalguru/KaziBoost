# KaziBoost Baseline Report

Date: 2026-08-16  
Branch: `sol/kaziboost-20260805`  
HEAD at capture: `2c1cf15` before Build 0 documentation commit

## Reproduction commands

Run from repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest --cov=kaziboost_api --cov-report=term --cov-fail-under=80 -q
cd apps/web && ./node_modules/.bin/tsc -p tsconfig.json --noEmit --incremental false
cd apps/web && npm run build
cd apps/web && npm audit --audit-level=high
```

## Results

| Gate | Result | Evidence |
|---|---|---|
| API regression suite | PASS | 128 tests passed |
| API coverage | PASS | 84.06%, required 80% |
| Frontend TypeScript | PASS | no output/errors |
| Frontend production build | PASS | Next.js 16.3.1; all 12 routes generated/served |
| npm dependency audit | PASS | 0 vulnerabilities |
| Python dependency audit | PASS after upgrading local audit tool environment | `pip-audit` reported no known vulnerabilities; local project is not published to PyPI and was skipped |
| Git working tree | PASS | clean before Build 0 docs |

The API suite emits existing deprecation/resource warnings. They are non-blocking for this baseline but are tracked as follow-up work: Starlette/httpx compatibility and SQLite connection lifecycle cleanup.

## Preview route verification

The local production preview was verified at `http://127.0.0.1:3000` with the API at `http://127.0.0.1:8000`.

| Route | Status |
|---|---:|
| `/` | 200 |
| `/dashboard` | 200 |
| `/dashboard/sites` | 200 |
| `/dashboard/crm` | 200 |
| `/dashboard/whatsapp` | 200 |
| `/dashboard/payments` | 200 |
| `/dashboard/analytics` | 200 |
| `/dashboard/seo` | 200 |
| `/dashboard/training` | 200 |

The dashboard's public readiness panel is API-aware. In local preview, `/ready` returns `not_ready` when protected webhook secrets are absent; this is intentional fail-closed behavior, not a hidden healthy state.

## Repository baseline observations

- FastAPI composition is in `apps/api/kaziboost_api/main.py`.
- Most domain state remains in mutable dictionaries in `store.py`.
- SEO keywords and generated content are the only durable domain seam, using SQLite.
- Auth tokens, MFA state, contacts, conversations, payments, sites, and audit events remain process-local.
- AI-adjacent features are deterministic templates and lexical FAQ matching.
- Content governance metadata and review gating now exist for SEO generated content.
- Frontend routes are mostly shell/static UI; the dashboard readiness panel is the first API-aware overview.
- CI now gates API coverage/audit and frontend typecheck/build/audit.

## Scope lock

Initial launch segment: Kenyan service SMEs with inquiry, appointment, quote, or WhatsApp-led sales flows.

Primary activation event: a tenant publishes a lead-capable site, captures an attributed lead, records a WhatsApp handoff/follow-up action, and records a qualified/booked outcome or payment attempt within 14 days of signup.

Primary outcome metric: percentage of new tenants reaching activation within 14 days.

## Data inventory

| Aggregate | Current storage | Target control |
|---|---|---|
| Tenant/user/session/MFA | In-memory | PostgreSQL, durable session policy, strong password hashing |
| Site/page/SEO assets | In-memory | Tenant FK, lifecycle constraints, transactionally published |
| Contact/consent/timeline/notes | In-memory | Personal-data classification, retention/export/delete |
| WhatsApp/conversation/reminders | In-memory | Provider event IDs, idempotency, handoff lifecycle |
| Payment/refund/provider state | In-memory | State machine, transaction, reconciliation, idempotency |
| Generated SEO content | SQLite | Migration path, version/review state, repository boundary |
| Audit/request events | In-memory | Durable append-only operational record with safe metadata |

## Baseline decision

Proceed to Build 1: define repository/domain contracts and contract tests before selecting or copying a PostgreSQL schema. Do not add live LLM provider calls or broaden frontend scope before this boundary is explicit.
