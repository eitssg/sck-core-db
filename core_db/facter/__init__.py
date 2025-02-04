"""The Facter module contains the function and classes to create a VIEW on the Registry.

Combines data from tables:

- core-automation-clients
- core-automation-portfolios
- core-automation-zones
- core-automation-apps

Once data is combined, it's presented as create dictoinary of values (a View) for the Jinja2
render context when filling out Cloudformation tempaltes.

Example of facts would be:

.. code-block:: yaml

    Client: sample
    Zone: samlple-app-one-production-zone
    AccountName: Sample AWS Account
    AwsAccountId: "738499099231"
    CustomResourceExportName: core-cfndelta-lambda-handler:FunctionArn
    Environment: nonprod
    Kms:
       AwsAccountId: "624172648832"
       DelegateAwsAccountIds:
          - "738499099231"
       KmsKeyArn: arn:aws:logs:*:*:*
       KmsKey: THEKMSKEY
    VpcAliases:
       public: Vpc1
       private: Vpc1
    SubnetAliases:
       public: PublicSubnet
       app: PrivateSubnet
       private: PrivateSubnet
    Tags:
       AppGroup: NECportal
       CostCenter: TLNU0101
    ResourceNamespace: core
    Region: sin
    AwsRegion: ap-southeast-1
    AzCount: 3
    ImageAliases:
       amazon-linux-2: ami-0e2e44c03b85f58b3
       amazon-linux-2-CIS-202302_1: ami-0a11473dc50b85280
       rhel-8-CIS-202302_1: ami-0973e43f957605141
       amazon-linux-2-CIS-202303_1: ami-02daa8039d9fc9f5c
       rhel-8-CIS-202303_1: ami-0b40f087bb156581c
       amazon-linux-2-CIS-202304_1: ami-0759ae797112c4bdb
    StaticWebsiteImageAlias: amazon-linux-2
    MinSuccessfulInstancesPercent: 100
    SecurityAliases:
       public-internet:
          - { Type: cidr, Value: 0.0.0.0/0, Description: Internet }
       intranet:
          - { Type: cidr, Value: 10.0.0.0/8, Description: Summary route to on-prem }
       private-subnet:
          - { Type: cidr, Value: 10.0.201.0/27, Description: Private Subnet }
          - { Type: cidr, Value: 10.0.201.32/27, Description: Private Subnet }
          - { Type: cidr, Value: 10.0.201.64/27, Description: Private Subnet }
       data-subnet:
          - { Type: cidr, Value: 10.0.201.128/27, Description: Data Subnet }
          - { Type: cidr, Value: 10.0.201.160/27, Description: Data Subnet }
          - { Type: cidr, Value: 10.0.201.192/27, Description: Data Subnet }
       network-subnet:
          - { Type: cidr, Value: 10.175.96.0/23, Description: network  Subnet }
       imperva-public-ip:
          - { Type: cidr, Value: 199.83.128.0/21, Description: WAF IP }
          - { Type: cidr, Value: 198.143.32.0/19, Description: WAF IP }
          - { Type: cidr, Value: 149.126.72.0/21, Description: WAF IP }
          - { Type: cidr, Value: 103.28.248.0/22, Description: WAF IP }
          - { Type: cidr, Value: 185.11.124.0/22, Description: WAF IP }
          - { Type: cidr, Value: 192.230.64.0/18, Description: WAF IP }
          - { Type: cidr, Value: 45.64.64.0/22, Description: WAF IP }
          - { Type: cidr, Value: 107.154.0.0/16, Description: WAF IP }
          - { Type: cidr, Value: 45.60.0.0/16, Description: WAF IP }
          - { Type: cidr, Value: 45.223.0.0/16, Description: WAF IP }
          - { Type: cidr, Value: 131.125.128.0/17, Description: WAF IP }
       whitelist:
          - { Type: cidr, Value: 13.229.36.48/32, Description: Build Nat Gateway }
          - { Type: cidr, Value: 52.220.200.25/32, Description: Build Nat Gateway }
       cgnat-subnet:
          - { Type: cidr, Value: 100.65.128.0/20, Description: Sec Private Subnet }
       apigw1:
          - { Type: cidr, Value: 34.87.26.15/32, Description: apigw IP 1 }
       apigw2:
          - { Type: cidr, Value: 34.87.26.16/32, Description: apigw IP 2 }
       cloudfront-prefix:
          - {
               Type: prefix,
               Value: pl-31a34658,
               Description: Cloudfront PrefixList ID,
            }
    ProxyUrl: "http://myprox.net:8080"
    NoProxy: 127.0.0.1,localhost,169.254.169.253,169.254.169.254,s3-ap-southeast-1.amazonaws.com,dynamodb.ap-southeast-1.amazonaws.com,10.*
    SecurityGroupAliases:
       - public-internet: sg-0b1b3b3b3b3b3b3b3
    Repository: https://sourcecode.com/repo.git
    Approvers:
       - Sequence: 1
         Email: sample@me.com
         Name: Sample
         Enabled: true
         DependsOn: []
    Contacts:
       - Email: contact@me.com
         Name: Contact
         Enabled: true
    Owner:
        Email: owner@me.com
        Name: Owner
    NameServers:
       - 10.175.96.133
       - 10.175.96.5
       - 10.175.96.69

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
    "FactsActions",
]
