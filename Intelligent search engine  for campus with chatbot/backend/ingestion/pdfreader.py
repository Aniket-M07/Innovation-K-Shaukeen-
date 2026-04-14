from typing import Optional

try:
	from PyPDF2 import PdfReader
except Exception:  # pragma: no cover - optional import for environments without PyPDF2
	PdfReader = None


def extract_text_from_pdf(path: str) -> str:
	if not PdfReader:
		return ""
	try:
		reader = PdfReader(path)
		return "\n".join(page.extract_text() or "" for page in reader.pages)
	except Exception:
		return ""
