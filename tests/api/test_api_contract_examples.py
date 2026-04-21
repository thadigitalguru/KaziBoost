from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def test_openapi_has_request_examples_for_key_endpoints():
    openapi = client.get("/openapi.json").json()

    mpesa_post = openapi["paths"]["/v1/payments/mpesa/initiate"]["post"]
    wa_post = openapi["paths"]["/v1/whatsapp/webhook/incoming"]["post"]

    mpesa_examples = mpesa_post["requestBody"]["content"]["application/json"]["examples"]
    wa_examples = wa_post["requestBody"]["content"]["application/json"]["examples"]

    assert "basic" in mpesa_examples
    assert "booking_query" in wa_examples


def test_error_codes_catalog_exists_and_lists_core_codes():
    with open("docs/api/error-codes.md", "r", encoding="utf-8") as f:
        content = f.read()

    assert "validation_error" in content
    assert "unauthorized" in content
    assert "rate_limited" in content
