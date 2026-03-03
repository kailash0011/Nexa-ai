"""
Tests for nexa/voice — Speaker and Listener (mocked hardware).
"""

from unittest.mock import MagicMock, patch

import pytest

from nexa.voice.listener import Listener, WAKE_WORDS
from nexa.voice.speaker import Speaker


class TestSpeaker:
    """Test the Speaker TTS wrapper (pyttsx3 mocked out)."""

    def test_speak_prints_text(self, capsys):
        """speak() always prints to stdout even without pyttsx3."""
        speaker = Speaker()
        speaker._engine = None  # force no TTS engine
        speaker.speak("Hello Kailash!")
        captured = capsys.readouterr()
        assert "Hello Kailash!" in captured.out

    def test_speak_with_mock_engine(self):
        """speak() calls engine.say and runAndWait when engine is present."""
        mock_engine = MagicMock()
        speaker = Speaker()
        speaker._engine = mock_engine

        with patch("nexa.voice.speaker._PYTTSX3_AVAILABLE", True):
            speaker.speak("Test speech", blocking=True)

        mock_engine.say.assert_called_once_with("Test speech")
        mock_engine.runAndWait.assert_called_once()

    def test_speak_nonblocking_does_not_block(self):
        """Non-blocking speak returns immediately."""
        mock_engine = MagicMock()
        speaker = Speaker()
        speaker._engine = mock_engine

        with patch("nexa.voice.speaker._PYTTSX3_AVAILABLE", True):
            # Should return without raising
            speaker.speak("Background speech", blocking=False)


class TestListener:
    """Test the Listener speech recogniser (hardware mocked out)."""

    def test_wake_word_detection(self):
        listener = Listener()
        assert listener.contains_wake_word("hey nexa open chrome")
        assert listener.contains_wake_word("Nexa what's the time")
        assert not listener.contains_wake_word("open chrome please")

    def test_strip_wake_word(self):
        listener = Listener()
        result = listener.strip_wake_word("hey nexa open chrome")
        assert result == "open chrome"

    def test_strip_wake_word_no_wake_word(self):
        listener = Listener()
        result = listener.strip_wake_word("open chrome")
        assert result == "open chrome"

    def test_wake_words_list(self):
        assert len(WAKE_WORDS) >= 2
        assert "hey nexa" in WAKE_WORDS
        assert "nexa" in WAKE_WORDS

    def test_listen_returns_none_when_unavailable(self):
        """If SpeechRecognition is not available, listen() returns None."""
        listener = Listener()
        listener._recognizer = None
        result = listener.listen(prompt=False)
        assert result is None

    def test_listen_handles_timeout(self):
        """Simulated WaitTimeoutError → returns None."""
        pytest.importorskip("speech_recognition", reason="SpeechRecognition not installed")
        import speech_recognition as sr  # type: ignore

        listener = Listener()
        mock_rec = MagicMock()
        mock_mic = MagicMock()

        with patch("nexa.voice.listener._SR_AVAILABLE", True), \
             patch("nexa.voice.listener.sr.Microphone", return_value=mock_mic), \
             patch.object(mock_rec, "listen", side_effect=sr.WaitTimeoutError):
            listener._recognizer = mock_rec
            mock_mic.__enter__ = MagicMock(return_value=MagicMock())
            mock_mic.__exit__ = MagicMock(return_value=False)
            result = listener.listen(prompt=False)
        # Result is None because WaitTimeoutError is caught
        assert result is None
