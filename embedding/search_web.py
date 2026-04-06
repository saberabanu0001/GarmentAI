#!/usr/bin/env python3
"""
Minimal local web UI to test QueryEngine.search().

From repo root (with venv active):
  pip install -r requirements.txt
  python embedding/search_web.py
  python embedding/search_web.py --port 8766   # if 8765 is already in use

Open http://127.0.0.1:8765 (or the port you pass). Run one command per line in the shell; do not paste comment lines like "# or".
"""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

from flask import Flask, request

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from embedding.query_engine import QueryEngine  # noqa: E402

app = Flask(__name__)
_engine: QueryEngine | None = None


def get_engine() -> QueryEngine:
    global _engine
    if _engine is None:
        _engine = QueryEngine()
    return _engine


def _page(q: str, top_k: int, body: str) -> str:
    q_esc = html.escape(q)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>KB search test</title>
  <style>
    :root {{
      --bg: #0f1419;
      --card: #1a2332;
      --text: #e7ecf3;
      --muted: #8b9cb3;
      --accent: #3d9ee6;
      --border: #2a3544;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: ui-sans-serif, system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 1.25rem;
      line-height: 1.45;
      max-width: 52rem;
      margin-left: auto;
      margin-right: auto;
    }}
    h1 {{ font-size: 1.25rem; font-weight: 600; margin: 0 0 0.5rem; }}
    p.lead {{ color: var(--muted); font-size: 0.9rem; margin: 0 0 1rem; }}
    form {{ display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin-bottom: 1.25rem; }}
    input[type="text"] {{
      flex: 1 1 12rem;
      min-width: 0;
      padding: 0.55rem 0.75rem;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--card);
      color: var(--text);
      font-size: 1rem;
    }}
    input[type="number"] {{
      width: 4rem;
      padding: 0.55rem;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--card);
      color: var(--text);
    }}
    button {{
      padding: 0.55rem 1rem;
      border: none;
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      font-weight: 600;
      cursor: pointer;
    }}
    button:hover {{ filter: brightness(1.08); }}
    .err {{
      background: #3a2020;
      border: 1px solid #6b3030;
      color: #f0c0c0;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      margin-bottom: 1rem;
      white-space: pre-wrap;
    }}
    .hit {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem;
      margin-bottom: 0.75rem;
    }}
    .hit-meta {{ font-size: 0.8rem; color: var(--muted); margin-bottom: 0.35rem; }}
    .hit-score {{ color: var(--accent); font-weight: 600; }}
    .hit-text {{ font-size: 0.92rem; margin-top: 0.5rem; white-space: pre-wrap; word-break: break-word; }}
    .empty {{ color: var(--muted); }}
    code {{ font-size: 0.85em; }}
  </style>
</head>
<body>
  <h1>Knowledge base search (test)</h1>
  <p class="lead">E5 multilingual — same index as <code>query_engine.py</code>. Binds to 127.0.0.1 only.</p>
  <form method="get" action="/">
    <input type="text" name="q" placeholder="Ask in English or Bangla…" value="{q_esc}" autofocus />
    <label>Top <input type="number" name="top_k" min="1" max="20" value="{top_k}" /></label>
    <button type="submit">Search</button>
  </form>
  {body}
</body>
</html>"""


@app.get("/")
def index():
    q = (request.args.get("q") or "").strip()
    try:
        top_k = int(request.args.get("top_k") or "5")
    except ValueError:
        top_k = 5
    top_k = max(1, min(top_k, 20))

    body_parts: list[str] = []
    if q:
        try:
            hits = get_engine().search(q, top_k=top_k)
            if not hits:
                body_parts.append('<p class="empty">No results.</p>')
            for h in hits:
                body_parts.append(
                    '<article class="hit">'
                    f'<div class="hit-meta"><span class="hit-score">#{h.rank} · score {h.score:.4f}</span>'
                    f" · {html.escape(h.source_name)} — {html.escape(h.document_name)}</div>"
                    f'<div class="hit-meta">{html.escape(h.section)}</div>'
                    f'<div class="hit-meta">{html.escape(h.chunks_file)} · chunk {h.chunk_id}</div>'
                    f'<div class="hit-text">{html.escape(h.text)}</div></article>'
                )
        except Exception as e:
            body_parts.append(f'<div class="err">{html.escape(str(e))}</div>')

    body = "\n  ".join(body_parts)
    return _page(q, top_k, body), 200, {"Content-Type": "text/html; charset=utf-8"}


def main() -> None:
    p = argparse.ArgumentParser(description="Local KB search test UI (Flask).")
    p.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    p.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    args = p.parse_args()
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
