"""Provides a set of Exceptions that the DB engine uses to provide feedback of operations.

This module defines a hierarchy of custom exceptions for database operations, each
corresponding to specific HTTP status codes. All exceptions inherit from OperationException
and provide structured error handling for the Core-DB system.

Exception Hierarchy:
    OperationException (Base)
    ├── NotFoundException (404)
    ├── ForbiddenException (403)
    ├── UnauthorizedException (401)
    ├── ConflictException (409)
    ├── BadRequestException (400)
    └── UnknownException (500)

Common Usage Patterns:
    - **NotFoundException**: Resource doesn't exist in database
    - **ForbiddenException**: User lacks permissions for operation
    - **UnauthorizedException**: Authentication required or invalid
    - **ConflictException**: Resource already exists or condition check failed
    - **BadRequestException**: Invalid input data or missing required fields
    - **UnknownException**: Unexpected internal errors or database failures

Examples:
    >>> try:
    ...     client = ClientActions.get(client="nonexistent")
    ... except NotFoundException as e:
    ...     print(f"Client not found: {e.message}")
    ...     # Handle 404 error

    >>> try:
    ...     ClientActions.create(client="acme", ...)
    ... except ConflictException as e:
    ...     print(f"Client already exists: {e.message}")
    ...     # Handle 409 error

    >>> # Exception handling with context
    >>> try:
    ...     operation_result = some_db_operation()
    ... except OperationException as e:
    ...     logger.error(f"Database error: {e.message}", extra=e.context)
    ...     return {"error": e.message, "code": e.code}
"""

from core_framework.constants import (
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_BAD_REQUEST,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    HTTP_CONFLICT,
    HTTP_UNAUTHORIZED,
)


class OperationException(Exception):
    """Base exception class for DB table operation errors.

    This class is used to raise exceptions when a table operation fails.
    All other database exceptions inherit from this base class to provide
    consistent error handling and HTTP status code mapping.

    Args:
        message (str): Human readable error description that explains what went wrong
        code (int): HTTP status code that represents the error type (e.g., 404, 500)
        context (dict, optional): Additional error context data for debugging.
            Can include request details, database state, or operation metadata.
            Defaults to None.

    Attributes:
        message (str): Human readable error description
        code (int): HTTP status code that represents the error
        context (dict): Additional error context data (empty dict if not provided)

    Examples:
        >>> # Basic exception with just message and code
        >>> raise OperationException("Database connection failed", 500)

        >>> # Exception with additional context
        >>> raise OperationException(
        ...     "Failed to update item",
        ...     500,
        ...     context={"prn": "portfolio:acme:web", "table": "items"}
        ... )

        >>> # Catching and handling base exception
        >>> try:
        ...     perform_database_operation()
        ... except OperationException as e:
        ...     logger.error(f"DB Error {e.code}: {e.message}", extra=e.context)
        ...     return error_response(e.message, e.code)

        >>> # Accessing exception properties
        >>> try:
        ...     client_action.get(client="missing")
        ... except OperationException as e:
        ...     print(f"Error: {e.message}")          # Human readable message
        ...     print(f"HTTP Code: {e.code}")         # 404, 500, etc.
        ...     print(f"Context: {e.context}")        # Additional debug info
    """

    def __init__(self, message: str, code: int, context: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}


class NotFoundException(OperationException):
    """Exception raised when a requested resource is not found.

    This exception corresponds to HTTP status code 404 (Not Found).
    Typically raised when attempting to retrieve, update, or delete
    a resource that does not exist in the database.

    Args:
        message (str): Human readable error description explaining what resource
            was not found and any relevant identifying information

    Examples:
        >>> # Client not found
        >>> raise NotFoundException("Client 'acme' does not exist")

        >>> # Portfolio not found
        >>> raise NotFoundException(
        ...     "Portfolio 'web-services' not found for client 'acme'"
        ... )

        >>> # Item not found by PRN
        >>> raise NotFoundException(
        ...     "Item with PRN 'build:acme:web:api:main:123' not found"
        ... )

        >>> # Handling not found errors
        >>> try:
        ...     portfolio = PortfolioActions.get(client="acme", portfolio="missing")
        ... except NotFoundException as e:
        ...     return {"error": "Portfolio not found", "details": e.message}

        >>> # Common usage in action methods
        >>> def get_client(client_name: str):
        ...     result = ClientActions.get(client=client_name)
        ...     if not result.data:
        ...         raise NotFoundException(f"Client '{client_name}' does not exist")
        ...     return result.data
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_NOT_FOUND)


class ForbiddenException(OperationException):
    """Exception raised when access to a resource is forbidden.

    This exception corresponds to HTTP status code 403 (Forbidden).
    Typically raised when a user has valid credentials but lacks
    sufficient permissions to access or modify the requested resource.

    Args:
        message (str): Human readable error description explaining what
            operation was forbidden and why access was denied

    Examples:
        >>> # Insufficient permissions for operation
        >>> raise ForbiddenException("Insufficient permissions to delete client")

        >>> # Role-based access control
        >>> raise ForbiddenException(
        ...     "NetworkAdmin role required to modify zone configuration"
        ... )

        >>> # Client-specific access restriction
        >>> raise ForbiddenException(
        ...     "User does not have access to client 'enterprise' resources"
        ... )

        >>> # Handling permission errors
        >>> try:
        ...     ClientActions.delete(client="protected-client")
        ... except ForbiddenException as e:
        ...     return {"error": "Access denied", "details": e.message}

        >>> # Common usage with role checking
        >>> def delete_portfolio(user_roles: list, client: str, portfolio: str):
        ...     if "admin" not in user_roles:
        ...         raise ForbiddenException(
        ...             f"Admin role required to delete portfolio '{portfolio}'"
        ...         )
        ...     return PortfolioActions.delete(client=client, portfolio=portfolio)
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_FORBIDDEN)


class UnauthorizedException(OperationException):
    """Exception raised when authentication is required but not provided.

    This exception corresponds to HTTP status code 401 (Unauthorized).
    Typically raised when a request lacks valid authentication credentials
    or the provided credentials are invalid or expired.

    Args:
        message (str): Human readable error description explaining what
            authentication is required or why credentials are invalid

    Examples:
        >>> # Missing authentication
        >>> raise UnauthorizedException("Valid authentication credentials required")

        >>> # Invalid credentials
        >>> raise UnauthorizedException("Invalid API key or token")

        >>> # Expired credentials
        >>> raise UnauthorizedException("Authentication token has expired")

        >>> # Handling authentication errors
        >>> try:
        ...     authenticated_operation()
        ... except UnauthorizedException as e:
        ...     return {"error": "Authentication required", "details": e.message}

        >>> # Common usage in authentication middleware
        >>> def require_auth(request):
        ...     token = request.headers.get("Authorization")
        ...     if not token:
        ...         raise UnauthorizedException("Authorization header is required")
        ...     if not validate_token(token):
        ...         raise UnauthorizedException("Invalid or expired token")
        ...     return True
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_UNAUTHORIZED)


class ConflictException(OperationException):
    """Exception raised when a resource conflict occurs.

    This exception corresponds to HTTP status code 409 (Conflict).
    Typically raised when attempting to create a resource that already
    exists, or when a condition check fails during an operation due to
    concurrent modifications or business rule violations.

    Args:
        message (str): Human readable error description explaining what
            conflict occurred and how it can be resolved

    Examples:
        >>> # Resource already exists
        >>> raise ConflictException("Client 'acme' already exists")

        >>> # Condition check failure
        >>> raise ConflictException(
        ...     "Cannot delete portfolio 'web-services': active deployments exist"
        ... )

        >>> # Concurrent modification conflict
        >>> raise ConflictException(
        ...     "Item was modified by another user. Please refresh and try again."
        ... )

        >>> # Handling conflict errors
        >>> try:
        ...     ClientActions.create(client="existing-client", ...)
        ... except ConflictException as e:
        ...     return {"error": "Client already exists", "details": e.message}

        >>> # Common usage in create operations
        >>> def create_client(client_data: dict):
        ...     existing = ClientActions.get(client=client_data["name"])
        ...     if existing.data:
        ...         raise ConflictException(
        ...             f"Client '{client_data['name']}' already exists"
        ...         )
        ...     return ClientActions.create(**client_data)
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_CONFLICT)


class BadRequestException(OperationException):
    """Exception raised when a request is malformed or invalid.

    This exception corresponds to HTTP status code 400 (Bad Request).
    Typically raised when required parameters are missing, data format
    is invalid, validation constraints are violated, or business rules
    are not met.

    Args:
        message (str): Human readable error description explaining what
            aspect of the request is invalid and how to correct it

    Examples:
        >>> # Missing required field
        >>> raise BadRequestException("Client name is required")

        >>> # Invalid data format
        >>> raise BadRequestException(
        ...     "Invalid data format: expected string, got int"
        ... )

        >>> # Validation constraint violation
        >>> raise BadRequestException(
        ...     "Client name must be lowercase alphanumeric (3-50 characters)"
        ... )

        >>> # Invalid PRN format
        >>> raise BadRequestException(
        ...     "Invalid PRN format: expected 'type:client:portfolio:...'"
        ... )

        >>> # Handling validation errors
        >>> try:
        ...     ClientActions.create(client="", name="")  # Invalid empty values
        ... except BadRequestException as e:
        ...     return {"error": "Validation failed", "details": e.message}

        >>> # Common usage in validation
        >>> def validate_client_data(client_data: dict):
        ...     if not client_data.get("name"):
        ...         raise BadRequestException("Client name is required")
        ...     if len(client_data["name"]) < 3:
        ...         raise BadRequestException("Client name must be at least 3 characters")
        ...     return True
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_BAD_REQUEST)


class UnknownException(OperationException):
    """Exception raised when an unexpected internal error occurs.

    This exception corresponds to HTTP status code 500 (Internal Server Error).
    Typically raised when an unexpected error occurs during database operations,
    external service failures, or when other exceptions cannot be categorized
    into specific error types.

    Args:
        message (str): Human readable error description explaining what
            unexpected error occurred, often including technical details

    Examples:
        >>> # Database connection failure
        >>> raise UnknownException("Database connection failed")

        >>> # Unexpected exception wrapping
        >>> try:
        ...     complex_database_operation()
        ... except Exception as e:
        ...     raise UnknownException(f"Unexpected error: {str(e)}")

        >>> # External service failure
        >>> raise UnknownException(
        ...     "Failed to connect to DynamoDB: Connection timeout"
        ... )

        >>> # Configuration error
        >>> raise UnknownException(
        ...     "Invalid table configuration: missing required environment variables"
        ... )

        >>> # Handling unknown errors
        >>> try:
        ...     complex_operation()
        ... except UnknownException as e:
        ...     logger.exception("Internal server error occurred")
        ...     return {"error": "Internal server error", "details": "Please try again later"}

        >>> # Common usage in exception handling
        >>> def safe_database_operation():
        ...     try:
        ...         return perform_complex_operation()
        ...     except (NotFoundException, ConflictException, BadRequestException):
        ...         raise  # Re-raise known exceptions
        ...     except Exception as e:
        ...         # Wrap unexpected exceptions
        ...         raise UnknownException(f"Internal error: {str(e)}")
    """

    def __init__(self, message: str):
        super().__init__(message, HTTP_INTERNAL_SERVER_ERROR)
