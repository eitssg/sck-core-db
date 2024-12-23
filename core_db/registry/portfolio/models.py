""" Definiton of the Portfolio Facts in the core-automation-portfolios table """

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
)

import core_framework as util

from ...config import get_table_name, PORTFOLIO_FACTS


class ContactFacts(MapAttribute):
    """Contact details"""

    name = UnicodeAttribute()
    """str: Name of the contact"""

    email = UnicodeAttribute(null=True)
    """str: Email address of the contact"""

    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the contact"""

    enabled = BooleanAttribute(default=True)
    """bool: Is the contact enabled"""

    UserInstantiated = UnicodeAttribute(null=True)

    def serialize(self, values, *args, **kwargs):

        # Why?  Well, because the "default" value is for initialization, not for serialization
        if "enabled" not in values:
            values["enabled"] = True

        return super().serialize(values, *args, **kwargs)


class ApproverFacts(MapAttribute):
    """Approver details"""

    sequence = NumberAttribute(default=1)
    """int: Sequence number of the approver. Default is 1.  Can be used to order the approvers"""
    name = UnicodeAttribute()
    """str: Name of the approver"""
    email = UnicodeAttribute(null=True)
    """str: Email address of the approver"""
    roles: ListAttribute = ListAttribute(of=UnicodeAttribute, null=True)
    """list: List of roles for the approver.  This approver can approve only specified roles"""
    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the approver"""
    depends_on: ListAttribute = ListAttribute(of=NumberAttribute, null=True)
    """list: List of sequence numbers of approvers that this approver depends on (which approvers must approve before this approver) """
    enabled = BooleanAttribute(default=True)
    """bool: Is the approver enabled"""

    UserInstantiated = UnicodeAttribute(null=True)

    def serialize(self, values, *args, **kwargs):

        # Why?  Well, because the "default" value is for initialization, not for serialization
        if "sequence" not in values:
            values["sequence"] = 1
        if "enabled" not in values:
            values["enabled"] = True

        return super().serialize(values, *args, **kwargs)


class OwnerFacts(MapAttribute):
    """Owner details"""

    name = UnicodeAttribute()
    """str: Name of the owner"""
    email = UnicodeAttribute(null=True)
    """str: Email address of the owner"""
    phone = UnicodeAttribute(null=True)
    """str: Phone number of the owner"""
    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the owner"""

    UserInstantiated = UnicodeAttribute(null=True)


class ProjectFacts(MapAttribute):
    """Project details"""

    name = UnicodeAttribute()
    """str: Name of the project"""
    code = UnicodeAttribute()
    """str: Code of the project"""
    repository = UnicodeAttribute(null=True)
    """str: Git repository of the project"""
    description = UnicodeAttribute(null=True)
    """str: Description of the project"""
    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the project"""

    UserInstantiated = UnicodeAttribute(null=True)


class PortfolioFacts(Model):
    """Portfolio Facts database table record model"""

    class Meta:
        table_name = get_table_name(PORTFOLIO_FACTS)
        region = util.get_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    client = UnicodeAttribute(hash_key=True)
    """str: Client name is the Organization name "slug" representing the client organization. Example: "myorg" """

    portfolio = UnicodeAttribute(range_key=True)
    """str: Portfolio name is the name of the portfolio. Example: "myportfolio" """

    contacts = ListAttribute(of=ContactFacts, null=True)
    """list[ContactFacts]: List of contacts for the portfolio"""

    approvers = ListAttribute(of=ApproverFacts, null=True)
    """list[ApproverFacts]: List of approvers for the portfolio"""

    project = ProjectFacts(null=True)
    """ProjectFacts: Project details such as Jira Project, Confluence Workspace, Bitbucket Project, Jira Align Key"""

    bizapp = ProjectFacts(null=True)
    """ProjectFacts: Business Application details

        BizApp Code may be a Gitlab Group, GitHub org or GitHub group or team

    """
    owner = OwnerFacts(null=True)
    """OwnerFacts: Owner details"""

    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    """dict: Additional attributes for the portfolio

        Allow an option number of attributes to be added to the portfolio as UnicodeAttributes
        These will be used to store additional information about the portfolio
        that is not covered by the standard attributes
    """

    UserInstantiated = UnicodeAttribute(null=True)
