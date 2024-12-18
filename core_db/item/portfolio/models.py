""" This module provides the field extensions for Items.Portfolios in the core-automation-items table """

from pynamodb.attributes import UnicodeAttribute
from ..models import ItemModel


class PortfolioModel(ItemModel):
    """
    Portfolio model field extensions

    """
    # Attributes
    contact_email = UnicodeAttribute(null=False)

    def __repr__(self):
        return f"<Portfolio(prn={self.prn},name={self.name})>"
