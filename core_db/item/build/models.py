"""This module provides the field extensions for Items.Build in the core-automation-items table"""

from pynamodb.attributes import UnicodeAttribute, MapAttribute

from core_framework.status import INIT

from ...constants import ITEMS
from ...config import get_table_name
from ..models import ItemModel


class BuildModel(ItemModel):
    """
    Build model field extensions
    """

    # Attribute status is required
    status = UnicodeAttribute(default_for_new=INIT)
    """str: Status of the build.  Two possible values :class:`core_framework.status.BuildStatus` """

    message = UnicodeAttribute(null=True)
    """str: Message details for the build. """

    context: MapAttribute = MapAttribute(null=True)
    """str: Context details for the build. """

    portfolio_prn = UnicodeAttribute(null=False)
    """str: Portfolio PRN for the build. """

    app_prn = UnicodeAttribute(null=False)
    """str: App PRN for the build. """

    branch_prn = UnicodeAttribute(null=False)
    """str: Branch PRN for the build. """

    def __repr__(self):
        return f"<Build(prn={self.prn},name={self.name},status={self.status})>"


class BuildModelFactory:
    """
    Factory class to create the BuildModel
    """

    _model_cache = {}

    @classmethod
    def get_model(cls, client_name: str) -> BuildModel:
        """
        Get the BuildModel for the given client

        Args:
            client_name (str): The name of the client

        Returns:
            BuildModel: The BuildModel for the given client

        """
        if client_name not in cls._model_cache:
            cls._model_cache[client_name] = cls._create_model(client_name)
        return cls._model_cache[client_name]

    @classmethod
    def _create_model(cls, client_name: str) -> BuildModel:
        class BuildModelClass(BuildModel):
            class Meta(BuildModel.Meta):
                table_name = get_table_name(ITEMS, client_name)

        return BuildModelClass
