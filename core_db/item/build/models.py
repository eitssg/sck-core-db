"""Build model extensions for the core-automation-items DynamoDB table.

This module provides PynamoDB and Pydantic models for build items in the Configuration
Management Database (CMDB). Build items represent specific infrastructure deployment
instances within branches, tracking the deployment lifecycle from initiation to completion.

Key Components:
    - **BuildModel**: PynamoDB model with build-specific field extensions
    - **BuildModelFactory**: Factory for client-specific model management
    - **BuildItem**: Pydantic model with validation and serialization

Build items track deployment status, context information, and serve as containers
for the actual AWS components that get deployed, enabling full traceability in the hierarchy:
Portfolio -> App -> Branch -> Build -> Component
"""

from typing import Type, Dict, Any, Optional, Self
from core_framework.status import BuildStatus
from pydantic import Field, model_validator
from pynamodb.attributes import UnicodeAttribute, MapAttribute

import core_framework as util

from ...models import TableFactory
from ..models import ItemModel, ItemModelRecord


class BuildModel(ItemModel):
    """Build model field extensions for build items in the CMDB.

    Extends the base ItemModel with build-specific fields like status, message,
    context, and parent PRN references. Inherits all the PascalCase/snake_case
    conversion functionality from the parent ItemModel.

    Attributes:
        prn (str): Pipeline Reference Number (PRN) of the build item (primary key).
            Format: "prn:portfolio:app:branch:build"
        parent_prn (str): Parent Pipeline Reference Number (PRN) pointing to the branch item.
            Format: "prn:portfolio:app:branch"
        item_type (str): Type classification of the item, always "build" for BuildModel instances
        name (str): Human-readable name of the build
        created_at (datetime): Timestamp when the build item was first created (auto-generated)
        updated_at (datetime): Timestamp when the build item was last modified (auto-updated)
        status (str): Current status of the build. Uses values from BuildStatus enum.
            Default: INIT. Common values: INIT, RUNNING, SUCCESS, FAILED
        message (str, optional): Human-readable message providing details about the build status or outcome
        context (dict, optional): Additional context information for the build
        portfolio_prn (str): Portfolio PRN that this build belongs to.
            Format: "prn:portfolio"
        app_prn (str): App PRN that this build belongs to.
            Format: "prn:portfolio:app"
        branch_prn (str): Branch PRN that this build belongs to.
            Format: "prn:portfolio:app:branch"

    Note:
        Build items represent specific infrastructure deployment instances within a
        branch. They track the deployment lifecycle from initiation to completion,
        including status updates and context information. Each build serves as a
        container for the actual AWS components that get deployed.

        The hierarchy is: Portfolio -> App -> Branch -> Build -> Component
    """

    status = UnicodeAttribute(default_for_new="INIT", attr_name="Status")
    message = UnicodeAttribute(null=True, attr_name="Message")
    context = MapAttribute(null=True, attr_name="Context")
    portfolio_prn = UnicodeAttribute(null=False, attr_name="PortfolioPrn")
    app_prn = UnicodeAttribute(null=False, attr_name="AppPrn")
    branch_prn = UnicodeAttribute(null=False, attr_name="BranchPrn")

    def __repr__(self) -> str:
        """Return string representation of the BuildModel.

        Returns:
            str: String representation showing key fields
        """
        return f"<BuildModel(prn={self.prn},name={self.name},status={self.status})>"


BuildModelType = Type[BuildModel]


class BuildModelFactory:
    """Factory class for creating client-specific BuildModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for BuildModel.
    """

    @classmethod
    def get_model(cls, client: str) -> BuildModelType:
        """Get the BuildModel class for the given client.

        Args:
            client (str): The client identifier

        Returns:
            BuildModelType: Client-specific BuildModel class
        """
        return TableFactory.get_model(BuildModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        """Create the BuildModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists
        """
        return TableFactory.create_table(BuildModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        """Delete the BuildModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist
        """
        return TableFactory.delete_table(BuildModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        """Check if the BuildModel table exists for the given client.

        Args:
            client (str): The client identifier

        Returns:
            bool: True if the table exists, False otherwise
        """
        return TableFactory.exists(BuildModel, client)


class BuildItem(ItemModelRecord):
    """Pydantic model for Build items with validation and serialization.

    Extends ItemModelRecord with build-specific fields like status, message, context,
    and parent PRN references. Provides type validation, PascalCase serialization for APIs,
    and conversion methods between PynamoDB and API formats.

    Inherits core item fields (prn, parent_prn, item_type, name) and
    audit fields (created_at, updated_at) from ItemModelRecord.

    Attributes:
        status (str): Current status of the build (INIT, RUNNING, SUCCESS, FAILED)
        message (str, optional): Human-readable message providing details about the build status or outcome
        context (dict, optional): Additional context information for the build
        portfolio_prn (str): Portfolio PRN that this build belongs to
        app_prn (str): App PRN that this build belongs to
        branch_prn (str): Branch PRN that this build belongs to
    """

    # Build-specific fields with PascalCase aliases
    status: str = Field(default="INIT", alias="Status", description="Current status of the build (INIT, RUNNING, SUCCESS, FAILED)")
    message: Optional[str] = Field(
        None, alias="Message", description="Human-readable message providing details about the build status or outcome"
    )
    context: Optional[Dict[str, Any]] = Field(None, alias="Context", description="Additional context information for the build")
    portfolio_prn: str = Field(None, alias="PortfolioPrn", description="Portfolio PRN that this build belongs to")
    app_prn: str = Field(None, alias="AppPrn", description="App PRN that this build belongs to")
    branch_prn: str = Field(None, alias="BranchPrn", description="Branch PRN that this build belongs to")

    @model_validator(mode="before")
    def validate_model_before(cls, ov: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the model before instantiation.

        Ensures that the build PRN is valid and that required fields are present.

        Args:
            values (Dict[str, Any]): The field values to validate

        Returns:
            Dict[str, Any]: Validated field values

        Raises:
            ValueError: If the build PRN is invalid or required fields are missing
        """
        values = util.pascal_case_to_snake_case(ov)

        # Done't allow metadata to be set directly, use the metadata field instead
        values["metadata"] = ov.get("metadata", ov.get("Metadata", None))

        build_prn = values.get("prn", values.get("build_prn", None))
        if build_prn is None:
            build_prn = util.generate_build_prn(values)

        normalized_build_prn = build_prn.replace(".", "-")  # Normalize PRN format just in case
        if not util.validate_build_prn(normalized_build_prn):
            raise ValueError(f"Invalid build PRN provided: {build_prn}")
        values["prn"] = normalized_build_prn

        parent_prn: str = cls.get_parent_prn(normalized_build_prn)
        if not util.validate_branch_prn(parent_prn):
            raise ValueError(f"Invalid or missing parent PRN: {parent_prn}")
        values["parent_prn"] = parent_prn

        # Branch PRN reference
        branch_prn = values.get("branch_prn")
        if not branch_prn:
            branch_prn = util.generate_branch_prn(values)
            values["branch_prn"] = branch_prn
        if not util.validate_branch_prn(branch_prn):
            raise ValueError(f"Invalid branch PRN provided: {branch_prn}")

        # App PRN reference
        app_prn = values.get("app_prn")
        if not app_prn:
            app_prn = util.generate_app_prn(values)
            values["app_prn"] = app_prn
        if not util.validate_app_prn(app_prn):
            raise ValueError(f"Invalid app PRN provided: {app_prn}")

        # Portfolio PRN Reference
        portfolio_prn = values.get("portfolio_prn")
        if not portfolio_prn:
            portfolio_prn = util.generate_portfolio_prn(values)
            values["portfolio_prn"] = portfolio_prn
        if not util.validate_portfolio_prn(portfolio_prn):
            raise ValueError(f"Invalid portfolio PRN provided: {portfolio_prn}")

        name = values.get("name")
        if not name:
            name = build_prn[build_prn.rindex(":") + 1 :]
            values["name"] = name

        values["status"] = str(BuildStatus.from_str(values.get("status", "INIT")))

        values["item_type"] = "build"

        return values

    @classmethod
    def model_class(cls, client: str = None) -> BuildModelType:
        """Get the PynamoDB model class for this Pydantic model.

        Args:
            client (str): Client identifier for table selection

        Returns:
            BuildModelType: Client-specific PynamoDB BuildModel class
        """
        return BuildModelFactory.get_model(client)

    @classmethod
    def from_model(cls, model: BuildModel) -> Self:
        """Convert a PynamoDB model instance to a Pydantic BuildItem.

        Args:
            model (BuildModel): PynamoDB model instance

        Returns:
            BuildItem: Pydantic BuildItem instance with data from the model
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> BuildModel:
        """Convert this Pydantic BuildItem to a PynamoDB model instance.

        Args:
            client (str): Client identifier for table selection

        Returns:
            BuildModel: PynamoDB model instance with data from this BuildItem
        """
        model_class = self.model_class(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    def __repr__(self) -> str:
        """Return a string representation of the BuildItem instance.

        Returns:
            str: String representation of the build item
        """
        return f"<BuildItem(prn={self.prn},name={self.name},status={self.status})>"
