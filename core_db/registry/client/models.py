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

    # Attributes
    organization_id = UnicodeAttribute(null=True)
    organization_name = UnicodeAttribute(null=True)
    organization_account = UnicodeAttribute(null=True)
    audit_account = UnicodeAttribute(null=True)
    master_region = UnicodeAttribute(null=True)
    docs_bucket = UnicodeAttribute(null=True)
    client_region = UnicodeAttribute(null=True)
    automation_bucket = UnicodeAttribute(null=True)
    bucket_region = UnicodeAttribute(null=True)
    automation_account = UnicodeAttribute(null=True)
    security_account = UnicodeAttribute(null=True)
    scope_prefix = UnicodeAttribute(null=True)
    ui_bucket = UnicodeAttribute(null=True)
