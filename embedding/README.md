# Embedding (compatibility layer)

New code lives under **`backend/`** (`services`, `core`, `api`). This folder keeps **CLI entrypoints** and **import shims** so scripts that used `embedding.*` keep working:

- `build_chroma.py` → `backend.services.chroma_ingest`
- `chroma_query_engine.py` → `backend.services.chroma_engine`
- `rag_answer.py` / `rag_cli.py` → `backend.services.rag`
- `roles.py` → `backend.core.security`
- `llm_client.py` → `backend.services.llm_wrapper`

**Manifest:** [`backend/collection_manifest.yaml`](../backend/collection_manifest.yaml)

**Ingest:** prefer `python scripts/ingest_laws.py` from the repository root.
