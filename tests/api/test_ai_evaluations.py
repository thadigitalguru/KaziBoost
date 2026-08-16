from kaziboost_api.ai_evaluations import EvaluationCase, evaluate_cases
from kaziboost_api.ai_runtime import AiResult


def result(output: dict[str, object], status: str = "completed") -> AiResult:
    return AiResult(
        status=status,
        trace_id="trace",
        capability="seo_title",
        prompt_version="prompt-v1",
        policy_version="policy-v1",
        model="test-model",
        generation_mode="provider",
        output=output,
    )


def test_evaluation_harness_checks_schema_claims_and_language_breakdown():
    cases = [
        EvaluationCase(
            case_id="en-safe",
            capability="seo_title",
            language="en",
            input_context={"keyword": "salon"},
            required_fields=("title",),
            forbidden_substrings=("guaranteed cure",),
            max_output_chars=80,
        ),
        EvaluationCase(
            case_id="sw-safe",
            capability="seo_title",
            language="sw",
            input_context={"keyword": "saluni"},
            required_fields=("title",),
            forbidden_substrings=("secret",),
            max_output_chars=80,
        ),
    ]

    report = evaluate_cases(cases, lambda case: result({"title": f"{case.language} title"}))

    assert report.total == 2
    assert report.passed == 2
    assert report.pass_rate == 1.0
    assert report.by_language == {"en": {"total": 1, "passed": 1}, "sw": {"total": 1, "passed": 1}}


def test_evaluation_harness_reports_unsafe_claim_failure():
    case = EvaluationCase(
        case_id="unsafe-claim",
        capability="seo_title",
        language="en",
        input_context={},
        required_fields=("title",),
        forbidden_substrings=("guaranteed cure",),
        max_output_chars=80,
    )

    report = evaluate_cases([case], lambda _case: result({"title": "Guaranteed cure for every customer"}))

    assert report.passed == 0
    assert report.failures[0].violations == ("forbidden:guaranteed cure",)
