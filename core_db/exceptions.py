"""Provides a set of Exceptions that the DB engine uses to provide feedback of operations"""

from core_framework.constants import (
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_BAD_REQUEST,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    HTTP_CONFLICT,
    HTTP_UNAUTHORIZED,
)


class TableException(Exception):
    """
    Base exception class for DB table operation errors.

    This class is used to raise exceptions when a table operation fails.
    All other database exceptions inherit from this base class.

    Parameters
    ----------
    message : str
        Human readable error description
    code : int
        HTTP status code that represents the error
    context : dict, optional
        User defined data for additional error context

    Attributes
    ----------
    message : str
        Human readable error description
    code : int
        HTTP status code that represents the error
    context : dict
        User defined data for additional error context

    See Also
    --------
    NotFoundException : Resource not found (404)
    ForbiddenException : Access forbidden (403)
    UnauthorizedException : Authorization required (401)
    ConflictException : Resource conflict (409)
    BadRequestException : Invalid request (400)
    UnknownException : Internal server error (500)
    """

    def __init__(self, message: str, code: int, context: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}


class NotFoundException(TableException):
    """
    Exception raised when a requested resource is not found.

    This exception corresponds to HTTP status code 404 (Not Found).
    Typically raised when attempting to retrieve, update, or delete
    a resource that does not exist in the database.

    Parameters
    ----------
    message : str
        Human readable error description

    Examples
    --------
    >>> raise NotFoundException("Client 'acme' does not exist")
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_NOT_FOUND)


class ForbiddenException(TableException):
    """
    Exception raised when access to a resource is forbidden.

    This exception corresponds to HTTP status code 403 (Forbidden).
    Typically raised when a user has valid credentials but lacks
    sufficient permissions to access the requested resource.

    Parameters
    ----------
    message : str
        Human readable error description

    Examples
    --------
    >>> raise ForbiddenException("Insufficient permissions to delete client")
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_FORBIDDEN)


class UnauthorizedException(TableException):
    """
    Exception raised when authentication is required but not provided.

    This exception corresponds to HTTP status code 401 (Unauthorized).
    Typically raised when a request lacks valid authentication credentials
    or the provided credentials are invalid.

    Parameters
    ----------
    message : str
        Human readable error description

    Examples
    --------
    >>> raise UnauthorizedException("Valid authentication credentials required")
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_UNAUTHORIZED)


class ConflictException(TableException):
    """
    Exception raised when a resource conflict occurs.

    This exception corresponds to HTTP status code 409 (Conflict).
    Typically raised when attempting to create a resource that already
    exists or when a condition check fails during an operation.

    Parameters
    ----------
    message : str
        Human readable error description

    Examples
    --------
    >>> raise ConflictException("Client 'acme' already exists")
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_CONFLICT)


class BadRequestException(TableException):
    """
    Exception raised when a request is malformed or invalid.

    This exception corresponds to HTTP status code 400 (Bad Request).
    Typically raised when required parameters are missing, data format
    is invalid, or validation constraints are violated.

    Parameters
    ----------
    message : str
        Human readable error description

    Examples
    --------
    >>> raise BadRequestException("Client name is required")
    >>> raise BadRequestException("Invalid data format: expected string, got int")
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_BAD_REQUEST)


class UnknownException(TableException):
    """
    Exception raised when an unexpected internal error occurs.

    This exception corresponds to HTTP status code 500 (Internal Server Error).
    Typically raised when an unexpected error occurs during database operations
    or when other exceptions cannot be categorized into specific error types.

    Parameters
    ----------
    message : str
        Human readable error description

    Examples
    --------
    >>> raise UnknownException("Database connection failed")
    >>> raise UnknownException(f"Unexpected error: {str(e)}")
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_INTERNAL_SERVER_ERROR)
