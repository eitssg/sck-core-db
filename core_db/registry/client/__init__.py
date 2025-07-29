"""Module defiing the Actions and Models for the Registry.Clients database table core-autoamtion-clients"""

from .models import ClientFacts, ClientFactsFactory
from .actions import ClientActions

__all__ = ["ClientFacts", "ClientActions", "ClientFactsFactory"]
