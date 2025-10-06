"""Portfolio model extensions for the core-automation-items DynamoDB table.

This module provides PynamoDB and Pydantic models for portfolio items in the Configuration
Management Database (CMDB). Portfolio items represent the highest level organizational units,
serving as containers for applications and their associated infrastructure.

Key Components:
    - **PortfolioModel**: PynamoDB model with portfolio-specific field extensions
    - **PortfolioModelFactory**: Factory for client-specific model management
    - **PortfolioItem**: Pydantic model with validation and serialization

Portfolio items enable logical grouping and management of related services and resources
at the top of the deployment hierarchy: Portfolio -> App -> Branch -> Build -> Component
"""

from typing import Type, Dict, Any

from pynamodb.attributes import UnicodeAttribute

from pydantic import Field, model_validator

import core_framework as util

from ..models import ItemModel, ItemModelRecord
from ...models import TableFactory


class PortfolioModel(ItemModel):
    """Portfolio model field extensions for portfolio items in the CMDB.

    Extends the base ItemModel with portfolio-specific fields like contact email.
    Inherits all the PascalCase/snake_case conversion functionality from the parent ItemModel.

    Attributes:
        prn (str): Pipeline Reference Number (PRN) of the portfolio item (primary key).
            Format: "prn:portfolio" (e.g., "prn:core", "prn:ecommerce")
        parent_prn (str): Parent Pipeline Reference Number (PRN). For portfolios, this is typically None
            as they are top-level items in the hierarchy
        item_type (str): Type classification of the item, always "portfolio" for PortfolioModel instances
        name (str): Human-readable name of the portfolio (e.g., "Core Services", "E-Commerce Platform", "Analytics")
        created_at (datetime): Timestamp when the portfolio item was first created (auto-generated)
        updated_at (datetime): Timestamp when the portfolio item was last modified (auto-updated)
        contact_email (str): Contact email for the portfolio team or owner responsible for this portfolio

    Note:
        Portfolio items represent the highest level organizational units in the CMDB.
        They serve as containers for applications and their associated infrastructure,
        enabling logical grouping and management of related services and resources.

        The hierarchy is: Portfolio -> App -> Branch -> Build -> Component
    """

    contact_email = UnicodeAttribute(null=False, attr_name="ContactEmail")

    def __repr__(self) -> str:
        """Return string representation of the PortfolioModel.

        Returns:
            str: String representation showing key fields
        """
        return f"<Portfolio(prn={self.prn},name={self.name},contact={self.contact_email})>"


PortfolioModelType = Type[PortfolioModel]


class PortfolioModelFactory:
    """Factory class for creating client-specific PortfolioModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for PortfolioModel.
    """

    @classmethod
    def get_model(cls, client: str) -> PortfolioModelType:
        """Get the PortfolioModel class for the given client.

        Args:
            client (str): The client identifier

        Returns:
            PortfolioModelType: Client-specific PortfolioModel class
        """
        return TableFactory.get_model(PortfolioModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        """Create the PortfolioModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists
        """
        return TableFactory.create_table(PortfolioModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        """Delete the PortfolioModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist
        """
        return TableFactory.delete_table(PortfolioModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        """Check if the PortfolioModel table exists for the given client.

        Args:
            client (str): The client identifier

        Returns:
            bool: True if the table exists, False otherwise
        """
        return TableFactory.exists(PortfolioModel, client)


class PortfolioItem(ItemModelRecord):
    """Pydantic model for Portfolio items with validation and serialization.

    Extends ItemModelRecord with portfolio-specific fields like contact email.
    Provides type validation, PascalCase serialization for APIs,
    and conversion methods between PynamoDB and API formats.

    Inherits core item fields (prn, parent_prn, item_type, name) and
    audit fields (created_at, updated_at) from ItemModelRecord.

    Attributes:
        contact_email (str): Contact email for the portfolio team or owner responsible for this portfolio
    """

    # Portfolio-specific field with PascalCase alias
    contact_email: str = Field(
        ...,
        alias="ContactEmail",
        description="Contact email for the portfolio team or owner",
    )

    @model_validator(mode="before")
    @classmethod
    def model_validator_before(cls, ov: Dict[str, Any]) -> Dict[str, Any]:
        """Validate required fields before model instantiation.

        Args:
            values: Input values to validate

        Returns:
            Dict[str, Any]: Validated values

        Raises:
            ValueError: If required fields are missing or invalid
        """
        values = util.pascal_case_to_snake_case(ov)

        # do not snake_case metadata.  Leave it as user originally provided it
        values["metadata"] = ov.get("metadata", ov.get("Metadata", None))

        portfolio_prn = values.get("prn", values.pop("portfolio_prn", None))
        if not portfolio_prn:
            portfolio_prn = util.generate_portfolio_prn(values)
        if not util.validate_portfolio_prn(portfolio_prn):
            raise ValueError(f"Invalid portfolio PRN: {portfolio_prn}")
        values["prn"] = portfolio_prn

        parent_prn = cls.get_parent_prn(portfolio_prn)
        if parent_prn != "prn":
            raise ValueError(f"Portfolio PRN must be at the top level, got: {portfolio_prn}")
        values["parent_prn"] = parent_prn

        name = values.get("name")
        if name is None:
            name = portfolio_prn[portfolio_prn.rindex(":") + 1 :]
            values["name"] = name

        contact_email = values.get("contact_email")
        if not contact_email:
            raise ValueError("Contact email is required for PortfolioItem")

        values["item_type"] = "portfolio"

        return values

    @classmethod
    def model_class(cls, client: str) -> PortfolioModelType:
        """Get the PynamoDB model class for this Pydantic model.

        Args:
            client (str): Client identifier for table selection

        Returns:
            PortfolioModelType: Client-specific PynamoDB PortfolioModel class
        """
        return PortfolioModelFactory.get_model(client)

    @classmethod
    def from_model(cls, model: PortfolioModel) -> "PortfolioItem":
        """Convert a PynamoDB model instance to a Pydantic PortfolioItem.

        Args:
            model (PortfolioModel): PynamoDB model instance

        Returns:
            PortfolioItem: Pydantic PortfolioItem instance
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> PortfolioModel:
        """Convert this Pydantic PortfolioItem to a PynamoDB model instance.

        Args:
            client (str): Client identifier for table selection

        Returns:
            PortfolioModel: PynamoDB model instance with data from this PortfolioItem
        """
        model_class = self.model_class(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    def __repr__(self) -> str:
        """Return a string representation of the PortfolioItem instance.

        Returns:
            str: String representation of the portfolio item
        """
        return f"<PortfolioItem(prn={self.prn},name={self.name},contact={self.contact_email})>"
