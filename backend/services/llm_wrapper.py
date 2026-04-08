"""LLM backends: Ollama, Groq (OpenAI-compatible), and optional Google Gemini."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Literal

from backend.core.config import get_settings

ChatMessage = dict[str, str]

BackendName = Literal["ollama", "groq", "gemini"]


def ollama_chat(
    messages: list[ChatMessage],
    *,
    base_url: str | None = None,
    model: str | None = None,
    timeout_s: int = 180,
) -> str:
    s = get_settings()
    base = (
        base_url
        or s.ollama_host
        or os.environ.get("OLLAMA_HOST")
        or "http://127.0.0.1:11434"
    ).rstrip("/")
    if not base.startswith("http"):
        base = "http://" + base
    m = model or s.ollama_model or os.environ.get("OLLAMA_MODEL") or "llama3.2"
    url = f"{base}/api/chat"
    payload = json.dumps({"model": m, "messages": messages, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Ollama request failed ({url}). Is `ollama serve` running and model pulled? {e}"
        ) from e
    try:
        return str(data["message"]["content"])
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"Unexpected Ollama response: {data!r}") from e


def groq_chat(
    messages: list[ChatMessage],
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    s = get_settings()
    key = api_key or s.groq_api_key or os.environ.get("GROQ_API_KEY")
    if not key or not key.strip():
        raise RuntimeError("Set GROQ_API_KEY in the environment (or pass api_key=).")
    m = model or s.groq_model or os.environ.get("GROQ_MODEL") or "llama-3.3-70b-versatile"
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("Install Groq client: pip install openai") from e

    client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
    r = client.chat.completions.create(
        model=m,
        messages=messages,
        temperature=0.2,
    )
    choice = r.choices[0].message
    if choice.content is None:
        return ""
    return choice.content


def _messages_to_gemini_prompt(messages: list[ChatMessage]) -> str:
    parts: list[str] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        parts.append(f"[{role}]\n{content}")
    return "\n\n".join(parts)


def gemini_chat(
    messages: list[ChatMessage],
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    s = get_settings()
    key = api_key or s.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not key or not key.strip():
        raise RuntimeError("Set GEMINI_API_KEY in the environment (or pass api_key=).")
    m = model or s.gemini_model or os.environ.get("GEMINI_MODEL") or "gemini-2.0-flash"
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise RuntimeError("Install: pip install google-generativeai") from e

    genai.configure(api_key=key)
    gm = genai.GenerativeModel(m)
    prompt = _messages_to_gemini_prompt(messages)
    r = gm.generate_content(prompt)
    if not r.text:
        return ""
    return r.text


def chat(
    messages: list[ChatMessage],
    *,
    backend: BackendName,
    ollama_base_url: str | None = None,
    ollama_model: str | None = None,
    groq_api_key: str | None = None,
    groq_model: str | None = None,
    gemini_api_key: str | None = None,
    gemini_model: str | None = None,
) -> str:
    if backend == "ollama":
        return ollama_chat(
            messages,
            base_url=ollama_base_url,
            model=ollama_model,
        )
    if backend == "groq":
        return groq_chat(messages, api_key=groq_api_key, model=groq_model)
    if backend == "gemini":
        return gemini_chat(messages, api_key=gemini_api_key, model=gemini_model)
    raise ValueError(f"Unknown backend: {backend}")
