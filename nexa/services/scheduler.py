"""
Nexa AI — Scheduler Service
Set reminders and timers; background thread fires callbacks when due.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional
import re

from nexa.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Reminder:
    """Represents a single scheduled reminder."""

    id: str
    message: str
    trigger_time: datetime
    callback: Optional[Callable[[str], None]] = field(default=None, repr=False)
    fired: bool = False


def _parse_time(time_str: str) -> Optional[datetime]:
    """
    Parse a natural-language time string into a datetime.

    Supports:
    - "in X minutes" / "in X hours" / "in X seconds"
    - "HH:MM" or "H:MM am/pm"
    - "Xpm" / "Xam"

    Returns:
        datetime if parsed, else None.
    """
    now = datetime.now()
    ts = time_str.lower().strip()

    # "in X minutes/hours/seconds"
    m = re.match(r"in\s+(\d+)\s+(second|seconds|minute|minutes|hour|hours)", ts)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if "second" in unit:
            return now + timedelta(seconds=n)
        if "minute" in unit:
            return now + timedelta(minutes=n)
        if "hour" in unit:
            return now + timedelta(hours=n)

    # "3pm", "3:30pm", "15:30"
    for fmt in ("%I%p", "%I:%M%p", "%H:%M"):
        try:
            parsed = datetime.strptime(ts.replace(" ", ""), fmt)
            trigger = now.replace(
                hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
            )
            if trigger <= now:
                trigger += timedelta(days=1)
            return trigger
        except ValueError:
            continue

    return None


class Scheduler:
    """
    Background reminder scheduler.
    Fires a callback (or logs) when a reminder's time arrives.
    """

    def __init__(self) -> None:
        self._reminders: dict[str, Reminder] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the background scheduler thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("⏰ Scheduler started.")

    def stop(self) -> None:
        """Stop the background scheduler thread."""
        self._running = False

    def set_reminder(
        self,
        message: str,
        time_str: str,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Optional[str]:
        """
        Schedule a reminder.

        Args:
            message: The reminder text.
            time_str: When to fire (e.g. "in 10 minutes", "3pm").
            callback: Function called with the message when the reminder fires.

        Returns:
            Reminder ID string, or None if the time string couldn't be parsed.
        """
        trigger = _parse_time(time_str)
        if trigger is None:
            logger.warning(f"Could not parse time: '{time_str}'")
            return None

        rid = str(uuid.uuid4())[:8]
        reminder = Reminder(
            id=rid,
            message=message,
            trigger_time=trigger,
            callback=callback,
        )
        with self._lock:
            self._reminders[rid] = reminder
        logger.info(f"⏰ Reminder set [{rid}]: '{message}' at {trigger.strftime('%H:%M:%S')}")
        return rid

    def list_reminders(self) -> list[dict]:
        """Return a list of active (unfired) reminders."""
        with self._lock:
            return [
                {
                    "id": r.id,
                    "message": r.message,
                    "time": r.trigger_time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for r in self._reminders.values()
                if not r.fired
            ]

    def cancel_reminder(self, reminder_id: str) -> bool:
        """
        Cancel a scheduled reminder.

        Args:
            reminder_id: The ID returned by set_reminder.

        Returns:
            True if the reminder was found and removed.
        """
        with self._lock:
            if reminder_id in self._reminders:
                del self._reminders[reminder_id]
                logger.info(f"🗑️  Reminder cancelled: {reminder_id}")
                return True
        logger.warning(f"Reminder not found: {reminder_id}")
        return False

    def _run(self) -> None:
        """Background loop: check reminders every second."""
        while self._running:
            now = datetime.now()
            with self._lock:
                for reminder in list(self._reminders.values()):
                    if not reminder.fired and now >= reminder.trigger_time:
                        reminder.fired = True
                        self._fire(reminder)
            time.sleep(1)

    def _fire(self, reminder: Reminder) -> None:
        """Trigger a reminder callback or log it."""
        logger.info(f"🔔 REMINDER [{reminder.id}]: {reminder.message}")
        if reminder.callback:
            try:
                reminder.callback(reminder.message)
            except Exception as exc:
                logger.error(f"Reminder callback error: {exc}")


# Module-level singleton (call .start() to activate)
scheduler = Scheduler()
