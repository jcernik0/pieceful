class PieceException(Exception):
    def __init__(self, message) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


class PieceNotFound(PieceException):
    pass


class PieceAnnotationException(PieceException):
    pass


class AmbiguousPieceException(PieceException):
    pass
