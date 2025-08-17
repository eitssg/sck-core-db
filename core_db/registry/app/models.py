"""Classes defining the Apps record model for the core-automation-apps table"""

import re
from typing import Dict, Optional, Type
from pydantic import Field, model_validator

from pynamodb.attributes import UnicodeAttribute, MapAttribute

from ...constants import PORTFOLIO_KEY, APP_KEY
from ...models import TableFactory, DatabaseRecord, DatabaseTable


class AppFactsModel(DatabaseTable):
    """App facts model for the core-automation-apps table.

    This model defines the structure for app facts that can be created
    dynamically for different clients using the AppFactsFactory. It stores
    configuration information about applications including deployment zones,
    regions, and metadata.

    Attributes:
        portfolio (str): Portfolio identifier (hash key)
        app_regex (str): App Regex identifier (range key) for matching application names
        name (str): Human-readable name of the app (required)
        environment (str, optional): Environment where the app is deployed (e.g., 'production', 'staging')
        account (str, optional): AWS account number where the app is deployed
        zone (str): Zone identifier where the app is deployed
        region (str): AWS region where the app is deployed
        repository (str, optional): Git repository URL for the app source code
        enforce_validation (str, optional): Flag to enforce validation rules for the app
        image_aliases (dict, optional): Image aliases to reduce bake time for deployments
        tags (dict, optional): Tags to apply to AWS resources created for this app
        metadata (dict, optional): Additional metadata for the app configuration

    Note:
        We call this "zone" now. A "zone" contains "apps" that are deployed together
        in an Account. A zone can have multiple region definitions.

    Examples:
        >>> # Both formats work identically (thanks to DatabaseTable conversion)
        >>> app1 = AppFactsModel(
        ...     portfolio="acme",
        ...     app_regex="core-api-.*",
        ...     name="Core API",
        ...     environment="production",
        ...     zone="prod-east",
        ...     region="us-east-1"
        ... )

        >>> app2 = AppFactsModel(
        ...     Portfolio="acme",
        ...     AppRegex="core-api-.*",
        ...     Name="Core API",
        ...     Environment="production",
        ...     Zone="prod-east",
        ...     Region="us-east-1"
        ... )
    """

    class Meta(DatabaseTable.Meta):
        """Meta class for AppFactsModel DynamoDB table configuration.

        Inherits configuration from DatabaseTable.Meta including table naming,
        region settings, and billing mode.
        """

        pass

    # Hash and Range Keys
    portfolio = UnicodeAttribute(attr_name=PORTFOLIO_KEY, hash_key=True)
    app_regex = UnicodeAttribute(attr_name=APP_KEY, range_key=True)

    # App Details
    name = UnicodeAttribute(attr_name="Name")
    environment = UnicodeAttribute(null=True, attr_name="Environment")
    account = UnicodeAttribute(null=True, attr_name="Account")
    zone = UnicodeAttribute(null=False, attr_name="Zone")
    region = UnicodeAttribute(null=False, attr_name="Region")
    repository = UnicodeAttribute(null=True, attr_name="Repository")
    enforce_validation = UnicodeAttribute(null=True, attr_name="EnforceValidation")

    # Complex Attributes
    image_aliases = MapAttribute(null=True, attr_name="ImageAliases")
    tags = MapAttribute(null=True, attr_name="Tags")
    metadata = MapAttribute(null=True, attr_name="Metadata")

    def __repr__(self) -> str:
        """Return string representation of the AppFactsModel.

        Returns:
            str: String representation showing key fields

        Examples:
            >>> app = AppFactsModel(portfolio="acme", app_regex="core-api-.*")
            >>> repr(app)
            '<AppFactsModel(acme,app_regex=core-api-.*)>'
        """
        return f"<AppFactsModel({self.portfolio},app_regex={self.app_regex})>"


AppFactsType = Type[AppFactsModel]


class AppFactsFactory:
    """Factory class for creating client-specific AppFactsModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for AppFactsModel.

    Examples:
        >>> # Get client-specific model
        >>> client_model = AppFactsFactory.get_model("acme")

        >>> # Create table for client
        >>> AppFactsFactory.create_table("acme", wait=True)

        >>> # Check if table exists
        >>> exists = AppFactsFactory.exists("acme")

        >>> # Delete table
        >>> AppFactsFactory.delete_table("acme", wait=True)
    """

    @classmethod
    def get_model(cls, client: str) -> AppFactsType:
        """Get the AppFactsModel class for the given client.

        Args:
            client (str): The name of the client

        Returns:
            AppFactsType: Client-specific AppFactsModel class

        Examples:
            >>> model_class = AppFactsFactory.get_model("acme")
            >>> app = model_class(client_portfolio="acme", app_regex="core-api-.*")
        """
        return TableFactory.get_model(AppFactsModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        """Create the AppFactsModel table for the given client.

        Args:
            client (str): The name of the client
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists

        Examples:
            >>> AppFactsFactory.create_table("acme", wait=True)
            True
        """
        return TableFactory.create_table(AppFactsModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        """Delete the AppFactsModel table for the given client.

        Args:
            client (str): The name of the client
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist

        Examples:
            >>> AppFactsFactory.delete_table("acme", wait=True)
            True
        """
        return TableFactory.delete_table(AppFactsModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        """Check if the AppFactsModel table exists for the given client.

        Args:
            client (str): The name of the client

        Returns:
            bool: True if the table exists, False otherwise

        Examples:
            >>> AppFactsFactory.exists("acme")
            True
        """
        return TableFactory.exists(AppFactsModel, client)


class AppFact(DatabaseRecord):
    """Pydantic model for App Facts with validation and serialization.

    Provides type validation, PascalCase serialization for APIs, and conversion methods
    between PynamoDB and API formats. Apps define deployment configurations within
    portfolios using regex patterns to match application names.

    Inherits audit fields (created_at, updated_at) from DatabaseRecord.

    Attributes:
        portfolio (str): Portfolio identifier (hash key for table partitioning)
        app_regex (str): App regex identifier (range key) for matching application names
        name (str): Human-readable name of the app (required)
        environment (str, optional): Environment where the app is deployed (e.g., 'production', 'staging')
        account (str, optional): AWS account number where the app is deployed
        zone (str): Zone identifier where the app is deployed (required)
        region (str): AWS region where the app is deployed (required)
        repository (str, optional): Git repository URL for the app source code
        enforce_validation (str, optional): Flag to enforce validation rules for the app
        image_aliases (dict, optional): Image aliases to reduce bake time for deployments
        tags (dict, optional): Tags to apply to AWS resources created for this app
        metadata (dict, optional): Additional metadata for the app configuration

        Inherited from DatabaseRecord:
            created_at (datetime): Timestamp when the record was first created (auto-generated)
            updated_at (datetime): Timestamp when the record was last modified (auto-updated)

    Note:
        All string fields use PascalCase aliases for API compatibility and DynamoDB attribute naming.
        The portfolio and app_regex fields together form the composite primary key for DynamoDB.

    Examples:
        >>> # Create app fact with validation
        >>> app = AppFact(
        ...     Portfolio="acme",
        ...     AppRegex="core-api-.*",
        ...     Name="Core API",
        ...     Zone="prod-east",
        ...     Region="us-east-1"
        ... )

        >>> # Convert from DynamoDB model
        >>> db_app = AppFactsModel(portfolio="acme", app_regex="core-api-.*")
        >>> pydantic_app = AppFact.from_model(db_app)

        >>> # Convert to DynamoDB format
        >>> db_model = app.to_model("acme")
    """

    # Core App Keys with PascalCase aliases
    portfolio: str = Field(
        ...,
        alias="Portfolio",
        description="Portfolio identifier (hash key)",
    )
    app_regex: str = Field(
        ...,
        alias="AppRegex",
        description="App Regex identifier (range key) for matching application names",
    )
    # App Configuration Fields
    name: Optional[str] = Field(
        None,
        alias="Name",
        description="Human-readable name of the app",
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
    metadata: Optional[Dict[str, str]] = Field(
        None,
        alias="Metadata",
        description="Additional metadata for the app configuration",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_model_before(cls, values: Dict[str, str]) -> Dict[str, str]:
        """Validate model fields before instantiation.

                Args:
                    values (Dict[str, str]): Dictionary of field values to validate

                Returns:
                    Dict[str, str]: Validated field values

                Raises:
                    ValueError: If required fields are missing or invalid

                Examples:
                    >>> AppFact.validate_model_before({"Portfolio": "acme", "AppRegex": "core-api-.*"})
        -            {'Portfolio': 'acme', 'AppRegex': 'core-api-.*'}
        +            {'Portfolio': 'acme', 'AppRegex': 'core-api-.*', 'Name': 'core-api-.*'}
        """
        name = values.get("Name", values.get("name"))
        if not name:
            name = values.get("app_regex", values.get("AppRegex", ""))
            values["Name"] = name
        return values

    @classmethod
    def model_class(cls, client: str) -> AppFactsType:
        """Get the PynamoDB model class for this Pydantic model.

        Args:
            client (str): Client name for table selection

        Returns:
            AppFactsType: Client-specific PynamoDB AppFactsModel class

        Examples:
            >>> model_class = AppFact.model_class("acme")
            >>> app = model_class(portfolio="acme", app_regex="core-api-.*")
        """
        return AppFactsFactory.get_model(client)

    @classmethod
    def from_model(cls, model: AppFactsModel) -> "AppFact":
        """Convert PynamoDB AppFactsModel to Pydantic AppFact.

        Args:
            model (AppFactsModel): PynamoDB AppFactsModel instance to convert

        Returns:
            AppFact: Converted Pydantic AppFact instance

        Examples:
            >>> db_app = AppFactsModel(portfolio="acme", app_regex="core-api-.*")
            >>> pydantic_app = AppFact.from_model(db_app)
            >>> print(pydantic_app.portfolio)
            'acme'
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> AppFactsModel:
        """Convert Pydantic AppFact to PynamoDB AppFactsModel instance.

        Args:
            client (str): Client identifier for table isolation (used for factory)

        Returns:
            AppFactsModel: PynamoDB AppFactsModel instance ready for database operations

        Examples:
            >>> app_fact = AppFact(Portfolio="acme", AppRegex="core-api-.*", Name="Core API", Zone="prod", Region="us-east-1")
             >>> db_model = app_fact.to_model("acme")
             >>> db_model.save()
        """
        model_class = AppFactsFactory.get_model(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    def matches_app_name(self, name: str) -> bool:
        """Check if the given app name matches this app's regex pattern.

        Uses regex matching to determine if an application name falls within
        this app fact's scope. Falls back to exact string matching if the
        regex is invalid.

        Args:
            app_name (str): Application name to test against the regex pattern

        Returns:
            bool: True if the app name matches the regex pattern, False otherwise

        Examples:
            >>> app = AppFact(
            ...     Portfolio="acme",
            ...     AppRegex="core-api-.*",
            ...     Zone="prod",
            ...     Region="us-east-1"
            ... )
            >>> app.matches_app_name("core-api-v1")
            True

            >>> app.matches_app_name("billing-api")
            False

            >>> # Invalid regex falls back to exact match
            >>> invalid_app = AppFact(
            ...     Portfolio="acme",
            ...     AppRegex="[invalid-regex",
            ...     Name="Invalid Regex App",
            ...     Zone="prod",
            ...     Region="us-east-1"
            ... )
            >>> invalid_app.matches_app_name("[invalid-regex")
            True
        """
        try:
            return bool(re.match(self.app_regex, name))
        except re.error:
            # If regex is invalid, fall back to exact string match
            return self.app_regex == name

    def is_validation_enforced(self) -> bool:
        """Check if validation enforcement is enabled for this app.

        Checks various string representations of boolean values to determine
        if validation should be enforced for this application.

        Returns:
            bool: True if validation should be enforced, False otherwise

        Examples:
            >>> app = AppFact(
            ...     Portfolio="acme",
            ...     AppRegex="core-api-.*",
            ...     Zone="prod",
            ...     Region="us-east-1",
            ...     EnforceValidation="true"
            ... )
            >>> app.is_validation_enforced()
            True

            >>> app.enforce_validation = "false"
            >>> app.is_validation_enforced()
            False

            >>> app.enforce_validation = None
            >>> app.is_validation_enforced()
            False
        """
        if self.enforce_validation is None:
            return False
        return self.enforce_validation.lower() in ("true", "1", "yes", "on", "enabled")

    def __repr__(self) -> str:
        """Return a string representation of the AppFact instance.

        Returns:
            str: String representation for debugging

        Examples:
            >>> app = AppFact(
            ...     Portfolio="acme",
            ...     AppRegex="core-api-.*",
            ...     Zone="prod",
            ...     Region="us-east-1"
            ... )
            >>> repr(app)
            '<AppFact(portfolio=acme,app_regex=core-api-.*)>'
        """
        return f"<AppFact(portfolio={self.portfolio},app_regex={self.app_regex})>"
