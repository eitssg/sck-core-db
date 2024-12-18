""" This module provides the field extensions for Items.Branch in the core-automation-items table """

from pynamodb.attributes import UnicodeAttribute

from ...constants import PRN, RELEASED_BUILD_PRN

from ..models import ItemModel


class BranchModel(ItemModel):
    """
    Branch Model field extentions
    """
    # Attributes. This mus be a generated short name (slug)
    short_name = UnicodeAttribute(null=False)

    # Releases references
    released_build_prn = UnicodeAttribute(null=True)

    # PRN References
    portfolio_prn = UnicodeAttribute(null=False)
    app_prn = UnicodeAttribute(null=False)

    def __repr__(self):
        return f"<Branch(prn={self.prn},name={self.name})>"

    @classmethod
    def construct_released_build(cls, **kwargs) -> dict:
        released_build_prn = kwargs.get(RELEASED_BUILD_PRN, None)
        if released_build_prn:
            return {PRN: released_build_prn}
        return {}
