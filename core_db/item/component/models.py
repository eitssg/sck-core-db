""" This module provides the field extensions for Items.Component in the core-automation-items table """

from pynamodb.attributes import UnicodeAttribute

from ..models import ItemModel

from core_framework.status import INIT


class ComponentModel(ItemModel):
    """
    Component Model field extensions
    """

    # Attribute status is required
    status = UnicodeAttribute(default_for_new=INIT)

    message = UnicodeAttribute(null=True)
    component_type = UnicodeAttribute(null=True)

    # This may be a VM and we want to record the AMI information.
    image_id = UnicodeAttribute(null=True)
    image_alias = UnicodeAttribute(null=True)

    # PRN References
    portfolio_prn = UnicodeAttribute(null=False)
    app_prn = UnicodeAttribute(null=False)
    branch_prn = UnicodeAttribute(null=False)
    build_prn = UnicodeAttribute(null=False)

    def __repr__(self):
        return f"<Component(prn={self.prn},name={self.name},component_type={self.component_type})>"
