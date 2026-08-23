import os
import subprocess
import tempfile
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from src.config.settings import POSTS_DIR
from src.formatters.caption_generator import CaptionGenerator
from src.utils.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = BASE_DIR / "template"
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

class CardRenderer:
    """Renders 1080x1080 Instagram carousel images from HTML templates using headless Chrome."""

    def __init__(self, template_dir: Path = TEMPLATE_DIR, output_dir: Path = POSTS_DIR):
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(str(self.template_dir)))

    def render_html_to_png(self, html_content: str, output_png_path: Path) -> bool:
        """Saves rendered HTML to a temp file and executes headless Chrome screenshot."""
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", suffix=".html", dir=self.template_dir, delete=False, encoding="utf-8") as tf:
            tf.write(html_content)
            temp_html_path = tf.name

        try:
            cmd = [
                CHROME_PATH,
                "--headless=new",
                f"--screenshot={str(output_png_path)}",
                "--window-size=1080,1080",
                "--default-background-color=00000000",
                "--hide-scrollbars",
                "--disable-gpu",
                "--no-sandbox",
                "--force-device-scale-factor=1",
                f"file://{temp_html_path}"
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
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

    def render_carousel(
        self,
        top_jobs: List[Dict[str, Any]],
        category_meta: Optional[Dict[str, Any]] = None,
        batch_name: Optional[str] = None,
        location_label: str = "Bengaluru, IN",
        post_id: Optional[str] = None
    ) -> List[Path]:
        """
        Renders complete 12-slide Instagram carousel for a single category:
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

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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

        rendered_images: List[Path] = []
        logger.info(f"🎨 Rendering {total_slides} Carousel cards (1080x1080) for '{meta['label']}' [{meta['color'].upper()} theme] into: tmp/posts/{target_dir.name}/")

        # 1. Slide 0: Category-Specific Thumbnail / Cover (Matching Theme Frame)
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
        if self.render_html_to_png(thumb_html, thumb_png):
            rendered_images.append(thumb_png)
            logger.info(f"  🖼 [00/{total_slides-1}] Thumbnail generated: {thumb_png.name} (Theme: {meta['color'].upper()})")

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
            if self.render_html_to_png(card_html, job_png):
                rendered_images.append(job_png)
                logger.info(f"  🖼 [{idx:02d}/{total_slides-1}] Job card generated: {job_png.name} (Theme: {meta['color'].upper()})")

        # 3. Slide Last: End Note
        endnote_template = self.jinja_env.get_template("end-note.html")
        endnote_html = endnote_template.render(
            bg_frame=meta["frame"],
            total_slides=total_slides,
            current_slide=total_slides - 1
        )
        endnote_png = target_dir / f"{total_slides-1:02d}_end_note.png"
        if self.render_html_to_png(endnote_html, endnote_png):
            rendered_images.append(endnote_png)
            logger.info(f"  🖼 [{total_slides-1:02d}/{total_slides-1}] End note generated: {endnote_png.name}")

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

        logger.info(f"✨ Category Carousel complete! Saved in tmp/posts/{target_dir.name}/")
        return rendered_images
