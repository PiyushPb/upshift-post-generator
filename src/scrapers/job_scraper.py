import concurrent.futures
from typing import List, Optional, Dict, Any
import pandas as pd
from jobspy import scrape_jobs
from src.config.settings import ScraperConfig
from src.utils.logger import logger

class JobScraper:
    """Scrapes jobs from India-supported platforms using python-jobspy."""

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()

    def scrape_site(self, site: str, term: str, location: str, results_wanted: int) -> pd.DataFrame:
        """Scrapes a single site with error isolation."""
        logger.info(f"🔎 Scraping [{site.upper()}] | Query: '{term}' in '{location}'")

        params: Dict[str, Any] = {
            "site_name": [site],
            "search_term": term,
            "location": location,
            "results_wanted": results_wanted,
            "verbose": self.config.verbose,
        }

        # India-specific configurations
        if site in ["indeed", "glassdoor"]:
            params["country_indeed"] = "India"
        elif site == "google":
            params["google_search_term"] = f"{term} jobs in {location}"

        if self.config.hours_old:
            params["hours_old"] = self.config.hours_old

        try:
            df = scrape_jobs(**params)
            if df is not None and not df.empty:
                logger.info(f"✅ [{site.upper()}] Found {len(df)} jobs for '{term}'")
                if self.config.drop_description and "description" in df.columns:
                    df = df.drop(columns=["description"])
                return df
            else:
                logger.warning(f"⚠️ [{site.upper()}] No jobs found for '{term}'")
        except Exception as e:
            logger.error(f"❌ [{site.upper()}] Error scraping '{term}': {e}")

        return pd.DataFrame()

    def scrape(
        self,
        search_terms: Optional[List[str]] = None,
        sites: Optional[List[str]] = None,
        location: Optional[str] = None,
        results_per_site: Optional[int] = None
    ) -> pd.DataFrame:
        """Scrapes across all sites and search terms."""
        terms = search_terms or self.config.search_terms
        target_sites = sites or self.config.site_names
        loc = location or self.config.location
        wanted = results_per_site or self.config.results_wanted

        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []
            for term in terms:
                for site in target_sites:
                    futures.append(executor.submit(self.scrape_site, site, term, loc, wanted))

            for future in concurrent.futures.as_completed(futures):
                df = future.result()
                if not df.empty:
                    all_results.append(df)

        if not all_results:
            return pd.DataFrame()

        combined = pd.concat(all_results, ignore_index=True)
        if self.config.drop_description and "description" in combined.columns:
            combined = combined.drop(columns=["description"])

        logger.info(f"📊 Scraped total {len(combined)} raw jobs across all platforms.")
        return combined
