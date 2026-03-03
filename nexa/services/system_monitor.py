"""
Nexa AI — System Monitor Service
Reports CPU, RAM, disk, and battery status via psutil.
"""

from typing import Any, Optional

import psutil  # type: ignore

from nexa.utils.logger import get_logger

logger = get_logger(__name__)


class SystemMonitor:
    """Provides human-readable system resource information."""

    def get_cpu_usage(self) -> str:
        """Return current CPU usage as a formatted string."""
        try:
            usage = psutil.cpu_percent(interval=1)
            return f"CPU: {usage:.1f}%"
        except Exception as exc:
            logger.error(f"get_cpu_usage error: {exc}")
            return "CPU: unavailable"

    def get_ram_usage(self) -> str:
        """Return RAM usage as a formatted string (used / total GB)."""
        try:
            mem = psutil.virtual_memory()
            used_gb = mem.used / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            pct = mem.percent
            return f"RAM: {used_gb:.1f}/{total_gb:.1f} GB ({pct:.0f}%)"
        except Exception as exc:
            logger.error(f"get_ram_usage error: {exc}")
            return "RAM: unavailable"

    def get_disk_usage(self, path: str = "/") -> str:
        """
        Return disk usage for the given path.

        Args:
            path: Filesystem path to check (default: root).

        Returns:
            Human-readable disk usage string.
        """
        try:
            disk = psutil.disk_usage(path)
            free_gb = disk.free / (1024 ** 3)
            total_gb = disk.total / (1024 ** 3)
            used_pct = disk.percent
            return f"Disk: {free_gb:.0f} GB free of {total_gb:.0f} GB ({used_pct:.0f}% used)"
        except Exception as exc:
            logger.error(f"get_disk_usage error: {exc}")
            return "Disk: unavailable"

    def get_battery(self) -> str:
        """Return battery status as a formatted string."""
        try:
            bat = psutil.sensors_battery()
            if bat is None:
                return "Battery: not available (desktop)"
            pct = bat.percent
            plugged = "⚡ charging" if bat.power_plugged else "🔋 on battery"
            return f"Battery: {pct:.0f}% ({plugged})"
        except Exception as exc:
            logger.error(f"get_battery error: {exc}")
            return "Battery: unavailable"

    def get_system_info(self) -> str:
        """
        Return a full system status summary.

        Returns:
            Multi-field status string suitable for Nexa to speak.
        """
        cpu = self.get_cpu_usage()
        ram = self.get_ram_usage()
        # Use home partition on Linux/macOS; C: drive on Windows
        import platform
        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        disk = self.get_disk_usage(disk_path)
        battery = self.get_battery()
        return f"{cpu} | {ram} | {disk} | {battery}"

    def get_raw_stats(self) -> dict[str, Any]:
        """
        Return raw numeric system statistics.

        Returns:
            Dict with cpu_percent, ram_percent, disk_percent, battery_percent.
        """
        stats: dict[str, Any] = {}
        try:
            stats["cpu_percent"] = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            stats["ram_percent"] = mem.percent
            stats["ram_used_gb"] = round(mem.used / (1024 ** 3), 2)
            stats["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)
            disk = psutil.disk_usage("/")
            stats["disk_percent"] = disk.percent
            stats["disk_free_gb"] = round(disk.free / (1024 ** 3), 2)
            bat = psutil.sensors_battery()
            stats["battery_percent"] = bat.percent if bat else None
        except Exception as exc:
            logger.error(f"get_raw_stats error: {exc}")
        return stats


# Module-level singleton
system_monitor = SystemMonitor()
