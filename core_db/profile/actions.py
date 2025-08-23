"""Profile management actions for the core-automation-profiles DynamoDB table.

This module provides comprehensive CRUD operations for user profile management with
proper error handling and validation. Supports both individual profile operations
and administrative listing capabilities with client-specific table isolation.

Key Features:
    - **Composite Key Support**: Handles user_id + profile_name composite primary keys
    - **Multi-operation Support**: Single profile, multiple profiles, and administrative operations
    - **Client Isolation**: Factory pattern for client-specific ProfileModel instances
    - **Soft/Hard Delete**: Configurable deletion strategies for data retention
    - **Authentication Integration**: Session tracking and login timestamp management

Usage Patterns:
    - Single profile operations: when both user_id and profile_name are provided
    - Multiple profile operations: when only user_id is provided (all profiles for user)
    - Administrative listing: when no path parameters are provided (all profiles)

Note:
    All methods expect kwargs containing the merged ChainMap of body, path_parameters,
    and query_parameters from HTTP requests. The 'client' parameter is required to
    initialize the ProfileModel through the factory pattern.
"""

import datetime
from pynamodb.exceptions import UpdateError
from pynamodb.expressions.update import Action

from core_framework.time_utils import make_default_time

import core_logging as log
import core_framework as util

from core_db.models import Paginator

from ..actions import TableActions
from ..response import Response, SuccessResponse
from ..exceptions import BadRequestException, ConflictException, UnknownException, NotFoundException
from .model import UserProfile


class ProfileActions(TableActions):
    """Actions for managing user profiles in the database.

    Provides comprehensive CRUD operations for user profile management with proper error handling
    and validation. Supports both individual profile operations and listing profiles
    for administrative purposes.

    With the composite primary key (user_id + profile_name), this class handles:
    - Single profile operations: when both user_id and profile_name are provided
    - Multiple profile operations: when only user_id is provided (returns all profiles for user)
    - Administrative listing: when no path parameters are provided

    The class uses a factory pattern to obtain client-specific ProfileModel instances,
    ensuring proper table isolation between different clients.

    Note:
        All methods expect kwargs containing the merged ChainMap of body, path_parameters,
        and query_parameters from HTTP requests. The 'client' parameter is required to
        initialize the ProfileModel through the factory pattern.
    """

    @classmethod
    def list(cls, **kwargs) -> Response:
        """List user profiles with optional filtering and pagination.

        Retrieves user profiles with support for various filtering options including
        active status, email-based filtering, and pagination. Uses either table scan
        or GSI queries depending on filter criteria for optimal performance.

        Args:
            **kwargs: Merged parameters from ChainMap(body, path_parameters, query_parameters)
                     containing optional filters and pagination parameters.

                     Query Parameters:
                         active (str, optional): Filter by active status ("true"/"false").
                                               Default: all profiles (no filter).
                         limit (str, optional): Maximum number of profiles to return (1-100).
                                              Default: "50".
                         last_key (str, optional): Pagination token for next page.
                                                  Format: "user_id:profile_name".
                         email (str, optional): Filter profiles by email address.
                                              Uses GSI for efficient querying.
                         client (str, required): Client identifier for table isolation.

        Returns:
            Response: SuccessResponse containing:
                - profiles (list): List of profile dictionaries
                - count (int): Number of profiles returned
                - total_found (int): Total profiles found (email filter only)
                - last_key (str|None): Pagination token for next page
                - filter_type (str): Type of filter used ("email" or "scan")

        Raises:
            BadRequestException: If client is missing, limit is invalid, or pagination token malformed.
            UnknownException: If an unexpected error occurs during profile retrieval.

        Performance Notes:
            - Email filtering uses GSI for efficient queries
            - Active status filtering applied in-memory for email queries
            - Table scan used for general listing with optional active filter
            - Pagination tokens encode composite key (user_id:profile_name)
        """
        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        if not client:
            raise BadRequestException("Client parameter is required to list profiles")

        model_class = UserProfile.model_class(client)

        try:
            paginator = Paginator(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        scan_kwargs = {
            "limit": paginator.limit,
        }
        if paginator.cursor is not None:
            scan_kwargs["last_evaluated_key"] = paginator.cursor

        result = model_class.scan(**scan_kwargs)
        profiles = []
        for item in result:
            profile = UserProfile.from_model(item).model_dump(mode="json")
            profiles.append(profile)

        paginator.cursor = getattr(result, "last_evaluated_key", None)
        paginator.total_count = getattr(result, "total_count", len(profiles))

        return SuccessResponse(data=profiles, metadata=paginator.get_metadata())

    @classmethod
    def get(cls, **kwargs) -> Response:
        """Get profile(s) by user ID and optionally profile name.

        Retrieves either a specific profile (when both user_id and profile_name provided)
        or all profiles for a user (when only user_id provided). Supports filtering
        by active status and provides detailed profile information.

        Args:
            **kwargs: Merged parameters from ChainMap(body, path_parameters, query_parameters).

                     Path Parameters:
                         user_id (str, required): AWS user identifier (ARN format).
                         profile_name (str, optional): Specific profile name to retrieve.

                     Query Parameters:
                         include_inactive (str, optional): Include inactive profiles.
                                                          Default: "false".
                         client (str, required): Client identifier for table isolation.

        Returns:
            Response: SuccessResponse containing either:
                - Single profile: Complete profile data dictionary
                - Multiple profiles: Dictionary with user_id, profiles list, count, active_only flag

        Raises:
            BadRequestException: If user_id is missing or client parameter not provided.
            NotFoundException: If profile(s) not found or all profiles are inactive.
            UnknownException: If an unexpected error occurs during profile retrieval.

        Behavior Notes:
            - Single profile mode: Returns profile data directly
            - Multiple profile mode: Returns structured response with metadata
            - Inactive profiles filtered out unless include_inactive="true"
            - Uses composite key queries for efficient retrieval
        """
        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        if not client:
            raise BadRequestException("Client parameter is required to retrieve profiles")

        # Get the model class for this client
        user_id = kwargs.get("user_id")
        profile_name = kwargs.get("profile_name")
        email = kwargs.get("email")

        # By default, we include ALL profiles.  If you specify include_inactive='false', they will be filtered out.
        only_active = str(kwargs.get("include_inactive", "true")).lower() != "true"

        if user_id and profile_name:
            return cls._get_single_profile(client, user_id=user_id, profile_name=profile_name)
        elif user_id:
            return cls._get_active_profiles_by_user(client, user_id=user_id, only_active=only_active)
        elif email:
            return cls._get_profiles_by_email(client, email=email, only_active=only_active)
        else:
            raise BadRequestException("Either user_id, email, or user_id+profile_name must be provided")

    @classmethod
    def create(cls, **kwargs) -> Response:

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        if not client:
            raise BadRequestException("Client parameter is required to create profile")

        try:
            data = UserProfile(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid profile data: {str(e)}") from e

        try:
            item = data.to_model(client)
            item.save(type(item).user_id.does_not_exist() & type(item).profile_name.does_not_exist())
            return SuccessResponse(data=data.model_dump(mode="json"))
        except Exception as e:
            # Check if it's a conditional check failure (profile already exists)
            if "ConditionalCheckFailedException" in str(e):
                raise ConflictException(f"Profile already exists: user_id={data.user_id}, profile_name={data.profile_name}")
            else:
                log.error(f"Failed to create profile: {str(e)}")
                raise UnknownException(f"Failed to create profile: {str(e)}")

    @classmethod
    def update(cls, **kwargs) -> Response:
        return cls._update(remove_none=True, **kwargs)

    @classmethod
    def patch(cls, **kwargs) -> Response:
        return cls._update(remove_none=False, **kwargs)

    @classmethod
    def delete(cls, **kwargs) -> Response:

        client = kwargs.get("client", kwargs.get("Client")) or util.get_client()
        if not client:
            raise BadRequestException("Client parameter is required to delete profile")

        user_id = kwargs.get("user_id")
        profile_name = kwargs.get("profile_name")
        email = kwargs.get("email")

        if user_id and profile_name:
            return cls._delete_user_profile(client=client, user_id=user_id, profile_name=profile_name)
        elif user_id:
            # If only user_id is provided, delete all profiles for that user
            return cls._delete_user_profiles(client=client, user_id=user_id)
        elif email:
            return cls._delete_user_profiles_by_email(client=client, email=email)
        else:
            raise BadRequestException("Either user_id, email, or user_id+profile_name must be provided for deletion")

    @classmethod
    def _delete_user_profile(cls, client: str, user_id: str, profile_name: str) -> Response:
        if not user_id or not profile_name:
            raise BadRequestException("user_id and profile_name are required to delete profile")

        model_class = UserProfile.model_class(client)

        deleted_profile = {}
        try:
            item = model_class.get(hash_key=user_id, range_key=profile_name)
            item.delete()

            deleted_profile = {"user_id": user_id, "profile_name": profile_name, "email": item.email}
            return SuccessResponse(message="User Profile deleted successfully", data=deleted_profile)
        except model_class.DoesNotExist:
            raise NotFoundException(f"Profile not found: user_id={user_id}, profile_name={profile_name}")
        except Exception as e:
            raise UnknownException(f"Failed to delete profile: {str(e)}")

    @classmethod
    def _delete_user_profiles(cls, client: str, user_id: str) -> Response:
        """Delete all profiles for a specific user ID.

        Args:
            client (str): Client identifier for table isolation.
            user_id (str): User ID to delete all profiles for.

        Returns:
            Response: SuccessResponse indicating deletion status.

        Raises:
            BadRequestException: If user_id is missing.
            NotFoundException: If no profiles found for the user.
            UnknownException: If an unexpected error occurs during deletion.
        """
        if not user_id:
            raise BadRequestException("user_id is required to delete profiles")

        model_class = UserProfile.model_class(client)

        deleted_profiles = []
        try:
            # Query all profiles for the user
            results = model_class.query(hash_key=user_id)

            if not results:
                raise NotFoundException(f"No profiles found for user_id={user_id}")

            # Delete each profile
            for item in results:
                item.delete()
                deleted_profiles.append({"user_id": user_id, "profile_name": item.profile_name, "email": item.email})

            return SuccessResponse(message="All profiles deleted successfully", data=deleted_profiles)
        except Exception as e:
            raise UnknownException(f"Failed to delete profiles for user {user_id}: {str(e)}")

    @classmethod
    def _delete_user_profiles_by_email(cls, client: str, email: str) -> Response:
        """Delete all profiles associated with a specific email address.

        Args:
            client (str): Client identifier for table isolation.
            email (str): Email address to delete profiles for.

        Returns:
            Response: SuccessResponse indicating deletion status.

        Raises:
            BadRequestException: If email is missing.
            NotFoundException: If no profiles found for the email.
            UnknownException: If an unexpected error occurs during deletion.
        """
        if not email:
            raise BadRequestException("Email is required to delete profiles")

        model_class = UserProfile.model_class(client)

        deleted_profiles = []
        try:
            # Query using GSI for email index
            results = model_class.email_index.query(hash_key=email)

            if not results:
                raise NotFoundException(f"No profiles found for email: {email}")

            # Delete each profile
            for item in results:
                item.delete()
                deleted_profiles.append({"email": email, "profile_name": item.profile_name, "user_id": item.user_id})

            return SuccessResponse(message="All profiles deleted successfully", data=deleted_profiles)
        except Exception as e:
            raise UnknownException(f"Failed to delete profiles for email {email}: {str(e)}")

    @classmethod
    def _update(cls, remove_none: bool = True, **kwargs) -> Response:
        """Update an existing profile in the database with Action statements.

        Creates PynamoDB Action statements for efficient updates. By default,
        performs complete replacement by removing None fields (PUT semantics).

        Args:
            remove_none: If True, fields set to None will be removed from the database.
                        If False, None fields are skipped (not updated).

        Returns:
            Self: Updated profile instance with fresh data from database

        Raises:
            BadRequestException: If user_id or profile_name is missing
            NotFoundException: If profile doesn't exist
            UnknownException: If database operation fails
        """
        client = kwargs.get("client") or util.get_client()
        if not client:
            raise BadRequestException("Client parameter is required to update profile")

        # Validate required fields
        user_id = kwargs.get("user_id")
        profile_name = kwargs.get("profile_name")
        increment_session = str(kwargs.get("increment_session", "false")).lower() == "true"

        if not user_id:
            raise BadRequestException("user_id is required to update profile")
        if not profile_name:
            raise BadRequestException("profile_name is required to update profile")

        model_class = UserProfile.model_class(client)

        if remove_none:
            input_data = UserProfile(**kwargs)
        else:
            input_data = UserProfile.model_construct(**kwargs)

        excluded_fields = {"user_id", "profile_name", "created_at", "updated_at"}

        try:
            if increment_session:
                item = model_class.get(hash_key=user_id, range_key=profile_name)
                # Increment session tracking
                if item.session_count is None:
                    input_data.session_count = 1
                else:
                    input_data.session_count = item.session_count + 1
                input_data.last_login = make_default_time()

            # Get all field values from self
            values = input_data.model_dump(by_alias=False, exclude_none=False, exclude=excluded_fields)

            attributes = model_class.get_attributes()

            # Build update actions
            actions: list[Action] = []

            # Iterate through all fields in self
            for key, value in values.items():
                # Skip primary key fields (can't be updated)
                if key in excluded_fields:
                    continue

                if key in attributes:
                    attr = attributes[key]

                    # Get the model attribute for this field
                    if value is None:
                        if remove_none:
                            # Remove the field from the database
                            actions.append(attr.remove())
                    else:
                        actions.append(attr.set(value))

            actions.append(model_class.updated_at.set(make_default_time()))

            # Create item instance for update operation
            item = model_class(user_id=user_id, profile_name=profile_name)
            item.update(actions=actions, condition=model_class.user_id.exists() & model_class.profile_name.exists())
            item.refresh()

            data = UserProfile.from_model(item).model_dump(mode="json")

            return SuccessResponse(data=data)

        except UpdateError as e:
            # Handle specific update errors, e.g., conditional check failures (checking to see if the profile exists)
            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Profile not found: user_id={user_id}, profile_name={profile_name}")
            else:
                log.error(f"Failed to update profile: {str(e)}")
                raise UnknownException(f"Failed to update profile: {str(e)}")
        except Exception as e:
            log.error(f"Failed to update profile: {str(e)}")
            raise UnknownException(f"Failed to update profile: {str(e)}")

    @classmethod
    def _get_single_profile(cls, client: str, user_id: str, profile_name: str) -> UserProfile:
        """Retrieve a single user profile by user_id and profile_name.

        Args:
            user_id (str): AWS user identifier (hash key).
            profile_name (str): Profile name (range key).

        Returns:
            UserProfile: The retrieved profile instance.

        Raises:
            NotFoundException: If the profile does not exist.
            BadRequestException: If required parameters are missing.
        """
        if not user_id or not profile_name:
            raise BadRequestException("user_id and profile_name are required to load profile")

        try:
            # Get the client-specific model class
            model_class = UserProfile.model_class(client)

            # Retrieve the item from DynamoDB using composite primary key
            item = model_class.get(hash_key=user_id, range_key=profile_name)
            data = UserProfile.from_model(item).model_dump(mode="json")

            return SuccessResponse(data=data)

        except model_class.DoesNotExist:
            raise NotFoundException(f"Profile not found: user_id={user_id}, profile_name={profile_name}")
        except Exception as e:
            raise UnknownException(f"Failed to load profile: {str(e)}")

    @classmethod
    def _get_profiles_by_email(cls, client: str, email: str, only_active: bool = True) -> Response:
        """Retrieve all user profiles associated with a specific email address.

        Args:
            email (str): Email address to search for
            only_active (bool): If True, filter out inactive profiles

        Returns:
            Response: SuccessResponse containing the list of profiles associated with the email
        """
        if not email:
            raise BadRequestException("Email is required to retrieve profiles")

        model_class = UserProfile.model_class(client)

        # Query using GSI for email index
        if only_active:
            results = model_class.email_index.query(hash_key=email, filter_condition=model_class.is_active == True)
        else:
            results = model_class.email_index.query(hash_key=email)

        data = [UserProfile.from_model(item).model_dump(mode="json") for item in results]

        if len(data) == 0:
            raise NotFoundException(f"No profiles found for email: {email}")

        return SuccessResponse(data=data, metadata={"total_count": len(data)})

    @classmethod
    def _get_active_profiles_by_user(cls, client: str, user_id: str, only_active: bool = True) -> Response:
        """Get all active profiles for a specific user ID.

        Args:
            user_id (str): User ID to search for

        Returns:
            Response: SuccessResponse containing the list of active profiles
        """
        model_class = UserProfile.model_class(client)

        if only_active:
            # Query for active profiles only
            results = model_class.query(hash_key=user_id, filter_condition=model_class.is_active == True)
        else:
            # Query for all profiles regardless of active status
            results = model_class.query(hash_key=user_id)

        result = [UserProfile.from_model(item).model_dump(mode="json") for item in results]

        if len(result) == 0:
            raise NotFoundException(f"No profiles found for user_id: {user_id}")

        return SuccessResponse(data=result, metadata={"total_count": len(result)})
