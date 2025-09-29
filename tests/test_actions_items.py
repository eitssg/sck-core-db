import pytest

from core_db.event import EventItem
from core_db.item.portfolio import PortfolioActions, PortfolioItem
from core_db.item.app import AppActions, AppItem
from core_db.item.branch import BranchActions, BranchItem
from core_db.item.build import BuildActions, BuildItem
from core_db.item.component import ComponentActions, ComponentItem

from .bootstrap import *

client = util.get_client()

"""Create a portfolio item - foundation for all other tests."""
portfolio_data = {
    "name": "test-portfolio",
    "contact_email": "test@example.com",
    "metadata": {
        "tags": {"environment": "test", "team": "qa"},
        "description": "Test portfolio for integration tests",
    },
}
app_data = {
    "portfolio": "test-portfolio",
    "name": "test-app",
    "contact_email": "app-team@example.com",
    "metadata": {
        "description": "Test application for integration tests",
        "repository_url": "https://github.com/test/test-app.git",
        "tags": {"language": "python", "framework": "fastapi"},
    },
}
branch_data = {
    "portfolio": "test-portfolio",
    "app": "test-app",
    "name": "main",
    "metadata": {
        "description": "Main branch for test application",
        "source_branch": "master",
        "tags": {"type": "main", "protected": "true"},
    },
}

build_data = {
    "portfolio": "test-portfolio",
    "app": "test-app",
    "branch": "main",
    "build": "1.0.0",
    "name": "1.0.0",
    "metadata": {
        "description": "Test build for integration tests",
        "commit_hash": "abc123def456",
        "tags": {"type": "release", "environment": "test"},
    },
}

component_data = {
    "portfolio": "test-portfolio",
    "app": "test-app",
    "branch": "main",
    "build": "1.0.0",
    "name": "api-gateway",
    "component_type": "service",
    "metadata": {
        "description": "API Gateway component for test application",
        "tags": {
            "type": "gateway",
            "protocol": "https",
        },
    },
}

# Global test data to maintain state across dependent tests
test_data = {
    "portfolio": portfolio_data,
    "app": app_data,
    "branch": branch_data,
    "build": build_data,
    "component": component_data,
}

#############################################
# Portfolio Item Actions Tests
#############################################


def test_portfolio_items_create(bootstrap_dynamo):

    response: PortfolioItem = PortfolioActions.create(client=client, **portfolio_data)

    assert isinstance(response, PortfolioItem)
    assert response.name == portfolio_data["name"]
    assert response.contact_email == portfolio_data["contact_email"]
    assert response.metadata["tags"]["environment"] == "test"

    # Store for dependent tests
    test_data["portfolio"] = response
    print(f"✅ Created portfolio: {response.prn}")


def test_portfolio_items_list():
    """List portfolio items - depends on create test."""

    portfolio_prn = "prn:test-portfolio"

    response, paginator = PortfolioActions.list(client=client, prn=portfolio_prn)

    assert isinstance(response, list)
    assert len(response) >= 1, "Should find at least the created portfolio"
    assert paginator.total_count >= 1

    # Verify we can find our created portfolio
    found = False
    for item in response:
        if item.prn == portfolio_prn:
            found = True
            break

    assert found, f"Should find portfolio {portfolio_prn} in list results"
    print(f"✅ Listed portfolios, found: {len(response)} items")


def test_portfolio_items_update():
    """Update portfolio item - depends on list test."""
    assert test_data["portfolio"] is not None, "Portfolio create and list tests must run first"

    portfolio_prn = "prn:test-portfolio"

    update_data = {
        "prn": portfolio_prn,
        "contact_email": "updated@example.com",
        "metadata": {
            "tags": {"environment": "test", "team": "qa", "updated": "true"},
            "description": "Updated test portfolio description",
        },
    }

    response: PortfolioItem = PortfolioActions.update(client=client, **update_data)

    assert isinstance(response, PortfolioItem)
    assert response.contact_email == update_data["contact_email"]

    # Update stored data
    test_data["portfolio"] = response
    print(f"✅ Updated portfolio: {portfolio_prn}")


def test_portfolio_items_delete():
    """Delete portfolio item - depends on update test."""
    assert test_data["portfolio"] is not None, "Portfolio create, list, and update tests must run first"

    portfolio_prn = "prn:test-portfolio"

    response: bool = PortfolioActions.delete(client=client, prn=portfolio_prn)

    assert response is True
    print(f"✅ Deleted portfolio: {portfolio_prn}")


#############################################
# App Item Actions Tests
#############################################


def test_app_items_create(bootstrap_dynamo):
    """Create an app item - depends on portfolio being available."""

    response: AppItem = AppActions.create(client=client, **app_data)

    assert isinstance(response, AppItem)
    assert response.name == app_data["name"]
    assert response.portfolio_prn == "prn:test-portfolio"
    assert response.contact_email == app_data["contact_email"]

    # Store for dependent tests
    test_data["app"] = response
    print(f"✅ Created app: {response.prn}")


def test_app_items_list():
    """List app items - depends on create test."""
    assert test_data["app"] is not None, "App create test must run first"

    app_prn = "prn:test-portfolio:test-app"

    response, paginator = AppActions.list(client=client, prn=app_prn)

    assert isinstance(response, list)
    assert len(response) >= 1, "Should find at least the created app"

    # Verify we can find our created app
    found = False
    for item in response:
        if item.prn == app_prn:
            found = True
            break

    assert found, f"Should find app {app_prn} in list results"
    print(f"✅ Listed apps, found: {len(response)} items")


def test_app_items_update():
    """Update app item - depends on list test."""
    assert test_data["app"] is not None, "App create and list tests must run first"

    app_prn = "prn:test-portfolio:test-app"

    update_data = {
        "prn": app_prn,
        "contact_email": "updated-app-team@example.com",
        "metadata": {
            "description": "Updated test application description",
            "repository_url": "https://github.com/test/updated-test-app.git",
            "tags": {"language": "python", "framework": "fastapi", "updated": "true"},
        },
    }

    response: AppItem = AppActions.update(client=client, **update_data)

    assert isinstance(response, AppItem)

    assert response.contact_email == update_data["contact_email"]

    # Update stored data
    test_data["app"] = response
    print(f"✅ Updated app: {app_prn}")


def test_app_items_delete():
    """Delete app item - depends on update test."""
    assert test_data["app"] is not None, "App create, list, and update tests must run first"

    app_prn = "prn:test-portfolio:test-app"

    response: bool = AppActions.delete(client=client, prn=app_prn)

    assert response is True
    print(f"✅ Deleted app: {app_prn}")


#############################################
# Branch Item Actions Tests
#############################################


def test_branch_items_create(bootstrap_dynamo):
    """Create a branch item - depends on app being available."""

    response: BranchItem = BranchActions.create(client=client, **branch_data)

    assert isinstance(response, BranchItem)
    assert response.name == branch_data["name"]
    assert response.app_prn == "prn:test-portfolio:test-app"

    # Store for dependent tests
    test_data["branch"] = response
    print(f"✅ Created branch: {response.prn}")


def test_branch_items_list():
    """List branch items - depends on create test."""
    assert test_data["branch"] is not None, "Branch create test must run first"

    branch_prn = "prn:test-portfolio:test-app:main"

    response, paginator = BranchActions.list(client=client, prn=branch_prn)

    assert isinstance(response, list)
    assert len(response) >= 1, "Should find at least the created branch"
    assert paginator.total_count >= 1

    # Verify we can find our created branch
    found = False
    for item in response:
        if item.prn == branch_prn:
            found = True
            break

    assert found, f"Should find branch {branch_prn} in list results"
    print(f"✅ Listed branches, found: {len(response)} items")


def test_branch_items_update():
    """Update branch item - depends on list test."""
    assert test_data["branch"] is not None, "Branch create and list tests must run first"

    branch_prn = "prn:test-portfolio:test-app:main"

    update_data = {
        "prn": branch_prn,
        "contact_email": "updated-branch-team@example.com",
        "released_build_prn": "prn:test-portfolio:test-app:main:1.0.0",
        "metadata": {
            "tags": {
                "updated": "true",
            },
            "description": "Updated main branch description",
        },
    }

    response: BranchItem = BranchActions.update(client=client, **update_data)

    assert isinstance(response, BranchItem)
    assert response.metadata is not None
    assert response.metadata["description"] == "Updated main branch description"
    assert response.metadata["tags"]["updated"] == "true"

    # The prn will be normalized as '.' characters are not allowed and replaced with '-'
    assert response.released_build.prn == "prn:test-portfolio:test-app:main:1-0-0"

    # Update stored data
    test_data["branch"] = response
    print(f"✅ Updated branch: {branch_prn}")


def test_branch_items_delete():
    """Delete branch item - depends on update test."""
    assert test_data["branch"] is not None, "Branch create, list, and update tests must run first"

    branch_prn = "prn:test-portfolio:test-app:main"

    response: bool = BranchActions.delete(client=client, prn=branch_prn)

    assert response is True
    print(f"✅ Deleted branch: {branch_prn}")


#############################################
# Build Item Actions Tests
#############################################


def test_build_items_create(bootstrap_dynamo):
    """Create a build item - depends on branch being available."""

    response: BuildItem = BuildActions.create(client=client, **build_data)

    assert isinstance(response, BuildItem)
    assert response.name == build_data["name"]
    assert response.branch_prn == "prn:test-portfolio:test-app:main"

    # The prn will be normalized as '.' characters are not allowed and replaced with '-'
    assert response.prn == "prn:test-portfolio:test-app:main:1-0-0"

    # Store for dependent tests
    test_data["build"] = response
    print(f"✅ Created build: {response.prn}")


def test_build_items_list():
    """List build items - depends on create test."""
    assert test_data["build"] is not None, "Build create test must run first"

    build_prn = "prn:test-portfolio:test-app:main:1-0-0"

    response, paginator = BuildActions.list(client=client, prn=build_prn)

    assert isinstance(response, list)
    assert len(response) >= 1, "Should find at least the created build"
    assert paginator.total_count >= 1

    # Verify we can find our created build
    found = False
    for item in response:
        if item.prn == build_prn:
            found = True
            break

    assert found, f"Should find build {build_prn} in list results"
    print(f"✅ Listed builds, found: {len(response)} items")


def test_build_items_update():
    """Update build item - depends on list test."""
    assert test_data["build"] is not None, "Build create and list tests must run first"

    build_prn = "prn:test-portfolio:test-app:main:1-0-0"

    update_data = {
        "prn": build_prn,
        "metadata": {
            "description": "Updated test build description",
            "tags": {"type": "release", "environment": "test", "updated": "true"},
            "updated": "true",
        },
    }

    response: BuildItem = BuildActions.update(client=client, **update_data)

    assert isinstance(response, BuildItem)
    assert response.metadata is not None
    assert response.metadata["description"] == "Updated test build description"
    assert response.metadata["tags"]["updated"] == "true"
    assert response.metadata["tags"]["type"] == "release"

    # Update stored data
    test_data["build"] = response
    print(f"✅ Updated build: {build_prn}")


def test_build_items_delete():
    """Delete build item - depends on update test."""
    assert test_data["build"] is not None, "Build create, list, and update tests must run first"

    build_prn = "prn:test-portfolio:test-app:main:1-0-0"

    response: bool = BuildActions.delete(client=client, prn=build_prn)

    assert response is True
    print(f"✅ Deleted build: {build_prn}")


#############################################
# Component Item Actions Tests
#############################################


def test_component_items_create(bootstrap_dynamo):
    """Create a component item - depends on build being available."""

    response: ComponentItem = ComponentActions.create(client=client, **component_data)

    assert isinstance(response, ComponentItem)
    assert response.name == component_data["name"]
    assert response.component_type == component_data["component_type"]
    assert response.build_prn == "prn:test-portfolio:test-app:main:1-0-0"

    # Store for dependent tests
    test_data["component"] = response
    print(f"✅ Created component: {response.prn}")


def test_component_items_list():
    """List component items - depends on create test."""
    assert test_data["component"] is not None, "Component create test must run first"

    component_prn = "prn:test-portfolio:test-app:main:1-0-0:api-gateway"

    response, paginator = ComponentActions.list(client=client, prn=component_prn)

    assert isinstance(response, list)
    assert len(response) >= 1, "Should find at least the created component"
    assert paginator.total_count >= 1

    # Verify we can find our created component
    found = False
    for item in response:
        if item.prn == component_prn:
            found = True
            break

    assert found, f"Should find component {component_prn} in list results"
    print(f"✅ Listed components, found: {len(response)} items")


def test_component_items_update():
    """Update component item - depends on list test."""
    assert test_data["component"] is not None, "Component create and list tests must run first"

    component_prn = "prn:test-portfolio:test-app:main:1-0-0:api-gateway"

    update_data = {
        "prn": component_prn,
        "metadata": {
            "description": "Updated API Gateway component description",
            "tags": {"type": "gateway", "protocol": "https", "updated": "true"},
        },
    }

    response: ComponentItem = ComponentActions.update(client=client, **update_data)

    assert isinstance(response, ComponentItem)
    assert response.metadata is not None
    assert response.metadata["description"] == "Updated API Gateway component description"
    assert response.metadata["tags"]["updated"] == "true"

    # Update stored data
    test_data["component"] = response.metadata
    print(f"✅ Updated component: {component_prn}")


def test_component_items_delete():
    """Delete component item - depends on update test."""
    assert test_data["component"] is not None, "Component create, list, and update tests must run first"

    component_prn = "prn:test-portfolio:test-app:main:1-0-0:api-gateway"

    response: bool = ComponentActions.delete(client=client, prn=component_prn)

    assert response is True
    print(f"✅ Deleted component: {component_prn}")
