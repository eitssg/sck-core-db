"""Constants for field names and keys for the Core-DB database tables.

This module defines all the constant values used throughout the Core-DB system
for DynamoDB field names, table keys, query parameters, and table names.
Constants are organized by their usage context and table relationships.

The constants follow different naming conventions based on their context:
- **Registry Tables**: Use PascalCase for field names (e.g., "Client", "Portfolio")
- **Items/Events Tables**: Use snake_case for field names (e.g., "item_type", "created_at")
- **Query Parameters**: Use snake_case for API parameters (e.g., "limit", "sort")
"""

# =============================================================================
# Primary Key Constants
# =============================================================================

PRN = "prn"
"""Hash key field name for the Items and Events tables.
    
The PRN (Platform Resource Name) serves as the unique identifier for all
deployment items and events in the core automation system.
"""

ITEM_TYPE = "item_type"
"""Field name for the item_type field in the Items table.

Specifies the type of deployment item (portfolio, app, branch, build, component).
Used for filtering and categorizing items in queries.
"""

EVENT_TYPE = "event_type"
"""Field name for the event_type field in the Events table.

Specifies the type of deployment event (deploy_start, deploy_success, deploy_failure, etc.).
Used for filtering and categorizing events in queries.
"""

# =============================================================================
# Portfolio Facts Attributes (PascalCase)
# =============================================================================

APPROVERS = "Approvers"
"""Field name for the Approvers field in the PortfolioFactsModel table.

Contains a list of users who can approve deployments for this portfolio.
Used for deployment authorization workflows.
"""

CONTACTS = "Contacts"
"""Field name for the Contacts field in the PortfolioFactsModel table.

Contains contact information for the portfolio including technical and business contacts.
Used for notifications and escalation procedures.
"""

OWNER = "Owner"
"""Field name for the Owner field in the PortfolioFactsModel table.

Identifies the primary owner responsible for the portfolio.
Used for accountability and access control decisions.
"""

# =============================================================================
# App Facts Attributes (PascalCase)
# =============================================================================

REGION = "Region"
"""Field name for the Region field in the AppFactsModel table.

Specifies the AWS region where the application is deployed.
Used for region-specific deployment logic and resource placement.
"""

ENVIRONMENT = "Environment"
"""Field name for the Environment field in the AppFactsModel table.

Specifies the deployment environment (dev, staging, prod, etc.).
Used for environment-specific configuration and deployment policies.
"""

# =============================================================================
# Registry Model Keys (PascalCase)
# =============================================================================

CLIENT_KEY = "Client"
"""Hash Key name used to specify the Client in the Client and Portfolio registry tables.

The client identifier represents an AWS Organization or tenant in the system.
Used as the primary partition key for client-specific data isolation.
"""

PORTFOLIO_KEY = "Portfolio"
"""Range Key name used to lookup the portfolio name in Portfolio registry table for the Client.

Combined with CLIENT_KEY, forms the composite primary key for portfolio records.
Used to identify specific portfolios within a client organization.
"""


# =============================================================================
# Registry Range Keys (PascalCase)
# =============================================================================

APP_KEY = "AppRegex"
"""Range Key name used to lookup the app name in the App registry table for the Client and Portfolio.

Uses regex pattern matching for flexible app name lookups within portfolios.
Combined with CLIENT_PORTFOLIO_KEY for app identification.
"""

ZONE_KEY = "Zone"
"""Range Key name used to lookup the zone name in the Zone registry table for the Client and Portfolio.

Combined with CLIENT_PORTFOLIO_KEY to identify specific deployment zones.
Zones represent deployment boundaries with specific AWS accounts and regions.
"""

# =============================================================================
# Items Table Fields (snake_case)
# =============================================================================

NAME = "name"
"""Field name for the name of the object inside the items table.

Human-readable name for deployment items (portfolios, apps, branches, etc.).
Used for display purposes and identification in logs and UIs.
"""

CONTACT_EMAIL = "contact_email"
"""Field name for the contact_email field in the Items table.

Primary contact email for the deployment item owner or responsible team.
Used for notifications, alerts, and communication.
"""

# =============================================================================
# PRN Hierarchy Fields (snake_case)
# =============================================================================

PARENT_PRN = "parent_prn"
"""Field name for the parent_prn field in the Items table.

References the PRN of the parent item in the deployment hierarchy.
Used to build the hierarchical relationship between deployment items.
"""

PORTFOLIO_PRN = "portfolio_prn"
"""Field name for the portfolio_prn field in the Items table.

References the portfolio that contains this item.
For portfolio items, this is the same as the PRN itself.
"""

APP_PRN = "app_prn"
"""Field name for the app_prn field in the Items table.

References the app that contains this item.
An App belongs to a Portfolio. For app items, parent_prn and portfolio_prn are the same.
"""

BRANCH_PRN = "branch_prn"
"""Field name for the branch_prn field in the Items table.

References the branch that contains this item.
A Branch belongs to an App. For branch items, parent_prn is the app_prn.
"""

BUILD_PRN = "build_prn"
"""Field name for the build_prn field in the Items table.

References the build that contains this item.
A Build belongs to a Branch. For build items, parent_prn is the branch_prn.
"""

COMPONENT_PRN = "component_prn"
"""Field name for the component_prn field in the Items table.

References the component for items that belong to components.
A Component belongs to a Build. For component items, parent_prn is the build_prn.
"""

# =============================================================================
# Special Item Fields (snake_case)
# =============================================================================

SHORT_NAME = "short_name"
"""Field name for the short_name field in the Items table.

The Branch Short Name is calculated to make it possible to use as an AWS resource ID.
Since repository branch names can contain special characters, this generates
a sanitized version suitable for AWS resource naming.
"""

RELEASED_BUILD_PRN = "released_build_prn"
"""Field name for the released_build_prn field in the Items table for the Branch records.

When a build is released, the core_api sets the released_build_prn on the Branch item record.
This tracks which build is currently released for the branch.
"""

RELEASED_BUILD = "released_build"
"""Field name for the released_build field in the Items table for the Branch records.

When a build is released, the core_api sets the released_build on the Branch item record.
This contains additional metadata about the released build.
"""

# =============================================================================
# Event and Status Fields (snake_case)
# =============================================================================

STATUS = "status"
"""Field name for the status field in the Events table.

Indicates the status of deployment events (success, failure, in_progress, etc.).
Used for tracking deployment progress and health monitoring.
"""

# =============================================================================
# Timestamp Fields (snake_case)
# =============================================================================

UPDATED_AT = "updated_at"
"""Field name for the updated_at date field in both the Items and Events tables.

Timestamp indicating when the record was last modified.
Automatically maintained by the system for audit tracking.
"""

CREATED_AT = "created_at"
"""Field name for the created_at date field in both the Items and Events tables.

Timestamp indicating when the record was first created.
Set once during record creation and never modified.
"""

# =============================================================================
# Query Parameters (snake_case)
# =============================================================================

EARLIEST_TIME = "earliest_time"
"""Field name for the earliest_time query parameter.

Used in time-based queries to specify the start of a time range.
Typically used for filtering events and items by creation or update time.
"""

LATEST_TIME = "latest_time"
"""Field name for the latest_time query parameter.

Used in time-based queries to specify the end of a time range.
Combined with earliest_time for comprehensive time range filtering.
"""

DATA_PAGINATOR = "data_paginator"
"""Field name for the data_paginator query parameter.

Contains pagination token for continuing queries across multiple pages.
Used with DynamoDB's LastEvaluatedKey for efficient result pagination.
"""

SORT = "sort"
"""Field name for the sort query parameter.

Specifies the field to sort results by in queries.
Combined with ASCENDING parameter to control sort direction.
"""

LIMIT = "limit"
"""Field name for the limit query parameter.

Specifies the maximum number of items to return in a single query.
Used for pagination and performance optimization.
"""

ASCENDING = "ascending"
"""Field name for the ascending query parameter.

Boolean flag controlling sort direction when SORT parameter is specified.
True for ascending order, False for descending order.
"""

# =============================================================================
# Table Names
# =============================================================================

PROFILES = "profiles"
"""Name of the Profiles table in the database.

Table containing user and system configuration profiles.
Used for storing user preferences, system settings, and configuration templates.
"""
