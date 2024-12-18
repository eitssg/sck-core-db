""" Definiton of the Portfolio Facts in the core-automation-portfolios table """

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
)

import core_framework as util

from ...config import get_table_name, PORTFOLIO_FACTS


class ContactFacts(MapAttribute):
    """ Contact details """
    name = UnicodeAttribute(hash_key=True)
    email = UnicodeAttribute(range_key=True)
    enabled = BooleanAttribute(default=True)


class ApproverFacts(MapAttribute):
    """ Approver details """
    name = UnicodeAttribute(hash_key=True)
    email = UnicodeAttribute(range_key=True)
    enabled = BooleanAttribute(default=True)


class OwnerFacts(MapAttribute):
    """ Owner details """
    name = UnicodeAttribute(hash_key=True)
    email = UnicodeAttribute(range_key=True)
    phone = UnicodeAttribute(null=True)


class PortfolioFacts(Model):
    """ Portfolio Facts database table record model """
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
    project_name = UnicodeAttribute(null=True)
    project_code = UnicodeAttribute(null=True)
    project_description = UnicodeAttribute(null=True)

    # Business Application
    # BizApp Code may be a Gitlab Group, GitHub org or GitHub group or team
    bizapp_name = UnicodeAttribute(null=True)
    bizapp_code = UnicodeAttribute(null=True)  # Confluence Workspace Code
    bizapp_description = UnicodeAttribute(null=True)

    # Application Owners
    owner = OwnerFacts(null=True)

    # Allow an option number of attributes to be added to the portfolio as UnicodeAttributes
    # These will be used to store additional information about the portfolio
    # that is not covered by the standard attributes
    attributes = ListAttribute(of=UnicodeAttribute, null=True)
