"""Multilingual E5 embeddings via transformers (query: / passage: prefixes)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ensure_hf_cache() -> None:
    cache = REPO_ROOT / "embedding" / ".hf_cache"
    cache.mkdir(parents=True, exist_ok=True)
    import os

    os.environ.setdefault("HF_HOME", str(cache))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(cache / "hub"))


class E5Embedder:
    def __init__(self, model_name: str, device: str | None = None) -> None:
        _ensure_hf_cache()
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    @torch.inference_mode()
    def encode(
        self,
        texts: list[str],
        *,
        is_query: bool,
        batch_size: int = 16,
        max_length: int = 512,
    ) -> np.ndarray:
        prefix = "query: " if is_query else "passage: "
        chunks: list[np.ndarray] = []
        for i in range(0, len(texts), batch_size):
            batch = [prefix + t for t in texts[i : i + batch_size]]
            tok = self.tokenizer(
                batch,
                max_length=max_length,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            tok = {k: v.to(self.device) for k, v in tok.items()}
            out = self.model(**tok)
            emb = _mean_pool(out.last_hidden_state, tok["attention_mask"])
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            chunks.append(emb.cpu().numpy().astype(np.float32))
        return np.vstack(chunks)


def _mean_pool(token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    summed = torch.sum(token_embeddings * mask, 1)
    denom = torch.clamp(mask.sum(1), min=1e-9)
    return summed / denom
