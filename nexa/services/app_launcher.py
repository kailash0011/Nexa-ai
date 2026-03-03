"""
Nexa AI — Application Launcher Service
Open and close applications on Windows / Linux / macOS.
"""

import platform
import subprocess
from typing import Optional

import psutil  # type: ignore

from nexa.utils.logger import get_logger

logger = get_logger(__name__)

_OS = platform.system()

# Common Windows app paths / commands
WINDOWS_APPS: dict[str, str] = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "explorer": "explorer.exe",
    "vs code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vscode": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",  # Windows Terminal
    "powershell": "powershell.exe",
    "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "spotify": r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "discord": r"C:\Users\{user}\AppData\Local\Discord\Discord.exe",
    "steam": r"C:\Program Files (x86)\Steam\Steam.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
}

# Linux / macOS equivalents
LINUX_APPS: dict[str, str] = {
    "chrome": "google-chrome",
    "google chrome": "google-chrome",
    "firefox": "firefox",
    "terminal": "gnome-terminal",
    "vs code": "code",
    "vscode": "code",
    "calculator": "gnome-calculator",
    "files": "nautilus",
    "vlc": "vlc",
    "spotify": "spotify",
    "discord": "discord",
}

MAC_APPS: dict[str, str] = {
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "firefox": "Firefox",
    "safari": "Safari",
    "terminal": "Terminal",
    "vs code": "Visual Studio Code",
    "vscode": "Visual Studio Code",
    "calculator": "Calculator",
    "finder": "Finder",
    "vlc": "VLC",
    "spotify": "Spotify",
    "discord": "Discord",
}


class AppLauncher:
    """Launch and close desktop applications."""

    def open_app(self, app_name: str) -> bool:
        """
        Open an application by name.

        Args:
            app_name: Common name of the application (case-insensitive).

        Returns:
            True if the app was launched successfully.
        """
        key = app_name.lower().strip()
        try:
            if _OS == "Windows":
                return self._open_windows(key)
            elif _OS == "Darwin":
                return self._open_mac(key)
            else:
                return self._open_linux(key)
        except Exception as exc:
            logger.error(f"open_app error for '{app_name}': {exc}")
            return False

    def _open_windows(self, key: str) -> bool:
        path = WINDOWS_APPS.get(key, key)
        try:
            subprocess.Popen(path, shell=True)
            logger.info(f"🚀 Opened (Windows): {key}")
            return True
        except Exception as exc:
            logger.error(f"Windows open error: {exc}")
            return False

    def _open_linux(self, key: str) -> bool:
        cmd = LINUX_APPS.get(key, key)
        try:
            subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"🚀 Opened (Linux): {key}")
            return True
        except Exception as exc:
            logger.error(f"Linux open error: {exc}")
            return False

    def _open_mac(self, key: str) -> bool:
        app = MAC_APPS.get(key, key)
        try:
            subprocess.Popen(["open", "-a", app])
            logger.info(f"🚀 Opened (macOS): {key}")
            return True
        except Exception as exc:
            logger.error(f"macOS open error: {exc}")
            return False

    def close_app(self, app_name: str) -> bool:
        """
        Close all running processes whose name contains app_name.

        Args:
            app_name: Name of the process to kill (case-insensitive).

        Returns:
            True if at least one matching process was terminated.
        """
        key = app_name.lower()
        killed = False
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if key in proc.info["name"].lower():
                    proc.kill()
                    logger.info(f"💀 Closed process: {proc.info['name']} (PID {proc.info['pid']})")
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not killed:
            logger.warning(f"No process found for '{app_name}'")
        return killed

    def list_running_apps(self) -> list[str]:
        """
        Return a deduplicated list of currently running application names.

        Returns:
            Sorted list of process name strings.
        """
        names: set[str] = set()
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"]
                if name:
                    names.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(names)


# Module-level singleton
app_launcher = AppLauncher()
