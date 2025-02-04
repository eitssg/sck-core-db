"""Classes defining the Clients record model for the core-automation-clients table"""

from pynamodb.attributes import UnicodeAttribute

import core_framework as util

from ...constants import CLIENT_FACTS
from ...config import get_table_name

from ..models import RegistryModel


class ClientFacts(RegistryModel):

    class Meta:
        table_name = get_table_name(CLIENT_FACTS)
        region = util.get_dynamodb_region()
        host = util.get_dynamodb_host()
        read_capacity_units = 1
        write_capacity_units = 1

    # Hash/Range keys
    Client = UnicodeAttribute(hash_key=True)
    """str: Client ID or slug as the unique identifier for the client organization. Example: "myorg" """
    ClientName = UnicodeAttribute(null=True)
    """str: Client name. Example: "My Organization" """
    # Attributes
    OrganizationId = UnicodeAttribute(null=True)
    """str: Organization ID for the organization. Example: "o-t73gu32ai5" """
    OrganizationName = UnicodeAttribute(null=True)
    """str: Organization name. Example: "My Organization" """
    OrganizationAccount = UnicodeAttribute(null=True)
    """str: Organization acount number for the organization (Root Account). Example: "123456789012" """
    OrganizationEmail = UnicodeAttribute(null=True)
    """str: Organization email address for the organization (Root Account). Example: aws+1@gmail.com """
    Domain = UnicodeAttribute(null=True)
    """str: Domain name for the organization. Example: "myorg.com" """
    AuditAccount = UnicodeAttribute(null=True)
    """str: Audit account number for the audit account where Centralized Logging takes place. Example: "123456789012" """
    MasterRegion = UnicodeAttribute(null=True)
    """str: Master region where the master account resides and is where Core-Auotmation is deployed. Example: "us-west-2" """
    DocsBucketName = UnicodeAttribute(null=True)
    """str: Documentation bucket where the documentation is stored. Example: "myorg-core-automation-docs" """
    ClientRegion = UnicodeAttribute(null=True)
    """str: Client region for use when other region values are blank. Example: "us-west-2" """
    AutomationAccount = UnicodeAttribute(null=True)
    """str: Automation account number for the automation account where the automation artefacts are stored. Example: "123456789012" """
    BucketName = UnicodeAttribute(null=True)
    """str: Automation S3 bucket where the automation artefacts (packages/files/artefacts) are stored. Example: "myorg-core-automation" """
    BucketRegion = UnicodeAttribute(null=True)
    """str: Bucket region where the automation bucket resides. Example: "us-west-2" """
    ArtefactBucketName = UnicodeAttribute(null=True)
    """str: Artefact S3 bucket where the artefacts are stored. Example: "myorg-core-automation-artefacts" """
    SecurityAccount = UnicodeAttribute(null=True)
    """str: Security account number for the security account where your centralized SOC will operate. Example: "123456789012" """
    NetworkAccount = UnicodeAttribute(null=True)
    """str: Network account number for the network account where your centralized VPCs, domain services, and endpoints will operate. Example: "123456789012" """
    UiBucketName = UnicodeAttribute(null=True)
    """str: UI bucket where the UI website is stored. Example: "myorg-core-automation-ui" """
    Scope = UnicodeAttribute(null=True)
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
    UiBucket = UnicodeAttribute(null=True)
    """str: UI Bucket is the S3 bucket where the UI website is stored. Example: "core-automation-ui" """

    UserInstantiated = UnicodeAttribute(null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"ClientFacts({self.Client})"
