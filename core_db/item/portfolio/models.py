from pynamodb.attributes import UnicodeAttribute
from ..models import ItemModel


class PortfolioModel(ItemModel):

    # Attributes
    contact_email = UnicodeAttribute(null=False)

    def __repr__(self):
        return f"<Portfolio(prn={self.prn},name={self.name})>"
