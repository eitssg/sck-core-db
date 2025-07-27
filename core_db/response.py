"""Response module for the core_db package. Response objects are returned by the actions module."""

import traceback

from typing import Any, Literal
from datetime import timezone, datetime as dt

from pydantic import BaseModel, Field, ConfigDict, model_validator

from core_framework.constants import (
    HTTP_OK,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NO_CONTENT,
)


class ErrorDetail(BaseModel):
    """
    Model representing detailed error information.

    This class captures exception details including type, message, and stack trace
    for comprehensive error reporting in API responses.

    Attributes
    ----------
    type : str
        The type of the exception that occurred
    message : str
        The error message describing what went wrong
    track : str, optional
        The stack trace information for debugging purposes

    Examples
    --------
    Creating an error detail for an exception:

    >>> try:
    ...     raise ValueError("Invalid input")
    ... except ValueError as e:
    ...     error = ErrorDetail(
    ...         type=type(e).__name__,
    ...         message=str(e),
    ...         track=traceback.format_exc()
    ...     )
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )

    type: str = Field(..., description="The type of the exception", alias="Type")
    message: str = Field(..., description="The error message", alias="Message")
    track: str | None = Field(
        None, description="The stack trace of the error", alias="Track"
    )

    def model_dump(self, **kwargs) -> dict:
        """
        Convert the model to a dictionary, excluding None values by default.

        :param kwargs: Additional arguments for model dumping
        :type kwargs: dict
        :returns: Dictionary representation of the error detail
        :rtype: dict
        """
        # Set default exclude_none=True if not specified
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


class Response(BaseModel):
    """
    Base response model for all API responses.

    This object is returned by all database actions and can be serialized
    to JSON for API responses. It provides a consistent structure for both
    successful and error responses.

    Attributes
    ----------
    status : Literal["ok", "error"]
        The status of the response, either "ok" for success or "error" for failures
    code : int, optional
        The HTTP status code associated with the response (default: 200)
    data : dict | list | str | None
        The main response payload containing the requested data or operation result
    links : list[dict] | None
        Links to related resources following REST API conventions
    metadata : dict | None
        Additional metadata about the response or operation
    errors : list[ErrorDetail] | None
        List of error details if the operation failed

    Properties
    ----------
    timestamp : str
        ISO formatted timestamp of when the response was created

    Examples
    --------
    Creating a successful response:

    >>> response = Response(
    ...     status="ok",
    ...     code=200,
    ...     data={"client": "acme", "name": "ACME Corp"}
    ... )

    Creating an error response:

    >>> response = Response(
    ...     status="error",
    ...     code=404,
    ...     data={"message": "Client not found"},
    ...     errors=[ErrorDetail(type="NotFoundException", message="Client 'xyz' does not exist")]
    ... )

    Notes
    -----
    **For Invoker Handler**: This object is converted to a dictionary and returned directly.

    **For Gateway Handler**: This object is serialized to JSON and returned as the
    response body in a GatewayResponse object.

    **Validation**: The data field must be a dictionary, list, or string. Other types
    will raise a ValueError during model validation.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )

    status: Literal["ok", "error"] = Field(
        "ok",
        description="The status of the response: 'ok' for success, 'error' for failure",
        alias="Status",
    )
    code: int | None = Field(HTTP_OK, description="The HTTP status code", alias="Code")
    data: dict | list | str | None = Field(
        None,
        description="The main response data (DynamoDB object or composite response)",
        alias="Data",
    )
    links: list[dict] | None = Field(
        None,
        description="Links to related resources following REST API conventions",
        alias="Links",
    )
    metadata: dict | None = Field(
        None,
        description="Additional metadata about the response or operation",
        alias="Metadata",
    )
    errors: list[ErrorDetail] | None = Field(
        None,
        description="List of errors that occurred during processing with traceback information",
        alias="Errors",
    )

    @property
    def timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.

        :returns: ISO formatted timestamp in UTC
        :rtype: str
        """
        return dt.now(timezone.utc).isoformat()

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: Any) -> Any:
        """
        Validate the response model before instantiation.

        :param values: The values to validate
        :type values: Any
        :returns: Validated values
        :rtype: Any
        :raises ValueError: If data field is not a dictionary, list, or string
        """
        if isinstance(values, dict):
            # Check both snake_case and PascalCase field names
            data = values.get("data") or values.get("Data")
            if data is not None:
                if not isinstance(data, (dict, list, str)):
                    raise ValueError("data must be a dictionary, list, or string")
        return values

    def model_dump(self, **kwargs) -> dict:
        """
        Convert the model to a dictionary, excluding None values by default.

        :param kwargs: Additional arguments for model dumping
        :type kwargs: dict
        :returns: Dictionary representation of the response
        :rtype: dict
        """
        # Set default exclude_none=True if not specified
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def __repr__(self) -> str:
        """
        Return string representation of the Response.

        :returns: String representation showing status, code, and data
        :rtype: str
        """
        return f"Response(status={self.status}, code={self.code}, data={self.data})"


class SuccessResponse(Response):
    """
    Convenience class for successful API responses.

    This class automatically sets the status to "ok" and code to 200,
    simplifying the creation of successful responses.

    Parameters
    ----------
    data : Any, optional
        The response data to return
    links : list[dict[str, Any]], optional
        Links to related resources
    additional_data : dict, optional
        Additional metadata for the response

    Examples
    --------
    Creating a simple success response:

    >>> response = SuccessResponse({"message": "Operation completed successfully"})

    Creating a success response with client data:

    >>> client_data = {"client": "acme", "name": "ACME Corporation"}
    >>> response = SuccessResponse(client_data)

    Creating a success response with links and metadata:

    >>> response = SuccessResponse(
    ...     data={"clients": ["acme", "example"]},
    ...     links=[{"rel": "self", "href": "/api/clients"}],
    ...     additional_data={"total_count": 2}
    ... )

    Using PascalCase aliases:

    >>> response = SuccessResponse(
    ...     Data={"clients": ["acme", "example"]},
    ...     Links=[{"rel": "self", "href": "/api/clients"}],
    ...     additional_data={"total_count": 2}
    ... )
    """

    def __init__(
        self,
        data: Any = None,
        links: list[dict[str, Any]] | None = None,
        additional_data: dict | None = None,
        **kwargs,
    ):
        """
        Initialize a SuccessResponse.

        :param data: The response data to return
        :type data: Any
        :param links: Links to related resources
        :type links: list[dict[str, Any]] | None
        :param additional_data: Additional metadata for the response
        :type additional_data: dict | None
        :param kwargs: Additional keyword arguments (supports PascalCase aliases)
        :type kwargs: dict
        """
        # Handle PascalCase aliases in kwargs
        if "Data" in kwargs and data is None:
            data = kwargs.pop("Data")
        if "Links" in kwargs and links is None:
            links = kwargs.pop("Links")
        if "Metadata" in kwargs and additional_data is None:
            additional_data = kwargs.pop("Metadata")

        super().__init__(
            status="ok",
            code=HTTP_OK,
            data=data,
            links=links,
            metadata=additional_data,
            errors=None,
            **kwargs,
        )

    def __repr__(self) -> str:
        """
        Return string representation of the SuccessResponse.

        :returns: String representation showing the response data
        :rtype: str
        """
        return f"SuccessResponse(data={self.data})"


class NoContentResponse(Response):
    """
    Convenience class for no-content responses.

    This class is used when an operation completes successfully but has no
    content to return. Sets status to "ok" and code to 204 (No Content).

    Parameters
    ----------
    data : Any
        The response data (typically a message explaining the no-content status)
    links : list[dict[str, Any]], optional
        Links to related resources
    additional_data : dict, optional
        Additional metadata for the response

    Examples
    --------
    Creating a no-content response:

    >>> response = NoContentResponse("Client 'xyz' does not exist")

    Creating a no-content response for a successful deletion:

    >>> response = NoContentResponse("Resource deleted successfully")

    Using PascalCase aliases:

    >>> response = NoContentResponse(
    ...     Data="Client 'xyz' does not exist",
    ...     Links=[{"rel": "parent", "href": "/api/clients"}]
    ... )
    """

    def __init__(
        self,
        data: Any,
        links: list[dict[str, Any]] | None = None,
        additional_data: dict | None = None,
        **kwargs,
    ):
        """
        Initialize a NoContentResponse.

        :param data: The response data explaining the no-content status
        :type data: Any
        :param links: Links to related resources
        :type links: list[dict[str, Any]] | None
        :param additional_data: Additional metadata for the response
        :type additional_data: dict | None
        :param kwargs: Additional keyword arguments (supports PascalCase aliases)
        :type kwargs: dict
        """
        # Handle PascalCase aliases in kwargs
        if "Data" in kwargs and data is None:
            data = kwargs.pop("Data")
        if "Links" in kwargs and links is None:
            links = kwargs.pop("Links")
        if "Metadata" in kwargs and additional_data is None:
            additional_data = kwargs.pop("Metadata")

        super().__init__(
            status="ok",
            code=HTTP_NO_CONTENT,
            data=data,
            links=links,
            metadata=additional_data,
            errors=None,
            **kwargs,
        )

    def __repr__(self) -> str:
        """
        Return string representation of the NoContentResponse.

        :returns: String representation showing the response data
        :rtype: str
        """
        return f"NoContentResponse(data={self.data})"


def _build_error_chain(exc: Exception) -> list[ErrorDetail]:
    """
    Build a chain of error details from an exception and its causes.

    This function traverses the exception chain (including __cause__ and __context__)
    to create a comprehensive list of error details for debugging.

    :param exc: The exception to build the error chain from
    :type exc: Exception
    :returns: List of error details representing the exception chain
    :rtype: list[ErrorDetail]

    Examples
    --------
    Building error chain from a simple exception:

    >>> try:
    ...     raise ValueError("Invalid input")
    ... except ValueError as e:
    ...     errors = _build_error_chain(e)

    Building error chain from chained exceptions:

    >>> try:
    ...     try:
    ...         raise ValueError("Original error")
    ...     except ValueError as e:
    ...         raise RuntimeError("Secondary error") from e
    ... except RuntimeError as e:
    ...     errors = _build_error_chain(e)  # Will include both exceptions
    """
    error_chain = []
    while exc:
        error_detail = ErrorDetail(
            type=type(exc).__name__,
            message=str(exc),
            track="".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            ),
        )
        error_chain.append(error_detail)
        exc = exc.__cause__ or exc.__context__  # type: ignore

    return error_chain


class ErrorResponse(Response):
    """
    Convenience class for error API responses.

    This class automatically sets the status to "error" and builds a comprehensive
    error chain from the provided exception, including stack traces for debugging.

    Parameters
    ----------
    e : Exception
        The exception that caused the error
    code : int, optional
        The HTTP status code (defaults to exception.code if available, otherwise 500)
    message : str, optional
        Custom error message (defaults to str(e))
    additional_data : dict, optional
        Additional metadata for the error response

    Examples
    --------
    Creating an error response from an exception:

    >>> try:
    ...     raise ValueError("Invalid client name")
    ... except ValueError as e:
    ...     response = ErrorResponse(e)

    Creating an error response with custom code and message:

    >>> try:
    ...     raise RuntimeError("Database connection failed")
    ... except RuntimeError as e:
    ...     response = ErrorResponse(e, code=503, message="Service temporarily unavailable")

    Creating an error response with additional metadata:

    >>> try:
    ...     raise KeyError("Missing required field")
    ... except KeyError as e:
    ...     response = ErrorResponse(
    ...         e,
    ...         code=400,
    ...         additional_data={"field": "client_name", "required": True}
    ...     )

    Using PascalCase field names:

    >>> try:
    ...     raise ValueError("Invalid input")
    ... except ValueError as e:
    ...     response = ErrorResponse(
    ...         e,
    ...         Code=400,
    ...         additional_data={"Field": "client_name", "Required": True}
    ...     )
    """

    def __init__(
        self,
        e: Exception,
        *,
        code: int | None = None,
        message: str | None = None,
        additional_data: dict | None = None,
        **kwargs,
    ):
        """
        Initialize an ErrorResponse from an exception.

        :param e: The exception that caused the error
        :type e: Exception
        :param code: Custom HTTP status code
        :type code: int | None
        :param message: Custom error message
        :type message: str | None
        :param additional_data: Additional metadata for the error response
        :type additional_data: dict | None
        :param kwargs: Additional keyword arguments (supports PascalCase aliases)
        :type kwargs: dict
        """
        # Handle PascalCase aliases in kwargs
        if "Code" in kwargs and code is None:
            code = kwargs.pop("Code")
        if "Message" in kwargs and message is None:
            message = kwargs.pop("Message")
        if "Metadata" in kwargs and additional_data is None:
            additional_data = kwargs.pop("Metadata")

        if not message:
            message = str(e)
        if not code:
            code = HTTP_INTERNAL_SERVER_ERROR

        super().__init__(
            status="error",
            code=int(e.code) if hasattr(e, "code") else code,
            data={"message": message},
            links=None,
            metadata=additional_data,
            errors=_build_error_chain(e),
            **kwargs,
        )

    def __repr__(self) -> str:
        """
        Return string representation of the ErrorResponse.

        :returns: String representation showing the error code and message
        :rtype: str
        """
        message = self.data.get("message") if isinstance(self.data, dict) else None
        return f"ErrorResponse(code={self.code}, message={message})"
