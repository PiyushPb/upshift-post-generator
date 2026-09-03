import os
import shutil
import subprocess
import tempfile
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import concurrent.futures
from jinja2 import Environment, FileSystemLoader
from src.config.settings import POSTS_DIR
from src.formatters.caption_generator import CaptionGenerator
from src.utils.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = BASE_DIR / "template"

def get_chrome_executable() -> str:
    """Finds Google Chrome / Chromium executable on macOS, Linux, or custom path."""
    env_path = os.environ.get("CHROME_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    candidates = [
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium-browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c

    # Fallbacks based on environment
    which_chrome = shutil.which("google-chrome")
    if which_chrome:
        return which_chrome
    if Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome").exists():
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return "google-chrome"

CHROME_PATH = get_chrome_executable()

class CardRenderer:
    """Renders 1080x1080 Instagram carousel images from HTML templates using headless Chrome."""

    def __init__(self, template_dir: Path = TEMPLATE_DIR, output_dir: Path = POSTS_DIR, max_workers: int = 4):
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        self.chrome_path = get_chrome_executable()
        self.max_workers = max_workers
        self.last_batch_dir: Optional[Path] = None

    def render_html_to_png(self, html_content: str, output_png_path: Path) -> bool:
        """Saves rendered HTML to a temp file and executes optimized headless Chrome screenshot."""
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", suffix=".html", dir=self.template_dir, delete=False, encoding="utf-8") as tf:
            tf.write(html_content)
            temp_html_path = tf.name

        try:
            cmd = [
                self.chrome_path,
                "--headless=new",
                f"--screenshot={str(output_png_path)}",
                "--window-size=1080,1080",
                "--default-background-color=00000000",
                "--hide-scrollbars",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-default-apps",
                "--mute-audio",
                "--no-first-run",
                "--force-device-scale-factor=1",
                f"file://{temp_html_path}"
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
            if output_png_path.exists() and output_png_path.stat().st_size > 1000:
                return True
            else:
                logger.error(f"Failed to generate {output_png_path.name}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Screenshot execution failed for {output_png_path.name}: {e}")
            return False
        finally:
            if os.path.exists(temp_html_path):
                try:
                    os.remove(temp_html_path)
                except Exception:
                    pass

    def _render_task(self, item: Tuple[int, str, str, Path]) -> Optional[Tuple[int, Path]]:
        """Worker task for parallel rendering."""
        idx, label, html_content, output_path = item
        success = self.render_html_to_png(html_content, output_path)
        if success:
            logger.info(f"  🖼 [{idx:02d}] Slide generated: {output_path.name} ({label})")
            return (idx, output_path)
        return None

    def render_carousel(
        self,
        top_jobs: List[Dict[str, Any]],
        category_meta: Optional[Dict[str, Any]] = None,
        batch_name: Optional[str] = None,
        location_label: str = "Bengaluru, IN",
        post_id: Optional[str] = None
    ) -> List[Path]:
        """
        Renders complete 12-slide Instagram carousel concurrently:
        - 00_thumbnail.png (Category-specific title and matching frame)
        - 01_job_... to 10_job_... (10 jobs all in the same category)
        - 11_end_note.png (Disclaimer)
        - caption.txt (Instagram caption without links)
        - share_links.txt (WhatsApp & Telegram formatted list with links)
        """
        if not top_jobs:
            logger.warning("No jobs provided to render.")
            return []

        meta = category_meta or {
            "color": top_jobs[0].get("theme_color", "blue"),
            "label": top_jobs[0].get("category_label", "Engineering"),
            "frame": top_jobs[0].get("theme_frame", "./assets/frame-blue.png"),
            "thumb_title_l1": "Engineering",
            "thumb_title_l2": "Opportunities",
            "thumb_subtitle": "Curated roles with direct application links."
        }

        cat_tag = meta["color"]
        current_post_id = post_id or top_jobs[0].get("post_id", "UP-0001")
        folder_name = batch_name or f"carousel_{cat_tag}_{current_post_id.lower().replace('-', '_')}"
        target_dir = self.output_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        self.last_batch_dir = target_dir

        total_slides = len(top_jobs) + 2
        now = datetime.datetime.now()
        date_str = now.strftime("%d %B %Y")
        post_id = current_post_id

        logger.info(
            f"🎨 Rendering {total_slides} Carousel cards (1080x1080) in parallel (workers={self.max_workers}) "
            f"for '{meta['label']}' [{meta['color'].upper()} theme] into: tmp/posts/{target_dir.name}/"
        )

        render_queue: List[Tuple[int, str, str, Path]] = []

        # 1. Slide 0: Category-Specific Thumbnail / Cover
        thumb_template = self.jinja_env.get_template("thumbnail.html")
        thumb_html = thumb_template.render(
            bg_frame=meta["frame"],
            date_str=date_str,
            location_str=location_label,
            ref_code=post_id,
            heading_line1=meta.get("thumb_title_l1", "Tech"),
            heading_line2=meta.get("thumb_title_l2", "Opportunities"),
            sub_heading=meta.get("thumb_subtitle", "Curated opportunities with direct application links."),
            category_text=meta["label"]
        )
        thumb_png = target_dir / "00_thumbnail.png"
        render_queue.append((0, f"Cover ({meta['color'].upper()})", thumb_html, thumb_png))

        # 2. Slides 1 to N: Job Post Cards
        job_template = self.jinja_env.get_template("job-post.html")
        for idx, job in enumerate(top_jobs, start=1):
            source_tag = f"{meta['label']} job via {job.get('clean_site', 'Indeed')}"
            card_html = job_template.render(
                bg_frame=meta["frame"],
                source_tag=source_tag,
                company_name=job.get("clean_company", "Top Company"),
                title_line1=job.get("title_line1", "Software Engineer"),
                title_line2=job.get("title_line2", ""),
                skills=job.get("skills_badges", ["Tech", "Engineering"]),
                location=job.get("clean_location", "India"),
                salary=job.get("salary_str", "₹ Not Disclosed"),
                total_slides=total_slides,
                current_slide=idx
            )
            safe_comp = "".join(c for c in job.get("clean_company", "comp") if c.isalnum() or c in "_-")[:15]
            job_png = target_dir / f"{idx:02d}_job_{safe_comp}.png"
            render_queue.append((idx, f"Job {idx}", card_html, job_png))

        # 3. Slide Last: End Note
        endnote_template = self.jinja_env.get_template("end-note.html")
        endnote_html = endnote_template.render(
            bg_frame=meta["frame"],
            total_slides=total_slides,
            current_slide=total_slides - 1
        )
        endnote_png = target_dir / f"{total_slides-1:02d}_end_note.png"
        render_queue.append((total_slides - 1, "End Note", endnote_html, endnote_png))

        # Parallel Execution
        rendered_images: List[Path] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {executor.submit(self._render_task, task): task for task in render_queue}
            results = []
            for future in concurrent.futures.as_completed(future_to_task):
                res = future.result()
                if res:
                    results.append(res)

        # Sort by slide index
        results.sort(key=lambda x: x[0])
        rendered_images = [path for _, path in results]

        # 4. Generate Instagram Caption (caption.txt)
        ig_caption = CaptionGenerator.generate_instagram_caption(
            top_jobs=top_jobs,
            category_meta=meta,
            location_str=location_label,
            post_id=post_id
        )
        caption_file = target_dir / "caption.txt"
        caption_file.write_text(ig_caption, encoding="utf-8")
        logger.info(f"  📝 [Instagram Caption] Created: {caption_file.name}")

        # 5. Generate WhatsApp / Telegram Links List (share_links.txt)
        share_links = CaptionGenerator.generate_share_links_list(
            top_jobs=top_jobs,
            category_meta=meta,
            location_str=location_label,
            post_id=post_id
        )
        links_file = target_dir / "share_links.txt"
        links_file.write_text(share_links, encoding="utf-8")
        logger.info(f"  🔗 [WhatsApp/Telegram Links] Created: {links_file.name}")

        logger.info(f"✨ Category Carousel complete! {len(rendered_images)} cards saved in tmp/posts/{target_dir.name}/")
        return rendered_images
