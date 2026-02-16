import re
from typing import Dict, List, Tuple

from datastructure.hashtable import HashTable
from datastructure.linkedlist import LinkedList, Posting
from datastructure.trie import Trie


STOPWORDS = {
	"a",
	"an",
	"and",
	"are",
	"as",
	"at",
	"be",
	"but",
	"by",
	"for",
	"if",
	"in",
	"into",
	"is",
	"it",
	"no",
	"not",
	"of",
	"on",
	"or",
	"such",
	"that",
	"the",
	"their",
	"then",
	"there",
	"these",
	"they",
	"this",
	"to",
	"was",
	"will",
	"with",
}


def tokenize(text: str) -> List[str]:
	tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
	return [token for token in tokens if token not in STOPWORDS]


class CampusSearchEngine:
	def __init__(self):
		self.inverted_index = HashTable()
		self.trie = Trie()
		self.documents: Dict[int, Dict[str, str]] = {}
		self.doc_counter = 0

	def add_document(self, title: str, content: str, filename: str) -> int:
		tokens = tokenize(content)
		if not tokens:
			return -1

		self.doc_counter += 1
		doc_id = self.doc_counter
		self.documents[doc_id] = {
			"title": title,
			"filename": filename,
			"length": str(len(tokens)),
		}

		term_counts: Dict[str, int] = {}
		for token in tokens:
			term_counts[token] = term_counts.get(token, 0) + 1

		for term, freq in term_counts.items():
			postings = self.inverted_index.get(term)
			if postings is None:
				postings = LinkedList()
				self.inverted_index.set(term, postings)
			postings.append(Posting(doc_id, freq))
			self.trie.insert(term)

		return doc_id

	def keyword_search(self, query: str) -> List[Tuple[int, int]]:
		return self._search(query, prefix=False)

	def prefix_search(self, query: str) -> List[Tuple[int, int]]:
		return self._search(query, prefix=True)

	def filename_search(self, query: str, prefix: bool = False) -> List[Tuple[int, int]]:
		query_value = query.strip().lower()
		if not query_value:
			return []
		ranked: List[Tuple[int, int]] = []
		for doc_id, meta in self.documents.items():
			filename = meta.get("filename", "").lower()
			if not filename:
				continue
			if prefix:
				is_match = filename.startswith(query_value)
			else:
				is_match = query_value in filename
			if is_match:
				ranked.append((doc_id, 1))
		return ranked

	def _search(self, query: str, prefix: bool) -> List[Tuple[int, int]]:
		query_tokens = tokenize(query)
		if not query_tokens:
			return []

		candidate_terms: List[str] = []
		for token in query_tokens:
			if prefix:
				candidate_terms.extend(self.trie.autocomplete(token, limit=25))
			else:
				candidate_terms.append(token)

		doc_scores: Dict[int, int] = {}
		for term in candidate_terms:
			postings = self.inverted_index.get(term)
			if not postings:
				continue
			for posting in postings.items():
				doc_scores[posting.doc_id] = doc_scores.get(posting.doc_id, 0) + posting.term_freq

		return sorted(doc_scores.items(), key=lambda item: item[1], reverse=True)
