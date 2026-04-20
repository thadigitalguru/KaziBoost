# KaziBoost

AI-powered local business growth platform for Kenyan SMEs.

## Current Slice Implemented
- FastAPI backend scaffold
- Auth + tenant bootstrap endpoints
  - `POST /v1/auth/signup`
  - `POST /v1/auth/login`
  - `GET /v1/auth/me`
- Tests-first workflow established

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn kaziboost_api.main:app --reload
```
