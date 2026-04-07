import re

from fastapi import UploadFile

from app.core.config import settings
from app.models.schemas import EmbedResponse, QueryResponse, SourceCitation
from app.services.document_processor import DocumentProcessor
from app.services.openai_service import OpenAIService
from app.services.web_search_service import WebSearchService
from app.services.vector_store import VectorStore

class RAGService:
  def __init__(self) -> None:
    self.processor = DocumentProcessor()
    self.openai_service = OpenAIService()
    self.web_search_service = WebSearchService()
    self.vector_store = VectorStore()

  async def embed_files(self, files: list[UploadFile]) -> EmbedResponse:
    all_texts: list[str] = []
    all_metadata: list[dict] = []
    document_names: list[str] = []

    for file in files:
      self.processor.validate_extension(file.filename)
      binary = await file.read()
      text = self.processor.extract_text(file.filename, binary)

      if not text:
        continue

      chunks = self.processor.split_text(text)
      if not chunks:
        continue

      document_names.append(file.filename)

      for idx, chunk in enumerate(chunks, start=1):
        all_texts.append(chunk)
        all_metadata.append(
          {
            "document_name": file.filename,
            "chunk_id": idx,
            "chunk_text": chunk,
          }
        )

    if not all_texts:
      raise ValueError("No readable text was found in uploaded files")

    embeddings = self.openai_service.embed_texts(all_texts)
    added = self.vector_store.add(embeddings, all_metadata)

    return EmbedResponse(
      message="Documents embedded successfully",
      embedded_documents=len(document_names),
      embedded_chunks=added,
      document_names=document_names,
    )

  def query(self, user_query: str, top_k: int, feedback_context: str | None = None) -> QueryResponse:
    if not user_query.strip():
      raise ValueError("query is required")

    if self._should_use_general_answer(user_query):
      return self._answer_without_docs(user_query, feedback_context, "General knowledge question routed to web/GPT.")

    if self.vector_store.is_empty():
      return self._answer_without_docs(user_query, feedback_context, "No documents have been embedded yet.")

    if self.openai_service.offline_mode:
      top = self.vector_store.search_lexical(user_query, top_k or settings.default_top_k)
    else:
      query_embedding = self.openai_service.embed_texts([user_query])[0]
      top = self.vector_store.search(query_embedding, top_k or settings.default_top_k)

    if not top:
      return self._answer_without_docs(user_query, feedback_context, "No relevant context was retrieved from indexed documents.")

    if self.openai_service.offline_mode:
      normalized_scores = [min(1.0, max(0.0, float(item["score"]))) for item in top]
    else:
      normalized_scores = [self._normalize_score(item["score"]) for item in top]
    confidence = sum(normalized_scores) / len(normalized_scores)

    if max(normalized_scores) < settings.min_confidence_threshold:
      return self._answer_without_docs(user_query, feedback_context, "Relevant information was not found with enough confidence.")

    contexts = [
      {
        "document_name": item["metadata"]["document_name"],
        "chunk_id": item["metadata"]["chunk_id"],
        "chunk_text": item["metadata"]["chunk_text"],
      }
      for item in top
    ]

    answer = self.openai_service.generate_answer_with_feedback(user_query, contexts, feedback_context)
    citations = [
      SourceCitation(
        document_name=item["metadata"]["document_name"],
        chunk_id=int(item["metadata"]["chunk_id"]),
        chunk_text=item["metadata"]["chunk_text"],
        score=round(self._normalize_score(item["score"]), 4),
      )
      for item in top
    ]

    return QueryResponse(
      answer=answer,
      confidence_score=round(confidence, 4),
      citations=citations,
      fallback=False,
      source="documents",
    )

  @staticmethod
  def _normalize_score(raw_score: float) -> float:
    normalized = (raw_score + 1.0) / 2.0
    if normalized < 0:
      return 0.0
    if normalized > 1:
      return 1.0
    return float(normalized)

  @staticmethod
  def _should_use_general_answer(user_query: str) -> bool:
    query = user_query.lower().strip()
    campus_terms = (
      "campus",
      "admission",
      "admissions",
      "student",
      "teacher",
      "faculty",
      "document",
      "syllabus",
      "course",
      "exam",
      "semester",
      "attendance",
      "fee",
      "fees",
      "library",
      "hostel",
      "placement",
    )

    if any(term in query for term in campus_terms):
      return False

    general_starts = (
      "what is",
      "what are",
      "who is",
      "who are",
      "why is",
      "why are",
      "how is",
      "how are",
      "define ",
      "explain ",
      "tell me about ",
      "describe ",
    )
    return query.startswith(general_starts) or len(re.findall(r"[A-Za-z0-9_]+", query)) <= 5

  def _answer_without_docs(self, user_query: str, feedback_context: str | None, reason: str) -> QueryResponse:
    web_results = self.web_search_service.search(user_query, settings.web_search_max_results)

    if web_results:
      answer = self.openai_service.generate_answer_with_web_search(user_query, web_results, feedback_context)
      citations = [
        SourceCitation(
          document_name=item["title"],
          chunk_id=idx,
          chunk_text=item["snippet"],
          score=round(max(0.0, 1.0 - (idx * 0.08)), 4),
        )
        for idx, item in enumerate(web_results[:5], start=1)
      ]

      return QueryResponse(
        answer=answer,
        confidence_score=0.62,
        citations=citations,
        fallback=True,
        source="web",
        web_sources=web_results,
      )

    answer = self.openai_service.generate_general_answer(user_query, feedback_context)

    if self.openai_service.offline_mode:
      answer = f"I could not find reliable information in the uploaded documents or web results. Reason: {reason}"

    return QueryResponse(
      answer=answer,
      confidence_score=0.0,
      citations=[],
      fallback=True,
      source="ai" if not self.openai_service.offline_mode else "documents",
    )