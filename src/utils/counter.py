import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from src.utils.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
COUNTER_FILE = BASE_DIR / "src" / "config" / "post_counter.json"

DEFAULT_COUNTER_DATA = {
    "global_counter": 1,
    "categories": {
        "engineering": 1,
        "data": 1,
        "devops": 1,
        "product": 1
    }
}

class PostCounter:
    """
    Manages sequential, strictly incrementing Post IDs (e.g., UP-0001).
    Firebase Firestore is the primary source of truth.
    The counter is read before post creation and incremented strictly upon
    successful post rendering, Firebase storage, and Telegram publishing.
    """

    @classmethod
    def _read_data(cls) -> Dict[str, Any]:
        """
        Reads counter data primarily from Firebase Firestore.
        Falls back to local post_counter.json or defaults if Firebase is unreachable.
        """
        # 1. Primary: Try reading from Firebase Firestore
        try:
            from src.utils.firebase_client import FirebaseClient
            fb = FirebaseClient()
            remote_doc = fb.get_document("counters", "post_counter")
            if remote_doc and isinstance(remote_doc, dict) and "global_counter" in remote_doc:
                remote_count = int(remote_doc.get("global_counter", 1))
                data = {
                    "global_counter": remote_count,
                    "categories": remote_doc.get("categories", DEFAULT_COUNTER_DATA["categories"])
                }
                logger.info(f"🔥 Fetched canonical Post ID counter from Firebase Firestore: UP-{remote_count:04d}")
                cls._write_local_file(data)
                return data
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch counter from Firebase Firestore: {e}")

        # 2. Fallback: Read from local post_counter.json
        if COUNTER_FILE.exists():
            try:
                with open(COUNTER_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict) and "global_counter" in loaded:
                        logger.info(f"📂 Read Post ID counter from local fallback: UP-{int(loaded['global_counter']):04d}")
                        return loaded
            except Exception as e:
                logger.debug(f"Could not read local post_counter.json: {e}")

        # 3. Default initial counter
        return dict(DEFAULT_COUNTER_DATA)

    @classmethod
    def _write_local_file(cls, data: dict):
        """Caches counter data locally for offline fallback."""
        try:
            COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(COUNTER_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not write local cache post_counter.json: {e}")

    @classmethod
    def _write_data(cls, data: dict) -> bool:
        """
        Commits counter data directly to Firebase Firestore (and caches locally).
        """
        cls._write_local_file(data)
        success = False
        try:
            from src.utils.firebase_client import FirebaseClient
            fb = FirebaseClient()
            # Attach metadata
            payload = dict(data)
            payload["last_updated_at"] = datetime.datetime.now().isoformat()
            payload["last_post_id"] = f"UP-{int(data.get('global_counter', 1)) - 1:04d}"
            success = fb.save_document("counters", "post_counter", payload)
            if success:
                logger.info(f"✅ Committed updated Post ID counter to Firebase Firestore: UP-{data['global_counter']:04d}")
            else:
                logger.warning("⚠️ Failed to commit counter update to Firebase Firestore.")
        except Exception as e:
            logger.error(f"❌ Firestore counter commit failed: {e}")

        return success

    @classmethod
    def get_current_id(cls) -> str:
        """
        Returns the active Post ID (e.g. UP-0016) without incrementing.
        Used to prepare cards, captions, and batch data prior to publish.
        """
        data = cls._read_data()
        count = int(data.get("global_counter", 1))
        return f"UP-{count:04d}"

    @classmethod
    def peek_next_id(cls, category: Optional[str] = None) -> str:
        """Alias for get_current_id()."""
        return cls.get_current_id()

    @classmethod
    def increment_and_commit(cls, category: Optional[str] = None) -> str:
        """
        Strictly called AFTER successful post creation and publishing.
        Increments the counter and commits the new state to Firebase Firestore.
        Returns the new next ID.
        """
        data = cls._read_data()
        current_count = int(data.get("global_counter", 1))
        used_id = f"UP-{current_count:04d}"

        # Increment global and category counters
        next_count = current_count + 1
        data["global_counter"] = next_count

        if category:
            cat_key = category.lower()
            data.setdefault("categories", {})
            data["categories"][cat_key] = data["categories"].get(cat_key, 1) + 1

        cls._write_data(data)
        logger.info(f"🔢 Successfully incremented Post ID counter after post delivery: {used_id} -> UP-{next_count:04d}")
        return f"UP-{next_count:04d}"

    @classmethod
    def get_and_increment(cls, category: Optional[str] = None) -> str:
        """
        Legacy helper that returns current ID and immediately increments.
        Prefer get_current_id() followed by increment_and_commit().
        """
        current_id = cls.get_current_id()
        cls.increment_and_commit(category)
        return current_id
