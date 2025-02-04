"""Defines the RegistryAction Interface for all tables marked as Registry"""

from ..actions import TableActions


class RegistryAction(TableActions):
    """Defines a class name and common functions for RegistryActions extending TableActions class"""

    def __init__(self):
        return super().__init__()
