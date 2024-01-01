# pieceful

Minimalistic library for easy and convenient dependency injection by help of python decorators.

## Get started
Let's start straight with the simple example.\
With some abstraction included we are defining composition problem, when we have a `car` that has it's driver and engine.\
Car is an abstract vehicle concept that also depends on abstact driver and abstract engine. Let's define our abstraction layer.

```python
from abc import ABC, abstractmethod


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

```

Now when we have defined our abstraction, let's move to the specific implementation.\
Let's start with the __driver__.

```python

from pieceful import Piece, get_piece

@Piece("driver")
class GoodDriver(AbstractDriver):
    def drive(self) -> None:
        print("Good driver is ready to go")


@Piece("lazy_driver")
class LazyDriver(AbstractDriver):
    def drive(self) -> None:
        print("Lazy driver is too lazy to go")
```
> Notice, that classes are decorated with `@Piece` decorator. This decorator instantiate classes and make them ready to inject.

> See that we are defining `name` of dependency in `@Piece` decorator.

Let's have also a specific engine.
```python
@Piece("engine")
class PowerfulEngine(AbstractEngine):
    def run(self):
        print("Powerful engine is running and ready to go")
```

And finally lets implement __car__, which is basically an `AbstractVehicle`.

```python
import typing as t

@Piece("car", wheels=4)
class Car(AbstractVehicle):
    def __init__(
        self,
        wheels: int,
        engine: t.Annotated[AbstractEngine, "engine"],
        driver: t.Annotated[AbstractDriver, "driver"],
    ) -> None:
        self.wheels: int = wheels
        self.engine = engine
        self.driver = driver

    def start(self) -> None:
        self.engine.run()
        self.driver.drive()
        print(f"Car with {self.wheels} wheels started")
```
> Notice that `Car` depends on `engine` and a `driver`, that are injected in a constructor. Also number of wheels is required to instantiate the `Car`. Parameters needed for instantiation that are not `Piece` can be defined in the `Car`'s `@Piece` decorator as `*params` (for example `wheels=4`).

> To tell the framework what dependencies we want to inject to our `Car`, we use `typing.Annotated`, where first argument has a meaning of `type` of dependency and second represents `name` of our `Piece`. This way, framework will recognize what to inject. 

To connect defined pieces together, we can define `main` method, where we use the object with type of `AbstractVehicle`. Function `get_piece` retrieves a registered `Piece`.

```python

def main():
    car: AbstractVehicle = get_piece(AbstractVehicle, "car")
    car.start()

if __name__ == "__main__":
    main()
```
> Notice that `main` function does not need to know anything about specific car implementation. Function depends only on abstract concept and _dependecy inversion_ principle is followed this way. Also see that, function `get_piece` can retrieve required dependency based on abstract type and dependency name. In summary, _dependency inversion_ principle is supported by this framework.

If we run the script, we can see our output in the terminal.
```
Powerful engine is running and ready to go
Good driver is ready to go
Car with 4 wheels started 
```
Now let's assume, that we want to use other `driver` dependency in our `Car` definition. All it takes is to change annotation (`"driver"` -> `"lazy_driver"`):

```python
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

```
This way we wire `LazyDriver` dependency to our `Car`. We get following output from the script:
```
Powerful engine is running and ready to go
Lazy driver is too lazy to go
Car with 4 wheels started 
``` 
> To repeat again, `Car` depends on abstract concepts, so both `GoodDriver` and `LazyDriver` match type `AbstractDriver` and can be injected as a `driver` parameter to `Car` constructor.

## @PieceFactory decorator
Another way to create dependencies is to use _function_ that returns desired object. Let's use `AbstractVehicle` class already defined. See example below:
```python
class Car(AbstractVehicle):
    def start(self) -> None:
        print("car started")

@PieceFactory
def pretty_car() -> AbstractVehicle:
    print("pretty car is being created")
    return Car()
```

Function `car_factory` behaves as an initializer for object of type `AbstractVehicle`. Remember, that dependency is registered with the name matching name of initialization function, which is `"pretty_car"`. This way, we can inject `"pretty_car"` piece where needed using `typing.Annotation` or obtain object reference by using:

```python
pc = get_piece("pretty_car", AbstractVehicle)
```

## Eager vs. Lazy initialization
Library allows to choose from two strategies of object initialization. Strategy can be specified when decorating class with `@Piece` with help of enum type: `PieceStrategy`.

```python
from pieceful import Piece, PieceStrategy

@Piece("foo", strategy=PieceStrategy.EAGER)
class Foo:
    pass

@Piece("bar", strategy=PieceStrategy.LAZY)
class Bar:
    pass
```

LAZY:\
Object is initialized right when its needed for the first time. This means object is obtained by `get_piece` function or is injected to the component that is being initialized. Approach with `@PieceFactory` supports only lazy instantiation.

EAGER:\
Object is initialized at the same time interpreter reads class definition (decorated with `@Piece`). This approach is not recommended because it's more tricky to understand when object is created inside library and depends on the order of imports.
> Think that if we import module in other file, code of whole module is executed and this way also `@Piece` object is also created in library storage.

If strategy is not sopecified, default is __LAZY__ since this is more safe option. Also when decorated many dependencies with EAGER strategies, all initializations may have impact on performance, because dependencies are created usually at application startup (usually, because for example with `importlib` behavior can be different).