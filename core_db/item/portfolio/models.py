"""This module provides the field extensions for Items.Portfolios in the core-automation-items table"""

from pynamodb.attributes import UnicodeAttribute

from ...constants import ITEMS
from ...config import get_table_name
from ..models import ItemModel


class PortfolioModel(ItemModel):
    """
    Portfolio model field extensions

    """

    contact_email = UnicodeAttribute(null=False)
    """str: Contact email for the portfolio. Example: """

    def __repr__(self):
        return f"<Portfolio(prn={self.prn},name={self.name})>"


class PortfolioModelFactory:
    """
    Factory class to create the PortfolioModel
    """

    _model_cache = {}

    @classmethod
    def get_model(cls, client_name: str) -> PortfolioModel:
        """
        Get the PortfolioModel for the given client

        Args:
            client_name (str): The name of the client

        Returns:
            PortfolioModel: The PortfolioModel for the given client
        """
        if client_name not in cls._model_cache:
            cls._model_cache[client_name] = cls._create_model(client_name)
        return cls._model_cache[client_name]

    @classmethod
    def _create_model(cls, client_name: str) -> PortfolioModel:
        class PortfolioModelClass(PortfolioModel):
            class Meta(PortfolioModel.Meta):
                table_name = get_table_name(ITEMS, client_name)

        return PortfolioModelClass
