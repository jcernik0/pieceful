# Pieceful

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/your-username/pieceful/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

## Description

Pieceful is a Python package that provides a collection of utility functions for working with dependency injection.

## Installation

Install with
```bash
pip install pieceful
```

## Features

- TODO

## Usage
First perform necessary import:
```python
from typing import Annotated
from pieceful import Piece, PieceFactor, get_piece
```
Than decorate your dependencies with `Piece` or `PieceFactory` decorator and name your dependencies.
```python
class Engine:
    pass

class PowerfulEngine(Engine):
    pass

@PieceFactory("powerful_engine")
def powerful_engine_factory() -> Engine:
    return PowerfulEngine()

class AbstractVehicle:
    pass

@Piece("car")
class Car(AbstractVehicle):
    def __init__(self, engine: Annotated[Engine, "powerful_engine"]):
        self.engine = engine
```

When components are registered (with decorators in this case) they can be injected to other components (like `Engine` -> `Car`) by using `typing.Annotated` or they can be directly obtained.

```python
car = get_piece("car", Car)
```

