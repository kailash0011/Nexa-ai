"""
Nexa AI — Phone Calls via ADB (Android Debug Bridge)
Controls a connected Android device to make/end calls and send SMS.
"""

import subprocess
import time
import urllib.parse

from nexa.utils.logger import get_logger

logger = get_logger(__name__)


class PhoneCall:
    """
    Interface for making phone calls and sending SMS via ADB.
    Requires an Android phone connected via USB with USB Debugging enabled.
    """

    def __init__(self) -> None:
        self._adb_available = self._check_adb()

    # ------------------------------------------------------------------
    # ADB helpers
    # ------------------------------------------------------------------

    def _check_adb(self) -> bool:
        """Return True if adb is installed and a device is connected."""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().splitlines()
            # Filter out the header line; any remaining line = device connected
            devices = [l for l in lines[1:] if l.strip() and "offline" not in l]
            if devices:
                logger.info(f"📱 ADB device found: {devices[0]}")
                return True
            logger.warning("⚠️  No ADB device connected.")
            return False
        except FileNotFoundError:
            logger.warning("⚠️  adb not found in PATH. Phone features disabled.")
            return False
        except Exception as exc:
            logger.error(f"ADB check error: {exc}")
            return False

    def _adb(self, *args: str) -> subprocess.CompletedProcess:
        """Run an adb shell command."""
        return subprocess.run(
            ["adb", "shell", *args],
            capture_output=True,
            text=True,
            timeout=10,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_connected(self) -> bool:
        """Check if a phone is currently connected."""
        return self._check_adb()

    def make_call(self, phone_number: str) -> bool:
        """
        Dial a phone number on the connected Android device.

        Args:
            phone_number: E.164 or local number string.

        Returns:
            True if the call command was sent successfully.
        """
        if not self._adb_available:
            logger.error("❌ Cannot make call — no ADB device.")
            return False
        try:
            encoded = urllib.parse.quote(phone_number)
            self._adb("am", "start", "-a", "android.intent.action.CALL",
                      "-d", f"tel:{encoded}")
            logger.info(f"📞 Calling {phone_number}…")
            return True
        except Exception as exc:
            logger.error(f"make_call error: {exc}")
            return False

    def end_call(self) -> bool:
        """
        Hang up the current call.

        Returns:
            True if the command was sent successfully.
        """
        if not self._adb_available:
            return False
        try:
            self._adb("input", "keyevent", "6")  # KEYCODE_ENDCALL
            logger.info("📵 Call ended.")
            return True
        except Exception as exc:
            logger.error(f"end_call error: {exc}")
            return False

    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send an SMS via the Android Messages app using ADB.

        Args:
            phone_number: Recipient phone number.
            message: SMS body text.

        Returns:
            True if the intent was sent successfully.
        """
        if not self._adb_available:
            logger.error("❌ Cannot send SMS — no ADB device.")
            return False
        try:
            encoded_msg = urllib.parse.quote(message)
            encoded_num = urllib.parse.quote(phone_number)
            self._adb(
                "am", "start", "-a", "android.intent.action.SENDTO",
                "-d", f"sms:{encoded_num}",
                "--es", "sms_body", encoded_msg,
                "--ez", "exit_on_sent", "true",
            )
            time.sleep(1)
            # Simulate pressing Send button
            self._adb("input", "keyevent", "22")  # KEYCODE_DPAD_RIGHT to Send button
            self._adb("input", "keyevent", "66")  # KEYCODE_ENTER
            logger.info(f"💬 SMS sent to {phone_number}")
            return True
        except Exception as exc:
            logger.error(f"send_sms error: {exc}")
            return False


# Module-level singleton
phone = PhoneCall()
