""" Defines the generic model for items stored in the core-automation-items table.

This will be subclassed by portfolio, app, branch, build, component modesl to implmeent their
specific field extentions.

"""

from dateutil import parser

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
    """str: Parent Pipeline Reference Number (PRN) of the item (a.k.a identity) """

    created_at = UTCDateTimeAttribute(range_key=True)
    """datetime: Timestamp of the item creation.  Let the system auto-generate.  This is a RANGE key for the index. """


class ItemModel(Model):
    """
    Defines the generic model for items stored in the core-automation-items table.

    References:
        * :class:`core_db.item.portfolio.models.PortfolioModel`
        * :class:`core_db.item.app.models.AppModel`
        * :class:`core_db.item.branch.models.BranchModel`
        * :class:`core_db.item.build.models.BuildModel`
        * :class:`core_db.item.component.models.ComponentModel`

    Args:
        Model (Model): Pynamodb Model class

    Returns:
        ItemModel: The Item Model representing the core-automation-items table
    """

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

    prn = UnicodeAttribute(hash_key=True)
    """str: Pipeline Reference Number (PRN) of the item (a.k.a identity) """

    parent_prn = UnicodeAttribute(null=False)
    """str: Parent Pipeline Reference Number (PRN) of the item (a.k.a identity) """

    item_type = UnicodeAttribute(null=False)
    """str: Type of item this event relates to such as portfolio, app, branch, build, component, account, etc. """

    name = UnicodeAttribute(null=False)
    """str: Name of the item.  This is the human readable name of the item. """

    created_at = UTCDateTimeAttribute(default_for_new=make_default_time)
    """datetime: Timestamp of the item creation.  Let the system auto-generate """

    updated_at = UTCDateTimeAttribute(default=make_default_time)
    """datetime: Timestamp of the item update.  Let the system auto-generate """

    parent_created_at_index = ParentCreatedAtIndex()
    """GlobalSecondaryIndex: Index for parent_prn and created_at fields.  Used for querying items by parent and creation date.  """

    def __init__(self, *args, **kwargs):
        if "created_at" in kwargs and isinstance(kwargs["created_at"], str):
            kwargs["created_at"] = parser.parse(kwargs["created_at"])
        if "updated_at" in kwargs and isinstance(kwargs["updated_at"], str):
            kwargs["updated_at"] = parser.parse(kwargs["updated_at"])
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Item(prn={self.prn},item_type={self.item_type},name={self.name})>"

    def save(self, *args, **kwargs):
        self.updated_at = make_default_time()
        super(ItemModel, self).save(*args, **kwargs)

    def update(self, actions=None, condition=None, **kwargs):
        self.updated_at = make_default_time()
        super(ItemModel, self).update(actions=actions, condition=condition, **kwargs)
