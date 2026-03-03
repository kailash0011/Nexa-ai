"""
Nexa AI — Auto Reply
Generates smart, context-aware replies when the owner is busy.
"""

from nexa.brain.llm import llm
from nexa.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = """You are Nexa, a personal AI assistant for {owner}.
{owner} is currently busy and has asked you to handle incoming messages.

Generate a polite, concise auto-reply on behalf of {owner}.
The reply should:
- Sound natural and friendly
- Acknowledge the incoming message
- Let them know {owner} is busy
- Promise to get back to them
- Be tailored to the sender's name and message context

Sender: {sender}
Incoming message: "{incoming}"
Busy reason: {busy_reason}

Reply (keep it under 2 sentences):"""


class AutoReply:
    """Generate contextual auto-replies when Nexa's owner is busy."""

    def __init__(self, owner_name: str = "Kailash") -> None:
        self.owner_name = owner_name
        self.custom_message: str = ""

    def set_custom_message(self, message: str) -> None:
        """Set a static custom busy message (overrides AI generation)."""
        self.custom_message = message
        logger.info(f"✉️  Custom busy message set: '{message}'")

    def generate_reply(
        self,
        sender: str = "Someone",
        incoming: str = "",
        busy_reason: str = "busy at the moment",
    ) -> str:
        """
        Generate an auto-reply for an incoming message.

        Args:
            sender: Name of the person messaging.
            incoming: The content of their message.
            busy_reason: Why the owner is busy (optional context).

        Returns:
            Auto-reply string to send back.
        """
        # Use custom message if set
        if self.custom_message:
            return self.custom_message

        prompt = _SYSTEM_PROMPT.format(
            owner=self.owner_name,
            sender=sender,
            incoming=incoming or "a message",
            busy_reason=busy_reason,
        )
        reply = llm.ask(prompt)
        logger.info(f"🤖 Auto-reply generated for {sender}: '{reply}'")
        return reply


# Module-level singleton (owner_name filled in later by assistant.py)
auto_reply = AutoReply()
