from .models import ErrorResponse


def error_responses(*status_codes: int) -> dict:
    responses: dict = {}
    for status_code in status_codes:
        responses[status_code] = {
            "model": ErrorResponse,
            "description": f"Error {status_code}",
        }
    return responses
