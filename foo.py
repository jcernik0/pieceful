from pieceful import PieceException, PieceFactory, get_piece

from example import AbstractVehicle


class Car(AbstractVehicle):
    def start(self) -> None:
        print("car started")


@PieceFactory
def car_factory() -> AbstractVehicle:
    return Car()


car = get_piece("car_factory", AbstractVehicle)
print(car.__class__)
