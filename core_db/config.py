"""Configuration utilities for Core Automation DynamoDB table naming.

This module provides functions and constants for constructing DynamoDB table names
based on client, automation scope, and table type. Table names are generated using
standard conventions and may be customized via environment variables.

The table naming convention follows the pattern:
- **Client-agnostic tables**: `{prefix}{scope}-{table-type}`
- **Client-specific tables**: `{prefix}{client}-{scope}-{table-type}`

Where:
- `prefix`: Optional automation scope prefix from environment
- `client`: Client organization identifier (e.g., "acme", "enterprise")
- `scope`: Core automation scope (typically "core-automation")
- `table-type`: Specific table type (e.g., "clients", "portfolios", "zones")

Examples:
    >>> # Client-agnostic table (clients registry)
    >>> get_table_name(ClientFactsModel)
    'core-automation-clients'

    >>> # Client-specific table (portfolios for ACME)
    >>> get_table_name(PortfolioFactsModel, client="acme")
    'acme-core-automation-portfolios'

    >>> # With automation scope prefix
    >>> # (when AUTOMATION_SCOPE=dev- is set)
    >>> get_table_name(ZoneFactsModel, client="acme")
    'dev-acme-core-automation-zones'
"""

from typing import Optional
import core_framework as util
from core_framework.constants import V_CORE_AUTOMATION


def get_dynamodb_host() -> str:
    """Get the DynamoDB host URL for table connections.

    Uses the AWS_DYNAMODB_HOST environment variable or defaults to the local
    DynamoDB development endpoint.

    Returns:
        str: DynamoDB host URL

    Environment Variables:
        AWS_DYNAMODB_HOST: Custom DynamoDB endpoint URL

    Examples:
        >>> # Default local development endpoint
        >>> get_dynamodb_host()
        'http://localhost:8000'

        >>> # When AWS_DYNAMODB_HOST=https://dynamodb.us-west-2.amazonaws.com
        >>> get_dynamodb_host()
        'https://dynamodb.us-west-2.amazonaws.com'
    """
    return util.get_dynamodb_host() or "http://localhost:8000"


def get_region() -> str:
    """Get the AWS region for DynamoDB table operations.

    Uses the AWS_DEFAULT_REGION environment variable or defaults to us-east-1.

    Returns:
        str: AWS region code

    Environment Variables:
        AWS_DEFAULT_REGION: AWS region for DynamoDB operations

    Examples:
        >>> # Default region
        >>> get_region()
        'us-east-1'

        >>> # When AWS_DEFAULT_REGION=us-west-2
        >>> get_region()
        'us-west-2'
    """
    return util.get_dynamodb_region() or "us-east-1"


def get_table_name(model: type, client: str | None = None, default: Optional[str] | None = None) -> str:
    """Generate DynamoDB table name for the specified model type and client.

    Table names are constructed using standard conventions and may be customized
    via environment variables. The naming pattern depends on whether the table
    is client-specific or client-agnostic.

    Args:
        model (type): The PynamoDB model class to get the table name for.
            Must be one of the supported model types (e.g., ClientFactsModel,
            PortfolioFactsModel, ZoneFactsModel, etc.)
        client (str, optional): The client name for table naming. If None,
            uses the default client from environment variables or "client".
            Required for client-specific tables.
        default (str, optional): Default value to return if the table type
            is not found in the mapping. If None and model is not found,
            raises ValueError.

    Returns:
        str: The resolved DynamoDB table name following the naming convention

    Raises:
        ValueError: If the model class name is not found in the supported
            table mapping and no default is provided

    Environment Variables:
        AUTOMATION_SCOPE: Optional prefix for all table names
        CLIENT: Default client name when client parameter is None

    Note:
        **Supported Model Types**:

        - **ClientFactsModel**: Client registry (client-agnostic)
        - **ZoneFactsModel**: Zone configurations (client-specific)
        - **PortfolioFactsModel**: Portfolio definitions (client-specific)
        - **AppFactsModel**: Application registry (client-specific)
        - **ItemModel**: Deployment items (client-specific)
        - **EventModel**: Deployment events (client-specific)
        - **ProfileModel**: User configurations (client-specific)

        **Table Naming Patterns**:

        - **Client Registry**: `{prefix}core-automation-clients`
        - **Client Tables**: `{prefix}{client}-core-automation-{type}`

        Where `{prefix}` comes from AUTOMATION_SCOPE environment variable.

    Examples:
        >>> # Client registry table (no client needed)
        >>> get_table_name(ClientFactsModel)
        'core-automation-clients'

        >>> # Client-specific portfolio table
        >>> get_table_name(PortfolioFactsModel, client="acme")
        'acme-core-automation-portfolios'

        >>> # Zone table for enterprise client
        >>> get_table_name(ZoneFactsModel, client="enterprise")
        'enterprise-core-automation-zones'

        >>> # With automation scope prefix (dev environment)
        >>> # When AUTOMATION_SCOPE="dev-"
        >>> get_table_name(AppFactsModel, client="acme")
        'dev-acme-core-automation-apps'

        >>> # Using default fallback
        >>> get_table_name(UnknownModel, default="fallback-table")
        'fallback-table'

        >>> # Error case - unknown model without default
        >>> try:
        ...     get_table_name(UnknownModel)
        ... except ValueError as e:
        ...     print(f"Error: {e}")
        Error: Table name not found for UnknownModel
    """
    if not client:
        client = "core"

    prefix = util.get_automation_scope() or ""

    # The key of this table is the model class name
    tables = {
        #
        # Global tables
        #
        # OAuth Authorizations Table
        "AuthorizationsModel": f"{prefix}core-{V_CORE_AUTOMATION}-oauth",
        "RateLimitsModel": f"{prefix}core-{V_CORE_AUTOMATION}-oauth",
        "OAuthTableModel": f"{prefix}core-{V_CORE_AUTOMATION}-oauth",
        "ForgotPasswordModel": f"{prefix}core-{V_CORE_AUTOMATION}-oauth",
        # Passkeys / WebAuthn Table
        "PassKeysModel": f"{prefix}core-{V_CORE_AUTOMATION}-passkeys",
        # Client Facts is the base tenant registration table (no "client" prefix)
        "ClientFactsModel": f"{prefix}core-{V_CORE_AUTOMATION}-clients",
        #
        # Tenant aware tables
        #
        # Profiles for user-defined configurations
        "ProfileModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-profiles",
        # AWS Account(s) and zone names
        "ZoneFactsModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-zones",
        # Portfolio BizApps / Deployment App targets
        "PortfolioFactsModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-portfolios",
        # The application zone selectors (App Registry)
        "AppFactsModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-apps",
        # Components and Items deployed to AWS
        "ItemModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
        # All the portfolio deployment items
        "PortfolioModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
        # All the app deployments items
        "AppModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
        # All branch deployment items
        "BranchModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
        # All build deployment items
        "BuildModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
        # All component deployment items
        "ComponentModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-items",
        # All the events that are generated during deployment
        "EventModel": f"{prefix}{client}-{V_CORE_AUTOMATION}-events",
    }

    # We may also want to first check if an environment variable is set
    # and if so, use that value instead of the default

    table = tables.get(model.__name__, default)
    if table is None:
        raise ValueError(f"Table name not found for {model.__name__}")

    return table
