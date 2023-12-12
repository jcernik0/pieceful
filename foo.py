from pieceful._swallower import swallow_exception
from pieceful import PieceException
from pieceful._components import _find_existing_component


import inspect


def my_func(a: int) -> float:
    return 1.1


sig = inspect.signature(my_func)

print()
