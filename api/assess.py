from fastapi import FastAPI, HTTPException, Query
import requests
import os

app = FastAPI()

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

@app.get("/")
@app.get("/assess")
def assess(username: str = Query(..., min_length=1, max_length=80)):
    try:
        username = _normalize_username(username)
        token = os.getenv("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=20)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail=f"GitHub API error: {r.status_code}")
        return {"username": username, "profile": r.json()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
