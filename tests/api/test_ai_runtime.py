from dataclasses import dataclass

from kaziboost_api.ai_runtime import (
    AiRequest,
    AiRuntime,
    ProviderResponse,
    SafetyDecision,
)


@dataclass
class FakeProvider:
    model: str = "test-model"
    output: dict[str, object] | None = None

    def generate(self, request: AiRequest) -> ProviderResponse:
        return ProviderResponse(model=self.model, output=self.output or {"title": "Safe title"}, latency_ms=12, output_tokens=4)


class AllowSafety:
    def check_input(self, request: AiRequest) -> SafetyDecision:
        return SafetyDecision.allow()

    def check_output(self, request: AiRequest, output: dict[str, object]) -> SafetyDecision:
        return SafetyDecision.allow()


def request() -> AiRequest:
    return AiRequest(
        tenant_id="tenant-a",
        user_id="user-a",
        capability="seo_title",
        prompt_version="seo-v1",
        policy_version="policy-v1",
        input_context={"keyword": "salon westlands"},
        trace_id="trace-a",
    )


def test_runtime_returns_validated_result_and_metadata():
    runtime = AiRuntime(provider_allowlist={"test-model"})
    result = runtime.run(request(), FakeProvider(), AllowSafety(), validator=lambda output: {"title": str(output["title"])})

    assert result.status == "completed"
    assert result.output == {"title": "Safe title"}
    assert result.model == "test-model"
    assert result.prompt_version == "seo-v1"
    assert result.trace_id == "trace-a"


def test_runtime_fails_closed_for_input_and_output_safety():
    class BlockInput(AllowSafety):
        def check_input(self, request: AiRequest) -> SafetyDecision:
            return SafetyDecision.block("prompt_injection")

    blocked = AiRuntime(provider_allowlist={"test-model"}).run(request(), FakeProvider(), BlockInput(), validator=lambda value: value)
    assert blocked.status == "blocked"
    assert blocked.reason == "prompt_injection"

    class ReviewOutput(AllowSafety):
        def check_output(self, request: AiRequest, output: dict[str, object]) -> SafetyDecision:
            return SafetyDecision.review("unsupported_claim")

    review = AiRuntime(provider_allowlist={"test-model"}).run(request(), FakeProvider(), ReviewOutput(), validator=lambda value: value)
    assert review.status == "needs_review"
    assert review.reason == "unsupported_claim"


def test_runtime_uses_deterministic_fallback_on_provider_failure():
    class BrokenProvider:
        def generate(self, request: AiRequest) -> ProviderResponse:
            raise TimeoutError("provider timeout")

    result = AiRuntime(provider_allowlist={"test-model"}).run(
        request(),
        BrokenProvider(),
        AllowSafety(),
        validator=lambda output: output,
        fallback=lambda _request: {"title": "Fallback title"},
    )
    assert result.status == "completed"
    assert result.generation_mode == "fallback"
    assert result.output == {"title": "Fallback title"}
