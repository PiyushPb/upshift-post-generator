import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
from src.config.settings import TelegramConfig
from src.utils.logger import logger

class TelegramPublisher:
    """
    Publishes formatted job alerts, media groups, and curated batches to Telegram.
    Supports:
    1. Personal Chat: Sends all 12 carousel images + Instagram caption + share links.
    2. Group/Channel: Sends Cover Thumbnail + Numbered direct apply links list.
    """

    def __init__(self, config: Optional[TelegramConfig] = None):
        self.config = config or TelegramConfig()
        self.base_url = f"https://api.telegram.org/bot{self.config.bot_token}"

    def send_message(self, text: str, chat_id: Optional[str] = None, parse_mode: str = "HTML") -> bool:
        """Sends a text message to the specified Telegram chat/channel."""
        target_chat = chat_id or (self.config.chat_ids[0] if self.config.chat_ids else "")
        if not self.config.bot_token or not target_chat:
            logger.warning("Telegram Bot Token or Chat ID not configured.")
            return False

        if self.config.dry_run:
            logger.info("📢 [DRY RUN] Telegram message preview:\n" + "-"*40 + "\n" + text + "\n" + "-"*40)
            return True

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            response = requests.post(url, json=payload, timeout=15)
            data = response.json()
            if response.status_code == 200 and data.get("ok"):
                logger.info(f"✅ Sent Telegram message successfully to [{target_chat}].")
                time.sleep(1.2)
                return True
            else:
                logger.error(f"❌ Telegram API Error ({target_chat}): {data.get('description', response.text)}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message to [{target_chat}]: {e}")
            return False

    def send_photo(self, photo_path: Path, chat_id: Optional[str] = None, caption: Optional[str] = None) -> bool:
        """Sends a single photo with optional caption."""
        target_chat = chat_id or (self.config.chat_ids[0] if self.config.chat_ids else "")
        if not self.config.bot_token or not target_chat:
            return False

        if self.config.dry_run:
            logger.info(f"📢 [DRY RUN] Would send photo: {photo_path.name}")
            return True

        url = f"{self.base_url}/sendPhoto"
        data = {
            "chat_id": target_chat,
            "caption": caption or "",
            "parse_mode": "HTML"
        }

        try:
            with open(photo_path, "rb") as photo_file:
                files = {"photo": photo_file}
                response = requests.post(url, data=data, files=files, timeout=25)
                res_json = response.json()
                if response.status_code == 200 and res_json.get("ok"):
                    logger.info(f"✅ Sent photo '{photo_path.name}' to Telegram [{target_chat}].")
                    time.sleep(1.2)
                    return True
                else:
                    logger.error(f"❌ Failed to send photo to [{target_chat}]: {res_json.get('description')}")
                    return False
        except Exception as e:
            logger.error(f"❌ Photo upload error to [{target_chat}]: {e}")
            return False

    def send_media_group(self, image_paths: List[Path], chat_id: Optional[str] = None, caption: Optional[str] = None) -> bool:
        """Sends up to 10 photos as a single Telegram media album."""
        target_chat = chat_id or (self.config.chat_ids[0] if self.config.chat_ids else "")
        if not self.config.bot_token or not target_chat or not image_paths:
            return False


        if self.config.dry_run:
            logger.info(f"📢 [DRY RUN] Would send media group of {len(image_paths)} images.")
            return True

        url = f"{self.base_url}/sendMediaGroup"
        media = []
        files = {}

        # Telegram supports max 10 photos per media group
        batch_slice = image_paths[:10]
        for idx, img_path in enumerate(batch_slice):
            field_name = f"photo_{idx}"
            files[field_name] = open(img_path, "rb")
            media_item = {
                "type": "photo",
                "media": f"attach://{field_name}",
            }
            if idx == 0 and caption:
                media_item["caption"] = caption
                media_item["parse_mode"] = "HTML"
            media.append(media_item)

        try:
            data = {
                "chat_id": target_chat,
                "media": json_dumps(media)
            }
            response = requests.post(url, data=data, files=files, timeout=40)
            res_json = response.json()
            # Close file handles
            for f in files.values():
                f.close()

            if response.status_code == 200 and res_json.get("ok"):
                logger.info(f"✅ Sent album of {len(batch_slice)} images to Telegram.")
                time.sleep(1.5)
                return True
            else:
                logger.error(f"❌ MediaGroup upload failed: {res_json.get('description')}")
                return False
        except Exception as e:
            for f in files.values():
                try:
                    f.close()
                except Exception:
                    pass
            logger.error(f"❌ MediaGroup error: {e}")
            return False

    def publish_personal_kit(
        self,
        carousel_folder: Path,
        caption_text: str,
        share_links_text: str,
        chat_id: Optional[str] = None
    ) -> bool:
        """
        Sends complete Instagram asset kit to personal chat(s):
        1. All 12 carousel cards sent sequentially / as albums for 1-click mobile download.
        2. Clean copy-paste Instagram caption (caption.txt).
        3. Formatted WhatsApp & Telegram share links list.
        """
        target_chats = [chat_id] if chat_id else self.config.chat_ids
        if not target_chats:
            logger.warning("No Telegram Chat IDs configured.")
            return False

        logger.info(f"📲 Dispatching complete Instagram Post Kit to Telegram chat(s) {target_chats}...")

        all_success = True
        for target_chat in target_chats:
            logger.info(f"📤 Sending kit to user/chat [{target_chat}]...")
            # 1. Gather all rendered PNGs in proper order
            png_files = sorted(list(carousel_folder.glob("*.png")))
            if png_files:
                logger.info(f"📸 Sending {len(png_files)} carousel slides to [{target_chat}]...")
                # Send in 2 albums (e.g. 0-9 and 10-11) or sequential photos
                self.send_media_group(png_files[:10], chat_id=target_chat, caption="📸 <b>Instagram Carousel Slides (1-10)</b>")
                if len(png_files) > 10:
                    time.sleep(1.5)
                    self.send_media_group(png_files[10:], chat_id=target_chat, caption="📸 <b>Instagram Carousel Slides (11-12)</b>")

            # 2. Send Instagram Caption
            time.sleep(1.2)
            caption_msg = f"📝 <b>INSTAGRAM CAPTION (COPY & PASTE):</b>\n\n<code>{caption_text}</code>"
            self.send_message(caption_msg, chat_id=target_chat, parse_mode="HTML")

            # 3. Send WhatsApp & Telegram Direct Apply Links List
            time.sleep(1.2)
            import re
            html_links = ""
            for line in share_links_text.splitlines():
                cleaned_line = re.sub(r"\*(.*?)\*", r"<b>\1</b>", line)
                html_links += cleaned_line + "\n"

            links_msg = f"🔗 <b>WHATSAPP & TELEGRAM SHARE LIST:</b>\n\n{html_links.strip()}"
            self.send_message(links_msg, chat_id=target_chat, parse_mode="HTML")
            time.sleep(1.5)

        return all_success

    def publish_to_group_or_channel(
        self,
        thumbnail_path: Path,
        share_links_text: str,
        channel_id: str
    ) -> bool:
        """
        Auto-posts only Cover Thumbnail and formatted direct links to a public Group or Channel.
        """
        logger.info(f"📢 Auto-posting Thumbnail & Links to Group/Channel [{channel_id}]...")
        
        # 1. Send Cover Thumbnail Photo
        if thumbnail_path and thumbnail_path.exists():
            self.send_photo(thumbnail_path, chat_id=channel_id, caption="🚀 <b>New Curated Job Batch — Upshift</b>")
            time.sleep(1.2)

        # 2. Send Clickable Links List
        import re
        html_links = ""
        for line in share_links_text.splitlines():
            cleaned_line = re.sub(r"\*(.*?)\*", r"<b>\1</b>", line)
            html_links += cleaned_line + "\n"

        success = self.send_message(html_links.strip(), chat_id=channel_id, parse_mode="HTML")
        return success


def json_dumps(obj):
    import json
    return json.dumps(obj)
