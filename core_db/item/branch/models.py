"""This module provides the field extensions for Items.Branch in the core-automation-items table"""

from pynamodb.attributes import UnicodeAttribute

from ...constants import PRN, RELEASED_BUILD_PRN

from ...constants import ITEMS
from ...config import get_table_name
from ..models import ItemModel


class BranchModel(ItemModel):
    """Branch Model field extentions"""

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

        .. code-block:: json

            {
              "prn": "prn:portfolio:app:branch:build"
            }


        Returns:
            dict: Dictionary with the released build PRN

        """

        released_build_prn = kwargs.get(RELEASED_BUILD_PRN, None)
        if released_build_prn:
            return {PRN: released_build_prn}
        return {}


class BranchModelFactory:
    """
    Factory class to create the BranchModel
    """

    _model_cache = {}

    @classmethod
    def get_model(cls, client_name: str) -> BranchModel:
        """
        Get the BranchModel for the given client

        Args:
            client_name (str): The name of the client

        Returns:
            BranchModel: The BranchModel for the given client
        """
        if client_name not in cls._model_cache:
            cls._model_cache[client_name] = cls._create_model(client_name)
        return cls._model_cache[client_name]

    @classmethod
    def _create_model(cls, client_name: str) -> BranchModel:
        class BranchModelClass(BranchModel):
            class Meta(BranchModel.Meta):
                table_name = get_table_name(ITEMS, client_name)

        return BranchModelClass
