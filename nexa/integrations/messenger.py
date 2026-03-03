"""
Nexa AI — Facebook Messenger Integration
Uses Selenium browser automation (free) to send Messenger messages.
"""

import time
from pathlib import Path
from typing import Optional

from nexa.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from selenium import webdriver  # type: ignore
    from selenium.webdriver.chrome.options import Options  # type: ignore
    from selenium.webdriver.chrome.service import Service  # type: ignore
    from selenium.webdriver.common.by import By  # type: ignore
    from selenium.webdriver.common.keys import Keys  # type: ignore
    from selenium.webdriver.support import expected_conditions as EC  # type: ignore
    from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
    from webdriver_manager.chrome import ChromeDriverManager  # type: ignore

    _SELENIUM_AVAILABLE = True
except ImportError:
    _SELENIUM_AVAILABLE = False
    logger.warning(
        "⚠️  Selenium / webdriver-manager not installed — Messenger disabled. "
        "Run: pip install selenium webdriver-manager"
    )

# Path where Selenium saves the browser profile for session persistence
_PROFILE_DIR = str(Path.home() / ".nexa_messenger_profile")
MESSENGER_URL = "https://www.messenger.com"


class Messenger:
    """
    Send Facebook Messenger messages via headless Chrome automation.
    Stores login session to avoid repeated logins.
    """

    def __init__(self) -> None:
        self._driver: Optional[object] = None

    def _get_driver(self) -> Optional[object]:
        """Initialise (or reuse) a Chrome WebDriver instance."""
        if self._driver:
            return self._driver

        if not _SELENIUM_AVAILABLE:
            return None

        try:
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument(f"--user-data-dir={_PROFILE_DIR}")
            options.add_argument("--disable-notifications")
            options.add_experimental_option("excludeSwitches", ["enable-logging"])

            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=options)
            return self._driver
        except Exception as exc:
            logger.error(f"Failed to start Chrome: {exc}")
            return None

    def send_message(self, contact_name: str, message: str) -> bool:
        """
        Send a message to a Messenger contact by name.

        Args:
            contact_name: The display name of the Messenger contact.
            message: Message body text.

        Returns:
            True if the message was sent successfully.
        """
        if not _SELENIUM_AVAILABLE:
            logger.error("❌ Selenium not available.")
            return False

        driver = self._get_driver()
        if not driver:
            return False

        try:
            driver.get(MESSENGER_URL)
            wait = WebDriverWait(driver, 20)

            # Search for contact
            search_box = wait.until(
                EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search Messenger"]'))
            )
            search_box.clear()
            search_box.send_keys(contact_name)
            time.sleep(2)
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)

            # Type and send message
            msg_box = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@role="textbox"][@contenteditable="true"]')
                )
            )
            msg_box.click()
            msg_box.send_keys(message)
            msg_box.send_keys(Keys.RETURN)

            logger.info(f"✅ Messenger message sent to {contact_name}")
            return True
        except Exception as exc:
            logger.error(f"Messenger send error: {exc}")
            return False

    def close(self) -> None:
        """Close the browser session."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None


# Module-level singleton
messenger = Messenger()
