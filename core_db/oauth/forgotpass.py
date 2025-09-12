from datetime import datetime
from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, UTCDateTimeAttribute
from pydantic import Field

from ..models import TableFactory
from .oauthtable import OAuthTableModel, OAuthRecord


class ForgotPasswordModel(OAuthTableModel):

    class Meta(OAuthTableModel.Meta):
        pass

    client = UnicodeAttribute(null=False, attr_name="Client")
    client_id = UnicodeAttribute(null=False, attr_name="ClientID")
    user_id = UnicodeAttribute(null=False, attr_name="UserID")
    email = UnicodeAttribute(null=False, attr_name="Email")
    reset_token = UnicodeAttribute(null=False, attr_name="ResetToken")
    verified = BooleanAttribute(null=False, attr_name="Verified")
    used = BooleanAttribute(null=False, attr_name="Used")
    used_at = UTCDateTimeAttribute(null=True, attr_name="UsedAt", default=None)
    expires_at = UTCDateTimeAttribute(null=False, attr_name="ExpiresAt")

    # created_at is defined in DatabaseTable parent class
    # updated_at is defined in DatabaseTable parent class


class ForgotPasswordModelFactory(TableFactory):

    @classmethod
    def get_model(cls, client: str) -> type[ForgotPasswordModel]:
        return super().get_model(ForgotPasswordModel, client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.create_table(ForgotPasswordModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.delete_table(ForgotPasswordModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        return TableFactory.exists(ForgotPasswordModel, client)


class ForgotPassword(OAuthRecord):

    client: str = Field(
        ...,
        description="Client where the profile is located",
        alias="Client",
    )
    client_id: str = Field(..., description="OAuth Client ID where the request initiated", alias="ClientID")

    user_id: str = Field(..., description="User ID associated with the account", alias="UserID")
    email: str = Field(..., description="Email address associated with the account", alias="Email")
    reset_token: str = Field(..., description="Reset token for password recovery", alias="ResetToken")
    verified: bool = Field(description="Indicates if the email has been verified", default=False, alias="Verified")
    used: bool = Field(description="Indicates if the reset token has been used", default=False, alias="Used")
    used_at: datetime | None = Field(default=None, description="Timestamp when the reset token was used", alias="UsedAt")
    expires_at: datetime = Field(..., description="Expiration timestamp for the reset token", alias="ExpiresAt")

    # created_at is defined in DatabaseRecord parent class
    # updated_at is defined in DatabaseRecord parent class

    @classmethod
    def model_class(cls, client: str) -> type[ForgotPasswordModel]:

        return TableFactory.get_model(ForgotPasswordModel, client)

    @classmethod
    def from_model(cls, model: ForgotPasswordModel) -> "ForgotPassword":

        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> ForgotPasswordModel:

        model_class = TableFactory.get_model(ForgotPasswordModel, client)
        return model_class(**self.model_dump(by_alias=False))
