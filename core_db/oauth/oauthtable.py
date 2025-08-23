from pynamodb.attributes import UnicodeAttribute
from pydantic import Field

from ..models import DatabaseRecord, DatabaseTable


class OAuthTable(DatabaseTable):

    class Meta(DatabaseTable.Meta):
        pass

    code = UnicodeAttribute(hash_key=True, attr_name="Code")


class OAuthRecord(DatabaseRecord):

    code: str = Field(
        ...,
        description="Authorization Code",
        alias="Code",
    )

    @classmethod
    def model_class(cls, client: str) -> type[OAuthTable]:

        raise NotImplementedError("model_class() must be implemented")

    @classmethod
    def from_model(cls, model: OAuthTable) -> "OAuthRecord":

        raise NotImplementedError("from_model() must be implemented")

    def to_model(self, client: str) -> OAuthTable:

        raise NotImplementedError("to_model() must be implemented")
