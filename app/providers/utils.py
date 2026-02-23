from typing import Iterable, List, TypeVar
T = TypeVar("T")
def chunks(items: List[T], size: int) -> Iterable[List[T]]:
    for i in range(0, len(items), size):
        yield items[i:i+size]
