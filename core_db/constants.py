"""Constants for field names and keys for the Core-DB database tables."""

# Facts Fields / And Table Types for the Registry
CLIENT_FACTS = "ClientFacts"
"""
Key used to lookup the table name for the ClientFact registry table.

The client facts table name is typically: **core-automation-clients**

:value: ClientFacts
"""

PORTFOLIO_FACTS = "PortfolioFacts"
"""
Key used to lookup the table name for the PortfolioFact registry table.

The portfolio facts table name is typically: **core-automation-portfolios**

:value: PortfolioFacts
"""

ZONE_FACTS = "ZoneFacts"
"""
Key used to lookup the table name for the ZoneFact registry table.

The zone facts table name is typically: **core-automation-zones**

:value: ZoneFacts
"""

APP_FACTS = "AppFacts"
"""
Key used to lookup the table name for the AppFact registry table.

The app facts table name is typically: **core-automation-apps**

:value: AppFacts
"""

# Type Types for the Events and Deployments
EVENTS = "Events"
"""
Key used to lookup the table name for the Events registry table.

The events table name is typically: **{client}-core-automation-events**

:value: Events
"""

ITEMS = "Items"
"""
Key used to lookup the table name for the Items registry table.

The items table name is typically: **{client}-core-automation-items**

{client} is the client name

:value: Items
"""

PRN = "prn"
"""
Hash key field name for the Items and Events tables.

:value: prn
"""

ITEM_TYPE = "item_type"
"""
Field name for the item_type field in the Items table.

:value: item_type
"""

EVENT_TYPE = "event_type"
"""
Field name for the event_type field in the Events table.

:value: event_type
"""

# Attributes of Portfolio Facts
APPROVERS = "Approvers"
"""
Field name for the Approvers field in the PortfolioFacts table.

:value: Approvers
"""

CONTACTS = "Contacts"
"""
Field name for the Contacts field in the PortfolioFacts table.

:value: Contacts
"""

OWNER = "Owner"
"""
Field name for the Owner field in the PortfolioFacts table.

:value: Owner
"""

# Attributes of App Facts
REGION = "Region"
"""
Field name for the Region field in the AppFacts table.

:value: Region
"""

ENVIRONMENT = "Environment"
"""
Field name for the Environment field in the AppFacts table.

:value: Environment
"""

# Registry Model
CLIENT_KEY = "Client"
"""
Hash Key name used to specify the Client in the Client and Portfolio registry tables.

:value: Client
"""

PORTFOLIO_KEY = "Portfolio"
"""
Range Key name used to lookup the portfolio name in Portfolio registry table for the Client.

:value: Portfolio
"""

CLIENT_PORTFOLIO_KEY = "ClientPortfolio"
"""
Hash key name used to lookup apps and zones in the App and Zone registry tables for the Client and Portfolio.

:value: ClientPortfolio
"""

# Registry Range Keys
APP_KEY = "AppRegex"
"""
Range Key name used to lookup the app name in the App registry table for the Client and Portfolio.

:value: AppRegex
"""

ZONE_KEY = "Zone"
"""
Range Key name used to lookup the zone name in the Zone registry table for the Client and Portfolio.

:value: Zone
"""

# Whereas registry fields are in PascalCase, the fields in the Items and Events tables are in snake_case
NAME = "name"
"""
Field name for the name of the object inside the items table.

:value: name
"""

CONTACT_EMAIL = "contact_email"
"""
Field name for the contact_email field in the Items table.

:value: contact_email
"""

# MapAttribute fields
# These are fields in the items table "core-automation-items"
PARENT_PRN = "parent_prn"
"""
Field name for the parent_prn field in the Items table.

:value: parent_prn
"""

PORTFOLIO_PRN = "portfolio_prn"
"""
Field name for the portfolio_prn field in the Items table.

The parent_prn is the item record is the constant value "prn".

:value: portfolio_prn
"""

APP_PRN = "app_prn"
"""
Field name for the app_prn field in the Items table.

An App belongs to a Portfolio. The parent_prn and portfolio_prn are the same.

:value: app_prn
"""

BRANCH_PRN = "branch_prn"
"""
Field name for the branch_prn field in the Items table.

A Branch belongs to an App. The parent_prn is the app_prn and are the same.

:value: branch_prn
"""

BUILD_PRN = "build_prn"
"""
Field name for the build_prn field in the Items table.

A Build belongs to a Branch. The parent_prn is the branch_prn and are the same.

:value: build_prn
"""

COMPONENT_PRN = "component_prn"
"""
Field name for the component_prn field in the Items table.

A Component belongs to a Build. The parent_prn is the build_prn and are the same.

:value: component_prn
"""

SHORT_NAME = "short_name"
"""
Field name for the short_name field in the Items table.

The Branch Short Name is calculated to make it possible to use as an AWS resource ID.

Since your repository branch can be any string you like, this name is generated and
used as part of Resource ID's.

:value: short_name
"""

RELEASED_BUILD_PRN = "released_build_prn"
"""
Field name for the released_build_prn field in the Items table for the Branch records.

When a build is released, it's expected that the core_api will set the released_build_prn
on the Branch item record.

:value: released_build_prn
"""

RELEASED_BUILD = "released_build"
"""
Field name for the released_build field in the Items table for the Branch records.

When a build is released, it's expected that the core_api will set the released_build_prn
on the Branch item record.

:value: released_build
"""

# Fields For build and component releases
STATUS = "status"
"""
Field name for the status field in the Events table.

:value: status
"""

# Date fields
UPDATED_AT = "updated_at"
"""
Field name for the updated_at date field in both the Items and Events tables.

:value: updated_at
"""

CREATED_AT = "created_at"
"""
Field name for the created_at date field in both the Items and Events tables.

:value: created_at
"""

# Query tags (for pagination)
EARLIEST_TIME = "earliest_time"
"""
Field name for the earliest_time query parameter.

:value: earliest_time
"""

LATEST_TIME = "latest_time"
"""
Field name for the latest_time query parameter.

:value: latest_time
"""

DATA_PAGINATOR = "data_paginator"
"""
Field name for the data_paginator query parameter.

:value: data_paginator
"""

SORT = "sort"
"""
Field name for the sort query parameter.

:value: sort
"""

LIMIT = "limit"
"""
Field name for the limit query parameter.

:value: limit
"""

ASCENDING = "ascending"
"""
Field name for the ascending query parameter.

:value: ascending
"""
