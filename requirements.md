# KaziBoost — Product & Engineering Requirements

## 1. Document Purpose
This document translates the PRD into implementable requirements, acceptance criteria, and delivery constraints for engineering teams.

## 2. System Context
KaziBoost is a multi-tenant SaaS platform for Kenyan SMEs, combining:
- Website/landing management
- SEO/content AI
- CRM
- WhatsApp chatbot and workflow automation
- M-Pesa payments
- Analytics/reporting

## 3. Recommended Technical Baseline
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind + component library
- **Backend/API:** FastAPI (Python) or Node.js (NestJS/Express); REST + GraphQL gateway
- **DB:** PostgreSQL
- **Search/Indexing:** Elasticsearch/OpenSearch
- **Cache/Queue:** Redis + job queue (BullMQ/Celery/RQ)
- **Auth:** OAuth2/OIDC (JWT + refresh) + MFA for admin
- **Infra:** Docker + IaC + CI/CD + CDN
- **Observability:** OpenTelemetry + centralized logs + alerts

## 4. Architecture Requirements
1. Multi-tenant data isolation with tenant_id across bounded contexts.
2. Service boundaries:
   - Identity & Access
   - Site Builder
   - SEO/Content AI
   - CRM
   - Messaging (WhatsApp/SMS/Email)
   - Payments
   - Analytics
3. API-first design with versioning and idempotent write endpoints.
4. Event-driven integration (domain events for lead captured, payment succeeded, etc.).

## 5. Functional Requirements and Acceptance Criteria

## FR-1: Authentication & Authorization
- OAuth2/OIDC login with email/password + social options (phase 2 acceptable)
- RBAC roles: owner, manager, marketer, support, viewer
- Admin MFA required

**Acceptance Criteria**
- Users can sign up, verify email, and sign in.
- Role changes apply within one request cycle.
- Admin login requires second factor.

## FR-2: Website & Landing Builder
- Template library for Kenyan industries
- Drag-drop blocks (hero, services, testimonials, form, FAQ, contact map)
- Mobile-first and responsive behavior
- Auto SEO artifacts (meta, schema, sitemap, robots)

**Acceptance Criteria**
- User can publish a website in < 10 guided steps.
- Published pages pass mobile viewport and accessibility baseline checks.
- sitemap.xml and robots.txt auto-generated per site.

## FR-3: Multilingual Content
- English + Swahili + optional Sheng content entries
- Page-level language variants with hreflang support

**Acceptance Criteria**
- User can create at least two language versions of same page.
- Language switcher appears on published site if >1 variant exists.

## FR-4: Local Keyword Research
- Query and suggestion engine for local keywords and neighborhoods
- Keyword intent labels + estimated volume bands

**Acceptance Criteria**
- For a seed query, user receives >=20 keyword suggestions with intent.
- User can save selected keywords into a campaign/workspace.

## FR-5: AI Content Generation
- Generate SEO blog/article/product/FAQ content from selected keywords
- Tone/length/language controls
- Internal-link suggestions for pillar-cluster strategy

**Acceptance Criteria**
- Generated content contains target keyword and related terms.
- User can regenerate section-level output.
- Output includes meta title + description recommendations.

## FR-6: CRM Lead Management
- Form submissions create contacts and interactions
- Source attribution (web form, WhatsApp, import, manual)
- Tags/segments/notes and activity timeline

**Acceptance Criteria**
- New lead appears in CRM within 3 seconds after form submit.
- Contacts can be filtered by source/tag/date.
- Export to CSV includes selected filters.

## FR-7: WhatsApp Integration & Chatbot
- WhatsApp Business API integration
- FAQ chatbot with fallback to human handoff
- Appointment/order confirmation templates

**Acceptance Criteria**
- Incoming WhatsApp messages create/append conversation threads.
- Bot can answer from approved FAQ source.
- User can assign thread to human agent.

## FR-8: Payments (M-Pesa + Optional Adapters)
- Daraja STK push payment request
- Webhook verification and reconciliation
- Optional adapter interface for Airtel/card providers

**Acceptance Criteria**
- Payment request status transitions: initiated -> pending -> success/fail.
- Successful payment linked to contact/order record.
- Duplicate webhook delivery handled idempotently.

## FR-9: Analytics & Reporting
- Dashboard with acquisition, behavior, conversion metrics
- GA4 and Search Console connectors
- Scheduled reports and exports (CSV/PDF)

**Acceptance Criteria**
- Dashboard renders tenant KPI overview in <2s p95.
- User can schedule weekly report emails.

## FR-10: Training & Knowledge Base
- In-app learning center + searchable articles/videos

**Acceptance Criteria**
- Help center searchable by keyword.
- Articles can be categorized by feature.

## 6. Non-Functional Requirements

## NFR-1 Performance
- p95 API latency < 400ms for non-AI endpoints
- p95 page load under agreed performance budget

## NFR-2 Reliability
- 99.9% uptime target for paid tiers
- Retry + DLQ for async jobs

## NFR-3 Security
- OWASP ASVS-aligned controls
- Encryption at rest (DB, backups) and in transit (TLS1.2+)
- Secrets manager required

## NFR-4 Privacy & Compliance
- Kenya Data Protection Act alignment
- Consent capture and retention controls
- Data export, deletion, and access request workflows

## NFR-5 Scalability
- Horizontal scalability for API and worker nodes
- Queue-backed workloads for AI generation and webhook processing

## NFR-6 Observability
- Structured logging with correlation IDs
- Metrics and traces for all critical flows
- Alerting on error budgets and payment/message failures

## 7. Data Model (High-Level)
Core entities:
- Tenant
- User
- RoleMembership
- Website
- Page
- PageVariant(language)
- SEOAsset(meta/schema/sitemap)
- Keyword
- ContentPiece
- Contact
- Lead
- Interaction
- Conversation
- Message
- Order
- Payment
- Report
- AuditEvent

## 8. API Requirements
- REST endpoints for CRUD and transactional flows
- GraphQL aggregation for dashboard composition
- Webhook endpoints for Daraja/WhatsApp providers
- OpenAPI spec and contract tests required

## 9. Testing Requirements (Tests-First Policy)
1. Unit tests for domain services and utility layers
2. Integration tests for DB/repository and external adapters (mocked sandbox)
3. Contract tests for APIs and webhooks
4. E2E tests for:
   - signup -> publish site
   - lead capture -> CRM
   - WhatsApp chat -> handoff
   - STK push -> reconciliation
5. Performance smoke tests for critical APIs
6. Security checks (SAST/dep scan/basic DAST where possible)

Minimum CI thresholds:
- 80% statement coverage on core services
- 100% passing required test suites before merge

## 10. Delivery Constraints
- Build in incremental vertical slices.
- Feature flags for unfinished modules.
- No direct provider coupling in core domain (use adapters/interfaces).

## 11. Environments
- local
- test/ci
- staging
- production

Each env must include seeded test data and deterministic test scripts.

## 12. Definition of Done
A feature is complete when:
1. Acceptance criteria pass.
2. Unit + integration tests pass in CI.
3. API contracts documented and versioned.
4. Security and privacy checks complete.
5. Observability hooks are in place.
6. Documentation and runbooks updated.
