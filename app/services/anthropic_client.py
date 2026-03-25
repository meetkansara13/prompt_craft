"""
app/services/anthropic_client.py
==================================
Groq API client — drop-in replacement for the Anthropic client.
Same class name, same interface: AnthropicClient.complete(system, user)
Nothing else in the project needs to change.

Model used: llama-3.3-70b-versatile
  - Free tier on Groq
  - Very fast (typically 1-3 seconds)
  - Strong instruction following and JSON output
"""

import time
from groq import Groq, AuthenticationError, APITimeoutError, APIStatusError, APIConnectionError

from config.settings import get_config
from app.utils.errors import (
    APIKeyMissingError,
    APIKeyInvalidError,
    AnthropicTimeoutError,
    AnthropicAPIError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
_cfg   = get_config()


class AnthropicClient:
    """
    Groq client with the same interface as the original AnthropicClient.
    Routes and services call this exactly the same way — zero changes needed.

    Usage
    -----
    client = AnthropicClient(api_key="gsk_...")
    text   = client.complete(system="...", user="...")
    """

    def __init__(self, api_key: str) -> None:
        if not api_key or not api_key.strip():
            raise APIKeyMissingError()
        self._client     = Groq(api_key=api_key)
        self._model      = _cfg.GROQ_MODEL
        self._max_tokens = _cfg.GROQ_MAX_TOKENS
        logger.debug("GroqClient initialised | model=%s", self._model)

    def complete(self, system: str, user: str) -> str:
        """
        Send a system + user message to Groq and return the text response.
        Same signature as the original Anthropic version.
        """
        t0 = time.perf_counter()
        logger.info(
            "Groq call | model=%s system_len=%d user_len=%d",
            self._model, len(system), len(user),
        )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
            )

            elapsed = time.perf_counter() - t0
            text    = response.choices[0].message.content or ""
            logger.info(
                "Groq call complete | elapsed=%.2fs output_len=%d",
                elapsed, len(text),
            )
            return text

        except AuthenticationError as exc:
            logger.warning("Groq auth error: %s", exc)
            raise APIKeyInvalidError("Groq API key rejected. Check your key.") from exc

        except APITimeoutError as exc:
            logger.warning("Groq timeout after %.2fs", time.perf_counter() - t0)
            raise AnthropicTimeoutError("Groq request timed out.") from exc

        except APIStatusError as exc:
            logger.error("Groq API status error %s: %s", exc.status_code, exc.message)
            raise AnthropicAPIError(f"Groq error {exc.status_code}: {exc.message}") from exc

        except APIConnectionError as exc:
            logger.error("Groq connection error: %s", exc)
            raise AnthropicAPIError(f"Could not connect to Groq: {exc}") from exc

    @classmethod
    def verify_key(cls, api_key: str) -> bool:
        """
        Verify a Groq API key with a minimal test call.
        Returns True if valid, raises APIKeyInvalidError if not.
        """
        if not api_key or not api_key.strip():
            raise APIKeyInvalidError("No key provided.")
        if not api_key.startswith("gsk_"):
            raise APIKeyInvalidError("Groq key must start with gsk_")
        try:
            test_client = Groq(api_key=api_key)
            test_client.chat.completions.create(
                model=_cfg.GROQ_MODEL,
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}],
            )
            logger.info("Groq API key verified successfully")
            return True
        except AuthenticationError as exc:
            raise APIKeyInvalidError(f"Key rejected by Groq: {exc}") from exc
        except Exception as exc:
            raise AnthropicAPIError(f"Groq verification failed: {exc}") from exc
