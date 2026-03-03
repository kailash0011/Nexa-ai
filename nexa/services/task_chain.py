"""
Nexa AI — Task Chain (AI Agent)
Takes ANY instruction, breaks it into steps using LLM, and executes each step.
This is the core "do anything" engine.
"""

import json
import re
import time
from typing import Any, Optional

from nexa.services.pc_controller import pc_controller
from nexa.utils.logger import get_logger

logger = get_logger(__name__)

# Common action mappings for quick execution without LLM
QUICK_ACTIONS = {
    "open chrome": [{"action": "open_url", "url": "https://www.google.com"}],
    "open google": [{"action": "open_url", "url": "https://www.google.com"}],
    "open youtube": [{"action": "open_url", "url": "https://www.youtube.com"}],
    "open facebook": [{"action": "open_url", "url": "https://www.facebook.com"}],
    "open messenger": [{"action": "open_url", "url": "https://www.messenger.com"}],
    "open instagram": [{"action": "open_url", "url": "https://www.instagram.com"}],
    "open twitter": [{"action": "open_url", "url": "https://x.com"}],
    "open github": [{"action": "open_url", "url": "https://github.com"}],
    "open gmail": [{"action": "open_url", "url": "https://mail.google.com"}],
    "open whatsapp web": [{"action": "open_url", "url": "https://web.whatsapp.com"}],
}

STEP_PLAN_PROMPT = """You are Nexa, a PC automation assistant. Break this user instruction into executable steps.

Available actions:
- open_url: Open a website (params: url)
- open_app: Open a desktop app (params: app_name)
- open_file: Open a file/folder (params: path)
- click: Click at a described location (params: description)
- type_text: Type text (params: text)
- press_key: Press a key (params: key — e.g. enter, tab, escape)
- hotkey: Press key combination (params: keys — e.g. ctrl+c, alt+tab)
- scroll: Scroll up or down (params: direction — up/down, amount)
- wait: Wait for page/app to load (params: seconds)
- search: Type in a search bar (params: query)
- select_text: Select all text (ctrl+a)
- copy: Copy selected text (ctrl+c)
- paste: Paste clipboard (ctrl+v)
- done: Task is complete

User instruction: "{instruction}"

Return ONLY a JSON array of steps. Example:
[
  {{"step": 1, "action": "open_url", "params": {{"url": "https://youtube.com"}}, "description": "Open YouTube"}},
  {{"step": 2, "action": "wait", "params": {{"seconds": 2}}, "description": "Wait for page to load"}},
  {{"step": 3, "action": "click", "params": {{"description": "search bar"}}, "description": "Click the search bar"}},
  {{"step": 4, "action": "type_text", "params": {{"text": "Python tutorial"}}, "description": "Type search query"}},
  {{"step": 5, "action": "press_key", "params": {{"key": "enter"}}, "description": "Press Enter to search"}},
  {{"step": 6, "action": "done", "params": {{}}, "description": "Task complete"}}
]

Return ONLY the JSON array, nothing else:"""

CLICK_LOCATION_PROMPT = """Look at the screenshot and tell me where to click for: "{description}"

The screen resolution is {width}x{height}.

Return ONLY a JSON object with x and y coordinates:
{{"x": 500, "y": 300}}

If you cannot determine the location, return:
{{"x": -1, "y": -1, "fallback": "description of what to try instead"}}
"""


class TaskChain:
    """
    AI Agent that can execute ANY multi-step instruction.
    Uses LLM to plan steps, then executes them using PC automation.
    """

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            from nexa.brain.llm import llm
            self._llm = llm
        return self._llm

    def execute_instruction(self, instruction: str, speak_fn=None) -> str:
        """
        Execute ANY user instruction by:
        1. Breaking it into steps (keyword match or LLM)
        2. Executing each step using PC automation
        """
        logger.info(f"⛓️ Task chain starting: '{instruction}'")
        if speak_fn:
            speak_fn(f"On it! Let me do that for you.")

        # Step 1: Check quick actions first (instant)
        steps = self._quick_match(instruction)

        # Step 2: If no quick match, use LLM to plan
        if not steps:
            steps = self._plan_with_llm(instruction)

        if not steps:
            return "I couldn't figure out how to do that. Can you break it into simpler steps?"

        # Step 3: Execute each step
        results = []
        for i, step in enumerate(steps):
            action = step.get("action", "")
            params = step.get("params", {})
            desc = step.get("description", f"Step {i+1}")

            logger.info(f"⛓️ Step {i+1}/{len(steps)}: {desc}")
            if speak_fn and i == 0:
                speak_fn(f"Step 1: {desc}")

            success = self._execute_step(action, params)
            results.append({"step": i+1, "description": desc, "success": success})

            if action == "done":
                break

            # Small delay between steps for stability
            time.sleep(0.5)

        # Summary
        total = len(results)
        succeeded = sum(1 for r in results if r["success"])
        summary = f"Completed {succeeded}/{total} steps."
        if succeeded == total:
            summary = f"All done! Completed all {total} steps successfully."

        logger.info(f"⛓️ {summary}")
        return summary

    def _quick_match(self, instruction: str) -> Optional[list]:
        """Check for common instructions that don't need LLM planning."""
        lower = instruction.lower().strip()

        # Direct URL/website matches
        for key, steps in QUICK_ACTIONS.items():
            if key in lower:
                return steps + [{"action": "wait", "params": {"seconds": 2}, "description": "Wait for page"}]

        # "Open [file/folder path]" pattern
        path_match = re.search(
            r'open\s+(?:the\s+)?(?:file\s+|folder\s+)?["\']?([a-zA-Z]:\\[^"\']+|/[^"\']+)["\']?',
            instruction,
            re.IGNORECASE,
        )
        if path_match:
            return [
                {"action": "open_file", "params": {"path": path_match.group(1).strip()}, "description": f"Open {path_match.group(1)}"},
                {"action": "done", "params": {}, "description": "Done"},
            ]

        # "Search [query] on YouTube/Google" pattern
        search_match = re.search(r'search\s+(?:for\s+)?["\']?(.+?)["\']?\s+on\s+(youtube|google)', lower)
        if search_match:
            query = search_match.group(1)
            site = search_match.group(2)
            if site == "youtube":
                url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            else:
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            return [
                {"action": "open_url", "params": {"url": url}, "description": f"Search '{query}' on {site}"},
                {"action": "done", "params": {}, "description": "Done"},
            ]

        # "Go to [website]" pattern
        go_match = re.search(
            r'(?:go to|visit|navigate to|open)\s+(?:the\s+)?(?:website\s+)?([a-zA-Z0-9][\w.-]+\.[a-zA-Z]{2,})',
            lower,
        )
        if go_match:
            domain = go_match.group(1)
            url = domain if domain.startswith("http") else f"https://{domain}"
            return [
                {"action": "open_url", "params": {"url": url}, "description": f"Go to {domain}"},
                {"action": "wait", "params": {"seconds": 2}, "description": "Wait for page"},
                {"action": "done", "params": {}, "description": "Done"},
            ]

        return None

    def _plan_with_llm(self, instruction: str) -> Optional[list]:
        """Use LLM to break instruction into executable steps."""
        try:
            prompt = STEP_PLAN_PROMPT.format(instruction=instruction)
            raw = self._get_llm().ask(prompt)
            steps = self._extract_json_array(raw)
            if steps:
                logger.info(f"🧠 LLM planned {len(steps)} steps")
                return steps
        except Exception as exc:
            logger.error(f"LLM planning error: {exc}")
        return None

    def _execute_step(self, action: str, params: dict) -> bool:
        """Execute a single automation step."""
        try:
            if action == "open_url":
                url = params.get("url", "")
                return pc_controller.open_url(url)

            elif action == "open_app":
                app = params.get("app_name", "")
                from nexa.services.app_launcher import app_launcher
                return app_launcher.open_app(app)

            elif action == "open_file":
                path = params.get("path", "")
                return pc_controller.open_path(path)

            elif action in ("type_text", "search"):
                text = params.get("text", params.get("query", ""))
                pc_controller.wait(0.3)
                return pc_controller.type_text(text)

            elif action == "press_key":
                key = params.get("key", "enter")
                return pc_controller.press_key(key)

            elif action == "hotkey":
                keys_str = params.get("keys", "")
                keys = [k.strip() for k in keys_str.split("+")]
                return pc_controller.hotkey(*keys)

            elif action == "click":
                # If x,y provided, use them
                x = params.get("x")
                y = params.get("y")
                if x is not None and y is not None and x >= 0 and y >= 0:
                    return pc_controller.click(int(x), int(y))
                # Otherwise try to find by description
                desc = params.get("description", "")
                logger.info(f"🖱️ Need to find: '{desc}' — trying search bar shortcut")
                # Common shortcuts for known UI elements
                if "search" in desc.lower() or "address" in desc.lower():
                    return pc_controller.hotkey("ctrl", "l") or pc_controller.press_key("tab")
                elif "compose" in desc.lower() or "new" in desc.lower():
                    return pc_controller.hotkey("ctrl", "n")
                return True  # Skip unknown clicks gracefully

            elif action == "scroll":
                direction = params.get("direction", "down")
                amount = int(params.get("amount", 3))
                return pc_controller.scroll(-amount if direction == "down" else amount)

            elif action == "wait":
                seconds = float(params.get("seconds", 1))
                pc_controller.wait(seconds)
                return True

            elif action == "select_text":
                return pc_controller.select_all()

            elif action == "copy":
                return pc_controller.copy()

            elif action == "paste":
                return pc_controller.paste()

            elif action == "done":
                return True

            else:
                logger.warning(f"Unknown action: {action}")
                return True  # Don't fail on unknown actions

        except Exception as exc:
            logger.error(f"Step execution error: {action} — {exc}")
            return False

    def _extract_json_array(self, text: str) -> Optional[list]:
        """Extract a JSON array from LLM response text."""
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None


task_chain = TaskChain()
