from typing import List, Tuple

from pynamodb.exceptions import (
    DeleteError,
    DoesNotExist,
    PutError,
    ScanError,
    UpdateError,
)
from functools import reduce
from pydantic import ValidationError

from core_framework.time_utils import make_default_time

from ..exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnknownException,
)
from ..models import Paginator
from ..actions import TableActions
from .oauthtable import OAuthRecord
from .authorization import Authorizations
from .ratelimits import RateLimits
from .forgotpass import ForgotPassword


class OAuthActions(TableActions):
    """Implements CRUD operations for OAuth records."""

    @classmethod
    def create(cls, record_type: OAuthRecord, **kwargs) -> OAuthRecord:
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
            data: OAuthRecord = record_type(**kwargs)
            item = data.to_model(client)

            # Prevent overwrite
            item.save(condition=type(item).code.does_not_exist())
            # Return the created record
            return data

        except PutError as e:
            if "ConditionalCheckFailed" in str(e):
                raise ConflictException("Authorization code already exists") from e
            raise UnknownException(f"Failed to create authorization: {e}") from e
        except (ValueError, ValidationError) as e:
            raise BadRequestException(f"Invalid authorization data: {e}") from e
        except Exception as e:
            raise UnknownException(f"Failed to create authorization: {e}") from e

    @classmethod
    def list(cls, record_type: OAuthRecord, **kwargs) -> Tuple[List[OAuthRecord], Paginator]:
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
            data = [record_type.from_model(item) for item in result]

            paginator = Paginator(total_count=len(data))

            return data, paginator

        except ScanError as e:
            raise UnknownException(f"Failed to list authorizations: {e}") from e
        except Exception as e:
            raise UnknownException(f"Failed to list authorizations: {e}") from e

    @classmethod
    def get(cls, record_type: OAuthRecord, **kwargs) -> OAuthRecord:
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

            return record_type.from_model(item)

        except DoesNotExist:
            raise NotFoundException(f"Authorization code {code} not found")
        except Exception as e:
            raise UnknownException(f"Failed to retrieve authorization: {e}") from e

    @classmethod
    def update(cls, record_type: OAuthRecord, **kwargs) -> OAuthRecord:
        """Update an authorization record; if a field value is None, remove the attribute.

        Args:
            **kwargs: Must include client and code. Other provided fields will be set;
                      fields explicitly set to None will be removed.

        Returns:
            Response: SuccessResponse with updated record.
        """
        return cls._update(record_type, remove_none=True, **kwargs)

    @classmethod
    def patch(cls, record_type: OAuthRecord, **kwargs) -> OAuthRecord:
        """Patch an authorization record; ignore fields set to None (no change).

        Args:
            **kwargs: Must include client and code. Provided non-None fields will be set.

        Returns:
            Response: SuccessResponse with updated record.
        """
        return cls._update(record_type, remove_none=False, **kwargs)

    @classmethod
    def _update(cls, record_type: OAuthRecord, remove_none: bool, **kwargs) -> OAuthRecord:
        """Internal update helper."""

        client = kwargs.get("client", kwargs.get("Client"))
        code = kwargs.get("code", kwargs.get("Code"))
        client_id = kwargs.get("client_id", kwargs.get("ClientId", kwargs.get("clientId")))

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

        conditions = []
        try:
            # Use a single timestamp for this mutation to keep comparisons consistent
            now = make_default_time()

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
                    if key == "used_at":
                        continue
                    actions.append(attr.set(value))
                    if key == "used" and value is True:
                        if not client_id:
                            raise BadRequestException("client_id is required when marking used=True")
                        actions.append(attributes["used_at"].set(now))
                        # If marking used=True, ensure it was previously False (or not set)
                        conditions.append((model_class.used == False) | model_class.used.does_not_exist())
                        conditions.append(model_class.client_id == client_id)
                        conditions.append(model_class.expires_at > now)

            # Always update updated_at
            actions.append(model_class.updated_at.set(now))

            conditions.append(model_class.code.exists())
            condition = reduce(lambda a, b: a & b, conditions)

            item = model_class(code)
            item.update(actions=actions, condition=condition)
            item.refresh()

            return record_type.from_model(item)

        except UpdateError as e:
            if "ConditionalCheckFailed" in str(e):
                # Any conditional failure (missing item, already used, expired, or client mismatch)
                raise NotFoundException("Authorization code not found or not eligible for update") from e

            raise UnknownException(f"Failed to update authorization: {e}") from e

        except Exception as e:
            raise UnknownException(f"Failed to update authorization: {e}") from e

    @classmethod
    def delete(cls, record_type: OAuthRecord, **kwargs) -> bool:
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

            item = model_class(code)
            item.delete(condition=type(item).code.exists())

            return True

        except DeleteError as e:
            if "ConditionalCheckFailed" in str(e):
                raise ConflictException("Authorization code does not exist") from e

            raise UnknownException(f"Failed to delete authorization: {e}") from e

        except Exception as e:
            raise UnknownException(f"Failed to delete authorization: {e}") from e


class AuthActions(OAuthActions):

    @classmethod
    def create(cls, **kwargs) -> Authorizations:
        return super().create(record_type=Authorizations, **kwargs)

    @classmethod
    def list(cls, **kwargs) -> Tuple[List[Authorizations], Paginator]:
        return super().list(record_type=Authorizations, **kwargs)

    @classmethod
    def get(cls, **kwargs) -> Authorizations:
        return super().get(record_type=Authorizations, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> Authorizations:
        return super().update(record_type=Authorizations, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> Authorizations:
        return super().patch(record_type=Authorizations, **kwargs)

    @classmethod
    def delete(cls, **kwargs) -> bool:
        return super().delete(record_type=Authorizations, **kwargs)


class RateLimitActions(OAuthActions):

    @classmethod
    def create(cls, **kwargs) -> RateLimits:
        return super().create(record_type=RateLimits, **kwargs)

    @classmethod
    def list(cls, **kwargs) -> Tuple[List[RateLimits], Paginator]:
        return super().list(record_type=RateLimits, **kwargs)

    @classmethod
    def get(cls, **kwargs) -> RateLimits:
        return super().get(record_type=RateLimits, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> RateLimits:
        return super().update(record_type=RateLimits, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> RateLimits:
        return super().patch(record_type=RateLimits, **kwargs)

    @classmethod
    def delete(cls, **kwargs) -> bool:
        return super().delete(record_type=RateLimits, **kwargs)


class ForgotPasswordActions(OAuthActions):

    @classmethod
    def create(cls, **kwargs) -> ForgotPassword:
        return super().create(record_type=ForgotPassword, **kwargs)

    @classmethod
    def list(cls, **kwargs) -> Tuple[List[ForgotPassword], Paginator]:
        return super().list(record_type=ForgotPassword, **kwargs)

    @classmethod
    def get(cls, **kwargs) -> ForgotPassword:
        return super().get(record_type=ForgotPassword, **kwargs)

    @classmethod
    def update(cls, **kwargs) -> ForgotPassword:
        return super().update(record_type=ForgotPassword, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> ForgotPassword:
        return super().patch(record_type=ForgotPassword, **kwargs)

    @classmethod
    def delete(cls, **kwargs) -> bool:
        return super().delete(record_type=ForgotPassword, **kwargs)
