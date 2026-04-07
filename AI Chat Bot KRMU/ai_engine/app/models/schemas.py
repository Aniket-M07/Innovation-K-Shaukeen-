from pydantic import BaseModel, Field


class EmbedResponse(BaseModel):
  message: str
  embedded_documents: int
  embedded_chunks: int
  document_names: list[str]


class QueryRequest(BaseModel):
  query: str = Field(min_length=1)
  top_k: int = Field(default=4, ge=1, le=10)
  feedback_context: str | None = None


class WebSource(BaseModel):
  title: str
  url: str
  snippet: str


class SourceCitation(BaseModel):
  document_name: str
  chunk_id: int
  chunk_text: str
  score: float


class QueryResponse(BaseModel):
  answer: str
  confidence_score: float
  citations: list[SourceCitation]
  fallback: bool
  source: str = "documents"
  web_sources: list[WebSource] = Field(default_factory=list)