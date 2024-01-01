from typing import Annotated, Protocol, runtime_checkable

import pieceful


@runtime_checkable
class LoggerProtocol(Protocol):
    def log(self, info: str) -> str:
        ...


@pieceful.Piece("logger")
class Logger:
    def log(self, info: str) -> str:
        print(info)
        return info


@pieceful.Piece("cont")
class Controller:
    def __init__(self, logger: Annotated[LoggerProtocol, "logger"]):
        self.logger = logger
