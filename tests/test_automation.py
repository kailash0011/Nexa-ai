"""
Tests for nexa/services/pc_controller.py and nexa/services/task_chain.py,
plus new intent keywords in nexa/brain/intent_parser.py.
"""

import json
import sys
from unittest.mock import MagicMock, patch, call

import pytest

# Inject a mock pyautogui before importing pc_controller so tests work
# in headless environments that have no display.
_mock_pyautogui = MagicMock()
sys.modules.setdefault("pyautogui", _mock_pyautogui)

from nexa.services.pc_controller import PCController
import nexa.services.pc_controller as _pc_mod

from nexa.services.task_chain import TaskChain, QUICK_ACTIONS
from nexa.brain.intent_parser import IntentParser, SUPPORTED_INTENTS


# -----------------------------------------------------------------------
# PCController
# -----------------------------------------------------------------------

class TestPCController:
    """Test PCController with mocked pyautogui."""

    def setup_method(self):
        self.pc = PCController()
        self.pc.available = True
        # Reset call history on the shared mock
        _mock_pyautogui.reset_mock()

    def test_click_when_available(self):
        _pc_mod.pyautogui = _mock_pyautogui
        result = self.pc.click(100, 200)
        assert result is True
        _mock_pyautogui.click.assert_called_once_with(100, 200, clicks=1, button="left")

    def test_click_when_unavailable(self):
        self.pc.available = False
        result = self.pc.click(100, 200)
        assert result is False

    def test_double_click(self):
        _pc_mod.pyautogui = _mock_pyautogui
        result = self.pc.double_click(50, 60)
        assert result is True
        _mock_pyautogui.click.assert_called_once_with(50, 60, clicks=2, button="left")

    def test_right_click(self):
        _pc_mod.pyautogui = _mock_pyautogui
        result = self.pc.right_click(10, 20)
        assert result is True
        _mock_pyautogui.click.assert_called_once_with(10, 20, clicks=1, button="right")

    def test_type_text_ascii(self):
        _pc_mod.pyautogui = _mock_pyautogui
        result = self.pc.type_text("hello")
        assert result is True
        _mock_pyautogui.typewrite.assert_called_once_with("hello", interval=0.02)

    def test_type_text_non_ascii_uses_write(self):
        _pc_mod.pyautogui = _mock_pyautogui
        result = self.pc.type_text("héllo")
        assert result is True
        _mock_pyautogui.write.assert_called_once()

    def test_press_key(self):
        _pc_mod.pyautogui = _mock_pyautogui
        result = self.pc.press_key("enter")
        assert result is True
        _mock_pyautogui.press.assert_called_once_with("enter")

    def test_hotkey(self):
        _pc_mod.pyautogui = _mock_pyautogui
        result = self.pc.hotkey("ctrl", "c")
        assert result is True
        _mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")

    def test_screenshot_returns_path(self, tmp_path):
        _pc_mod.pyautogui = _mock_pyautogui
        save_path = str(tmp_path / "test_shot.png")
        mock_img = MagicMock()
        _mock_pyautogui.screenshot.return_value = mock_img
        result = self.pc.screenshot(save_path)
        assert result == save_path
        mock_img.save.assert_called_once_with(save_path)

    def test_screenshot_when_unavailable(self):
        self.pc.available = False
        result = self.pc.screenshot()
        assert result is None

    def test_get_screen_size_when_unavailable(self):
        self.pc.available = False
        size = self.pc.get_screen_size()
        assert size == (1920, 1080)

    def test_get_mouse_position_when_unavailable(self):
        self.pc.available = False
        pos = self.pc.get_mouse_position()
        assert pos == (0, 0)

    def test_open_url(self):
        with patch("webbrowser.open") as mock_open:
            result = self.pc.open_url("https://example.com")
        assert result is True
        mock_open.assert_called_once_with("https://example.com")

    def test_open_path_missing_returns_false(self):
        result = self.pc.open_path("/nonexistent/path/file.txt")
        assert result is False

    def test_scroll_when_available(self):
        _pc_mod.pyautogui = _mock_pyautogui
        result = self.pc.scroll(3)
        assert result is True
        _mock_pyautogui.scroll.assert_called_once_with(3)

    def test_convenience_hotkeys(self):
        _pc_mod.pyautogui = _mock_pyautogui
        assert self.pc.select_all() is True
        assert self.pc.copy() is True
        assert self.pc.paste() is True
        assert self.pc.cut() is True
        assert self.pc.save() is True


# -----------------------------------------------------------------------
# TaskChain — quick_match
# -----------------------------------------------------------------------

class TestTaskChainQuickMatch:
    """Test TaskChain._quick_match for fast path without LLM."""

    def setup_method(self):
        self.tc = TaskChain()

    def _get_urls(self, steps):
        """Extract all URLs from a list of steps."""
        return [s.get("url", s.get("params", {}).get("url", "")) for s in steps]

    def test_open_youtube_quick_match(self):
        steps = self.tc._quick_match("open youtube please")
        assert steps is not None
        urls = self._get_urls(steps)
        assert any(u == "https://www.youtube.com" for u in urls)

    def test_open_google_quick_match(self):
        steps = self.tc._quick_match("open google")
        assert steps is not None
        urls = self._get_urls(steps)
        assert any(u == "https://www.google.com" for u in urls)

    def test_open_github_quick_match(self):
        steps = self.tc._quick_match("open github")
        assert steps is not None

    def test_search_on_youtube(self):
        steps = self.tc._quick_match("search for Python tutorials on youtube")
        assert steps is not None
        urls = self._get_urls(steps)
        assert any("youtube.com/results" in u for u in urls)

    def test_search_on_google(self):
        steps = self.tc._quick_match("search for best pizza on google")
        assert steps is not None
        urls = self._get_urls(steps)
        assert any("google.com/search" in u for u in urls)

    def test_go_to_domain(self):
        steps = self.tc._quick_match("go to github.com")
        assert steps is not None
        urls = self._get_urls(steps)
        assert any(u == "https://github.com" for u in urls)

    def test_open_unix_path(self):
        steps = self.tc._quick_match("open /home/user/documents")
        assert steps is not None
        assert steps[0]["action"] == "open_file"

    def test_no_match_returns_none(self):
        steps = self.tc._quick_match("what is the weather like")
        assert steps is None

    def test_all_quick_actions_keys_present(self):
        for key in QUICK_ACTIONS:
            steps = self.tc._quick_match(key)
            assert steps is not None, f"Quick match failed for '{key}'"


# -----------------------------------------------------------------------
# TaskChain — _plan_with_llm
# -----------------------------------------------------------------------

class TestTaskChainPlanWithLLM:
    """Test TaskChain._plan_with_llm with a mocked LLM."""

    def setup_method(self):
        self.tc = TaskChain()

    def _mock_llm(self, response: str):
        mock_llm = MagicMock()
        mock_llm.ask.return_value = response
        self.tc._llm = mock_llm
        return mock_llm

    def test_plan_returns_steps_from_json_array(self):
        steps_json = json.dumps([
            {"step": 1, "action": "open_url", "params": {"url": "https://youtube.com"}, "description": "Open YouTube"},
            {"step": 2, "action": "done", "params": {}, "description": "Done"},
        ])
        self._mock_llm(steps_json)
        steps = self.tc._plan_with_llm("open youtube and search for cats")
        assert steps is not None
        assert len(steps) == 2
        assert steps[0]["action"] == "open_url"

    def test_plan_extracts_embedded_json_array(self):
        raw = 'Sure! Here are the steps:\n[{"step": 1, "action": "done", "params": {}, "description": "Done"}]\nThat is all.'
        self._mock_llm(raw)
        steps = self.tc._plan_with_llm("do something")
        assert steps is not None
        assert steps[0]["action"] == "done"

    def test_plan_returns_none_on_bad_response(self):
        self._mock_llm("I cannot help with that.")
        steps = self.tc._plan_with_llm("impossible task")
        assert steps is None

    def test_plan_returns_none_on_llm_error(self):
        mock_llm = MagicMock()
        mock_llm.ask.side_effect = Exception("LLM unavailable")
        self.tc._llm = mock_llm
        steps = self.tc._plan_with_llm("some task")
        assert steps is None


# -----------------------------------------------------------------------
# TaskChain — _execute_step
# -----------------------------------------------------------------------

class TestTaskChainExecuteStep:
    """Test TaskChain._execute_step for each action type."""

    def setup_method(self):
        self.tc = TaskChain()

    def test_execute_open_url(self):
        with patch("nexa.services.pc_controller.pc_controller.open_url", return_value=True) as mock_open:
            result = self.tc._execute_step("open_url", {"url": "https://example.com"})
        assert result is True
        mock_open.assert_called_once_with("https://example.com")

    def test_execute_press_key(self):
        with patch("nexa.services.pc_controller.pc_controller.press_key", return_value=True) as mock_key:
            result = self.tc._execute_step("press_key", {"key": "enter"})
        assert result is True
        mock_key.assert_called_once_with("enter")

    def test_execute_hotkey(self):
        with patch("nexa.services.pc_controller.pc_controller.hotkey", return_value=True) as mock_hk:
            result = self.tc._execute_step("hotkey", {"keys": "ctrl+c"})
        assert result is True
        mock_hk.assert_called_once_with("ctrl", "c")

    def test_execute_click_with_coordinates(self):
        with patch("nexa.services.pc_controller.pc_controller.click", return_value=True) as mock_click:
            result = self.tc._execute_step("click", {"x": 100, "y": 200})
        assert result is True
        mock_click.assert_called_once_with(100, 200)

    def test_execute_click_search_bar_shortcut(self):
        with patch("nexa.services.pc_controller.pc_controller.hotkey", return_value=True):
            result = self.tc._execute_step("click", {"description": "click the search bar"})
        assert result is True

    def test_execute_scroll_down(self):
        with patch("nexa.services.pc_controller.pc_controller.scroll", return_value=True) as mock_scroll:
            result = self.tc._execute_step("scroll", {"direction": "down", "amount": 3})
        assert result is True
        mock_scroll.assert_called_once_with(-3)

    def test_execute_scroll_up(self):
        with patch("nexa.services.pc_controller.pc_controller.scroll", return_value=True) as mock_scroll:
            result = self.tc._execute_step("scroll", {"direction": "up", "amount": 2})
        assert result is True
        mock_scroll.assert_called_once_with(2)

    def test_execute_wait(self):
        with patch("nexa.services.pc_controller.pc_controller.wait") as mock_wait:
            result = self.tc._execute_step("wait", {"seconds": 1})
        assert result is True
        mock_wait.assert_called_once_with(1.0)

    def test_execute_done(self):
        result = self.tc._execute_step("done", {})
        assert result is True

    def test_execute_select_text(self):
        with patch("nexa.services.pc_controller.pc_controller.select_all", return_value=True):
            result = self.tc._execute_step("select_text", {})
        assert result is True

    def test_execute_copy(self):
        with patch("nexa.services.pc_controller.pc_controller.copy", return_value=True):
            result = self.tc._execute_step("copy", {})
        assert result is True

    def test_execute_paste(self):
        with patch("nexa.services.pc_controller.pc_controller.paste", return_value=True):
            result = self.tc._execute_step("paste", {})
        assert result is True

    def test_execute_unknown_action_returns_true(self):
        result = self.tc._execute_step("nonexistent_action", {})
        assert result is True

    def test_execute_open_file_missing_path(self):
        result = self.tc._execute_step("open_file", {"path": "/nonexistent/file.txt"})
        assert result is False


# -----------------------------------------------------------------------
# TaskChain — execute_instruction integration
# -----------------------------------------------------------------------

class TestTaskChainExecuteInstruction:
    """Integration tests for execute_instruction."""

    def setup_method(self):
        self.tc = TaskChain()

    def test_execute_quick_action(self):
        with patch("nexa.services.pc_controller.pc_controller.open_url", return_value=True):
            with patch("nexa.services.pc_controller.pc_controller.wait"):
                result = self.tc.execute_instruction("open youtube")
        assert "done" in result.lower() or "step" in result.lower()

    def test_speak_fn_called(self):
        speak_calls = []
        with patch("nexa.services.pc_controller.pc_controller.open_url", return_value=True):
            with patch("nexa.services.pc_controller.pc_controller.wait"):
                result = self.tc.execute_instruction("open github", speak_fn=speak_calls.append)
        assert len(speak_calls) >= 1

    def test_no_steps_returns_helpful_message(self):
        mock_llm = MagicMock()
        mock_llm.ask.return_value = "not json"
        self.tc._llm = mock_llm
        result = self.tc.execute_instruction("xyzzy flibbertigibbet")
        assert "couldn't" in result.lower() or "simpler" in result.lower()


# -----------------------------------------------------------------------
# TaskChain — _extract_json_array
# -----------------------------------------------------------------------

class TestExtractJsonArray:
    def setup_method(self):
        self.tc = TaskChain()

    def test_pure_json_array(self):
        data = [{"action": "done"}]
        result = self.tc._extract_json_array(json.dumps(data))
        assert result == data

    def test_embedded_in_text(self):
        text = 'Here are the steps: [{"action": "done"}] Hope that helps!'
        result = self.tc._extract_json_array(text)
        assert result is not None
        assert result[0]["action"] == "done"

    def test_invalid_returns_none(self):
        result = self.tc._extract_json_array("no json here at all")
        assert result is None


# -----------------------------------------------------------------------
# IntentParser — new keyword rules
# -----------------------------------------------------------------------

class TestIntentParserKeywords:
    """Test the new keyword-based intent rules."""

    def setup_method(self):
        self.parser = IntentParser()

    def test_multi_step_intent_and_then(self):
        result = self.parser.parse("Open Chrome and then go to youtube")
        assert result["action"] == "multi_step"
        assert result["target"] == "Open Chrome and then go to youtube"

    def test_multi_step_intent_then(self):
        result = self.parser.parse("Open notepad then type hello")
        assert result["action"] == "multi_step"

    def test_browse_intent_go_to(self):
        result = self.parser.parse("go to youtube.com")
        assert result["action"] == "browse"
        assert "go to youtube.com" in result["target"]

    def test_browse_intent_navigate_to(self):
        result = self.parser.parse("navigate to github.com")
        assert result["action"] == "browse"

    def test_browse_intent_visit(self):
        result = self.parser.parse("visit stackoverflow.com")
        assert result["action"] == "browse"

    def test_web_search_intent(self):
        result = self.parser.parse("search for Python tutorials on google")
        assert result["action"] == "web_search"

    def test_login_intent(self):
        result = self.parser.parse("login to gmail")
        assert result["action"] == "login"
        assert result["target"] == "login to gmail"

    def test_sign_in_to_intent(self):
        result = self.parser.parse("sign in to my GitHub account")
        assert result["action"] == "login"

    def test_new_intents_in_supported_list(self):
        assert "multi_step" in SUPPORTED_INTENTS
        assert "browse" in SUPPORTED_INTENTS
        assert "login" in SUPPORTED_INTENTS

    def test_keyword_match_bypasses_llm(self):
        """Keyword match should not call LLM."""
        with patch("nexa.brain.intent_parser.llm.ask") as mock_llm:
            result = self.parser.parse("go to example.com")
        mock_llm.assert_not_called()
        assert result["action"] == "browse"

