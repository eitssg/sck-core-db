from unittest import result
import pytest
import datetime
from unittest.mock import patch

import core_framework as util

from core_db.profile.actions import ProfileActions
from core_db.profile.model import UserProfile
from core_db.response import Response, SuccessResponse, ErrorResponse
from core_db.exceptions import BadRequestException, NotFoundException, ConflictException

from .bootstrap import *

# Test client for all profile tests
client = util.get_client()


user_profiles = [
    {
        "user_id": "test_single_user123",
        "profile_name": "default",
        "email": "user1@gmail.com",
        "display_name": "User One(123) as Default",
        "first_name": "John",
        "last_name": "Doe",
        "theme": "dark",
        "is_active": True,
    },
    {
        "user_id": "test_single_user123",
        "profile_name": "admin",
        "email": "user2@gmail.com",
        "display_name": "User One(123) as Admin",
        "first_name": "John",
        "last_name": "Doe",
        "theme": "dark",
        "is_active": True,
    },
    {
        "user_id": "test_single_user123",
        "profile_name": "developer",
        "email": "user3@gmail.com",
        "display_name": "User One(123) as Developer",
        "first_name": "John",
        "last_name": "Doe",
        "theme": "dark",
        "is_active": False,
    },
    {
        "user_id": "test_single_user456",
        "profile_name": "personal",
        "email": "user1@gmail.com",
        "display_name": "User One(456) as Personal",
        "first_name": "Jane",
        "last_name": "Smith",
        "theme": "light",
        "is_active": True,
    },
    {
        "user_id": "test_single_user789",
        "profile_name": "work",
        "email": "user4@gmail.com",
        "display_name": "User One(789) as Work",
        "first_name": "Bob",
        "last_name": "Johnson",
        "theme": "dark",
        "is_active": True,
    },
]


# =============================================================================
# Basic CRUD Tests
# =============================================================================


def test_create_all_profiles(bootstrap_dynamo):
    """Test creating all test profiles."""
    for i, profile_data in enumerate(user_profiles):
        # Verify profile was saved
        data: UserProfile = ProfileActions.create(client=client, **profile_data)

        assert data is not None, f"Profile creation failed for {profile_data['profile_name']}"

        assert data.user_id == profile_data["user_id"]
        assert data.profile_name == profile_data["profile_name"]
        assert data.email == profile_data["email"]
        assert data.display_name == profile_data["display_name"]
        assert data.first_name == profile_data["first_name"]
        assert data.last_name == profile_data["last_name"]
        assert data.is_active == profile_data["is_active"]


def test_get_profiles_by_user():
    """Test getting all profiles for a specific user."""
    user_id = "test_single_user123"

    result, paginator = ProfileActions.list(client=client, user_id=user_id)

    assert result is not None, "No profiles found for user"
    assert isinstance(result, list)
    assert all(profile.user_id == user_id for profile in result)


def test_get_single_profile():
    """Test getting a specific profile by user_id and profile_name."""
    user_id = "test_single_user123"
    profile_name = "default"

    result: UserProfile = ProfileActions.get(client=client, user_id=user_id, profile_name=profile_name)

    assert result is not None, "Profile not found"
    assert isinstance(result, UserProfile)

    assert result.user_id == user_id
    assert result.profile_name == profile_name
    assert result.email == "user1@gmail.com"


def test_get_profiles_by_email():
    """Test getting profiles by email address."""
    email = "user1@gmail.com"

    result, paginator = ProfileActions.list(client=client, email=email)

    assert result is not None, "No profiles found for email"
    assert isinstance(result, list)
    assert len(result) == 2

    assert paginator.total_count == 2


def test_get_active_profiles_by_user():
    """Test getting only active profiles for a user."""
    user_id = "test_single_user123"

    result, paginator = ProfileActions.list(client=client, user_id=user_id, only_active=True)

    assert result is not None, "No active profiles found for user"
    assert isinstance(result, list)

    # Only the active profiles should be returned
    assert len(result) == 2

    for profile in result:
        assert profile.is_active is True


# =============================================================================
# Update/Patch Tests
# =============================================================================


def test_update_profile():
    """Test full profile update (PUT semantics)."""
    user_id = "test_single_user456"
    profile_name = "personal"

    # Update with new data
    update_data = {
        "client": client,
        "user_id": user_id,
        "profile_name": profile_name,
        "email": "updated@gmail.com",
        "display_name": "Updated Display Name",
        "first_name": "Updated First",
        "last_name": "Updated Last",
        "is_active": True,
    }

    result: UserProfile = ProfileActions.update(**update_data)
    assert isinstance(result, UserProfile)

    # Verify changes
    assert result.email == "updated@gmail.com"
    assert result.display_name == "Updated Display Name"
    assert result.first_name == "Updated First"
    assert result.last_name == "Updated Last"


def test_patch_profile():
    """Test partial profile update (PATCH semantics)."""
    user_id = "test_single_user456"
    profile_name = "personal"

    # Only update email and theme, leave other fields unchanged
    patch_data = {
        "client": client,
        "user_id": user_id,
        "profile_name": profile_name,
        "email": "patched@gmail.com",
        "theme": "dark",
    }

    result: UserProfile = ProfileActions.patch(**patch_data)
    assert isinstance(result, UserProfile)

    # Verify only specified fields changed
    assert result.email == "patched@gmail.com"
    # Other fields should remain from previous update
    assert result.display_name == "Updated Display Name"
    assert result.first_name == "Updated First"


def test_session_tracking_per_profile():
    """Test session tracking increment functionality."""
    user_id = "test_single_user123"
    profile_name = "default"

    # First increment (should start at 1)
    result1: UserProfile = ProfileActions.patch(
        client=client,
        user_id=user_id,
        profile_name=profile_name,
        increment_session="true",
    )

    assert isinstance(result1, UserProfile), "Failed to increment session count"
    assert result1 is not None, "No data returned after incrementing session"

    assert result1.session_count is not None and result1.session_count > 0, "Session count should be incremented"
    first_count = result1.session_count

    # Second increment (should increment further)
    result2: UserProfile = ProfileActions.patch(
        client=client,
        user_id=user_id,
        profile_name=profile_name,
        increment_session="true",
    )

    assert result2.session_count == first_count + 1, "Session count should increment by 1"
    assert result2.last_login is not None, "Last login should be updated"


# =============================================================================
# List/Pagination Tests
# =============================================================================


def test_list_profiles():
    """Test listing all profiles with basic pagination.

    We will NOT build a mechansim to fetch ALL profiles at once.
    """
    with pytest.raises(BadRequestException):
        ProfileActions.list(client=client, limit=3)


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_create_duplicate_profile():
    """Test creating duplicate profile should fail."""
    duplicate_data = user_profiles[0].copy()  # Use existing profile data

    with pytest.raises(ConflictException):
        ProfileActions.create(client=client, **duplicate_data)


def test_get_nonexistent_profile():
    """Test getting non-existent profile."""
    with pytest.raises(NotFoundException):
        ProfileActions.get(
            client=client,
            user_id="nonexistent_user",
            profile_name="nonexistent_profile",
        )


def test_get_nonexistent_email():
    """Test getting profiles for non-existent email."""
    with pytest.raises(NotFoundException):
        ProfileActions.list(client=client, email="nonexistent@example.com")


def test_update_nonexistent_profile():
    """Test updating non-existent profile."""
    with pytest.raises(NotFoundException):
        ProfileActions.update(
            client=client,
            user_id="nonexistent_user",
            profile_name="nonexistent_profile",
            email="test@example.com",
        )


def test_patch_nonexistent_profile():
    """Test patching non-existent profile."""
    with pytest.raises(NotFoundException):
        ProfileActions.patch(
            client=client,
            user_id="nonexistent_user",
            profile_name="nonexistent_profile",
            email="test@example.com",
        )


def test_missing_required_parameters():
    """Test various missing parameter scenarios."""

    # Missing user_id for get
    with pytest.raises(BadRequestException):
        ProfileActions.get(client=client, profile_name="test")

    # Missing user_id for update
    with pytest.raises(BadRequestException):
        ProfileActions.update(client=client, profile_name="test", email="test@example.com")

    # Missing profile_name for update
    with pytest.raises(BadRequestException):
        ProfileActions.update(client=client, user_id="test", email="test@example.com")


# =============================================================================
# Data Validation Tests
# =============================================================================


def test_create_invalid_profile_data():
    """Test creating profile with invalid data."""
    invalid_data = {
        "client": client,
        "user_id": "",  # Empty user_id
        "profile_name": "test",
        "email": "invalid-email",  # Invalid email format
        "is_active": "not_a_boolean",  # Invalid boolean
    }

    with pytest.raises(BadRequestException):
        ProfileActions.create(**invalid_data)


def test_create_missing_required_fields():
    """Test creating profile with missing required fields."""
    incomplete_data = {
        "client": client,
        "user_id": "test_user",
        # Missing profile_name - should fail
        "email": "test@example.com",
    }

    with pytest.raises(BadRequestException):
        ProfileActions.create(**incomplete_data)


# =============================================================================
# Delete Tests
# =============================================================================


def test_delete_single_profile():
    """Test deleting a specific profile."""
    user_id = "test_single_user789"
    profile_name = "work"

    # Verify profile exists first
    existing: UserProfile = ProfileActions.get(client=client, user_id=user_id, profile_name=profile_name)

    # Delete the profile
    ProfileActions.delete(client=client, user_id=user_id, profile_name=profile_name)

    # Verify profile is gone
    with pytest.raises(NotFoundException):
        ProfileActions.get(client=client, user_id=user_id, profile_name=profile_name)


def test_delete_by_email():
    """Test deleting all profiles with specific email."""
    email = "user2@gmail.com"

    # First verify profiles exist
    profiles_before, paginator = ProfileActions.list(client=client, email=email)
    assert len(profiles_before) > 0
    initial_count = len(profiles_before)

    # Delete by email
    ProfileActions.delete(client=client, email=email)

    # Verify profiles are gone
    with pytest.raises(NotFoundException):
        ProfileActions.list(client=client, email=email)

    assert len(profiles_before) == initial_count, "Should return count of deleted profiles"

    # Verify profiles are gone
    with pytest.raises(NotFoundException):
        ProfileActions.list(client=client, email=email)


def test_delete_user_by_user_id():
    """Test deleting all profiles for a user."""
    user_id = "test_single_user123"

    # Get initial count
    profiles_before, paginator = ProfileActions.list(client=client, user_id=user_id)
    initial_count = len(profiles_before)
    assert initial_count > 0, "Should have profiles to delete"

    # Delete the user profiles
    result: bool = ProfileActions.delete(client=client, user_id=user_id)

    assert result is True, "Failed to delete user profiles"

    # Verify the profiles no longer exist
    with pytest.raises(NotFoundException):
        ProfileActions.list(client=client, user_id=user_id)


def test_delete_nonexistent_profile():
    """Test deleting non-existent profile."""
    with pytest.raises(NotFoundException):
        ProfileActions.delete(
            client=client,
            user_id="nonexistent_user",
            profile_name="nonexistent_profile",
        )


# =============================================================================
# Client Isolation Tests
# =============================================================================


def test_client_isolation():
    """Test that different clients are properly isolated."""
    different_client = "acme"

    # Create profile in different client
    profile_data = {
        "user_id": "isolated_user",
        "profile_name": "isolated_profile",
        "email": "isolated@example.com",
        "display_name": "Isolated User",
        "first_name": "Isolated",
        "last_name": "User",
        "is_active": True,
    }

    # This should work (different client table)
    result: UserProfile = ProfileActions.create(client=different_client, **profile_data)
    assert isinstance(result, UserProfile)

    # Should not be visible in original client
    with pytest.raises(NotFoundException):
        ProfileActions.get(client=client, user_id="isolated_user", profile_name="isolated_profile")  # Original client

    # Should be visible in the different client
    isolated_result: UserProfile = ProfileActions.get(
        client=different_client,
        user_id="isolated_user",
        profile_name="isolated_profile",
    )
    assert isinstance(isolated_result, UserProfile)
    assert isolated_result.user_id == "isolated_user"

    # Cleanup - delete from different client
    ProfileActions.delete(
        client=different_client,
        user_id="isolated_user",
        profile_name="isolated_profile",
    )


# =============================================================================
# Edge Cases and Advanced Scenarios
# =============================================================================


def test_session_tracking_edge_cases():
    """Test session tracking with various edge case scenarios."""
    user_id = "test_single_user456"
    profile_name = "personal"

    # Test increment with string "true"
    profile1: UserProfile = ProfileActions.patch(
        client=client,
        user_id=user_id,
        profile_name=profile_name,
        increment_session="true",
    )

    first_session_count = profile1.session_count

    # Test increment with string "false" (should not increment)
    profile2: UserProfile = ProfileActions.patch(
        client=client,
        user_id=user_id,
        profile_name=profile_name,
        increment_session="false",
        email="no_increment@example.com",
    )
    assert profile2.session_count == first_session_count, "Session count should not increment when false"
    assert profile2.email == "no_increment@example.com", "Other fields should still update"

    # Test increment with boolean True
    profile3: UserProfile = ProfileActions.patch(
        client=client,
        user_id=user_id,
        profile_name=profile_name,
        increment_session=True,
    )
    assert profile3.session_count == first_session_count + 1, "Session count should increment with boolean True"


def test_large_profile_data():
    """Test creating profile with larger metadata fields."""
    large_profile_data = {
        "client": client,
        "user_id": "test_large_user",
        "profile_name": "large_profile",
        "email": "large@example.com",
        "display_name": "User with Large Data",
        "first_name": "Large",
        "last_name": "User",
        "theme": "dark",
        "is_active": True,
        "preferences": {
            "dashboard_settings": {
                "layout": "grid",
                "widgets": ["weather", "calendar", "tasks", "notifications"],
                "refresh_rate": 30,
                "theme_customization": {
                    "primary_color": "#007bff",
                    "secondary_color": "#6c757d",
                    "font_family": "Arial, sans-serif",
                },
            },
            "notification_preferences": {
                "email_notifications": True,
                "push_notifications": False,
                "sms_notifications": True,
                "frequency": "daily",
            },
        },
        "permissions": {
            "can_read": True,
            "can_write": True,
            "can_delete": False,
            "admin_access": False,
            "resource_access": ["dashboard", "reports", "settings"],
        },
    }

    # Create profile with large data
    created_profile: UserProfile = ProfileActions.create(**large_profile_data)
    assert isinstance(created_profile, UserProfile)

    # Verify data integrity
    assert created_profile.preferences is not None
    assert created_profile.permissions is not None
    assert created_profile.preferences["dashboard_settings"]["layout"] == "grid"
    assert created_profile.permissions["can_read"] is True

    # Cleanup
    ProfileActions.delete(client=client, user_id="test_large_user", profile_name="large_profile")


def test_empty_response_handling():
    """Test handling of empty responses in various scenarios."""
    # Test user with no profiles
    with pytest.raises(NotFoundException):
        ProfileActions.list(client=client, user_id="user_with_no_profiles")

    # Test email with no profiles
    with pytest.raises(NotFoundException):
        ProfileActions.list(client=client, email="email_with_no_profiles@example.com")

    # Test list with very restrictive pagination
    with pytest.raises(BadRequestException):
        result = ProfileActions.list(client=client, limit=0)
