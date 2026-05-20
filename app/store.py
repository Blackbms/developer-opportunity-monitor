from __future__ import annotations

import json
import hashlib
import sqlite3
from pathlib import Path
from typing import Any


class SeenStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_jobs (
                    fingerprint TEXT PRIMARY KEY,
                    company TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    url TEXT,
                    seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS collected_jobs (
                    fingerprint TEXT PRIMARY KEY,
                    company TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    location TEXT,
                    country TEXT,
                    country_code TEXT,
                    url TEXT,
                    apply_url TEXT,
                    raw_json TEXT NOT NULL,
                    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed_at DATETIME
                )
                """
            )

    @staticmethod
    def fingerprint(company: str, external_id: str, url: str) -> str:
        base = f"{company}|{external_id}|{url}".encode("utf-8")
        return hashlib.sha256(base).hexdigest()

    def has_seen(self, fingerprint: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_jobs WHERE fingerprint = ?", (fingerprint,)
            ).fetchone()
            return row is not None

    def mark_seen(
        self,
        fingerprint: str,
        company: str,
        external_id: str,
        url: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO seen_jobs (
                    fingerprint,
                    company,
                    external_id,
                    url
                )
                VALUES (?, ?, ?, ?)
                """,
                (fingerprint, company, external_id, url),
            )
            conn.commit()

    def delete_seen(self, fingerprint: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM seen_jobs WHERE fingerprint = ?",
                (fingerprint,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def record_collected_job(
        self,
        company: str,
        provider: str,
        job: dict[str, Any],
    ) -> str:
        external_id = str(job.get("external_id", ""))
        url = str(job.get("url", ""))
        fingerprint = self.fingerprint(company, external_id, url)
        raw_payload = job.get("raw", job)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO collected_jobs (
                    fingerprint,
                    company,
                    provider,
                    external_id,
                    title,
                    location,
                    country,
                    country_code,
                    url,
                    apply_url,
                    raw_json,
                    collected_at,
                    processed_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    CURRENT_TIMESTAMP,
                    NULL
                )
                """,
                (
                    fingerprint,
                    company,
                    provider,
                    external_id,
                    str(job.get("title", "")),
                    str(job.get("location", "")),
                    str(job.get("country", "")),
                    str(job.get("country_code", "")),
                    url,
                    str(job.get("apply_url", "")),
                    json.dumps(raw_payload, ensure_ascii=False),
                ),
            )
            conn.commit()

        return fingerprint
