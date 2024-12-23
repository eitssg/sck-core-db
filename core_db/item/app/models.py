""" This module provides the field extensions for Items.App in the core-automation-items table """

from pynamodb.attributes import UnicodeAttribute

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
