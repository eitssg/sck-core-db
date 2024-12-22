""" Provides a set of Exceptions that the DB engine uses to provide feedback of operations """

from core_framework.constants import (
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_BAD_REQUEST,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    HTTP_CONFLICT,
    HTTP_UNAUTHORIZED,
)


class TableException(Exception):
    """Base exception class for DB table operation errors.

    This class is used to raise exceptions when a table operation fails.

    References:
        - :class:`NotFoundException`
        - :class:`ForbiddenException`
        - :class:`UnauthorizedException`
        - :class:`ConflictException`
        - :class:`BadRequestException`
        - :class:`UnknownException`

    Attributes:
        message (str): Human readable error description
        code (int): A code that represents the error
        context (dict | None): User defined data

    """

    def __init__(self, message: str, code: int, context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class NotFoundException(TableException):
    """Exception raised when a resource is not found code 404

    Extends: :class:`TableException`

    Args:
        message (str): Human readable error description

    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_NOT_FOUND)


class ForbiddenException(TableException):
    """Exception raised when a resource is not found code 403

    Extends: :class:`TableException`

    Args:
        message (str): Human readable error description

    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_FORBIDDEN)


class UnauthorizedException(TableException):
    """Exception raised when a resource is not found code 401

    Extends: :class:`TableException`

    Args:
        message (str): Human readable error description

    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_UNAUTHORIZED)


class ConflictException(TableException):
    """Exception raised when a resource is not found code 409

    Extends: :class:`TableException`

    Args:
        message (str): Human readable error description

    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_CONFLICT)


class BadRequestException(TableException):
    """Exception raised when a resource is not found code 400

    Extends: :class:`TableException`

    Args:
        message (str): Human readable error description

    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_BAD_REQUEST)


class UnknownException(TableException):
    """Exception raised when a resource is not found code 500

    Extends: :class:`TableException`

    Args:
        message (str): Human readable error description

    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_INTERNAL_SERVER_ERROR)
