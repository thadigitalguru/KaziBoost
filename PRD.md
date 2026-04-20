# PRD — KaziBoost (AI‑Powered Local Business Growth Engine)

## 1) Product Summary
KaziBoost is a SaaS platform that helps Kenyan SMEs build and grow a strong digital presence through an integrated stack of:
- Mobile-first website and landing-page creation
- Localized SEO and AI-assisted content marketing
- CRM and first-party customer data capture
- WhatsApp commerce automation
- M-Pesa (and optional Airtel/card) payments
- Actionable analytics and reporting

KaziBoost is designed for non-technical business owners and teams with limited time, budget, and in-house marketing capacity.

---

## 2) Problem Statement
Kenyan SMEs face a structural growth gap online:
1. Low SEO adoption and weak web presence despite high search-led discovery.
2. Limited staffing and marketing budgets reduce execution consistency.
3. Over-reliance on social media platforms with weak first-party data ownership.
4. Mobile-first customer behavior requires WhatsApp + mobile payment-led journeys.
5. Existing tools are expensive, generic, and poorly localized for Kenyan market realities (language, channels, payment rails).

---

## 3) Vision
To become the default growth operating system for Kenyan SMEs by combining local web presence, AI marketing automation, CRM, conversational commerce, and local payment infrastructure in one affordable platform.

---

## 4) Product Goals (12–18 months)
1. Help SMEs launch production-ready, SEO-optimized websites in <2 hours.
2. Increase qualified inbound leads by 30%+ for active customers.
3. Improve lead-to-sale conversion through CRM + WhatsApp flows + payment integrations.
4. Provide clear ROI visibility via integrated analytics dashboards.
5. Keep entry barrier low through free tier + incremental upgrades.

---

## 5) Target Users
### Primary
- Micro, small, and medium-sized businesses in Kenya (Nairobi and major towns):
  - Restaurants, salons, clinics, hardware stores, logistics, local services
- Freelancers/professionals: tutors, consultants, lawyers, coaches

### Secondary
- Agencies/freelance marketers serving SMEs
- Multi-branch SMEs needing centralized lead and campaign management

### User Traits
- Mobile-first workflows
- Non-technical
- Outcome-oriented (leads, bookings, orders, repeat sales)
- Need bilingual or multilingual communication (English, Swahili, Sheng)

---

## 6) Value Proposition
KaziBoost uniquely combines:
- Localized web + SEO tooling
- AI bilingual content and campaign automation
- First-party CRM ownership
- WhatsApp commerce workflows
- M-Pesa-native checkout and reconciliation

All in one platform tailored to Kenyan SMEs, with affordability and usability as first-class constraints.

---

## 7) Scope
## In Scope (MVP+)
1. Website/Landing Builder (mobile-first, templates, SEO scaffolding)
2. Local keyword research + AI content generation
3. CRM with forms, segmentation, activity history
4. WhatsApp Business integration + FAQ chatbot + human handoff
5. M-Pesa Daraja integration (STK push)
6. Core analytics dashboard + GA4/Search Console integration
7. Training knowledge base

## Out of Scope (Initial)
- Full inventory/WMS
- Deep accounting module
- Native marketplace aggregation
- Advanced ad buying automation (Meta/Google campaign execution)

---

## 8) Functional Requirements by Capability
## 8.1 Website & Landing Builder
- Drag/drop page builder with Kenyan-industry templates.
- Mobile-first design defaults and performance constraints.
- Auto-generated: meta title/description, sitemap.xml, robots.txt, LocalBusiness schema.
- Multi-language page support (English/Swahili/Sheng), including bilingual page variants.
- Publish flow with SSL and custom domain support.

## 8.2 Local SEO & AI Content
- Local keyword discovery with intent categorization (transactional/informational/navigation).
- Suggestions include vernacular and neighborhood context (e.g., Westlands, Kilimani, CBD).
- AI generation for blog posts, product descriptions, FAQs, landing copy.
- Tone and length controls; bilingual outputs.
- Pillar-cluster assistant (topic map + internal linking suggestions).
- Content calendar and scheduling recommendations.

## 8.3 CRM & First-Party Data
- Configurable lead/booking/quote forms.
- Contact timeline with source attribution.
- Segmentation/tagging and notes.
- Campaign actions: basic email/SMS sends or third-party integration.
- Exportable customer data and audit trail for compliance.

## 8.4 WhatsApp & Chatbot
- WhatsApp Business API integration.
- Automated flows: inquiry capture, booking, order status, reminders.
- FAQ chatbot grounded on business-defined knowledge base.
- Code-switch support (English/Swahili).
- Human handoff and conversation assignment.

## 8.5 Payments
- M-Pesa Daraja STK push checkout.
- Webhook handling for payment confirmations.
- Optional Airtel Money/card via gateway adapters.
- Payment reconciliation into CRM/order records.

## 8.6 Analytics & Reporting
- Dashboard metrics: traffic, top pages, bounce rate, rankings, leads, conversion, revenue proxies.
- GA4 + Search Console ingestion.
- Export report as CSV/PDF.
- Scheduled email summaries.

## 8.7 Learning & Support
- In-app guides, help center articles, tutorial videos.
- Community Q&A/forum (phase 2 acceptable).
- Premium virtual onboarding support.

---

## 9) Non-Functional Requirements
- Performance: mobile page load target LCP <= 2.5s on median 4G conditions.
- Availability: 99.9% target for paid tiers.
- Security: OAuth2/OIDC auth, RBAC, admin MFA, encryption in transit/at rest.
- Privacy/compliance: Kenya Data Protection Act + GDPR readiness.
- Scalability: microservice-friendly boundaries; queue-based async workflows.
- Observability: logs, metrics, traces, alerting, audit logs.
- Localization: timezone Africa/Nairobi; local currency KES; multilingual UX support.

---

## 10) Success Metrics (North Star + KPIs)
### North Star
- Monthly qualified leads captured per active business

### KPIs
- Time to publish first site
- Organic impressions/click growth
- Form completion rate
- WhatsApp conversation-to-lead conversion
- M-Pesa checkout completion rate
- 90-day retention by plan tier
- ARPU and free-to-paid conversion

---

## 11) Personas
1. **Amina (Salon Owner)**: needs bookings, WhatsApp reminders, local SEO visibility.
2. **Kamau (Hardware Store)**: wants catalog inquiries + M-Pesa order confirmations.
3. **Otieno (Tutor)**: needs landing pages, lead forms, and bilingual content.

---

## 12) Risks and Mitigations
- API dependency risk (WhatsApp/Daraja): use adapter pattern + retry/idempotency.
- AI content quality risk: human review gates + SEO linting.
- Compliance risk: consent capture, retention policies, DSR tooling.
- Adoption risk: onboarding templates + guided checklist + in-product education.

---

## 13) Milestones
1. M0: Product/design validation + architecture baseline
2. M1: Website builder + SEO basics + authentication
3. M2: CRM + forms + segmentation
4. M3: WhatsApp integration + chatbot MVP
5. M4: M-Pesa checkout + reconciliation
6. M5: Analytics/reporting + knowledge base + beta launch

---

## 14) Release Strategy
- Private alpha (10–20 SMEs)
- Closed beta (100 SMEs, Nairobi-heavy)
- Public launch with tiered pricing and onboarding playbooks

---

## 15) Pricing (Product Packaging)
- **Free**: basic pages, forms, limited AI credits
- **Starter**: CRM + baseline analytics + limited WhatsApp
- **Growth**: full WhatsApp chatbot + M-Pesa + advanced analytics + messaging
- **Enterprise**: custom integrations, dedicated support/hosting, SLA/API access
