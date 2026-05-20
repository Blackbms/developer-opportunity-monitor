from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv

from app.notify import send_telegram_message
from app.scoring import should_alert
from app.sources import fetch_jobs_for_company
from app.store import SeenStore


def load_settings(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def format_message(
    company_name: str, job: dict[str, Any], score_info: dict[str, Any]
) -> str:
    title = job.get("title", "Unknown title")
    location = job.get("location", "Unknown location")
    url = job.get("url", "")
    score = score_info.get("score", 0)
    matched = ", ".join(score_info.get("matched", [])) or "none"

    return (
        f"New role match ({score})\n"
        f"Company: {company_name}\n"
        f"Title: {title}\n"
        f"Location: {location}\n"
        f"Matched: {matched}\n"
        f"Link: {url}"
    )


def _effective_settings(
    settings: dict[str, Any], company: dict[str, Any]
) -> dict[str, Any]:
    effective = dict(settings)

    company_min_score = company.get("min_score")
    if company_min_score is not None:
        effective["min_score"] = company_min_score

    company_keywords = company.get("keywords")
    if isinstance(company_keywords, dict):
        merged_keywords = dict(settings.get("keywords", {}))
        for key in ("include", "exclude"):
            if key in company_keywords:
                merged_keywords[key] = company_keywords[key]
        effective["keywords"] = merged_keywords

    return effective


def run_once(settings_path: str = "config/settings.yaml") -> None:
    load_dotenv()
    settings = load_settings(settings_path)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    db_path = str(Path("data") / "jobs.db")
    store = SeenStore(db_path)

    companies = settings.get("companies", [])
    for company in companies:
        company_name = company.get("name", "Unknown")
        provider = company.get("provider", "")
        print(f"Checking {company_name}...")

        try:
            jobs = fetch_jobs_for_company(company)
        except requests.RequestException as exc:
            print(f"Failed to fetch {company_name}: {exc}")
            continue

        for job in jobs:
            fp = store.record_collected_job(company_name, provider, job)
            external_id = str(job.get("external_id", ""))
            url = job.get("url", "")
            if store.has_seen(fp):
                continue

            decision, score_info = should_alert(
                job, _effective_settings(settings, company)
            )
            if decision:
                message = format_message(company_name, job, score_info)
                try:
                    sent = send_telegram_message(bot_token, chat_id, message)
                    if sent:
                        title = job.get("title", "")
                        print(
                            f"Alert sent: {company_name} - {title}"
                        )
                    else:
                        print(
                            f"Alert not sent (Telegram not configured): "
                            f"{company_name} - {job.get('title', '')}"
                        )
                except requests.RequestException as exc:
                    print(f"Failed to notify for {company_name}: {exc}")

            store.mark_seen(fp, company_name, external_id, url)


def prune_seen_jobs(
    settings_path: str = "config/settings.yaml",
    dry_run: bool = False,
) -> int:
    load_dotenv()
    settings = load_settings(settings_path)

    db_path = str(Path("data") / "jobs.db")
    store = SeenStore(db_path)

    removed = 0
    companies = settings.get("companies", [])
    for company in companies:
        company_name = company.get("name", "Unknown")
        provider = company.get("provider", "")
        mode = "previewing" if dry_run else "pruning"
        print(f"{mode.capitalize()} {company_name}...")

        try:
            jobs = fetch_jobs_for_company(company)
        except requests.RequestException as exc:
            print(f"Failed to fetch {company_name}: {exc}")
            continue

        effective_settings = _effective_settings(settings, company)
        for job in jobs:
            fp = store.record_collected_job(company_name, provider, job)
            if store.has_seen(fp):
                decision, _score_info = should_alert(job, effective_settings)
                if not decision:
                    title = job.get("title", "")
                    if dry_run:
                        removed += 1
                        print(
                            f"Would remove filtered job: {company_name} - "
                            f"{title}"
                        )
                    elif store.delete_seen(fp):
                        removed += 1
                        print(
                            f"Removed filtered job: {company_name} - "
                            f"{title}"
                        )

    print(f"Prune complete. Removed {removed} jobs.")
    return removed


if __name__ == "__main__":
    run_once()
