from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar


T = TypeVar("T")


@dataclass
class Initializer(Generic[T]):
    constructor: Callable[..., T]
    args: dict[str, Any]

    def initialize(self) -> T:
        return self.constructor(**self.args)
