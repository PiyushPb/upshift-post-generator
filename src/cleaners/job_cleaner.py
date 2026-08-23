import re
import pandas as pd
from typing import Optional
from src.utils.logger import logger

class JobCleaner:
    """Cleans and deduplicates job records for India searches."""

    @staticmethod
    def format_inr_salary(row: pd.Series) -> str:
        """Formats Indian salaries into clean LPA / monthly display format."""
        min_amt = row.get("min_amount")
        max_amt = row.get("max_amount")
        interval = str(row.get("interval") or "yearly").lower()

        has_min = pd.notnull(min_amt) and min_amt > 0
        has_max = pd.notnull(max_amt) and max_amt > 0

        if not has_min and not has_max:
            return "₹ Not Disclosed"

        def to_lpa(amt: float) -> str:
            if amt >= 100000:
                return f"{amt/100000:.1f} LPA".replace(".0 LPA", " LPA")
            return f"₹{amt:,.0f}"

        suffix = " /mo" if interval == "monthly" else ""

        if has_min and has_max:
            if min_amt == max_amt:
                return f"{to_lpa(min_amt)}{suffix}"
            return f"{to_lpa(min_amt)} - {to_lpa(max_amt)}{suffix}"
        elif has_min:
            return f"From {to_lpa(min_amt)}{suffix}"
        else:
            return f"Up to {to_lpa(max_amt)}{suffix}"

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans, standardizes and deduplicates jobs DataFrame."""
        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()

        # 1. Drop description to keep dataset lightweight
        if "description" in df.columns:
            df = df.drop(columns=["description"])

        # 2. Filter out invalid/empty records
        df = df.dropna(subset=["title", "job_url"])
        df = df[df["title"].str.strip() != ""]

        # 3. Clean strings & whitespace
        for col in ["title", "company", "location"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

        # 4. Standardize date_posted
        if "date_posted" in df.columns:
            df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce").dt.strftime("%Y-%m-%d")

        # 5. Standardize salary display for India
        df["salary_display"] = df.apply(self.format_inr_salary, axis=1)

        # 5. Deduplicate across platforms by (company + title)
        df["_dedup_id"] = (
            df["company"].str.lower().str.replace(r"[^\w]", "", regex=True) + "_" +
            df["title"].str.lower().str.replace(r"[^\w]", "", regex=True)
        )
        df = df.drop_duplicates(subset=["_dedup_id"], keep="first").drop(columns=["_dedup_id"])

        logger.info(f"✨ Cleaned dataset: {len(df)} unique jobs retained.")
        return df.reset_index(drop=True)
