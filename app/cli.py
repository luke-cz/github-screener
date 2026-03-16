from __future__ import annotations

import argparse
from pathlib import Path

from app.assess import assess_user
from app.report import build_report_payload, write_html, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitHub profile assessor (MVP).")
    subparsers = parser.add_subparsers(dest="command")

    assess_parser = subparsers.add_parser("assess", help="Assess a GitHub profile.")
    assess_parser.add_argument("username", help="GitHub username")
    assess_parser.add_argument("--token", help="GitHub token (optional)")
    assess_parser.add_argument("--json", dest="json_path", help="Path to JSON report")
    assess_parser.add_argument("--html", dest="html_path", help="Path to HTML report")

    return parser


def run() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command != "assess":
        parser.print_help()
        return

    result = assess_user(args.username, token=args.token)
    payload = build_report_payload(
        username=args.username,
        user_info=result["user"],
        repo_summaries=result["repos"],
        specialization_scores=result["specialization_scores"],
        score_breakdown=result["score_breakdown"],
    )

    json_path = Path(args.json_path) if args.json_path else None
    html_path = Path(args.html_path) if args.html_path else None
    template_dir = Path(__file__).resolve().parent.parent / "templates"

    write_json(payload, json_path)
    if html_path:
        write_html(payload, template_dir, html_path)


if __name__ == "__main__":
    run()
