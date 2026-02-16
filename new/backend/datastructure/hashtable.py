from typing import Any, Optional

from .linkedlist import LinkedList


class HashTable:
	def __init__(self, capacity: int = 1024):
		self.capacity = max(8, capacity)
		self.buckets = [LinkedList() for _ in range(self.capacity)]
		self.size = 0

	def _hash(self, key: str) -> int:
		h = 0
		for ch in key:
			h = (h * 31 + ord(ch)) % self.capacity
		return h

	def set(self, key: str, value: Any) -> None:
		index = self._hash(key)
		bucket = self.buckets[index]
		node = bucket.find(lambda kv: kv[0] == key)
		if node:
			node.value = (key, value)
			return
		bucket.append((key, value))
		self.size += 1
		if self.size / self.capacity > 0.75:
			self._resize()

	def get(self, key: str) -> Optional[Any]:
		index = self._hash(key)
		bucket = self.buckets[index]
		node = bucket.find(lambda kv: kv[0] == key)
		if node:
			return node.value[1]
		return None

	def _resize(self) -> None:
		old_buckets = self.buckets
		self.capacity *= 2
		self.buckets = [LinkedList() for _ in range(self.capacity)]
		self.size = 0
		for bucket in old_buckets:
			for key, value in bucket.items():
				self.set(key, value)
