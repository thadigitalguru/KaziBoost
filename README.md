# KaziBoost

AI-powered local business growth platform for Kenyan SMEs.

## Current Slice Implemented
- FastAPI backend scaffold
- Next.js web shell scaffold
- Auth + tenant bootstrap + owner MFA flows
  - `POST /v1/auth/signup`
  - `POST /v1/auth/login`
  - `GET /v1/auth/me`
  - `POST /v1/auth/mfa/enroll`
  - `POST /v1/auth/mfa/challenge`
  - `POST /v1/auth/mfa/verify`
- Sites, SEO, CRM, WhatsApp, M-Pesa, analytics, onboarding, and training modules
- Custom domains, multilingual page variants, SEO topic maps, analytics connectors
- Site template catalog, CRM tag management, WhatsApp human replies, payment provider registry, analytics PDF export
- Site listing, SEO workspace listing, analytics connector status updates, WhatsApp FAQ deletion, onboarding recommendations
- Audit filters, CRM contact search, payment provider lifecycle controls, report schedule updates
- Site detail + unpublish, CRM segment updates, analytics dashboard summary, training search filters/limits
- Site deletion, CRM contact detail, campaign subject filters, SEO calendar date filters, analytics connector deletion
- Site page listing, CRM segment detail, payment provider filters, analytics connector filters, training related articles
- Site page detail, CRM segment contact counts, reconciliation summary, SEO workspace rename, training article duplication
- Web dashboard shell with sites, CRM, WhatsApp, payments, analytics, SEO, and training routes
- Tests-first workflow established

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
export KAZIBOOST_ENV=local
uvicorn kaziboost_api.main:app --reload

# Frontend
cd apps/web
npm install
npm run dev
```
