from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from .ai_runtime import AiResult


EVALUATION_VERSION = "ai-eval-v1"


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    capability: str
    language: str
    input_context: dict[str, object]
    expected_status: str = "completed"
    required_fields: tuple[str, ...] = ()
    forbidden_substrings: tuple[str, ...] = ()
    max_output_chars: int = 4000


@dataclass(frozen=True)
class EvaluationFailure:
    case_id: str
    capability: str
    language: str
    violations: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationReport:
    evaluation_version: str
    total: int
    passed: int
    failures: tuple[EvaluationFailure, ...]
    by_language: dict[str, dict[str, int]]

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 1.0


def evaluate_case(case: EvaluationCase, result: AiResult) -> EvaluationFailure | None:
    violations: list[str] = []
    if result.status != case.expected_status:
        violations.append(f"status:{result.status}")

    output = result.output or {}
    for field in case.required_fields:
        if field not in output or output[field] in (None, ""):
            violations.append(f"missing:{field}")

    serialized = json.dumps(output, ensure_ascii=False).lower()
    for forbidden in case.forbidden_substrings:
        if forbidden.lower() in serialized:
            violations.append(f"forbidden:{forbidden}")
    if len(serialized) > case.max_output_chars:
        violations.append(f"max_chars:{case.max_output_chars}")

    if not violations:
        return None
    return EvaluationFailure(
        case_id=case.case_id,
        capability=case.capability,
        language=case.language,
        violations=tuple(violations),
    )


def evaluate_cases(
    cases: list[EvaluationCase],
    execute: Callable[[EvaluationCase], AiResult],
) -> EvaluationReport:
    failures: list[EvaluationFailure] = []
    by_language: dict[str, dict[str, int]] = {}
    for case in cases:
        result = execute(case)
        failure = evaluate_case(case, result)
        language_stats = by_language.setdefault(case.language, {"total": 0, "passed": 0})
        language_stats["total"] += 1
        if failure:
            failures.append(failure)
        else:
            language_stats["passed"] += 1

    return EvaluationReport(
        evaluation_version=EVALUATION_VERSION,
        total=len(cases),
        passed=len(cases) - len(failures),
        failures=tuple(failures),
        by_language=by_language,
    )
