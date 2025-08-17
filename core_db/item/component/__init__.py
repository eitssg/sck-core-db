"""Component item management for the core-automation-items table.

This module provides comprehensive component item management functionality including
actions, models, and data validation for component records in the DynamoDB items table.
Component items represent individual deployable artifacts within builds, such as Lambda
functions, containers, or infrastructure components.

Key Components:
    - **ComponentActions**: CRUD operations for component items with validation
    - **ComponentModel**: PynamoDB model for DynamoDB component table operations
    - **ComponentRecord**: Pydantic model for API serialization and validation
    - **Component validation**: Business rules and constraints for component data

Features:
    - **Hierarchical Organization**: Component items are the leaf nodes in the deployment hierarchy
    - **Client Isolation**: Each client has their own component namespace within builds
    - **Deployment Tracking**: Individual component deployment status and configuration
    - **Resource Management**: AWS resource tracking and lifecycle management
    - **Artifact Association**: Direct linkage to build artifacts and deployment packages
    - **Audit Trail**: Automatic creation/modification timestamp tracking

Component Hierarchy:
    ```
    Portfolio (great-great-grandparent)
    ├── App (great-grandparent)
    │   ├── Branch (grandparent)
    │   │   ├── Build (parent)
    │   │   │   └── Component (this module - leaf node)
    ```

Schema Structure:
    The component schema in the core-automation-items table includes:
    - **prn**: Primary key in format "component:client:portfolio:app:branch:build:component_name"
    - **name**: Human-readable component display name
    - **build_prn**: Reference to parent build
    - **component_type**: Type of component (lambda, container, infrastructure, etc.)
    - **artifact_location**: S3 or ECR location of deployable artifact
    - **deployment_status**: Current deployment status (pending, deploying, deployed, failed)
    - **aws_resources**: List of AWS resources created by this component
    - **configuration**: Component-specific configuration and parameters
    - **health_check**: Health check endpoint and configuration
    - **deployed_at**: Timestamp when component was last deployed
    - **created_at/updated_at**: Automatic audit timestamps

Examples:
    >>> from core_db.item.component import ComponentActions, ComponentRecord

    >>> # Create a Lambda function component
    >>> result = ComponentActions.create(
    ...     prn="component:acme:web-services:api:main:123:user-service",
    ...     name="User Service Lambda",
    ...     build_prn="build:acme:web-services:api:main:123",
    ...     component_type="lambda",
    ...     artifact_location="s3://acme-artifacts/builds/123/user-service.zip",
    ...     deployment_status="pending",
    ...     configuration={
    ...         "runtime": "python3.9",
    ...         "memory": 512,
    ...         "timeout": 30,
    ...         "environment_variables": {
    ...             "DB_HOST": "rds.example.com",
    ...             "LOG_LEVEL": "INFO"
    ...         }
    ...     }
    ... )

    >>> # Create a container component
    >>> ComponentActions.create(
    ...     prn="component:acme:web-services:api:main:123:web-frontend",
    ...     name="Web Frontend Container",
    ...     build_prn="build:acme:web-services:api:main:123",
    ...     component_type="container",
    ...     artifact_location="123456789012.dkr.ecr.us-west-2.amazonaws.com/acme/web-frontend:v123",
    ...     deployment_status="pending",
    ...     configuration={
    ...         "port": 8080,
    ...         "cpu": 256,
    ...         "memory": 512,
    ...         "desired_count": 2,
    ...         "health_check_path": "/health"
    ...     }
    ... )

    >>> # Create an infrastructure component
    >>> ComponentActions.create(
    ...     prn="component:acme:web-services:api:main:123:database",
    ...     name="RDS Database",
    ...     build_prn="build:acme:web-services:api:main:123",
    ...     component_type="infrastructure",
    ...     artifact_location="s3://acme-artifacts/builds/123/database-template.yaml",
    ...     deployment_status="pending",
    ...     configuration={
    ...         "engine": "postgresql",
    ...         "engine_version": "13.7",
    ...         "instance_class": "db.t3.medium",
    ...         "allocated_storage": 100,
    ...         "backup_retention": 7
    ...     }
    ... )

    >>> # Retrieve component data
    >>> component_data = ComponentActions.get(
    ...     prn="component:acme:web-services:api:main:123:user-service"
    ... )

    >>> # Convert to API response format
    >>> component_record = ComponentRecord.from_dynamodb(component_data.data)
    >>> api_response = component_record.model_dump()

    >>> # List all components in a build
    >>> components = ComponentActions.list_by_build("build:acme:web-services:api:main:123")

    >>> # Update deployment status during deployment
    >>> ComponentActions.update(
    ...     prn="component:acme:web-services:api:main:123:user-service",
    ...     deployment_status="deploying",
    ...     deployment_started_at="2025-01-15T14:30:00Z"
    ... )

    >>> # Complete deployment with AWS resources
    >>> ComponentActions.update(
    ...     prn="component:acme:web-services:api:main:123:user-service",
    ...     deployment_status="deployed",
    ...     deployed_at="2025-01-15T14:35:00Z",
    ...     aws_resources=[
    ...         {
    ...             "type": "AWS::Lambda::Function",
    ...             "logical_id": "UserServiceFunction",
    ...             "physical_id": "acme-user-service-function",
    ...             "arn": "arn:aws:lambda:us-west-2:123456789012:function:acme-user-service"
    ...         },
    ...         {
    ...             "type": "AWS::IAM::Role",
    ...             "logical_id": "UserServiceRole",
    ...             "physical_id": "acme-user-service-role",
    ...             "arn": "arn:aws:iam::123456789012:role/acme-user-service-role"
    ...         }
    ...     ],
    ...     health_check={
    ...         "url": "https://api.acme.com/user/health",
    ...         "last_check": "2025-01-15T14:40:00Z",
    ...         "status": "healthy",
    ...         "response_time": 150
    ...     }
    ... )

    >>> # Mark component deployment as failed
    >>> ComponentActions.update(
    ...     prn="component:acme:web-services:api:main:123:database",
    ...     deployment_status="failed",
    ...     deployment_error={
    ...         "code": "INSUFFICIENT_PERMISSIONS",
    ...         "message": "IAM role lacks RDS creation permissions",
    ...         "timestamp": "2025-01-15T14:32:00Z"
    ...     }
    ... )

    >>> # Create serverless component
    >>> ComponentActions.create(
    ...     prn="component:enterprise:platform:auth:main:200:api-gateway",
    ...     name="Authentication API Gateway",
    ...     build_prn="build:enterprise:platform:auth:main:200",
    ...     component_type="api-gateway",
    ...     artifact_location="s3://enterprise-artifacts/auth/200/api-spec.yaml",
    ...     deployment_status="pending",
    ...     configuration={
    ...         "stage": "prod",
    ...         "throttling": {
    ...             "rate_limit": 1000,
    ...             "burst_limit": 2000
    ...         },
    ...         "cors": {
    ...             "allow_origins": ["https://app.enterprise.com"],
    ...             "allow_methods": ["GET", "POST", "PUT", "DELETE"]
    ...         }
    ...     }
    ... )

    >>> # Delete component (cleanup)
    >>> ComponentActions.delete(prn="component:acme:web-services:api:main:120:old-service")

Usage Patterns:
    **Creating Components**: Use ComponentActions.create() with build reference and artifact location

    **Querying Components**: Use ComponentActions.get() for single items or ComponentActions.list() for bulk operations

    **API Integration**: Use ComponentRecord for JSON serialization and API responses

    **Deployment Tracking**: Update deployment status throughout the deployment lifecycle

    **Resource Management**: Track AWS resources created by component deployments

    **Health Monitoring**: Configure and track component health checks

Table Information:
    - **Table Name**: {client}-core-automation-items (client-specific)
    - **Hash Key**: prn (component:client:portfolio:app:branch:build:component_name)
    - **Schema Type**: Items.Component
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

Validation Rules:
    - PRN must follow format: "component:client:portfolio:app:branch:build:component_name"
    - Component name must be unique within build namespace
    - Build PRN must reference existing build
    - Component type must be from allowed component type constants
    - Artifact location must be valid S3 or ECR URI
    - Deployment status must be from allowed status constants
    - AWS resources must have valid ARN format

Component Types:
    ```python
    # Supported component types
    component_types = {
        "lambda": "AWS Lambda function",
        "container": "ECS/Fargate container service",
        "infrastructure": "CloudFormation infrastructure stack",
        "api-gateway": "API Gateway REST or HTTP API",
        "database": "RDS, DynamoDB, or other database",
        "storage": "S3 bucket or EFS file system",
        "messaging": "SQS queue, SNS topic, or EventBridge",
        "cdn": "CloudFront distribution",
        "static-website": "S3 static website hosting",
        "batch-job": "AWS Batch job definition"
    }
    ```

Deployment Status Lifecycle:
    ```python
    # Component deployment status progression
    deployment_statuses = [
        "pending",     # Component ready for deployment
        "deploying",   # Deployment in progress
        "deployed",    # Successfully deployed and healthy
        "failed",      # Deployment failed
        "rollback",    # Rolling back to previous version
        "archived",    # Component archived/deprecated
        "maintenance"  # Component in maintenance mode
    ]
    ```

Configuration Examples:
    ```python
    # Lambda function component
    lambda_component = {
        "prn": "component:acme:web-services:api:main:123:auth-service",
        "name": "Authentication Service",
        "build_prn": "build:acme:web-services:api:main:123",
        "component_type": "lambda",
        "artifact_location": "s3://acme-artifacts/auth/123/auth-service.zip",
        "deployment_status": "deployed",
        "configuration": {
            "runtime": "python3.9",
            "memory": 1024,
            "timeout": 60,
            "environment_variables": {
                "JWT_SECRET": "{{ssm:/acme/auth/jwt-secret}}",
                "DB_CONNECTION": "{{rds:auth-db:endpoint}}"
            },
            "vpc_config": {
                "subnet_ids": ["subnet-12345", "subnet-67890"],
                "security_group_ids": ["sg-abcdef"]
            }
        },
        "aws_resources": [
            {
                "type": "AWS::Lambda::Function",
                "logical_id": "AuthService",
                "physical_id": "acme-auth-service",
                "arn": "arn:aws:lambda:us-west-2:123456789012:function:acme-auth-service"
            }
        ]
    }

    # Container service component
    container_component = {
        "prn": "component:enterprise:platform:web:main:200:frontend-app",
        "name": "Frontend Application",
        "build_prn": "build:enterprise:platform:web:main:200",
        "component_type": "container",
        "artifact_location": "123456789012.dkr.ecr.us-west-2.amazonaws.com/enterprise/frontend:v200",
        "deployment_status": "deployed",
        "configuration": {
            "cpu": 512,
            "memory": 1024,
            "desired_count": 3,
            "port": 3000,
            "health_check_path": "/api/health",
            "environment_variables": {
                "NODE_ENV": "production",
                "API_ENDPOINT": "https://api.enterprise.com"
            },
            "auto_scaling": {
                "min_capacity": 2,
                "max_capacity": 10,
                "target_cpu": 70
            }
        },
        "aws_resources": [
            {
                "type": "AWS::ECS::Service",
                "logical_id": "FrontendService",
                "physical_id": "enterprise-frontend-service"
            },
            {
                "type": "AWS::ApplicationAutoScaling::ScalableTarget",
                "logical_id": "FrontendScalingTarget"
            }
        ]
    }

    # Infrastructure component
    infrastructure_component = {
        "prn": "component:acme:data:etl:main:150:data-pipeline",
        "name": "Data Processing Pipeline",
        "build_prn": "build:acme:data:etl:main:150",
        "component_type": "infrastructure",
        "artifact_location": "s3://acme-artifacts/etl/150/pipeline-template.yaml",
        "deployment_status": "deployed",
        "configuration": {
            "stack_name": "acme-data-pipeline",
            "parameters": {
                "DataBucketName": "acme-data-lake",
                "ProcessingSchedule": "rate(1 hour)",
                "NotificationEmail": "data-team@acme.com"
            },
            "tags": {
                "Environment": "production",
                "Team": "data-engineering",
                "CostCenter": "analytics"
            }
        },
        "aws_resources": [
            {
                "type": "AWS::S3::Bucket",
                "logical_id": "ProcessingBucket",
                "physical_id": "acme-data-processing-bucket"
            },
            {
                "type": "AWS::Lambda::Function",
                "logical_id": "DataProcessor",
                "physical_id": "acme-data-processor"
            },
            {
                "type": "AWS::Events::Rule",
                "logical_id": "ProcessingSchedule",
                "physical_id": "acme-data-schedule"
            }
        ]
    }
    ```

Health Check Configuration:
    ```python
    # Health check configurations by component type
    health_checks = {
        "lambda": {
            "type": "function_invocation",
            "timeout": 10,
            "retry_count": 3
        },
        "container": {
            "type": "http",
            "path": "/health",
            "port": 8080,
            "interval": 30,
            "timeout": 5,
            "healthy_threshold": 2,
            "unhealthy_threshold": 3
        },
        "api-gateway": {
            "type": "http",
            "path": "/health",
            "expected_status": 200,
            "timeout": 10
        }
    }
    ```

Related Modules:
    - core_db.item.build: Parent build items that components reference
    - core_db.item.branch: Grandparent branch context for components
    - core_db.item.app: Great-grandparent app context
    - core_db.item.portfolio: Great-great-grandparent portfolio context

Error Handling:
    All operations may raise:
    - NotFoundException: Component not found
    - ConflictException: Component already exists (create operations)
    - BadRequestException: Invalid component data or PRN format
    - UnauthorizedException: Missing or invalid authentication
    - ForbiddenException: Insufficient permissions for operation

Integration Points:
    - **AWS Services**: Direct integration with Lambda, ECS, CloudFormation, etc.
    - **Artifact Storage**: S3 and ECR for deployment packages and container images
    - **Monitoring**: CloudWatch metrics, alarms, and health checks
    - **Security**: IAM roles, security groups, and resource policies
    - **Configuration Management**: Parameter Store, Secrets Manager integration

Note:
    Component items are the leaf nodes in the deployment hierarchy and represent
    the actual deployable units of an application. They provide the finest level
    of granularity for deployment tracking, resource management, and operational
    monitoring. Components are directly mapped to AWS resources and services.
"""

from .actions import ComponentActions
from .models import ComponentModel, ComponentItem

__all__ = ["ComponentActions", "ComponentModel", "ComponentItem"]
