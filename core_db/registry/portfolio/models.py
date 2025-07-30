"""Definition of the Portfolio Facts in the core-automation-portfolios table"""

from pynamodb.attributes import (
    UnicodeAttribute,
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
)

import core_logging as log

from ...config import get_table_name, PORTFOLIO_FACTS
from ...constants import CLIENT_KEY, PORTFOLIO_KEY

from ..models import RegistryModel, ExtendedMapAttribute


class ContactFacts(ExtendedMapAttribute):
    """
    Contact details for a portfolio.

    This model represents contact information for individuals associated with a portfolio.

    Attributes
    ----------
    Name : str
        Name of the contact.
    Email : str, optional
        Email address of the contact.
    Attributes : dict, optional
        Additional attributes for the contact.
    Enabled : bool
        Is the contact enabled. Default is True.
    """

    Name = UnicodeAttribute()
    Email = UnicodeAttribute(null=True)
    Attributes = MapAttribute(of=UnicodeAttribute, null=True)
    Enabled = BooleanAttribute(default=True)
    UserInstantiated = UnicodeAttribute(null=True)  # Internal PynamoDB field

    def serialize(self, values, *args, **kwargs):
        """
        Serialize the contact facts with default values.

        Parameters
        ----------
        values : dict
            Values to serialize.
        *args
            Additional arguments.
        **kwargs
            Additional keyword arguments.

        Returns
        -------
        dict
            Serialized values with defaults applied.
        """
        # Apply default value for serialization
        if "Enabled" not in values:
            values["Enabled"] = True
        return super().serialize(values, *args, **kwargs)


class ApproverFacts(ExtendedMapAttribute):
    """
    Approver details for a portfolio.

    This model represents approval workflow information for portfolio operations.

    Attributes
    ----------
    Sequence : int
        Sequence number of the approver. Default is 1. Used to order approvers.
    Name : str
        Name of the approver.
    Email : str, optional
        Email address of the approver.
    Roles : list[str], optional
        List of roles for the approver. This approver can approve only specified roles.
    Attributes : dict, optional
        Additional attributes for the approver.
    DependsOn : list[int], optional
        List of sequence numbers of approvers that this approver depends on.
    Enabled : bool
        Is the approver enabled. Default is True.
    """

    Sequence = NumberAttribute(default=1)
    Name = UnicodeAttribute()
    Email = UnicodeAttribute(null=True)
    Roles = ListAttribute(of=UnicodeAttribute, null=True)
    Attributes = MapAttribute(of=UnicodeAttribute, null=True)
    DependsOn = ListAttribute(of=NumberAttribute, null=True)
    Enabled = BooleanAttribute(default=True)
    UserInstantiated = UnicodeAttribute(null=True)  # Internal PynamoDB field

    def serialize(self, values, *args, **kwargs):
        """
        Serialize the approver facts with default values.

        Parameters
        ----------
        values : dict
            Values to serialize.
        *args
            Additional arguments.
        **kwargs
            Additional keyword arguments.

        Returns
        -------
        dict
            Serialized values with defaults applied.
        """
        # Apply default values for serialization
        if "Sequence" not in values:
            values["Sequence"] = 1
        if "Enabled" not in values:
            values["Enabled"] = True
        return super().serialize(values, *args, **kwargs)


class OwnerFacts(ExtendedMapAttribute):
    """
    Owner details for a portfolio.

    This model represents ownership information for a portfolio.

    Attributes
    ----------
    Name : str
        Name of the owner.
    Email : str, optional
        Email address of the owner.
    Phone : str, optional
        Phone number of the owner.
    Attributes : dict, optional
        Additional attributes for the owner.
    """

    Name = UnicodeAttribute()
    Email = UnicodeAttribute(null=True)
    Phone = UnicodeAttribute(null=True)
    Attributes = MapAttribute(of=UnicodeAttribute, null=True)
    UserInstantiated = UnicodeAttribute(null=True)  # Internal PynamoDB field


class ProjectFacts(ExtendedMapAttribute):
    """
    Project details for a portfolio.

    This model represents project or business application information.

    Attributes
    ----------
    Name : str
        Name of the project.
    Code : str
        Code of the project.
    Repository : str, optional
        Git repository of the project.
    Description : str, optional
        Description of the project.
    Attributes : dict, optional
        Additional attributes for the project.
    """

    Name = UnicodeAttribute()
    Code = UnicodeAttribute()
    Repository = UnicodeAttribute(null=True)
    Description = UnicodeAttribute(null=True)
    Attributes = MapAttribute(of=UnicodeAttribute, null=True)
    UserInstantiated = UnicodeAttribute(null=True)  # Internal PynamoDB field


class PortfolioFacts(RegistryModel):
    """
    Protocol defining the interface for PortfolioFacts models.

    This protocol defines the structure for portfolio facts models that can be created
    dynamically for different clients using the PortfolioFactsFactory. It represents
    a complete portfolio configuration including contacts, approvers, project details,
    and metadata for deployment automation.

    Attributes
    ----------
    Client : UnicodeAttribute
        Client identifier (alternate key "client")
    Portfolio : UnicodeAttribute
        Portfolio identifier (alternate key "portfolio")
    Contacts : ListAttribute
        List of contact details for the portfolio (alternate key "contacts")
    Approvers : ListAttribute
        List of approver details for approval workflows (alternate key "approvers")
    Project : ProjectFacts
        Primary project details for the portfolio (alternate key "project")
    Domain : UnicodeAttribute
        Domain name or identifier for the portfolio (alternate key "domain")
    Bizapp : ProjectFacts
        Business application details, alternative to Project (alternate key "bizapp")
    Owner : OwnerFacts
        Owner details for the portfolio (alternate key "owner")
    Tags : MapAttribute
        Tags for deployment resources (alternate key "tags")
    Metadata : MapAttribute
        Additional metadata for the portfolio (alternate key "metadata")
    Attributes : MapAttribute
        Custom attributes for the portfolio (alternate key "attributes")
    UserInstantiated : UnicodeAttribute
        User instantiated the Model (internal PynamoDB field)

    Notes
    -----
    PortfolioFacts inherits all standard PynamoDB methods from ModelProtocol including:

    Instance Methods:
        - save(condition=None): Save instance to DynamoDB
        - delete(condition=None): Delete instance from DynamoDB
        - update(actions, condition=None): Update instance with actions
        - refresh(consistent_read=None): Refresh from DynamoDB
        - serialize(values=None): Serialize to dictionary
        - deserialize(values): Deserialize from dictionary
        - to_simple_dict(): Convert to simple dictionary
        - get_attributes(): Get model attributes
        - convert_keys(**kwargs): Convert attribute keys to proper case

    Class Methods:
        - get(hash_key, range_key=None): Get single item by keys
        - query(hash_key, **kwargs): Query items by hash key
        - scan(**kwargs): Scan all items in table
        - count(hash_key=None, **kwargs): Count items in table
        - exists(): Check if table exists
        - create_table(wait=False): Create DynamoDB table
        - delete_table(): Delete DynamoDB table
        - describe_table(): Get table description
        - batch_get(keys, **kwargs): Batch get multiple items
        - batch_write(auto_commit=True): Create batch write context
        - get_meta_data(): Get model metadata
        - from_raw_data(data): Create instance from raw DynamoDB data

    Custom Methods:
        - get_client_portfolio_key(): Get formatted client:portfolio key

    Examples
    --------
    Creating a portfolio with the factory pattern:

    >>> model_class = PortfolioFactsFactory.get_model("acme")
    >>> portfolio = model_class(
    ...     "acme", "web-services",
    ...     Domain="webservices.acme.com",
    ...     Owner={"Name": "John Doe", "Email": "john@acme.com"},
    ...     Tags={"Environment": "production", "Team": "platform"}
    ... )
    >>> portfolio.save()

    Querying portfolios for a client:

    >>> portfolios = list(model_class.query("acme"))
    >>> for p in portfolios:
    ...     print(f"{p.Client}:{p.Portfolio} - {p.Domain}")

    Using approval workflow:

    >>> portfolio.Approvers = [
    ...     {"Sequence": 1, "Name": "Manager", "Email": "mgr@acme.com"},
    ...     {"Sequence": 2, "Name": "Director", "Email": "dir@acme.com", "DependsOn": [1]}
    ... ]
    >>> portfolio.save()
    """

    class Meta(RegistryModel.Meta):
        pass

    Client = UnicodeAttribute(attr_name=CLIENT_KEY, hash_key=True)
    Portfolio = UnicodeAttribute(attr_name=PORTFOLIO_KEY, range_key=True)
    Contacts = ListAttribute(of=ContactFacts, null=True)
    Approvers = ListAttribute(of=ApproverFacts, null=True)
    Project = ProjectFacts(null=True)
    Domain = UnicodeAttribute(null=True)
    Bizapp = ProjectFacts(null=True)
    Owner = OwnerFacts(null=True)
    Tags = MapAttribute(of=UnicodeAttribute, null=True)
    Metadata = MapAttribute(of=UnicodeAttribute, null=True)
    Attributes = MapAttribute(of=UnicodeAttribute, null=True)
    UserInstantiated = UnicodeAttribute(null=True)


PortfolioFactsType = type[PortfolioFacts]


class PortfolioFactsFactory:
    """Factory to create client-specific PortfolioFacts models with dynamic table names."""

    _model_cache = {}

    @classmethod
    def get_model(
        cls, client: str, auto_create_table: bool = False
    ) -> PortfolioFactsType:
        """
        Get a PortfolioFacts model class for a specific client.

        Parameters
        ----------
        client : str
            The client name for table name generation.
        auto_create_table : bool, optional
            Whether to auto-create the table if it doesn't exist (default: True)

        Returns
        -------
        type[PortfolioFacts]
            A PortfolioFacts model class configured for the specified client.
        """
        if client not in cls._model_cache:
            model_class = cls._create_client_model(client)
            cls._model_cache[client] = model_class

            # Auto-create table if requested
            if auto_create_table:
                cls._ensure_table_exists(model_class)

        return cls._model_cache[client]

    @classmethod
    def _ensure_table_exists(cls, model_class: PortfolioFactsType) -> None:
        """
        Ensure the table exists, create it if it doesn't.

        Parameters
        ----------
        model_class : type
            The model class to check/create table for
        client : str
            The client name for logging
        """
        try:
            if not model_class.exists():
                log.info("Creating portfolio table: %s", model_class.Meta.table_name)
                model_class.create_table(wait=True)
                log.info(
                    "Successfully created portfolio table: %s",
                    model_class.Meta.table_name,
                )
        except Exception as e:
            log.error(
                "Failed to create portfolio table %s: %s",
                model_class.Meta.table_name,
                str(e),
            )
            # Don't raise - let the operation proceed and fail naturally
            pass

    @classmethod
    def _create_client_model(cls, client: str) -> PortfolioFactsType:
        """
        Create a new PortfolioFacts model class for a specific client.
        Parameters
        ----------
        client : str
            The client name for table configuration.
        Returns
        -------
        type[PortfolioFacts]
            Dynamic PortfolioFacts model class.
        """

        class PortfolioFactsModel(PortfolioFacts):
            class Meta(PortfolioFacts.Meta):
                table_name = get_table_name(PORTFOLIO_FACTS, client)

        return PortfolioFactsModel
