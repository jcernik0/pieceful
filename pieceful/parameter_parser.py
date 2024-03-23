import inspect
from typing import Annotated, Any, Callable, ForwardRef, Iterable

from .exceptions import (
    ParameterNotAnnotatedException,
    PieceException,
    PieceIncorrectUseException,
)
from .parameters import (
    DefaultFactoryParameter,
    DefaultParameter,
    Parameter,
    PieceParameter,
)

ANNOTATION_TYPE = type(Annotated[str, "example"])


def create_piece_parameter(
    name: str, piece_type: Any, piece_name: str
) -> PieceParameter:
    if not piece_name.strip():
        raise PieceException("piece_name must not be blank")
    return PieceParameter(name, piece_name, piece_type)


def create_default_factory_parameter(name: str, factory: Callable[[], Any]):
    return DefaultFactoryParameter(name, factory)


def evaluate_forward_ref(fr: ForwardRef, globals_dict: dict[str, Any]) -> Any:
    raise PieceException("ForwardRef is not supported")


def count_non_default_parameters(fn) -> int:
    try:
        parameters = inspect.signature(fn).parameters.values()
    except ValueError:
        parameters = tuple()

    filtered = filter(
        lambda p: p.default is inspect.Parameter.empty,
        parameters,
    )
    return sum(1 for _ in filtered)


def parse_parameter(parameter: inspect.Parameter) -> Parameter:
    annotation = parameter.annotation

    if parameter.default is not inspect.Parameter.empty:
        return DefaultParameter(parameter.name, parameter.default)

    if type(annotation) is not ANNOTATION_TYPE:
        raise ParameterNotAnnotatedException(parameter)

    metadata = annotation.__metadata__
    if len(metadata) < 1:
        raise PieceIncorrectUseException("piece metadata not specified in Annotated[]")

    piece_type = annotation.__origin__

    if isinstance(piece_type, ForwardRef):
        try:
            gd = metadata[1]
            assert isinstance(gd, dict), "expected globals to be instance of dict"
        except IndexError:
            raise PieceException("globals not provided to evaluate ForwardRef")
        except AssertionError as e:
            raise PieceException(e.args[0])

        piece_type = evaluate_forward_ref(piece_type, gd)

    metainfo = metadata[0]
    if isinstance(metainfo, str):
        return create_piece_parameter(parameter.name, piece_type, metainfo)

    if callable(metainfo) and count_non_default_parameters(metainfo) == 0:
        return create_default_factory_parameter(parameter.name, metainfo)

    raise PieceIncorrectUseException("invalid use")


def get_parameters(fn: Callable[..., Any]) -> Iterable[Parameter]:
    return tuple(map(parse_parameter, inspect.signature(fn).parameters.values()))
