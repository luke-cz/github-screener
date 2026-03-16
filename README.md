# GitHub Assessor (MVP)

This is a lightweight MVP that fetches public GitHub profile data and produces a concise assessment report with scores and specialization signals.

## Quick start

1. Install Python 3.11+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Recommended) Set a GitHub token to avoid rate limits:

```bash
setx GITHUB_TOKEN "your_token_here"
```

4. Run an assessment:

```bash
python -m app assess octocat --html report.html --json report.json
```

## Deploy to Vercel

1. Create a new Vercel project and import this folder.
2. Set an environment variable `GITHUB_TOKEN` in Vercel (recommended).
3. Deploy.

Once deployed, call:

```
GET https://your-vercel-domain/api/assess?username=octocat
```

## What this MVP does

- Pulls up to 8 most recently updated public repos
- Checks for signals like tests, CI, linting, docs, and infra tooling
- Computes an overall score and specialization fit
- Outputs JSON and optional HTML

## Notes

- This uses public GitHub API endpoints only.
- Private repos are not supported in this MVP.
- Scores are heuristic and are intended to support, not replace, human review.
