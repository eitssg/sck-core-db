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


class Response(BaseModel):
    """
    Base response model for all API responses.

    This object is returned by all database actions and can be serialized
    to JSON for API responses. It provides a consistent structure for both
    successful and error responses.

    :param status: The status of the response, either "ok" for success or "error" for failures
    :type status: Literal["ok", "error"]
    :param code: The HTTP status code associated with the response (default: 200)
    :type code: int, optional
    :param data: The main response payload containing the requested data or operation result
    :type data: dict | list | str | None
    :param links: Links to related resources following REST API conventions
    :type links: list[dict] | None
    :param metadata: Additional metadata about the response or operation
    :type metadata: dict | None

    **Properties**

    :property timestamp: ISO formatted timestamp of when the response was created
    :type timestamp: str

    **Examples**

    Creating a successful response::

        response = Response(
            status="ok",
            code=200,
            data={"client": "acme", "name": "ACME Corp"}
        )

    Creating an error response::

        response = Response(
            status="error",
            code=404,
            data={"message": "Client not found"},
            errors=[ErrorDetail(type="NotFoundException", message="Client 'xyz' does not exist")]
        )

    **Notes**

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
        alias="Status",
    )
    code: int | None = Field(HTTP_OK, description="The HTTP status code", alias="Code")
    data: dict | list | str | None = Field(
        None,
        description="The main response data (DynamoDB object or composite response)",
        alias="Data",
    )
    # Add optional message field for convenience
    message: str | None = Field(default=None, description="Custom error message", exclude=True, alias="Message")

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

    @model_validator(mode="after")
    def validate_after(self) -> "Response":
        """
        Validate the response model after instantiation.

        This method can be used to perform additional validation checks
        after the model has been created.

        :returns: The validated Response instance
        :rtype: Response
        """
        # Example: Ensure status is either "ok" or "error"
        if self.status not in ["ok", "error"]:
            raise ValueError("status must be 'ok' or 'error'")

        if self.message:
            if self.data is None:
                self.data = self.message
            if isinstance(self.data, dict):
                if "message" not in self.data:
                    self.data["message"] = self.message

        return self

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

    :param data: The response data to return
    :type data: Any, optional
    :param links: Links to related resources
    :type links: list[dict[str, Any]], optional
    :param metadata: Additional metadata for the response
    :type metadata: dict, optional

    **Examples**

    Creating a simple success response::

        response = SuccessResponse(message="Operation completed successfully")

    Creating a success response with client data::

        client_data = {"client": "acme", "name": "ACME Corporation"}
        response = SuccessResponse(data=client_data)

    Creating a success response with links and metadata::

        response = SuccessResponse(
            data={"clients": ["acme", "example"]},
            links=[{"rel": "self", "href": "/api/clients"}],
            metadata={"total_count": 2}
        )

    Using PascalCase aliases::

        response = SuccessResponse(
            Data={"clients": ["acme", "example"]},
            Links=[{"rel": "self", "href": "/api/clients"}],
            Metadata={"total_count": 2}
        )
    """

    @model_validator(mode="after")
    def validate_after(self) -> "SuccessResponse":
        """
        Validate the success response after instantiation.

        This method can be used to perform additional validation checks
        after the model has been created.

        :returns: The validated SuccessResponse instance
        :rtype: SuccessResponse
        """
        # Ensure status is "ok" and code is HTTP_OK
        self.status = "ok"
        self.code = HTTP_OK

        if self.message:
            if self.data is None:
                self.data = self.message
            elif isinstance(self.data, dict):
                if "message" not in self.data:
                    self.data["message"] = self.message

        return self

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

    :param data: The response data (typically a message explaining the no-content status)
    :type data: Any
    :param links: Links to related resources
    :type links: list[dict[str, Any]], optional
    :param metadata: Additional metadata for the response
    :type metadata: dict, optional

    **Examples**

    Creating a no-content response::

        response = NoContentResponse(data="Client 'xyz' does not exist")

    Creating a no-content response for a successful deletion::

        response = NoContentResponse(data="Resource deleted successfully")

    Using PascalCase aliases::

        response = NoContentResponse(
            Data="Client 'xyz' does not exist",
            Links=[{"rel": "parent", "href": "/api/clients"}]
        )
    """

    @model_validator(mode="after")
    def validate_after(self) -> "NoContentResponse":
        """
        Validate the no-content response after instantiation.

        This method can be used to perform additional validation checks
        after the model has been created.

        :returns: The validated NoContentResponse instance
        :rtype: NoContentResponse
        """
        # Ensure data is None or a string message
        self.status = "ok"
        self.code = HTTP_NO_CONTENT

        return self

    def __repr__(self) -> str:
        """
        Return string representation of the NoContentResponse.

        :returns: String representation showing the response data
        :rtype: str
        """
        return f"NoContentResponse(data={self.data})"


class ErrorDetail(BaseModel):
    """
    Model representing detailed error information.

    This class captures exception details including type, message, and stack trace
    for comprehensive error reporting in API responses.

    :param type: The type of the exception that occurred
    :type type: str
    :param message: The error message describing what went wrong
    :type message: str
    :param track: The stack trace information for debugging purposes
    :type track: str, optional

    **Examples**

    Creating an error detail for an exception::

        try:
            raise ValueError("Invalid input")
        except ValueError as e:
            error = ErrorDetail(
                type=type(e).__name__,
                message=str(e),
                track=traceback.format_exc()
            )
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(..., description="The type of the exception", alias="Type")
    message: str = Field(..., description="The error message", alias="Message")
    track: str | None = Field(None, description="The stack trace of the error", alias="Track")

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


class ErrorResponse(Response):
    """
    Convenience class for error API responses.

    This class automatically sets the status to "error" and builds a comprehensive
    error chain from the provided exception, including stack traces for debugging.

    :param exception: The exception that caused the error (default: None)
    :type exception: Exception, optional
    :param code: The HTTP status code (defaults to exception.code if available, otherwise 500)
    :type code: int, optional
    :param message: Custom error message (defaults to str(exception) if provided)
    :type message: str, optional
    :param metadata: Additional metadata for the error response
    :type metadata: dict, optional

    **Examples**

    Creating an error response from an exception::

        try:
            raise ValueError("Invalid client name")
        except ValueError as e:
            response = ErrorResponse(exception=e)

    Creating an error response with just a message::

        response = ErrorResponse(message="Custom error message", code=400)

    Creating an error response with metadata::

        try:
            raise KeyError("Missing required field")
        except KeyError as e:
            response = ErrorResponse(
                exception=e,
                code=400,
                metadata={"field": "client_name", "required": True}
            )
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    # Add exception field to store the original exception (optional and excluded from serialization)
    exception: Exception | None = Field(default=None, description="The original exception", exclude=True, alias="Exception")

    errors: list[ErrorDetail] | None = Field(
        None,
        description="List of errors that occurred during processing with traceback information",
        alias="Errors",
    )

    @model_validator(mode="after")
    def build_error_response(self) -> "ErrorResponse":
        """
        Build error response after model instantiation.

        :returns: The configured ErrorResponse instance
        :rtype: ErrorResponse
        """
        # Extract message from the temporary field or exception
        message = self.message
        if not message and self.exception:
            message = str(self.exception)
        if not message:
            message = "An error occurred"

        # Extract code from exception if not provided
        if not self.code and self.exception:
            self.code = getattr(self.exception, "code", HTTP_INTERNAL_SERVER_ERROR)
        elif not self.code:
            self.code = HTTP_INTERNAL_SERVER_ERROR

        # FORCE status to "error" - ignore any user attempt to override
        self.status = "error"

        # Set the data field with the message
        if isinstance(self.data, dict):
            self.data["message"] = message
        else:
            self.data = {"message": message}

        # Build error chain from exception if not already provided
        if not self.errors and self.exception:
            self.errors = _build_error_chain(self.exception)
        elif not self.errors:
            self.errors = []

        return self

    def __repr__(self) -> str:
        """
        Return string representation of the ErrorResponse.

        :returns: String representation showing the error code and message
        :rtype: str
        """
        message = self.data.get("message") if isinstance(self.data, dict) else None
        return f"ErrorResponse(code={self.code}, message={message})"


def _build_error_chain(exc: Exception) -> list[ErrorDetail]:
    """
    Build a chain of error details from an exception and its causes.

    This function traverses the exception chain (including __cause__ and __context__)
    to create a comprehensive list of error details for debugging.

    :param exc: The exception to build the error chain from
    :type exc: Exception
    :returns: List of error details representing the exception chain
    :rtype: list[ErrorDetail]

    **Examples**

    Building error chain from a simple exception::

        try:
            raise ValueError("Invalid input")
        except ValueError as e:
            errors = _build_error_chain(e)

    Building error chain from chained exceptions::

        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise RuntimeError("Secondary error") from e
        except RuntimeError as e:
            errors = _build_error_chain(e)  # Will include both exceptions
    """
    error_chain = []
    while exc:
        error_detail = ErrorDetail(
            type=type(exc).__name__,
            message=str(exc),
            track="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        )
        error_chain.append(error_detail)
        exc = exc.__cause__ or exc.__context__  # type: ignore

    return error_chain
