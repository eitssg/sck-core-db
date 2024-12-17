import traceback

from typing import Any, Literal
from datetime import timezone, datetime as dt

from pydantic import BaseModel, Field, model_validator

from core_framework.constants import (
    HTTP_OK,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NO_CONTENT,
)


class ErrorDetail(BaseModel):
    class Config:
        exclude_none = True

    type: str = Field(..., description="The type of the Error")
    message: str = Field(..., description="The error messge")
    track: str | None = Field(None, description="The track of the error")

    # Override the model_dump method to exclude None values
    def model_dump(self, **kwargs) -> dict:
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)


class Response(BaseModel):
    """
    Base response model for all API responses

    This object is turned into a Dict and returned by the Invoker handler.

    For the gateway handler, this object is turned into a JSON string and returned as the body of the response GatewayResponse.
    """

    status: Literal["ok", "error"] = Field(
        "ok", description="The status of the response easy to see 'ok' or 'error'"
    )
    code: int | None = Field(HTTP_OK, description="The HTTP status code")
    data: dict | list | str | None = Field(
        None,
        description="The data returned by the API (DynamoDB Object or composite repsonse)",
    )
    links: list[dict] | None = Field(
        None, description="Links to related resources like you might find in a REST API"
    )
    metadata: dict | None = None

    @property
    def timestamp(self):
        return dt.now(timezone.utc).isoformat()

    errors: list[ErrorDetail] | None = Field(
        None,
        description="A list of errors that occured during processing with trackeback information",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: Any) -> Any:
        if isinstance(values, dict):
            data = values.get("data", None)
            if data:
                if (
                    not isinstance(data, dict)
                    and not isinstance(data, list)
                    and not isinstance(data, str)
                ):
                    raise ValueError("data must be a dictionary, list, or string")
        return values

    # Override the model_dump method to exclude None values
    def model_dump(self, **kwargs) -> dict:
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

    def __repr__(self):
        return f"Response(status={self.status}, code={self.code}, data={self.data})"


class SuccessResponse(Response):
    """Convenience class for success responses"""

    def __init__(
        self,
        data: Any = None,
        links: list[dict[str, Any]] | None = None,
        additional_data: dict | None = None,
    ):
        super().__init__(
            status="ok",
            code=HTTP_OK,
            data=data,
            links=links,
            metadata=additional_data,
            errors=None,
        )

    def __repr__(self):
        return f"SuccessResponse(data={self.data})"


class NoContentResponse(Response):
    """Convenience class for no-content responses"""

    def __init__(
        self,
        data: Any,
        links: list[dict[str, Any]] | None = None,
        additional_data: dict | None = None,
    ):
        super().__init__(
            status="ok",
            code=HTTP_NO_CONTENT,
            data=data,
            links=links,
            metadata=additional_data,
            errors=None,
        )


def _build_error_chain(exc: Exception) -> list[ErrorDetail]:

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
    """Convenience class for error responses"""

    def __init__(self, e: Exception, additional_data: dict | None = None):
        super().__init__(
            status="error",
            code=int(e.code) if hasattr(e, "code") else HTTP_INTERNAL_SERVER_ERROR,
            data={"message": str(e)},
            links=None,
            metadata=additional_data,
            errors=_build_error_chain(e),
        )
