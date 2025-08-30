from pynamodb.exceptions import (
    DeleteError,
    DoesNotExist,
    PutError,
    ScanError,
    UpdateError,
)
from pydantic import ValidationError

from core_framework.time_utils import make_default_time
from test.test_reprlib import r

from ..response import Response, SuccessResponse, NoContentResponse
from ..exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnknownException,
)
from ..actions import TableActions
from .oauthtable import OAuthRecord
from .authorization import Authorizations
from .ratelimits import RateLimits
from .forgotpass import ForgotPassword


class OAuthActions(TableActions):
    """Implements CRUD operations for OAuth records."""

    @classmethod
    def create(cls, record_type: OAuthRecord, **kwargs) -> Response:
        """Create an authorization code record.

        Args:
            **kwargs: Fields for Authorizations pydantic model (must include client and code).

        Returns:
            Response: SuccessResponse with created record data.

        Raises:
            ConflictException: If the code already exists.
            UnknownException: On unexpected errors.
        """
        client = kwargs.get("client", kwargs.get("Client"))
        if not client:
            raise BadRequestException("Missing client parameter")

        try:
            data = record_type(**kwargs)
            item = data.to_model(client)
            # Prevent overwrite
            item.save(condition=type(item).code.does_not_exist())
            # Return the created record
            created = data.model_dump(by_alias=False, mode="json")
            return SuccessResponse(data=created)
        except PutError as e:
            if "ConditionalCheckFailed" in str(e):
                raise ConflictException("Authorization code already exists") from e
            raise UnknownException(f"Failed to create authorization: {e}") from e
        except (ValueError, ValidationError) as e:
            raise BadRequestException(f"Invalid authorization data: {e}") from e
        except Exception as e:
            raise UnknownException(f"Failed to create authorization: {e}") from e

    @classmethod
    def list(cls, record_type: OAuthRecord, **kwargs) -> Response:
        """List authorization codes for a client.

        Args:
            **kwargs: Must include client.

        Returns:
            Response: SuccessResponse with list data or NoContentResponse if none.
        """
        client = kwargs.get("client", kwargs.get("Client"))

        if not client:
            raise BadRequestException("Missing client parameter")

        try:
            model_class = record_type.model_class(client)
            result = model_class.scan()
            data = [record_type.from_model(item).model_dump(mode="json") for item in result]

            if len(data) == 0:
                return NoContentResponse(metadata={"message": "There are no authorizations found."})

            return SuccessResponse(data=data, metadata={"total_count": len(data)})
        except ScanError as e:
            raise UnknownException(f"Failed to list authorizations: {e}") from e
        except Exception as e:
            raise UnknownException(f"Failed to list authorizations: {e}") from e

    @classmethod
    def get(cls, record_type: OAuthRecord, **kwargs) -> Response:
        """Get a single authorization code record.

        Args:
            **kwargs: Must include client and code.

        Returns:
            Response: SuccessResponse with record data.

        Raises:
            NotFoundException: If the code does not exist.
        """
        client = kwargs.get("client", kwargs.get("Client"))
        code = kwargs.get("code", kwargs.get("Code"))

        if not client:
            raise BadRequestException("Missing client parameter")

        if not code:
            raise BadRequestException("Missing authorization code")

        try:
            model_class = record_type.model_class(client)
            item = model_class.get(code)
            data = record_type.from_model(item).model_dump(by_alias=False, mode="json")
            return SuccessResponse(data=data)
        except DoesNotExist:
            raise NotFoundException(f"Authorization code {code} not found")
        except Exception as e:
            raise UnknownException(f"Failed to retrieve authorization: {e}") from e

    @classmethod
    def update(cls, record_type: OAuthRecord, **kwargs) -> Response:
        """Update an authorization record; if a field value is None, remove the attribute.

        Args:
            **kwargs: Must include client and code. Other provided fields will be set;
                      fields explicitly set to None will be removed.

        Returns:
            Response: SuccessResponse with updated record.
        """
        return cls._update(record_type, remove_none=True, **kwargs)

    @classmethod
    def patch(cls, record_type: OAuthRecord, **kwargs) -> Response:
        """Patch an authorization record; ignore fields set to None (no change).

        Args:
            **kwargs: Must include client and code. Provided non-None fields will be set.

        Returns:
            Response: SuccessResponse with updated record.
        """
        return cls._update(record_type, remove_none=False, **kwargs)

    @classmethod
    def _update(cls, record_type: OAuthRecord, remove_none: bool = True, **kwargs) -> Response:
        """Internal update helper."""
        client = kwargs.get("client", kwargs.get("Client"))
        code = kwargs.get("code", kwargs.get("Code"))

        if not client:
            raise BadRequestException("Missing client parameter")

        if not code:
            raise BadRequestException("Missing authorization code")

        try:
            if remove_none:
                record = record_type(**kwargs)
            else:
                # allow constructing with possibly missing required fields for patch semantics
                record = record_type.model_construct(**kwargs)
        except (ValueError, ValidationError) as e:
            raise BadRequestException(f"Invalid authorization data: {e}") from e

        model_class = record_type.model_class(client)
        attributes = model_class.get_attributes()
        values = record.model_dump(by_alias=False, exclude_none=False)

        excluded_fields = {"code", "created_at", "updated_at"}

        try:
            actions = []
            for key, value in values.items():
                if key in excluded_fields or key not in attributes:
                    continue

                attr = attributes[key]
                if value is None:
                    if remove_none:
                        actions.append(attr.remove())
                    # else: patch semantics — ignore None (no change)
                else:
                    actions.append(attr.set(value))

            # Always update updated_at
            if "updated_at" in attributes:
                actions.append(model_class.updated_at.set(make_default_time()))

            if not actions:
                # Nothing to update; return current record
                current = model_class.get(code)
                data = record_type.from_model(current).model_dump(by_alias=False, mode="json")
                return SuccessResponse(data=data)

            item = model_class(code)
            item.update(actions=actions, condition=type(item).code.exists())
            item.refresh()

            data = record_type.from_model(item).model_dump(by_alias=False, mode="json")
            return SuccessResponse(data=data)

        except UpdateError as e:
            if "ConditionalCheckFailed" in str(e):
                raise ConflictException("Authorization code does not exist") from e
            raise UnknownException(f"Failed to update authorization: {e}") from e
        except Exception as e:
            raise UnknownException(f"Failed to update authorization: {e}") from e

    @classmethod
    def delete(cls, record_type: OAuthRecord, **kwargs) -> Response:
        """Delete an authorization record.

        Args:
            **kwargs: Must include client and code.

        Returns:
            Response: SuccessResponse with a message on success.
        """
        client = kwargs.get("client", kwargs.get("Client"))
        code = kwargs.get("code", kwargs.get("Code"))

        if not client:
            raise BadRequestException("Missing client parameter")

        if not code:
            raise BadRequestException("Missing authorization code")

        try:
            model_class = record_type.model_class(client)
            # Use instance delete to support condition expression consistently
            item = model_class(code)
            item.delete(condition=type(item).code.exists())
            return SuccessResponse(message="Authorization code deleted")
        except DeleteError as e:
            if "ConditionalCheckFailed" in str(e):
                raise ConflictException("Authorization code does not exist") from e
            raise UnknownException(f"Failed to delete authorization: {e}") from e
        except Exception as e:
            raise UnknownException(f"Failed to delete authorization: {e}") from e


class AuthActions(OAuthActions):

    @classmethod
    def create(cls, **kwargs) -> Response:
        return super().create(record_type=Authorizations, **kwargs)

    @classmethod
    def list(cls, **kwargs) -> Response:
        return super().list(record_type=Authorizations, **kwargs)

    @classmethod
    def get(cls, **kwargs) -> Response:
        return super().get(record_type=Authorizations, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> Response:
        return super().update(record_type=Authorizations, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> Response:
        return super().patch(record_type=Authorizations, **kwargs)

    @classmethod
    def delete(cls, **kwargs) -> Response:
        return super().delete(record_type=Authorizations, **kwargs)


class RateLimitActions(OAuthActions):

    @classmethod
    def create(cls, **kwargs) -> Response:
        return super().create(record_type=RateLimits, **kwargs)

    @classmethod
    def list(cls, **kwargs) -> Response:
        return super().list(record_type=RateLimits, **kwargs)

    @classmethod
    def get(cls, **kwargs) -> Response:
        return super().get(record_type=RateLimits, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> Response:
        return super().update(record_type=RateLimits, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> Response:
        return super().patch(record_type=RateLimits, **kwargs)

    @classmethod
    def delete(cls, **kwargs) -> Response:
        return super().delete(record_type=RateLimits, **kwargs)


class ForgotPasswordActions(OAuthActions):

    @classmethod
    def create(cls, **kwargs) -> Response:
        return super().create(record_type=ForgotPassword, **kwargs)

    @classmethod
    def list(cls, **kwargs) -> Response:
        return super().list(record_type=ForgotPassword, **kwargs)

    @classmethod
    def get(cls, **kwargs) -> Response:
        return super().get(record_type=ForgotPassword, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> Response:
        return super().update(record_type=ForgotPassword, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> Response:
        return super().patch(record_type=ForgotPassword, **kwargs)

    @classmethod
    def delete(cls, **kwargs) -> Response:
        return super().delete(record_type=ForgotPassword, **kwargs)
