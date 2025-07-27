"""Classes defining the Apps record model for the core-automation-apps table"""

from typing import Protocol, Optional, Any, Iterator
from pynamodb.attributes import MapAttribute, UnicodeAttribute
from pynamodb.expressions.condition import Condition

import core_framework as util
import core_logging as log

from ...constants import CLIENT_PORTFOLIO_KEY, APP_KEY
from ...config import get_table_name, APP_FACTS
from ..models import RegistryModel, ModelProtocol


class AppFacts(ModelProtocol):
    """
    Protocol defining the Apps record model interface for the core-automation-apps table.

    This protocol defines the structure for app facts models that can be created
    dynamically for different clients using the AppFactsFactory.

    Attributes
    ----------
    ClientPortfolio : UnicodeAttribute
        Client Portfolio identifier (alternate key "client-portfolio")
    AppRegex : UnicodeAttribute
        App Regex identifier (alternate key "app-regex")
    Name : UnicodeAttribute
        Name of the app (alternate key "name")
    Environment : UnicodeAttribute
        Environment of the app (alternate key "environment")
    Account : UnicodeAttribute
        Account of the app (alternate key "account")
    Zone : UnicodeAttribute
        Zone of the app (alternate key "zone")
    ImageAliases : MapAttribute
        Image Aliases of the app to reduce bake time (alternate key "image-aliases")
    Repository : UnicodeAttribute
        Git repository of the app (alternate key "repository")
    Region : UnicodeAttribute
        Region of the app (alternate key "region")
    Tags : MapAttribute
        Tags of the app (alternate key "tags")
    EnforceValidation : UnicodeAttribute
        Enforce validation of the app (alternate key "enforce-validation")
    Metadata : MapAttribute
        Metadata of the app (alternate key "metadata")

    Notes
    -----
    We call this "zone" now. A "zone" contains "apps" that are deployed together
    in an Account. A zone can have multiple region definitions.
    """

    # Attribute definitions
    ClientPortfolio: UnicodeAttribute
    AppRegex: UnicodeAttribute
    Name: UnicodeAttribute
    Environment: UnicodeAttribute
    Account: UnicodeAttribute
    Zone: UnicodeAttribute
    ImageAliases: MapAttribute
    Repository: UnicodeAttribute
    Region: UnicodeAttribute
    Tags: MapAttribute
    EnforceValidation: UnicodeAttribute
    Metadata: MapAttribute
    UserInstantiated: UnicodeAttribute


class AppFactsFactory:
    """Factory to create client-specific AppFacts models with dynamic table names."""

    _model_cache = {}

    @classmethod
    def get_model(cls, client: str, auto_create_table: bool = True) -> type[AppFacts]:
        """
        Get an AppFacts model class for a specific client.

        :param client: The client name for table name generation
        :type client: str
        :param auto_create_table: Whether to auto-create the table if it doesn't exist
        :type auto_create_table: bool
        :returns: An AppFacts model class configured for the specified client
        :rtype: type[AppFacts]
        """
        if client not in cls._model_cache:
            model_class = cls._create_client_model(client)
            cls._model_cache[client] = model_class

            # Auto-create table if requested
            if auto_create_table:
                cls._ensure_table_exists(model_class, client)

        return cls._model_cache[client]

    @classmethod
    def _ensure_table_exists(cls, model_class: type, client: str) -> None:
        """
        Ensure the table exists, create it if it doesn't.

        :param model_class: The model class to check/create table for
        :type model_class: type
        :param client: The client name for logging
        :type client: str
        """
        try:
            if not model_class.exists():
                log.info("Creating app table for client: %s", client)
                model_class.create_table(wait=True)
                log.info("Successfully created app table for client: %s", client)
        except Exception as e:
            log.error("Failed to create app table for client %s: %s", client, str(e))
            # Don't raise - let the operation proceed and fail naturally

    @classmethod
    def _create_client_model(cls, client: str):
        """
        Create a new AppFacts model class for a specific client.

        :param client: The client name for table configuration
        :type client: str
        :returns: Dynamic AppFacts model class
        :rtype: type
        """

        class Meta:
            table_name = get_table_name(APP_FACTS, client)  # Client-specific table
            region = util.get_dynamodb_region()
            host = util.get_dynamodb_host()
            read_capacity_units = 1
            write_capacity_units = 1

        def __init__(self, *args, **kwargs):
            """
            Initialize an AppFacts instance.

            :param args: Positional arguments for model initialization
            :param kwargs: Keyword arguments for model attributes
            """
            RegistryModel.__init__(self, *args, **kwargs)

        def __repr__(self) -> str:
            """
            Return string representation of AppFacts.

            :returns: String representation showing ClientPortfolio and AppRegex
            :rtype: str
            """
            return f"AppFacts({self.ClientPortfolio}, {self.AppRegex})"

        # Create dynamic class
        model_attrs = {
            "Meta": Meta,
            "ClientPortfolio": UnicodeAttribute(
                attr_name=CLIENT_PORTFOLIO_KEY, hash_key=True
            ),
            "AppRegex": UnicodeAttribute(attr_name=APP_KEY, range_key=True),
            "Name": UnicodeAttribute(null=True),
            "Environment": UnicodeAttribute(null=True),
            "Account": UnicodeAttribute(null=True),
            "Zone": UnicodeAttribute(null=False),
            "ImageAliases": MapAttribute(null=True),
            "Repository": UnicodeAttribute(null=True),
            "Region": UnicodeAttribute(null=False),
            "Tags": MapAttribute(null=True),
            "EnforceValidation": UnicodeAttribute(null=True),
            "Metadata": MapAttribute(null=True),
            "UserInstantiated": UnicodeAttribute(null=True),
            # Add methods directly
            "__init__": __init__,
            "__repr__": __repr__,
        }

        # Create the dynamic class
        ClientAppFacts = type(f"AppFacts_{client}", (RegistryModel,), model_attrs)

        return ClientAppFacts
