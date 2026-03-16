from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from app.assess import assess_user
from app.report import build_report_payload

app = FastAPI(title="GitHub Assessor", version="0.1.0")


@app.get("/assess")
def assess(username: str = Query(..., min_length=1, max_length=80)) -> dict:
    try:
        result = assess_user(username)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload = build_report_payload(
        username=username,
        user_info=result["user"],
        repo_summaries=result["repos"],
        specialization_scores=result["specialization_scores"],
        score_breakdown=result["score_breakdown"],
    )
    return payload
