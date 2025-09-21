"""Classes defining the Apps record model for the core-automation-apps table"""

from typing import List
import re
from typing import Dict, Optional, Type
from pydantic import Field, model_validator

from pynamodb.attributes import UnicodeAttribute, MapAttribute, ListAttribute

from ...models import TableFactory, DatabaseRecord, DatabaseTable


class AppFactsModel(DatabaseTable):

    class Meta(DatabaseTable.Meta):

        pass

    # Hash and Range Keys
    portfolio = UnicodeAttribute(attr_name="Portfolio", hash_key=True)
    # Auto generate derived from client/portfolio/name. URL-safe slug; unique
    # within portfolio; generated from Name; immutable after create
    app = UnicodeAttribute(attr_name="App", range_key=True)
    # Friendly name for this deployment
    name = UnicodeAttribute(attr_name="Name")
    # PRN Matcher
    app_regex = UnicodeAttribute(attr_name="AppRegex")

    # App Details

    environment = UnicodeAttribute(null=True, attr_name="Environment")
    account = UnicodeAttribute(null=True, attr_name="Account")
    zone = UnicodeAttribute(null=False, attr_name="Zone")
    region = UnicodeAttribute(null=False, attr_name="Region")
    repository = UnicodeAttribute(null=True, attr_name="Repository")
    enforce_validation = UnicodeAttribute(null=True, attr_name="EnforceValidation")

    # Complex Attributes
    image_aliases = MapAttribute(null=True, attr_name="ImageAliases")
    tags = MapAttribute(null=True, attr_name="Tags")
    labels = ListAttribute(of=UnicodeAttribute, null=True, attr_name="Labels")
    metadata = MapAttribute(null=True, attr_name="Metadata")

    def __repr__(self) -> str:
        return f"<AppFactsModel(portfolio={self.portfolio}, app={self.app}, regex={self.app_regex})>"


AppFactsType = Type[AppFactsModel]


class AppFactsFactory:

    @classmethod
    def get_model(cls, client: str) -> AppFactsType:
        return TableFactory.get_model(AppFactsModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.create_table(AppFactsModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        return TableFactory.delete_table(AppFactsModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        return TableFactory.exists(AppFactsModel, client)


class AppFact(DatabaseRecord):

    # Core App Keys with PascalCase aliases
    portfolio: str = Field(
        ...,
        alias="Portfolio",
        description="Portfolio identifier (slug) (hash key)",
    )
    app: str = Field(
        ...,
        alias="App",
        description="App identifier (slug) (derived from AppRegex for compatibility)",
    )
    app_regex: str = Field(
        ...,
        alias="AppRegex",
        description="App Regex identifier (range key) for matching application names",
    )
    # App Configuration Fields
    name: str = Field(
        ...,
        alias="Name",
        description="Human-readable name of the app (required)",
    )
    environment: Optional[str] = Field(
        None,
        alias="Environment",
        description="Environment where the app is deployed (e.g., 'production', 'staging')",
    )
    account: Optional[str] = Field(
        None,
        alias="Account",
        description="AWS account number where the app is deployed",
    )
    zone: str = Field(
        ...,
        alias="Zone",
        description="Zone identifier where the app is deployed",
    )
    region: str = Field(
        ...,
        alias="Region",
        description="AWS region where the app is deployed",
    )
    repository: Optional[str] = Field(
        None,
        alias="Repository",
        description="Git repository URL for the app source code",
    )
    enforce_validation: Optional[str] = Field(
        None,
        alias="EnforceValidation",
        description="Flag to enforce validation rules for the app",
    )
    # Complex Configuration Fields
    image_aliases: Optional[Dict[str, str]] = Field(
        None,
        alias="ImageAliases",
        description="Image aliases to reduce bake time for deployments",
    )
    tags: Optional[Dict[str, str]] = Field(
        None,
        alias="Tags",
        description="Tags to apply to AWS resources created for this app",
    )
    labels: Optional[List[str]] = Field(
        None,
        alias="Labels",
        description="Labels to apply to AWS resources created for this app",
    )
    metadata: Optional[Dict[str, str]] = Field(
        None,
        alias="Metadata",
        description="Additional metadata for the app configuration",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_model_before(cls, values: Dict[str, str]) -> Dict[str, str]:
        return values

    def matches_app(self, name: str) -> bool:
        try:
            return bool(re.match(self.app_regex, name))
        except re.error:
            # If regex is invalid, fall back to exact string match
            return self.app_regex == name

    def is_validation_enforced(self) -> bool:
        if self.enforce_validation is None:
            return False
        return self.enforce_validation.lower() in ("true", "1", "yes", "on", "enabled")

    @classmethod
    def model_class(cls, client: str) -> AppFactsType:
        return AppFactsFactory.get_model(client)

    @classmethod
    def from_model(cls, model: AppFactsModel) -> "AppFact":
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> AppFactsModel:
        model_class = AppFactsFactory.get_model(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    def __repr__(self) -> str:
        return f"<AppFact(portfolio={self.portfolio}, app={self.app}, regex={self.app_regex})>"
