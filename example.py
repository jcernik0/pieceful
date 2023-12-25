import typing as t
from abc import ABC, abstractmethod

from pieceful import Piece, get_piece


class AbstractEngine(ABC):
    @abstractmethod
    def run(self) -> None:
        ...


class AbstractDriver(ABC):
    @abstractmethod
    def drive(self) -> None:
        ...


class AbstractVehicle(ABC):
    engine: AbstractEngine
    driver: AbstractDriver

    @abstractmethod
    def start(self) -> None:
        ...


@Piece("driver")
class GoodDriver(AbstractDriver):
    def drive(self) -> None:
        print("Good driver is ready to go")


@Piece("lazy_driver")
class LazyDriver(AbstractDriver):
    def drive(self) -> None:
        print("Lazy driver is too lazy to go")


@Piece("engine")
class PowerfulEngine(AbstractEngine):
    def run(self):
        print("Powerful engine is running and ready to go")


@Piece("car", wheels=4)
class Car(AbstractVehicle):
    def __init__(
        self,
        wheels: int,
        engine: t.Annotated[AbstractEngine, "engine"],
        driver: t.Annotated[AbstractDriver, "lazy_driver"],
    ) -> None:
        self.wheels: int = wheels
        self.engine = engine
        self.driver = driver

    def start(self) -> None:
        self.engine.run()
        self.driver.drive()
        print(f"Car with {self.wheels} wheels started")


def main():
    car = get_piece("car", Car)
    car.start()


if __name__ == "__main__":
    main()
