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
    """Contact details

    Attributes:
        name (str): Name of the contact
        email (str): Email address of the contact
        attributes (dict): Additional attributes for the contact
        enabled (bool): Is the contact enabled

    """

    name = UnicodeAttribute()
    email = UnicodeAttribute(null=True)
    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    enabled = BooleanAttribute(default=True)

    def serialize(self, values, *args, **kwargs):

        # Why?  Well, because the "default" value is for initialization, not for serialization
        if "enabled" not in values:
            values["enabled"] = True

        return super().serialize(values, *args, **kwargs)


class ApproverFacts(MapAttribute):
    """Approver details

    Attributes:
        sequence (int): Sequence number of the approver
        name (str): Name of the approver
        email (str): Email address of the approver
        roles (list): List of roles for the approver
        attributes (dict): Additional attributes for the approver
        depends_on (list): List of sequence numbers of approvers that this approver depends on
        enabled (bool): Is the approver enabled

    """

    sequence = NumberAttribute(default=1)
    name = UnicodeAttribute()
    email = UnicodeAttribute(null=True)
    roles: ListAttribute = ListAttribute(of=UnicodeAttribute, null=True)
    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
    depends_on: ListAttribute = ListAttribute(of=NumberAttribute, null=True)
    enabled = BooleanAttribute(default=True)

    def serialize(self, values, *args, **kwargs):

        # Why?  Well, because the "default" value is for initialization, not for serialization
        if "sequence" not in values:
            values["sequence"] = 1
        if "enabled" not in values:
            values["enabled"] = True

        return super().serialize(values, *args, **kwargs)


class OwnerFacts(MapAttribute):
    """Owner details

    Attributes:
        name (str): Name of the owner
        email (str): Email address of the owner
        phone (str): Phone number of the owner
        attributes (dict): Additional attributes for the owner

    """

    name = UnicodeAttribute()
    email = UnicodeAttribute(null=True)
    phone = UnicodeAttribute(null=True)
    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)


class ProjectFacts(MapAttribute):
    """Project details

    Attributes:
        name (str): Name of the project
        code (str): Code of the project
        repository (str): Repository of the project
        description (str): Description of the project
        attributes (dict): Additional attributes for the project

    """

    name = UnicodeAttribute()
    code = UnicodeAttribute()
    repository = UnicodeAttribute(null=True)
    description = UnicodeAttribute(null=True)
    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)


class PortfolioFacts(Model):
    """Portfolio Facts database table record model

    Attributes:
        client (str): Client name
        portfolio (str): Portfolio name
        contacts (list): List of contacts
        approvers (list): List of approvers
        project (dict): Project details
        bizapp (dict): Business Application details
        owner (dict): Owner details
        attributes (dict): Additional attributes for the portfolio
    """

    class Meta:
        table_name = get_table_name(PORTFOLIO_FACTS)
        region = util.get_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    # Hash/Range keys
    client = UnicodeAttribute(hash_key=True)
    portfolio = UnicodeAttribute(range_key=True)

    # Contacts and Approvers
    contacts = ListAttribute(of=ContactFacts, null=True)
    approvers = ListAttribute(of=ApproverFacts, null=True)

    # JIRA Key, Confluence Workspace Code, Bitbucket Project Key, Jira Align Key
    project = ProjectFacts(null=True)

    # Business Application
    # BizApp Code may be a Gitlab Group, GitHub org or GitHub group or team
    bizapp = ProjectFacts(null=True)

    # Application Owners
    owner = OwnerFacts(null=True)

    # Allow an option number of attributes to be added to the portfolio as UnicodeAttributes
    # These will be used to store additional information about the portfolio
    # that is not covered by the standard attributes
    attributes: MapAttribute = MapAttribute(of=UnicodeAttribute, null=True)
