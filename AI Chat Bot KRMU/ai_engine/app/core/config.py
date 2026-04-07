import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load root .env (backend/shared settings) and ai_engine/.env (AI-specific secrets).
# ai_engine/.env is loaded with override so OPENAI_API_KEY can be set there safely.
ROOT_DIR = Path(__file__).resolve().parents[3]
AI_ENGINE_DIR = ROOT_DIR / "ai_engine"

load_dotenv(ROOT_DIR / ".env")
load_dotenv(AI_ENGINE_DIR / ".env", override=True)


@dataclass
class Settings:
  openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
  openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
  openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
  openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

  web_search_enabled: bool = os.getenv("WEB_SEARCH_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
  web_search_provider: str = os.getenv("WEB_SEARCH_PROVIDER", "duckduckgo")
  web_search_max_results: int = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
  web_search_timeout_ms: int = int(os.getenv("WEB_SEARCH_TIMEOUT_MS", "8000"))

  chunk_size: int = int(os.getenv("CHUNK_SIZE", "800"))
  chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
  default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "4"))
  min_confidence_threshold: float = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.55"))

  faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "ai_engine/data/faiss.index")
  faiss_metadata_path: str = os.getenv("FAISS_METADATA_PATH", "ai_engine/data/faiss_metadata.json")

  def ensure_data_dirs(self) -> None:
    Path(self.faiss_index_path).parent.mkdir(parents=True, exist_ok=True)
    Path(self.faiss_metadata_path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_data_dirs()