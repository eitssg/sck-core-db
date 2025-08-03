"""This module provides the field extensions for Items.Component in the core-automation-items table"""

from pynamodb.attributes import UnicodeAttribute

from ...constants import ITEMS
from ...config import get_table_name
from ..models import ItemModel

from core_framework.status import INIT


class ComponentModel(ItemModel):
    """
    Component Model field extensions
    """

    # Attribute status is required
    status = UnicodeAttribute(default_for_new=INIT)
    """str: Status of the component.  Two possible values :class:`core_framework.status.BuildStatus` """

    message = UnicodeAttribute(null=True)
    """str: Message details for the component. """

    component_type = UnicodeAttribute(null=True)
    """str: Component type (ec2, s3, eni, etc) """

    image_id = UnicodeAttribute(null=True)
    """str: Image ID of the EC2 component. """

    image_alias = UnicodeAttribute(null=True)
    """str: Image Alias name of the EC2 component. """

    portfolio_prn = UnicodeAttribute(null=False)
    """str: Portfolio PRN for the component. """

    app_prn = UnicodeAttribute(null=False)
    """str: App PRN for the component. """

    branch_prn = UnicodeAttribute(null=False)
    """str: Branch PRN for the component. """

    build_prn = UnicodeAttribute(null=False)
    """str: Build PRN for the component. """

    def __repr__(self):
        return f"<Component(prn={self.prn},name={self.name},component_type={self.component_type})>"


class ComponentModelFactory:
    """
    Factory class to create the ComponentModel
    """

    __model_cache = {}

    @classmethod
    def get_model(cls, client_name: str) -> ComponentModel:
        """
        Get the ComponentModel for the given client

        Args:
            client_name (str): The name of the client

        Returns:
            ComponentModel: The ComponentModel for the given client
        """
        if client_name not in cls.__model_cache:
            cls.__model_cache[client_name] = cls._create_model(client_name)
        return cls.__model_cache[client_name]

    @classmethod
    def _create_model(cls, client_name: str) -> ComponentModel:
        """
        Create a new ComponentModel class for the given client.

        Args:
            client_name (str): The name of the client

        Returns:
            ComponentModel: A new ComponentModel class for the given client
        """

        class ComponentModelClass(ComponentModel):
            class Meta(ComponentModel.Meta):
                table_name = get_table_name(ITEMS, client_name)

        return ComponentModelClass
