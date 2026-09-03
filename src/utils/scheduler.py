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
        - Slot 1: ~13:00 (1:00 PM IST)
        - Slot 2: ~18:00 (6:00 PM IST)
        """
        timetable = cls.load_timetable()
        ist_tz = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.datetime.now(ist_tz)

        # 1. Day of Week
        day_key = (day_override or now_ist.strftime("%A")).lower()
        if day_key not in timetable.get("schedule", {}):
            day_key = "monday"

        # 2. Slot Selection (Slot 1 = 1:00 PM IST / before 15:00, Slot 2 = 6:00 PM IST / after 15:00)
        if slot_override:
            slot_key = f"slot_{slot_override.replace('slot_', '')}"
        else:
            hour_ist = now_ist.hour
            # If current IST hour is < 15 (3 PM), pick slot_1 (1:00 PM), otherwise slot_2 (6:00 PM)
            slot_key = "slot_1" if hour_ist < 15 else "slot_2"

        day_schedule = timetable["schedule"].get(day_key, {})
        slot_config = day_schedule.get(slot_key, day_schedule.get("slot_1", {}))

        slot_info = timetable.get("slots", {}).get(slot_key, {})
        time_desc = slot_info.get("time_ist", "13:00" if slot_key == "slot_1" else "18:00")

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

    @classmethod
    def is_within_delivery_window(cls, slot_key: str) -> tuple[bool, str]:
        """
        Validates if current time is within strict acceptable delivery window for the slot.
        Slot 1: Target 13:00 IST (1:00 PM). Acceptable: 12:45 PM to 02:00 PM IST.
        Slot 2: Target 18:00 IST (6:00 PM). Acceptable: 05:45 PM to 07:00 PM IST.
        Prevents dispatching messages at random times or middle of the night if runners were delayed.
        """
        ist_tz = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.datetime.now(ist_tz)
        current_time_str = now_ist.strftime("%I:%M %p")
        current_minute = now_ist.hour * 60 + now_ist.minute

        clean_slot = str(slot_key).lower().replace("slot_", "")
        if clean_slot == "1":
            target = "1:00 PM IST"
            window_start = 12 * 60 + 45  # 12:45 PM
            window_end = 14 * 60 + 0     # 02:00 PM
            window_desc = "12:45 PM - 02:00 PM IST"
        elif clean_slot == "2":
            target = "6:00 PM IST"
            window_start = 17 * 60 + 45  # 05:45 PM
            window_end = 19 * 60 + 0     # 07:00 PM
            window_desc = "05:45 PM - 07:00 PM IST"
        else:
            return True, f"Slot {slot_key} has no window restriction."

        if window_start <= current_minute <= window_end:
            return True, f"Current time ({current_time_str} IST) is within window for Slot {clean_slot} ({window_desc})."
        else:
            return False, (
                f"Current time ({current_time_str} IST) is OUTSIDE acceptable delivery window for Slot {clean_slot} "
                f"(Target: {target}, Window: {window_desc}). "
                f"Aborting execution to prevent untimely messages."
            )

