from __future__ import annotations

from typing import Any


def _to_search_text(job: dict[str, Any]) -> str:
    title = job.get("title", "")
    location = job.get("location", "")
    return f"{title} {location}".lower()


def score_job(
    job: dict[str, Any],
    include_weights: dict[str, int],
    exclude_keywords: list[str],
) -> tuple[int, list[str], bool]:
    text = _to_search_text(job)

    is_excluded = any(keyword.lower() in text for keyword in exclude_keywords)
    matched: list[str] = []
    score = 0

    for keyword, weight in include_weights.items():
        if keyword.lower() in text:
            matched.append(keyword)
            score += int(weight)

    return score, matched, is_excluded


def _location_allowed(
    job: dict[str, Any], allowed_locations: list[str]
) -> bool:
    if not allowed_locations:
        return True

    location = str(job.get("location", "")).lower()
    country = str(job.get("country", "")).lower()
    country_code = str(job.get("country_code", "")).lower()
    return any(
        allowed_location.lower() in location
        or allowed_location.lower() in country
        or allowed_location.lower() in country_code
        for allowed_location in allowed_locations
    )


def should_alert(
    job: dict[str, Any], config: dict[str, Any]
) -> tuple[bool, dict[str, Any]]:
    include_weights = config.get("keywords", {}).get("include", {})
    exclude_keywords = config.get("keywords", {}).get("exclude", [])
    min_score = int(config.get("min_score", 0))
    allowed_locations = config.get("locations", {}).get("include", [])

    score, matched, is_excluded = score_job(
        job, include_weights, exclude_keywords
    )
    is_location_excluded = not _location_allowed(job, allowed_locations)
    decision = (
        (not is_excluded)
        and (not is_location_excluded)
        and score >= min_score
    )

    return decision, {
        "score": score,
        "matched": matched,
        "excluded": is_excluded,
        "location_excluded": is_location_excluded,
    }
