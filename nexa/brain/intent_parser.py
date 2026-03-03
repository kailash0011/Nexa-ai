"""
Nexa AI — Intent Parser
Converts natural-language commands into structured JSON action objects
using the LLM backend.
"""

import json
import re
from typing import Any

from nexa.brain.llm import llm
from nexa.utils.logger import get_logger

logger = get_logger(__name__)

# Canonical list of supported intents
SUPPORTED_INTENTS = [
    "call",
    "message",
    "whatsapp",
    "messenger",
    "open_app",
    "close_app",
    "search_file",
    "open_file",
    "system_info",
    "set_reminder",
    "set_busy",
    "web_search",
    "general_chat",
]

_SYSTEM_PROMPT = """You are an intent parser for the Nexa AI assistant.
Your job is to convert user commands into a structured JSON object.

Return ONLY a valid JSON object with the following keys (omit unused keys):
- "action": one of {intents}
- "target": the contact name, app name, file name, or query (string)
- "message": the message text to send (string)
- "platform": "phone", "whatsapp", "messenger", or "sms"
- "duration": time duration string (e.g. "2 hours", "30 minutes")
- "time": time string for reminders (e.g. "3pm", "in 10 minutes")

Examples:
User: "Call Ram and tell him I'm busy"
Response: {{"action": "call", "target": "Ram", "message": "I'm busy"}}

User: "Send WhatsApp to Sandhya - I will call you later"
Response: {{"action": "whatsapp", "target": "Sandhya", "message": "I will call you later"}}

User: "Open Chrome"
Response: {{"action": "open_app", "target": "Chrome"}}

User: "What's my system status"
Response: {{"action": "system_info"}}

User: "I'm busy for 2 hours"
Response: {{"action": "set_busy", "duration": "2 hours"}}

User: "Remind me to call mom at 3pm"
Response: {{"action": "set_reminder", "message": "call mom", "time": "3pm"}}

User: "Search for report.pdf"
Response: {{"action": "search_file", "target": "report.pdf"}}

User command: "{{command}}"
Response:""".format(
    intents=", ".join(SUPPORTED_INTENTS)
)


class IntentParser:
    """Parse natural language commands into structured action dicts."""

    def parse(self, command: str) -> dict[str, Any]:
        """
        Parse a user command into a structured action dictionary.

        Args:
            command: Raw user text command.

        Returns:
            Dict with at minimum an "action" key, e.g.:
            {"action": "call", "target": "Ram", "message": "boss is busy"}
        """
        prompt = _SYSTEM_PROMPT.replace("{command}", command)
        raw = llm.ask(prompt)

        result = self._extract_json(raw)
        if not result:
            logger.warning(f"Could not parse intent from: '{command}' — falling back to general_chat")
            return {"action": "general_chat", "target": command}

        # Ensure action is valid
        action = result.get("action", "general_chat")
        if action not in SUPPORTED_INTENTS:
            result["action"] = "general_chat"

        logger.info(f"🎯 Intent parsed: {result}")
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """Try to extract the first JSON object from a raw LLM response."""
        # Try direct parse first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Extract JSON block using regex
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None


# Module-level singleton
intent_parser = IntentParser()
