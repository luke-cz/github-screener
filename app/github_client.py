from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

import requests

from app.config import DEFAULT_CONFIG


@dataclass
class GitHubClient:
    token: str | None = None

    def __post_init__(self) -> None:
        if not self.token:
            self.token = os.getenv("GITHUB_TOKEN")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": DEFAULT_CONFIG.user_agent,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{DEFAULT_CONFIG.github_api_base}{path}"
        response = requests.get(url, headers=self._headers(), params=params, timeout=20)
        if response.status_code == 403 and "rate limit" in response.text.lower():
            raise RuntimeError("GitHub rate limit exceeded. Set GITHUB_TOKEN and retry.")
        response.raise_for_status()
        return response.json()

    def get_user(self, username: str) -> dict[str, Any]:
        return self._get(f"/users/{username}")

    def list_repos(self, username: str) -> list[dict[str, Any]]:
        params = {"per_page": 100, "sort": "updated", "type": "owner"}
        return self._get(f"/users/{username}/repos", params=params)

    def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        return self._get(f"/repos/{owner}/{repo}/languages")

    def get_contents(self, owner: str, repo: str, path: str = "") -> list[dict[str, Any]]:
        return self._get(f"/repos/{owner}/{repo}/contents/{path}")
