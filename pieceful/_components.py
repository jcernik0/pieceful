import inspect
import typing as t
from collections import defaultdict
from enum import Enum, auto

from ._depends import Depends
from . import exc
from ._swallower import swallow_exception

from typing_extensions import ParamSpec

P = ParamSpec("P")
T = t.TypeVar("T")


_pieces: dict[str, dict[type, object]] = defaultdict(dict)

_register: dict[str, dict[type, dict[str, t.Any]]] = defaultdict(dict)

annot_type = type(t.Annotated[str, "type"])


class HasMetadata(t.Protocol):
    __metadata__: t.Any


class PieceStrategy(Enum):
    LAZY = auto()
    EAGER = auto()


def _check_annot_type(param_name, type_hint: t.Any):
    if type(type_hint) is not annot_type:
        raise exc.PieceAnnotationException(
            f"Parameter `{param_name}` is not annotated for dependency injection."
        )


def _check_annot_definition(type_hint: HasMetadata):
    if len(type_hint.__metadata__) != 1:
        raise exc.PieceAnnotationException(
            'Expected using one component name in annotations: Annotated[MyClass, "component_name"].'
        )


def _parse_annotation(param_name: str, type_hint: t.Any) -> tuple[str, type]:
    _check_annot_type(param_name, type_hint)
    _check_annot_definition(type_hint)

    component_name = type_hint.__metadata__[0]
    component_type = type_hint.__origin__

    if not isinstance(component_name, str):
        raise exc.PieceAnnotationException(
            "Expected annotated component name to be str"
        )

    if isinstance(component_type, t.ForwardRef):
        raise exc.PieceAnnotationException(
            f"This library does not support forward references. Replace {component_type} with explicit reference."
        )

    return component_name, component_type


def _find_existing_component(
    piece_name: str,
    piece_type: t.Type[T],
    storage: dict[str, dict[type, t.Any]],
) -> tuple[t.Type[T], t.Any]:
    not_found_error = exc.PieceNotFound(
        f"Missing component `{piece_name}` of type {piece_type.__name__}"
    )

    if piece_name not in storage:
        raise not_found_error

    found: list[tuple[t.Type[T], t.Any]] = [
        (_cls, _obj)
        for _cls, _obj in storage[piece_name].items()
        if issubclass(_cls, piece_type)
    ]

    if len(found) == 0:
        raise not_found_error

    elif len(found) > 1:
        raise exc.AmbiguousPieceException(
            f"Found total {len(found)} components of subclass `{piece_type.__name__}` with name `{piece_name}`"
        )
    return found[0]


def _get_instantiation_args(
    inspectable: t.Callable[..., t.Any],
    params: dict[str, t.Any],
    param_transformer: t.Callable[[str, type], t.Any],
) -> dict[str, t.Any]:
    instantiation_args: dict[str, t.Any] = {}

    for param_name, param in inspect.signature(inspectable).parameters.items():
        if param_name in params:
            instantiation_args[param_name] = params[param_name]
            continue

        if param.default is not param.empty:
            continue

        component_name, component_type = _parse_annotation(param_name, param.annotation)

        instantiation_args[param_name] = param_transformer(
            component_name, component_type
        )

    return instantiation_args


def _check_duplicates(piece_name: str, piece_type: type):
    if piece_type in _register[piece_name]:
        raise exc.AmbiguousPieceException(
            f"Piece `{piece_name}` of type `{piece_type}` already registered"
        )
    if piece_type in _pieces[piece_name]:
        raise exc.AmbiguousPieceException(
            f"Piece `{piece_name}` of type `{piece_type}` already instantiated"
        )


class Piece:
    """Decorate class as a component.\\
    Automatically instantiates the class and inject all other required components dependencies and parameters.
    
    Args:
        name (str): Name of piece
        params: Parameters, that are not @Piece and should be injected on initialization
    """

    LAZY: PieceStrategy = PieceStrategy.LAZY
    EAGER: PieceStrategy = PieceStrategy.EAGER

    def __init__(
        self, name: str, strategy: PieceStrategy = PieceStrategy.LAZY, **params
    ):
        self.name = name
        self.strategy = strategy
        self.params = params

    def __call__(self, cls: t.Type[T]) -> t.Type[T]:
        if not isinstance(cls, type):
            raise exc.PieceException(
                f"Wrong usage of @{self.__class__.__name__}. Must be used on class. `{cls.__name__}` is not a class."
            )
        _check_duplicates(self.name, cls)

        if self.strategy == PieceStrategy.EAGER:
            self.run_eager(cls)
        elif self.strategy == PieceStrategy.LAZY:
            self.run_lazy(cls)
        else:
            raise exc.PieceException(f"Invalid strategy: `{self.strategy}`")

        return cls

    def run_lazy(self, cls):
        args = _get_instantiation_args(cls, self.params, Depends)
        _register[self.name][cls] = args

    def run_eager(self, cls):
        args = _get_instantiation_args(
            cls,
            self.params,
            lambda c_name, c_type: _find_existing_component(c_name, c_type, _pieces),
        )
        _pieces[self.name][cls] = cls(**args)


def PieceFactory(fn: t.Callable[P, T]) -> t.Callable[P, T]:
    ret_type = inspect.signature(fn).return_annotation
    if ret_type is None:
        raise exc.PieceException("PieceFactory function cannot return None")

    _check_duplicates(fn.__name__, ret_type)

    args = _get_instantiation_args(fn, dict(), Depends)
    _register[fn.__name__][ret_type] = args

    return fn


def _save_piece(piece_name: str, piece: object):
    named_pieces = _pieces[piece_name]
    if piece.__class__ in named_pieces:
        raise exc.AmbiguousPieceException(
            f"Dependency {piece_name}({piece.__class__.__name__}) already exist"
        )

    named_pieces[piece.__class__] = piece


def get_piece(piece_name: str, piece_type: t.Type[T]) -> T:
    try:
        return _find_existing_component(piece_name, piece_type, _pieces)[1]
    except exc.PieceException:
        pass

    # _find_existing_component can be split to two functions
    cls, params = _find_existing_component(piece_name, piece_type, _register)

    for param_name, param_val in params.items():
        if isinstance(param_val, Depends):
            params[param_name] = get_piece(param_val.name, param_val.component_type)

    piece = cls(**params)
    _save_piece(piece_name, piece)

    if piece.__class__ is piece_type:
        del _register[piece_name][piece_type]

    return piece
