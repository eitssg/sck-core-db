# Facts Fields / And Table Types for the Registry
CLIENT_FACTS = "ClientFacts"
""" Key used to lookup the table name for the ClientFact registry table

    The client facts table name is typically: **core-automation-clients**

    value: ClientFacts
"""
PORTFOLIO_FACTS = "PortfolioFacts"
""" Key used to lookup the table name for the PortfolioFact registry table


    The portfolio facts table name is typically: **core-automation-portfolios**

    value: PortfolioFacts
"""
ZONE_FACTS = "ZoneFacts"
""" Key used to lookup the table name for the ZoneFact registry table

    The zone facts table name is typically: **core-automation-zones**

    value: ZoneFacts
"""
APP_FACTS = "AppFacts"
""" Key used to lookup the table name for the AppFact registry table

    The app facts table name is typically: **core-automation-apps**

    value: AppFacts
"""

# Type Types for the Events and Deployments
EVENTS = "Events"
""" Key used to lookup the table name for the Events registry table

    The events table name is typically: **{client}-core-automation-events**

    value: Events
"""
ITEMS = "Items"
""" Key used to lookup the table name for the Items registry table

    The items table name is typically: **{client}-core-automation-items**

    {client} is the client name

    value: Items
"""

PRN = "prn"
""" Hash key field name for the Items and Events tables

    Value: prn
"""
ITEM_TYPE = "item_type"
""" Field name for the item_type field in the Items table

    Value: item_type
"""
EVENT_TYPE = "event_type"
""" Field name for the event_type field in the Events table

    Value: event_type
"""
# Attributes of Portfolio Facts
APPROVERS = "Approvers"
""" Field name for the Approvers field in the PortfolioFacts table

    Value: Approvers
"""
CONTACTS = "Contacts"
""" Field name for the Contacts field in the PortfolioFacts table

    Value: Contacts
"""
OWNER = "Owner"
""" Field name for the Owner field in the PortfolioFacts table

    Value: Owner
"""
# Attributes of App Facts
REGION = "Region"
""" Field name for the Region field in the AppFacts table

    Value: Region
"""
ENVIRONMENT = "Environment"
""" Field name for the Environment field in the AppFacts table

    Value: Environment
"""
# Registry Model
CLIENT_KEY = "client"
""" Hash Key name used to specify the Client in the Client and Portflio registry tables

    Value: Client
"""
PORTFOLIO_KEY = "portfolio"
""" Range Key name used to lookup the portfolion name int Portfolio registry table for the Client

    Value: Portfolio
"""
CLIENT_PORTFOLIO_KEY = "ClientPortfolio"
""" Hash key name used to lookp apps and zones in the App and Zone registry tables for the Client and Portfolio

    Value: ClientPortfolio
"""
# Registry Range Keys
APP_KEY = "AppRegex"
""" Range Key name used to lookup the app name in the App registry table for the Client and Portfolio

    Value: AppRegex
"""
ZONE_KEY = "Zone"
""" Range Key name used to lookup the zone name in the Zone registry table for the Client and Portfolio

    Value: Zone
"""
NAME = "name"
""" Field name for the name of the object inside the items table

    Value: name
"""
ITEM_TYPE = "item_type"
""" Field name for the item_type field in the Items table

    Possible item types are: portfolio, app, branch, build, component, zone

    Value: item_type
"""
CONTACT_EMAIL = "contact_email"
""" Field name for the contact_email field in the Items table

    Value: contact_email
"""
# MapAttribute fields
# These are fields in the items table "core-automation-items"
PARENT_PRN = "parent_prn"
""" Field name for the parent_prn field in the Items table

    Value: parent_prn
"""
PORTFOLIO_PRN = "portfolio_prn"
""" Field name for the portfolio_prn field in the Items table.

    The parent_prn is the item record is the constant value "prn".

    Value: portfolio_prn
"""
APP_PRN = "app_prn"
""" Field name for the app_prn field in the Items table.

    An App belongs to a Portfolio.  The parent_prn and portfolio_prn are the same.

    Value: app_prn
"""
BRANCH_PRN = "branch_prn"
""" Field name for the branch_prn field in the Items table.

    A Branch belongs to an App.  The parent_prn is the app_prn and are the same.

    Value: branch_prn
"""
BUILD_PRN = "build_prn"
""" Field name for the build_prn field in the Items table.

    A Build belongs to a Branch.  The parent_prn is the branch_prn and are the same.

    Value: build_prn
"""
COMPONENT_PRN = "component_prn"
""" Field name for the component_prn field in the Items table.

    A Component belongs to a Build.  The parent_prn is the build_prn and are the same.

    Value: component_prn
"""
SHORT_NAME = "short_name"
""" Field name for the short_name field in the Items table.

    The Branch Short Name is calulated to make it possible to use as an AWS resource ID.

    Since your repository branch can be any string you like, this name is generated and
    used as part of Resource ID's.

    Value: short_name
"""
RELEASED_BUILD_PRN = "released_build_prn"
""" Field name for the released_build_prn field in the Items table for the Branch records.

    When a build is released, it's expectted that the core_api will set the released_build_prn
    on the Branch item record.

    Value: released_build_prn
"""
RELEASED_BUILD = "released_build"
""" Field name for the released_build field in the Items table for the Branch records.

    When a build is released, it's expectted that the core_api will set the released_build_prn
    on the Branch item record.

    Value: released_build
"""
# Fields For build and component releases
STATUS = "status"
""" Field name for the status field in the Events table.

    Value: status
"""
# Date fields
UPDATED_AT = "updated_at"
""" Field name for the updated_at date field in both the Items and Events tables.

    Value: updated_at
"""
CREATED_AT = "created_at"
""" Field name for the created_at date field in both the Items and Events tables.

    Value: created_at
"""
# Query tags (for pagenation)
EARLIEST_TIME = "earliest_time"
LATEST_TIME = "latest_time"
DATA_PAGINATOR = "data_paginator"
SORT = "sort"
LIMIT = "limit"
ASCENDING = "ascending"
