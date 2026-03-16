from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    max_repos: int = 8
    github_api_base: str = "https://api.github.com"
    user_agent: str = "github-assessor-mvp"


DEFAULT_CONFIG = AppConfig()
