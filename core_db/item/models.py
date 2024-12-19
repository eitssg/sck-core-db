""" Defines the generic model for items stored in the core-automation-items table.

This will be subclassed by portfolio, app, branch, build, component modesl to implmeent their
specific field extentions.

"""

from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute

import core_framework as util

from core_framework.time_utils import make_default_time

from ..constants import ITEMS
from ..config import get_table_name


class ParentCreatedAtIndexMeta:
    index_name = "parent-created_at-index"
    projection = AllProjection()
    read_capacity_units = 1
    write_capacity_units = 1


class ParentCreatedAtIndex(GlobalSecondaryIndex):
    class Meta(ParentCreatedAtIndexMeta):
        pass

    parent_prn = UnicodeAttribute(hash_key=True)
    created_at = UTCDateTimeAttribute(range_key=True)


class ItemModel(Model):
    class Meta:
        """
        The metadata is used to configure the table for the ItemModel
        Item Model maintains the table documenting all deployments from
        portfolios through components segments.
        """

        table_name = get_table_name(ITEMS)  # e.g. "core-automation-items"
        region = util.get_dynamodb_region()  # e.g. "us-east-1"
        host = (
            util.get_dynamodb_host()
        )  # e.g. "https://dynamodb.us-east-1.amazonaws.com"
        read_capacity_units = 1
        write_capacity_units = 1

    # Attribute primary key
    prn = UnicodeAttribute(hash_key=True)

    # A parent is ALWAYS required.  In this current implementation, the portfolio parent is always "prn".
    parent_prn = UnicodeAttribute(null=False)

    # Iem attributes
    item_type = UnicodeAttribute(null=False)
    name = UnicodeAttribute(null=False)

    # Date/Time fields.  We want to know when the item was created and last updated.
    created_at = UTCDateTimeAttribute(default_for_new=make_default_time)
    updated_at = UTCDateTimeAttribute(default=make_default_time)

    # Indexes
    parent_created_at_index = ParentCreatedAtIndex()

    def __repr__(self):
        return f"<Item(prn={self.prn},item_type={self.item_type},name={self.name})>"

    def save(self, *args, **kwargs):
        self.updated_at = make_default_time()
        super(ItemModel, self).save(*args, **kwargs)

    def update(self, actions=None, condition=None, **kwargs):
        self.updated_at = make_default_time()
        super(ItemModel, self).update(actions=actions, condition=condition, **kwargs)
