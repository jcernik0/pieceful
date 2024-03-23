from collections import defaultdict
from re import Pattern
from typing import Any, Iterator, Type, TypeVar

from .core import PieceData
from .exceptions import (
    AmbiguousPieceException,
    PieceNotFound,
    _NeedCalculation,
)

Storage = dict[str, dict[Type[Any], PieceData[Any]]]

_T = TypeVar("_T")


class Registry:
    def __init__(self):
        self.registry: Storage = defaultdict(dict)

    def add(self, piece_name: str, piece_data: PieceData[Any]):
        piece_dict = self.registry[piece_name]

        if piece_data.type in piece_dict:
            raise AmbiguousPieceException(
                f"Piece {piece_data.type} is already registered as a subclass of {piece_data.type}."
            )

        piece_dict[piece_data.type] = piece_data

    def _get_piece_data(
        self, piece_name: str, piece_type: Type[_T]
    ) -> PieceData[_T] | None:
        if (pd := self.registry[piece_name].get(piece_type)) is not None:
            return pd

        for type_, pd in self.registry[piece_name].items():
            if issubclass(type_, piece_type):
                return pd
        return None

    def get_object(self, piece_name: str, piece_type: Type[_T]) -> _T:
        piece_data = self._get_piece_data(piece_name, piece_type)

        if piece_data is None:
            raise PieceNotFound(f"Piece {piece_type} not found in registry.")

        if (instance := piece_data.get_instance()) is not None:
            return instance

        params: dict[str, Any] = {}
        for param in piece_data.parameters:
            try:
                param_val = param.get()
            except _NeedCalculation as e:
                param_val = self.get_object(e.piece_name, e.piece_type)
            params[param.name] = param_val

        return piece_data.initialize(params)

    def get_all_objects_by_supertype(self, super_type: Type[_T]) -> Iterator[_T]:
        for piece_name, piece_data in self.registry.items():
            for type_ in piece_data.keys():
                if issubclass(type_, super_type):
                    yield self.get_object(piece_name, type_)

    def get_all_objects_by_name_matching(self, name_pattern: Pattern) -> Iterator[Any]:
        for name, data in (
            (name, data)
            for name, data in self.registry.items()
            if name_pattern.search(name)
        ):
            for piece_data in data.values():
                yield self.get_object(name, piece_data.type)

    def clear(self):
        self.registry.clear()

    def __getitem__(self, item: str) -> dict[Type[Any], PieceData[Any]]:
        return self.registry[item]


registry: Registry = Registry()
