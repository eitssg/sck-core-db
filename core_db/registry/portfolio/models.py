""" Definiton of the Portfolio Facts in the core-automation-portfolios table """

from pynamodb.attributes import (
    UnicodeAttribute,
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
)

import core_framework as util

from ...config import get_table_name, PORTFOLIO_FACTS

from ..models import RegistryModel, ExtendedMapAttribute


class ContactFacts(ExtendedMapAttribute):
    """Contact details"""

    Name = UnicodeAttribute()
    """str: Name of the contact"""
    Email = UnicodeAttribute(null=True)
    """str: Email address of the contact"""
    Attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the contact"""
    Enabled = BooleanAttribute(default=True)
    """bool: Is the contact enabled"""

    UserInstantiated = UnicodeAttribute(null=True)

    def serialize(self, values, *args, **kwargs):

        # Why?  Well, because the "default" value is for initialization, not for serialization
        if "Enabled" not in values:
            values["Enabled"] = True

        return super().serialize(values, *args, **kwargs)


class ApproverFacts(ExtendedMapAttribute):
    """Approver details"""

    Sequence = NumberAttribute(default=1)
    """int: Sequence number of the approver. Default is 1.  Can be used to order the approvers"""
    Name = UnicodeAttribute()
    """str: Name of the approver"""
    Email = UnicodeAttribute(null=True)
    """str: Email address of the approver"""
    Roles: ListAttribute = ListAttribute(of=UnicodeAttribute, null=True)
    """list: List of roles for the approver.  This approver can approve only specified roles"""
    Attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the approver"""
    DependsOn: ListAttribute = ListAttribute(of=NumberAttribute, null=True)
    """list: List of sequence numbers of approvers that this approver depends on (which approvers must approve before this approver) """
    Enabled = BooleanAttribute(default=True)
    """bool: Is the approver enabled"""

    UserInstantiated = UnicodeAttribute(null=True)

    def serialize(self, values, *args, **kwargs):

        # Why?  Well, because the "default" value is for initialization, not for serialization
        if "Sequence" not in values:
            values["Sequence"] = 1
        if "Enabled" not in values:
            values["Enabled"] = True

        return super().serialize(values, *args, **kwargs)


class OwnerFacts(ExtendedMapAttribute):
    """Owner details"""

    Name = UnicodeAttribute()
    """str: Name of the owner"""
    Email = UnicodeAttribute(null=True)
    """str: Email address of the owner"""
    Phone = UnicodeAttribute(null=True)
    """str: Phone number of the owner"""
    Attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the owner"""

    UserInstantiated = UnicodeAttribute(null=True)


class ProjectFacts(ExtendedMapAttribute):
    """Project details"""

    Name = UnicodeAttribute()
    """str: Name of the project"""
    Code = UnicodeAttribute()
    """str: Code of the project"""
    Repository = UnicodeAttribute(null=True)
    """str: Git repository of the project"""
    Description = UnicodeAttribute(null=True)
    """str: Description of the project"""
    Attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the project"""

    UserInstantiated = UnicodeAttribute(null=True)


class PortfolioFacts(RegistryModel):
    """Portfolio Facts database table record model"""

    class Meta:
        table_name = get_table_name(PORTFOLIO_FACTS)
        region = util.get_dynamodb_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    Client = UnicodeAttribute(hash_key=True)
    """str: Client name is the Organization name "slug" representing the client organization. Example: "myorg" """

    Portfolio = UnicodeAttribute(range_key=True)
    """str: Portfolio name is the name of the portfolio. Example: "myportfolio" """

    Contacts = ListAttribute(of=ContactFacts, null=True)
    """list[ContactFacts]: List of contacts for the portfolio"""

    Approvers = ListAttribute(of=ApproverFacts, null=True)
    """list[ApproverFacts]: List of approvers for the portfolio"""

    Project = ProjectFacts(null=True)
    """ProjectFacts: Project details such as Jira Project, Confluence Workspace, Bitbucket Project, Jira Align Key"""

    Domain = UnicodeAttribute(null=True)
    """str: Domain name for the portfolio bizapp"""

    Bizapp = ProjectFacts(null=True)
    """ProjectFacts: Business Application details

        BizApp Code may be a Gitlab Group, GitHub org or GitHub group or team

    """
    Owner = OwnerFacts(null=True)
    """OwnerFacts: Owner details"""

    Tags: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Tags for the portfolio

        Tags are key value pairs that can be used to categorize and manage the portfolio and
        will be applied to all Apps registered in the portfolio.
    """

    Metadata: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional metadata for the portfolio

        Allow an option number of attributes to be added to the portfolio as UnicodeAttributes
        These will be used to store additional information about the portfolio
        that is not covered by the standard attributes
    """

    Attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the portfolio

        Allow an option number of attributes to be added to the portfolio as UnicodeAttributes
        These will be used to store additional information about the portfolio
        that is not covered by the standard attributes
    """

    UserInstantiated = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"PortfolioFacts({self.Client}, {self.Portfolio})"

    def get_client_portfolio_key(self):
        """Get the client portfolio key

        The key is a combination of the client and portfolio names

        The format is "{Client}:{Portfolio}"

        Returns:
            str: The client portfolio key

        """
        return f"{self.Client}:{self.Portfolio}"
