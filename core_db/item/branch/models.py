""" This module provides the field extensions for Items.Branch in the core-automation-items table """

from pynamodb.attributes import UnicodeAttribute

from ...constants import PRN, RELEASED_BUILD_PRN

from ..models import ItemModel


class BranchModel(ItemModel):
    """
    Branch Model field extentions

    """
    class Meta:
        """
        :no-index:
        """
        pass

    short_name = UnicodeAttribute(null=False)
    """str: Short name of the branch. """

    released_build_prn = UnicodeAttribute(null=True)
    """str: PRN of the released build. """

    portfolio_prn = UnicodeAttribute(null=False)
    """str: Portfolio PRN for the branch"""

    app_prn = UnicodeAttribute(null=False)
    """str: App PRN for the branch"""

    def __repr__(self):
        return f"<Branch(prn={self.prn},name={self.name})>"

    @classmethod
    def construct_released_build(cls, **kwargs) -> dict:
        """
        Construct the released build PRN.  Get's the PRN from
        the kwargs if available or returns an empty dict.

        Return example:

            ```
            {
                "prn": "prn:portfolio:app:branch:build"
            }
            ```

        Returns:
            dict: Dictionary with the released build PRN
        """

        released_build_prn = kwargs.get(RELEASED_BUILD_PRN, None)
        if released_build_prn:
            return {PRN: released_build_prn}
        return {}
