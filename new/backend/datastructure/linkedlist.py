from dataclasses import dataclass
from typing import Callable, Iterator, Optional


@dataclass
class Posting:
	doc_id: int
	term_freq: int


class LinkedListNode:
	def __init__(self, value):
		self.value = value
		self.next: Optional["LinkedListNode"] = None


class LinkedList:
	def __init__(self):
		self.head: Optional[LinkedListNode] = None

	def append(self, value) -> None:
		node = LinkedListNode(value)
		if not self.head:
			self.head = node
			return
		current = self.head
		while current.next:
			current = current.next
		current.next = node

	def find(self, predicate: Callable) -> Optional[LinkedListNode]:
		current = self.head
		while current:
			if predicate(current.value):
				return current
			current = current.next
		return None

	def items(self) -> Iterator:
		current = self.head
		while current:
			yield current.value
			current = current.next
