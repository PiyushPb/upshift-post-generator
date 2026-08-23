import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pytz
from src.utils.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TIMETABLE_FILE = BASE_DIR / "src" / "config" / "timetable.json"

class TimetableScheduler:
    """Resolves correct job category, search terms, and location based on day & IST time slot."""

    @classmethod
    def load_timetable(cls) -> Dict[str, Any]:
        if not TIMETABLE_FILE.exists():
            raise FileNotFoundError(f"Timetable file not found at: {TIMETABLE_FILE}")
        with open(TIMETABLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def get_current_slot_config(
        cls,
        day_override: Optional[str] = None,
        slot_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determines the correct scheduled configuration for the current execution:
        - Timezone: Asia/Kolkata (IST)
        - Slot 1: ~13:30 (1:30 PM IST)
        - Slot 2: ~18:00 (6:00 PM IST)
        """
        timetable = cls.load_timetable()
        ist_tz = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.datetime.now(ist_tz)

        # 1. Day of Week
        day_key = (day_override or now_ist.strftime("%A")).lower()
        if day_key not in timetable.get("schedule", {}):
            day_key = "monday"

        # 2. Slot Selection (Slot 1 = 1:30 PM IST / before 16:00, Slot 2 = 6:00 PM IST / after 16:00)
        if slot_override:
            slot_key = f"slot_{slot_override.replace('slot_', '')}"
        else:
            hour_ist = now_ist.hour
            # If current IST hour is < 16 (4 PM), pick slot_1 (1:30 PM), otherwise slot_2 (6:00 PM)
            slot_key = "slot_1" if hour_ist < 16 else "slot_2"

        day_schedule = timetable["schedule"].get(day_key, {})
        slot_config = day_schedule.get(slot_key, day_schedule.get("slot_1", {}))

        slot_info = timetable.get("slots", {}).get(slot_key, {})
        time_desc = slot_info.get("time_ist", "13:30" if slot_key == "slot_1" else "18:00")

        logger.info(
            f"📅 [TIMETABLE] Day: {day_key.capitalize()} | Slot: {slot_key.upper()} ({time_desc} IST) | "
            f"Category: {slot_config.get('category').upper()} | Focus: '{slot_config.get('label')}' | "
            f"Location: '{slot_config.get('location')}'"
        )

        return {
            "day": day_key,
            "slot": slot_key,
            "time_ist": time_desc,
            "category": slot_config.get("category", "engineering"),
            "label": slot_config.get("label", "Software Engineering"),
            "location": slot_config.get("location", "Bengaluru"),
            "search_terms": slot_config.get("search_terms", ["Software Engineer"]),
            "top_n": slot_config.get("top_n", 10)
        }
