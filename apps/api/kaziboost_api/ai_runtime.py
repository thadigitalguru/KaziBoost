from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


@dataclass(frozen=True)
class AiRequest:
    tenant_id: str
    user_id: str | None
    capability: str
    prompt_version: str
    policy_version: str
    input_context: dict[str, object]
    trace_id: str


@dataclass(frozen=True)
class ProviderResponse:
    model: str
    output: dict[str, object]
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0


class AiProvider(Protocol):
    def generate(self, request: AiRequest) -> ProviderResponse: ...


@dataclass(frozen=True)
class SafetyDecision:
    status: str
    reason: str | None = None

    @classmethod
    def allow(cls) -> "SafetyDecision":
        return cls("allowed")

    @classmethod
    def block(cls, reason: str) -> "SafetyDecision":
        return cls("blocked", reason)

    @classmethod
    def review(cls, reason: str) -> "SafetyDecision":
        return cls("needs_review", reason)


class SafetyPolicy(Protocol):
    def check_input(self, request: AiRequest) -> SafetyDecision: ...

    def check_output(self, request: AiRequest, output: dict[str, object]) -> SafetyDecision: ...


@dataclass(frozen=True)
class AiResult:
    status: str
    trace_id: str
    capability: str
    prompt_version: str
    policy_version: str
    model: str | None = None
    generation_mode: str | None = None
    output: dict[str, object] | None = None
    reason: str | None = None
    latency_ms: int | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: dict[str, object] = field(default_factory=dict)


class AiRuntime:
    def __init__(self, provider_allowlist: set[str]) -> None:
        self.provider_allowlist = frozenset(provider_allowlist)

    def run(
        self,
        request: AiRequest,
        provider: AiProvider,
        safety_policy: SafetyPolicy,
        validator: Callable[[dict[str, object]], dict[str, object]],
        fallback: Callable[[AiRequest], dict[str, object]] | None = None,
    ) -> AiResult:
        input_decision = safety_policy.check_input(request)
        if input_decision.status != "allowed":
            return self._result(request, input_decision.status, reason=input_decision.reason)

        try:
            response = provider.generate(request)
            if response.model not in self.provider_allowlist:
                return self._result(request, "not_ready", reason="model_not_allowed", model=response.model)
            output = validator(response.output)
            latency_ms = response.latency_ms
            model = response.model
            mode = "provider"
            input_tokens = response.input_tokens
            output_tokens = response.output_tokens
        except Exception as exc:  # provider failures must become explicit results
            if fallback is None:
                return self._result(request, "failed", reason=type(exc).__name__)
            try:
                output = validator(fallback(request))
            except Exception as fallback_exc:
                return self._result(request, "failed", reason=f"fallback:{type(fallback_exc).__name__}")
            latency_ms = None
            model = None
            mode = "fallback"
            input_tokens = 0
            output_tokens = 0

        output_decision = safety_policy.check_output(request, output)
        if output_decision.status != "allowed":
            return self._result(
                request,
                output_decision.status,
                reason=output_decision.reason,
                model=model,
                generation_mode=mode,
                output=output,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

        return self._result(
            request,
            "completed",
            model=model,
            generation_mode=mode,
            output=output,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    @staticmethod
    def _result(
        request: AiRequest,
        status: str,
        reason: str | None = None,
        **kwargs: object,
    ) -> AiResult:
        return AiResult(
            status=status,
            trace_id=request.trace_id,
            capability=request.capability,
            prompt_version=request.prompt_version,
            policy_version=request.policy_version,
            reason=reason,
            **kwargs,
        )
