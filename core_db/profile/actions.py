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

from typing import List, Tuple

from pynamodb.exceptions import (
    UpdateError,
    DoesNotExist,
    PutError,
    GetError,
    ScanError,
    QueryError,
)
from pynamodb.expressions.update import Action

from core_framework.time_utils import make_default_time

import core_logging as log

from core_db.models import Paginator

from ..actions import TableActions
from ..exceptions import (
    BadRequestException,
    ConflictException,
    UnknownException,
    NotFoundException,
)
from .model import ProfileModel, UserProfile


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

    LIST_RETURN_FILEDS = [
        "UserId",
        "ProfileName",
        "Email",
        "IsActive",
        "CreatedAt",
        "UpdatedAt",
        "LastLogin",
        "SessionCount",
    ]

    @classmethod
    def list(
        cls, *, client: str, user_id: str | None = None, email: str | None = None, **kwargs
    ) -> Tuple[List[UserProfile], Paginator]:
        if not client:
            raise BadRequestException("Client is required")

        if email:
            return cls._list_by_email(client=client, email=email, **kwargs)
        elif user_id:
            return cls._list_by_user_id(client=client, user_id=user_id, **kwargs)
        else:
            raise BadRequestException("Either user_id or email must be provided to list profiles")

    @classmethod
    def _list_by_email(cls, *, client: str, email: str, **kwargs) -> List[UserProfile]:

        model_class = UserProfile.model_class(client)

        try:
            paginator = Paginator(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        query_args = paginator.get_query_args()
        if "only_active" in kwargs:
            only_active = str(kwargs.get("only_active", "true")).lower() == "true"
            if only_active:
                query_args["filter_conditions"] = model_class.is_active == True

        query_args["attributes_to_get"] = cls.LIST_RETURN_FILEDS

        data = []

        try:

            # all profiles for this email
            result = model_class.email_index.query(email, **query_args)

            data = [UserProfile.from_model(item) for item in result]

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(data)

        except QueryError as e:
            raise UnknownException(f"Failed to list profiles by email: {str(e)}") from e
        except Exception as e:
            raise UnknownException(f"Failed to list profiles by email: {str(e)}") from e

        if len(data) == 0:
            raise NotFoundException(f"No profiles found for email: {email}")

        return data, paginator

    @classmethod
    def _list_by_user_id(cls, *, client: str, user_id: str | None = None, **kwargs) -> Tuple[List[UserProfile], Paginator]:

        model_class = UserProfile.model_class(client)

        try:
            paginator = Paginator(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid pagination parameters: {str(e)}") from e

        query_args = paginator.get_query_args()

        if "only_active" in kwargs:
            only_active = str(kwargs.get("only_active", "true")).lower() == "true"
            if only_active:
                query_args["filter_condition"] = model_class.is_active == True

        query_args["attributes_to_get"] = cls.LIST_RETURN_FILEDS

        data = []

        try:

            # all profiles for this user
            result = model_class.query(user_id, **query_args)

            data = [UserProfile.from_model(item) for item in result]

            paginator.cursor = getattr(result, "last_evaluated_key", None)
            paginator.total_count = len(data)

        except QueryError as e:
            raise UnknownException(f"Failed to list profiles: {str(e)}") from e
        except Exception as e:
            raise UnknownException(f"Failed to list profiles: {str(e)}") from e

        if len(data) == 0:
            raise NotFoundException(f"No profiles found for user_id: {user_id}")

        return data, paginator

    @classmethod
    def get(
        cls,
        *,
        client: str,
        user_id: str | None = None,
        email: str | None = None,
        profile_name: str,
        **kwargs,
    ) -> UserProfile:
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
        if not client:
            raise BadRequestException("Client parameter is required to retrieve profiles")

        if user_id and profile_name:
            return cls._get_single_profile_by_user_id(client, user_id=user_id, profile_name=profile_name)
        elif email:
            return cls._get_single_profile_by_email(client, email=email, profile_name=profile_name)
        else:
            raise BadRequestException("Either user_id, email, or user_id+profile_name must be provided")

    @classmethod
    def create(cls, *, client: str, record: UserProfile | None = None, **kwargs) -> UserProfile:

        if not client:
            raise BadRequestException("Client parameter is required to create profile")

        try:
            if not record:
                record = UserProfile(**kwargs)
        except ValueError as e:
            raise BadRequestException(f"Invalid profile data: {str(e)}") from e

        try:

            item = record.to_model(client)
            item.save(type(item).user_id.does_not_exist() & type(item).profile_name.does_not_exist())

            return record

        except PutError as e:
            # Check if it's a conditional check failure (profile already exists)
            if "ConditionalCheckFailedException" in str(e):
                raise ConflictException(f"Profile already exists: user_id={record.user_id}, profile_name={record.profile_name}")
            else:
                log.error(f"Failed to create profile: {str(e)}")
                raise UnknownException(f"Failed to create profile: {str(e)}")

        except Exception as e:
            raise UnknownException(f"Failed to create profile: {str(e)}")

    @classmethod
    def update(cls, *, client: str, record: UserProfile | None = None, **kwargs) -> UserProfile:
        return cls._update(remove_none=True, client=client, record=record, **kwargs)

    @classmethod
    def patch(cls, *, client: str, record: UserProfile | None = None, **kwargs) -> UserProfile:
        return cls._update(remove_none=False, client=client, record=record, **kwargs)

    @classmethod
    def delete(
        cls,
        *,
        client: str,
        user_id: str | None = None,
        profile_name: str | None = None,
        email: str | None = None,
        **kwargs,
    ) -> bool:

        if not client:
            raise BadRequestException("Client parameter is required to delete profile")

        if user_id and profile_name:
            return cls._delete_user_profile(client=client, user_id=user_id, profile_name=profile_name)
        elif user_id:
            return cls._delete_user_profiles(client=client, user_id=user_id)
        elif email and profile_name:
            return cls._delete_user_profile_by_email(client=client, email=email, profile_name=profile_name)
        elif email:
            return cls._delete_user_profiles_by_email(client=client, email=email)
        else:
            raise BadRequestException("Either user_id, email, or user_id+profile_name must be provided for deletion")

    @classmethod
    def _delete_user_profile(cls, client: str, user_id: str, profile_name: str) -> bool:

        if not user_id or not profile_name:
            raise BadRequestException("user_id and profile_name are required to delete profile")

        model_class = UserProfile.model_class(client)

        try:

            item = model_class.get(hash_key=user_id, range_key=profile_name)
            item.delete()

            return True

        except DoesNotExist:
            raise NotFoundException(f"Profile not found: user_id={user_id}, profile_name={profile_name}")
        except Exception as e:
            raise UnknownException(f"Failed to delete profile: {str(e)}")

    @classmethod
    def _delete_user_profiles(cls, client: str, user_id: str) -> bool:
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

        try:

            # Query all profiles for the user
            results = model_class.query(hash_key=user_id)

            if not results:
                raise NotFoundException(f"No profiles found for user_id={user_id}")

            # Delete each profile
            for item in results:
                item.delete()

            return True

        except Exception as e:
            raise UnknownException(f"Failed to delete profiles for user {user_id}: {str(e)}")

    @classmethod
    def _delete_user_profile_by_email(cls, client: str, email: str, profile_name: str) -> bool:

        if not email or not profile_name:
            raise BadRequestException("Email and profile_name are required to delete profile")

        model_class = UserProfile.model_class(client)

        try:

            range_key_condition = model_class.profile_name == profile_name

            results = model_class.email_index.query(hash_key=email, range_key_condition=range_key_condition)

            # read the result stream
            data: list[ProfileModel] = [item for item in results]

            if len(data) == 0:
                raise NotFoundException(f"No profiles found for email: {email} and profile_name: {profile_name}")

            if len(data) > 1:
                raise BadRequestException(
                    f"Multiple profiles found for email: {email} and profile_name: {profile_name}. Please specify user_id and profile_name."
                )

            # Delete the single profile found
            data[0].delete()

            return True

        except Exception as e:
            raise UnknownException(f"Failed to delete profile for email {email}: {str(e)}")

    @classmethod
    def _delete_user_profiles_by_email(cls, client: str, email: str) -> bool:
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

        try:

            # Query using GSI for email index
            results = model_class.email_index.query(email)

            if not results:
                raise NotFoundException(f"No profiles found for email: {email}")

            # Delete each profile
            for item in results:
                item.delete()

            return True

        except Exception as e:
            raise UnknownException(f"Failed to delete profiles for email {email}: {str(e)}")

    @classmethod
    def _update(
        cls,
        *,
        remove_none: bool,
        client: str,
        record: UserProfile | None = None,
        **kwargs,
    ) -> UserProfile:
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
        if not client:
            raise BadRequestException("Client parameter is required to update profile")

        increment_session = str(kwargs.get("increment_session", "false")).lower() == "true"

        user_id = kwargs.get("user_id")
        profile_name = kwargs.get("profile_name")

        if not user_id:
            raise BadRequestException("user_id is required to update profile")
        if not profile_name:
            raise BadRequestException("profile_name is required to update profile")

        model_class = UserProfile.model_class(client)

        excluded_fields = {"user_id", "profile_name", "created_at", "updated_at"}

        if record:
            values = record.model_dump(by_alias=False, exclude_none=False, exclude=excluded_fields)
        else:
            values = {key: value for key, value in kwargs.items() if key not in excluded_fields}

        try:
            if increment_session:
                item = model_class.get(hash_key=user_id, range_key=profile_name)
                # Increment session tracking
                if item.session_count is None:
                    values["session_count"] = 1
                else:
                    values["session_count"] = item.session_count + 1
                values["last_login"] = make_default_time()

            # Get all field values from self

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
            item.update(
                actions=actions,
                condition=model_class.user_id.exists() & model_class.profile_name.exists(),
            )
            item.refresh()

            return UserProfile.from_model(item)

        except UpdateError as e:

            if "ConditionalCheckFailedException" in str(e):
                raise NotFoundException(f"Profile not found: user_id={user_id}, profile_name={profile_name}")

            log.error(f"Failed to update profile: {str(e)}")
            raise UnknownException(f"Failed to update profile: {str(e)}")

        except Exception as e:
            log.error(f"Failed to update profile: {str(e)}")
            raise UnknownException(f"Failed to update profile: {str(e)}")

    @classmethod
    def _get_single_profile_by_user_id(cls, client: str, user_id: str, profile_name: str) -> UserProfile:
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

        # Get the client-specific model class
        model_class = UserProfile.model_class(client)

        try:

            # Retrieve the item from DynamoDB using composite primary key
            item = model_class.get(hash_key=user_id, range_key=profile_name)

            return UserProfile.from_model(item)

        except DoesNotExist:
            raise NotFoundException(f"Profile not found: user_id={user_id}, profile_name={profile_name}")
        except Exception as e:
            raise UnknownException(f"Failed to load profile: {str(e)}")

    @classmethod
    def _get_single_profile_by_email(cls, client: str, email: str, profile_name: str) -> UserProfile:
        """Retrieve all user profiles associated with a specific email address.

        Args:
            email (str): Email address to search for
            profile_name (str): Profile name to search for

        Returns:
            Response: SuccessResponse containing the list of profiles associated with the email
        """
        if not email or not profile_name:
            raise BadRequestException("Email and profile_name are required to retrieve profiles")

        model_class = UserProfile.model_class(client)

        try:

            range_key_condition = model_class.profile_name == profile_name

            results = model_class.email_index.query(hash_key=email, range_key_condition=range_key_condition)

            # read the result stream
            data = [item for item in results]

            if len(data) == 0:
                raise NotFoundException(f"No profiles found for email: {email} and profile_name: {profile_name}")

            if len(data) >= 1:
                raise BadRequestException(
                    f"Multiple profiles found for email: {email} and profile_name: {profile_name}. Please specify user_id and profile_name."
                )

            return UserProfile.from_model(data[0])

        except QueryError as e:
            raise UnknownException(f"Failed to query profiles by email {email}: {str(e)}")

        except Exception as e:
            raise UnknownException(f"Failed to load profiles by email {email}: {str(e)}")
