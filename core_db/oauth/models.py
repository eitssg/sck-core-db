from pynamodb.attributes UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute

from ..models import DatabaseTable, DatabaseRecord

class AuthorizationsModel(DatabaseTable):

    class Meta(DatabaseTable.Meta):
        pass

    code = UnicodeAttribute(hash_key=True, attr_name="Code")
    client_id = UnicodeAttribute(attr_name="Client")
    user_id = UnicodeAttribute(attr_name="UserId")
    redirect_url = UnicodeAttribute(attr_name="RedirectUrl")
    scope = UnicodeAttribute(attr_name="Scope")
    jwt_token = UnicodeAttribute(attr_name="JwtToken")
    expires_at = UTCDateTimeAttribute(null=True, attr_name="ExpiresAt")
    used = BooleanAttribute(null=False, attr_name="Used")

    # created_at is defined in DatabaseTable parent class
    # updated_at is defined in DatabaseTable parent class

class Authorizations(DatabaseRecord):

    code: str = Field(..., description="Authorization Code", alias="Code",)
    client_id: str = Field(..., description="Client Application ID", alias="ClientId",)
    user_id: str | None = Field(None, description="User ID", alias="UserId",)
    redirect_url: str | None = Field(None, description="Redirect URL", alias="RedirectUrl",)
    scope: str | None = Field(None, description="Scope of the oauth event", alias="Scope",)
    jwt_token: str | None = Field(None, description="JWT Token containing credentials", alias="JwtToken",)
    expires_at: datetime | None = Field(None, description="Date the Authorization code expires", alias="ExpiresAt",)
    used: bool = Field(False, description="Determines if this code already been used", alias="Used",)

    # created_at is defined in DatabaseRecord parent class
    # updated_at is defined in DatabaseRecord parent class

    @classmethod
    def model_class(cls, client: str) -> type[AuthorizationsModel]:

        return TableFactory.get_model(AuthorizationsModel, client)

    @classmethod
    def from_model(cls, model: AuthorizationsModel) -> "Authorizations":

        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> Self:

        model_class = TableFactory.get_model(AuthorizationsModel, client)
        return model_class(**self.model_dump(by_alias=False))

