"""This module provides the field extensions for Items.App in the core-automation-items table."""

from typing import Type, Dict, Any, Self
from pydantic import Field
from pydantic.functional_validators import model_validator
from pynamodb.attributes import UnicodeAttribute

import core_framework as util

from ...models import TableFactory
from ..models import ItemModel, ItemModelRecord


class AppModel(ItemModel):
    """App model field extensions for application items in the CMDB.

    Extends the base ItemModel with app-specific fields like contact email
    and portfolio reference. Inherits all the PascalCase/snake_case conversion
    functionality from the parent ItemModel.

    Attributes:
        prn (str): Pipeline Reference Number (PRN) of the app item (primary key).
            Format: "prn:portfolio:app" (e.g., "prn:core:api")
        parent_prn (str): Parent Pipeline Reference Number (PRN) pointing to the portfolio item.
            Format: "prn:portfolio" (e.g., "prn:core")
        item_type (str): Type classification of the item, always "app" for AppModel instances
        name (str): Human-readable name of the application (e.g., "API Service", "Frontend", "Database")
        created_at (datetime): Timestamp when the app item was first created (auto-generated)
        updated_at (datetime): Timestamp when the app item was last modified (auto-updated)
        contact_email (str): Contact email for the app team or maintainer responsible for this application
        portfolio_prn (str): Portfolio PRN that this app belongs to.
            Format: "prn:portfolio" (e.g., "prn:core")

    Note:
        App items represent functional components or modules within a portfolio.
        They serve as containers for branches and their associated builds, enabling
        full traceability from application level down to individual AWS resources.

        The hierarchy is: Portfolio -> App -> Branch -> Build -> Component
    """

    contact_email = UnicodeAttribute(null=False, attr_name="ContactEmail")
    portfolio_prn = UnicodeAttribute(null=False, attr_name="PortfolioPrn")

    def __repr__(self) -> str:
        """Return string representation of the AppModel.

        Returns:
            str: String representation showing key fields
        """
        return f"<App(prn={self.prn},name={self.name},contact={self.contact_email})>"


AppModelType = Type[AppModel]


class AppModelFactory:
    """Factory class for creating client-specific AppModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for AppModel.
    """

    @classmethod
    def get_model(cls, client: str) -> AppModelType:
        """Get the AppModel class for the given client.

        Args:
            client (str): The client identifier

        Returns:
            AppModelType: Client-specific AppModel class
        """
        return TableFactory.get_model(AppModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        """Create the AppModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists
        """
        return TableFactory.create_table(AppModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        """Delete the AppModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist
        """
        return TableFactory.delete_table(AppModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        """Check if the AppModel table exists for the given client.

        Args:
            client (str): The client identifier

        Returns:
            bool: True if the table exists, False otherwise
        """
        return TableFactory.exists(AppModel, client)


class AppItem(ItemModelRecord):
    """Pydantic model for App items with validation and serialization.

    Extends ItemModelRecord with app-specific fields like contact email
    and portfolio reference. Provides type validation, PascalCase serialization
    for APIs, and conversion methods between PynamoDB and API formats.

    Inherits core item fields (prn, parent_prn, item_type, name) and
    audit fields (created_at, updated_at) from ItemModelRecord.

    Attributes:
        contact_email (str): Contact email for the app team or maintainer responsible for this application
        portfolio_prn (str): Portfolio PRN that this app belongs to
    """

    # App-specific fields with PascalCase aliases
    contact_email: str = Field(
        ..., alias="ContactEmail", description="Contact email for the app team or maintainer responsible for this application"
    )
    portfolio_prn: str = Field(..., alias="PortfolioPrn", description="Portfolio PRN that this app belongs to")

    @model_validator(mode="before")
    def model_validate_before(cls, ov: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and transform input data before model instantiation.

        Args:
            values (Dict[str, Any]): Input data to validate

        Returns:
            Dict[str, Any]: Validated and transformed data

        Raises:
            ValueError: If required fields are missing or invalid
        """
        values = util.pascal_case_to_snake_case(ov)

        # do not snake_case metadata.  Leave it as user originally provided it
        values["metadata"] = ov.get("metadata", ov.get("Metadata", None))

        app_prn = values.get("prn", values.pop("app_prn", None))
        if not app_prn:
            app_prn = util.generate_app_prn(values)
        if not util.validate_app_prn(app_prn):
            raise ValueError(f"Invalid or missing app PRN: {app_prn}")
        values["prn"] = app_prn

        parent_prn: str = cls.get_parent_prn(app_prn)
        if not util.validate_portfolio_prn(parent_prn):
            raise ValueError(f"Invalid or missing parent PRN: {parent_prn}")
        values["parent_prn"] = parent_prn

        portfolio_prn = values.get("portfolio_prn")
        if not portfolio_prn:
            portfolio_prn = util.generate_portfolio_prn(values)
            values["portfolio_prn"] = portfolio_prn
        if not util.validate_portfolio_prn(portfolio_prn):
            raise ValueError(f"Invalid or missing portfolio PRN: {portfolio_prn}")

        name = values.get("name")
        if name is None:
            name = app_prn[app_prn.rindex(":") + 1 :]
            values["name"] = name

        contact_email = values.get("contact_email")
        if not contact_email:
            raise ValueError("Contact email is required for AppItem")

        values["item_type"] = "app"

        return values

    @classmethod
    def model_class(cls, client: str = None) -> AppModelType:
        """Get the PynamoDB model class for this Pydantic model.

        Args:
            client (str): Client identifier for table selection

        Returns:
            AppModelType: Client-specific PynamoDB AppModel class
        """
        if client is None:
            client = util.get_client()
        return AppModelFactory.get_model(client)

    @classmethod
    def from_model(cls, model: AppModel) -> Self:
        """Convert a PynamoDB model instance to a Pydantic AppItem.

        Args:
            model (AppModel): PynamoDB model instance

        Returns:
            AppItem: Pydantic AppItem instance with data from the model
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> AppModel:
        """Convert this Pydantic AppItem to a PynamoDB model instance.

        Args:
            client (str): Client identifier for table selection

        Returns:
            AppModel: PynamoDB model instance with data from this AppItem
        """
        model_class = self.model_class(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    def __repr__(self) -> str:
        """Return a string representation of the AppItem instance.

        Returns:
            str: String representation of the app item
        """
        return f"<AppItem(prn={self.prn},name={self.name},contact={self.contact_email})>"
