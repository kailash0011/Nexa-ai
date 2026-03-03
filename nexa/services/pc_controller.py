"""
Nexa AI — PC Controller
Low-level mouse, keyboard, and screen control using pyautogui.
"""
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

from nexa.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.3  # Small delay between actions
    _PYAUTOGUI_AVAILABLE = True
except Exception:
    _PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not available. Run: pip install pyautogui (requires display)")

_IS_WINDOWS = platform.system() == "Windows"


class PCController:
    """Control mouse, keyboard, and screen."""

    def __init__(self):
        self.available = _PYAUTOGUI_AVAILABLE

    # ── Mouse Actions ──
    def click(self, x: int, y: int, clicks: int = 1, button: str = "left") -> bool:
        if not self.available:
            return False
        try:
            pyautogui.click(x, y, clicks=clicks, button=button)
            logger.info(f"🖱️ Clicked ({x}, {y}) button={button}")
            return True
        except Exception as exc:
            logger.error(f"Click error: {exc}")
            return False

    def double_click(self, x: int, y: int) -> bool:
        return self.click(x, y, clicks=2)

    def right_click(self, x: int, y: int) -> bool:
        return self.click(x, y, button="right")

    def move_to(self, x: int, y: int, duration: float = 0.3) -> bool:
        if not self.available:
            return False
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as exc:
            logger.error(f"Move error: {exc}")
            return False

    def scroll(self, amount: int) -> bool:
        if not self.available:
            return False
        try:
            pyautogui.scroll(amount)
            logger.info(f"🖱️ Scrolled {amount}")
            return True
        except Exception as exc:
            logger.error(f"Scroll error: {exc}")
            return False

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> bool:
        if not self.available:
            return False
        try:
            pyautogui.moveTo(start_x, start_y)
            pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
            logger.info(f"🖱️ Dragged from ({start_x},{start_y}) to ({end_x},{end_y})")
            return True
        except Exception as exc:
            logger.error(f"Drag error: {exc}")
            return False

    # ── Keyboard Actions ──
    def type_text(self, text: str, interval: float = 0.02) -> bool:
        if not self.available:
            return False
        try:
            if text.isascii():
                pyautogui.typewrite(text, interval=interval)
            else:
                pyautogui.write(text)
            logger.info(f"⌨️ Typed: '{text[:50]}...'")
            return True
        except Exception:
            # Fallback for non-ASCII characters
            try:
                import pyperclip
                pyperclip.copy(text)
                pyautogui.hotkey("ctrl", "v")
                logger.info(f"⌨️ Typed (clipboard): '{text[:50]}...'")
                return True
            except Exception as exc:
                logger.error(f"Type error: {exc}")
                return False

    def press_key(self, key: str) -> bool:
        if not self.available:
            return False
        try:
            pyautogui.press(key)
            logger.info(f"⌨️ Pressed: {key}")
            return True
        except Exception as exc:
            logger.error(f"Key press error: {exc}")
            return False

    def hotkey(self, *keys: str) -> bool:
        if not self.available:
            return False
        try:
            pyautogui.hotkey(*keys)
            logger.info(f"⌨️ Hotkey: {'+'.join(keys)}")
            return True
        except Exception as exc:
            logger.error(f"Hotkey error: {exc}")
            return False

    # ── Screen Actions ──
    def screenshot(self, save_path: str = "screenshot.png") -> Optional[str]:
        if not self.available:
            return None
        try:
            img = pyautogui.screenshot()
            img.save(save_path)
            logger.info(f"📸 Screenshot saved: {save_path}")
            return save_path
        except Exception as exc:
            logger.error(f"Screenshot error: {exc}")
            return None

    def get_screen_size(self) -> Tuple[int, int]:
        if not self.available:
            return (1920, 1080)
        return pyautogui.size()

    def get_mouse_position(self) -> Tuple[int, int]:
        if not self.available:
            return (0, 0)
        return pyautogui.position()

    def find_on_screen(self, image_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """Find an image on screen and return its center coordinates."""
        if not self.available:
            return None
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                logger.info(f"🔍 Found image at ({center.x}, {center.y})")
                return (center.x, center.y)
        except Exception as exc:
            logger.debug(f"Image not found: {exc}")
        return None

    # ── Windows-Specific Helpers ──
    def open_run_dialog(self) -> bool:
        return self.hotkey("win", "r")

    def open_start_menu(self) -> bool:
        return self.press_key("win")

    def switch_window(self) -> bool:
        return self.hotkey("alt", "tab")

    def minimize_all(self) -> bool:
        return self.hotkey("win", "d")

    def open_task_manager(self) -> bool:
        return self.hotkey("ctrl", "shift", "escape")

    def select_all(self) -> bool:
        return self.hotkey("ctrl", "a")

    def copy(self) -> bool:
        return self.hotkey("ctrl", "c")

    def paste(self) -> bool:
        return self.hotkey("ctrl", "v")

    def cut(self) -> bool:
        return self.hotkey("ctrl", "x")

    def undo(self) -> bool:
        return self.hotkey("ctrl", "z")

    def save(self) -> bool:
        return self.hotkey("ctrl", "s")

    def close_window(self) -> bool:
        return self.hotkey("alt", "f4")

    def new_tab(self) -> bool:
        return self.hotkey("ctrl", "t")

    def close_tab(self) -> bool:
        return self.hotkey("ctrl", "w")

    def address_bar(self) -> bool:
        """Focus browser address bar."""
        return self.hotkey("ctrl", "l")

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)

    # ── Open Files/Folders ──
    def open_path(self, path: str) -> bool:
        """Open any file or folder with default app."""
        try:
            p = Path(path)
            if not p.exists():
                logger.warning(f"Path not found: {path}")
                return False
            if _IS_WINDOWS:
                os.startfile(str(p))
            else:
                subprocess.Popen(["xdg-open", str(p)])
            logger.info(f"📂 Opened: {path}")
            return True
        except Exception as exc:
            logger.error(f"Open path error: {exc}")
            return False

    def open_url(self, url: str) -> bool:
        """Open a URL in default browser."""
        try:
            import webbrowser
            webbrowser.open(url)
            logger.info(f"🌐 Opened URL: {url}")
            return True
        except Exception as exc:
            logger.error(f"Open URL error: {exc}")
            return False


pc_controller = PCController()
