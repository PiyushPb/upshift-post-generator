from typing import Optional, Set, List
import pandas as pd
from src.config.settings import SelectorConfig
from src.utils.logger import logger

class JobSelector:
    """
    Filters and ranks cleaned jobs according to target criteria and deduplication history.
    """

    def __init__(self, config: Optional[SelectorConfig] = None):
        self.config = config or SelectorConfig()

    def select(
        self,
        df: pd.DataFrame,
        already_posted_ids: Optional[Set[str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Applies selection criteria and removes already posted jobs."""
        if df.empty:
            return df

        selected_df = df.copy()
        initial_count = len(selected_df)

        # 1. Filter out already posted jobs
        if already_posted_ids:
            def is_new(row) -> bool:
                job_id = str(row.get("id") or row.get("job_url") or f"{row.get('company')}-{row.get('title')}")
                return job_id not in already_posted_ids

            selected_df = selected_df[selected_df.apply(is_new, axis=1)]
            logger.info(f"🚫 Filtered out {initial_count - len(selected_df)} already posted jobs.")

        # 2. Excluded keywords filter
        if self.config.excluded_keywords:
            ex_pattern = "|".join([re_escape for re_escape in self.config.excluded_keywords])
            mask = ~selected_df["title"].str.contains(ex_pattern, case=False, na=False)
            selected_df = selected_df[mask]

        # 3. Required keywords filter (if any specified)
        if self.config.required_keywords:
            req_pattern = "|".join(self.config.required_keywords)
            mask = selected_df["title"].str.contains(req_pattern, case=False, na=False) | \
                   selected_df["skills"].astype(str).str.contains(req_pattern, case=False, na=False)
            selected_df = selected_df[mask]

        # 4. Remote only filter
        if self.config.remote_only and "is_remote" in selected_df.columns:
            selected_df = selected_df[selected_df["is_remote"] == True]

        # 5. Min salary filter
        if self.config.min_salary_annual is not None and "min_amount" in selected_df.columns:
            # Keep either jobs matching salary threshold OR jobs where salary is undisclosed
            salary_mask = (selected_df["min_amount"] >= self.config.min_salary_annual) | (selected_df["min_amount"].isna())
            selected_df = selected_df[salary_mask]

        # 6. Apply limit
        run_limit = limit or self.config.limit_per_run
        if run_limit and len(selected_df) > run_limit:
            selected_df = selected_df.head(run_limit)

        selected_df = selected_df.reset_index(drop=True)
        logger.info(f"🎯 Selected {len(selected_df)} target jobs ready for publication/posting.")
        return selected_df
