"""Build item management for the core-automation-items table.

This module provides comprehensive build item management functionality including
actions, models, and data validation for build records in the DynamoDB items table.
Build items represent specific build instances created from Git branches during CI/CD processes.

Key Components:
    - **BuildActions**: CRUD operations for build items with validation
    - **BuildModel**: PynamoDB model for DynamoDB build table operations
    - **BuildRecord**: Pydantic model for API serialization and validation
    - **Build validation**: Business rules and constraints for build data

Features:
    - **Hierarchical Organization**: Build items serve as children of branches and parents of components
    - **Client Isolation**: Each client has their own build namespace within branches
    - **CI/CD Integration**: Build tracking and artifact management for deployment pipelines
    - **Status Tracking**: Build lifecycle management from queued to deployed
    - **Artifact Management**: Reference and tracking of build artifacts and outputs
    - **Audit Trail**: Automatic creation/modification timestamp tracking

Build Hierarchy:
    
    Portfolio (great-grandparent)
    ├── App (grandparent)
    │   ├── Branch (parent)
    │   │   ├── Build (this module)
    │   │   │   └── Component (build_prn references this)
    

Schema Structure:
    The build schema in the core-automation-items table includes:
    - **prn**: Primary key in format "build:client:portfolio:app:branch:build_number"
    - **name**: Human-readable build display name
    - **branch_prn**: Reference to parent branch
    - **build_number**: Incremental build identifier (e.g., "123", "v2.1.0")
    - **git_commit**: Git commit SHA that triggered this build
    - **status**: Current build status (queued, building, success, failed, deployed)
    - **artifacts**: List of build artifacts and their locations
    - **test_results**: Test execution results and coverage data
    - **build_duration**: Time taken to complete the build
    - **deployed_at**: Timestamp when build was deployed (if applicable)
    - **created_at/updated_at**: Automatic audit timestamps

Examples:
    >>> from core_db.item.build import BuildActions, BuildRecord

    >>> # Create a new build
    >>> result = BuildActions.create(
    ...     prn="build:acme:web-services:api:main:123",
    ...     name="Build #123",
    ...     branch_prn="branch:acme:web-services:api:main",
    ...     build_number="123",
    ...     git_commit="a1b2c3d4e5f6789012345678901234567890abcd",
    ...     status="queued",
    ...     triggered_by="github-webhook"
    ... )

    >>> # Retrieve build data
    >>> build_data = BuildActions.get(
    ...     prn="build:acme:web-services:api:main:123"
    ... )

    >>> # Convert to API response format
    >>> build_record = BuildRecord.from_dynamodb(build_data.data)
    >>> api_response = build_record.model_dump()

    >>> # List all builds for a branch
    >>> builds = BuildActions.list_by_branch("branch:acme:web-services:api:main")

    >>> # Update build status during CI/CD
    >>> BuildActions.update(
    ...     prn="build:acme:web-services:api:main:123",
    ...     status="building",
    ...     started_at="2025-01-15T10:30:00Z"
    ... )

    >>> # Complete build with artifacts
    >>> BuildActions.update(
    ...     prn="build:acme:web-services:api:main:123",
    ...     status="success",
    ...     completed_at="2025-01-15T10:45:00Z",
    ...     build_duration=900,  # 15 minutes in seconds
    ...     artifacts=[
    ...         {
    ...             "name": "lambda-function.zip",
    ...             "type": "deployment-package",
    ...             "location": "s3://acme-artifacts/builds/123/lambda-function.zip",
    ...             "size": 1024000,
    ...             "checksum": "sha256:abc123..."
    ...         },
    ...         {
    ...             "name": "cloudformation-template.yaml",
    ...             "type": "infrastructure",
    ...             "location": "s3://acme-artifacts/builds/123/template.yaml",
    ...             "size": 4096,
    ...             "checksum": "sha256:def456..."
    ...         }
    ...     ],
    ...     test_results={
    ...         "unit_tests": {"passed": 145, "failed": 0, "skipped": 2},
    ...         "integration_tests": {"passed": 23, "failed": 0, "skipped": 1},
    ...         "coverage": {"lines": 87.5, "branches": 82.3}
    ...     }
    ... )

    >>> # Mark build as deployed
    >>> BuildActions.update(
    ...     prn="build:acme:web-services:api:main:123",
    ...     status="deployed",
    ...     deployed_at="2025-01-15T11:00:00Z",
    ...     deployment_target="production"
    ... )

    >>> # Create release build
    >>> BuildActions.create(
    ...     prn="build:acme:web-services:api:release-v2.1:124",
    ...     name="Release v2.1.0",
    ...     branch_prn="branch:acme:web-services:api:release-v2.1",
    ...     build_number="124",
    ...     git_commit="b2c3d4e5f6789012345678901234567890abcdef",
    ...     status="queued",
    ...     build_type="release",
    ...     version="2.1.0",
    ...     release_notes="Major feature update with new authentication system"
    ... )

    >>> # Create hotfix build
    >>> BuildActions.create(
    ...     prn="build:acme:web-services:api:hotfix-security:125",
    ...     name="Security Hotfix",
    ...     branch_prn="branch:acme:web-services:api:hotfix-security",
    ...     build_number="125",
    ...     git_commit="c3d4e5f6789012345678901234567890abcdef12",
    ...     status="queued",
    ...     build_type="hotfix",
    ...     priority="high",
    ...     security_patch=True
    ... )

    >>> # Delete old build
    >>> BuildActions.delete(prn="build:acme:web-services:api:main:120")

Usage Patterns:
    **Creating Builds**: Use BuildActions.create() with branch reference and Git commit info

    **Querying Builds**: Use BuildActions.get() for single items or BuildActions.list() for bulk operations

    **API Integration**: Use BuildRecord for JSON serialization and API responses

    **Hierarchy Management**: Build PRNs serve as parent_prn for component items

    **CI/CD Integration**: Track build progress and store artifacts for deployment

    **Status Management**: Update build status throughout the CI/CD pipeline lifecycle

Table Information:
    - **Table Name**: {client}-core-automation-items (client-specific)
    - **Hash Key**: prn (build:client:portfolio:app:branch:build_number)
    - **Schema Type**: Items.Build
    - **Billing Mode**: PAY_PER_REQUEST
    - **Client Isolation**: Each client has separate table

Validation Rules:
    - PRN must follow format: "build:client:portfolio:app:branch:build_number"
    - Build number must be unique within branch namespace
    - Branch PRN must reference existing branch
    - Git commit must be valid SHA format (40 characters, hexadecimal)
    - Status must be from allowed build status constants
    - Build number must follow semantic versioning or incremental format
    - Artifacts must have valid S3 locations and checksums

Build Status Lifecycle:
    ..code: python
        # Build status progression
        build_statuses = [
            "queued",      # Build requested and waiting to start
            "building",    # Build in progress
            "testing",     # Running tests and quality checks
            "success",     # Build completed successfully
            "failed",      # Build failed due to errors
            "cancelled",   # Build was cancelled by user
            "deployed",    # Build artifacts deployed to target environment
            "archived"     # Build artifacts archived for retention
        ]
    

Configuration Examples:
    ..code: python
        # Standard application build
        app_build = {
            "prn": "build:acme:web-services:api:main:123",
            "name": "API Build #123",
            "branch_prn": "branch:acme:web-services:api:main",
            "build_number": "123",
            "git_commit": "a1b2c3d4e5f6789012345678901234567890abcd",
            "status": "success",
            "build_type": "standard",
            "triggered_by": "git-push",
            "build_duration": 600,
            "artifacts": [
                {
                    "name": "api-service.zip",
                    "type": "lambda-package",
                    "location": "s3://acme-artifacts/api/123/api-service.zip"
                }
            ]
        }

        # Release build with versioning
        release_build = {
            "prn": "build:enterprise:platform:auth:release-v3.0:200",
            "name": "Authentication Service v3.0.0",
            "branch_prn": "branch:enterprise:platform:auth:release-v3.0",
            "build_number": "200",
            "git_commit": "b3c4d5e6f7890123456789012345678901abcdef",
            "status": "success",
            "build_type": "release",
            "version": "3.0.0",
            "semver": {"major": 3, "minor": 0, "patch": 0},
            "release_notes": "Major version with breaking changes",
            "artifacts": [
                {
                    "name": "auth-service-3.0.0.zip",
                    "type": "release-package",
                    "location": "s3://enterprise-releases/auth/3.0.0/"
                },
                {
                    "name": "migration-scripts.zip",
                    "type": "database-migration",
                    "location": "s3://enterprise-releases/auth/3.0.0/migrations/"
                }
            ],
            "approval_required": True,
            "security_scan": {
                "vulnerabilities": 0,
                "scan_date": "2025-01-15T10:00:00Z"
            }
        }

        # Hotfix build with priority
        hotfix_build = {
            "prn": "build:acme:web-services:api:hotfix-cve-2025:126",
            "name": "Security Hotfix CVE-2025-1234",
            "branch_prn": "branch:acme:web-services:api:hotfix-cve-2025",
            "build_number": "126",
            "git_commit": "d5e6f7890123456789012345678901abcdef234",
            "status": "success",
            "build_type": "hotfix",
            "priority": "critical",
            "security_patch": True,
            "cve_numbers": ["CVE-2025-1234"],
            "expedited": True,
            "bypass_approval": True,
            "artifacts": [
                {
                    "name": "security-patch.zip",
                    "type": "hotfix-package",
                    "location": "s3://acme-security/patches/126/"
                }
            ]
        }
    

Build Types and Strategies:
    **Standard Builds**: Regular CI builds triggered by Git commits

    **Release Builds**: Versioned builds for production releases

    **Hotfix Builds**: Emergency builds for critical security or bug fixes

    **Feature Builds**: Builds from feature branches for testing

    **Nightly Builds**: Scheduled builds for continuous integration

Artifact Management:
    ..code: python
        # Artifact types and locations
        artifact_types = {
            "lambda-package": "Zipped Lambda function code",
            "container-image": "Docker container image",
            "cloudformation": "Infrastructure as Code templates",
            "static-assets": "Web assets, documentation, etc.",
            "database-migration": "Database schema changes",
            "configuration": "Environment-specific configuration"
        }

        # Artifact storage patterns
        artifact_locations = {
            "s3": "s3://bucket/path/to/artifact",
            "ecr": "123456789012.dkr.ecr.region.amazonaws.com/repo:tag",
            "codecommit": "codecommit://repo-name/path/to/file"
        }
    

Related Modules:
    - core_db.item.branch: Parent branch items that builds reference
    - core_db.item.component: Child component items that reference builds
    - core_db.item.app: Grandparent app context for builds
    - core_db.item.portfolio: Great-grandparent portfolio context

Error Handling:
    All operations may raise:
    - NotFoundException: Build not found
    - ConflictException: Build already exists (create operations)
    - BadRequestException: Invalid build data or PRN format
    - UnauthorizedException: Missing or invalid authentication
    - ForbiddenException: Insufficient permissions for operation

Integration Points:
    - **CI/CD Systems**: Jenkins, GitHub Actions, AWS CodePipeline integration
    - **Git Repositories**: Source code and commit tracking
    - **Artifact Storage**: S3, ECR, CodeArtifact for build outputs
    - **Deployment Systems**: CloudFormation, CDK, Terraform deployment
    - **Monitoring**: Build metrics, failure analysis, and alerting

Note:
    Build items represent specific build instances in the deployment hierarchy. They
    track the entire build lifecycle from source code to deployed artifacts. Build
    records serve as the foundation for deployment traceability and rollback
    capabilities. Consider retention policies for build artifacts and metadata.
"""

from .actions import BuildActions
from .models import BuildModel, BuildItem

__all__ = ["BuildActions", "BuildModel", "BuildItem"]
