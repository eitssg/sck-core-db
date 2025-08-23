from pynamodb.attributes import UnicodeAttribute
from pydantic import Field

from ..models import DatabaseRecord, DatabaseTable, TableFactory


class OAuthTableModel(DatabaseTable):

    class Meta(DatabaseTable.Meta):
        pass

    code = UnicodeAttribute(hash_key=True, attr_name="Code")


class OAuthTableModelFactory(TableFactory):

    @classmethod
    def get_model(cls, client: str) -> type[OAuthTableModel]:
        return super().get_model(OAuthTableModel, client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.create_table(OAuthTableModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.delete_table(OAuthTableModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        return TableFactory.exists(OAuthTableModel, client)


class OAuthRecord(DatabaseRecord):

    code: str = Field(
        ...,
        description="Authorization Code",
        alias="Code",
    )

    @classmethod
    def model_class(cls, client: str) -> type[OAuthTableModel]:

        raise NotImplementedError("model_class() must be implemented")

    @classmethod
    def from_model(cls, model: OAuthTableModel) -> "OAuthRecord":

        raise NotImplementedError("from_model() must be implemented")

    def to_model(self, client: str) -> OAuthTableModel:

        raise NotImplementedError("to_model() must be implemented")
