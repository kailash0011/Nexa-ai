"""
Nexa AI — Main Entry Point
Starts Nexa and runs the interactive command loop.

Usage:
    python main.py           # auto-detect voice / text mode
    python main.py --text    # force text-only mode (no microphone)
"""

import sys

from config import config
from nexa.assistant import NexaAssistant
from nexa.utils.logger import get_logger
from nexa.voice.listener import get_listener

logger = get_logger(__name__)

# Shutdown commands
EXIT_COMMANDS = {"exit", "quit", "bye nexa", "bye", "goodbye", "shutdown", "stop"}

ASCII_BANNER = r"""
  _   _ _______  _____ ___
 | \ | | ____\ \/ /  _  \
 |  \| |  _|  \  /| |_| |
 | |\  | |___ /  \|  _  /
 |_| \_|_____/_/\_\_| \_\ 

  🤖  Your Personal AI Assistant
"""


def _is_exit(text: str) -> bool:
    """Return True if the text is a shutdown command."""
    return text.lower().strip() in EXIT_COMMANDS


def run_text_mode(nexa: NexaAssistant) -> None:
    """Interactive text-input loop."""
    print("\n💬 Text mode active. Type your command (or 'bye' to exit).\n")
    while True:
        try:
            command = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not command:
            continue

        if _is_exit(command):
            nexa.farewell()
            break

        nexa.execute(command)


def run_voice_mode(nexa: NexaAssistant) -> None:
    """Voice-input loop with text fallback on empty audio."""
    listener = get_listener()
    print("\n🎤 Voice mode active. Say 'Hey Nexa' or just speak your command.")
    print("   Press Ctrl+C to exit.\n")

    while True:
        try:
            text = listener.listen()
        except KeyboardInterrupt:
            break

        if text is None:
            # Nothing heard — silently continue
            continue

        # Strip wake word if present
        command = listener.strip_wake_word(text)
        if not command:
            continue

        if _is_exit(command):
            nexa.farewell()
            break

        nexa.execute(command)


def main() -> None:
    """Entry point — parse flags, start Nexa, enter the command loop."""
    print(ASCII_BANNER)
    print("=" * 50)

    # Force text mode if --text flag or voice is disabled in config
    force_text = "--text" in sys.argv or not config.VOICE_ENABLED

    nexa = NexaAssistant()
    nexa.greet()

    if force_text:
        run_text_mode(nexa)
    else:
        # Try voice mode; fall back to text if no microphone
        try:
            run_voice_mode(nexa)
        except Exception as exc:
            logger.warning(f"Voice mode error: {exc}. Falling back to text mode.")
            run_text_mode(nexa)


if __name__ == "__main__":
    main()
