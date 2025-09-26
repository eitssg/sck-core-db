"""The Facter module provides registry data aggregation and view generation functionality.

This module combines data from multiple registry tables to create a unified view for
CloudFormation template rendering. The Facter system aggregates configuration data
across clients, portfolios, zones, and apps to provide complete deployment context.

Key Components:
    - **get_facts()**: Main function to retrieve complete fact aggregation
    - **get_client_facts()**: Client-specific configuration and metadata
    - **get_portfolio_facts()**: Portfolio-level settings and contacts
    - **get_zone_facts()**: Zone configuration including AWS account details
    - **get_app_facts()**: Application-specific deployment parameters
    - **FactsActions**: Action class for fact retrieval operations

Data Sources:
    The Facter module combines data from these registry tables:
    - **core-automation-clients**: Client configuration and global settings
    - **core-automation-portfolios**: Portfolio metadata and contact information
    - **core-automation-zones**: Zone configuration with AWS account details
    - **core-automation-apps**: Application deployment settings and parameters

Features:
    - **Multi-table Aggregation**: Combines related data across registry tables
    - **Jinja2 Integration**: Provides render context for CloudFormation templates
    - **Hierarchical Context**: Builds complete deployment context from client to app
    - **AWS Integration**: Includes AWS account, region, and resource configuration
    - **Security Context**: Aggregates security groups, VPC, and network configurations

Use Cases:
    - **CloudFormation Rendering**: Provides complete context for template generation
    - **Deployment Configuration**: Supplies all necessary parameters for deployments
    - **Environment Setup**: Configures AWS resources based on aggregated facts
    - **Security Configuration**: Applies security rules and network configurations

Examples:
    >>> from core_db.facter import get_facts, get_client_facts, get_zone_facts

    >>> # Get complete facts for deployment
    >>> facts = get_facts(
    ...     client="acme",
    ...     portfolio="web-services",
    ...     zone="production",
    ...     app="api"
    ... )
    >>> print(facts["Client"])        # "acme"
    >>> print(facts["AwsAccountId"])  # "738499099231"
    >>> print(facts["Region"])       # "us-west-2"

    >>> # Get client-specific facts
    >>> client_facts = get_client_facts("acme")
    >>> print(client_facts["ResourceNamespace"])  # "core"
    >>> print(client_facts["Tags"]["CostCenter"])  # "COST123"

    >>> # Get zone facts with AWS configuration
    >>> zone_facts = get_zone_facts("acme", "production")
    >>> print(zone_facts["AwsAccountId"])    # "738499099231"
    >>> print(zone_facts["AwsRegion"])       # "us-west-2"
    >>> print(zone_facts["Environment"])     # "production"

    >>> # Get zone facts by AWS account ID
    >>> account_facts = get_zone_facts_by_account_id("738499099231")
    >>> print(account_facts["AccountName"])  # "ACME Production Account"

    >>> # Get portfolio facts
    >>> portfolio_facts = get_portfolio_facts("acme", "web-services")
    >>> print(portfolio_facts["Owner"]["Email"])    # "owner@acme.com"
    >>> print(portfolio_facts["Contacts"][0]["Email"])  # "contact@acme.com"

    >>> # Get app-specific facts
    >>> app_facts = get_app_facts("acme", "web-services", "api")
    >>> print(app_facts["Repository"])      # "https://github.com/acme/api.git"
    >>> print(app_facts["Approvers"][0]["Email"])  # "approver@acme.com"

Fact Structure Examples:
    The aggregated facts include comprehensive configuration data::

        # Basic identification and AWS configuration
        facts = {
            "Client": "acme",
            "Zone": "acme-web-production-zone",
            "AccountName": "ACME Production Account",
            "AwsAccountId": "738499099231",
            "Environment": "production",
            "Region": "usw2",
            "AwsRegion": "us-west-2",
            "AzCount": 3,
            "ResourceNamespace": "core"
        }

        # KMS configuration for encryption
        facts["Kms"] = {
            "AwsAccountId": "624172648832",
            "DelegateAwsAccountIds": ["738499099231"],
            "KmsKeyArn": "arn:aws:kms:us-west-2:624172648832:key/12345",
            "KmsKey": "alias/acme-production"
        }

        # Network configuration
        facts["VpcAliases"] = {
            "public": "Vpc1",
            "private": "Vpc1"
        }
        facts["SubnetAliases"] = {
            "public": "PublicSubnet",
            "app": "PrivateSubnet",
            "private": "PrivateSubnet"
        }

        # Security configuration
        facts["SecurityAliases"] = {
            "public-internet": [
                {"Type": "cidr", "Value": "0.0.0.0/0", "Description": "Internet"}
            ],
            "intranet": [
                {"Type": "cidr", "Value": "10.0.0.0/8", "Description": "Corporate network"}
            ]
        }

        # AMI configuration
        facts["ImageAliases"] = {
            "amazon-linux-2": "ami-0e2e44c03b85f58b3",
            "amazon-linux-2-CIS": "ami-0a11473dc50b85280"
        }

        # Tags for resource tagging
        facts["Tags"] = {
            "AppGroup": "WebServices",
            "CostCenter": "COST123",
            "Environment": "production"
        }

        # Contact information
        facts["Owner"] = {
            "Email": "owner@acme.com",
            "Name": "System Owner"
        }
        facts["Contacts"] = [
            {
                "Email": "contact@acme.com",
                "Name": "Technical Contact",
                "Enabled": True
            }
        ]

        # Approval workflow
        facts["Approvers"] = [
            {
                "Sequence": 1,
                "Email": "approver@acme.com",
                "Name": "Lead Developer",
                "Enabled": True,
                "DependsOn": []
            }
        ]

CloudFormation Integration:
    Facts are used as Jinja2 template context for CloudFormation generation::

        # In CloudFormation template (YAML)
        Resources:
          MyVPC:
            Type: AWS::EC2::VPC
            Properties:
              CidrBlock: 10.0.0.0/16
              Tags:
                - Key: AppGroup
                  Value: "{{ Tags.AppGroup }}"
                - Key: CostCenter
                  Value: "{{ Tags.CostCenter }}"

          MyLambda:
            Type: AWS::Lambda::Function
            Properties:
              KmsKeyArn: "{{ Kms.KmsKeyArn }}"
              Environment:
                Variables:
                  AWS_ACCOUNT_ID: "{{ AwsAccountId }}"
                  ENVIRONMENT: "{{ Environment }}"

Usage Patterns:
    **Deployment Context**: Use get_facts() for complete deployment parameter aggregation

    **Template Rendering**: Pass facts as Jinja2 context for CloudFormation templates

    **Environment Configuration**: Use zone facts for AWS account and region setup

    **Security Setup**: Use security aliases for security group and network ACL configuration

    **Resource Tagging**: Apply consistent tags across all resources using facts["Tags"]

Data Hierarchy:
    Facts are aggregated in hierarchical order from most general to most specific:
    1. **Client Facts**: Global client configuration and defaults
    2. **Portfolio Facts**: Portfolio-specific settings and contacts
    3. **Zone Facts**: Environment and AWS account configuration
    4. **App Facts**: Application-specific parameters and repository settings

Caching and Performance:
    - **Registry Queries**: Facts are built from live registry table queries
    - **Aggregation Logic**: Combines data with proper precedence rules
    - **Template Context**: Optimized for CloudFormation template rendering performance
    - **Client Isolation**: Each client's facts are independently retrieved and cached

Error Handling:
    All fact retrieval operations may raise:
    - NotFoundException: Client, portfolio, zone, or app not found in registry
    - BadRequestException: Invalid parameters or malformed identifiers
    - UnauthorizedException: Missing authentication for registry access
    - ForbiddenException: Insufficient permissions for client data access

Integration Points:
    - **CloudFormation Templates**: Primary consumer for template variable substitution
    - **Deployment Pipelines**: Provides configuration context for deployment operations
    - **Resource Provisioning**: Supplies AWS account and region information
    - **Security Configuration**: Provides network and security rule definitions

Note:
    The Facter module serves as the central configuration aggregation point for the
    entire Simple Cloud Kit system. It ensures consistent configuration data is
    available for all deployment and provisioning operations across the platform.
"""

from .facter import (
    get_facts,
    get_client_facts,
    get_app_facts,
    get_portfolio_facts,
    get_zone_facts,
    get_zone_facts_by_account_id,
)

__all__ = [
    "get_client_facts",
    "get_portfolio_facts",
    "get_zone_facts",
    "get_zone_facts_by_account_id",
    "get_app_facts",
    "get_facts",
]
