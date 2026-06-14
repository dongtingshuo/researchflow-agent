"""OpenAI-compatible chat completion client."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    """One chat message for the LLM API."""

    role: str
    content: str


class LLMClientError(RuntimeError):
    """Raised when the LLM API call fails."""


class OpenAICompatibleClient:
    """Minimal OpenAI-compatible chat completions client using the standard library."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: int = 60,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def chat(self, messages: list[ChatMessage]) -> str:
        """Call an OpenAI-compatible /chat/completions endpoint."""
        if not self.api_key:
            raise LLMClientError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "messages": [message.__dict__ for message in messages],
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout_seconds
            ) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LLMClientError(f"LLM API returned HTTP {exc.code}: {detail}") from exc
        except Exception as exc:
            raise LLMClientError(f"LLM API request failed: {exc}") from exc

        try:
            parsed = json.loads(body)
            return parsed["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise LLMClientError("LLM API returned an unexpected response.") from exc
