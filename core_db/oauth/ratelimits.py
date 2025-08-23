from datetime import datetime

from pynamodb.attributes import UnicodeAttribute
from pydantic import Field

from ..models import TableFactory
from .oauthtable import OAuthTable, OAuthRecord


class RateLimitsModel(OAuthTable):

    class Meta(OAuthTable.Meta):
        pass

    attempts = UnicodeAttribute(null=False, attr_name="Attempts")
    ttl = UnicodeAttribute(null=False, attr_name="TTL")

    # created_at is defined in DatabaseTable parent class
    # updated_at is defined in DatabaseTable parent class


class RateLimitModelFactory(TableFactory):

    @classmethod
    def get_model(cls, client: str) -> type[RateLimitsModel]:
        return super().get_model(RateLimitsModel, client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.create_table(RateLimitsModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.delete_table(RateLimitsModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        return TableFactory.exists(RateLimitsModel, client)


class RateLimits(OAuthRecord):

    attempts: str = Field(
        ...,
        description="Number of attempts",
        alias="Attempts",
    )
    ttl: str = Field(
        ...,
        description="Time to live",
        alias="TTL",
    )

    # created_at is defined in DatabaseRecord parent class
    # updated_at is defined in DatabaseRecord parent class

    @classmethod
    def model_class(cls, client: str) -> type[RateLimitsModel]:

        return TableFactory.get_model(RateLimitsModel, client)

    @classmethod
    def from_model(cls, model: RateLimitsModel) -> "RateLimits":

        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> RateLimitsModel:

        model_class = TableFactory.get_model(RateLimitsModel, client)
        return model_class(**self.model_dump(by_alias=False))
