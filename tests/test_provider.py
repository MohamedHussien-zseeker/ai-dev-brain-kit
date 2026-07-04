"""Tests for brain/provider.py — LLM provider abstraction."""

import json
from unittest.mock import patch, MagicMock
from urllib.error import URLError, HTTPError

from brain.provider import LLMProvider


def _provider(**kw):
    defaults = dict(api_key="sk-test", base_url="https://api.test.com/v1", model="gpt-4o")
    defaults.update(kw)
    return LLMProvider(**defaults)


def test_complete_returns_text():
    p = _provider()
    fake_response = {
        "choices": [{"message": {"content": "Hello, world!"}}]
    }
    with patch("urllib.request.urlopen") as mock_urlopen:
        cm = MagicMock()
        cm.read.return_value = json.dumps(fake_response).encode()
        cm.__enter__.return_value = cm
        mock_urlopen.return_value = cm
        result = p.complete(system="Be helpful", messages=[{"role": "user", "content": "Hi"}])
    assert result == "Hello, world!"


def test_complete_posts_correct_payload():
    p = _provider()
    with patch("urllib.request.urlopen") as mock_urlopen:
        cm = MagicMock()
        cm.read.return_value = json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()
        cm.__enter__.return_value = cm
        mock_urlopen.return_value = cm
        p.complete(system="Sys msg", messages=[{"role": "user", "content": "Q"}])

    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == "https://api.test.com/v1/chat/completions"
    assert req.get_header("Authorization") == "Bearer sk-test"
    body = json.loads(req.data)
    assert body["model"] == "gpt-4o"
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][0]["content"] == "Sys msg"


def test_network_error_returns_graceful_message():
    p = _provider()
    with patch("urllib.request.urlopen", side_effect=URLError("connection refused")):
        result = p.complete(system="", messages=[])
    assert result.startswith("LLM unavailable")
    assert "connection refused" in result


def test_auth_error_reported():
    p = _provider()
    with patch("urllib.request.urlopen", side_effect=HTTPError(
            "https://api.test.com/v1/chat/completions", 401, "Unauthorized", {}, None
    )):
        result = p.complete(system="", messages=[])
    assert result.startswith("LLM unavailable (HTTP 401)")


def test_empty_choices_returns_fallback():
    p = _provider()
    with patch("urllib.request.urlopen") as mock_urlopen:
        cm = MagicMock()
        cm.read.return_value = json.dumps({"choices": []}).encode()
        cm.__enter__.return_value = cm
        mock_urlopen.return_value = cm
        result = p.complete(system="", messages=[])
    assert result.startswith("LLM returned empty response")


def test_malformed_response_returns_graceful():
    p = _provider()
    with patch("urllib.request.urlopen") as mock_urlopen:
        cm = MagicMock()
        cm.read.return_value = b"not json"
        cm.__enter__.return_value = cm
        mock_urlopen.return_value = cm
        result = p.complete(system="", messages=[])
    assert result.startswith("Failed to parse LLM response")


def test_default_base_url():
    p = LLMProvider(api_key="sk-test")
    assert "openai.com" in p.base_url


def test_default_model():
    p = LLMProvider(api_key="sk-test")
    assert p.model == "gpt-4o"


def test_custom_provider_url():
    p = LLMProvider(api_key="sk-test", base_url="https://custom.ai/v1", model="claude-3-haiku")
    assert p.base_url == "https://custom.ai/v1"
    assert p.model == "claude-3-haiku"
