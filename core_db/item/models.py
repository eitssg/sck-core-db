"""Defines the generic model for items stored in the core-automation-items table.

This will be subclassed by portfolio, app, branch, build, component models to implement their
specific field extensions.
"""

from typing import Dict, Any, Optional, Type

from pynamodb.attributes import MapAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute

from pydantic import Field

from ..models import DatabaseTable, DatabaseRecord


class ParentCreatedAtIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying items by parent PRN and creation date.

    This index allows efficient querying of child items by their parent PRN
    and ordering by creation timestamp.

    Attributes:
        parent_prn (str): Parent Pipeline Reference Number (PRN) of the item (hash key)
        created_at (datetime): Timestamp of the item creation (range key)
    """

    class Meta:
        index_name = "parent-created_at-index"
        projection = AllProjection()

    parent_prn = UnicodeAttribute(hash_key=True, attr_name="ParentPrn")
    created_at = UTCDateTimeAttribute(range_key=True, attr_name="CreatedAt")


class ItemModel(DatabaseTable):
    """Configuration Management Database (CMDB) model for AWS infrastructure items.

    This model serves as the foundation of a comprehensive Configuration Management Database
    (CMDB) that maintains a complete hierarchical record of all AWS resources provisioned
    for clients. The database enables full traceability from individual AWS components
    back to their business context (client, portfolio, application, branch, and build).

    The CMDB maintains a strict hierarchical structure that mirrors the business and
    technical organization of infrastructure deployments:

    1. **Client** - Top-level tenant organization
    2. **Portfolio** - Business application or service grouping within a client
    3. **App** - Functional component or module within a portfolio
    4. **Branch** - Version control branch representing different development streams
    5. **Build** - Specific infrastructure deployment instance with unique pipeline
       reference number
    6. **Component** - Individual AWS resources deployed as part of the build

    Attributes:
        prn (str): Pipeline Reference Number (PRN) of the item (primary key).
            Unique identifier that encodes the item's position in the business hierarchy.
            Format varies by item type but always includes full hierarchical path.
        parent_prn (str): Parent Pipeline Reference Number (PRN) of the item.
            References the immediate parent in the hierarchy. Root items use "prn" as their parent_prn.
        item_type (str): Type classification of the item in the hierarchy.
            Valid values: "client", "portfolio", "app", "branch", "build", "component".
            Determines the expected PRN format and allowed child types.
        name (str): Human-readable name of the item for display and identification purposes.
            Should be descriptive and meaningful to business users and operators.
        created_at (datetime): Timestamp when the item was first created in the CMDB (auto-generated).
            Used for audit trails, reporting, and temporal queries.
            Set automatically on item creation and never modified.
        updated_at (datetime): Timestamp when the item was last modified in the CMDB (auto-updated).
            Updated automatically on every save() or update() operation.
            Used for change tracking and data freshness validation.
        parent_created_at_index (ParentCreatedAtIndex): Global Secondary Index enabling efficient queries
            by parent PRN and creation date.

    Note:
        **AWS Resource Traceability**: When AWS components are deployed, they may not always have
        complete tagging due to service limitations, human error, legacy resources, or cost optimization.
        This CMDB solves the traceability problem by maintaining a complete record that enables:

        - **Forward Lookup**: Find AWS resources deployed in a specific build
        - **Reverse Lookup**: Identify which client/portfolio/app a resource belongs to
        - **Impact Analysis**: Determine which applications will be affected by changes
        - **Compliance Reporting**: Generate complete resource inventories by client
        - **Cost Attribution**: Track AWS costs by portfolio or application

        **Pipeline Reference Numbers (PRNs)**: Each item is identified by a Pipeline Reference Number
        that encodes the hierarchical relationship and ensures global uniqueness. PRNs always begin
        with "prn:" just like AWS ARNs always begin with "arn:":

        - Portfolio PRN: "prn:core"
        - App PRN: "prn:core:api"
        - Branch PRN: "prn:core:api:master"
        - Build PRN: "prn:core:api:master:1234"
        - Component PRN: "prn:core:api:master:1234:auth-lambda-handler"
    """

    class Meta(DatabaseTable.Meta):
        """Meta class for ItemModel DynamoDB table configuration.

        Inherits configuration from DatabaseTable.Meta including table naming,
        region settings, and billing mode.
        """

        pass

    # Hash key is the parent prn.  For a portfolio, which has the name 'prn:my-portoolio', the parent_prn is 'prn'
    parent_prn = UnicodeAttribute(hash_key=True, null=False, attr_name="ParentPrn")

    # Range key is the prn.  There are many prn's for each parent prn (i.e. a range of prns)
    # for the portfolio 'prn:my-portfolio', the prn is 'prn:my-portfolio'

    prn = UnicodeAttribute(range_key=True, null=False, attr_name="Prn")

    # for the portfolio 'prn:my-portfolio', the name is 'my-portfolio'
    name = UnicodeAttribute(null=False, attr_name="Name")

    # for the portfolio 'prn:my-portfolio', the item_type is 'portfolio'
    item_type = UnicodeAttribute(null=False, attr_name="ItemType")

    # Any optional metadata for the item
    metadata = MapAttribute(null=True, attr_name="Metadata")

    # Indexes
    parent_created_at_index = ParentCreatedAtIndex()

    def __repr__(self) -> str:
        """Return string representation of the ItemModel.

        Returns:
            str: String representation showing key fields
        """
        return f"<Item(prn={self.prn},type={self.item_type},name={self.name})>"


ItemModelType = Type[ItemModel]


class ItemModelRecord(DatabaseRecord):
    """Pydantic model for Items with validation and serialization.

    Provides type validation, PascalCase serialization for APIs,
    and conversion methods between PynamoDB and API formats.

    Inherits audit fields (created_at, updated_at) from DatabaseRecord.
    Represents items in the Configuration Management Database (CMDB)
    including portfolios, apps, branches, builds, and components.

    Attributes:
        prn (str): Pipeline Reference Number (PRN) of the item (primary key)
        parent_prn (str): Parent Pipeline Reference Number (PRN) of the item
        item_type (str): Type classification of the item in the hierarchy
        name (str): Human-readable name of the item for display and identification
    """

    # hash_key
    parent_prn: str = Field(
        ...,
        alias="ParentPrn",
        description="Parent Pipeline Reference Number (PRN) of the item",
    )

    # range_key
    prn: str = Field(
        ...,
        alias="Prn",
        description="Pipeline Reference Number (PRN) of the item (primary key)",
    )

    name: str = Field(
        ...,
        alias="Name",
        description="Human-readable name of the item for display and identification",
    )
    item_type: str = Field(
        None,
        alias="ItemType",
        description="Type classification of the item in the hierarchy",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        alias="Metadata",
        description="Optional metadata dictionary for additional item attributes",
    )

    @classmethod
    def get_parent_prn(cls, prn: str) -> str:
        """Extract the parent PRN from a given item PRN.

        Args:
            prn (str): The full Pipeline Reference Number (PRN) of the item.

        Returns:
            str: The parent PRN extracted from the item PRN.
        """
        return prn[0 : prn.rindex(":")] if ":" in prn else prn

    @classmethod
    def model_class(cls, client: str) -> ItemModelType:
        """You need to override this"""
        raise NotImplementedError(
            f"You must implement the model_class method in {cls.__name__} to return the PynamoDB model class."
        )

    @classmethod
    def to_model(cls, client: str) -> ItemModel:
        """You need to override this"""
        raise NotImplementedError(
            f"You must implement the to_model method in {cls.__name__} to convert the record to a PynamoDB model instance."
        )

    def from_model(self, model: ItemModel) -> "ItemModelRecord":
        """You need to override this"""
        raise NotImplementedError(
            f"You must implement the from_model method in {self.__class__.__name__} to convert a PynamoDB model instance to a record."
        )

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to ensure snake_case serialization for PynamoDB compatibility.

        For ItemRecords in the items table, we use snake_case field names in the API by default.
        Even though the PynamoDB model uses PascalCase to store them.

        Args:
            **kwargs: Additional parameters for model_dump

        Returns:
            Dict[str, Any]: Dictionary with snake_case field names
        """
        kwargs.setdefault("by_alias", False)
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def __repr__(self) -> str:
        """Return a string representation of the ItemModelRecord instance.

        Returns:
            str: String representation for debugging
        """
        return f"<ItemRecord(prn={self.prn},type={self.item_type},name={self.name})>"


ItemModelRecordType = Type[ItemModelRecord]
