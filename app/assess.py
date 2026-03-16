from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.config import DEFAULT_CONFIG
from app.github_client import GitHubClient
from app.heuristics import RepoSignals, detect_signals
from app.scoring import aggregate_scores, score_repo_signals


def _repo_file_names(contents: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for item in contents:
        name = item.get("name")
        if name:
            names.append(name)
    return names


def _specialization_max(current: int, candidate: int) -> int:
    return max(current, min(100, candidate))


def _score_specializations(repos: list[dict[str, Any]]) -> dict[str, int]:
    scores = {
        "smart_contracts_solidity": 0,
        "smart_contracts_rust": 0,
        "backend": 0,
        "infrastructure": 0,
        "frontend": 0,
        "mobile": 0,
    }

    for repo in repos:
        languages = set(repo.get("languages", []))
        signals: RepoSignals = repo["signals"]

        solidity_score = 0
        if "Solidity" in languages:
            solidity_score += 60
        if signals.solidity:
            solidity_score += 20
        if signals.tests:
            solidity_score += 10
        if signals.security:
            solidity_score += 10
        scores["smart_contracts_solidity"] = _specialization_max(
            scores["smart_contracts_solidity"], solidity_score
        )

        rust_sc_score = 0
        if "Rust" in languages:
            rust_sc_score += 30
        if signals.rust_sc:
            rust_sc_score += 50
        if signals.tests:
            rust_sc_score += 10
        if signals.security:
            rust_sc_score += 10
        scores["smart_contracts_rust"] = _specialization_max(
            scores["smart_contracts_rust"], rust_sc_score
        )

        backend_score = 0
        if languages & {"Rust", "Go", "TypeScript", "Java"}:
            backend_score += 50
        if signals.tests:
            backend_score += 15
        if signals.ci:
            backend_score += 15
        if signals.docs:
            backend_score += 10
        scores["backend"] = _specialization_max(scores["backend"], backend_score)

        infra_score = 0
        if signals.infra:
            infra_score += 60
        if signals.ci:
            infra_score += 15
        if signals.docs:
            infra_score += 10
        if signals.security:
            infra_score += 15
        scores["infrastructure"] = _specialization_max(
            scores["infrastructure"], infra_score
        )

        frontend_score = 0
        if languages & {"JavaScript", "TypeScript"}:
            frontend_score += 40
        if signals.frontend:
            frontend_score += 30
        if signals.tests:
            frontend_score += 15
        if signals.lint:
            frontend_score += 15
        scores["frontend"] = _specialization_max(scores["frontend"], frontend_score)

        mobile_score = 0
        if signals.mobile:
            mobile_score += 70
        if signals.tests:
            mobile_score += 10
        if signals.ci:
            mobile_score += 10
        if signals.docs:
            mobile_score += 10
        scores["mobile"] = _specialization_max(scores["mobile"], mobile_score)

    return scores


def assess_user(username: str, token: str | None = None) -> dict[str, Any]:
    client = GitHubClient(token=token)
    user_info = client.get_user(username)
    repos = client.list_repos(username)

    filtered = [repo for repo in repos if not repo.get("fork")]
    filtered.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    selected = filtered[: DEFAULT_CONFIG.max_repos]

    repo_summaries: list[dict[str, Any]] = []
    repo_scores: list[dict[str, int]] = []

    for repo in selected:
        owner = repo["owner"]["login"]
        name = repo["name"]
        languages_map = client.get_languages(owner, name)
        languages = sorted(languages_map.keys(), key=lambda k: languages_map[k], reverse=True)

        contents = client.get_contents(owner, name, "")
        file_names = _repo_file_names(contents)

        if ".github" in {item.get("name") for item in contents}:
            try:
                workflows = client.get_contents(owner, name, ".github/workflows")
                if workflows:
                    file_names.append(".github/workflows")
            except Exception:
                pass

        signals = detect_signals(file_names)
        repo_score = score_repo_signals(signals)
        repo_scores.append(repo_score)

        repo_summaries.append(
            {
                "name": name,
                "description": repo.get("description"),
                "html_url": repo.get("html_url"),
                "pushed_at": repo.get("pushed_at"),
                "stars": repo.get("stargazers_count"),
                "forks": repo.get("forks_count"),
                "languages": languages,
                "signals": asdict(signals),
            }
        )

    breakdown = aggregate_scores(repo_scores)
    specialization_scores = _score_specializations(
        [
            {"languages": repo["languages"], "signals": RepoSignals(**repo["signals"])}
            for repo in repo_summaries
        ]
    )

    return {
        "user": user_info,
        "repos": repo_summaries,
        "specialization_scores": specialization_scores,
        "score_breakdown": breakdown,
    }
