import hashlib
import re

from openai import OpenAI

from app.core.config import settings


class OpenAIService:
  def __init__(self) -> None:
    self.client = (
      OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
      if settings.openai_api_key
      else None
    )
    self.offline_mode = self.client is None

  @staticmethod
  def _local_embed(text: str, dim: int = 1536) -> list[float]:
    # Lightweight lexical hashing embedding so indexing works without external APIs.
    vec = [0.0] * dim
    tokens = re.findall(r"[A-Za-z0-9_]+", (text or "").lower())
    if not tokens:
      return vec

    for token in tokens:
      digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
      idx = int.from_bytes(digest[:4], "little") % dim
      sign = 1.0 if (digest[4] & 1) == 0 else -1.0
      weight = 1.0 + (digest[5] / 255.0)
      vec[idx] += sign * weight

    return vec

  def embed_texts(self, texts: list[str]) -> list[list[float]]:
    if not texts:
      return []

    if self.offline_mode:
      return [self._local_embed(text) for text in texts]

    response = self.client.embeddings.create(
      model=settings.openai_embedding_model,
      input=texts,
    )
    return [item.embedding for item in response.data]

  def generate_answer(self, query: str, contexts: list[dict[str, str]]) -> str:
    return self._generate_answer(query, contexts, feedback_context=None)

  def generate_answer_with_feedback(self, query: str, contexts: list[dict[str, str]], feedback_context: str | None = None) -> str:
    return self._generate_answer(query, contexts, feedback_context=feedback_context)

  def generate_general_answer(self, query: str, feedback_context: str | None = None) -> str:
    if self.offline_mode:
      return (
        "I am running in local mode because OPENAI_API_KEY is not configured. "
        "Please enable GPT mode for richer general answers."
      )

    messages = [
      {
        "role": "system",
        "content": (
          "You are Smart Campus AI. Answer the user's question directly, clearly, and concisely. "
          "If you are unsure, say so rather than inventing details."
        ),
      },
      {
        "role": "user",
        "content": (
          f"User query:\n{query}\n\n"
          f"Recent user feedback context:\n{feedback_context or 'No feedback context available.'}\n\n"
          "Respond with the best possible answer."
        ),
      },
    ]

    completion = self.client.chat.completions.create(
      model=settings.openai_chat_model,
      temperature=0.2,
      messages=messages,
    )

    return completion.choices[0].message.content or "No response generated."

  def generate_answer_with_web_search(
    self,
    query: str,
    web_results: list[dict[str, str]],
    feedback_context: str | None = None,
  ) -> str:
    if self.offline_mode:
      if not web_results:
        return "No relevant information found in web results."

      snippets = []
      for item in web_results[:3]:
        snippet = item.get("snippet", "").strip()
        if snippet:
          snippets.append(snippet)

      return snippets[0] if snippets else "No relevant information found in web results."

    numbered_context = []
    for idx, result in enumerate(web_results, start=1):
      numbered_context.append(
        f"[{idx}] Title: {result['title']}\nURL: {result['url']}\nSnippet: {result['snippet']}"
      )

    prompt_context = "\n\n".join(numbered_context)

    completion = self.client.chat.completions.create(
      model=settings.openai_chat_model,
      temperature=0.2,
      messages=[
        {
          "role": "system",
          "content": (
            "You are Smart Campus AI. Answer only from provided context. "
            "If context is missing details, clearly state limits and avoid fabrication."
          ),
        },
        {
          "role": "user",
          "content": (
            f"User query:\n{query}\n\n"
            f"Retrieved context:\n{prompt_context}\n\n"
            f"Recent user feedback context:\n{feedback_context or 'No feedback context available.'}\n\n"
            "Provide a concise answer and mention citation numbers like [1], [2]."
          ),
        },
      ],
    )

    return completion.choices[0].message.content or "No response generated."

  def _generate_answer(
    self,
    query: str,
    contexts: list[dict[str, str]],
    feedback_context: str | None,
  ) -> str:
    if self.offline_mode:
      if not contexts:
        return "No relevant information found in indexed documents."

      query_tokens = set(re.findall(r"[A-Za-z0-9_]+", query.lower()))

      def score_sentence(sentence: str) -> int:
        sentence_tokens = set(re.findall(r"[A-Za-z0-9_]+", sentence.lower()))
        return len(query_tokens & sentence_tokens)

      best_context = contexts[0]
      chunk_text = best_context["chunk_text"].replace("\r", " ").replace("\n", " ")
      sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", chunk_text) if part.strip()]
      best_sentence = max(sentences, key=score_sentence, default=chunk_text[:280])

      if score_sentence(best_sentence) == 0:
        best_sentence = chunk_text[:280]

      feedback_note = f" {feedback_context}" if feedback_context else ""
      return f"{best_sentence}{feedback_note}".strip()

    numbered_context = []
    for idx, context in enumerate(contexts, start=1):
      numbered_context.append(
        f"[{idx}] Source: {context['document_name']} | Chunk {context['chunk_id']}\n{context['chunk_text']}"
      )

    prompt_context = "\n\n".join(numbered_context)

    messages = [
      {
        "role": "system",
        "content": (
          "You are Smart Campus AI. Answer only from provided context. "
          "If context is missing details, clearly state limits and avoid fabrication."
        ),
      },
      {
        "role": "user",
        "content": (
          f"User query:\n{query}\n\n"
          f"Retrieved context:\n{prompt_context}\n\n"
          f"Recent user feedback context:\n{feedback_context or 'No feedback context available.'}\n\n"
          "Provide a concise answer and mention citation numbers like [1], [2]."
        ),
      },
    ]

    completion = self.client.chat.completions.create(
      model=settings.openai_chat_model,
      temperature=0.2,
      messages=messages,
    )

    return completion.choices[0].message.content or "No response generated."