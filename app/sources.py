from __future__ import annotations

from urllib.parse import urlparse
from typing import Any

import requests


def fetch_greenhouse_jobs(board: str) -> list[dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    payload = response.json()
    jobs = payload.get("jobs", [])

    normalized: list[dict[str, Any]] = []
    for job in jobs:
        normalized.append(
            {
                "external_id": str(job.get("id", "")),
                "title": job.get("title", ""),
                "url": job.get("absolute_url", ""),
                "location": (job.get("location") or {}).get("name", ""),
                "raw": job,
            }
        )
    return normalized


def _resolve_icims_jobs_api(company: dict[str, Any]) -> str:
    configured = str(company.get("jobs_api_url", "")).strip()
    if configured:
        return configured

    careers_url = str(company.get("careers_url", "")).strip()
    if careers_url:
        parsed = urlparse(careers_url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/api/jobs"

    return ""


def fetch_icims_jobs(company: dict[str, Any]) -> list[dict[str, Any]]:
    jobs_api_url = _resolve_icims_jobs_api(company)
    if not jobs_api_url:
        return []

    response = requests.get(
        jobs_api_url,
        headers={"Accept": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []

    normalized: list[dict[str, Any]] = []
    for job in jobs:
        data = job.get("data", {}) if isinstance(job, dict) else {}
        external_id = str(data.get("req_id") or data.get("slug") or "")
        title = str(data.get("title") or "")
        location = str(
            data.get("location_name") or data.get("full_location") or ""
        )
        language = str(data.get("language") or "en-us")
        careers_url = str(company.get("careers_url", "")).strip()
        base_url = careers_url.rstrip("/")
        detail_url = (
            f"{base_url}/{external_id}?lang={language}"
            if base_url and external_id
            else str(data.get("apply_url") or "")
        )

        normalized.append(
            {
                "external_id": external_id,
                "title": title,
                "url": detail_url,
                "apply_url": str(data.get("apply_url") or ""),
                "location": location,
                "country": str(data.get("country") or ""),
                "country_code": str(data.get("country_code") or ""),
                "raw": job,
            }
        )

    return normalized


def fetch_jobs_for_company(company: dict[str, Any]) -> list[dict[str, Any]]:
    provider = company.get("provider", "").lower()
    if provider == "greenhouse":
        board = company.get("board", "")
        if not board:
            return []
        return fetch_greenhouse_jobs(board)
    if provider == "icims":
        return fetch_icims_jobs(company)

    # Minimal scaffold: unsupported providers are skipped gracefully.
    return []
