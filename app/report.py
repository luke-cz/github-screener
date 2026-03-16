from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.scoring import ScoreBreakdown


def build_report_payload(
    username: str,
    user_info: dict[str, Any],
    repo_summaries: list[dict[str, Any]],
    specialization_scores: dict[str, int],
    score_breakdown: ScoreBreakdown,
) -> dict[str, Any]:
    return {
        "username": username,
        "profile": {
            "name": user_info.get("name"),
            "bio": user_info.get("bio"),
            "public_repos": user_info.get("public_repos"),
            "followers": user_info.get("followers"),
            "following": user_info.get("following"),
            "created_at": user_info.get("created_at"),
        },
        "scores": {
            "overall": score_breakdown.overall,
            "breakdown": asdict(score_breakdown),
            "specializations": specialization_scores,
        },
        "repos": repo_summaries,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_json(payload: dict[str, Any], path: Path | None) -> None:
    if path is None:
        print(json.dumps(payload, indent=2))
        return
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_html(payload: dict[str, Any], template_dir: Path, path: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html")
    html = template.render(payload=payload)
    path.write_text(html, encoding="utf-8")
