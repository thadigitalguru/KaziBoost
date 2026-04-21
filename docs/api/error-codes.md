# KaziBoost API Error Codes

This document lists standardized API error codes returned in the `code` field.

## Core codes
- `validation_error` — request validation failed (422)
- `bad_request` — malformed or invalid request state (400)
- `unauthorized` — authentication required or invalid credentials/token (401)
- `forbidden` — authenticated but not allowed (403)
- `not_found` — resource not found (404)
- `conflict` — duplicate or conflicting operation (409)
- `rate_limited` — too many attempts in a short period (429)
- `http_error` — generic HTTP exception fallback

## Error payload contract
```json
{
  "detail": "human-readable message or validation details",
  "code": "validation_error",
  "request_id": "uuid-or-client-request-id"
}
```
