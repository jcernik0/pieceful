from abc import ABC


class AbstractVehicle(ABC):
    engine: "AbstractEngine"


class AbstractBrakes(ABC):
    pass


class AbstractEngine(ABC):
    pass


class EagerEngine(AbstractEngine):
    pass


class LazyEngine(AbstractEngine):
    pass


# class
