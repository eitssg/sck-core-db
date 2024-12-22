""" This module provides the field extensions for Items.Component in the core-automation-items table """

from pynamodb.attributes import UnicodeAttribute

from ..models import ItemModel

from core_framework.status import INIT


class ComponentModel(ItemModel):
    """
    Component Model field extensions
    """
    class Meta:
        """
        :no-index:
        """
        pass

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
