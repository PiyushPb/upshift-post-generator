import json
from pathlib import Path
from typing import Optional
from src.utils.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
COUNTER_FILE = BASE_DIR / "src" / "config" / "post_counter.json"

class PostCounter:
    """
    Manages sequential, strictly incrementing Post IDs starting from UP-0001.
    Persists locally and syncs with Firebase Firestore to prevent duplicated IDs across cloud runs.
    """

    @classmethod
    def _read_data(cls) -> dict:
        local_data = {"global_counter": 1, "categories": {"engineering": 1, "data": 1, "devops": 1, "product": 1}}
        if COUNTER_FILE.exists():
            try:
                with open(COUNTER_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict) and "global_counter" in loaded:
                        local_data = loaded
            except Exception as e:
                logger.debug(f"Could not read local post_counter.json: {e}")

        # Try to sync from Firebase Firestore
        try:
            from src.utils.firebase_client import FirebaseClient
            fb = FirebaseClient()
            remote_doc = fb.get_document("counters", "post_counter")
            if remote_doc and isinstance(remote_doc, dict):
                remote_count = int(remote_doc.get("global_counter", 0))
                local_count = int(local_data.get("global_counter", 1))
                if remote_count > local_count:
                    logger.info(f"🔄 Synced Post ID counter from Firebase Firestore (UP-{remote_count:04d})")
                    local_data["global_counter"] = remote_count
                    if "categories" in remote_doc and isinstance(remote_doc["categories"], dict):
                        local_data["categories"] = remote_doc["categories"]
                    cls._write_local_file(local_data)
        except Exception as e:
            logger.debug(f"Firestore counter sync skipped: {e}")

        return local_data

    @classmethod
    def _write_local_file(cls, data: dict):
        COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def _write_data(cls, data: dict):
        cls._write_local_file(data)
        # Try to persist to Firebase Firestore
        try:
            from src.utils.firebase_client import FirebaseClient
            fb = FirebaseClient()
            fb.save_document("counters", "post_counter", data)
        except Exception as e:
            logger.debug(f"Firestore counter write skipped: {e}")

    @classmethod
    def peek_next_id(cls, category: Optional[str] = None) -> str:
        """Returns the upcoming formatted ID (e.g. UP-0001) without incrementing."""
        data = cls._read_data()
        count = data.get("global_counter", 1)
        return f"UP-{count:04d}"

    @classmethod
    def get_and_increment(cls, category: Optional[str] = None) -> str:
        """Returns the next sequential Post ID (e.g. UP-0001) and increments the counter."""
        data = cls._read_data()
        current_count = int(data.get("global_counter", 1))
        formatted_id = f"UP-{current_count:04d}"

        # Increment
        data["global_counter"] = current_count + 1
        if category:
            cat_key = category.lower()
            data.setdefault("categories", {})
            data["categories"][cat_key] = data["categories"].get(cat_key, 1) + 1

        cls._write_data(data)
        logger.info(f"🔢 Assigned Sequential Post ID: {formatted_id} (Next will be: UP-{(current_count+1):04d})")
        return formatted_id

