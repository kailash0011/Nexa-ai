"""
Nexa AI — LLM Integration
Primary: Ollama (local, free) with Phi-3 model.
Fallback: Google Gemini free API, then Groq free API.
"""

import json
from typing import Any

import requests

from config import config
from nexa.utils.logger import get_logger

logger = get_logger(__name__)

# Gemini and Groq are optional imports — handled gracefully
try:
    import google.generativeai as genai  # type: ignore

    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

try:
    from groq import Groq  # type: ignore

    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False


class LLMClient:
    """
    AI brain for Nexa.  Tries backends in order:
    1. Ollama (local Phi-3)
    2. Google Gemini (free tier)
    3. Groq (free tier)
    """

    def __init__(self) -> None:
        self._backend: str = self._detect_backend()
        logger.info(f"🧠 LLM backend selected: {self._backend}")

    # ------------------------------------------------------------------
    # Backend detection
    # ------------------------------------------------------------------

    def _detect_backend(self) -> str:
        """Return the first available backend."""
        if self._ollama_alive():
            return "ollama"
        if config.GEMINI_API_KEY and _GEMINI_AVAILABLE:
            return "gemini"
        if config.GROQ_API_KEY and _GROQ_AVAILABLE:
            return "groq"
        logger.warning("⚠️  No LLM backend available — responses will be limited.")
        return "none"

    def _ollama_alive(self) -> bool:
        """Check whether the Ollama server is reachable."""
        try:
            resp = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ask(self, prompt: str) -> str:
        """
        Send a single prompt and return the text response.

        Args:
            prompt: The user prompt string.

        Returns:
            Model response as a string.
        """
        if self._backend == "ollama":
            return self._ollama_generate(prompt)
        if self._backend == "gemini":
            return self._gemini_generate(prompt)
        if self._backend == "groq":
            return self._groq_generate(prompt)
        return "I'm sorry, no AI backend is available right now."

    def chat(self, messages: list[dict[str, str]]) -> str:
        """
        Multi-turn conversation interface.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."} dicts.

        Returns:
            Model response as a string.
        """
        if self._backend == "ollama":
            return self._ollama_chat(messages)
        if self._backend == "gemini":
            # Flatten to a single prompt for Gemini free tier
            flat = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
            return self._gemini_generate(flat)
        if self._backend == "groq":
            return self._groq_chat(messages)
        return "I'm sorry, no AI backend is available right now."

    # ------------------------------------------------------------------
    # Ollama backend
    # ------------------------------------------------------------------

    def _ollama_generate(self, prompt: str) -> str:
        try:
            payload: dict[str, Any] = {
                "model": config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            }
            resp = requests.post(
                f"{config.OLLAMA_URL}/api/generate",
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except Exception as exc:
            logger.error(f"Ollama generate error: {exc}")
            return "Error communicating with Ollama."

    def _ollama_chat(self, messages: list[dict[str, str]]) -> str:
        try:
            payload: dict[str, Any] = {
                "model": config.OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
            }
            resp = requests.post(
                f"{config.OLLAMA_URL}/api/chat",
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "").strip()
        except Exception as exc:
            logger.error(f"Ollama chat error: {exc}")
            return "Error communicating with Ollama."

    # ------------------------------------------------------------------
    # Gemini backend
    # ------------------------------------------------------------------

    def _gemini_generate(self, prompt: str) -> str:
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.error(f"Gemini error: {exc}")
            return "Error communicating with Gemini."

    # ------------------------------------------------------------------
    # Groq backend
    # ------------------------------------------------------------------

    def _groq_generate(self, prompt: str) -> str:
        return self._groq_chat([{"role": "user", "content": prompt}])

    def _groq_chat(self, messages: list[dict[str, str]]) -> str:
        try:
            client = Groq(api_key=config.GROQ_API_KEY)
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=messages,  # type: ignore[arg-type]
            )
            return completion.choices[0].message.content.strip()
        except Exception as exc:
            logger.error(f"Groq error: {exc}")
            return "Error communicating with Groq."


# Module-level singleton
llm = LLMClient()
