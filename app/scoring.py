from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.heuristics import RepoSignals


@dataclass
class ScoreBreakdown:
    code_quality: int
    architecture: int
    testing: int
    security: int
    maintainability: int
    domain: int
    overall: int


def _clamp(value: float) -> int:
    return max(0, min(100, int(round(value))))


def score_repo_signals(signals: RepoSignals) -> dict[str, int]:
    code_quality = 10 if signals.lint else 4
    architecture = 8 if signals.docs else 3
    testing = 12 if signals.tests else 2
    security = 8 if signals.security else 3
    maintainability = 8 if signals.docs else 3
    domain = 6 * sum(
        [
            signals.solidity,
            signals.rust_sc,
            signals.frontend,
            signals.infra,
            signals.mobile,
        ]
    )
    return {
        "code_quality": code_quality,
        "architecture": architecture,
        "testing": testing,
        "security": security,
        "maintainability": maintainability,
        "domain": domain,
    }


def aggregate_scores(scores: Iterable[dict[str, int]]) -> ScoreBreakdown:
    totals = {
        "code_quality": 0,
        "architecture": 0,
        "testing": 0,
        "security": 0,
        "maintainability": 0,
        "domain": 0,
    }
    count = 0
    for item in scores:
        count += 1
        for key in totals:
            totals[key] += item.get(key, 0)

    if count == 0:
        return ScoreBreakdown(0, 0, 0, 0, 0, 0, 0)

    averaged = {key: totals[key] / count for key in totals}
    overall = (
        averaged["code_quality"]
        + averaged["architecture"]
        + averaged["testing"]
        + averaged["security"]
        + averaged["maintainability"]
        + averaged["domain"]
    )
    return ScoreBreakdown(
        code_quality=_clamp(averaged["code_quality"] * 2.5),
        architecture=_clamp(averaged["architecture"] * 2.5),
        testing=_clamp(averaged["testing"] * 2.5),
        security=_clamp(averaged["security"] * 2.5),
        maintainability=_clamp(averaged["maintainability"] * 2.5),
        domain=_clamp(averaged["domain"] * 2.5),
        overall=_clamp(overall * 2.5),
    )
