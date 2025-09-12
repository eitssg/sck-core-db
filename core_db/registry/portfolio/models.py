"""Definition of the Portfolio Facts in the core-automation-portfolios table"""

from typing import Dict, Optional, List, Type
from pydantic import Field, ConfigDict, BaseModel
from pynamodb.attributes import (
    UnicodeAttribute,
    BooleanAttribute,
    NumberAttribute,
    MapAttribute,
    ListAttribute,
)

from ...constants import PORTFOLIO_KEY
from ...models import TableFactory, DatabaseRecord, DatabaseTable, EnhancedMapAttribute


class ContactFacts(EnhancedMapAttribute):
    """Contact details for a portfolio.

    This model represents contact information for individuals associated with a portfolio.

    Attributes:
        name (str): Name of the contact
        email (str, optional): Email address of the contact
        attributes (dict, optional): Additional attributes for the contact
        enabled (bool): Is the contact enabled. Default is True
        user_instantiated (str, optional): Internal PynamoDB field indicating user instantiation

    Examples:
        >>> # Both formats work identically (thanks to ExtendedMapAttribute)
        >>> contact1 = ContactFacts(
        ...     name="John Doe",
        ...     email="john@acme.com",
        ...     enabled=True
        ... )

        >>> contact2 = ContactFacts(
        ...     Name="John Doe",
        ...     Email="john@acme.com",
        ...     Enabled=True
        ... )
    """

    name = UnicodeAttribute(attr_name="Name")
    email = UnicodeAttribute(null=True, attr_name="Email")
    attributes = MapAttribute(null=True, attr_name="Attributes")
    enabled = BooleanAttribute(default=True, attr_name="Enabled")


class ApproverFacts(EnhancedMapAttribute):
    """Approver details for a portfolio.

    This model represents approval workflow information for portfolio operations.

    Attributes:
        sequence (int): Sequence number of the approver. Default is 1. Used to order approvers
        name (str): Name of the approver
        email (str, optional): Email address of the approver
        roles (list[str], optional): List of roles for the approver. This approver can approve only specified roles
        attributes (dict, optional): Additional attributes for the approver
        depends_on (list[int], optional): List of sequence numbers of approvers that this approver depends on
        enabled (bool): Is the approver enabled. Default is True
        user_instantiated (str, optional): Internal PynamoDB field indicating user instantiation

    Examples:
        >>> # Both formats work identically
        >>> approver1 = ApproverFacts(
        ...     sequence=1,
        ...     name="Manager",
        ...     email="mgr@acme.com",
        ...     roles=["deployment", "approval"],
        ...     enabled=True
        ... )

        >>> approver2 = ApproverFacts(
        ...     Sequence=2,
        ...     Name="Director",
        ...     Email="dir@acme.com",
        ...     DependsOn=[1],
        ...     Enabled=True
        ... )
    """

    sequence = NumberAttribute(default=1, attr_name="Sequence")
    name = UnicodeAttribute(attr_name="Name")
    email = UnicodeAttribute(null=True, attr_name="Email")
    roles = ListAttribute(of=UnicodeAttribute, null=True, attr_name="Roles")
    attributes = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Attributes")
    depends_on = ListAttribute(of=NumberAttribute, null=True, attr_name="DependsOn")
    enabled = BooleanAttribute(default=True, attr_name="Enabled")


class OwnerFacts(EnhancedMapAttribute):
    """Owner details for a portfolio.

    This model represents ownership information for a portfolio.

    Attributes:
        name (str): Name of the owner
        email (str, optional): Email address of the owner
        phone (str, optional): Phone number of the owner
        attributes (dict, optional): Additional attributes for the owner
        user_instantiated (str, optional): Internal PynamoDB field indicating user instantiation

    Examples:
        >>> # Both formats work identically
        >>> owner1 = OwnerFacts(
        ...     name="John Smith",
        ...     email="john.smith@acme.com",
        ...     phone="+1-555-0123"
        ... )

        >>> owner2 = OwnerFacts(
        ...     Name="John Smith",
        ...     Email="john.smith@acme.com",
        ...     Phone="+1-555-0123"
        ... )
    """

    name = UnicodeAttribute(attr_name="Name")
    email = UnicodeAttribute(null=True, attr_name="Email")
    phone = UnicodeAttribute(null=True, attr_name="Phone")
    attributes = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Attributes")


class ProjectFacts(EnhancedMapAttribute):
    """Project details for a portfolio.

    This model represents project or business application information.

    Attributes:
        name (str): Name of the project
        code (str): Code of the project
        repository (str, optional): Git repository of the project
        description (str, optional): Description of the project
        attributes (dict, optional): Additional attributes for the project
        user_instantiated (str, optional): Internal PynamoDB field indicating user instantiation

    Examples:
        >>> # Both formats work identically
        >>> project1 = ProjectFacts(
        ...     name="Web Services API",
        ...     code="web-api",
        ...     repository="https://github.com/acme/web-api",
        ...     description="Core web services API"
        ... )

        >>> project2 = ProjectFacts(
        ...     Name="Web Services API",
        ...     Code="web-api",
        ...     Repository="https://github.com/acme/web-api",
        ...     Description="Core web services API"
        ... )
    """

    name = UnicodeAttribute(attr_name="Name")
    code = UnicodeAttribute(attr_name="Code")
    repository = UnicodeAttribute(null=True, attr_name="Repository")
    description = UnicodeAttribute(null=True, attr_name="Description")
    attributes = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Attributes")


class PortfolioFactsModel(DatabaseTable):
    """Portfolio facts model for client-specific portfolio registry tables.

    This model represents a complete portfolio configuration including contacts, approvers,
    project details, and metadata for deployment automation. PortfolioFactsModel stores
    organizational and configuration data for portfolio-level operations.

    Attributes:
        client (str): Client identifier (hash key)
            Example: "acme", "enterprise", "startup"
        portfolio (str): Portfolio identifier (range key)
            Example: "web-services", "mobile-app", "analytics"
        contacts (list[ContactFacts], optional): List of contact details for the portfolio
        approvers (list[ApproverFacts], optional): List of approver details for approval workflows
        project (ProjectFacts, optional): Primary project details for the portfolio
        domain (str, optional): Domain name or identifier for the portfolio
            Example: "webservices.acme.com", "api.enterprise.com"
        bizapp (ProjectFacts, optional): Business application details, alternative to project
        owner (OwnerFacts, optional): Owner details for the portfolio
        tags (dict, optional): Tags for deployment resources
            Example: {"Environment": "production", "Team": "platform"}
        metadata (dict, optional): Additional metadata for the portfolio
        attributes (dict, optional): Custom attributes for the portfolio
        user_instantiated (str, optional): Internal PynamoDB field indicating user instantiation

    Note:
        **Portfolio Structure**: Portfolios are the top-level organizational units that contain
        multiple applications. They define:

        - **Ownership and Contacts**: Who owns and manages the portfolio
        - **Approval Workflows**: Who can approve deployments and changes
        - **Project Information**: Business context and repository details
        - **Domain Configuration**: DNS and networking settings
        - **Tagging Strategy**: Resource organization and cost allocation

        **Approval Workflows**: The approvers list supports complex approval chains:

        - **Sequence**: Order of approval (1, 2, 3...)
        - **Dependencies**: Approver 2 can depend on approver 1 completing first
        - **Role-based**: Approvers can be limited to specific roles/operations
        - **Parallel/Sequential**: Mix of parallel and sequential approval steps

        **Domain Integration**: Domain field integrates with:

        - **DNS Management**: Automatic Route53 hosted zone creation
        - **SSL Certificates**: ACM certificate provisioning
        - **Load Balancer Configuration**: ALB/NLB domain association
        - **CDN Setup**: CloudFront distribution configuration

        **Factory Pattern**: PortfolioFactsModel uses client-specific tables:

        - **Client "acme"**: Table "acme-core-automation-portfolios"
        - **Client "enterprise"**: Table "enterprise-core-automation-portfolios"
        - **Isolation**: Each client's data is completely separated

        The hierarchy is: Portfolio -> App -> Branch -> Build -> Component

    Examples:
        >>> # Both formats work identically (thanks to DatabaseTable)
        >>> # Snake case (Python style)
        >>> portfolio1 = PortfolioFactsModel(
        ...     client="acme",
        ...     portfolio="web-services",
        ...     domain="webservices.acme.com",
        ...     owner={"name": "John Doe", "email": "john@acme.com"},
        ...     tags={"Environment": "production", "Team": "platform"}
        ... )

        >>> # PascalCase (DynamoDB style)
        >>> portfolio2 = PortfolioFactsModel(
        ...     Client="acme",
        ...     Portfolio="web-services",
        ...     Domain="webservices.acme.com",
        ...     Owner={"Name": "John Doe", "Email": "john@acme.com"},
        ...     Tags={"Environment": "production", "Team": "platform"}
        ... )

        >>> # Portfolio with approval workflow
        >>> enterprise_portfolio = PortfolioFactsModel(
        ...     client="enterprise",
        ...     portfolio="core-platform",
        ...     contacts=[
        ...         {"name": "Tech Lead", "email": "lead@enterprise.com"},
        ...         {"name": "Product Manager", "email": "pm@enterprise.com"}
        ...     ],
        ...     approvers=[
        ...         {"sequence": 1, "name": "Manager", "email": "mgr@enterprise.com"},
        ...         {"sequence": 2, "name": "Director", "email": "dir@enterprise.com", "depends_on": [1]}
        ...     ],
        ...     project={"name": "Core Platform", "code": "core", "repository": "https://github.com/enterprise/core"}
        ... )
    """

    class Meta(DatabaseTable.Meta):
        """Meta class for PortfolioFactsModel DynamoDB table configuration.

        Inherits configuration from DatabaseTable.Meta including table naming,
        region settings, and billing mode.
        """

        pass

    # Composite primary key
    portfolio = UnicodeAttribute(hash_key=True, attr_name=PORTFOLIO_KEY)

    name = UnicodeAttribute(null=True, attr_name="Name")

    # Portfolio configuration
    contacts = ListAttribute(of=ContactFacts, null=True, attr_name="Contacts")
    approvers = ListAttribute(of=ApproverFacts, null=True, attr_name="Approvers")
    project = ProjectFacts(null=True, attr_name="Project")
    domain = UnicodeAttribute(null=True, attr_name="Domain")
    bizapp = ProjectFacts(null=True, attr_name="Bizapp")
    owner = OwnerFacts(null=True, attr_name="Owner")

    # Metadata and attributes
    tags = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Tags")
    metadata = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Metadata")
    attributes = MapAttribute(of=UnicodeAttribute, null=True, attr_name="Attributes")
    user_instantiated = UnicodeAttribute(null=True, attr_name="UserInstantiated")

    def __repr__(self) -> str:
        """Return string representation of PortfolioFactsModel.

        Returns:
            str: String representation showing client and portfolio identifiers

        Examples:
            >>> portfolio = PortfolioFactsModel(client="acme", portfolio="web-services")
            >>> repr(portfolio)
            '<PortfolioFactsModel(client=acme,portfolio=web-services)>'
        """
        return f"<PortfolioFactsModel(client={self.client},portfolio={self.portfolio})>"


PortfolioFactsType = Type[PortfolioFactsModel]


class PortfolioFactsFactory:
    """Factory class for creating client-specific PortfolioFactsModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for PortfolioFactsModel.

    Examples:
        >>> # Get client-specific model
        >>> client_model = PortfolioFactsFactory.get_model("acme")

        >>> # Create table for client
        >>> PortfolioFactsFactory.create_table("acme", wait=True)

        >>> # Check if table exists
        >>> exists = PortfolioFactsFactory.exists("acme")

        >>> # Delete table
        >>> PortfolioFactsFactory.delete_table("acme", wait=True)
    """

    @classmethod
    def get_model(cls, client_name: str) -> PortfolioFactsType:
        """Get the PortfolioFactsModel model for the given client.

        Args:
            client_name (str): The name of the client

        Returns:
            PortfolioFactsType: The PortfolioFactsModel model for the given client

        Examples:
            >>> model_class = PortfolioFactsFactory.get_model("acme")
            >>> portfolio = model_class(client="acme", portfolio="web-services")
        """
        return TableFactory.get_model(PortfolioFactsModel, client=client_name)

    @classmethod
    def create_table(cls, client_name: str, wait: bool = True) -> bool:
        """Create the PortfolioFactsModel table for the given client.

        Args:
            client_name (str): The name of the client
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists

        Examples:
            >>> PortfolioFactsFactory.create_table("acme", wait=True)
            True
        """
        return TableFactory.create_table(PortfolioFactsModel, client_name, wait=wait)

    @classmethod
    def delete_table(cls, client_name: str, wait: bool = True) -> bool:
        """Delete the PortfolioFactsModel table for the given client.

        Args:
            client_name (str): The name of the client
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist

        Examples:
            >>> PortfolioFactsFactory.delete_table("acme", wait=True)
            True
        """
        return TableFactory.delete_table(PortfolioFactsModel, client_name, wait=wait)

    @classmethod
    def exists(cls, client_name: str) -> bool:
        """Check if the PortfolioFactsModel table exists for the given client.

        Args:
            client_name (str): The name of the client

        Returns:
            bool: True if the table exists, False otherwise

        Examples:
            >>> PortfolioFactsFactory.exists("acme")
            True
        """
        return TableFactory.exists(PortfolioFactsModel, client_name)


# =============================================================================
# Pydantic MapAttribute Models
# =============================================================================


class ContactFactsItem(BaseModel):
    """Pydantic model for ContactFacts MapAttribute.

    Provides validation and serialization for contact information with PascalCase API aliases.

    Attributes:
        name (str): Name of the contact
        email (str, optional): Email address of the contact
        attributes (dict, optional): Additional attributes for the contact
        enabled (bool): Is the contact enabled. Default is True

    Examples:
        >>> contact = ContactFactsItem(
        ...     Name="John Doe",
        ...     Email="john@acme.com",
        ...     Enabled=True
        ... )
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(
        ...,
        alias="Name",
        description="Name of the contact",
    )
    email: Optional[str] = Field(
        None,
        alias="Email",
        description="Email address of the contact",
    )
    attributes: Optional[Dict[str, str]] = Field(
        None,
        alias="Attributes",
        description="Additional attributes for the contact",
    )
    enabled: bool = Field(
        True,
        alias="Enabled",
        description="Is the contact enabled",
    )


class ApproverFactsItem(BaseModel):
    """Pydantic model for ApproverFacts MapAttribute.

    Provides validation and serialization for approver workflow information with PascalCase API aliases.

    Attributes:
        sequence (int): Sequence number of the approver. Default is 1
        name (str): Name of the approver
        email (str, optional): Email address of the approver
        roles (list[str], optional): List of roles for the approver
        attributes (dict, optional): Additional attributes for the approver
        depends_on (list[int], optional): List of sequence numbers of approvers that this approver depends on
        enabled (bool): Is the approver enabled. Default is True

    Examples:
        >>> approver = ApproverFactsItem(
        ...     Sequence=1,
        ...     Name="Manager",
        ...     Email="mgr@acme.com",
        ...     Roles=["deployment", "approval"]
        ... )
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    sequence: int = Field(
        1,
        alias="Sequence",
        description="Sequence number of the approver",
    )
    name: str = Field(
        ...,
        alias="Name",
        description="Name of the approver",
    )
    email: Optional[str] = Field(
        None,
        alias="Email",
        description="Email address of the approver",
    )
    roles: Optional[List[str]] = Field(
        None,
        alias="Roles",
        description="List of roles for the approver",
    )
    attributes: Optional[Dict[str, str]] = Field(
        None,
        alias="Attributes",
        description="Additional attributes for the approver",
    )
    depends_on: Optional[List[int]] = Field(
        None,
        alias="DependsOn",
        description="List of sequence numbers of approvers that this approver depends on",
    )
    enabled: bool = Field(
        True,
        alias="Enabled",
        description="Is the approver enabled",
    )


class OwnerFactsItem(BaseModel):
    """Pydantic model for OwnerFacts MapAttribute.

    Provides validation and serialization for portfolio ownership information with PascalCase API aliases.

    Attributes:
        name (str): Name of the owner
        email (str, optional): Email address of the owner
        phone (str, optional): Phone number of the owner
        attributes (dict, optional): Additional attributes for the owner

    Examples:
        >>> owner = OwnerFactsItem(
        ...     Name="John Smith",
        ...     Email="john.smith@acme.com",
        ...     Phone="+1-555-0123"
        ... )
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(
        ...,
        alias="Name",
        description="Name of the owner",
    )
    email: Optional[str] = Field(
        None,
        alias="Email",
        description="Email address of the owner",
    )
    phone: Optional[str] = Field(
        None,
        alias="Phone",
        description="Phone number of the owner",
    )
    attributes: Optional[Dict[str, str]] = Field(
        None,
        alias="Attributes",
        description="Additional attributes for the owner",
    )


class ProjectFactsItem(BaseModel):
    """Pydantic model for ProjectFacts MapAttribute.

    Provides validation and serialization for project information with PascalCase API aliases.

    Attributes:
        name (str): Name of the project
        code (str): Code of the project
        repository (str, optional): Git repository of the project
        description (str, optional): Description of the project
        attributes (dict, optional): Additional attributes for the project

    Examples:
        >>> project = ProjectFactsItem(
        ...     Name="Web Services API",
        ...     Code="web-api",
        ...     Repository="https://github.com/acme/web-api"
        ... )
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(
        ...,
        alias="Name",
        description="Name of the project",
    )
    code: str = Field(
        ...,
        alias="Code",
        description="Code of the project",
    )
    repository: Optional[str] = Field(
        None,
        alias="Repository",
        description="Git repository of the project",
    )
    description: Optional[str] = Field(
        None,
        alias="Description",
        description="Description of the project",
    )
    attributes: Optional[Dict[str, str]] = Field(
        None,
        alias="Attributes",
        description="Additional attributes for the project",
    )


# =============================================================================
# Main Pydantic Model
# =============================================================================


class PortfolioFact(DatabaseRecord):
    """Pydantic model for Portfolio Facts with validation and serialization.

    Extends DatabaseRecord with portfolio-specific fields including contacts, approvers,
    project details, and metadata. Provides type validation, PascalCase serialization
    for APIs, and conversion methods between PynamoDB and API formats.

    Inherits audit fields (created_at, updated_at) from DatabaseRecord.

    Attributes:
        portfolio (str): Portfolio identifier (unique portfolio name within client namespace)
        contacts (list[ContactFactsItem], optional): List of contact details for the portfolio
        approvers (list[ApproverFactsItem], optional): List of approver details for approval workflows
        project (ProjectFactsItem, optional): Primary project details for the portfolio
        domain (str, optional): Domain name or identifier for the portfolio
        bizapp (ProjectFactsItem, optional): Business application details, alternative to project
        owner (OwnerFactsItem, optional): Owner details for the portfolio
        tags (dict, optional): Tags for deployment resources
        metadata (dict, optional): Additional metadata for the portfolio
        attributes (dict, optional): Custom attributes for the portfolio
        user_instantiated (str, optional): Internal field indicating user instantiation

        Inherited from DatabaseRecord:
            created_at (datetime): Timestamp when the record was first created (auto-generated)
            updated_at (datetime): Timestamp when the record was last modified (auto-updated)

    Note:
        All string fields use PascalCase aliases for API compatibility and DynamoDB attribute naming.
        The portfolio field serves as the hash key for DynamoDB operations when combined with
        client context from the table factory.

    Examples:
        >>> # Create portfolio fact with validation
        >>> portfolio = PortfolioFact(
        ...     Portfolio="web-services",
        ...     Domain="webservices.acme.com",
        ...     Owner={"Name": "John Doe", "Email": "john@acme.com"}
        ... )

        >>> # Create with minimal required fields
        >>> minimal_portfolio = PortfolioFact(
        ...     Portfolio="mobile-app"
        ... )

        >>> # Convert from DynamoDB model
        >>> db_portfolio = PortfolioFactsModel(portfolio="web-services")
        >>> pydantic_portfolio = PortfolioFact.from_model(db_portfolio)

    """

    portfolio: str = Field(
        ...,
        alias="Portfolio",
        description="Portfolio identifier (unique portfolio name within client namespace)",
    )
    name: Optional[str] = Field(
        None,
        alias="Name",
        description="Optional descriptive name for the portfolio",
    )

    # Portfolio Configuration Fields
    contacts: Optional[List[ContactFactsItem]] = Field(
        None,
        alias="Contacts",
        description="List of contact details for the portfolio",
    )
    approvers: Optional[List[ApproverFactsItem]] = Field(
        None,
        alias="Approvers",
        description="List of approver details for approval workflows",
    )
    project: Optional[ProjectFactsItem] = Field(
        None,
        alias="Project",
        description="Primary project details for the portfolio",
    )
    domain: Optional[str] = Field(
        None,
        alias="Domain",
        description="Domain name or identifier for the portfolio",
    )
    bizapp: Optional[ProjectFactsItem] = Field(
        None,
        alias="Bizapp",
        description="Business application details, alternative to project",
    )
    owner: Optional[OwnerFactsItem] = Field(
        None,
        alias="Owner",
        description="Owner details for the portfolio",
    )

    # Metadata Fields
    tags: Optional[Dict[str, str]] = Field(
        None,
        alias="Tags",
        description="Tags for deployment resources",
    )
    metadata: Optional[Dict[str, str]] = Field(
        None,
        alias="Metadata",
        description="Additional metadata for the portfolio",
    )
    attributes: Optional[Dict[str, str]] = Field(
        None,
        alias="Attributes",
        description="Custom attributes for the portfolio",
    )
    user_instantiated: Optional[str] = Field(
        None,
        alias="UserInstantiated",
        description="Internal field indicating user instantiation",
    )

    @classmethod
    def model_class(cls, client: str) -> PortfolioFactsType:
        """Get the PynamoDB model class for this Pydantic model.

        Args:
            client (str): Client name for table selection

        Returns:
            PortfolioFactsType: Client-specific PynamoDB PortfolioFactsModel class

        Examples:
            >>> model_class = PortfolioFact.model_class("acme")
            >>> portfolio = model_class(client="acme", portfolio="web-services")
        """
        return PortfolioFactsFactory.get_model(client)

    @classmethod
    def from_model(cls, model: PortfolioFactsModel) -> "PortfolioFact":
        """Convert PynamoDB PortfolioFactsModel to Pydantic PortfolioFact.

        Args:
            portfolio_model (PortfolioFactsModel): PynamoDB PortfolioFactsModel instance

        Returns:
            PortfolioFact: Pydantic PortfolioFact instance

        Examples:
            >>> db_portfolio = PortfolioFactsModel(portfolio="web-services")
            >>> pydantic_portfolio = PortfolioFact.from_model(db_portfolio)
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> PortfolioFactsModel:
        """Convert Pydantic PortfolioFact to PynamoDB PortfolioFactsModel instance.

        Args:
            client (str): Client identifier for table isolation (used for factory)

        Returns:
            PortfolioFactsModel: PynamoDB PortfolioFactsModel instance ready for database operations

        Examples:
            >>> portfolio_fact = PortfolioFact(Portfolio="web-services")
            >>> db_model = portfolio_fact.to_model("acme")
            >>> db_model.save()
        """
        model_class = PortfolioFactsFactory.get_model(client)
        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    def __repr__(self) -> str:
        """String representation for debugging.

        Returns:
            str: String representation of the portfolio fact

        Examples:
            >>> portfolio = PortfolioFact(Portfolio="web-services")
            >>> repr(portfolio)
            '<PortfolioFact(portfolio=web-services)>'
        """
        return f"<PortfolioFact(portfolio={self.portfolio})>"
