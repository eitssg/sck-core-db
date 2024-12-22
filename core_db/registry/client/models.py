""" Classes defining the Clients record model for the core-automation-clients table """

from pynamodb.attributes import UnicodeAttribute

import core_framework as util

from ...constants import CLIENT_FACTS
from ...config import get_table_name

from ..models import RegistryModel


class ClientFacts(RegistryModel):

    class Meta:
        table_name = get_table_name(CLIENT_FACTS)
        region = util.get_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    # Hash/Range keys
    client = UnicodeAttribute(hash_key=True)
    """str: Client ID or slug as the unique identifier for the client organization. Example: "myorg" """
    # Attributes
    organization_id = UnicodeAttribute(null=True)
    """str: Organization ID for the organization. Example: "o-t73gu32ai5" """
    organization_name = UnicodeAttribute(null=True)
    """str: Organization name. Example: "My Organization" """
    organization_account = UnicodeAttribute(null=True)
    """str: Organization acount number for the organization (Root Account). Example: "123456789012" """
    audit_account = UnicodeAttribute(null=True)
    """str: Audit account number for the audit account where Centralized Logging takes place. Example: "123456789012" """
    master_region = UnicodeAttribute(null=True)
    """str: Master region where the master account resides and is where Core-Auotmation is deployed. Example: "us-west-2" """
    docs_bucket = UnicodeAttribute(null=True)
    """str: Documentation bucket where the documentation is stored. Example: "myorg-core-automation-docs" """
    client_region = UnicodeAttribute(null=True)
    """str: Client region for use when other region values are blank. Example: "us-west-2" """
    automation_bucket = UnicodeAttribute(null=True)
    """str: Automation S3 bucket where the automation artefacts (packages/files/artefacts) are stored. Example: "myorg-core-automation" """
    bucket_region = UnicodeAttribute(null=True)
    """str: Bucket region where the automation bucket resides. Example: "us-west-2" """
    automation_account = UnicodeAttribute(null=True)
    """str: Automation account number for the automation account where the automation artefacts are stored. Example: "123456789012" """
    security_account = UnicodeAttribute(null=True)
    """str: Security account number for the security account where your centralized SOC will operate. Example: "123456789012" """
    scope_prefix = UnicodeAttribute(null=True)
    """str: Scope Prefix as a profix for all resources created for the client. Example: "testing-"

    Note: Ensure to put a hyphen after the name. Use "tst-", not "tst"

    And will result in Core automation adding this to the front of all bucket names, lambda functions, table names, roles, rules and other items.

        Example of resource names:
            * "tst-myorg-core-automation"
            * "tst-myorg-core-automation-docs"
            * "tst-myorg-core-automation-logs"
            * "tst-myorg-core-automation-ui"
            * "tst-myorg-core-automation-items"
            * "tst-myorg-core-automation-events"
            * "tst-core-automation-clients"
            * "tst-core-automation-portfolios"
            * "tst-core-automation-apps"
            * "tst-core-automation-zones"
            * "tst-core-automation-invoker"
            * "tst-core-automation-execute"
            * "tst-core-automation-runner"
            * "tst-core-automation-component-compiler"
            * "tst-core-automation-deployspec-executor"
            * I think you get the idea.
    """
    ui_bucket = UnicodeAttribute(null=True)
    """str: UI Bucket is the S3 bucket where the UI website is stored. Example: "core-automation-ui" """
