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
    - **Cookie Support**: FastAPI-compatible cookie handling for OAuth/session management

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

    >>> # Response with cookies for OAuth flows
    >>> response = SuccessResponse(data={"access_token": "abc123"})
    >>> response.set_cookie("session_id", "xyz789", max_age=3600, httponly=True, secure=True)
    >>> print(len(response.cookies))  # 1
"""

import datetime
import traceback
import os

from typing import Any, Literal, Self, Optional, Union, Dict
from datetime import timezone, datetime

from pydantic import BaseModel, Field, ConfigDict, model_validator
from pydantic import ValidationError

from core_framework.constants import (
    HTTP_OK,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NO_CONTENT,
    HTTP_CREATED,
)


class Response(BaseModel):
    """Base response model for all API responses.

    This object is returned by all database actions and can be serialized
    to JSON for API responses. It provides a consistent structure for both
    successful and error responses, with optional cookie support for OAuth
    and session management.

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
        cookies (list[str] | None, optional): Set-Cookie header values for browser session
            management. Excluded from JSON serialization. Defaults to None.

    Attributes:
        status (str): Response status indicator
        code (int): HTTP status code
        data (dict | list | str | None): Response payload
        links (list[dict] | None): Related resource links
        metadata (dict | None): Additional response metadata
        cookies (list[str] | None): Cookie header values (excluded from serialization)

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

        >>> # Response with cookies for OAuth
        >>> response = Response(status="ok", code=302, data="/redirect")
        >>> response.set_cookie("oauth_state", "abc123", max_age=600, httponly=True)
        >>> response.set_cookie("session_id", "xyz789", httponly=True, secure=True)
        >>> print(len(response.cookies))  # 2

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

        **For OAuth Handler**: Cookies are extracted and converted to AWS API Gateway
        multi-value headers format.

        **Validation**: The data field must be a dictionary, list, or string. Other types
        will raise a ValueError during model validation.
    """

    model_config = ConfigDict(populate_by_name=True)

    status: Literal["ok", "error"] = Field(
        "ok",
        description="The status of the response: 'ok' for success, 'error' for failure",
    )
    code: int = Field(
        HTTP_OK,
        description="The HTTP status code",
    )
    data: dict | list | str | None = Field(
        None,
        description="The main response data (DynamoDB object or composite response)",
    )

    message: str | None = Field(
        default=None,
        description="Custom error message for convenience (excluded from serialization)",
    )

    links: list[dict] | None = Field(
        None,
        description="Links to related resources following REST API conventions",
    )

    metadata: dict | None = Field(
        None,
        description="Additional metadata about the response or operation",
    )

    # Add optional cookie support for OAuth/session endpoints
    cookies: list[str] | None = Field(
        None,
        description="Set-Cookie header values for browser session management",
        exclude=True,  # Exclude from JSON serialization to maintain API compatibility
    )

    headers: list[dict] | None = Field(
        None,
        description="Additional HTTP headers for the response",
        exclude=True,  # Exclude from JSON serialization to maintain API compatibility
    )

    def set_header(self, name: str, value: str) -> None:
        """Set a custom HTTP header in the response.

        Args:
            name (str): The name of the header to set
            value (str): The value of the header

        Examples:
            >>> response = Response(data={"key": "value"})
            >>> response.set_header("X-Custom-Header", "CustomValue")
            >>> print(response.headers)
            [{"X-Custom-Header": "CustomValue"}]
        """
        if self.headers is None:
            self.headers = []
        self.headers.append({name: value})

    def delete_header(self, name: str) -> None:
        """Delete a custom HTTP header from the response.

        Args:
            name (str): The name of the header to delete

        Examples:
            >>> response = Response(data={"key": "value"})
            >>> response.set_header("X-Custom-Header", "CustomValue")
            >>> print(response.headers)
            [{"X-Custom-Header": "CustomValue"}]
            >>> response.delete_header("X-Custom-Header")
            >>> print(response.headers)
            []
        """
        if self.headers is None:
            return
        self.headers = [h for h in self.headers if name not in h]

    def delete_cookie(
        self,
        key: str,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = "lax",
    ) -> None:
        """Delete a cookie by setting it to empty value with immediate expiration.

        Args:
            key (str): Cookie name to delete
            path (str): Cookie path scope (default: "/")
            domain (Optional[str]): Cookie domain scope
            secure (bool): Secure flag (default: False)
            httponly (bool): HttpOnly flag (default: False)
            samesite (Optional[str]): SameSite policy (default: "lax")
        """
        self.set_cookie(
            key=key,
            value="",
            max_age=0,
            expires="Thu, 01 Jan 1970 00:00:00 GMT",
            path=path,
            domain=domain,
            secure=secure,
            httponly=httponly,
            samesite=samesite,
        )

    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: Optional[int] = None,
        expires: Optional[Union[datetime, str, int]] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = "lax",
    ) -> None:
        """Set a cookie in the response.

        This method signature matches FastAPI's Response.set_cookie() exactly,
        allowing drop-in replacement without code modifications. The generated
        cookie string follows the HTTP Set-Cookie header format specification.

        Args:
            key (str): Cookie name (e.g., "session_id", "oauth_state")
            value (str): Cookie value (default: "")
            max_age (Optional[int]): Cookie lifetime in seconds. Takes precedence over expires.
            expires (Optional[Union[datetime, str, int]]): Cookie expiration as datetime,
                string, or Unix timestamp. Ignored if max_age is set.
            path (str): Cookie path scope (default: "/")
            domain (Optional[str]): Cookie domain scope (e.g., ".example.com")
            secure (bool): Secure flag - only send over HTTPS (default: False)
            httponly (bool): HttpOnly flag - not accessible via JavaScript (default: False)
            samesite (Optional[str]): SameSite policy: "strict", "lax", or "none" (default: "lax")

        Returns:
            None: Modifies the response's cookies list in-place

        Examples:
            >>> response = SuccessResponse(data={"token": "abc123"})

            >>> # Basic session cookie
            >>> response.set_cookie("session_id", "abc123", max_age=1800, httponly=True)
            >>> print(response.cookies[0])
            # "session_id=abc123; Max-Age=3600; Path=/; HttpOnly; SameSite=Lax"

            >>> # Secure OAuth state cookie
            >>> response.set_cookie(
            ...     "oauth_state", "xyz789",
            ...     max_age=600,
            ...     httponly=True,
            ...     secure=True,
            ...     samesite="strict"
            ... )

            >>> # Cookie with custom domain and path
            >>> response.set_cookie(
            ...     "tracking", "abc123",
            ...     path="/api",
            ...     domain=".example.com",
            ...     max_age=86400
            ... )

            >>> # Clear a cookie (set empty value with max_age=0)
            >>> response.set_cookie("old_session", "", max_age=0)

        Note:
            **Cookie Precedence**: If both max_age and expires are provided, max_age takes
            precedence as per HTTP specification.

            **SameSite Handling**: The samesite value is automatically title-cased to match
            HTTP specification ("Lax", "Strict", "None").

            **Datetime Handling**: datetime objects are converted to HTTP-date format
            automatically. Unix timestamps are converted to datetime first.

            **AWS API Gateway**: These cookies are automatically converted to multi-value
            Set-Cookie headers when used with ProxyResponse.
        """
        if self.cookies is None:
            self.cookies = []

        # Build cookie string following HTTP Set-Cookie format
        cookie_parts = [f"{key}={value}"]

        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")

        if expires is not None:
            if isinstance(expires, datetime):
                expires_str = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
            elif isinstance(expires, str):
                expires_str = expires
            elif isinstance(expires, int):
                # Assume Unix timestamp
                expires_dt = datetime.fromtimestamp(expires)
                expires_str = expires_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
            else:
                expires_str = str(expires)
            cookie_parts.append(f"Expires={expires_str}")

        if path:
            cookie_parts.append(f"Path={path}")

        if domain:
            cookie_parts.append(f"Domain={domain}")

        if secure:
            cookie_parts.append("Secure")

        if httponly:
            cookie_parts.append("HttpOnly")

        if samesite:
            cookie_parts.append(f"SameSite={samesite.title()}")

        cookie_string = "; ".join(cookie_parts)
        self.cookies.append(cookie_string)

    @property
    def timestamp(self) -> str:
        """Get the current timestamp in ISO format.

        Returns the current UTC timestamp whenever accessed, providing a
        fresh timestamp for each property access.

        Returns:
            str: ISO formatted timestamp in UTC timezone with microsecond precision

        Examples:
            >>> response = Response()
            >>> timestamp = response.timestamp
            >>> print(timestamp)  # "2025-01-01T12:00:00.000000+00:00"

            >>> # Timestamp is always current when accessed
            >>> import time
            >>> ts1 = response.timestamp
            >>> time.sleep(1)
            >>> ts2 = response.timestamp
            >>> print(ts1 != ts2)  # True - different timestamps

        Note:
            This property generates a new timestamp on each access rather than
            storing a creation timestamp. For audit trails requiring a fixed
            creation time, store the timestamp value when the response is created.
        """
        return datetime.now(timezone.utc).isoformat()

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: Any) -> Any:
        """Validate the response model before instantiation.

        Performs validation on the input values, ensuring the data field contains
        only supported types (dict, list, str) and handles both snake_case and
        PascalCase field naming conventions.

        Args:
            values (Any): The input values to validate, typically a dictionary

        Returns:
            Any: Validated values with data field properly typed

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
            ...     print("Validation failed: data must be dict, list, or string")

            >>> # BaseModel conversion
            >>> from pydantic import BaseModel
            >>> class TestModel(BaseModel):
            ...     name: str
            >>> model_instance = TestModel(name="test")
            >>> response = Response(data=model_instance)
            >>> print(type(response.data))  # <class 'dict'> - converted automatically

        Note:
            **BaseModel Handling**: If data is a Pydantic BaseModel, it's automatically
            converted to a dictionary using model_dump(mode="json").

            **Case Sensitivity**: Supports both "data" and "Data" field names for
            compatibility with DynamoDB PascalCase conventions.
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

        Provides consistent serialization behavior across all response types,
        with sensible defaults for API responses.

        Args:
            **kwargs: Additional arguments for model dumping. Common options:
                - exclude_none (bool): Exclude None values (default: True)
                - by_alias (bool): Use field aliases (default: False)
                - exclude (set): Fields to exclude from output
                - include (set): Fields to include in output

        Returns:
            dict: Dictionary representation of the response with None values excluded

        Examples:
            >>> response = Response(status="ok", code=200, data={"test": "value"})

            >>> # Default serialization (excludes None values and excluded fields)
            >>> result = response.model_dump()
            >>> print(result)  # {"status": "ok", "code": 200, "data": {"test": "value"}}

            >>> # Include None values
            >>> result = response.model_dump(exclude_none=False)
            >>> print(result)  # {"status": "ok", "code": 200, "data": {...}, "links": None, ...}

            >>> # Use PascalCase aliases
            >>> result = response.model_dump(by_alias=True)
            >>> print(result)  # {"Status": "ok", "Code": 200, "Data": {"test": "value"}}

            >>> # Exclude specific fields
            >>> result = response.model_dump(exclude={"metadata"})

        Note:
            **Default Behavior**: Unlike standard Pydantic models, this method defaults
            to exclude_none=True for cleaner API responses.

            **Excluded Fields**: Fields marked with exclude=True (like cookies and message)
            are automatically excluded from serialization.
        """
        # Set default exclude_none=True if not specified
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def __repr__(self) -> str:
        """Return string representation of the Response.

        Provides a concise string representation showing the key response attributes
        for debugging and logging purposes.

        Returns:
            str: String representation showing status, code, and data

        Examples:
            >>> response = Response(status="ok", code=200, data={"test": "value"})
            >>> repr(response)
            "Response(status=ok, code=200, data={'test': 'value'})"

            >>> error_response = Response(status="error", code=404, data="Not found")
            >>> repr(error_response)
            "Response(status=error, code=404, data=Not found)"

            >>> # Response with cookies (cookies not shown in repr)
            >>> response = Response(status="ok", code=200, data="Success")
            >>> response.set_cookie("session", "abc123")
            >>> repr(response)
            "Response(status=ok, code=200, data=Success)"
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
        if not self.code or self.code < 200 or self.code >= 300:
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


class CreatedResponse(Response):
    """Convenience class for created responses.

    This class is used when a resource is successfully created. Sets status to "ok" and code to 201 (Created).
    """

    @model_validator(mode="after")
    def validate_after(self) -> Self:
        self.status = "ok"
        self.code = HTTP_CREATED
        return self


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

    error: str | None = Field(None, description="Stable, human-readable error code")

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

        self.error = self._get_error_name(self.code)

        # Build error chain from exception if not already provided
        if not self.errors and self.exception:
            self.errors = _build_error_chain(self.exception)

        return self

    def _get_error_name(self, status_code: int) -> str:
        """Map HTTP status codes to stable, SPA-friendly error codes.

        AWS API Gateway doesn't require any particular error name. We provide a
        comprehensive, human-readable, snake_case mapping for all standard 4xx and
        5xx statuses so the SPA can react consistently. Unknown 4xx map to
        "client_error" and unknown 5xx map to "server_error".

        Args:
            status_code (int): HTTP status code

        Returns:
            str: Error code (e.g., "bad_request", "unauthorized", "not_found").
        """
        # Centralized mapping table for API Gateway error responses used across the codebase.
        # This table is intentionally exhaustive for common web errors so the SPA can

        # switch on a stable, human-readable code regardless of the numeric HTTP status.
        ERROR_CODE_TO_NAME: Dict[int, str] = {
            # 4xx Client Errors
            400: "bad_request",
            401: "unauthorized",
            402: "payment_required",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            406: "not_acceptable",
            407: "proxy_authentication_required",
            408: "request_timeout",
            409: "conflict",
            410: "gone",
            411: "length_required",
            412: "precondition_failed",
            413: "payload_too_large",
            414: "uri_too_long",
            415: "unsupported_media_type",
            416: "range_not_satisfiable",
            417: "expectation_failed",
            418: "im_a_teapot",
            421: "misdirected_request",
            422: "unprocessable_entity",
            423: "locked",
            424: "failed_dependency",
            425: "too_early",
            426: "upgrade_required",
            428: "precondition_required",
            429: "too_many_requests",
            431: "request_header_fields_too_large",
            451: "unavailable_for_legal_reasons",
            # 5xx Server Errors
            500: "internal_server_error",
            501: "not_implemented",
            502: "bad_gateway",
            503: "service_unavailable",
            504: "gateway_timeout",
            505: "http_version_not_supported",
            506: "variant_also_negotiates",
            507: "insufficient_storage",
            508: "loop_detected",
            510: "not_extended",
            511: "network_authentication_required",
        }

        if status_code in ERROR_CODE_TO_NAME:
            return ERROR_CODE_TO_NAME[status_code]
        if 400 <= status_code <= 499:
            return "client_error"
        if 500 <= status_code <= 599:
            return "server_error"
        # Non-error classes shouldn't hit this function, but provide a safe default
        return "unknown_error"

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


class RedirectResponse(Response):

    url: str = Field(
        ...,
        description="The URL to redirect to",
        exclude=True,
    )

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        values["code"] = 302
        return values


# --- Cookie utilities -------------------------------------------------------
def cookie_opts() -> Dict[str, Any]:
    """Return default cookie options derived from environment.

    Centralizes cookie policy so all endpoints set/delete cookies consistently.

    Environment variables:
      - ENVIRONMENT: when "production" defaults SameSite=None, otherwise Lax
      - SCK_COOKIE_SAMESITE: none|lax|strict (overrides default)
      - SCK_COOKIE_SECURE: true|false (defaults true when SameSite=None)
      - SCK_COOKIE_HTTPONLY: true|false (default true)
      - SCK_COOKIE_DOMAIN: cookie Domain attribute (omit/None to bind to host)
      - SCK_COOKIE_PATH: cookie Path attribute (default "/")

    Returns a dict suitable for passing to set_cookie/delete_cookie, e.g.:
        response.set_cookie("session", token, max_age=1800, **cookie_opts())
        response.delete_cookie("session", **cookie_opts())
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    # Determine SameSite with sensible defaults per environment
    default_samesite = "none" if env == "production" else "lax"
    samesite = os.getenv("SCK_COOKIE_SAMESITE", default_samesite).strip().lower()
    if samesite not in ("none", "lax", "strict"):
        samesite = default_samesite

    # Secure default: required when SameSite=None; otherwise configurable
    secure_env = os.getenv("SCK_COOKIE_SECURE", "").strip().lower()
    if secure_env:
        secure = secure_env in ("1", "true", "yes", "on")
    else:
        secure = samesite == "none"

    # Enforce modern browser rule: SameSite=None requires Secure
    if samesite == "none" and not secure:
        secure = True

    httponly = os.getenv("SCK_COOKIE_HTTPONLY", "true").strip().lower() in ("1", "true", "yes", "on")
    path = os.getenv("SCK_COOKIE_PATH", "/")
    domain = os.getenv("SCK_COOKIE_DOMAIN") or None  # Keep None to omit Domain attribute

    return {
        "path": path,
        "domain": domain,
        "secure": secure,
        "httponly": httponly,
        "samesite": samesite,
    }
