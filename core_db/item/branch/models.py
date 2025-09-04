"""Branch model extensions for the core-automation-items DynamoDB table.

This module provides PynamoDB and Pydantic models for branch items in the Configuration
Management Database (CMDB). Branch items represent version control branches within
applications, serving as containers for builds and their associated infrastructure.

Key Components:
    - **BranchModel**: PynamoDB model with branch-specific field extensions
    - **BranchModelFactory**: Factory for client-specific model management
    - **ReleaseInfo**: Pydantic model for released build information
    - **BranchItem**: Pydantic model with validation and serialization

Branch items track the relationship between source code branches and their deployed
infrastructure, enabling full traceability from code to AWS resources in the hierarchy:
Portfolio -> App -> Branch -> Build -> Component
"""

from typing import Type, Dict, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pynamodb.attributes import UnicodeAttribute, MapAttribute

import core_framework as util

from ...models import TableFactory
from ..models import ItemModel, ItemModelRecord


class BranchModel(ItemModel):
    """Branch model field extensions for branch items in the CMDB.

    Extends the base ItemModel with branch-specific fields like short name,
    released build PRN, portfolio PRN, and app PRN. Inherits all the
    PascalCase/snake_case conversion functionality from the parent ItemModel.

    Attributes:
        prn (str): Pipeline Reference Number (PRN) of the branch item (primary key).
            Format: "prn:portfolio:app:branch"
        parent_prn (str): Parent Pipeline Reference Number (PRN) pointing to the app item.
            Format: "prn:portfolio:app"
        item_type (str): Type classification of the item, always "branch" for BranchModel instances
        name (str): Human-readable name of the branch
        created_at (datetime): Timestamp when the branch item was first created (auto-generated)
        updated_at (datetime): Timestamp when the branch item was last modified (auto-updated)
        short_name (str): Short name of the branch, typically the Git branch name without prefixes
        released_build_prn (str, optional): PRN of the currently released build for this branch (if any).
            Format: "prn:portfolio:app:branch:build"
        portfolio_prn (str): Portfolio PRN that this branch belongs to.
            Format: "prn:portfolio"
        app_prn (str): App PRN that this branch belongs to.
            Format: "prn:portfolio:app"

    Note:
        Branch items represent Git branches or deployment environments within an
        application. They track the relationship between source code branches and
        their deployed infrastructure, enabling full traceability from code to
        AWS resources.

        The hierarchy is: Portfolio -> App -> Branch -> Build -> Component
    """

    short_name = UnicodeAttribute(null=False, attr_name="ShortName")
    released_build = MapAttribute(null=True, attr_name="ReleasedBuild")

    portfolio_prn = UnicodeAttribute(null=False, attr_name="PortfolioPrn")
    app_prn = UnicodeAttribute(null=False, attr_name="AppPrn")

    def __repr__(self) -> str:
        """Return string representation of the BranchModel.

        Returns:
            str: String representation showing key fields
        """
        return f"<BranchModel(prn={self.prn},name={self.name},short={self.short_name})>"


BranchModelType = Type[BranchModel]


class BranchModelFactory:
    """Factory class for creating client-specific BranchModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for BranchModel.
    """

    @classmethod
    def get_model(cls, client: str) -> BranchModelType:
        """Get the BranchModel class for the given client.

        Args:
            client (str): The client identifier

        Returns:
            BranchModelType: Client-specific BranchModel class
        """
        return TableFactory.get_model(BranchModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        """Create the BranchModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists
        """
        return TableFactory.create_table(BranchModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        """Delete the BranchModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist
        """
        return TableFactory.delete_table(BranchModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        """Check if the BranchModel table exists for the given client.

        Args:
            client (str): The client identifier

        Returns:
            bool: True if the table exists, False otherwise
        """
        return TableFactory.exists(BranchModel, client)


class ReleaseInfo(BaseModel):
    """Pydantic model for release information in branch items.

    Represents the released build PRN and provides validation and serialization
    functionality. Used to track the currently released build for a branch.

    Attributes:
        prn (str, optional): Pipeline Reference Number (PRN) of the released build.
            Format: "prn:portfolio:app:branch:build"
        release_date (str, optional): Release date of the build
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )

    prn: Optional[str] = Field(
        None,
        alias="Prn",
        description="Pipeline Reference Number of the released build",
    )
    build: Optional[str] = Field(
        None,
        alias="Name",
        description="Name of the released build",
    )
    release_date: Optional[str] = Field(
        None,
        alias="ReleaseDate",
        description="Release date of the build",
    )

    @model_validator(mode="before")
    def validate_prn(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the PRN field before model instantiation.

        Args:
            values (Dict[str, Any]): Input values to validate

        Returns:
            Dict[str, Any]: Validated values

        Raises:
            ValueError: If the PRN format is invalid
        """
        values = util.pascal_case_to_snake_case(values)

        prn = values.pop(
            "released_build_prn",
            values.pop("ReleasedBuildPrn", values.pop("prn", values.pop("Prn", None))),
        )
        if not prn:
            raise ValueError("PRN is required for ReleaseInfo")

        build = values.pop("build", values.pop("Build", prn[prn.rindex(":") + 1 :] if prn else None))
        if not build:
            raise ValueError("Build is required for ReleaseInfo")
        values["build"] = build

        prn = prn.replace(".", "-")  # Normalize PRN format just in case

        if prn and not util.validate_build_prn(prn):
            raise ValueError(f"Invalid or missing release build PRN: {prn}")
        values["prn"] = prn

        return values


class BranchItem(ItemModelRecord):
    """Pydantic model for Branch items with validation and serialization.

    Extends ItemModelRecord with branch-specific fields like short name,
    released build PRN, and parent PRN references. Provides type validation,
    PascalCase serialization for APIs, and conversion methods between
    PynamoDB and API formats.

    Inherits core item fields (prn, parent_prn, item_type, name) and
    audit fields (created_at, updated_at) from ItemModelRecord.

    Attributes:
        short_name (str): Short name of the branch, typically the Git branch name without prefixes
        released_build (ReleaseInfo): Released build information for this branch
        portfolio_prn (str): Portfolio PRN that this branch belongs to
        app_prn (str): App PRN that this branch belongs to
    """

    # Branch-specific fields with PascalCase aliases
    short_name: str = Field(
        None,
        alias="ShortName",
        description="Short name of the branch, typically the Git branch name without prefixes",
    )
    portfolio_prn: str = Field(
        None,
        alias="PortfolioPrn",
        description="Portfolio PRN that this branch belongs to",
    )
    app_prn: str = Field(
        None,
        alias="AppPrn",
        description="App PRN that this branch belongs to",
    )
    released_build: Optional[ReleaseInfo] = Field(
        None,
        alias="ReleasedBuild",
        description="Released build information for this branch",
    )

    @model_validator(mode="before")
    def validate_fields(cls, ov: Dict[str, Any]) -> Dict[str, Any]:
        """Validate required fields before model instantiation.

        Ensures that all required fields are present and valid.
        Generates missing fields where possible.

        Args:
            values (Dict[str, Any]): Dictionary of field values to validate

        Returns:
            Dict[str, Any]: Validated field values

        Raises:
            ValueError: If any required field is missing or invalid
        """
        values = util.pascal_case_to_snake_case(ov)

        # do not snake_case metadata.  Leave it as user originally provided it
        values["metadata"] = ov.get("metadata", ov.get("Metadata", None))

        branch_prn = values.get("prn", values.pop("branch_prn", None))
        if not branch_prn:
            branch_prn = util.generate_branch_prn(values)
        if not util.validate_branch_prn(branch_prn):
            raise ValueError(f"Invalid or missing branch PRN: {branch_prn}")
        values["prn"] = branch_prn

        parent_prn: str = cls.get_parent_prn(branch_prn)
        if not util.validate_app_prn(parent_prn):
            raise ValueError(f"Invalid or missing parent PRN: {parent_prn}")
        values["parent_prn"] = parent_prn

        app_prn = values.get("app_prn")
        if not app_prn:
            app_prn = util.generate_app_prn(values)
            values["app_prn"] = app_prn
        if not util.validate_app_prn(app_prn):
            raise ValueError(f"Invalid app PRN: {app_prn}")

        portfolio_prn = values.get("portfolio_prn")
        if not portfolio_prn:
            portfolio_prn = util.generate_portfolio_prn(values)
            values["portfolio_prn"] = portfolio_prn
        if not util.validate_portfolio_prn(portfolio_prn):
            raise ValueError(f"Invalid or missing portfolio PRN: {portfolio_prn}")

        released_build = values.get("released_build")
        if released_build is None:
            released_build_prn = values.get("released_build_prn")
            if released_build_prn:
                released_build = ReleaseInfo(prn=released_build_prn)
            else:
                released_build = None
            values["released_build"] = released_build

        name = values.get("name")
        if not name:
            name = branch_prn[branch_prn.rindex(":") + 1 :]
            values["name"] = name

        short_name = values.get("short_name")
        if not short_name:
            short_name = util.generate_branch_short_name(name)
            values["short_name"] = short_name

        values["item_type"] = "branch"

        return values

    @classmethod
    def model_class(cls, client: str = None) -> BranchModelType:
        """Get the PynamoDB model class for this Pydantic model.

        Args:
            client (str): Client identifier for table selection

        Returns:
            BranchModelType: Client-specific PynamoDB BranchModel class
        """
        return BranchModelFactory.get_model(client)

    @classmethod
    def from_model(cls, model: BranchModel) -> "BranchItem":
        """Convert a PynamoDB model instance to a Pydantic BranchItem.

        Args:
            model (BranchModel): PynamoDB model instance

        Returns:
            BranchItem: Pydantic BranchItem instance with data from the model
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> BranchModel:
        """Convert this Pydantic BranchItem to a PynamoDB model instance.

        Args:
            client (str): Client identifier for table selection

        Returns:
            BranchModel: PynamoDB model instance with data from this BranchItem
        """
        model_class = self.model_class(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    def __repr__(self) -> str:
        """Return a string representation of the BranchItem instance.

        Returns:
            str: String representation of the branch item
        """
        return f"<BranchItem(prn={self.prn},name={self.name},short={self.short_name})>"
