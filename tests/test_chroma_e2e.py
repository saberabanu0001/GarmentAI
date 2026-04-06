"""
Optional E2E: Chroma + E5 + RBAC. Run locally after:
  pip install -r requirements.txt
  python embedding/build_chroma.py

  pytest tests/test_chroma_e2e.py -m e2e
or:
  RUN_E2E=1 pytest tests/test_chroma_e2e.py -m e2e
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = REPO_ROOT / "embedding" / "chroma_data"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "e2e: needs GPU/CPU E2E with built Chroma index (set RUN_E2E=1)",
    )


def _e2e_enabled() -> bool:
    return os.environ.get("RUN_E2E", "").strip() in ("1", "true", "yes")


@pytest.mark.e2e
@pytest.mark.skipif(not _e2e_enabled(), reason="set RUN_E2E=1 to run")
def test_worker_never_sees_risky_hr_chunk() -> None:
    from embedding.chroma_query_engine import ChromaQueryEngine
    from embedding.roles import Role

    if not (CHROMA_DIR / "meta.json").is_file():
        pytest.skip(f"Build Chroma first: python embedding/build_chroma.py ({CHROMA_DIR})")

    engine = ChromaQueryEngine(CHROMA_DIR)
    # Query crafted to match dummy HR chunk keywords.
    hits = engine.search(
        "salary deduction show cause payroll hold disciplinary",
        role=Role.WORKER,
        factory_id="risky",
        top_k=10,
    )
    for h in hits:
        assert not h.chunk_uid.startswith(
            "risky:"
        ), f"worker must not retrieve tenant HR chunk: {h.chunk_uid!r}"


@pytest.mark.e2e
@pytest.mark.skipif(not _e2e_enabled(), reason="set RUN_E2E=1 to run")
def test_hr_sees_risky_hr_chunk() -> None:
    from embedding.chroma_query_engine import ChromaQueryEngine
    from embedding.roles import Role

    if not (CHROMA_DIR / "meta.json").is_file():
        pytest.skip(f"Build Chroma first ({CHROMA_DIR})")

    engine = ChromaQueryEngine(CHROMA_DIR)
    hits = engine.search(
        "salary deduction show cause payroll hold",
        role=Role.HR_STAFF,
        factory_id="risky",
        top_k=10,
    )
    assert any(
        h.chunk_uid.startswith("risky:") for h in hits
    ), "HR staff should retrieve risky tenant HR chunk when relevant"


@pytest.mark.e2e
@pytest.mark.skipif(not _e2e_enabled(), reason="set RUN_E2E=1 to run")
@pytest.mark.parametrize(
    "query",
    [
        "সাপ্তাহিক ছুটি কত দিন?",
        "ওভারটাইম ভাতা কীভাবে হিসাব হয়?",
        "মaternal ছুটি কত দিন?",
        "ন্যূনতম মজুরি সম্পর্কে জানতে চাই",
        "ট্রেড ইউনিয়ন গঠন করার অধিকার আছে কি?",
    ],
)
def test_bangla_queries_return_hits(query: str) -> None:
    from embedding.chroma_query_engine import ChromaQueryEngine
    from embedding.roles import Role

    if not (CHROMA_DIR / "meta.json").is_file():
        pytest.skip(f"Build Chroma first ({CHROMA_DIR})")

    engine = ChromaQueryEngine(CHROMA_DIR)
    hits = engine.search(query, role=Role.WORKER, factory_id="", top_k=3)
    assert hits, f"no hits for {query!r}"
