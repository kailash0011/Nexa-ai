"""
Nexa AI — WhatsApp Integration
Sends WhatsApp messages using pywhatkit (free, uses WhatsApp Web).
"""

import time
from datetime import datetime, timedelta

from nexa.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import pywhatkit  # type: ignore

    _PYWHATKIT_AVAILABLE = True
except ImportError:
    _PYWHATKIT_AVAILABLE = False
    logger.warning(
        "⚠️  pywhatkit not installed — WhatsApp disabled. Run: pip install pywhatkit"
    )


class WhatsApp:
    """Send WhatsApp messages via pywhatkit (WhatsApp Web automation)."""

    def send_message(self, phone_number: str, message: str, wait_seconds: int = 15) -> bool:
        """
        Send a WhatsApp message to a phone number.

        Args:
            phone_number: Recipient's number in international format (e.g. "+919876543210").
            message: Message body text.
            wait_seconds: Seconds to wait before sending (pywhatkit needs WhatsApp Web to load).

        Returns:
            True if the message was sent successfully.
        """
        if not _PYWHATKIT_AVAILABLE:
            logger.error("❌ pywhatkit not available.")
            return False
        try:
            now = datetime.now() + timedelta(seconds=wait_seconds)
            hour, minute = now.hour, now.minute
            pywhatkit.sendwhatmsg(
                phone_number,
                message,
                hour,
                minute,
                wait_time=wait_seconds,
                tab_close=True,
                close_time=3,
            )
            logger.info(f"✅ WhatsApp message sent to {phone_number}")
            return True
        except Exception as exc:
            logger.error(f"WhatsApp send error: {exc}")
            return False

    def send_message_instantly(self, phone_number: str, message: str) -> bool:
        """
        Send a WhatsApp message immediately.

        Args:
            phone_number: Recipient number in international format.
            message: Message body text.

        Returns:
            True if sent successfully.
        """
        if not _PYWHATKIT_AVAILABLE:
            logger.error("❌ pywhatkit not available.")
            return False
        try:
            pywhatkit.sendwhatmsg_instantly(
                phone_number,
                message,
                wait_time=10,
                tab_close=True,
                close_time=3,
            )
            logger.info(f"✅ WhatsApp message sent instantly to {phone_number}")
            return True
        except Exception as exc:
            logger.error(f"WhatsApp instant send error: {exc}")
            return False


# Module-level singleton
whatsapp = WhatsApp()
