"""Merge / tie-break policy for multi-collection retrieval (no Chroma import)."""


def merge_tier(doc_scope: str) -> int:
    """Lower sorts first when similarity is tied: tenant beats compliance beats global law."""
    return {"tenant": 0, "compliance": 1, "global_law": 2}.get(doc_scope, 9)
