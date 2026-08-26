import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TMP_DIR = BASE_DIR / "tmp"
DATA_DIR = TMP_DIR / "data"
POSTS_DIR = TMP_DIR / "posts"
DB_PATH = TMP_DIR / "upshift_jobs.db"

# Ensure temp directories exist
for path in [TMP_DIR, DATA_DIR, POSTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

@dataclass
class ScraperConfig:
    # India-focused platforms
    site_names: List[str] = field(default_factory=lambda: [
        "indeed",
        "linkedin",
        "naukri",
        "glassdoor",
        "google"
    ])
    search_terms: List[str] = field(default_factory=lambda: [
        "Software Engineer",
        "Frontend Developer",
        "Backend Developer",
        "Data Analyst"
    ])
    location: str = "India"
    country_indeed: str = "India"
    results_wanted: int = 15
    hours_old: Optional[int] = 72
    drop_description: bool = True  # We only need metadata, no long description
    verbose: int = 1
    max_workers: int = 4

@dataclass
class SelectorConfig:
    top_n: int = 10
    min_salary_annual: Optional[float] = None
    excluded_keywords: List[str] = field(default_factory=lambda: ["unpaid", "commission"])
    required_keywords: List[str] = field(default_factory=list)
    remote_only: bool = False
    limit_per_run: int = 20

@dataclass
class TelegramConfig:
    bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    dry_run: bool = field(default_factory=lambda: os.getenv("TELEGRAM_DRY_RUN", "true").lower() == "true")

    @property
    def chat_ids(self) -> List[str]:
        """Returns a list of clean Telegram chat IDs parsed from comma/space separated values."""
        raw = self.chat_id or ""
        # Support comma-separated or space-separated chat IDs
        raw_list = [c.strip() for c in raw.replace(";", ",").split(",") if c.strip()]
        return raw_list

