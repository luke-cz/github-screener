from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import json
import os
import requests

app = FastAPI()


class AssessRequest(BaseModel):
    username: str
    domain: str


def _normalize_username(value: str) -> str:
    trimmed = value.strip()
    lowered = trimmed.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        try:
            path = trimmed.split("github.com/", 1)[1]
            return path.split("/", 1)[0]
        except Exception:
            return trimmed
    if "github.com/" in lowered:
        path = trimmed.split("github.com/", 1)[1]
        return path.split("/", 1)[0]
    return trimmed.lstrip("@")


def _github_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_github_json(path: str):
    url = f"https://api.github.com{path}"
    res = requests.get(url, headers=_github_headers(), timeout=20)
    if not res.ok:
        detail = ""
        try:
            detail = res.json().get("message", "")
        except Exception:
            detail = res.text[:200]
        detail = detail.strip()
        extra = f" - {detail}" if detail else ""
        raise HTTPException(status_code=400, detail=f"GitHub API error: {res.status_code}{extra}")
    return res.json()


def _fetch_repo_dir(owner: str, repo: str, path: str = ""):
    safe_path = f"/{path.strip('/')}" if path else ""
    return _fetch_github_json(f"/repos/{owner}/{repo}/contents{safe_path}")


def _fetch_repo_text_file(owner: str, repo: str, path: str, limit: int = 2000) -> str:
    try:
        data = _fetch_repo_dir(owner, repo, path)
    except HTTPException:
        return ""
    if not isinstance(data, dict) or data.get("type") != "file":
        return ""
    content = data.get("content") or ""
    if data.get("encoding") == "base64" and content:
        try:
            text = base64.b64decode(content).decode("utf-8", errors="ignore")
        except Exception:
            return ""
        return text[:limit]
    return ""


def _repo_signals(owner: str, repo: str) -> dict:
    try:
        entries = _fetch_repo_dir(owner, repo)
    except HTTPException:
        return {"files": [], "signals": []}

    if not isinstance(entries, list):
        return {"files": [], "signals": []}

    names = [e.get("name", "") for e in entries if isinstance(e, dict)]
    lower = {n.lower(): n for n in names}

    def _has_any(prefixes):
        return any(p in lower for p in prefixes)

    has_tests = _has_any(["tests", "test", "__tests__"])
    has_ci = ".github" in lower or _has_any([".travis.yml", "circleci", "azure-pipelines.yml"])
    has_docs = _has_any(["readme.md", "docs"])
    has_lint = _has_any([".eslintrc", ".eslintrc.js", ".eslintrc.json", ".pylintrc", "ruff.toml"])
    has_build = _has_any(["package.json", "pyproject.toml", "cargo.toml", "go.mod"])

    signals = []
    if has_tests:
        signals.append("tests folder present")
    if has_ci:
        signals.append("ci/workflows present")
    if has_docs:
        signals.append("readme/docs present")
    if has_lint:
        signals.append("lint config present")
    if has_build:
        signals.append("build config present")

    return {"files": names, "signals": signals}


@app.get("/")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api")
def health_api() -> dict:
    return {"status": "ok"}


@app.post("/api")
def assess_api(payload: AssessRequest) -> dict:
    return assess_ai(payload)


@app.post("/")
@app.post("/assess_ai")
def assess_ai(payload: AssessRequest) -> dict:
    username = _normalize_username(payload.username)
    domain = payload.domain.strip() if payload.domain else "General"

    profile = _fetch_github_json(f"/users/{username}")
    repos = _fetch_github_json(f"/users/{username}/repos?sort=updated&per_page=12&type=public")

    repo_summary = [
        {
            "name": r.get("name"),
            "description": r.get("description"),
            "language": r.get("language"),
            "stars": r.get("stargazers_count"),
            "forks": r.get("forks_count"),
            "updatedAt": (r.get("updated_at") or "")[:10],
            "fork": r.get("fork"),
        }
        for r in repos[:10]
    ]

    top_repos = [r for r in repos if not r.get("fork")]
    if not top_repos:
        top_repos = repos[:3]
    top_repos = top_repos[:3]

    repo_evidence = []
    for r in top_repos:
        name = r.get("name")
        if not name:
            continue
        signals = _repo_signals(username, name)
        readme = (
            _fetch_repo_text_file(username, name, "README.md")
            or _fetch_repo_text_file(username, name, "readme.md")
        )
        repo_evidence.append(
            {
                "name": name,
                "signals": signals.get("signals", []),
                "readme_excerpt": readme[:1200],
            }
        )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing ANTHROPIC_API_KEY.")

    model = os.getenv("ANTHROPIC_MODEL")
    if not model:
        raise HTTPException(status_code=500, detail="Missing ANTHROPIC_MODEL.")

    system_prompt = (
        "You are a senior technical recruiter and assessor. "
        "Be precise, honest, and evidence-based. "
        "Return ONLY valid JSON, no markdown."
    )

    user_prompt = f"""Assess this GitHub profile for the domain: "{domain}".

Profile:
- Username: {profile.get("login")}
- Name: {profile.get("name") or "N/A"}
- Bio: {profile.get("bio") or "N/A"}
- Public repos: {profile.get("public_repos")}
- Followers: {profile.get("followers")}
- Account created: {(profile.get("created_at") or "")[:10]}

Top repositories:
{repo_summary}

Repo evidence (file signals + README excerpts when available):
{repo_evidence}

When scoring Code Quality, rely on concrete evidence from repo files/signals. If evidence is weak, mention low confidence in the note, but do not penalize for low activity alone.
Do NOT downgrade scores just because repo activity is infrequent. Treat low activity as neutral unless there are clear red flags.
If there are no red flags, keep scores in a healthy range even with modest public activity.

Return a JSON object with exactly this structure:
{{
  "overallScore": <integer 0-100>,
  "verdict": <one of: "Strong Hire", "Hire", "Consider", "Maybe", "Pass">,
  "headline": <one sentence, max 15 words>,
  "summary": <3-4 paragraphs, recruiter-facing, evidence-based>,
  "dimensions": [
    {{ "name": "Domain Depth", "score": <0-100>, "note": <10 words max> }},
    {{ "name": "Code Quality", "score": <0-100>, "note": <10 words max> }},
    {{ "name": "Activity Level", "score": <0-100>, "note": <10 words max> }},
    {{ "name": "Open Source Impact", "score": <0-100>, "note": <10 words max> }}
  ],
  "flags": [
    {{ "type": "positive"|"warning"|"concern", "text": <max 5 words> }}
  ]
}}
"""

    res = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": model,
            "max_tokens": 1500,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=40,
    )
    if not res.ok:
        detail = res.text[:500]
        raise HTTPException(status_code=400, detail=f"Anthropic API error: {detail}")

    data = res.json()
    content = "".join([c.get("text", "") for c in data.get("content", [])])
    cleaned = content.replace("```json", "").replace("```", "").strip()
    try:
        analysis = json.loads(cleaned)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to parse AI response.")

    return {
        "profile": {
            "login": profile.get("login"),
            "name": profile.get("name"),
            "bio": profile.get("bio"),
            "avatar_url": profile.get("avatar_url"),
            "html_url": profile.get("html_url"),
            "company": profile.get("company"),
            "location": profile.get("location"),
        },
        "repos": repo_summary,
        "analysis": analysis,
    }

