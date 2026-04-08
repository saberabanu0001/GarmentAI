"""API + RAG wiring: mock Chroma + LLM so CI does not need a built index or Ollama."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_hr_dashboard(client: TestClient) -> None:
    r = client.get("/api/hr/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert "overview" in body
    assert "auditLog" in body
    assert body["overview"]["workforceTotal"] == 500


def _patch_rag_no_chroma() -> tuple[MagicMock, MagicMock]:
    mock_inst = MagicMock()
    mock_inst.search.return_value = []
    mock_cls = MagicMock(return_value=mock_inst)
    return mock_cls, mock_inst


def test_chat_with_mocked_llm(client: TestClient) -> None:
    mock_cls, mock_inst = _patch_rag_no_chroma()
    with patch("backend.services.rag.ChromaQueryEngine", mock_cls):
        with patch("backend.services.rag.chat", return_value="Mocked garment policy answer."):
            r = client.post(
                "/api/chat",
                json={
                    "question": "What is weekly holiday?",
                    "role": "worker",
                    "top_k": 3,
                },
            )
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "Mocked garment policy answer."
    assert data["hits"] == []
    mock_inst.search.assert_called_once()


def test_rag_legacy_alias(client: TestClient) -> None:
    mock_cls, _ = _patch_rag_no_chroma()
    with patch("backend.services.rag.ChromaQueryEngine", mock_cls):
        with patch("backend.services.rag.chat", return_value="ok"):
            r = client.post(
                "/api/rag",
                json={"question": "test", "role": "worker"},
            )
    assert r.status_code == 200
    assert r.json()["answer"] == "ok"


def test_chat_invalid_role(client: TestClient) -> None:
    r = client.post(
        "/api/chat",
        json={"question": "hello", "role": "not_a_role"},
    )
    assert r.status_code == 400
    err = r.json()
    assert "error" in err
