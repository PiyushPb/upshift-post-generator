import csv
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

from src.config.settings import ScraperConfig, TelegramConfig, DATA_DIR, POSTS_DIR, TMP_DIR
from src.scrapers.job_scraper import JobScraper
from src.cleaners.job_cleaner import JobCleaner
from src.selectors.ml_ranker import MLJobSelector
from src.generators.card_renderer import CardRenderer
from src.formatters.caption_generator import CaptionGenerator
from src.publishers.telegram_publisher import TelegramPublisher
from src.utils.firebase_client import FirebaseClient
from src.utils.counter import PostCounter
from src.utils.logger import logger

class JobPipeline:
    """
    End-to-end automated pipeline:
    1. Scrapes raw jobs
    2. Cleans and deduplicates
    3. ML Selects Top 10 purest & richest jobs
    4. Obtains sequential Post ID (e.g. UP-0001)
    5. Renders 1080x1080 Carousel images + caption.txt + share_links.txt
    6. Saves batch & job records to Firebase Firestore with clean sequential IDs
    7. Dispatches full Instagram Kit (Images + Caption + Links) to Telegram personal chat
    8. (Optional) Auto-posts Thumbnail + Links to Telegram Group/Channel
    9. (Optional) Clears temp files for GitHub Actions disk optimization
    """

    def __init__(
        self,
        scraper_config: Optional[ScraperConfig] = None,
        telegram_config: Optional[TelegramConfig] = None
    ):
        self.scraper = JobScraper(scraper_config)
        self.cleaner = JobCleaner()
        self.ml_selector = MLJobSelector()
        self.renderer = CardRenderer()
        self.publisher = TelegramPublisher(telegram_config)
        self.firebase = FirebaseClient()

    def run(
        self,
        search_terms: Optional[List[str]] = None,
        category: Optional[str] = None,
        location: str = "Bengaluru",
        results_per_site: int = 15,
        render_cards: bool = True,
        top_n: int = 10,
        publish_to_telegram: bool = True,
        telegram_channel_id: Optional[str] = None,
        save_to_firebase: bool = True,
        cleanup_after: bool = False,
        export_csv_path: Optional[Path] = None,
        export_json_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """Executes full pipeline."""
        cat_desc = category.upper() if category else "AUTO-DETECT"
        logger.info(f"🚀 Starting Upshift Pipeline | Category: [{cat_desc}] | Location: '{location}'")

        # 1. Scrape raw candidate jobs
        raw_df = self.scraper.scrape(
            search_terms=search_terms,
            location=location,
            results_per_site=results_per_site
        )

        if raw_df.empty:
            logger.warning("No raw jobs retrieved.")
            return []

        # 2. Clean & Deduplicate
        cleaned_df = self.cleaner.clean(raw_df)

        # 3. Export all cleaned jobs to tmp/data/
        csv_file = export_csv_path or (DATA_DIR / "jobs_india.csv")
        json_file = export_json_path or (DATA_DIR / "jobs_india.json")
        cleaned_df.to_csv(csv_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
        cleaned_df.to_json(json_file, orient="records", indent=2, force_ascii=False)
        logger.info(f"💾 Stored {len(cleaned_df)} cleaned jobs to tmp/data/{csv_file.name} and {json_file.name}")

        # 4. ML Selection for pure single category
        logger.info(f"🧠 Running ML Ranker to select top {top_n} pure-category jobs...")
        top_jobs, cat_meta = self.ml_selector.select_top_jobs(cleaned_df, category=category, top_n=top_n)

        if not top_jobs:
            logger.warning("No jobs qualified for selection.")
            return []

        # Sequential Post ID: get active ID without incrementing
        post_id = PostCounter.get_current_id()

        # 5. Render Carousel, caption.txt & share_links.txt into tmp/posts/
        carousel_folder = None
        if render_cards:
            self.renderer.render_carousel(
                top_jobs,
                category_meta=cat_meta,
                location_label=f"{location}, IN",
                post_id=post_id
            )
            carousel_folder = getattr(self.renderer, "last_batch_dir", None)

        ig_caption = CaptionGenerator.generate_instagram_caption(
            top_jobs=top_jobs,
            category_meta=cat_meta,
            location_str=f"{location}, IN",
            post_id=post_id
        )
        share_text = CaptionGenerator.generate_share_links_list(
            top_jobs=top_jobs,
            category_meta=cat_meta,
            location_str=f"{location}, IN",
            post_id=post_id
        )

        # 6. Save to Firebase Firestore Backend
        if save_to_firebase:
            batch_id = self.firebase.generate_batch_id(post_id=post_id, category=cat_meta.get("label", "engineering"))
            self.firebase.save_batch_post(
                batch_id=batch_id,
                category=cat_meta.get("label", "Engineering"),
                location=f"{location}, India",
                top_jobs=top_jobs,
                post_id=post_id
            )

        # 7. Publish to Telegram
        if publish_to_telegram and carousel_folder:
            # Send full Instagram Post Kit to Personal Chat
            self.publisher.publish_personal_kit(
                carousel_folder=carousel_folder,
                caption_text=ig_caption,
                share_links_text=share_text
            )

            # Auto-post Thumbnail + Links to Group/Channel if specified
            if telegram_channel_id:
                thumb_img = carousel_folder / "00_thumbnail.png"
                self.publisher.publish_to_group_or_channel(
                    thumbnail_path=thumb_img,
                    share_links_text=share_text,
                    channel_id=telegram_channel_id
                )

        # 8. Post succeeded: Commit incremented ID to Firebase Firestore
        PostCounter.increment_and_commit(category)

        # 9. Clean up temp data if requested
        if cleanup_after:
            logger.info("🧹 Cleaning up temporary workspace files (tmp/)...")
            try:
                shutil.rmtree(TMP_DIR, ignore_errors=True)
                TMP_DIR.mkdir(parents=True, exist_ok=True)
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                POSTS_DIR.mkdir(parents=True, exist_ok=True)
                logger.info("✨ Temp cleanup complete.")
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")

        return top_jobs
