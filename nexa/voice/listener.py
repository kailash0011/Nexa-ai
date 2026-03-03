"""
Nexa AI — Speech Recognition (Listener)
Uses the SpeechRecognition library with Google's free Web Speech API.
"""

from typing import Optional

from nexa.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import speech_recognition as sr  # type: ignore

    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False
    logger.warning(
        "⚠️  SpeechRecognition not installed — voice input disabled. "
        "Run: pip install SpeechRecognition"
    )

# Wake words that trigger Nexa
WAKE_WORDS = ["hey nexa", "nexa", "hey nexa ai"]


class Listener:
    """
    Microphone-based speech recogniser for Nexa.
    Wraps SpeechRecognition with ambient noise adjustment and timeouts.
    """

    def __init__(
        self,
        timeout: int = 5,
        phrase_time_limit: int = 10,
        energy_threshold: int = 300,
    ) -> None:
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        self.energy_threshold = energy_threshold
        self._recognizer: Optional[object] = None

        if _SR_AVAILABLE:
            self._init_recognizer()

    def _init_recognizer(self) -> None:
        """Set up the speech recogniser."""
        try:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = self.energy_threshold
            self._recognizer.dynamic_energy_threshold = True
            logger.info("🎙️  Speech recogniser initialised.")
        except Exception as exc:
            logger.error(f"Recogniser init error: {exc}")
            self._recognizer = None

    def listen(self, prompt: bool = True) -> Optional[str]:
        """
        Listen to the microphone and return the recognised text.

        Args:
            prompt: Print a listening prompt to console (default True).

        Returns:
            Recognised text string, or None if nothing heard / error.
        """
        if not _SR_AVAILABLE or not self._recognizer:
            return None

        if prompt:
            print("\n🎤 Listening... (speak now)")

        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
            text = self._recognizer.recognize_google(audio).strip()
            logger.info(f"🗣️  Heard: '{text}'")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            logger.debug("Could not understand audio.")
            return None
        except sr.RequestError as exc:
            logger.error(f"Google Speech API error: {exc}")
            return None
        except Exception as exc:
            logger.error(f"Listener error: {exc}")
            return None

    def contains_wake_word(self, text: str) -> bool:
        """
        Check whether a piece of text contains a wake word.

        Args:
            text: Recognised text to check.

        Returns:
            True if a wake word is found.
        """
        lower = text.lower()
        return any(word in lower for word in WAKE_WORDS)

    def strip_wake_word(self, text: str) -> str:
        """Remove the wake word prefix from a command string."""
        lower = text.lower()
        for word in WAKE_WORDS:
            if lower.startswith(word):
                return text[len(word):].strip()
        return text


# Module-level singleton
_listener: Optional[Listener] = None


def get_listener() -> Listener:
    """Return (and lazily create) the global Listener instance."""
    global _listener
    if _listener is None:
        _listener = Listener()
    return _listener
