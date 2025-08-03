"""This module provides the field extensions for Items.App in the core-automation-items table"""

from pynamodb.attributes import UnicodeAttribute

from ...constants import ITEMS
from ...config import get_table_name
from ..models import ItemModel


class AppModel(ItemModel):
    """
    App model field extensions
    """

    contact_email = UnicodeAttribute(null=False)
    """str: Contact email for the app. Example: """

    portfolio_prn = UnicodeAttribute(null=False)
    """str: Portfolio PRN for the app. """

    def __repr__(self):
        return f"<App(prn={self.prn},name={self.name})>"


class AppModelFactory:
    """
    Factory class to create the AppModel
    """

    _model_cache = {}

    @classmethod
    def get_model(cls, client_name: str) -> AppModel:
        """
        Get the AppModel for the given client

        Args:
            client_name (str): The name of the client

        Returns:
            AppModel: The AppModel for the given client
        """
        if client_name not in cls._model_cache:
            cls._model_cache[client_name] = cls._create_model(client_name)
        return cls._model_cache[client_name]

    @classmethod
    def _create_model(cls, client_name: str) -> AppModel:
        class AppModelClass(AppModel):
            class Meta(AppModel.Meta):
                table_name = get_table_name(ITEMS, client_name)

        return AppModelClass
