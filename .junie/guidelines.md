# KaziBoost Repository Constitution & Delivery Guidelines

## 1) Mission
Build an AI-powered local business growth platform for Kenyan SMEs with strict focus on:
- measurable business outcomes,
- local relevance (language, channels, payments),
- privacy/security by default,
- maintainable, test-first engineering.

## 2) Constitutional Principles (Non-Negotiable)
1. **User Value First:** Every change must tie to a customer outcome (lead growth, conversion, retention, ROI clarity).
2. **Kenya-First Localization:** English/Swahili support, mobile-first UX, KES currency, WhatsApp + M-Pesa centric journeys.
3. **Tests-First Delivery:** No production code without failing tests first.
4. **Security & Privacy by Design:** RBAC, MFA (admin), encryption, least privilege, compliance workflows.
5. **Explainability of AI:** AI-generated outputs must be reviewable/editable; confidence/sources where applicable.
6. **API & Adapter Discipline:** External providers are integrated through adapters; no provider lock-in in core domain.
7. **Observability Required:** Critical user flows must emit logs/metrics/traces with correlation IDs.
8. **Small, Reversible Changes:** Prefer incremental PRs with feature flags.
9. **Docs as Code:** PRD/requirements/ADR/tests/docs evolve with implementation.
10. **Approval Gate:** No scaffolding/implementation before explicit user approval of plan.

## 3) Working Agreement for Agents
- Always update `plan.md` before implementation.
- Request explicit approval after planning artifacts are ready.
- Use vertical slices (UI + API + data + tests) per feature.
- Never skip tests to meet speed.
- Include migration strategy for schema changes.

## 4) Branching, Commits, and PR Rules
- Branch naming: `feat/<area>-<summary>`, `fix/<area>-<summary>`, `chore/<area>-<summary>`
- Commit style: Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, etc.)
- Commit sequence rule:
  1. tests commit (failing or pending expected)
  2. implementation commit(s)
  3. docs/refactor commit(s)
- PR must include:
  - linked requirement IDs (FR/NFR)
  - test evidence
  - rollout/rollback notes
  - risk assessment

## 5) Engineering Standards
- Type-safe interfaces and schema validation at boundaries.
- Lint/format/test gates enforced in CI.
- Contract-first APIs (OpenAPI/GraphQL schema).
- Idempotency for webhooks and payment/message events.
- Background jobs for long-running tasks.

## 6) Domain Rules (KaziBoost)
- Any user-facing copy change must support localization readiness.
- SEO features must preserve valid metadata/schema output.
- Payments must never mark success before verified callback.
- WhatsApp automation must support human handoff path.
- CRM must maintain auditable lead source attribution.

## 7) Security & Compliance Rules
- Secrets must never be committed.
- PII access must be role-restricted and auditable.
- Data export/delete requests must be supportable.
- Retention policies must be configurable by tenant policy where possible.

## 8) Quality Gates (Must Pass)
- Unit + integration tests green
- Critical E2E paths green
- No high-severity security findings unresolved
- Performance budgets for affected flows respected

## 9) Documentation Rules
Required docs in repo root:
- `PRD.md`
- `requirements.md`
- `plan.md`

Required technical docs (as project evolves):
- `docs/adr/` architecture decisions
- `docs/runbooks/` operations incidents and recovery
- `docs/api/` contracts and examples

## 10) Subagents & Model Routing Policy
- Use specialized subagents (product, architecture, backend, frontend, QA, security, growth-SEO).
- Route complex reasoning/planning to higher-capability models.
- Route repetitive transforms/lint-like tasks to cost-efficient models.
- Human approval required before architecture-level pivots.

## 11) Definition of Ready (DoR)
A story is ready when:
- linked FR/NFR exists,
- acceptance criteria are testable,
- dependencies and data contracts are known,
- rollout plan exists.

## 12) Definition of Done (DoD)
A story is done when:
- all acceptance criteria pass,
- tests and CI gates pass,
- observability and docs updated,
- demoable value is visible to end user.
