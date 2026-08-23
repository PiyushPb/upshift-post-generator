import os
import argparse
import shutil
from pathlib import Path
import pandas as pd
from src.config.settings import ScraperConfig, TelegramConfig, DATA_DIR, TMP_DIR, POSTS_DIR
from src.pipeline.pipeline_runner import JobPipeline
from src.selectors.ml_ranker import MLJobSelector
from src.generators.card_renderer import CardRenderer
from src.formatters.caption_generator import CaptionGenerator
from src.publishers.telegram_publisher import TelegramPublisher
from src.utils.firebase_client import FirebaseClient
from src.utils.counter import PostCounter
from src.utils.scheduler import TimetableScheduler
from src.utils.logger import logger

def main():
    parser = argparse.ArgumentParser(description="Upshift Automated ML Job Pipeline (India)")
    parser.add_argument(
        "--auto-schedule",
        action="store_true",
        help="Auto-detect current day and IST time slot (1:30 PM or 6:00 PM) from timetable.json"
    )
    parser.add_argument(
        "--day",
        type=str,
        default=None,
        help="Force a specific day from timetable (e.g. monday, tuesday, wednesday...)"
    )
    parser.add_argument(
        "--slot",
        type=str,
        choices=["1", "2", "slot_1", "slot_2"],
        default=None,
        help="Force a specific slot (1 for 1:30 PM IST, 2 for 6:00 PM IST)"
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=["engineering", "data", "devops", "product"],
        default=None,
        help="Job category override: engineering (Blue), data (Pink), devops (Green), product (Yellow)"
    )
    parser.add_argument(
        "--search",
        nargs="+",
        default=None,
        help="Custom search terms (e.g. --search 'Data Analyst' 'Data Scientist')"
    )
    parser.add_argument(
        "--location",
        type=str,
        default=None,
        help="Target location in India (e.g. Bengaluru, Hyderabad, Pune, Mumbai)"
    )
    parser.add_argument(
        "--results",
        type=int,
        default=15,
        help="Results wanted per platform per search term (default: 15)"
    )
    parser.add_argument(
        "--sites",
        nargs="+",
        default=["indeed", "linkedin", "google", "glassdoor", "naukri"],
        help="Job platforms to scrape"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top richest jobs to rank and select within category (default: 10)"
    )
    parser.add_argument(
        "--channel",
        type=str,
        default=os.getenv("TELEGRAM_CHANNEL_ID", None),
        help="Optional Telegram Group or Channel ID (e.g. @upshift_jobs) to auto-post thumbnail + links"
    )
    parser.add_argument(
        "--no-publish",
        action="store_true",
        help="Disable sending alerts to Telegram"
    )
    parser.add_argument(
        "--no-firebase",
        action="store_true",
        help="Disable saving to Firebase Firestore"
    )
    parser.add_argument(
        "--clear-tmp",
        action="store_true",
        help="Clear all temporary files in tmp/ after run completes (ideal for GitHub Actions)"
    )
    parser.add_argument(
        "--from-file",
        type=str,
        default=None,
        help="Path to an existing JSON/CSV file in tmp/data to rank and render without re-scraping"
    )

    args = parser.parse_args()

    # Determine execution parameters (Auto-schedule timetable vs explicit flags)
    category = args.category
    search_terms = args.search
    location = args.location or "Bengaluru"
    top_n = args.top

    # If --auto-schedule or no explicit category and no file specified, use Timetable
    if args.auto_schedule or (category is None and args.from_file is None):
        slot_cfg = TimetableScheduler.get_current_slot_config(
            day_override=args.day,
            slot_override=args.slot
        )
        if not category:
            category = slot_cfg["category"]
        if not search_terms:
            search_terms = slot_cfg["search_terms"]
        if not args.location:
            location = slot_cfg["location"]
        if args.top == 10:
            top_n = slot_cfg.get("top_n", 10)
    else:
        if not search_terms:
            if category == "data":
                search_terms = ["Data Analyst", "Data Scientist", "Machine Learning Engineer"]
            elif category == "devops":
                search_terms = ["DevOps Engineer", "Cloud Engineer", "SRE"]
            elif category == "product":
                search_terms = ["Product Manager", "UI/UX Designer", "Product Designer"]
            else:
                search_terms = ["Software Engineer", "Backend Developer", "Frontend Developer"]

    # Fast-track mode: rank & render directly from saved data
    if args.from_file:
        file_path = Path(args.from_file)
        if not file_path.exists():
            alt_path = DATA_DIR / file_path.name
            if alt_path.exists():
                file_path = alt_path
            else:
                logger.error(f"File not found: {file_path}")
                return

        logger.info(f"📂 Loading existing dataset from: {file_path.name}")
        df = pd.read_json(file_path) if file_path.suffix == ".json" else pd.read_csv(file_path)
        
        ml_ranker = MLJobSelector()
        top_jobs, cat_meta = ml_ranker.select_top_jobs(df, category=category, top_n=top_n)
        
        post_id = PostCounter.get_and_increment(category)

        renderer = CardRenderer()
        renderer.render_carousel(
            top_jobs,
            category_meta=cat_meta,
            location_label=f"{location}, IN",
            post_id=post_id
        )
        carousel_folder = getattr(renderer, "last_batch_dir", None)

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

        # Firebase Save
        if not args.no_firebase and top_jobs:
            firebase = FirebaseClient()
            batch_id = firebase.generate_batch_id(post_id=post_id, category=cat_meta.get("label", "engineering"))
            firebase.save_batch_post(
                batch_id=batch_id,
                category=cat_meta.get("label", "Engineering"),
                location=f"{location}, India",
                top_jobs=top_jobs,
                post_id=post_id
            )

        # Telegram Send
        if not args.no_publish and top_jobs and carousel_folder:
            publisher = TelegramPublisher()
            publisher.publish_personal_kit(
                carousel_folder=carousel_folder,
                caption_text=ig_caption,
                share_links_text=share_text
            )
            if args.channel:
                thumb_img = carousel_folder / "00_thumbnail.png"
                publisher.publish_to_group_or_channel(
                    thumbnail_path=thumb_img,
                    share_links_text=share_text,
                    channel_id=args.channel
                )

        if args.clear_tmp:
            shutil.rmtree(TMP_DIR, ignore_errors=True)
            TMP_DIR.mkdir(parents=True, exist_ok=True)
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            POSTS_DIR.mkdir(parents=True, exist_ok=True)

        print_summary(top_jobs, cat_meta)
        return

    # Full End-to-End Execution
    scraper_config = ScraperConfig(
        site_names=args.sites,
        search_terms=search_terms,
        location=location,
        results_wanted=args.results,
        drop_description=True,
    )

    pipeline = JobPipeline(scraper_config=scraper_config)
    top_jobs = pipeline.run(
        search_terms=search_terms,
        category=category,
        location=location,
        results_per_site=args.results,
        render_cards=True,
        top_n=top_n,
        publish_to_telegram=not args.no_publish,
        telegram_channel_id=args.channel,
        save_to_firebase=not args.no_firebase,
        cleanup_after=args.clear_tmp
    )

    if top_jobs:
        cat_meta = pipeline.ml_selector.categories.get(category or "engineering")
        print_summary(top_jobs, cat_meta)

def print_summary(top_jobs, cat_meta=None):
    cat_label = cat_meta.get("label", "Tech") if cat_meta else "Tech"
    theme = cat_meta.get("color", "blue").upper() if cat_meta else "BLUE"

    print("\n" + "="*95)
    print(f"🏆 TOP {len(top_jobs)} ML-RANKED RICHEST {cat_label.upper()} JOBS (THEME: {theme}):")
    print("="*95)
    header = f"{'#':<3} | {'SCORE':<5} | {'COMPANY':<22} | {'TITLE':<36} | {'SALARY'}"
    print(header)
    print("-" * 95)
    for idx, j in enumerate(top_jobs, 1):
        print(f"{idx:<3} | {j.get('richness_score', 0):<5} | {j.get('clean_company', '')[:22]:<22} | {j.get('title', '')[:36]:<36} | {j.get('salary_str', '')}")
    print("="*95)
    print(f"🖼  1080x1080 UNIFORM CAROUSEL POSTS RENDERED [{theme} THEME]:")
    print(f"   • 00_thumbnail.png ({cat_label} Cover with {theme.lower()} frame)")
    print(f"   • 01 to {len(top_jobs):02d} Job Cards (100% {cat_label} roles with {theme.lower()} frame)")
    print(f"   • {len(top_jobs)+1:02d}_end_note.png (Disclaimer with matching frame)")
    print(f"   • caption.txt (Instagram-friendly caption without links)")
    print(f"   • share_links.txt (WhatsApp & Telegram share list with direct apply links)")
    print("All saved in: tmp/posts/")
    print("="*95 + "\n")

if __name__ == "__main__":
    main()
