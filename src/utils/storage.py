import sqlite3
from pathlib import Path
from typing import Optional, List, Set
import pandas as pd
from .logger import logger

class JobStorage:
    """Handles SQLite database persistence and CSV/JSON exports for job records."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initializes database tables for job records and publication history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    site TEXT,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    job_url TEXT,
                    job_url_direct TEXT,
                    date_posted TEXT,
                    job_type TEXT,
                    min_amount REAL,
                    max_amount REAL,
                    currency TEXT,
                    interval TEXT,
                    is_remote INTEGER,
                    job_level TEXT,
                    skills TEXT,
                    company_industry TEXT,
                    company_url TEXT,
                    company_logo TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posted_jobs (
                    job_id TEXT PRIMARY KEY,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    telegram_message_id INTEGER,
                    status TEXT
                )
            """)
            conn.commit()

    def get_already_posted_ids(self) -> Set[str]:
        """Returns a set of job IDs that have already been posted to Telegram."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT job_id FROM posted_jobs WHERE status = 'SUCCESS'")
            rows = cursor.fetchall()
            return {row[0] for row in rows}

    def save_raw_jobs(self, df: pd.DataFrame) -> int:
        """Upserts jobs into SQLite database. Returns count of inserted records."""
        if df.empty:
            return 0

        # Ensure unique identifier column exists
        records_to_insert = []
        for _, row in df.iterrows():
            job_id = str(row.get("id") or row.get("job_url") or f"{row.get('company')}-{row.get('title')}")
            records_to_insert.append((
                job_id,
                str(row.get("site", "")),
                str(row.get("title", "")),
                str(row.get("company", "")),
                str(row.get("location", "")),
                str(row.get("job_url", "")),
                str(row.get("job_url_direct", "") or ""),
                str(row.get("date_posted", "") or ""),
                str(row.get("job_type", "") or ""),
                row.get("min_amount") if pd.notnull(row.get("min_amount")) else None,
                row.get("max_amount") if pd.notnull(row.get("max_amount")) else None,
                str(row.get("currency", "") or ""),
                str(row.get("interval", "") or ""),
                1 if row.get("is_remote") is True else 0,
                str(row.get("job_level", "") or ""),
                str(row.get("skills", "") or ""),
                str(row.get("company_industry", "") or ""),
                str(row.get("company_url", "") or ""),
                str(row.get("company_logo", "") or "")
            ))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO jobs (
                    job_id, site, title, company, location, job_url, job_url_direct,
                    date_posted, job_type, min_amount, max_amount, currency,
                    interval, is_remote, job_level, skills, company_industry,
                    company_url, company_logo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records_to_insert)
            conn.commit()

        logger.info(f"💾 Stored/Updated {len(records_to_insert)} jobs in SQLite database: {self.db_path.name}")
        return len(records_to_insert)

    def mark_job_posted(self, job_id: str, telegram_message_id: Optional[int] = None, status: str = "SUCCESS"):
        """Records a job as posted in Telegram."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO posted_jobs (job_id, telegram_message_id, status)
                VALUES (?, ?, ?)
            """, (job_id, telegram_message_id, status))
            conn.commit()
