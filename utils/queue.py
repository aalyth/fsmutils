from typing import TypeVar, Generic

T = TypeVar("T")


class Queue(Generic[T]):
    values: list[T]

    def __init__(self, initial: list[T] = []) -> None:
        self.values = initial

    def push(self, val: T) -> None:
        self.values.insert(0, val)

    def pop(self) -> T:
        if self.is_empty():
            raise ValueError("popping an empty stack")
        return self.values.pop()

    def is_empty(self) -> bool:
        return len(self.values) == 0

    def __iter__(self) -> "Queue":
        return self

    def __next__(self) -> T:
        if self.is_empty():
            raise StopIteration()
        return self.values.pop()
