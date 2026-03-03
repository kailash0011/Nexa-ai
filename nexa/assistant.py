"""
Nexa AI — Main Orchestrator
The NexaAssistant class ties all modules together and routes commands
to the appropriate service.
"""

import threading
from typing import Any, Optional

from config import config
from nexa.brain.auto_reply import AutoReply, auto_reply
from nexa.brain.intent_parser import intent_parser
from nexa.brain.llm import llm
from nexa.contacts.manager import contact_manager
from nexa.integrations.messenger import messenger
from nexa.integrations.phone_call import phone
from nexa.integrations.whatsapp import whatsapp
from nexa.services.app_launcher import app_launcher
from nexa.services.file_manager import file_manager
from nexa.services.scheduler import scheduler
from nexa.services.system_monitor import system_monitor
from nexa.services.task_chain import task_chain
from nexa.utils.logger import get_logger
from nexa.voice.speaker import get_speaker

logger = get_logger(__name__)


class NexaAssistant:
    """
    Central AI assistant that orchestrates all Nexa modules.

    Usage::

        nexa = NexaAssistant()
        nexa.execute("Open Chrome")
        nexa.execute("Send WhatsApp to Ram - I'm on my way")
    """

    def __init__(self) -> None:
        self.owner = config.OWNER_NAME
        self.is_busy = config.BUSY_MODE
        self.busy_reason = "busy at the moment"
        self._conversation_history: list[dict[str, str]] = []
        self._current_tasks: list[str] = []

        # Initialise speaker
        self._speaker = get_speaker(
            speed=config.VOICE_SPEED,
            gender=config.VOICE_GENDER,
        )

        # Configure auto-reply with owner name
        auto_reply.owner_name = self.owner

        # Start background scheduler
        scheduler.start()

        logger.info(f"🤖 Nexa initialised for {self.owner}")

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    def execute(self, command: str) -> str:
        """
        Parse and execute a text command, then return Nexa's response.

        Args:
            command: Natural-language user command.

        Returns:
            Response string (also spoken aloud if voice is enabled).
        """
        logger.info(f"👤 Command: '{command}'")

        # Parse intent
        intent = intent_parser.parse(command)
        action = intent.get("action", "general_chat")
        target = intent.get("target", "")
        message = intent.get("message", "")
        platform = intent.get("platform", "")
        duration = intent.get("duration", "")
        time_str = intent.get("time", "")

        response = self._dispatch(
            action=action,
            target=target,
            message=message,
            platform=platform,
            duration=duration,
            time_str=time_str,
            raw_command=command,
        )

        self._speak(response)
        # Store turn in conversation history
        self._conversation_history.append({"role": "user", "content": command})
        self._conversation_history.append({"role": "assistant", "content": response})
        return response

    # ------------------------------------------------------------------
    # Intent dispatcher
    # ------------------------------------------------------------------

    def _dispatch(
        self,
        action: str,
        target: str,
        message: str,
        platform: str,
        duration: str,
        time_str: str,
        raw_command: str,
    ) -> str:
        """Route a parsed intent to the correct handler."""
        if action == "call":
            return self._handle_call(target, message)

        if action in ("message", "sms"):
            return self._handle_sms(target, message)

        if action == "whatsapp":
            return self._handle_whatsapp(target, message)

        if action == "messenger":
            return self._handle_messenger(target, message)

        if action == "open_app":
            return self._handle_open_app(target)

        if action == "close_app":
            return self._handle_close_app(target)

        if action == "search_file":
            return self._handle_search_file(target)

        if action == "open_file":
            return self._handle_open_file(target)

        if action == "system_info":
            return self._handle_system_info()

        if action == "set_reminder":
            return self._handle_set_reminder(message or target, time_str)

        if action == "set_busy":
            return self._handle_set_busy(duration)

        if action == "web_search":
            return self._handle_task_chain(target or raw_command)

        if action in ("multi_step", "browse", "login"):
            return self._handle_task_chain(target or raw_command)

        # If command looks like an instruction, try task_chain before general chat
        instruction_verbs = [
            "open", "go to", "search", "click", "type", "login", "send",
            "create", "download", "navigate", "visit", "close", "copy",
            "paste", "move", "delete",
        ]
        if any(verb in raw_command.lower() for verb in instruction_verbs):
            return self._handle_task_chain(raw_command)

        # Default: general chat
        return self._handle_general_chat(raw_command)

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _handle_call(self, target: str, message: str) -> str:
        contact = contact_manager.get_contact(target)
        if not contact:
            return f"I couldn't find {target} in your contacts. Please add them first."
        phone_number = contact.get("phone", "")
        if config.ADB_ENABLED:
            if message:
                phone.send_sms(phone_number, message)
                return f"📞 Calling {contact['name']}… and sent a message: '{message}'"
            phone.make_call(phone_number)
            return f"📞 Calling {contact['name']}…"
        return f"ADB is disabled. To call {contact['name']} manually, dial {phone_number}."

    def _handle_sms(self, target: str, message: str) -> str:
        contact = contact_manager.get_contact(target)
        if not contact:
            return f"Contact '{target}' not found."
        phone_number = contact.get("phone", "")
        success = phone.send_sms(phone_number, message)
        return (
            f"💬 SMS sent to {contact['name']}: '{message}' ✅"
            if success
            else f"❌ Failed to send SMS to {contact['name']}."
        )

    def _handle_whatsapp(self, target: str, message: str) -> str:
        contact = contact_manager.get_contact(target)
        if not contact:
            return f"Contact '{target}' not found."
        phone_number = contact.get("phone", "")
        success = whatsapp.send_message_instantly(phone_number, message)
        return (
            f"✅ WhatsApp message sent to {contact['name']}: '{message}'"
            if success
            else f"❌ Failed to send WhatsApp to {contact['name']}."
        )

    def _handle_messenger(self, target: str, message: str) -> str:
        success = messenger.send_message(target, message)
        return (
            f"✅ Messenger message sent to {target}: '{message}'"
            if success
            else f"❌ Failed to send Messenger message to {target}."
        )

    def _handle_open_app(self, target: str) -> str:
        success = app_launcher.open_app(target)
        return (
            f"🚀 Opening {target}… ✅"
            if success
            else f"❌ Could not open '{target}'. Make sure it is installed."
        )

    def _handle_close_app(self, target: str) -> str:
        success = app_launcher.close_app(target)
        return (
            f"💀 Closed {target} ✅"
            if success
            else f"❌ Could not find a running process for '{target}'."
        )

    def _handle_search_file(self, target: str) -> str:
        results = file_manager.search_files(target)
        if not results:
            return f"No files found matching '{target}'."
        top = results[:5]
        listed = "\n  ".join(top)
        suffix = f"\n  … and {len(results) - 5} more." if len(results) > 5 else ""
        return f"🔍 Found {len(results)} file(s) matching '{target}':\n  {listed}{suffix}"

    def _handle_open_file(self, target: str) -> str:
        success = file_manager.open_file(target)
        return f"📂 Opened '{target}' ✅" if success else f"❌ Could not open '{target}'."

    def _handle_system_info(self) -> str:
        return f"🖥️  {system_monitor.get_system_info()}"

    def _handle_set_reminder(self, message: str, time_str: str) -> str:
        if not time_str:
            return "Please specify when to remind you (e.g. 'in 10 minutes' or 'at 3pm')."
        rid = scheduler.set_reminder(message, time_str, callback=self._on_reminder)
        if rid:
            return f"⏰ Reminder set: '{message}' — I'll remind you {time_str} (ID: {rid})"
        return f"❌ Could not parse time '{time_str}'. Try 'in 10 minutes' or '3pm'."

    def _handle_set_busy(self, duration: str) -> str:
        self.set_busy(True, duration)
        msg = f"for {duration}" if duration else "until further notice"
        return f"🔕 Busy mode ON {msg}. I'll handle your messages!"

    def _handle_web_search(self, query: str) -> str:
        import webbrowser
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"🌐 Searching the web for: '{query}'"

    def _handle_task_chain(self, command: str) -> str:
        """Handle complex multi-step commands using task chain AI agent."""
        return task_chain.execute_instruction(command, speak_fn=self._speak)

    def _handle_general_chat(self, command: str) -> str:
        # Use conversation history for context
        messages = self._conversation_history[-10:] + [
            {"role": "user", "content": command}
        ]
        return llm.chat(messages)

    # ------------------------------------------------------------------
    # Busy mode
    # ------------------------------------------------------------------

    def set_busy(self, busy: bool, duration: str = "") -> None:
        """
        Enable or disable busy/auto-reply mode.

        Args:
            busy: True to activate busy mode, False to deactivate.
            duration: How long (for logging/display purposes).
        """
        self.is_busy = busy
        if busy:
            self.busy_reason = f"busy{' for ' + duration if duration else ''}"
            logger.info(f"🔕 Busy mode ON{' for ' + duration if duration else ''}")
            if duration:
                # Auto-disable after the duration
                from nexa.services.scheduler import scheduler as _sched
                _sched.set_reminder(
                    "Busy mode auto-disabled",
                    duration,
                    callback=lambda _: self.set_busy(False),
                )
        else:
            logger.info("🔔 Busy mode OFF")

    # ------------------------------------------------------------------
    # Voice helper
    # ------------------------------------------------------------------

    def _speak(self, text: str) -> None:
        """Speak text if voice is enabled."""
        if config.VOICE_ENABLED:
            self._speaker.speak(text)
        else:
            print(f"🤖 Nexa: {text}")

    # ------------------------------------------------------------------
    # Reminder callback
    # ------------------------------------------------------------------

    def _on_reminder(self, message: str) -> None:
        """Called by the scheduler when a reminder fires."""
        response = f"🔔 Reminder: {message}"
        self._speak(response)

    # ------------------------------------------------------------------
    # Greeting
    # ------------------------------------------------------------------

    def greet(self) -> str:
        """Return (and speak) a startup greeting."""
        greeting = (
            f"Hello {self.owner}! I am Nexa, your personal AI assistant. "
            "How can I help you?"
        )
        self._speak(greeting)
        return greeting

    def farewell(self) -> str:
        """Return (and speak) a goodbye message."""
        msg = f"Goodbye {self.owner}! I'll be here when you need me. 👋"
        self._speak(msg)
        scheduler.stop()
        return msg
