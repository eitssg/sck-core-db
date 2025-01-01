from core_framework.status import DEPLOY_COMPLETE, COMPILE_COMPLETE, COMPILE_IN_PROGRESS

test_data = [
    # Case 0
    (
        {
            "action": "portfolio:create",
            "data": {
                "prn": "prn:portfolio",
                "name": "Portfolio One",
                "contact_email": "test@gmail.com",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "contact_email": "test@gmail.com",
                "item_type": "portfolio",
                "name": "Portfolio One",
                "parent_prn": "prn",
                "prn": "prn:portfolio",
            },
        },
    ),
    # Case 1
    (
        {"action": "portfolio:list", "data": {"prn": "prn:portfolio"}},
        {
            "status": "ok",
            "code": 200,
            "data": [
                {
                    "contact_email": "test@gmail.com",
                    "item_type": "portfolio",
                    "name": "Portfolio One",
                    "parent_prn": "prn",
                    "prn": "prn:portfolio",
                }
            ],
        },
    ),
    # Case 2
    (
        {
            "action": "portfolio:update",
            "data": {"prn": "prn:portfolio", "contact_email": "test2@gmail.com"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "contact_email": "test2@gmail.com",
                "item_type": "portfolio",
                "name": "Portfolio One",
                "parent_prn": "prn",
                "prn": "prn:portfolio",
            },
        },
    ),
    # Case 3
    (
        {"action": "portfolio:get", "data": {"prn": "prn:portfolio"}},
        {
            "status": "ok",
            "code": 200,
            "data": {
                "contact_email": "test2@gmail.com",
                "item_type": "portfolio",
                "name": "Portfolio One",
                "parent_prn": "prn",
                "prn": "prn:portfolio",
            },
        },
    ),
    # Case 4
    (
        {"action": "portfolio:delete", "data": {"prn": "prn:portfolio"}},
        {"status": "ok", "code": 200, "data": "Item deleted: prn:portfolio"},
    ),
    # Case 5
    (
        {
            "action": "portfolio:create",
            "data": {
                "prn": "prn:portfolio",
                "name": "Portfolio One",
                "contact_email": "test@gmail.com",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "contact_email": "test@gmail.com",
                "item_type": "portfolio",
                "name": "Portfolio One",
                "parent_prn": "prn",
                "prn": "prn:portfolio",
            },
        },
    ),
    # Case 6
    (
        {
            "action": "app:create",
            "data": {
                "prn": "prn:portfolio:app",
                "portfolio_prn": "prn:portfolio",
                "name": "App One",
                "contact_email": "me@gmail.com",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "contact_email": "me@gmail.com",
                "item_type": "app",
                "name": "App One",
                "parent_prn": "prn:portfolio",
                "portfolio_prn": "prn:portfolio",
                "prn": "prn:portfolio:app",
            },
        },
    ),
    # Case 7
    (
        {
            "action": "app:list",
            "data": {"prn": "prn:portfolio:app", "portfolio_prn": "prn:portfolio"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": [
                {
                    "contact_email": "me@gmail.com",
                    "item_type": "app",
                    "name": "App One",
                    "parent_prn": "prn:portfolio",
                    "portfolio_prn": "prn:portfolio",
                    "prn": "prn:portfolio:app",
                }
            ],
        },
    ),
    # Case 8
    (
        {
            "action": "app:update",
            "data": {
                "prn": "prn:portfolio:app",
                "portfolio_prn": "prn:portfolio",
                "name": "App One",
                "contact_email": "me2@gmail.com",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "contact_email": "me2@gmail.com",
                "item_type": "app",
                "name": "App One",
                "parent_prn": "prn:portfolio",
                "portfolio_prn": "prn:portfolio",
                "prn": "prn:portfolio:app",
            },
        },
    ),
    # Case 9
    (
        {
            "action": "app:get",
            "data": {"prn": "prn:portfolio:app", "portfolio_prn": "prn:portfolio"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "contact_email": "me2@gmail.com",
                "item_type": "app",
                "name": "App One",
                "parent_prn": "prn:portfolio",
                "portfolio_prn": "prn:portfolio",
                "prn": "prn:portfolio:app",
            },
        },
    ),
    # Case 10
    (
        {
            "action": "app:delete",
            "data": {"prn": "prn:portfolio:app", "portfolio_prn": "prn:portfolio"},
        },
        {"status": "ok", "code": 200, "data": "Item deleted: prn:portfolio:app"},
    ),
    # Case 11
    (
        {
            "action": "app:create",
            "data": {
                "prn": "prn:portfolio:app",
                "portfolio_prn": "prn:portfolio",
                "name": "App One",
                "contact_email": "me@gmail.com",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "contact_email": "me@gmail.com",
                "item_type": "app",
                "parent_prn": "prn:portfolio",
                "portfolio_prn": "prn:portfolio",
                "prn": "prn:portfolio:app",
                "name": "App One",
                "contact_email": "me@gmail.com",
            },
        },
    ),
    # Case 12
    (
        {
            "action": "branch:create",
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "name": "Branch One",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "name": "Branch One",
            },
        },
    ),
    # Case 13
    (
        {
            "action": "branch:list",
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": [
                {
                    "prn": "prn:portfolio:app:branch",
                    "portfolio_prn": "prn:portfolio",
                    "app_prn": "prn:portfolio:app",
                    "name": "Branch One",
                }
            ],
        },
    ),
    # Case 14
    (
        {
            "action": "branch:update",
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "name": "Branch One 2",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "name": "Branch One 2",
            },
        },
    ),
    # Case 15
    (
        {
            "action": "branch:get",
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "name": "Branch One 2",
            },
        },
    ),
    # Case 16
    (
        {
            "action": "branch:delete",
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
            },
        },
        {"status": "ok", "code": 200, "data": "Item deleted: prn:portfolio:app:branch"},
    ),
    # Case 17
    (
        {
            "action": "branch:create",
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "name": "Branch One",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "name": "Branch One",
            },
        },
    ),
    # Case 18
    (
        {
            "action": "build:create",
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "name": "Build One",
                "status": COMPILE_IN_PROGRESS,
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "name": "Build One",
                "status": COMPILE_IN_PROGRESS,
            },
        },
    ),
    # Case 19
    (
        {
            "action": "build:list",
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": [
                {
                    "prn": "prn:portfolio:app:branch:build",
                    "portfolio_prn": "prn:portfolio",
                    "app_prn": "prn:portfolio:app",
                    "branch_prn": "prn:portfolio:app:branch",
                    "name": "Build One",
                    "status": COMPILE_IN_PROGRESS,
                }
            ],
        },
    ),
    # Case 20
    (
        {
            "action": "build:update",
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "name": "Build One 2",
                "status": COMPILE_COMPLETE,
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "name": "Build One 2",
                "status": COMPILE_COMPLETE,
            },
        },
    ),
    # Case 21
    (
        {
            "action": "build:get",
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "name": "Build One 2",
                "status": COMPILE_COMPLETE,
            },
        },
    ),
    # Case 22
    (
        {
            "action": "build:delete",
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": "Item deleted: prn:portfolio:app:branch:build",
        },
    ),
    # Case 23
    (
        {
            "action": "build:create",
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "name": "Build One",
                "status": COMPILE_COMPLETE,
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "name": "Build One",
                "status": COMPILE_COMPLETE,
            },
        },
    ),
    # Case 24
    (
        {
            "action": "component:create",
            "data": {
                "prn": "prn:portfolio:app:branch:build:component",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "build_prn": "prn:portfolio:app:branch:build",
                "name": "Component One",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch:build:component",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "build_prn": "prn:portfolio:app:branch:build",
                "name": "Component One",
            },
        },
    ),
    # Case 25
    (
        {
            "action": "component:list",
            "data": {
                "prn": "prn:portfolio:app:branch:build:component",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "build_prn": "prn:portfolio:app:branch:build",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": [
                {
                    "prn": "prn:portfolio:app:branch:build:component",
                    "portfolio_prn": "prn:portfolio",
                    "app_prn": "prn:portfolio:app",
                    "branch_prn": "prn:portfolio:app:branch",
                    "build_prn": "prn:portfolio:app:branch:build",
                    "name": "Component One",
                }
            ],
        },
    ),
    # Case 26
    (
        {
            "action": "component:update",
            "data": {
                "prn": "prn:portfolio:app:branch:build:component",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "build_prn": "prn:portfolio:app:branch:build",
                "name": "Component One 2",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch:build:component",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "build_prn": "prn:portfolio:app:branch:build",
                "name": "Component One 2",
            },
        },
    ),
    # Case 27
    (
        {
            "action": "component:get",
            "data": {
                "prn": "prn:portfolio:app:branch:build:component",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "build_prn": "prn:portfolio:app:branch:build",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch:build:component",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "build_prn": "prn:portfolio:app:branch:build",
                "name": "Component One 2",
            },
        },
    ),
    # Case 28
    (
        {
            "action": "component:delete",
            "data": {
                "prn": "prn:portfolio:app:branch:build:component",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "build_prn": "prn:portfolio:app:branch:build",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": "Item deleted: prn:portfolio:app:branch:build:component",
        },
    ),
    # Case 29
    (
        {
            "action": "event:create",
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "status": DEPLOY_COMPLETE,
                "message": "Deployment Complete",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "prn": "prn:portfolio:app:branch:build",
                "status": DEPLOY_COMPLETE,
                "message": "Deployment Complete",
            },
        },
    ),
    # Case 30
    (
        {
            "action": "event:list",
            "data": {"prn": "prn:portfolio:app:branch:build"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": [
                {
                    "prn": "prn:portfolio:app:branch:build",
                    "status": DEPLOY_COMPLETE,
                    "message": "Deployment Complete",
                }
            ],
        },
    ),
    # Case 31
    (
        {
            "action": "event:delete",
            "data": {"prn": "prn:portfolio:app:branch:build"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": "Event deleted: prn:portfolio:app:branch:build",
        },
    ),
    # Case 32
    (
        {
            "action": "registry:client:create",
            "data": {"Client": "client"},
        },
        {"status": "ok", "code": 200, "data": {"Client": "client"}},
    ),
    # Case 33
    (
        {
            "action": "registry:client:list",
            "data": {"Client": "client"},
        },
        {"status": "ok", "code": 200, "data": ["client"]},
    ),
    # Case 34
    (
        {
            "action": "registry:client:update",
            "data": {"Client": "client"},
        },
        {"status": "ok", "code": 200, "data": {"Client": "client"}},
    ),
    # Case 35
    (
        {
            "action": "registry:client:get",
            "data": {"Client": "client"},
        },
        {"status": "ok", "code": 200, "data": {"Client": "client"}},
    ),
    # Case 36
    (
        {
            "action": "registry:client:delete",
            "data": {"Client": "client"},
        },
        {"status": "ok", "code": 200, "data": "Client client deleted"},
    ),
    # Case 37
    (
        {
            "action": "registry:client:create",
            "data": {"Client": "client"},
        },
        {"status": "ok", "code": 200, "data": {"Client": "client"}},
    ),
    # Case 38
    (
        {
            "action": "registry:portfolio:create",
            "data": {"Client": "client", "Portfolio": "portfolio"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": {"Client": "client", "Portfolio": "portfolio"},
        },
    ),
    # Case 39
    (
        {
            "action": "registry:portfolio:list",
            "data": {"Client": "client"},
        },
        {"status": "ok", "code": 200, "data": ["portfolio"]},
    ),
    # Case 40
    (
        {
            "action": "registry:portfolio:get",
            "data": {"Client": "client", "Portfolio": "portfolio"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": {"Client": "client", "Portfolio": "portfolio"},
        },
    ),
    # Case 41
    (
        {
            "action": "registry:portfolio:update",
            "data": {"Client": "client", "Portfolio": "portfolio"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": {"Client": "client", "Portfolio": "portfolio"},
        },
    ),
    # Case 42
    (
        {
            "action": "registry:portfolio:delete",
            "data": {"Client": "client", "Portfolio": "portfolio"},
        },
        {"status": "ok", "code": 200, "data": "Portfolio deleted: client:portfolio"},
    ),
    # Case 43
    (
        {
            "action": "registry:portfolio:create",
            "data": {"Client": "client", "Portfolio": "portfolio"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": {"Client": "client", "Portfolio": "portfolio"},
        },
    ),
    # Case 44
    (
        {
            "action": "registry:app:create",
            "data": {
                "client": "client",
                "portfolio": "portfolio",
                "app-regex": r"^app(.*)$",
                "region": "sin",
                "zone": "the-primary-zone",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "ClientPortfolio": "client:portfolio",
                "AppRegex": r"^app(.*)$",
                "Region": "sin",
                "Zone": "the-primary-zone",
            },
        },
    ),
    # Case 45
    (
        {
            "action": "registry:app:list",
            "data": {"client-portfolio": "client:portfolio"},
        },
        {"status": "ok", "code": 200, "data": [r"^app(.*)$"]},
    ),
    # Case 46
    (
        {
            "action": "registry:app:update",
            "data": {
                "client-portfolio": "client:portfolio",
                "app-regex": r"^app(.*)$",
                "Region": "sea",
                "Zone": "the-secondary-zone",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "ClientPortfolio": "client:portfolio",
                "AppRegex": r"^app(.*)$",
                "Region": "sea",
                "Zone": "the-secondary-zone",
            },
        },
    ),
    # Case 47
    (
        {
            "action": "registry:app:get",
            "data": {"client-portfolio": "client:portfolio", "app-regex": r"^app(.*)$"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "ClientPortfolio": "client:portfolio",
                "AppRegex": r"^app(.*)$",
                "Region": "sea",
                "Zone": "the-secondary-zone",
            },
        },
    ),
    # Case 48
    (
        {
            "action": "registry:app:delete",
            "data": {"client-portfolio": "client:portfolio", "app-regex": r"^app(.*)$"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": "App [client:portfolio:^app(.*)$] deleted",
        },
    ),
    # Case 49
    (
        {
            "action": "registry:app:create",
            "data": {
                "client-portfolio": "client:portfolio",
                "app-regex": r"^app(.*)$",
                "Region": "sin",
                "Zone": "the-primary-zone",
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "ClientPortfolio": "client:portfolio",
                "AppRegex": r"^app(.*)$",
                "Region": "sin",
                "Zone": "the-primary-zone",
            },
        },
    ),
    # Case 50
    (
        {
            "action": "registry:zone:create",
            "data": {
                "Client": "client",
                "Zone": "zone-one",
                "AccountFacts": {
                    "AwsAccountId": "123456789012",
                    "Kms": {
                        "AwsAccountId": "123456789012",
                        "DelegateAwsAccountIds": ["123456789012"],
                    },
                },
                "RegionFacts": {"sin": {"AwsRegion": "ap-southeast-1", "AzCount": 3}},
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "Client": "client",
                "Zone": "zone-one",
                "AccountFacts": {
                    "AwsAccountId": "123456789012",
                    "Kms": {
                        "AwsAccountId": "123456789012",
                        "DelegateAwsAccountIds": ["123456789012"],
                    },
                },
                "RegionFacts": {"sin": {"AwsRegion": "ap-southeast-1", "AzCount": 3}},
            },
        },
    ),
    # Case 51
    (
        {
            "action": "registry:zone:list",
            "data": {"Client": "client", "Zone": "zone-one"},
        },
        {"status": "ok", "code": 200, "data": ["zone-one"]},
    ),
    # Case 52
    (
        {
            "action": "registry:zone:get",
            "data": {"Client": "client", "Zone": "zone-one"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "Client": "client",
                "Zone": "zone-one",
                "AccountFacts": {
                    "AwsAccountId": "123456789012",
                    "Kms": {
                        "AwsAccountId": "123456789012",
                        "DelegateAwsAccountIds": ["123456789012"],
                    },
                },
                "RegionFacts": {"sin": {"AwsRegion": "ap-southeast-1", "AzCount": 3}},
            },
        },
    ),
    # Case 53
    (
        {
            "action": "registry:zone:update",
            "data": {
                "Client": "client",
                "Zone": "zone-one",
                "AccountFacts": {
                    "AwsAccountId": "123456789012",
                    "Kms": {
                        "AwsAccountId": "123456789012",
                        "DelegateAwsAccountIds": ["123456789012"],
                    },
                },
                "RegionFacts": {"sin": {"AwsRegion": "ap-southeast-1", "AzCount": 3}},
            },
        },
        {
            "status": "ok",
            "code": 200,
            "data": {
                "Client": "client",
                "Zone": "zone-one",
                "AccountFacts": {
                    "AwsAccountId": "123456789012",
                    "Kms": {
                        "AwsAccountId": "123456789012",
                        "DelegateAwsAccountIds": ["123456789012"],
                    },
                },
                "RegionFacts": {"sin": {"AwsRegion": "ap-southeast-1", "AzCount": 3}},
            },
        },
    ),
    # Case 54
    (
        {
            "action": "registry:zone:delete",
            "data": {"Client": "client", "Zone": "zone-one"},
        },
        {
            "status": "ok",
            "code": 200,
            "data": "Zone deleted: zone-one",
        },
    ),
]
