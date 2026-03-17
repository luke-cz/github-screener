from fastapi import FastAPI, HTTPException, Query
from app.assess import assess_user
from app.report import build_report_payload

app = FastAPI(title="GitHub Assessor", version="0.1.0")

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
@app.get("/api/assess")
def assess(username: str = Query(..., min_length=1, max_length=80)) -> dict:
    try:
        normalized = _normalize_username(username)
        result = assess_user(normalized)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return build_report_payload(
        username=normalized,
        user_info=result["user"],
        repo_summaries=result["repos"],
        specialization_scores=result["specialization_scores"],
        score_breakdown=result["score_breakdown"],
    )