import io
import zipfile
import xml.etree.ElementTree as et

from pypdf import PdfReader

from app.core.config import settings

try:
  from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
  from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentProcessor:
  supported_extensions = {".pdf", ".docx", ".txt"}

  def __init__(self) -> None:
    self.splitter = RecursiveCharacterTextSplitter(
      chunk_size=settings.chunk_size,
      chunk_overlap=settings.chunk_overlap,
      length_function=len,
      separators=["\n\n", "\n", ". ", " ", ""],
    )

  def validate_extension(self, filename: str) -> None:
    ext = self._extension(filename)
    if ext not in self.supported_extensions:
      raise ValueError(f"Unsupported file format for {filename}. Use PDF, DOCX, or TXT.")

  def extract_text(self, filename: str, content: bytes) -> str:
    ext = self._extension(filename)

    if ext == ".pdf":
      return self._extract_pdf(content)
    if ext == ".docx":
      return self._extract_docx(content)
    if ext == ".txt":
      return self._extract_txt(content)

    raise ValueError(f"Unsupported file type: {ext}")

  def split_text(self, text: str) -> list[str]:
    if not text or not text.strip():
      return []
    return [chunk.strip() for chunk in self.splitter.split_text(text) if chunk.strip()]

  @staticmethod
  def _extension(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot != -1 else ""

  @staticmethod
  def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    parts: list[str] = []
    for page in reader.pages:
      parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()

  @staticmethod
  def _extract_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore").strip()

  @staticmethod
  def _extract_docx(content: bytes) -> str:
    try:
      with zipfile.ZipFile(io.BytesIO(content)) as zipped:
        xml_bytes = zipped.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as error:
      raise ValueError("Invalid DOCX file") from error

    root = et.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts = [node.text for node in root.findall(".//w:t", ns) if node.text]
    return " ".join(texts).strip()