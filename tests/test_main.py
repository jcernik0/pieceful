from typing import Annotated, Protocol, runtime_checkable
import pytest
from pieceful import Piece, get_piece, PieceFactory
from pieceful._components import _register, _pieces
from pieceful.exc import (
    AmbiguousPieceException,
    PieceAnnotationException,
    PieceException,
    PieceNotFound,
)
from .models import (
    AbstractBrakes,
    AbstractEngine,
    AbstractVehicle,
    LazyEngine,
    EagerEngine,
)
from .setup import (
    refresh_after,
    decorate_lazy_engine,
    decorate_eager_engine,
    NameTypeTuple,
)


def test_create_lazy_default(refresh_after):
    name: str = "lazy_engine_decorated"

    @Piece(name)
    class LazyEngineDecorated(AbstractEngine):
        pass

    assert LazyEngineDecorated in _register[name]
    assert LazyEngineDecorated not in _pieces[name]


def test_create_eager_nondefault(refresh_after):
    name = "eager_engine_decorated"

    @Piece(name, Piece.EAGER)
    class EagerEngineDecorated(AbstractEngine):
        pass

    assert EagerEngineDecorated in _pieces[name]
    assert isinstance(_pieces[name][EagerEngineDecorated], EagerEngineDecorated)
    assert EagerEngineDecorated not in _register[name]


def test_refresh_after():
    assert len(_pieces) == 0
    assert len(_register) == 0


def test_lazy_exists_in_pieces_after_instantiation(
    decorate_lazy_engine: NameTypeTuple, refresh_after
):
    piece_name: str = decorate_lazy_engine.name
    piece_type: type = decorate_lazy_engine.type

    assert isinstance(_register[piece_name][piece_type], dict)
    assert piece_type not in _pieces[piece_name]

    piece = get_piece(piece_name, piece_type)

    piece_in_storage = _pieces[piece_name][piece_type]

    assert piece_in_storage.__class__ is piece_type
    assert piece_type in _pieces[piece_name]

    assert piece is piece_in_storage


def test_get_lazy_piece_not_subclass(
    decorate_lazy_engine: NameTypeTuple, refresh_after
):
    N = decorate_lazy_engine.name
    T = decorate_lazy_engine.type
    assert get_piece(N, T).__class__ is T


def test_get_lazy_piece_subclass(decorate_lazy_engine: NameTypeTuple, refresh_after):
    assert (
        get_piece(decorate_lazy_engine.name, AbstractEngine).__class__
        is decorate_lazy_engine.type
    )


def test_get_eager_piece_not_subclass(
    decorate_eager_engine: NameTypeTuple, refresh_after
):
    piece_name: str = decorate_eager_engine.name
    piece_type: type = decorate_eager_engine.type
    assert isinstance(get_piece(piece_name, piece_type), piece_type)


def test_get_eager_piece_subclass(decorate_eager_engine: NameTypeTuple, refresh_after):
    piece_name: str = decorate_eager_engine.name
    piece_type: type = decorate_eager_engine.type
    assert isinstance(get_piece(piece_name, AbstractEngine), piece_type)


def test_ambiguous_register_error(decorate_lazy_engine: NameTypeTuple, refresh_after):
    with pytest.raises(AmbiguousPieceException):
        Piece(decorate_lazy_engine.name)(decorate_lazy_engine.type)


def test_ambiguous_eager_instantiation_error(
    decorate_eager_engine: NameTypeTuple, refresh_after
):
    with pytest.raises(AmbiguousPieceException):
        Piece(decorate_eager_engine.name, Piece.EAGER)(decorate_eager_engine.type)


def test_eagerly_instantiate_registered_piece_error(
    decorate_lazy_engine: NameTypeTuple, refresh_after
):
    with pytest.raises(AmbiguousPieceException):
        Piece(decorate_lazy_engine.name, Piece.EAGER)(decorate_lazy_engine.type)


def test_register_eagerly_instantiated_piece_error(
    decorate_eager_engine: NameTypeTuple, refresh_after
):
    with pytest.raises(AmbiguousPieceException):
        Piece(decorate_eager_engine.name)(decorate_eager_engine.type)


def test_get_piece_with_dependencies_lazy(
    decorate_lazy_engine: NameTypeTuple, refresh_after
):
    piece_name: str = "vehicle"

    @Piece("brakes")
    class Brakes(AbstractBrakes):
        pass

    @Piece(piece_name)
    class Vehicle(AbstractVehicle):
        def __init__(
            self,
            engine: decorate_lazy_engine.annotation,
            brakes: Annotated[Brakes, "brakes"],
        ):
            pass

    vehicle = get_piece(piece_name, Vehicle)

    assert vehicle.__class__ is Vehicle
    assert _pieces["brakes"][Brakes].__class__ is Brakes


def test_get_piece_with_dependencies_eager(
    decorate_eager_engine: NameTypeTuple, refresh_after
):
    piece_name: str = "vehicle"

    @Piece("brakes", strategy=Piece.EAGER)
    class Brakes(AbstractBrakes):
        pass

    @Piece(piece_name, strategy=Piece.EAGER)
    class Vehicle(AbstractVehicle):
        def __init__(
            self,
            engine: decorate_eager_engine.annotation,
            brakes: Annotated[Brakes, "brakes"],
        ):
            pass

    vehicle = get_piece(piece_name, Vehicle)

    assert vehicle.__class__ is Vehicle
    assert _pieces["brakes"][Brakes].__class__ is Brakes


def test_dependency_inversion_abc(decorate_lazy_engine: NameTypeTuple, refresh_after):
    vehicle_name: str = "vehicle"

    @Piece(vehicle_name)
    class Vehicle(AbstractVehicle):
        def __init__(
            self, engine: Annotated[AbstractEngine, decorate_lazy_engine.name]
        ) -> None:
            self.engine = engine

    vehicle = get_piece(vehicle_name, AbstractVehicle)

    assert isinstance(vehicle, AbstractVehicle)
    assert isinstance(vehicle.engine, decorate_lazy_engine.type)  # type: ignore


def test_dependency_inversion_protocol(refresh_after):
    vehicle_name: str = "car"
    engine_name: str = "super_engine"

    @Piece(engine_name)
    class SuperEngine:
        def run(self, speed_goal: int) -> bool:
            return True

    @runtime_checkable
    class EngineProtocol(Protocol):
        def run(self, _: int) -> bool:
            ...

    @Piece(vehicle_name)
    class Car(AbstractVehicle):
        def __init__(self, engine: Annotated[EngineProtocol, engine_name]):
            self.engine = engine

        def get_speed(self, unit: str) -> int:
            ...

    @runtime_checkable
    class CarProtocol(Protocol):
        def get_speed(self, _: str) -> int:
            ...

    vehicle = get_piece(vehicle_name, CarProtocol)

    assert isinstance(vehicle, Car)
    assert isinstance(vehicle.engine, SuperEngine)


def test_dependency_inversion_protocol_not_runtime_error(refresh_after):
    vehicle_name: str = "car"
    engine_name: str = "super_engine"

    @Piece(engine_name)
    class SuperEngine:
        def run(self, speed_goal: int) -> bool:
            return True

    class EngineProtocol(Protocol):
        def run(self, _: int) -> bool:
            ...

    @Piece(vehicle_name)
    class Car(AbstractVehicle):
        def __init__(self, engine: Annotated[EngineProtocol, engine_name]):
            self.engine = engine

        def get_speed(self, unit: str) -> int:
            ...

    with pytest.raises(TypeError):
        get_piece(vehicle_name, Car)


def test_not_dep_injection_error(decorate_lazy_engine: NameTypeTuple, refresh_after):
    with pytest.raises(PieceAnnotationException):

        @Piece("car")
        class Car(AbstractVehicle):
            def __init__(self, engine) -> None:
                pass


def test_piece_not_found_error(refresh_after):
    with pytest.raises(PieceNotFound):
        get_piece("car_not_found", AbstractVehicle)


def test_piece_factory(refresh_after, decorate_lazy_engine: NameTypeTuple):
    class Car(AbstractVehicle):
        def __init__(self, engine: AbstractEngine):
            self.engine = engine

    @PieceFactory
    def car_from_factory(engine: decorate_lazy_engine.annotation) -> Car:
        return Car(engine)

    car = get_piece(car_from_factory.__name__, AbstractVehicle)

    assert isinstance(car, (AbstractVehicle, Car))
    assert isinstance(car.engine, (AbstractEngine, decorate_lazy_engine.type))  # type: ignore


def test_piece_factory_inversion_return_error(
    refresh_after, decorate_lazy_engine: NameTypeTuple
):
    class Car(AbstractVehicle):
        def __init__(self, engine: AbstractEngine):
            self.engine = engine

    @PieceFactory
    def car_from_factory(engine: decorate_lazy_engine.annotation) -> AbstractVehicle:
        return Car(engine)

    with pytest.raises(TypeError):
        get_piece(car_from_factory.__name__, AbstractVehicle)
