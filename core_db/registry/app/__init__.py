""" Module defiing the Actions and Models for the Registry.App database table core-autoamtion-apps """

from .models import AppFacts

from .actions import AppActions

__all__ = ["AppFacts", "AppActions"]
