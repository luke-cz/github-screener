# GitHub Screener — Talent Intelligence for Technical Hiring

A recruiter‑friendly GitHub screening tool that evaluates **public GitHub profiles** and produces an **AI‑assisted assessment** with scores, signals, and a summary. It supports **1–3 specialization tracks per assessment**, highlights **reputable Web2/Web3 orgs**, and includes **repo evidence** (tests/CI/docs/configs) to ground Code Quality.

## What this app does

- Takes a GitHub handle or profile URL
- Lets you select **1–3 specializations** (e.g., Smart Contracts + Backend + Frontend)
- Pulls public GitHub data and **repo evidence signals**
- Uses Anthropic to generate:
  - overall score (0–100)
  - verdict (Hire / Consider / etc.)
  - dimension scores
  - recruiter summary
- Detects **prestige org signals** from a curated Web2/Web3 list
- Saves assessments locally in the browser (searchable, exportable to CSV)
- Allows **PDF export** of a completed assessment

## Tech overview

- Frontend: single‑page HTML (no framework)
- Backend: FastAPI on Vercel
- AI: Anthropic API (model set via environment variable)

## Setup (local)

1. Install Python 3.11+
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables:

```bash
setx ANTHROPIC_API_KEY "your_key_here"
setx ANTHROPIC_MODEL "your_model_id_here"
setx GITHUB_TOKEN "optional_github_token"
```

4. Start the app locally (via any Python server or Vercel dev)

## Deploy to Vercel

1. Create a new Vercel project and import this folder.
2. Set environment variables in Vercel:
   - `ANTHROPIC_API_KEY`
   - `ANTHROPIC_MODEL`
   - `GITHUB_TOKEN` (recommended for higher GitHub rate limits)
3. Deploy.

Once deployed, the API is available at:

```
POST https://your-vercel-domain/api
```

## Prestige org list

Prestige signals are stored in:

```
prestige_orgs.json
```

Update this file to add or remove Web2/Web3 orgs.

## Notes

- Only **public GitHub data** is used.
- Low GitHub activity is treated as **neutral**, not negative.
- Scores are heuristic and designed to **support** human review.
