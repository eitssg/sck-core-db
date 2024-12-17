from core_framework.constants import (
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_BAD_REQUEST,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    HTTP_CONFLICT,
    HTTP_UNAUTHORIZED,
)


class TableException(Exception):
    """Base exception class for API errors.

    Attributes:
        message (str): Human readable error description
        code (int): HTTP status code for the error
    """

    def __init__(self, message: str, code: int, context: dict | None = None):
        """
        Create a new ApiException object

        Args:
            message (str): Message to return
            code (int): Code to return in the message
        """
        super().__init__(message)
        self.code = code
        self.context = context or {}


class NotFoundException(TableException):
    def __init__(self, message: str):
        super().__init__(message, HTTP_NOT_FOUND)


class ForbiddenException(TableException):
    def __init__(self, message: str):
        super().__init__(message, HTTP_FORBIDDEN)


class UnauthorizedException(TableException):
    def __init__(self, message: str):
        super().__init__(message, HTTP_UNAUTHORIZED)


class ConflictException(TableException):
    def __init__(self, message: str):
        super().__init__(message, HTTP_CONFLICT)


class BadRequestException(TableException):
    def __init__(self, message: str):
        super().__init__(message, HTTP_BAD_REQUEST)


class UnknownException(TableException):
    def __init__(self, message: str):
        super().__init__(message, HTTP_INTERNAL_SERVER_ERROR)
