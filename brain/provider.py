"""LLM provider abstraction — OpenAI-compatible API."""

import json
import urllib.request
import urllib.error
from typing import Optional


class LLMProvider:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(
        self,
        system: str = "",
        messages: Optional[list[dict]] = None,
        timeout: int = 60,
    ) -> str:
        if messages is None:
            messages = []

        body = {
            "model": self.model,
            "messages": [],
        }
        if system:
            body["messages"].append({"role": "system", "content": system})
        body["messages"].extend(messages)

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return f"LLM unavailable (HTTP {e.code}): {e.reason}"
        except urllib.error.URLError as e:
            return f"LLM unavailable: {e.reason}"
        except TimeoutError:
            return "LLM unavailable: request timed out"

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            return f"Failed to parse LLM response: {e}"

        choices = parsed.get("choices", [])
        if not choices:
            return f"LLM returned empty response (no choices)"

        content = choices[0].get("message", {}).get("content", "")
        return content.strip()
