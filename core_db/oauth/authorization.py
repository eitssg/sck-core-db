from datetime import datetime

from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute
from pydantic import Field

from ..models import TableFactory
from .oauthtable import OAuthTableModel, OAuthRecord


class AuthorizationsModel(OAuthTableModel):

    class Meta(OAuthTableModel.Meta):
        pass

    client_id = UnicodeAttribute(null=False, attr_name="ClientId")
    redirect_url = UnicodeAttribute(null=False, attr_name="RedirectUrl")
    scope = UnicodeAttribute(null=False, attr_name="Scope")
    expires_at = UTCDateTimeAttribute(null=True, attr_name="ExpiresAt")
    used = BooleanAttribute(null=False, attr_name="Used")
    code_challenge = UnicodeAttribute(null=True, attr_name="CodeChallenge")
    code_challenge_method = UnicodeAttribute(null=True, attr_name="CodeChallengeMethod")
    jwt_signature = UnicodeAttribute(null=True, attr_name="JwtSignature")

    # created_at is defined in DatabaseTable parent class
    # updated_at is defined in DatabaseTable parent class


class AuthorizationsModelFactory(TableFactory):

    @classmethod
    def get_model(cls, client: str) -> type[AuthorizationsModel]:
        return super().get_model(AuthorizationsModel, client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.create_table(AuthorizationsModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.delete_table(AuthorizationsModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        return TableFactory.exists(AuthorizationsModel, client)


class Authorizations(OAuthRecord):

    client_id: str = Field(
        ...,
        description="Client Application ID",
        alias="ClientId",
    )
    redirect_url: str = Field(
        ...,
        description="Redirect URL",
        alias="RedirectUrl",
    )
    scope: str = Field(
        ...,
        description="Scope of the oauth event",
        alias="Scope",
    )
    expires_at: datetime | None = Field(
        None,
        description="Date the Authorization code expires",
        alias="ExpiresAt",
    )
    used: bool = Field(
        False,
        description="Determines if this code already been used",
        alias="Used",
    )
    code_challenge: str | None = Field(
        None,
        description="Code challenge for PKCE",
        alias="CodeChallenge",
    )
    code_challenge_method: str | None = Field(
        None,
        description="Method used for code challenge (e.g., 'S256')",
        alias="CodeChallengeMethod",
    )
    jwt_signature: str | None = Field(
        None,
        description="JWT signature for the authorization code",
        alias="JwtSignature",
    )

    # created_at is defined in DatabaseRecord parent class
    # updated_at is defined in DatabaseRecord parent class

    @classmethod
    def model_class(cls, client: str) -> type[AuthorizationsModel]:

        return TableFactory.get_model(AuthorizationsModel, client)

    @classmethod
    def from_model(cls, model: AuthorizationsModel) -> "Authorizations":

        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> AuthorizationsModel:

        model_class = TableFactory.get_model(AuthorizationsModel, client)
        return model_class(**self.model_dump(by_alias=False))
