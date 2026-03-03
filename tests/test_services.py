"""
Tests for nexa/services — FileManager, AppLauncher, SystemMonitor, Scheduler.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nexa.services.file_manager import FileManager
from nexa.services.system_monitor import SystemMonitor
from nexa.services.scheduler import Scheduler, _parse_time
from nexa.services.app_launcher import AppLauncher


# -----------------------------------------------------------------------
# FileManager
# -----------------------------------------------------------------------

class TestFileManager:
    def setup_method(self):
        self.fm = FileManager()

    def test_search_files_returns_list(self, tmp_path):
        """search_files should return matching paths."""
        (tmp_path / "report.pdf").write_text("dummy")
        (tmp_path / "notes.txt").write_text("dummy")

        results = self.fm.search_files("report", directory=str(tmp_path))
        assert any("report.pdf" in r for r in results)

    def test_search_files_no_match(self, tmp_path):
        results = self.fm.search_files("nonexistent_xyz", directory=str(tmp_path))
        assert results == []

    def test_list_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        entries = self.fm.list_files(str(tmp_path))
        assert "a.txt" in entries
        assert "b.txt" in entries

    def test_get_file_info_existing(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        info = self.fm.get_file_info(str(f))
        assert info["exists"] is True
        assert info["name"] == "test.txt"
        assert info["size_kb"] >= 0

    def test_get_file_info_missing(self):
        info = self.fm.get_file_info("/nonexistent/path/file.xyz")
        assert info["exists"] is False

    def test_open_file_missing_returns_false(self):
        result = self.fm.open_file("/definitely/not/there.txt")
        assert result is False


# -----------------------------------------------------------------------
# SystemMonitor
# -----------------------------------------------------------------------

class TestSystemMonitor:
    def setup_method(self):
        self.monitor = SystemMonitor()

    def test_get_cpu_usage_format(self):
        result = self.monitor.get_cpu_usage()
        assert "CPU:" in result

    def test_get_ram_usage_format(self):
        result = self.monitor.get_ram_usage()
        assert "RAM:" in result
        assert "GB" in result

    def test_get_disk_usage_format(self):
        result = self.monitor.get_disk_usage("/")
        assert "Disk:" in result

    def test_get_system_info_contains_all_sections(self):
        info = self.monitor.get_system_info()
        assert "CPU:" in info
        assert "RAM:" in info
        assert "Disk:" in info

    def test_get_raw_stats_returns_dict(self):
        stats = self.monitor.get_raw_stats()
        assert isinstance(stats, dict)
        assert "cpu_percent" in stats
        assert "ram_percent" in stats

    def test_get_battery_returns_string(self):
        result = self.monitor.get_battery()
        assert isinstance(result, str)
        assert "Battery:" in result


# -----------------------------------------------------------------------
# Scheduler
# -----------------------------------------------------------------------

class TestScheduler:
    def setup_method(self):
        self.sched = Scheduler()
        self.sched.start()

    def teardown_method(self):
        self.sched.stop()

    def test_set_and_list_reminder(self):
        rid = self.sched.set_reminder("Buy milk", "in 60 seconds")
        assert rid is not None
        reminders = self.sched.list_reminders()
        ids = [r["id"] for r in reminders]
        assert rid in ids

    def test_cancel_reminder(self):
        rid = self.sched.set_reminder("Test", "in 60 seconds")
        result = self.sched.cancel_reminder(rid)
        assert result is True
        ids = [r["id"] for r in self.sched.list_reminders()]
        assert rid not in ids

    def test_cancel_nonexistent(self):
        result = self.sched.cancel_reminder("nope_id")
        assert result is False

    def test_reminder_fires(self):
        fired = []
        rid = self.sched.set_reminder("Hello!", "in 1 seconds", callback=lambda m: fired.append(m))
        time.sleep(2)
        assert fired, "Reminder callback should have fired"
        assert fired[0] == "Hello!"

    def test_invalid_time_returns_none(self):
        rid = self.sched.set_reminder("Bad time", "not a valid time string")
        assert rid is None


class TestParseTime:
    def test_in_seconds(self):
        from datetime import datetime, timedelta
        result = _parse_time("in 5 seconds")
        assert result is not None
        assert abs((result - (datetime.now() + timedelta(seconds=5))).total_seconds()) < 2

    def test_in_minutes(self):
        from datetime import datetime, timedelta
        result = _parse_time("in 10 minutes")
        assert result is not None

    def test_in_hours(self):
        from datetime import datetime, timedelta
        result = _parse_time("in 2 hours")
        assert result is not None

    def test_hhmm_format(self):
        result = _parse_time("23:59")
        assert result is not None

    def test_invalid_returns_none(self):
        result = _parse_time("sometime tomorrow maybe")
        assert result is None


# -----------------------------------------------------------------------
# AppLauncher
# -----------------------------------------------------------------------

class TestAppLauncher:
    def setup_method(self):
        self.launcher = AppLauncher()

    def test_list_running_apps_returns_list(self):
        apps = self.launcher.list_running_apps()
        assert isinstance(apps, list)
        assert len(apps) > 0

    def test_close_nonexistent_app(self):
        result = self.launcher.close_app("definitely_not_running_app_xyz")
        assert result is False

    def test_open_app_windows_dict(self):
        from nexa.services.app_launcher import WINDOWS_APPS
        assert "chrome" in WINDOWS_APPS
        assert "notepad" in WINDOWS_APPS
