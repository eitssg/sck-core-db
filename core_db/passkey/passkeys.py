from calendar import c
from typing import Type
from datetime import datetime

from pynamodb.attributes import (
    UnicodeAttribute,
    UTCDateTimeAttribute,
    JSONAttribute,
    NumberAttribute,
    BooleanAttribute,
)
from pynamodb.exceptions import PutError, ScanError, QueryError, GetError, UpdateError, DeleteError
from pynamodb.expressions.update import Action
from pydantic import Field, field_validator

from core_framework import from_json
from core_framework.time_utils import make_default_time

from ..models import TableFactory, DatabaseTable, DatabaseRecord, Paginator
from ..actions import TableActions
from ..response import Response, SuccessResponse
from ..exceptions import BadRequestException, ConflictException, UnknownException, NotFoundException


class PassKeysModel(DatabaseTable):

    class Meta(DatabaseTable.Meta):
        pass

    user_id = UnicodeAttribute(hash_key=True)
    key_id = UnicodeAttribute(range_key=True)
    public_key = UnicodeAttribute()
    name = UnicodeAttribute(null=True)
    last_used_at = UTCDateTimeAttribute(null=True)
    last_uv_at = UTCDateTimeAttribute(null=True)
    sign_count = NumberAttribute(null=True)
    transports = JSONAttribute(null=True)
    aaguid = UnicodeAttribute(null=True)
    fmt = UnicodeAttribute(null=True)
    att_stmt = JSONAttribute(null=True)
    cred_protect = UnicodeAttribute(null=True)
    other_ui = BooleanAttribute(null=True)
    rk = BooleanAttribute(null=True)
    uv = BooleanAttribute(null=True)
    credential_backed_up = BooleanAttribute(null=True)
    extensions = JSONAttribute(null=True)
    device_type = UnicodeAttribute(null=True)
    authenticator_version = NumberAttribute(null=True)
    counter = NumberAttribute(null=True)
    clone_warning = BooleanAttribute(null=True)
    deleted = BooleanAttribute(null=True)
    deleted_at = UTCDateTimeAttribute(null=True)


class PassKeysModelFactory(TableFactory):

    @classmethod
    def get_model(cls, client: str) -> type[PassKeysModel]:
        return super().get_model(PassKeysModel, client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.create_table(PassKeysModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.delete_table(PassKeysModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        return TableFactory.exists(PassKeysModel, client)


class PassKey(DatabaseRecord):
    user_id: str = Field(...)
    key_id: str = Field(...)
    public_key: str = Field(...)
    name: str | None = Field(default=None)
    last_used_at: datetime | None = Field(default=None)
    last_uv_at: datetime | None = Field(default=None)
    sign_count: int | None = Field(default=0)
    transports: list[str] | None = Field(default=None)
    aaguid: str | None = Field(default=None)
    fmt: str | None = Field(default=None)
    att_stmt: dict | None = Field(default=None)
    cred_protect: str | None = Field(default=None)
    other_ui: bool | None = Field(default=None)
    rk: bool | None = Field(default=None)
    uv: bool | None = Field(default=None)
    credential_backed_up: bool | None = Field(default=None)
    extensions: dict | None = Field(default=None)
    device_type: str | None = Field(default=None)
    authenticator_version: int | None = Field(default=None)
    counter: int | None = Field(default=None)
    clone_warning: bool | None = Field(default=None)
    deleted: bool | None = Field(default=False)
    deleted_at: datetime | None = Field(default=None)
    # Add other fields as necessary

    @field_validator("transports", mode="before")
    def validate_transports(cls, v):
        if isinstance(v, str):
            return from_json(v)
        return v

    @field_validator("att_stmt", mode="before")
    def validate_att_stmt(cls, v):
        if isinstance(v, str):
            return from_json(v)
        return v

    @field_validator("extensions", mode="before")
    def validate_extensions(cls, v):
        if isinstance(v, str):
            return from_json(v)
        return v

    @classmethod
    def get_model(cls, client: str | None = None) -> Type[PassKeysModel]:
        """Get the ProfileModel class for the given client.

        Args:
            client (str): The client identifier

        Returns:
            ProfileModelType: Client-specific ProfileModel class
        """
        return TableFactory.get_model(PassKeysModel, client=client)

    def to_item(self) -> PassKeysModel:
        return PassKeysModel(**self.model_dump(exclude_none=True))

    @staticmethod
    def from_item(item: PassKeysModel) -> "PassKey":
        return PassKey(**item.to_simple_dict())


class PassKeyActions(TableActions):

    @classmethod
    def list(cls, **kwargs) -> Response:

        user_id = kwargs.pop("user_id", None)
        if user_id:
            return cls._get_for_user(user_id, **kwargs)

        return cls._get_all(**kwargs)

    @classmethod
    def _get_all(cls, **kwargs) -> Response:

        paginator = Paginator(**kwargs)

        model_class = PassKey.get_model()

        try:

            result = model_class.scan(**paginator.get_scan_args())
            data = []
            for item in result:
                data.append(PassKey.from_item(item).model_dump(mode="json"))

            return SuccessResponse(data=data, meta=paginator.get_metadata())

        except ScanError as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def _get_for_user(cls, user_id: str, **kwargs) -> Response:

        key_id = kwargs.get("key_id")

        paginator = Paginator(**kwargs)

        model_class = PassKey.get_model()

        if key_id:
            range_key_condition = model_class.key_id.is_in([key_id])
        else:
            range_key_condition = None

        try:
            result = model_class.query(user_id, range_key_condition=range_key_condition, **paginator.get_scan_args())
            data = []
            for item in result:
                data.append(PassKey.from_item(item).model_dump(mode="json"))

            return SuccessResponse(data=data, meta=paginator.get_metadata())
        except QueryError as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def get(cls, **kwargs) -> Response:
        model_class = PassKey.get_model()

        user_id = kwargs.get("user_id")
        key_id = kwargs.get("key_id")

        if not user_id or not key_id:
            raise BadRequestException(code=400, message="user_id and key_id are required")

        try:
            result = model_class.get(hash_key=user_id, range_key=key_id)

            data = PassKey.from_item(result).model_dump(mode="json")

            return SuccessResponse(data=data)

        except GetError as e:
            raise NotFoundException("PassKey not found")
        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def create(cls, **kwargs) -> Response:
        model_class = PassKey.get_model()

        try:
            item = model_class(**kwargs)
            item.save(condition=model_class.user_id.does_not_exist() & model_class.key_id.does_not_exist())

            data = PassKey.from_item(item).model_dump(mode="json")

            return SuccessResponse(data=data)

        except PutError:
            if "ConditionalCheckFailedException" in str(e):
                raise ConflictException("PassKey already exists")

            raise UnknownException(str(e)) from e

        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def update(cls, **kwargs) -> Response:
        model_class = PassKey.get_model()

        data = PassKey(**kwargs)

        try:
            item = model_class(**kwargs)
            item.save(condition=model_class.user_id.exists() & model_class.key_id.exists())

            return SuccessResponse(data=data.model_dump(mode="json"))

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException("PassKey not found")
            raise UnknownException(str(e)) from e

        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def patch(cls, **kwargs) -> Response:

        user_id = kwargs.pop("user_id", None)
        key_id = kwargs.pop("key_id", None)

        if not user_id or not key_id:
            raise BadRequestException(code=400, message="user_id and key_id are required")

        try:
            model_class = PassKey.get_model()

            actions: list[Action] = []

            attributes = model_class.get_attributes()

            for key, value in kwargs.items():
                if key in attributes:
                    attr = attributes[key]
                    actions.append(attr.set(value))

            actions.append(model_class.updated_at.set(make_default_time()))

            item = model_class(user_id=user_id, key_id=key_id)
            item.update(actions=actions, condition=model_class.user_id.exists() & model_class.key_id.exists())

            item.refresh()

            data = PassKey.from_item(item).model_dump(mode="json")

            return SuccessResponse(data=data)

        except UpdateError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException("PassKey not found")

            raise UnknownException(str(e)) from e

        except Exception as e:
            raise UnknownException(str(e)) from e

    @classmethod
    def delete(cls, **kwargs) -> Response:

        user_id = kwargs.get("user_id")
        key_id = kwargs.get("key_id")

        if not user_id or not key_id:
            raise BadRequestException(code=400, message="user_id and key_id are required")

        try:
            model_class = PassKey.get_model()

            model_class.delete(user_id=user_id, key_id=key_id, condition=model_class.user_id.exists() & model_class.key_id.exists())

            return SuccessResponse(code=204, message="PassKey deleted")

        except DeleteError as e:
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException("PassKey not found")
            raise UnknownException(str(e)) from e
        except Exception as e:
            raise UnknownException(str(e)) from e
