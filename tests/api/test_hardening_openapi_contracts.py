from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def test_security_headers_are_present_on_responses():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_error_response_contract_includes_code_and_request_id():
    response = client.post(
        "/v1/auth/login",
        json={"email": "invalid@example.com"},
        headers={"x-request-id": "req-contract-001"},
    )
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert body["code"] == "validation_error"
    assert body["request_id"] == "req-contract-001"


def test_openapi_documents_error_response_schema_for_mpesa_initiate():
    openapi = client.get("/openapi.json").json()
    path_item = openapi["paths"]["/v1/payments/mpesa/initiate"]["post"]
    assert "400" in path_item["responses"]
    schema_ref = path_item["responses"]["400"]["content"]["application/json"]["schema"]["$ref"]
    assert schema_ref.endswith("/ErrorResponse")
