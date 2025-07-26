"""Defines the generic model for items stored in the core-automation-items table.

This will be subclassed by portfolio, app, branch, build, component models to implement their
specific field extensions.
"""

from dateutil import parser
from typing import Type, Optional

from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute

import core_framework as util

from core_framework.time_utils import make_default_time

from ..constants import ITEMS
from ..config import get_table_name


class ParentCreatedAtIndexMeta:
    """Meta configuration for the parent-created_at GSI."""

    index_name = "parent-created_at-index"
    projection = AllProjection()
    read_capacity_units = 1
    write_capacity_units = 1


class ParentCreatedAtIndex(GlobalSecondaryIndex):
    """
    Global Secondary Index for querying items by parent PRN and creation date.

    This index allows efficient querying of child items by their parent PRN
    and ordering by creation timestamp.

    Attributes
    ----------
    parent_prn : str
        Parent Pipeline Reference Number (PRN) of the item (hash key)
    created_at : datetime
        Timestamp of the item creation (range key)
    """

    class Meta(ParentCreatedAtIndexMeta):
        pass

    parent_prn = UnicodeAttribute(hash_key=True)
    """str: Parent Pipeline Reference Number (PRN) of the item (a.k.a identity)"""

    created_at = UTCDateTimeAttribute(range_key=True)
    """datetime: Timestamp of the item creation. Let the system auto-generate. This is a RANGE key for the index."""


class ItemModel(Model):
    """
    Configuration Management Database (CMDB) model for AWS infrastructure items.

    This model serves as the foundation of a comprehensive Configuration Management Database
    (CMDB) that maintains a complete hierarchical record of all AWS resources provisioned
    for clients. The database enables full traceability from individual AWS components
    back to their business context (client, portfolio, application, branch, and build).

    Business Hierarchy & Purpose
    ----------------------------
    The CMDB maintains a strict hierarchical structure that mirrors the business and
    technical organization of infrastructure deployments:

    1. **Client** - Top-level tenant organization (e.g., "acme", "eits")
    2. **Portfolio** - Business application or service grouping within a client
       (e.g., "core", "web-services", "analytics")
    3. **App** - Functional component or module within a portfolio
       (e.g., "api", "frontend", "database", "analytics-engine")
    4. **Branch** - Version control branch representing different development streams
       (e.g., "master", "develop", "feature/new-auth", "release/v2.1")
    5. **Build** - Specific infrastructure deployment instance with unique pipeline
       reference number (e.g., "build-1234", "v1.2.3-build-5678")
    6. **Component** - Individual AWS resources deployed as part of the build
       (e.g., Lambda functions, S3 buckets, DynamoDB tables, EC2 instances)

    AWS Resource Traceability
    -------------------------
    When AWS components are deployed, they may not always have complete tagging due to:
    - Service limitations on tag support
    - Human error in tag application
    - Legacy resources without proper tagging
    - Cost optimization (tag limits)

    This CMDB solves the traceability problem by maintaining a complete record that enables:

    **Forward Lookup**: "What AWS resources were deployed in build-1234?"
    **Reverse Lookup**: "Which client/portfolio/app does this Lambda function belong to?"
    **Impact Analysis**: "If I modify this S3 bucket, what applications will be affected?"
    **Compliance Reporting**: "Show me all resources for client 'acme' in production"
    **Cost Attribution**: "What are the AWS costs for portfolio 'web-services'?"

    Pipeline Reference Numbers (PRNs)
    ---------------------------------
    Each item is identified by a Pipeline Reference Number (PRN) that encodes the
    hierarchical relationship and ensures global uniqueness. PRNs always begin
    with "prn:" just like AWS ARNs always begin with "arn:":

    - Portfolio PRN: ``"prn:core"``
      within the client 'acme', the prn for a portfolio is prn:<portfolio> or simply "prn:core"
    - App PRN: ``"prn:core:api"``
      within the client 'acme', the prn for an app is prn:<portfolio>:<app> or simply "prn:core:api"
    - Branch PRN: ``"prncore:api:master"``
      within the client 'acme', the prn for a branch is prn:<portfolio>:<app>:<branch> or simply "prn:core:api:master"
    - Build PRN: ``"prn:core:api:master:1234"``
      within the client 'acme', the prn for a build is prn:<portfolio>:<app>:<branch>:<build> or simply "prn:core:api:master:1234"
    - Component PRN: ``"prn:core:api:master:1234:auth-lambda-handler"``
      within the client 'acme', the prn for a component is prn:<portfolio>:<app>:<branch>:<build>:<component> or simply "prn:core:api:master:1234:auth-lambda-handler"

    Version Management Philosophy
    ----------------------------
    The model supports two deployment strategies:

    **Infrastructure-Centric**: Each infrastructure deployment (build number) contains
    a specific application version. This is the recommended approach as it ensures
    reproducible deployments and clear rollback points.

    **Application-Centric**: Application versions can be updated independently on
    existing infrastructure builds. While supported, this approach can complicate
    rollback scenarios and deployment traceability.

    CMDB Operations & Use Cases
    ---------------------------
    This CMDB enables several critical operational scenarios:

    **Incident Response**:
    - CloudWatch alert fires for Lambda function "auth-handler-prod-xyz"
    - Query CMDB by component name to immediately identify:
      - Client: acme
      - Portfolio: core
      - App: api
      - Branch: master
      - Build: 1234
      - Responsible team and contact information

    **Security Compliance**:
    - Audit requires list of all resources for client "acme"
    - Query CMDB for all components where client="acme"
    - Generate complete inventory with business context

    **Change Management**:
    - Need to update shared S3 bucket used by multiple apps
    - Query CMDB to find all components using the bucket
    - Identify affected portfolios and applications
    - Plan coordinated deployment strategy

    **Cost Optimization**:
    - Identify resources by portfolio for cost allocation
    - Find unused resources by querying build deployment dates
    - Analyze resource utilization patterns by app or branch

    Data Consistency & Integrity
    ----------------------------
    The model ensures data consistency through:

    - **Hierarchical Validation**: PRNs must follow the defined hierarchy
    - **Referential Integrity**: Child items must reference valid parent PRNs
    - **Temporal Tracking**: All items track creation and modification timestamps
    - **Immutable History**: Once created, the hierarchical relationships are preserved

    Attributes
    ----------
    prn : str
        Pipeline Reference Number (PRN) of the item (primary key).
        Unique identifier that encodes the item's position in the business hierarchy.
        Format varies by item type but always includes full hierarchical path.
    parent_prn : str
        Parent Pipeline Reference Number (PRN) of the item.
        References the immediate parent in the hierarchy (e.g., app PRN for a branch item).
        Root items (clients) use "prn" as their parent_prn.
    item_type : str
        Type classification of the item in the hierarchy.
        Valid values: "client", "portfolio", "app", "branch", "build", "component".
        Determines the expected PRN format and allowed child types.
    name : str
        Human-readable name of the item for display and identification purposes.
        Should be descriptive and meaningful to business users and operators.
        Examples: "Core API", "Authentication Service", "Production Build 1234"
    created_at : datetime
        Timestamp when the item was first created in the CMDB (auto-generated).
        Used for audit trails, reporting, and temporal queries.
        Set automatically on item creation and never modified.
    updated_at : datetime
        Timestamp when the item was last modified in the CMDB (auto-updated).
        Updated automatically on every save() or update() operation.
        Used for change tracking and data freshness validation.

    Indexes
    -------
    parent_created_at_index : ParentCreatedAtIndex
        Global Secondary Index enabling efficient queries by parent PRN and creation date.
        Supports use cases like "show all apps in portfolio X ordered by creation date"
        or "find components deployed in the last 24 hours for build Y".

    References
    ----------
    * :class:`core_db.item.portfolio.models.PortfolioModel` - Portfolio-specific extensions
    * :class:`core_db.item.app.models.AppModel` - Application-specific extensions
    * :class:`core_db.item.branch.models.BranchModel` - Branch-specific extensions
    * :class:`core_db.item.build.models.BuildModel` - Build-specific extensions
    * :class:`core_db.item.component.models.ComponentModel` - AWS component-specific extensions

    Examples
    --------
    Creating a complete deployment hierarchy:

    >>> # Create portfolio
    >>> portfolio = ItemModel(
    ...     prn="prn:portfolio:acme:core",
    ...     parent_prn="prn:client:acme",
    ...     item_type="portfolio",
    ...     name="Core Services Portfolio"
    ... )
    >>> portfolio.save()

    >>> # Create app within portfolio
    >>> app = ItemModel(
    ...     prn="prn:app:acme:core:api",
    ...     parent_prn="prn:portfolio:acme:core",
    ...     item_type="app",
    ...     name="Authentication API"
    ... )
    >>> app.save()

    >>> # Create AWS component for specific build
    >>> component = ItemModel(
    ...     prn="prn:acme:core:api:master:1234:lambda:auth-handler",
    ...     parent_prn="prn:acme:core:api:master:1234",
    ...     item_type="component",
    ...     name="Lambda: Authentication Handler"
    ... )
    >>> component.save()

    Querying for operational scenarios:

    >>> # Find all components for a specific build (forward lookup)
    >>> build_prn = "prn:build:acme:core:api:master:1234"
    >>> components = list(ItemModel.parent_created_at_index.query(build_prn))

    >>> # Find all items in a portfolio ordered by creation date
    >>> portfolio_prn = "prn:acme:core"
    >>> apps = list(ItemModel.parent_created_at_index.query(
    ...     portfolio_prn,
    ...     ItemModel.created_at.between(start_date, end_date)
    ... ))

    >>> # Reverse lookup: find parent context for a component
    >>> component = ItemModel.get("component:acme:core:api:master:1234:lambda:auth-handler")
    >>> build = ItemModel.get(component.parent_prn)
    >>> # Continue traversing up the hierarchy as needed

    Notes
    -----
    **Performance Considerations**:
    - Use the parent_created_at_index for hierarchical queries
    - Consider pagination for large result sets
    - Cache frequently accessed parent relationship data

    **Data Modeling Best Practices**:
    - Always populate both prn and parent_prn for referential integrity
    - Use consistent naming conventions for human-readable names
    - Include business context in component names for operational clarity

    **Operational Guidelines**:
    - Regularly validate PRN format consistency
    - Monitor for orphaned records (invalid parent_prn references)
    - Implement automated cleanup for old build/component records
    - Use bulk operations for large deployments to improve performance
    """

    class Meta:
        table_name = get_table_name(ITEMS)
        region = util.get_dynamodb_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    prn = UnicodeAttribute(hash_key=True)
    """str: Pipeline Reference Number (PRN) of the item (a.k.a identity)"""

    parent_prn = UnicodeAttribute(null=False)
    """str: Parent Pipeline Reference Number (PRN) of the item (a.k.a identity)"""

    item_type = UnicodeAttribute(null=False)
    """str: Type of item this event relates to such as portfolio, app, branch, build, component, account, etc."""

    name = UnicodeAttribute(null=False)
    """str: Name of the item. This is the human readable name of the item."""

    created_at = UTCDateTimeAttribute(default_for_new=make_default_time)
    """datetime: Timestamp of the item creation. Let the system auto-generate"""

    updated_at = UTCDateTimeAttribute(default=make_default_time)
    """datetime: Timestamp of the item update. Let the system auto-generate"""

    parent_created_at_index = ParentCreatedAtIndex()
    """GlobalSecondaryIndex: Index for parent_prn and created_at fields. Used for querying items by parent and creation date."""

    def __init__(self, *args, **kwargs):
        """
        Initialize an ItemModel instance.

        Handles string-to-datetime conversion for created_at and updated_at fields
        to support both string and datetime inputs.

        :param args: Positional arguments
        :type args: tuple
        :param kwargs: Keyword arguments including datetime fields
        :type kwargs: dict

        Examples
        --------
        >>> item = ItemModel(
        ...     prn="app:acme:core:api",
        ...     parent_prn="portfolio:acme:core",
        ...     item_type="app",
        ...     name="Authentication API"
        ... )

        With string datetime conversion:

        >>> item = ItemModel(
        ...     prn="app:acme:core:api",
        ...     parent_prn="portfolio:acme:core",
        ...     item_type="app",
        ...     name="Authentication API",
        ...     created_at="2023-01-01T00:00:00Z"
        ... )
        """
        if "created_at" in kwargs and isinstance(kwargs["created_at"], str):
            kwargs["created_at"] = parser.parse(kwargs["created_at"])
        if "updated_at" in kwargs and isinstance(kwargs["updated_at"], str):
            kwargs["updated_at"] = parser.parse(kwargs["updated_at"])
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        """
        Return string representation of the ItemModel.

        :returns: String representation showing key fields
        :rtype: str

        Examples
        --------
        >>> item = ItemModel(prn="app:acme:core:api", parent_prn="portfolio:acme:core", item_type="app", name="API")
        >>> repr(item)
        '<Item(prn=app:acme:core:api,item_type=app,name=API)>'
        """
        return f"<Item(prn={self.prn},item_type={self.item_type},name={self.name})>"

    def save(self, *args, **kwargs):
        """
        Save the item to the database.

        Automatically updates the updated_at timestamp before saving to ensure
        the modification time is accurately tracked.

        :param args: Positional arguments for save
        :type args: tuple
        :param kwargs: Keyword arguments for save
        :type kwargs: dict

        Examples
        --------
        >>> item = ItemModel(prn="app:acme:core:api", parent_prn="portfolio:acme:core", item_type="app", name="API")
        >>> item.save()

        With condition:

        >>> item.save(ItemModel.prn.does_not_exist())
        """
        self.updated_at = make_default_time()
        super(ItemModel, self).save(*args, **kwargs)

    def update(self, actions=None, condition=None, **kwargs):
        """
        Update the item in the database.

        Automatically updates the updated_at timestamp before updating to ensure
        the modification time is accurately tracked.

        :param actions: Update actions to perform
        :type actions: list | None
        :param condition: Condition for the update
        :type condition: Condition | None
        :param kwargs: Additional keyword arguments
        :type kwargs: dict

        Examples
        --------
        >>> item.update(actions=[ItemModel.name.set("New API Name")])

        With condition:

        >>> item.update(
        ...     actions=[ItemModel.name.set("New API Name")],
        ...     condition=ItemModel.item_type.eq("app")
        ... )
        """
        self.updated_at = make_default_time()
        super(ItemModel, self).update(actions=actions, condition=condition, **kwargs)


class ClientItemModel:
    """
    Client-specific ItemModel factory.

    This class provides client-specific table binding for ItemModel instances,
    allowing each client to have their own isolated table while maintaining
    the same model interface.

    :param client: The client name for table binding
    :type client: str

    Examples
    --------
    >>> client_model = ClientItemModel("acme")
    >>> ItemModel = client_model.get_model()
    >>> item = ItemModel(prn="app:acme:core:api", parent_prn="portfolio:acme:core", item_type="app", name="API")
    """

    def __init__(self, client: str):
        """
        Initialize ClientItemModel for a specific client.

        :param client: The client name for table binding
        :type client: str
        """
        self.client = client
        self._configure_model()

    def _configure_model(self):
        """
        Configure the model class for this client.

        Sets the client-specific table name in the ItemModel Meta class.
        """
        # Get the client-specific table name
        table_name = get_table_name(ITEMS, client=self.client)

        # Configure the model's Meta class
        ItemModel.Meta.table_name = table_name

    def get_model(self) -> Type[ItemModel]:
        """
        Get the configured ItemModel class.

        :returns: ItemModel class configured for this client
        :rtype: Type[ItemModel]

        Examples
        --------
        >>> client_model = ClientItemModel("acme")
        >>> ItemModel = client_model.get_model()
        >>> item = ItemModel(prn="app:acme:core:api", parent_prn="portfolio:acme:core", item_type="app", name="API")
        """
        return ItemModel

    def create_table(self, read_capacity_units: int = 1, write_capacity_units: int = 1, wait: bool = False) -> bool:
        """
        Create the table for this client.

        :param read_capacity_units: Read capacity units for the table
        :type read_capacity_units: int
        :param write_capacity_units: Write capacity units for the table
        :type write_capacity_units: int
        :param wait: Whether to wait for table creation to complete
        :type wait: bool
        :returns: True if table was created successfully
        :rtype: bool

        Examples
        --------
        >>> client_model = ClientItemModel("acme")
        >>> client_model.create_table(wait=True)
        """
        return ItemModel.create_table(read_capacity_units=read_capacity_units, write_capacity_units=write_capacity_units, wait=wait)

    def delete_table(self) -> bool:
        """
        Delete the table for this client.

        :returns: True if table was deleted successfully
        :rtype: bool

        Warning
        -------
        This operation is irreversible and will delete all data in the table.

        Examples
        --------
        >>> client_model = ClientItemModel("acme")
        >>> client_model.delete_table()
        """
        return ItemModel.delete_table()

    def table_exists(self) -> bool:
        """
        Check if the table exists for this client.

        :returns: True if table exists, False otherwise
        :rtype: bool

        Examples
        --------
        >>> client_model = ClientItemModel("acme")
        >>> if client_model.table_exists():
        ...     print("Table is ready")
        ... else:
        ...     client_model.create_table(wait=True)
        """
        try:
            return ItemModel.exists()
        except Exception:
            return False


class ItemModelFactory:
    """
    Factory for creating ClientItemModel instances.

    This factory provides a consistent interface for creating client-specific
    ItemModel instances, following the same pattern as other model factories
    in the codebase.

    Examples
    --------
    >>> client_model = ItemModelFactory.get_model("acme")
    >>> ItemModel = client_model.get_model()
    >>> item = ItemModel(prn="app:acme:core:api", parent_prn="portfolio:acme:core", item_type="app", name="API")
    """

    @staticmethod
    def get_model(client: str) -> ClientItemModel:
        """
        Get a ClientItemModel configured for the specified client.

        :param client: The client name
        :type client: str
        :returns: Configured ClientItemModel instance
        :rtype: ClientItemModel

        Examples
        --------
        >>> client_model = ItemModelFactory.get_model("acme")
        >>> ItemModel = client_model.get_model()
        >>> client_model.create_table(wait=True)
        """
        return ClientItemModel(client)
