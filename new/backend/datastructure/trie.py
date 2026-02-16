from collections import deque
from typing import Dict, List, Optional, Tuple


class TrieNode:
	def __init__(self):
		self.children: Dict[str, "TrieNode"] = {}
		self.is_end = False
		self.frequency = 0


class Trie:
	def __init__(self):
		self.root = TrieNode()

	def insert(self, word: str) -> None:
		node = self.root
		for ch in word:
			if ch not in node.children:
				node.children[ch] = TrieNode()
			node = node.children[ch]
		node.is_end = True
		node.frequency += 1

	def _walk(self, prefix: str) -> Optional[TrieNode]:
		node = self.root
		for ch in prefix:
			if ch not in node.children:
				return None
			node = node.children[ch]
		return node

	def autocomplete(self, prefix: str, limit: int = 10) -> List[str]:
		node = self._walk(prefix)
		if not node:
			return []

		results: List[Tuple[str, int]] = []
		queue = deque([(node, prefix)])
		while queue:
			current, current_prefix = queue.popleft()
			if current.is_end:
				results.append((current_prefix, current.frequency))
			for ch, child in current.children.items():
				queue.append((child, current_prefix + ch))

		results.sort(key=lambda item: item[1], reverse=True)
		return [term for term, _ in results[:limit]]
