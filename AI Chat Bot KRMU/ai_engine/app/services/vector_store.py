import json
import math
import threading
import re
from pathlib import Path

import faiss
import numpy as np

from app.core.config import settings

STOPWORDS = {
  "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "i", "in", "is",
  "it", "of", "on", "or", "that", "the", "their", "them", "then", "there", "these", "they",
  "this", "to", "was", "what", "when", "where", "which", "who", "why", "with", "you", "your",
}


class VectorStore:
  def __init__(self) -> None:
    self._lock = threading.Lock()
    self.index: faiss.Index | None = None
    self.metadata: list[dict] = []
    self.index_path = Path(settings.faiss_index_path)
    self.metadata_path = Path(settings.faiss_metadata_path)
    self._load()

  def _load(self) -> None:
    if self.index_path.exists():
      self.index = faiss.read_index(str(self.index_path))
    if self.metadata_path.exists():
      self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))

    if self.index is not None and self.index.ntotal != len(self.metadata):
      raise RuntimeError("FAISS index and metadata are out of sync. Rebuild the vector store.")

  def _persist(self) -> None:
    if self.index is not None:
      faiss.write_index(self.index, str(self.index_path))
    self.metadata_path.write_text(json.dumps(self.metadata, ensure_ascii=True, indent=2), encoding="utf-8")

  def is_empty(self) -> bool:
    return self.index is None or self.index.ntotal == 0

  def add(self, embeddings: list[list[float]], metadata: list[dict]) -> int:
    if not embeddings:
      return 0

    vectors = np.asarray(embeddings, dtype="float32")
    if vectors.ndim != 2:
      raise ValueError("Embeddings must be a 2D matrix")

    faiss.normalize_L2(vectors)
    dim = int(vectors.shape[1])

    with self._lock:
      if self.index is None:
        self.index = faiss.IndexFlatIP(dim)
      elif self.index.d != dim:
        raise ValueError("Embedding dimension mismatch with existing FAISS index")

      self.index.add(vectors)
      self.metadata.extend(metadata)
      self._persist()

    return int(vectors.shape[0])

  def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
    if self.is_empty():
      return []

    safe_top_k = max(1, min(int(top_k), self.index.ntotal))

    query_vector = np.asarray([query_embedding], dtype="float32")
    faiss.normalize_L2(query_vector)

    with self._lock:
      scores, indices = self.index.search(query_vector, safe_top_k)

    results: list[dict] = []
    for idx, score in zip(indices[0], scores[0]):
      if idx < 0 or idx >= len(self.metadata):
        continue
      results.append(
        {
          "score": float(score),
          "metadata": self.metadata[idx],
        }
      )

    return results

  @staticmethod
  def _tokens(text: str) -> set[str]:
    return {
      token
      for token in re.findall(r"[A-Za-z0-9_]+", (text or "").lower())
      if len(token) > 2 and token not in STOPWORDS
    }

  def search_lexical(self, query: str, top_k: int) -> list[dict]:
    if self.is_empty():
      return []

    query_tokens = self._tokens(query)
    if not query_tokens:
      return []

    ranked: list[dict] = []
    query_phrase = " ".join(sorted(query_tokens))

    for item in self.metadata:
      chunk_text = str(item.get("chunk_text", ""))
      chunk_tokens = self._tokens(chunk_text)
      if not chunk_tokens:
        continue

      overlap = len(query_tokens & chunk_tokens)
      if overlap == 0 and not any(token in chunk_text.lower() for token in query_tokens):
        continue

      union = len(query_tokens | chunk_tokens) or 1
      jaccard = overlap / union
      coverage = overlap / max(1, len(query_tokens))
      phrase_bonus = 0.15 if query_phrase and query_phrase in " ".join(sorted(chunk_tokens)) else 0.0
      document_bonus = 0.05 if any(token in str(item.get("document_name", "")).lower() for token in query_tokens) else 0.0
      exact_bonus = 0.1 if query.lower().strip() in chunk_text.lower() else 0.0

      score = jaccard + (0.6 * coverage) + phrase_bonus + document_bonus + exact_bonus
      ranked.append({"score": float(score), "metadata": item})

    ranked.sort(key=lambda entry: entry["score"], reverse=True)
    return ranked[: max(1, min(int(top_k), len(ranked)))]