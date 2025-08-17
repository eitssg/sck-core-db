from core_framework.models import DeploymentDetails

from core_db.registry.client import ClientActions
from core_db.registry.portfolio import PortfolioActions
from core_db.registry.app import AppActions
from core_db.registry.zone import ZoneActions

from core_db.facter import get_facts, get_client_facts, get_portfolio_facts, get_app_facts, get_zone_facts

from .bootstrap import *

client = util.get_client()

client_facts = {
    "client": client,
    "client_id": "ACME001",
    "client_type": "enterprise",
    "client_status": "active",
    "client_description": "ACME Corporation - Leading provider of innovative solutions for enterprise automation and cloud infrastructure management",
    "client_name": "ACME Corporation",
    # AWS Organization Configuration
    "organization_id": "o-acme123456789",
    "organization_name": "ACME Enterprise Organization",
    "organization_account": "123456789012",
    "organization_email": "aws-admin@acme.com",
    # Domain and Networking
    "domain": "acme.com",
    # AWS Account Assignments (Multi-account architecture)
    "iam_account": "123456789012",  # Same as org account for this example
    "audit_account": "123456789013",  # Dedicated audit account
    "automation_account": "123456789014",  # Automation artifacts account
    "security_account": "123456789015",  # Security operations account
    "network_account": "123456789016",  # Network and VPC account
    # Regional Configuration
    "master_region": "us-east-1",  # Primary control plane region
    "client_region": "us-east-1",  # Default client operations region
    "bucket_region": "us-east-1",  # S3 bucket region
    # S3 Bucket Configuration
    "bucket_name": "acme-automation-artifacts",
    "docs_bucket_name": "acme-documentation",
    "artefact_bucket_name": "acme-build-artifacts",
    "ui_bucket_name": "acme-ui-hosting",
    "ui_bucket": "acme-legacy-ui",  # Legacy field
    # Resource Naming and Scoping
    "scope": "acme-",  # Prefix for all resources
}

zone_facts = {
    "zone": "prod-east-primary",
    # AWS Account Configuration
    "account_facts": {
        "organizational_unit": "Production",
        "aws_account_id": "123456789012",  # Matches client organization_account
        "account_name": "ACME Production Account",
        "environment": "production",
        "kms": {
            "aws_account_id": "123456789012",
            "kms_key_arn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
            "kms_key": "12345678-1234-1234-1234-123456789012",
            "delegate_aws_account_ids": ["123456789012", "123456789013", "123456789014"],
            "allow_sns": True,
        },
        "resource_namespace": "acme-prod",
        "network_name": "production-network",
        "vpc_aliases": ["vpc-prod-main", "vpc-prod-backup", "vpc-prod-dmz"],
        "subnet_aliases": [
            "subnet-prod-public-1a",
            "subnet-prod-public-1b",
            "subnet-prod-public-1c",
            "subnet-prod-private-1a",
            "subnet-prod-private-1b",
            "subnet-prod-private-1c",
            "subnet-prod-database-1a",
            "subnet-prod-database-1b",
            "subnet-prod-database-1c",
        ],
        "tags": {
            "Environment": "production",
            "Owner": "platform-team",
            "CostCenter": "CC-IT-001",
            "Backup": "required",
            "Compliance": "soc2-hipaa",
            "BusinessUnit": "IT Operations",
        },
    },
    # Regional Configuration
    "region_facts": {
        # Primary Production Region - US East 1
        "us-east-1": {
            "aws_region": "us-east-1",
            "az_count": 3,
            "image_aliases": {
                "ubuntu-22": "ami-0c02fb55956c7d316",
                "ubuntu-20": "ami-0892d3c7ee96c0bf7",
                "amazon-linux-2": "ami-0b898040803850657",
                "amazon-linux-2023": "ami-0230bd60aa48260c6",
                "windows-2022": "ami-0c9978668f8d55984",
                "windows-2019": "ami-0f93c815788872c5d",
                "nginx-alpine": "ami-0123456789abcdef0",
                "redis-cluster": "ami-0987654321fedcba0",
                "postgresql-14": "ami-0abcdef123456789f",
            },
            "min_successful_instances_percent": 100,
            "security_aliases": {
                "corporate-cidrs": [
                    {"type": "CIDR", "value": "10.0.0.0/8", "description": "Corporate headquarters network range"},
                    {"type": "CIDR", "value": "172.16.0.0/12", "description": "Corporate VPN network range"},
                    {"type": "CIDR", "value": "192.168.100.0/24", "description": "Corporate WiFi guest network"},
                ],
                "admin-cidrs": [
                    {"type": "CIDR", "value": "192.168.1.0/24", "description": "IT Admin access network"},
                    {"type": "CIDR", "value": "10.100.0.0/16", "description": "DevOps team access network"},
                ],
                "office-cidrs": [
                    {"type": "CIDR", "value": "203.0.113.0/24", "description": "Seattle office public IP range"},
                    {"type": "CIDR", "value": "198.51.100.0/24", "description": "New York office public IP range"},
                ],
            },
            "security_group_aliases": {
                "web-tier-sg": "sg-web-prod-east-12345",
                "app-tier-sg": "sg-app-prod-east-67890",
                "db-tier-sg": "sg-db-prod-east-abcde",
                "cache-tier-sg": "sg-cache-prod-east-fghij",
                "lb-sg": "sg-lb-prod-east-klmno",
                "bastion-sg": "sg-bastion-prod-east-pqrst",
                "monitoring-sg": "sg-monitor-prod-east-uvwxy",
            },
            "proxy": [
                {
                    "host": "proxy.acme.com",
                    "port": "8080",
                    "url": "http://proxy.acme.com:8080",
                    "no_proxy": "*.acme.com,10.0.0.0/8,172.16.0.0/12,169.254.169.254,localhost",
                },
                {
                    "host": "proxy-backup.acme.com",
                    "port": "8080",
                    "url": "http://proxy-backup.acme.com:8080",
                    "no_proxy": "*.acme.com,10.0.0.0/8,172.16.0.0/12,169.254.169.254,localhost",
                },
            ],
            "proxy_host": "proxy.acme.com",
            "proxy_port": 8080,
            "proxy_url": "http://proxy.acme.com:8080",
            "no_proxy": "*.acme.com,10.0.0.0/8,172.16.0.0/12,169.254.169.254,localhost",
            "name_servers": ["8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "208.67.222.222"],
            "tags": {
                "Region": "us-east-1",
                "AZ": "multi-az",
                "NetworkTier": "production",
                "DataResidency": "us-east",
                "DisasterRecovery": "primary-region",
            },
        },
        # Disaster Recovery Region - US West 2
        "us-west-2": {
            "aws_region": "us-west-2",
            "az_count": 4,
            "image_aliases": {
                "ubuntu-22": "ami-0892d3c7ee96c0bf7",
                "ubuntu-20": "ami-0c2d3e23eb9d8a2ce",
                "amazon-linux-2": "ami-0c2d3e23eb9d8a2ce",
                "amazon-linux-2023": "ami-0095d4e46ef9e46cc",
                "windows-2022": "ami-0dd8be3d67c8e3db8",
                "windows-2019": "ami-0a634ae95e11c6f91",
                "nginx-alpine": "ami-west123456789abcdef",
                "redis-cluster": "ami-west987654321fedcba",
            },
            "min_successful_instances_percent": 75,
            "security_aliases": {
                "corporate-cidrs": [
                    {"type": "CIDR", "value": "10.0.0.0/8", "description": "Corporate headquarters network range"},
                    {"type": "CIDR", "value": "172.16.0.0/12", "description": "Corporate VPN network range"},
                ],
                "office-cidrs": [{"type": "CIDR", "value": "203.0.113.0/24", "description": "Seattle office public IP range"}],
            },
            "security_group_aliases": {
                "web-tier-sg": "sg-web-prod-west-12345",
                "app-tier-sg": "sg-app-prod-west-67890",
                "db-tier-sg": "sg-db-prod-west-abcde",
                "lb-sg": "sg-lb-prod-west-klmno",
            },
            "proxy_host": "proxy-west.acme.com",
            "proxy_port": 8080,
            "proxy_url": "http://proxy-west.acme.com:8080",
            "no_proxy": "*.acme.com,10.0.0.0/8,172.16.0.0/12,169.254.169.254,localhost",
            "name_servers": ["8.8.8.8", "1.1.1.1", "208.67.222.222"],
            "tags": {
                "Region": "us-west-2",
                "Purpose": "disaster-recovery",
                "NetworkTier": "production-dr",
                "DataResidency": "us-west",
                "DisasterRecovery": "secondary-region",
            },
        },
    },
    # Global Zone Tags
    "tags": {
        "Environment": "production",
        "Team": "platform-engineering",
        "Owner": "sarah.johnson",
        "CostCenter": "CC-IT-001",
        "Project": "enterprise-platform",
        "BusinessUnit": "IT Operations",
        "Criticality": "tier1",
        "Compliance": "soc2-hipaa-pci",
        "BackupRequired": "true",
        "MonitoringLevel": "enhanced",
        "SecurityScan": "daily",
        "PatchingWindow": "saturday-02:00-06:00-est",
        "DataClassification": "confidential",
        "DisasterRecovery": "multi-region-active",
        "ServiceLevel": "24x7-premium-support",
    },
}

portfolio_facts = {
    "portfolio": "acme-enterprise-platform",
    "domain": "platform.acme.com",
    # Project/Software Details
    "project": {
        "name": "ACME Enterprise Platform",
        "code": "AEP",
        "repository": "https://github.com/acme/enterprise-platform",
        "description": "Comprehensive enterprise automation platform for cloud infrastructure management, deployment orchestration, and monitoring solutions",
        "attributes": {
            "version": "2.1.0",
            "license": "Enterprise",
            "language": "Python",
            "framework": "FastAPI",
            "database": "DynamoDB",
            "cloud_provider": "AWS",
            "architecture": "microservices",
            "api_version": "v2",
            "build_tool": "Docker",
            "ci_cd": "GitHub Actions",
        },
    },
    # Business Application Details (Alternative software categorization)
    "bizapp": {
        "name": "Enterprise Cloud Automation Suite",
        "code": "ECAS",
        "repository": "https://github.com/acme/cloud-automation",
        "description": "Business application suite for automated cloud resource provisioning, compliance monitoring, and cost optimization",
        "attributes": {
            "business_unit": "IT Operations",
            "cost_center": "CC-IT-001",
            "application_type": "platform",
            "criticality": "high",
            "compliance": "SOC2,HIPAA,PCI-DSS",
            "data_classification": "confidential",
            "backup_requirement": "daily",
            "rto": "4_hours",
            "rpo": "1_hour",
        },
    },
    # Portfolio Owner
    "owner": {
        "name": "Sarah Johnson",
        "email": "sarah.johnson@acme.com",
        "phone": "+1-555-0199",
        "attributes": {
            "title": "Director of Platform Engineering",
            "department": "Engineering",
            "employee_id": "EMP-2024-001",
            "location": "Seattle, WA",
            "timezone": "PST",
            "manager": "mike.wilson@acme.com",
            "start_date": "2022-03-15",
        },
    },
    # Contact List
    "contacts": [
        {
            "name": "David Kim",
            "email": "david.kim@acme.com",
            "enabled": True,
            "attributes": {
                "role": "Tech Lead",
                "responsibility": "Architecture and Development",
                "phone": "+1-555-0187",
                "availability": "business_hours",
                "escalation_level": "1",
            },
        },
        {
            "name": "Lisa Chen",
            "email": "lisa.chen@acme.com",
            "enabled": True,
            "attributes": {
                "role": "DevOps Engineer",
                "responsibility": "Infrastructure and Deployment",
                "phone": "+1-555-0156",
                "availability": "24x7",
                "escalation_level": "2",
            },
        },
        {
            "name": "Mark Rodriguez",
            "email": "mark.rodriguez@acme.com",
            "enabled": True,
            "attributes": {
                "role": "Security Engineer",
                "responsibility": "Security and Compliance",
                "phone": "+1-555-0143",
                "availability": "business_hours",
                "escalation_level": "1",
            },
        },
        {
            "name": "Emergency Hotline",
            "email": "platform-emergency@acme.com",
            "enabled": True,
            "attributes": {
                "role": "Emergency Contact",
                "responsibility": "Critical Issues and Outages",
                "phone": "+1-800-ACME-911",
                "availability": "24x7",
                "escalation_level": "0",
            },
        },
    ],
    # Approval Workflow
    "approvers": [
        {
            "sequence": 1,
            "name": "David Kim",
            "email": "david.kim@acme.com",
            "roles": ["development", "testing", "minor_release"],
            "enabled": True,
            "attributes": {
                "title": "Tech Lead",
                "approval_authority": "technical_changes",
                "max_budget": "50000",
                "auto_approve_threshold": "patch_releases",
            },
        },
        {
            "sequence": 2,
            "name": "Sarah Johnson",
            "email": "sarah.johnson@acme.com",
            "roles": ["production", "major_release", "infrastructure"],
            "depends_on": [1],
            "enabled": True,
            "attributes": {
                "title": "Director of Platform Engineering",
                "approval_authority": "production_deployments",
                "max_budget": "500000",
                "approval_sla": "4_hours",
            },
        },
        {
            "sequence": 3,
            "name": "Mike Wilson",
            "email": "mike.wilson@acme.com",
            "roles": ["security", "compliance", "emergency"],
            "enabled": True,
            "attributes": {
                "title": "VP of Engineering",
                "approval_authority": "security_changes",
                "max_budget": "unlimited",
                "emergency_override": "true",
            },
        },
        {
            "sequence": 4,
            "name": "Jennifer Adams",
            "email": "jennifer.adams@acme.com",
            "roles": ["budget", "procurement", "vendor"],
            "depends_on": [2, 3],
            "enabled": True,
            "attributes": {
                "title": "VP of Finance",
                "approval_authority": "financial_approval",
                "budget_threshold": "100000",
                "procurement_authority": "true",
            },
        },
    ],
    # Resource Tags
    "tags": {
        "Environment": "production",
        "Team": "platform-engineering",
        "Owner": "sarah.johnson",
        "CostCenter": "CC-IT-001",
        "Project": "enterprise-platform",
        "BusinessUnit": "IT Operations",
        "Criticality": "high",
        "Compliance": "required",
        "BackupRequired": "true",
        "MonitoringLevel": "enhanced",
        "SecurityScan": "required",
        "PatchingWindow": "weekend",
        "DataClassification": "confidential",
        "Version": "2.1.0",
        "LicenseType": "enterprise",
    },
    # Portfolio Metadata
    "metadata": {
        "software_category": "platform",
        "deployment_model": "cloud_native",
        "service_tier": "enterprise",
        "support_level": "premium",
        "maintenance_window": "saturday_02:00_06:00_pst",
        "disaster_recovery": "multi_region",
        "scalability": "auto_scaling",
        "monitoring_strategy": "comprehensive",
        "logging_retention": "7_years",
        "encryption": "at_rest_and_transit",
        "network_isolation": "vpc_dedicated",
        "load_balancing": "application_load_balancer",
        "cdn": "cloudfront_enabled",
        "dns_management": "route53",
        "ssl_management": "acm_certificates",
        "container_orchestration": "ecs_fargate",
        "infrastructure_as_code": "terraform",
        "secret_management": "aws_secrets_manager",
        "api_gateway": "aws_api_gateway_v2",
    },
    # Custom Attributes
    "attributes": {
        "software_title": "ACME Enterprise Platform",
        "software_version": "2.1.0",
        "software_vendor": "ACME Corporation",
        "software_type": "internal_development",
        "release_date": "2024-08-15",
        "end_of_life_date": "2027-08-15",
        "support_end_date": "2029-08-15",
        "installation_type": "cloud_native",
        "user_count": "enterprise_unlimited",
        "concurrent_users": "10000",
        "api_rate_limit": "10000_per_minute",
        "storage_capacity": "unlimited",
        "bandwidth_allocation": "10_gbps",
        "uptime_sla": "99.9",
        "performance_sla": "sub_100ms_response",
        "integration_protocols": "REST,GraphQL,WebSocket,gRPC",
        "authentication_methods": "SAML,OAuth2,LDAP,MFA",
        "audit_logging": "comprehensive",
        "gdpr_compliant": "true",
        "hipaa_compliant": "true",
        "soc2_compliant": "true",
    },
}

app_facts = {
    "portfolio": "acme-enterprise-platform",
    "app_regex": "^prn:acme-enterprise-platform:acme-api-[^:]*:[^:]*:[^:]*$",
    "name": "ACME Enterprise Platform Core",
    "environment": "production",
    "account": "123456789012",  # Matches zone account
    "zone": "prod-east-primary",  # Matches our zone
    "region": "us-east-1",  # Primary region from zone
    "repository": "https://github.com/acme/enterprise-platform",
    "enforce_validation": "true",
    "user_instantiated": "false",
    # Image Aliases for Application Deployment
    "image_aliases": {
        "api-gateway": "ami-0c02fb55956c7d316",  # Ubuntu 22 for API gateway
        "core-api": "ami-0b898040803850657",  # Amazon Linux 2 for core API
        "worker-service": "ami-0230bd60aa48260c6",  # Amazon Linux 2023 for workers
        "database": "ami-0abcdef123456789f",  # PostgreSQL 14 image
        "cache": "ami-0987654321fedcba0",  # Redis cluster image
        "web-frontend": "ami-0123456789abcdef0",  # Nginx Alpine for web
        "monitoring": "ami-0c02fb55956c7d316",  # Ubuntu 22 for monitoring stack
        "backup-service": "ami-0b898040803850657",  # Amazon Linux 2 for backups
        "log-aggregator": "ami-0230bd60aa48260c6",  # Amazon Linux 2023 for logging
        "security-scanner": "ami-0892d3c7ee96c0bf7",  # Ubuntu 20 for security tools
    },
    # Application Resource Tags
    "tags": {
        "Application": "acme-enterprise-platform",
        "Component": "core-platform",
        "Environment": "production",
        "Owner": "sarah.johnson",
        "Team": "platform-engineering",
        "CostCenter": "CC-IT-001",
        "Project": "enterprise-platform",
        "BusinessUnit": "IT Operations",
        "Criticality": "tier1",
        "ServiceLevel": "24x7-premium",
        "Version": "2.1.0",
        "DeploymentType": "production",
        "BackupRequired": "true",
        "MonitoringLevel": "enhanced",
        "SecurityScan": "daily",
        "Compliance": "soc2-hipaa-pci",
        "DataClassification": "confidential",
        "DisasterRecovery": "multi-region-active",
        "AutoScaling": "enabled",
        "LoadBalancer": "application-lb",
        "HealthCheck": "comprehensive",
        "LogRetention": "7-years",
        "PatchingWindow": "saturday-02:00-06:00-est",
        "MaintenanceWindow": "saturday-06:00-10:00-est",
    },
    # Application Deployment Metadata
    "metadata": {
        # Deployment Configuration
        "deployment_strategy": "blue_green",
        "rollback_strategy": "automatic",
        "deployment_timeout": "1800",
        "health_check_grace_period": "300",
        "desired_capacity": "6",
        "min_capacity": "3",
        "max_capacity": "20",
        "target_cpu_utilization": "70",
        "target_memory_utilization": "80",
        # Service Configuration
        "service_type": "microservices",
        "container_orchestration": "ecs_fargate",
        "task_definition_family": "acne-api",
        "cpu_units": "2048",
        "memory_mb": "4096",
        "network_mode": "awsvpc",
        "requires_attributes": "ecs.capability.fargate",
        # Load Balancer Configuration
        "load_balancer_type": "application",
        "load_balancer_scheme": "internet-facing",
        "target_group_protocol": "HTTP",
        "target_group_port": "8080",
        "health_check_path": "/health",
        "health_check_interval": "30",
        "health_check_timeout": "5",
        "healthy_threshold": "2",
        "unhealthy_threshold": "5",
        # Security Configuration
        "security_groups": "web-tier-sg,app-tier-sg",
        "subnets": "subnet-prod-private-1a,subnet-prod-private-1b,subnet-prod-private-1c",
        "vpc_id": "vpc-prod-main",
        "ssl_certificate": "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012",
        "waf_enabled": "true",
        "cloudfront_enabled": "true",
        # Database Configuration
        "database_engine": "postgresql",
        "database_version": "14.9",
        "database_instance_class": "db.r6g.xlarge",
        "database_multi_az": "true",
        "database_backup_retention": "30",
        "database_encryption": "true",
        "database_subnets": "subnet-prod-database-1a,subnet-prod-database-1b,subnet-prod-database-1c",
        # Cache Configuration
        "cache_engine": "redis",
        "cache_version": "7.0",
        "cache_node_type": "cache.r6g.large",
        "cache_num_cache_clusters": "3",
        "cache_encryption_at_rest": "true",
        "cache_encryption_in_transit": "true",
        # Monitoring and Logging
        "cloudwatch_log_group": "/aws/ecs/acne-api",
        "log_retention_days": "2555",  # 7 years
        "metrics_namespace": "ACME/Platform",
        "alarm_notification_topic": "arn:aws:sns:us-east-1:123456789012:platform-alerts",
        "dashboard_name": "ACME-Enterprise-Platform-Production",
        # API Gateway Configuration
        "api_gateway_type": "REST",
        "api_gateway_stage": "prod",
        "api_gateway_throttle_burst": "5000",
        "api_gateway_throttle_rate": "2000",
        "api_gateway_caching": "true",
        "api_gateway_cache_ttl": "300",
        # Storage Configuration
        "s3_bucket_prefix": "acne-api-prod",
        "s3_versioning": "enabled",
        "s3_encryption": "AES256",
        "s3_lifecycle_policy": "intelligent_tiering",
        "efs_throughput_mode": "provisioned",
        "efs_performance_mode": "generalPurpose",
        # Backup and Recovery
        "backup_strategy": "continuous",
        "backup_retention": "30_days",
        "point_in_time_recovery": "true",
        "cross_region_backup": "us-west-2",
        "disaster_recovery_rto": "4_hours",
        "disaster_recovery_rpo": "1_hour",
        # CI/CD Configuration
        "build_project": "acne-api-build",
        "deploy_pipeline": "acne-api-deploy",
        "artifact_bucket": "acme-build-artifacts",
        "codebuild_image": "aws/codebuild/amazonlinux2-x86_64-standard:4.0",
        "approval_required": "true",
        "auto_rollback": "true",
        # DNS and CDN
        "route53_zone": "platform.acme.com",
        "primary_domain": "api.platform.acme.com",
        "cdn_distribution": "acne-api-cloudfront",
        "cdn_price_class": "PriceClass_All",
        "cdn_cache_behavior": "CachingOptimized",
        # Compliance and Governance
        "config_rules": "enabled",
        "cloudtrail_logging": "enabled",
        "access_logging": "enabled",
        "vpc_flow_logs": "enabled",
        "guardduty_enabled": "true",
        "security_hub_enabled": "true",
        "inspector_enabled": "true",
        # Cost Optimization
        "reserved_instances": "partial",
        "spot_instances": "development_only",
        "scheduled_scaling": "business_hours",
        "cost_allocation_tags": "detailed",
        "budget_alerts": "enabled",
        "rightsizing_recommendations": "weekly",
    },
}

deployment = {
    "client": client,
    "portfolio": "acme-enterprise-platform",  # Matches our portfolio
    "app": "acme-api-core",  # Matches app_regex "acne-api-.*"
    "branch": "main",  # Standard main branch
    "build": "1.2.0",  # Version build
    "environment": "production",  # Matches our zone environment
    "data_center": "us-east-1",  # Matches our zone region
    "tags": {
        "Team": "platform-engineering",
        "Environment": "production",
        "CostCenter": "CC-IT-001",
        "Project": "enterprise-platform",
        "BusinessUnit": "IT Operations",
        "Criticality": "tier1",
        "Version": "1.2.0",
    },
    "delivered_by": "github-actions",
}


def test_create_facts(bootstrap_dynamo):

    ClientActions.create(**client_facts)

    # Create portfolio facts
    PortfolioActions.create(client=client, **portfolio_facts)

    # Create app facts
    AppActions.create(client=client, **app_facts)

    # Create zone facts
    ZoneActions.create(client=client, **zone_facts)


def test_get_client_facts():

    facts = get_client_facts(client)

    # Validate core client identity
    assert facts["ClientId"] == "ACME001"
    assert facts["ClientType"] == "enterprise"
    assert facts["ClientStatus"] == "active"
    assert facts["ClientName"] == "ACME Corporation"
    assert (
        facts["ClientDescription"]
        == "ACME Corporation - Leading provider of innovative solutions for enterprise automation and cloud infrastructure management"
    )

    # Validate AWS Organization details
    assert facts["OrganizationId"] == "o-acme123456789"
    assert facts["OrganizationName"] == "ACME Enterprise Organization"
    assert facts["OrganizationAccount"] == "123456789012"
    assert facts["OrganizationEmail"] == "aws-admin@acme.com"


def test_get_zone_facts():

    zone = "prod-east-primary"

    facts = get_zone_facts(client, zone)

    assert facts["Zone"] == zone
    assert facts["AccountFacts"]["AwsAccountId"] == "123456789012"
    assert "RegionFacts" in facts
    assert "us-east-1" in facts["RegionFacts"]

    region_facts = facts["RegionFacts"]["us-east-1"]

    assert region_facts["AwsRegion"] == "us-east-1"


def test_get_portfolio_facts():

    facts = get_portfolio_facts(client, "acme-enterprise-platform")

    # Validate core portfolio identity
    assert facts["Portfolio"] == "acme-enterprise-platform"
    assert facts["Domain"] == "platform.acme.com"
    assert facts["Project"]["Name"] == "ACME Enterprise Platform"
    assert facts["Project"]["Code"] == "AEP"
    assert facts["Project"]["Repository"] == "https://github.com/acme/enterprise-platform"


def test_get_app_facts():

    deployment_details = DeploymentDetails(**deployment)

    facts_list = get_app_facts(deployment_details)

    assert len(facts_list) == 1

    facts = facts_list[0]

    # Validate core application identity
    assert facts["Portfolio"] == "acme-enterprise-platform"
    assert facts["Name"] == "ACME Enterprise Platform Core"
    assert facts["Environment"] == "production"
    assert facts["Account"] == "123456789012"
    assert facts["Zone"] == "prod-east-primary"
    assert facts["Region"] == "us-east-1"

    image_aliases = facts.get("ImageAliases", {})

    assert image_aliases.get("api-gateway") == "ami-0c02fb55956c7d316"


def test_get_facts():

    deployment_details = DeploymentDetails(**deployment)

    facts = get_facts(deployment_details)

    # ========== Core Identity Assertions ==========
    assert facts["Client"] == client
    assert facts["Portfolio"] == "acme-enterprise-platform"
    assert facts["App"] == "acme-api-core"
    assert facts["Branch"] == "main"
    assert facts["Build"] == "1.2.0"
    assert facts["Environment"] == "production"
    assert facts["DataCenter"] == "us-east-1"
    assert facts["DeliveredBy"] == "github-actions"

    # ========== AWS Account & Infrastructure Assertions ==========
    # From zone_facts.account_facts
    assert facts["AwsAccountId"] == "123456789012"
    assert facts["AccountName"] == "ACME Production Account"
    assert facts["OrganizationalUnit"] == "Production"
    assert facts["ResourceNamespace"] == "acme-prod"
    assert facts["NetworkName"] == "production-network"

    # ========== Regional Configuration Assertions ==========
    # From zone_facts.region_facts['us-east-1']
    assert facts["AwsRegion"] == "us-east-1"
    assert facts["AzCount"] == 3
    assert facts["MinSuccessfulInstancesPercent"] == 100

    # ========== VPC and Networking Assertions ==========
    assert "VpcAliases" in facts
    assert "vpc-prod-main" in facts["VpcAliases"]
    assert "vpc-prod-backup" in facts["VpcAliases"]
    assert "vpc-prod-dmz" in facts["VpcAliases"]

    assert "SubnetAliases" in facts
    expected_subnets = [
        "subnet-prod-public-1a",
        "subnet-prod-public-1b",
        "subnet-prod-public-1c",
        "subnet-prod-private-1a",
        "subnet-prod-private-1b",
        "subnet-prod-private-1c",
        "subnet-prod-database-1a",
        "subnet-prod-database-1b",
        "subnet-prod-database-1c",
    ]
    for subnet in expected_subnets:
        assert subnet in facts["SubnetAliases"]

    # ========== Security Configuration Assertions ==========
    assert "SecurityAliases" in facts
    assert "corporate-cidrs" in facts["SecurityAliases"]
    assert "admin-cidrs" in facts["SecurityAliases"]
    assert "office-cidrs" in facts["SecurityAliases"]

    # Validate CIDR structure
    corporate_cidrs = facts["SecurityAliases"]["corporate-cidrs"]
    assert len(corporate_cidrs) >= 2  # Should have multiple corporate CIDRs
    assert any(cidr["Value"] == "10.0.0.0/8" for cidr in corporate_cidrs)
    assert any(cidr["Value"] == "172.16.0.0/12" for cidr in corporate_cidrs)

    assert "SecurityGroupAliases" in facts
    security_groups = facts["SecurityGroupAliases"]
    assert "web-tier-sg" in security_groups
    assert "app-tier-sg" in security_groups
    assert "db-tier-sg" in security_groups
    assert security_groups["web-tier-sg"] == "sg-web-prod-east-12345"

    # ========== KMS Configuration Assertions ==========
    assert "Kms" in facts
    kms_config = facts["Kms"]
    assert kms_config["AwsAccountId"] == "123456789012"
    assert "kms_key_arn" in kms_config or "KmsKeyArn" in kms_config
    assert kms_config["AllowSNS"] is True
    assert "DelegateAwsAccountIds" in kms_config
    assert len(kms_config["DelegateAwsAccountIds"]) == 3

    # ========== Image Aliases Assertions ==========
    assert "ImageAliases" in facts
    image_aliases = facts["ImageAliases"]

    # From zone region facts
    assert "ubuntu-22" in image_aliases
    assert "amazon-linux-2" in image_aliases
    assert "postgresql-14" in image_aliases or "Postgresql14" in image_aliases

    # From app facts (should merge/override)
    assert "api-gateway" in image_aliases
    assert "core-api" in image_aliases
    assert "worker-service" in image_aliases
    assert image_aliases["api-gateway"] == "ami-0c02fb55956c7d316"

    # ========== Proxy Configuration Assertions ==========
    assert "ProxyHost" in facts
    assert "ProxyPort" in facts
    assert "ProxyUrl" in facts
    assert "NoProxy" in facts
    assert facts["ProxyHost"] == "proxy.acme.com"
    assert facts["ProxyPort"] == 8080
    assert facts["ProxyUrl"] == "http://proxy.acme.com:8080"

    # Proxy array should also exist
    if "Proxy" in facts:
        proxy_list = facts["Proxy"]
        assert len(proxy_list) >= 1
        assert proxy_list[0]["Host"] == "proxy.acme.com"
        assert proxy_list[0]["Port"] == "8080"

    # ========== DNS Configuration Assertions ==========
    assert "NameServers" in facts
    name_servers = facts["NameServers"]
    assert "8.8.8.8" in name_servers
    assert "1.1.1.1" in name_servers
    assert len(name_servers) >= 3

    # ========== Portfolio Configuration Assertions ==========
    # From portfolio_facts
    assert "Domain" in facts
    assert facts["Domain"] == "platform.acme.com"

    assert "Project" in facts
    project = facts["Project"]
    assert project["Name"] == "ACME Enterprise Platform"
    assert project["Code"] == "AEP"
    assert project["Repository"] == "https://github.com/acme/enterprise-platform"

    assert "Owner" in facts
    owner = facts["Owner"]
    assert owner["Name"] == "Sarah Johnson"
    assert owner["Email"] == "sarah.johnson@acme.com"
    assert owner["Phone"] == "+1-555-0199"

    assert "Contacts" in facts
    contacts = facts["Contacts"]
    assert len(contacts) == 4  # Should have 4 contacts including emergency
    contact_names = [c["Name"] for c in contacts]
    assert "David Kim" in contact_names
    assert "Lisa Chen" in contact_names
    assert "Mark Rodriguez" in contact_names
    assert "Emergency Hotline" in contact_names

    assert "Approvers" in facts
    approvers = facts["Approvers"]
    assert len(approvers) == 4
    assert approvers[0]["Name"] == "David Kim"
    assert approvers[1]["Name"] == "Sarah Johnson"

    # ========== Application Configuration Assertions ==========
    # From app_facts
    assert "Zone" in facts
    assert facts["Zone"] == "prod-east-primary"
    assert "Region" in facts
    assert facts["Region"] == "us-east-1"
    assert "Account" in facts
    assert facts["Account"] == "123456789012"
    assert "Repository" in facts
    assert facts["Repository"] == "https://github.com/acme/enterprise-platform"
    assert "EnforceValidation" in facts
    assert facts["EnforceValidation"] == "true"

    # Application metadata should be present
    assert "Metadata" in facts
    metadata = facts["Metadata"]
    assert "deployment_strategy" in metadata
    assert metadata["deployment_strategy"] == "blue_green"
    assert "container_orchestration" in metadata
    assert metadata["container_orchestration"] == "ecs_fargate"
    assert "database_engine" in metadata
    assert metadata["database_engine"] == "postgresql"

    # ========== Merged Tags Assertions ==========
    assert "Tags" in facts
    tags = facts["Tags"]

    # Deployment details tags
    assert tags["Team"] == "platform-engineering"
    assert tags["CostCenter"] == "CC-IT-001"
    assert tags["Project"] == "enterprise-platform"
    assert tags["BusinessUnit"] == "IT Operations"
    assert tags["Criticality"] == "tier1"
    assert tags["Version"] == "1.2.0"

    # Environment and region from derivation
    assert tags["Environment"] == "production"
    assert tags["Region"] == "us-east-1"

    # Owner and contacts formatted
    assert "Owner" in tags
    assert "sarah.johnson" in tags["Owner"].lower()
    assert "Contacts" in tags

    # App-level tags should be present
    assert tags["Application"] == "acme-enterprise-platform"
    assert tags["Component"] == "core-platform"
    assert tags["ServiceLevel"] == "24x7-premium-support"
    assert tags["Compliance"] == "soc2-hipaa-pci"

    # Zone-level tags should be present
    assert tags["DataClassification"] == "confidential"
    assert tags["DisasterRecovery"] == "multi-region-active"
    assert tags["MonitoringLevel"] == "enhanced"

    # ========== Compiler/Artifact Facts Assertions ==========
    # From get_compiler_facts()
    assert "ArtefactsBucketName" in facts
    assert "ArtifactBucketName" in facts  # Both spellings
    assert facts["ArtefactsBucketName"] == facts["ArtifactBucketName"]

    assert "ArtefactsBucketRegion" in facts
    assert "ArtifactBucketRegion" in facts

    assert "ArtifactKeyPrefix" in facts
    artifact_key = facts["ArtifactKeyPrefix"]
    assert "acme" in artifact_key.lower()
    assert "acme-enterprise-platform" in artifact_key
    assert "acme-api-core" in artifact_key
    assert "main" in artifact_key
    assert "1.2.0" in artifact_key

    assert "BuildFilesPrefix" in facts
    build_files = facts["BuildFilesPrefix"]
    assert "files" in build_files
    assert "acme-enterprise-platform" in build_files
    assert "acme-api-core" in build_files

    assert "PortfolioFilesPrefix" in facts
    assert "AppFilesPrefix" in facts
    assert "BranchFilesPrefix" in facts
    assert "SharedFilesPrefix" in facts

    # ========== Data Structure Validation ==========
    # Ensure facts is a dictionary
    assert isinstance(facts, dict)

    # Ensure no None values in critical paths
    critical_keys = ["Client", "Portfolio", "App", "AwsAccountId", "AwsRegion", "Environment"]
    for key in critical_keys:
        assert facts.get(key) is not None, f"Critical key {key} should not be None"

    # Ensure tags is a flat dictionary
    assert isinstance(facts["Tags"], dict)
    for tag_key, tag_value in facts["Tags"].items():
        assert isinstance(tag_key, str), f"Tag key {tag_key} should be string"
        assert isinstance(tag_value, (str, int, float, bool)), f"Tag value for {tag_key} should be primitive type"

    # ========== Integration Validation ==========
    # Verify that zone matches app configuration
    assert facts["Zone"] == "prod-east-primary"
    assert facts["Account"] == facts["AwsAccountId"]
    assert facts["Region"] == facts["AwsRegion"]

    # Verify portfolio consistency
    assert facts["Portfolio"] == "acme-enterprise-platform"
    assert "acme" in facts["Domain"]

    print("✅ All facts validation passed!")
    print(f"📊 Facts dictionary contains {len(facts)} top-level keys")
    print(f"🏷️  Tags dictionary contains {len(facts['Tags'])} tags")
    print(f"🖼️  ImageAliases contains {len(facts['ImageAliases'])} images")
    print(f"👥 Contacts list contains {len(facts['Contacts'])} contacts")
    print(f"✅ Approvers list contains {len(facts['Approvers'])} approvers")
