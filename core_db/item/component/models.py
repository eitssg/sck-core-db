"""Component model extensions for the core-automation-items DynamoDB table.

This module provides PynamoDB and Pydantic models for component items in the Configuration
Management Database (CMDB). Component items represent the actual AWS resources deployed as
part of a build, serving as the leaf nodes in the deployment hierarchy.

Key Components:
    - **ComponentModel**: PynamoDB model with component-specific field extensions
    - **ComponentModelFactory**: Factory for client-specific model management
    - **ComponentItem**: Pydantic model with validation and serialization

Component items track individual AWS resources like EC2 instances, S3 buckets, RDS databases,
Lambda functions, etc., enabling full traceability in the hierarchy:
Portfolio -> App -> Branch -> Build -> Component
"""

from typing import Type, Dict, Any, Optional
from pynamodb.attributes import UnicodeAttribute

from pydantic import Field, model_validator

import core_framework as util

from ..models import ItemModel, ItemModelRecord
from ...models import TableFactory

from core_framework.status import INIT


class ComponentModel(ItemModel):
    """Component model field extensions for component items in the CMDB.

    Extends the base ItemModel with component-specific fields like status, message,
    component type, image details, and parent PRN references. Inherits all the
    PascalCase/snake_case conversion functionality from the parent ItemModel.

    Attributes:
        prn (str): Pipeline Reference Number (PRN) of the component item (primary key).
            Format: "prn:portfolio:app:branch:build:component"
        parent_prn (str): Parent Pipeline Reference Number (PRN) pointing to the build item.
            Format: "prn:portfolio:app:branch:build"
        item_type (str): Type classification of the item, always "component" for ComponentModel instances
        name (str): Human-readable name of the component
        created_at (datetime): Timestamp when the component item was first created (auto-generated)
        updated_at (datetime): Timestamp when the component item was last modified (auto-updated)
        status (str): Status of the component. Uses values from BuildStatus enum.
            Default: INIT. Common values: INIT, RUNNING, SUCCESS, FAILED
        message (str, optional): Message details for the component providing status or error information
        component_type (str, optional): Component type classification (e.g., "ec2", "s3", "eni", "rds", "lambda")
        image_id (str, optional): Image ID of the EC2 component
        image_alias (str, optional): Image alias name of the EC2 component
        portfolio_prn (str): Portfolio PRN that this component belongs to.
            Format: "prn:portfolio"
        app_prn (str): App PRN that this component belongs to.
            Format: "prn:portfolio:app"
        branch_prn (str): Branch PRN that this component belongs to.
            Format: "prn:portfolio:app:branch"
        build_prn (str): Build PRN that this component belongs to.
            Format: "prn:portfolio:app:branch:build"

    Note:
        Component items represent the actual AWS resources that get deployed as part
        of a build. They are the leaf nodes in the deployment hierarchy and track
        the individual infrastructure components like EC2 instances, S3 buckets,
        RDS databases, Lambda functions, etc.

        The hierarchy is: Portfolio -> App -> Branch -> Build -> Component
    """

    status = UnicodeAttribute(default_for_new=INIT, attr_name="Status")
    message = UnicodeAttribute(null=True, attr_name="Message")
    component_type = UnicodeAttribute(null=True, attr_name="ComponentType")
    image_id = UnicodeAttribute(null=True, attr_name="ImageId")
    image_alias = UnicodeAttribute(null=True, attr_name="ImageAlias")

    portfolio_prn = UnicodeAttribute(null=False, attr_name="PortfolioPrn")
    app_prn = UnicodeAttribute(null=False, attr_name="AppPrn")
    branch_prn = UnicodeAttribute(null=False, attr_name="BranchPrn")
    build_prn = UnicodeAttribute(null=False, attr_name="BuildPrn")

    def __repr__(self) -> str:
        """Return string representation of the ComponentModel.

        Returns:
            str: String representation showing key fields
        """
        return f"<Component(prn={self.prn},name={self.name},component_type={self.component_type})>"


ComponentModelType = Type[ComponentModel]


class ComponentModelFactory:
    """Factory class for creating client-specific ComponentModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for ComponentModel.
    """

    @classmethod
    def get_model(cls, client: str) -> ComponentModelType:
        """Get the ComponentModel class for the given client.

        Args:
            client (str): The client identifier

        Returns:
            ComponentModelType: Client-specific ComponentModel class
        """
        return TableFactory.get_model(ComponentModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        """Create the ComponentModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists
        """
        return TableFactory.create_table(ComponentModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        """Delete the ComponentModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist
        """
        return TableFactory.delete_table(ComponentModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        """Check if the ComponentModel table exists for the given client.

        Args:
            client (str): The client identifier

        Returns:
            bool: True if the table exists, False otherwise
        """
        return TableFactory.exists(ComponentModel, client)


class ComponentItem(ItemModelRecord):
    """Pydantic model for Component items with validation and serialization.

    Extends ItemModelRecord with component-specific fields like status, message,
    component type, image details, and parent PRN references. Provides type validation,
    PascalCase serialization for APIs, and conversion methods between PynamoDB and API formats.

    Inherits core item fields (prn, parent_prn, item_type, name) and
    audit fields (created_at, updated_at) from ItemModelRecord.

    Attributes:
        status (str): Status of the component (INIT, RUNNING, SUCCESS, FAILED)
        message (str, optional): Message details for the component providing status or error information
        component_type (str, optional): Component type classification (e.g., "ec2", "s3", "eni", "rds", "lambda")
        image_id (str, optional): Image ID of the EC2 component
        image_alias (str, optional): Image alias name of the EC2 component
        portfolio_prn (str): Portfolio PRN that this component belongs to
        app_prn (str): App PRN that this component belongs to
        branch_prn (str): Branch PRN that this component belongs to
        build_prn (str): Build PRN that this component belongs to
    """

    # Component-specific fields with PascalCase aliases
    status: str = Field(
        default="INIT",
        alias="Status",
        description="Status of the component (INIT, RUNNING, SUCCESS, FAILED)",
    )
    message: Optional[str] = Field(
        None,
        alias="Message",
        description="Message details for the component providing status or error information",
    )
    component_type: Optional[str] = Field(
        None,
        alias="ComponentType",
        description="Component type classification (e.g., 'ec2', 's3', 'eni', 'rds', 'lambda')",
    )
    image_id: Optional[str] = Field(
        None, alias="ImageId", description="Image ID of the EC2 component"
    )
    image_alias: Optional[str] = Field(
        None, alias="ImageAlias", description="Image alias name of the EC2 component"
    )
    portfolio_prn: str = Field(
        None,
        alias="PortfolioPrn",
        description="Portfolio PRN that this component belongs to",
    )
    app_prn: str = Field(
        None, alias="AppPrn", description="App PRN that this component belongs to"
    )
    branch_prn: str = Field(
        None, alias="BranchPrn", description="Branch PRN that this component belongs to"
    )
    build_prn: str = Field(
        None, alias="BuildPrn", description="Build PRN that this component belongs to"
    )

    @model_validator(mode="before")
    def validate_fields(cls, ov: Dict[str, Any]) -> Dict[str, Any]:
        """Validate required fields before model instantiation.

        Args:
            values (Dict[str, Any]): Input values to validate

        Returns:
            Dict[str, Any]: Validated values

        Raises:
            ValueError: If required fields are missing or invalid
        """
        values = util.pascal_case_to_snake_case(ov)

        # Done't allow metadata to be set directly, use the metadata field instead
        values["metadata"] = ov.get("metadata", ov.get("Metadata", None))

        component_prn = values.get("prn", values.get("component_prn", None))
        if not component_prn:
            component_prn = util.generate_component_prn(values)
        normalized_component_prn = component_prn.replace(
            ".", "-"
        )  # Normalize PRN format just in case
        if not util.validate_component_prn(normalized_component_prn):
            raise ValueError(f"Invalid component_prn: {normalized_component_prn}")
        values["prn"] = normalized_component_prn

        parent_prn = cls.get_parent_prn(normalized_component_prn)
        normalized_parent_prn = parent_prn.replace(
            ".", "-"
        )  # Normalize PRN format just in case
        if not util.validate_build_prn(normalized_parent_prn):
            raise ValueError(f"Invalid or missing parent PRN: {normalized_parent_prn}")
        values["parent_prn"] = normalized_parent_prn

        build_prn = values.get("build_prn")
        if not build_prn:
            build_prn = util.generate_build_prn(values)
        normalized_build_prn = build_prn.replace(
            ".", "-"
        )  # Normalize PRN format just in case
        if not util.validate_build_prn(normalized_build_prn):
            raise ValueError(f"Invalid build_prn: {normalized_build_prn}")
        values["build_prn"] = normalized_build_prn

        # Branch PRN reference
        branch_prn = values.get("branch_prn")
        if not branch_prn:
            branch_prn = util.generate_branch_prn(values)
            values["branch_prn"] = branch_prn
        if not util.validate_branch_prn(branch_prn):
            raise ValueError(f"Invalid branch_prn: {branch_prn}")

        # App PRN reference
        app_prn = values.get("app_prn")
        if not app_prn:
            app_prn = util.generate_app_prn(values)
            values["app_prn"] = app_prn
        if not util.validate_app_prn(app_prn):
            raise ValueError(f"Invalid app_prn: {app_prn}")

        # Portfolio PRN Reference
        portfolio_prn = values.get("portfolio_prn")
        if not portfolio_prn:
            portfolio_prn = util.generate_portfolio_prn(values)
            values["portfolio_prn"] = portfolio_prn
        if not util.validate_portfolio_prn(portfolio_prn):
            raise ValueError(f"Invalid portfolio_prn: {portfolio_prn}")

        name = values.get("name")
        if not name:
            name = component_prn[component_prn.rindex(":") + 1 :]
            values["name"] = name

        values["item_type"] = "component"

        return values

    @classmethod
    def model_class(cls, client: str) -> ComponentModelType:
        """Get the PynamoDB model class for this Pydantic model.

        Args:
            client (str): Client identifier for table selection

        Returns:
            ComponentModelType: Client-specific PynamoDB ComponentModel class
        """
        return ComponentModelFactory.get_model(client)

    @classmethod
    def from_model(cls, model: ComponentModel) -> "ComponentItem":
        """Convert a PynamoDB model instance to a Pydantic ComponentItem.

        Args:
            model (ComponentModel): PynamoDB model instance

        Returns:
            ComponentItem: Pydantic ComponentItem instance with data from the model
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> ComponentModel:
        """Convert this Pydantic ComponentItem to a PynamoDB model instance.

        Args:
            client (str): Client identifier for table selection

        Returns:
            ComponentModel: PynamoDB model instance with data from this ComponentItem
        """
        model_class = self.model_class(client)
        return model_class(**self.model_dump(by_alias=True, exclude_unset=True))

    def __repr__(self) -> str:
        """Return a string representation of the ComponentItem instance.

        Returns:
            str: String representation of the component item
        """
        return f"<ComponentItem(prn={self.prn}, name={self.name}, component_type={self.component_type})>"
