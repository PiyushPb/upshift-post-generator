import json
from pathlib import Path
from typing import Optional
from src.utils.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
COUNTER_FILE = BASE_DIR / "src" / "config" / "post_counter.json"

class PostCounter:
    """
    Manages sequential, strictly incrementing Post IDs starting from UP-0001.
    Persists locally and supports synchronization.
    """

    @classmethod
    def _read_data(cls) -> dict:
        if not COUNTER_FILE.exists():
            default_data = {"global_counter": 1, "categories": {"engineering": 1, "data": 1, "devops": 1, "product": 1}}
            cls._write_data(default_data)
            return default_data

        try:
            with open(COUNTER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            default_data = {"global_counter": 1, "categories": {}}
            cls._write_data(default_data)
            return default_data

    @classmethod
    def _write_data(cls, data: dict):
        COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

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
        current_count = data.get("global_counter", 1)
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
