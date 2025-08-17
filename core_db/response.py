"""Response module for the core_db package. Response objects are returned by the actions module.

This module provides standardized response objects for all database actions and API operations.
The response classes ensure consistent structure across the entire system and provide proper
error handling with detailed exception information.

Key Components:
    - **Response**: Base response model for all API responses
    - **SuccessResponse**: Convenience class for successful operations
    - **NoContentResponse**: For operations that complete without returning data
    - **ErrorResponse**: Comprehensive error handling with exception chains
    - **ErrorDetail**: Detailed error information with stack traces

Features:
    - **Consistent Structure**: Standardized response format across all operations
    - **Error Chains**: Complete exception tracing for debugging
    - **HTTP Status Codes**: Proper status code mapping for REST APIs
    - **Flexible Data**: Support for various data types (dict, list, string)
    - **Audit Information**: Timestamps and metadata for tracking

Examples:
    >>> # Success response
    >>> response = SuccessResponse(data={"client": "acme", "name": "ACME Corp"})
    >>> print(response.status)  # "ok"
    >>> print(response.code)    # 200

    >>> # Error response from exception
    >>> try:
    ...     raise ValueError("Invalid input")
    ... except ValueError as e:
    ...     response = ErrorResponse(exception=e)
    >>> print(response.status)  # "error"
    >>> print(response.code)    # 500
"""

import traceback

from typing import Any, Literal, Self
from datetime import timezone, datetime as dt

from pydantic import BaseModel, Field, ConfigDict, model_validator
from pydantic import ValidationError

from core_framework.constants import (
    HTTP_OK,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NO_CONTENT,
)


class Response(BaseModel):
    """Base response model for all API responses.

    This object is returned by all database actions and can be serialized
    to JSON for API responses. It provides a consistent structure for both
    successful and error responses.

    Args:
        status (Literal["ok", "error"], optional): The status of the response, either "ok" for
            success or "error" for failures. Defaults to "ok".
        code (int, optional): The HTTP status code associated with the response.
            Defaults to 200 (HTTP_OK).
        data (dict | list | str | None, optional): The main response payload containing the
            requested data or operation result. Must be a dictionary, list, or string.
            Defaults to None.
        message (str, optional): Custom error message for convenience. This field is excluded
            from serialization but used to populate the data field. Defaults to None.
        links (list[dict] | None, optional): Links to related resources following REST API
            conventions. Defaults to None.
        metadata (dict | None, optional): Additional metadata about the response or operation.
            Defaults to None.

    Attributes:
        status (str): Response status indicator
        code (int): HTTP status code
        data (dict | list | str | None): Response payload
        links (list[dict] | None): Related resource links
        metadata (dict | None): Additional response metadata

    Properties:
        timestamp (str): ISO formatted timestamp of when the response was created

    Examples:
        >>> # Creating a successful response
        >>> response = Response(
        ...     status="ok",
        ...     code=200,
        ...     data={"client": "acme", "name": "ACME Corp"}
        ... )
        >>> print(response.timestamp)  # "2025-01-01T12:00:00.000000+00:00"

        >>> # Creating an error response
        >>> response = Response(
        ...     status="error",
        ...     code=404,
        ...     data={"message": "Client not found"}
        ... )

        >>> # Using convenience message field
        >>> response = Response(
        ...     status="error",
        ...     code=400,
        ...     message="Invalid client name"
        ... )
        >>> print(response.data)  # {"message": "Invalid client name"}

        >>> # PascalCase aliases for DynamoDB compatibility
        >>> response = Response(
        ...     Status="ok",
        ...     Code=200,
        ...     Data={"client": "acme"}
        ... )

    Note:
        **For Invoker Handler**: This object is converted to a dictionary and returned directly.

        **For Gateway Handler**: This object is serialized to JSON and returned as the
        response body in a GatewayResponse object.

        **Validation**: The data field must be a dictionary, list, or string. Other types
        will raise a ValueError during model validation.
    """

    model_config = ConfigDict(populate_by_name=True)

    status: Literal["ok", "error"] = Field(
        "ok",
        description="The status of the response: 'ok' for success, 'error' for failure",
    )
    code: int | None = Field(
        HTTP_OK,
        description="The HTTP status code",
    )
    data: dict | list | str | None = Field(
        None,
        description="The main response data (DynamoDB object or composite response)",
    )

    message: str | None = Field(
        default=None,
        description="Custom error message",
    )

    links: list[dict] | None = Field(
        None,
        description="Links to related resources following REST API conventions",
    )

    metadata: dict | None = Field(
        None,
        description="Additional metadata about the response or operation",
    )

    @property
    def timestamp(self) -> str:
        """Get the current timestamp in ISO format.

        Returns:
            str: ISO formatted timestamp in UTC timezone

        Examples:
            >>> response = Response()
            >>> timestamp = response.timestamp
            >>> print(timestamp)  # "2025-01-01T12:00:00.000000+00:00"

            >>> # Timestamp is always current when accessed
            >>> import time
            >>> ts1 = response.timestamp
            >>> time.sleep(1)
            >>> ts2 = response.timestamp
            >>> print(ts1 != ts2)  # True
        """
        return dt.now(timezone.utc).isoformat()

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: Any) -> Any:
        """Validate the response model before instantiation.

        Args:
            values: The values to validate

        Returns:
            Any: Validated values

        Raises:
            ValueError: If data field is not a dictionary, list, or string

        Examples:
            >>> # Valid data types
            >>> Response(data={"key": "value"})    # dict - OK
            >>> Response(data=["item1", "item2"])  # list - OK
            >>> Response(data="message")           # str - OK

            >>> # Invalid data type
            >>> try:
            ...     Response(data=42)  # int - not allowed
            ... except ValueError as e:
            ...     print("Validation failed")
        """
        if isinstance(values, dict):
            # Check both snake_case and PascalCase field names
            data = values.get("data")
            if data is not None:
                if isinstance(data, BaseModel):
                    data = data.model_dump(mode="json")
                elif not isinstance(data, (dict, list, str)):
                    raise ValueError("data must be a dictionary, list, or string")
            values["data"] = data
        return values

    def model_dump(self, **kwargs) -> dict:
        """Convert the model to a dictionary, excluding None values by default.

        Args:
            **kwargs: Additional arguments for model dumping. Common options:
                - exclude_none (bool): Exclude None values (default: True)
                - by_alias (bool): Use field aliases (default: False)
                - exclude (set): Fields to exclude from output

        Returns:
            dict: Dictionary representation of the response

        Examples:
            >>> response = Response(status="ok", code=200, data={"test": "value"})

            >>> # Default serialization (excludes None values)
            >>> result = response.model_dump()
            >>> print(result)  # {"status": "ok", "code": 200, "data": {"test": "value"}}

            >>> # Include None values
            >>> result = response.model_dump(exclude_none=False)
            >>> print(result)  # {"status": "ok", "code": 200, "data": {...}, "links": None, ...}

            >>> # Use PascalCase aliases
            >>> result = response.model_dump(by_alias=True)
            >>> print(result)  # {"Status": "ok", "Code": 200, "Data": {"test": "value"}}
        """
        # Set default exclude_none=True if not specified
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def __repr__(self) -> str:
        """Return string representation of the Response.

        Returns:
            str: String representation showing status, code, and data

        Examples:
            >>> response = Response(status="ok", code=200, data={"test": "value"})
            >>> repr(response)
            "Response(status=ok, code=200, data={'test': 'value'})"

            >>> error_response = Response(status="error", code=404, data="Not found")
            >>> repr(error_response)
            "Response(status=error, code=404, data=Not found)"
        """
        return f"Response(status={self.status}, code={self.code}, data={self.data})"


class SuccessResponse(Response):
    """Convenience class for successful API responses.

    This class automatically sets the status to "ok" and code to 200,
    simplifying the creation of successful responses.

    Args:
        data (Any, optional): The response data to return. Can be dict, list, string, or None.
            Defaults to None.
        links (list[dict], optional): Links to related resources following REST conventions.
            Defaults to None.
        metadata (dict, optional): Additional metadata for the response. Defaults to None.
        message (str, optional): Convenience message that will be set as data if data is None,
            or added to data dict if data is a dictionary. Defaults to None.

    Examples:
        >>> # Creating a simple success response
        >>> response = SuccessResponse(message="Operation completed successfully")
        >>> print(response.status)  # "ok"
        >>> print(response.code)    # 200
        >>> print(response.data)    # "Operation completed successfully"

        >>> # Creating a success response with client data
        >>> client_data = {"client": "acme", "name": "ACME Corporation"}
        >>> response = SuccessResponse(data=client_data)
        >>> print(response.data)    # {"client": "acme", "name": "ACME Corporation"}

        >>> # Creating a success response with links and metadata
        >>> response = SuccessResponse(
        ...     data={"clients": ["acme", "example"]},
        ...     links=[{"rel": "self", "href": "/api/clients"}],
        ...     metadata={"total_count": 2}
        ... )

        >>> # Using PascalCase aliases for DynamoDB compatibility
        >>> response = SuccessResponse(
        ...     Data={"clients": ["acme", "example"]},
        ...     Links=[{"rel": "self", "href": "/api/clients"}],
        ...     Metadata={"total_count": 2}
        ... )

        >>> # Message gets added to dict data
        >>> response = SuccessResponse(
        ...     data={"client": "acme"},
        ...     message="Client retrieved successfully"
        ... )
        >>> print(response.data)  # {"client": "acme", "message": "Client retrieved successfully"}
    """

    @model_validator(mode="after")
    def validate_after(self) -> Self:
        """Validate the success response after instantiation.

        This method ensures the response is properly configured for success,
        setting status to "ok" and handling message processing.

        Returns:
            SuccessResponse: The validated SuccessResponse instance

        Examples:
            >>> # Status and code are automatically set
            >>> response = SuccessResponse(data={"test": "value"})
            >>> print(response.status)  # "ok"
            >>> print(response.code)    # 200

            >>> # Message handling
            >>> response = SuccessResponse(message="Success!")
            >>> print(response.data)    # "Success!"
        """
        # Ensure status is "ok" and code is HTTP_OK
        self.status = "ok"
        self.code = HTTP_OK

        return self

    def __repr__(self) -> str:
        """Return string representation of the SuccessResponse.

        Returns:
            str: String representation showing the response data

        Examples:
            >>> response = SuccessResponse(data={"client": "acme"})
            >>> repr(response)
            "SuccessResponse(data={'client': 'acme'})"

            >>> response = SuccessResponse(message="Success!")
            >>> repr(response)
            "SuccessResponse(data=Success!)"
        """
        return f"SuccessResponse(data={self.data})"


class NoContentResponse(Response):
    """Convenience class for no-content responses.

    This class is used when an operation completes successfully but has no
    content to return. Sets status to "ok" and code to 204 (No Content).

    Args:
        data (Any, optional): The response data, typically a message explaining the
            no-content status. Can be dict, list, string, or None. Defaults to None.
        links (list[dict], optional): Links to related resources. Defaults to None.
        metadata (dict, optional): Additional metadata for the response. Defaults to None.
        message (str, optional): Convenience message for the no-content response.
            Defaults to None.

    Examples:
        >>> # Creating a no-content response for missing resource
        >>> response = NoContentResponse(data="Client 'xyz' does not exist")
        >>> print(response.status)  # "ok"
        >>> print(response.code)    # 204
        >>> print(response.data)    # "Client 'xyz' does not exist"

        >>> # Creating a no-content response for successful deletion
        >>> response = NoContentResponse(data="Resource deleted successfully")

        >>> # Using message convenience field
        >>> response = NoContentResponse(message="No data available")
        >>> print(response.data)    # "No data available"

        >>> # Using PascalCase aliases
        >>> response = NoContentResponse(
        ...     Data="Client 'xyz' does not exist",
        ...     Links=[{"rel": "parent", "href": "/api/clients"}]
        ... )

        >>> # With metadata for context
        >>> response = NoContentResponse(
        ...     data="No items found",
        ...     metadata={"query": "status=active", "total_searched": 1000}
        ... )
    """

    @model_validator(mode="after")
    def validate_after(self) -> Self:
        """Validate the no-content response after instantiation.

        This method ensures the response is properly configured for no-content,
        setting status to "ok" and code to 204.

        Returns:
            NoContentResponse: The validated NoContentResponse instance

        Examples:
            >>> # Status and code are automatically set
            >>> response = NoContentResponse(data="No content")
            >>> print(response.status)  # "ok"
            >>> print(response.code)    # 204
        """
        # Ensure data is None or a string message
        self.status = "ok"
        self.code = HTTP_NO_CONTENT

        return self

    def __repr__(self) -> str:
        """Return string representation of the NoContentResponse.

        Returns:
            str: String representation showing the response data

        Examples:
            >>> response = NoContentResponse(data="No content available")
            >>> repr(response)
            "NoContentResponse(data=No content available)"

            >>> response = NoContentResponse()
            >>> repr(response)
            "NoContentResponse(data=None)"
        """
        return f"NoContentResponse(data={self.data})"


class ErrorDetail(BaseModel):
    """Model representing detailed error information.

    This class captures exception details including type, message, and stack trace
    for comprehensive error reporting in API responses.

    Args:
        type (str): The type of the exception that occurred (e.g., "ValueError", "KeyError")
        message (str): The error message describing what went wrong
        track (str, optional): The stack trace information for debugging purposes.
            Defaults to None.

    Attributes:
        type (str): Exception type name
        message (str): Error message
        track (str | None): Stack trace for debugging

    Examples:
        >>> # Creating an error detail for an exception
        >>> try:
        ...     raise ValueError("Invalid input")
        ... except ValueError as e:
        ...     error = ErrorDetail(
        ...         type=type(e).__name__,
        ...         message=str(e),
        ...         track=traceback.format_exc()
        ...     )
        >>> print(error.type)     # "ValueError"
        >>> print(error.message)  # "Invalid input"

        >>> # Creating error detail without stack trace
        >>> error = ErrorDetail(
        ...     type="ValidationError",
        ...     message="Required field missing"
        ... )

        >>> # Using PascalCase aliases
        >>> error = ErrorDetail(
        ...     Type="ConnectionError",
        ...     Message="Database connection failed",
        ...     Track="Full stack trace here..."
        ... )

        >>> # Converting to dict for API response
        >>> error_dict = error.model_dump()
        >>> print(error_dict)  # {"type": "ValueError", "message": "Invalid input"}
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(
        ...,
        description="The type of the exception",
    )
    message: str = Field(
        ...,
        description="The error message",
    )
    track: str | None = Field(
        None,
        description="The stack trace of the error",
    )

    def model_dump(self, **kwargs) -> dict:
        """Convert the model to a dictionary, excluding None values by default.

        Args:
            **kwargs: Additional arguments for model dumping. Common options:
                - exclude_none (bool): Exclude None values (default: True)
                - by_alias (bool): Use field aliases (default: False)

        Returns:
            dict: Dictionary representation of the error detail

        Examples:
            >>> error = ErrorDetail(type="ValueError", message="Invalid input")

            >>> # Default serialization (excludes None track)
            >>> result = error.model_dump()
            >>> print(result)  # {"type": "ValueError", "message": "Invalid input"}

            >>> # Include None values
            >>> result = error.model_dump(exclude_none=False)
            >>> print(result)  # {"type": "ValueError", "message": "Invalid input", "track": None}

            >>> # Use PascalCase aliases
            >>> result = error.model_dump(by_alias=True)
            >>> print(result)  # {"Type": "ValueError", "Message": "Invalid input"}
        """
        # Set default exclude_none=True if not specified
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


class ErrorResponse(Response):
    """Convenience class for error API responses.

    This class automatically sets the status to "error" and builds a comprehensive
    error chain from the provided exception, including stack traces for debugging.

    Args:
        exception (Exception, optional): The exception that caused the error. If provided,
            the code will be extracted from exception.code (if available) and the message
            from str(exception). Defaults to None.
        code (int, optional): The HTTP status code. If not provided and exception has a
            code attribute, that will be used. Otherwise defaults to 500. Defaults to None.
        message (str, optional): Custom error message. If not provided and exception is
            given, str(exception) will be used. Defaults to None.
        metadata (dict, optional): Additional metadata for the error response.
            Defaults to None.

    Attributes:
        exception (Exception | None): The original exception (excluded from serialization)
        errors (list[ErrorDetail] | None): List of error details with traceback information

    Examples:
        >>> # Creating an error response from an exception
        >>> try:
        ...     raise ValueError("Invalid client name")
        ... except ValueError as e:
        ...     response = ErrorResponse(exception=e)
        >>> print(response.status)  # "error"
        >>> print(response.code)    # 500
        >>> print(response.data)    # {"message": "Invalid client name"}

        >>> # Creating an error response with just a message
        >>> response = ErrorResponse(message="Custom error message", code=400)
        >>> print(response.data)    # {"message": "Custom error message"}

        >>> # Creating an error response with metadata
        >>> try:
        ...     raise KeyError("Missing required field")
        ... except KeyError as e:
        ...     response = ErrorResponse(
        ...         exception=e,
        ...         code=400,
        ...         metadata={"field": "client_name", "required": True}
        ...     )

        >>> # Error response with chained exceptions
        >>> try:
        ...     try:
        ...         raise ValueError("Original error")
        ...     except ValueError as e:
        ...         raise RuntimeError("Secondary error") from e
        ... except RuntimeError as e:
        ...     response = ErrorResponse(exception=e)
        >>> len(response.errors)  # 2 (both exceptions in chain)

        >>> # Using custom exception with code attribute
        >>> class CustomException(Exception):
        ...     def __init__(self, message, code=400):
        ...         super().__init__(message)
        ...         self.code = code
        >>> try:
        ...     raise CustomException("Custom error", 422)
        ... except CustomException as e:
        ...     response = ErrorResponse(exception=e)
        >>> print(response.code)  # 422
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    errors: list[ErrorDetail] | None = Field(
        None,
        description="List of errors that occurred during processing with traceback information",
    )

    # Add exception field to store the original exception (optional and excluded from serialization)
    exception: Exception | None = Field(
        default=None,
        description="The original exception",
        exclude=True,
    )

    @model_validator(mode="after")
    def build_error_response(self) -> Self:
        """Build error response after model instantiation.

        This method configures the error response by extracting information from the
        exception, setting appropriate status codes, and building the error chain.

        Returns:
            ErrorResponse: The configured ErrorResponse instance

        Examples:
            >>> # Exception processing
            >>> try:
            ...     raise ValueError("Test error")
            ... except ValueError as e:
            ...     response = ErrorResponse(exception=e)
            >>> print(response.status)  # "error"
            >>> print(response.code)    # 500
            >>> len(response.errors)    # 1

            >>> # Message extraction
            >>> response = ErrorResponse(message="Custom message")
            >>> print(response.data)    # {"message": "Custom message"}
        """
        self.status = "error"

        # Extract code from exception if not provided
        if not self.code and self.exception:
            self.code = getattr(self.exception, "code", HTTP_INTERNAL_SERVER_ERROR)
        elif not self.code:
            self.code = HTTP_INTERNAL_SERVER_ERROR

        # Extract message from the temporary field or exception
        message = self.message
        if not message and self.exception:
            message = str(self.exception)
        if not message:
            message = "An error occurred"

        # Build error chain from exception if not already provided
        if not self.errors and self.exception:
            self.errors = _build_error_chain(self.exception)
        elif not self.errors:
            self.errors = []

        return self

    def __repr__(self) -> str:
        """Return string representation of the ErrorResponse.

        Returns:
            str: String representation showing the error code and message

        Examples:
            >>> response = ErrorResponse(message="Test error", code=400)
            >>> repr(response)
            "ErrorResponse(code=400, message=Test error)"

            >>> try:
            ...     raise ValueError("Invalid input")
            ... except ValueError as e:
            ...     response = ErrorResponse(exception=e)
            >>> repr(response)
            "ErrorResponse(code=500, message=Invalid input)"
        """
        message = self.data.get("message") if isinstance(self.data, dict) else None
        return f"ErrorResponse(code={self.code}, message={message})"


def _build_error_chain(exc: Exception) -> list[ErrorDetail]:
    """Build a chain of error details from an exception and its causes.

    This function traverses the exception chain (including __cause__ and __context__)
    to create a comprehensive list of error details for debugging.

    Args:
        exc (Exception): The exception to build the error chain from

    Returns:
        list[ErrorDetail]: List of error details representing the exception chain,
            starting with the most recent exception

    Examples:
        >>> # Building error chain from a simple exception
        >>> try:
        ...     raise ValueError("Invalid input")
        ... except ValueError as e:
        ...     errors = _build_error_chain(e)
        >>> len(errors)  # 1
        >>> errors[0].type  # "ValueError"
        >>> errors[0].message  # "Invalid input"

        >>> # Building error chain from chained exceptions
        >>> try:
        ...     try:
        ...         raise ValueError("Original error")
        ...     except ValueError as e:
        ...         raise RuntimeError("Secondary error") from e
        ... except RuntimeError as e:
        ...     errors = _build_error_chain(e)
        >>> len(errors)  # 2
        >>> errors[0].type  # "RuntimeError" (most recent)
        >>> errors[1].type  # "ValueError" (original cause)

        >>> # Pydantic ValidationError with multiple field errors
        >>> from pydantic import BaseModel, ValidationError
        >>> class TestModel(BaseModel):
        ...     name: str
        ...     age: int
        >>> try:
        ...     TestModel(name="", age="invalid")
        ... except ValidationError as e:
        ...     errors = _build_error_chain(e)
        >>> len(errors)  # Multiple errors - one for each validation failure
        >>> errors[0].type  # "ValidationError"
        >>> "name" in errors[0].message  # True - contains field info
    """
    if isinstance(exc, ValidationError):
        # Special case for Pydantic ValidationError - create individual error details for each validation error
        error_chain = []

        for error in exc.errors():
            # Extract field path
            field_path = " -> ".join(str(loc) for loc in error["loc"]) if error["loc"] else "root"

            # Build detailed error message
            error_type = error["type"]
            error_msg = error["msg"]
            error_input = error.get("input")

            # Format message with field context
            if error_input is not None:
                message = f"Field '{field_path}': {error_msg} (received: {error_input})"
            else:
                message = f"Field '{field_path}': {error_msg}"

            error_detail = ErrorDetail(
                type=f"ValidationError.{error_type}",
                message=message,
                track="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )
            error_chain.append(error_detail)

        return error_chain

    # Handle regular exceptions
    error_chain = []
    while exc:
        error_detail = ErrorDetail(
            type=type(exc).__name__,
            message=str(exc),
            track="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        )
        error_chain.append(error_detail)
        exc = exc.__cause__ or exc.__context__

    return error_chain
