"""
Tests for nexa/brain — LLM and intent parsing.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from nexa.brain.intent_parser import IntentParser, SUPPORTED_INTENTS


class TestIntentParser:
    """Test the IntentParser with a mocked LLM."""

    def setup_method(self):
        self.parser = IntentParser()

    def _mock_llm(self, response: str):
        """Patch llm.ask to return a canned response."""
        return patch("nexa.brain.intent_parser.llm.ask", return_value=response)

    def test_parse_call_intent(self):
        mock_json = json.dumps({"action": "call", "target": "Ram", "message": "boss is busy"})
        with self._mock_llm(mock_json):
            result = self.parser.parse("Call Ram and tell him my boss is busy")
        assert result["action"] == "call"
        assert result["target"] == "Ram"

    def test_parse_whatsapp_intent(self):
        mock_json = json.dumps({"action": "whatsapp", "target": "Sandhya", "message": "I will call you later"})
        with self._mock_llm(mock_json):
            result = self.parser.parse("Send WhatsApp to Sandhya - I will call you later")
        assert result["action"] == "whatsapp"
        assert result["target"] == "Sandhya"
        assert "call you later" in result["message"]

    def test_parse_open_app(self):
        mock_json = json.dumps({"action": "open_app", "target": "Chrome"})
        with self._mock_llm(mock_json):
            result = self.parser.parse("Open Chrome")
        assert result["action"] == "open_app"
        assert result["target"] == "Chrome"

    def test_parse_system_info(self):
        mock_json = json.dumps({"action": "system_info"})
        with self._mock_llm(mock_json):
            result = self.parser.parse("What is my system status?")
        assert result["action"] == "system_info"

    def test_parse_set_busy(self):
        mock_json = json.dumps({"action": "set_busy", "duration": "2 hours"})
        with self._mock_llm(mock_json):
            result = self.parser.parse("I'm busy for 2 hours")
        assert result["action"] == "set_busy"
        assert result["duration"] == "2 hours"

    def test_parse_reminder(self):
        mock_json = json.dumps({"action": "set_reminder", "message": "call mom", "time": "3pm"})
        with self._mock_llm(mock_json):
            result = self.parser.parse("Remind me to call mom at 3pm")
        assert result["action"] == "set_reminder"
        assert result["time"] == "3pm"

    def test_fallback_to_general_chat_on_bad_json(self):
        with self._mock_llm("This is not JSON at all"):
            result = self.parser.parse("Do something weird")
        assert result["action"] == "general_chat"

    def test_json_embedded_in_text(self):
        raw = 'Sure, here you go: {"action": "open_app", "target": "Notepad"} Done!'
        with self._mock_llm(raw):
            result = self.parser.parse("Open notepad please")
        assert result["action"] == "open_app"

    def test_all_supported_intents_defined(self):
        assert "call" in SUPPORTED_INTENTS
        assert "whatsapp" in SUPPORTED_INTENTS
        assert "messenger" in SUPPORTED_INTENTS
        assert "general_chat" in SUPPORTED_INTENTS
        assert len(SUPPORTED_INTENTS) >= 10

    def test_unknown_action_falls_back(self):
        mock_json = json.dumps({"action": "fly_to_moon"})
        with self._mock_llm(mock_json):
            result = self.parser.parse("Do something impossible")
        assert result["action"] == "general_chat"
