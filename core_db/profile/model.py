from datetime import datetime, timezone
from typing import Type, Optional, Dict, Any

from pydantic import Field, field_validator, model_validator


from pynamodb.attributes import (
    UnicodeAttribute,
    UTCDateTimeAttribute,
    MapAttribute,
    BooleanAttribute,
    NumberAttribute,
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection

from ..models import TableFactory, DatabaseTable, DatabaseRecord


class ProfileByEmailIndex(GlobalSecondaryIndex):
    """Global secondary index for querying profiles by email address.

    Allows efficient lookup of user profiles by email address across
    all users and profile names. Multiple profiles may be returned
    for the same email if a user has multiple roles/profiles.

    Attributes:
        email (str): User's email address as hash key for the GSI

    Note:
        Uses AllProjection to include all profile attributes in the index
        for efficient queries without additional table reads.
        Multiple profiles can have the same email address.
    """

    class Meta:
        index_name = "email-index"
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    email = UnicodeAttribute(hash_key=True, attr_name="Email")


class ProfileModel(DatabaseTable):
    """User profile model for authenticated AWS users with multiple roles/profiles.

    Stores user profile information with support for multiple profiles per user.
    Each user can have different profiles for different roles, contexts, or
    organizational units (e.g., 'admin', 'developer', 'billing', 'personal').

    The primary key structure uses AWS user ID + profile_name to allow
    multiple profiles per user while maintaining unique identification.

    Attributes:
        user_id (str): AWS user identifier (ARN or user ID) used as hash key.
            This identifies the user across different AWS authentication methods.
        profile_name (str): Profile identifier/role name used as range key.
            Defaults to 'default' for primary profile.
        email (str, optional): User's email address for contact and notifications.
            Used for account recovery and communication. Can be same across profiles.
        display_name (str, optional): User's preferred display name shown in the UI for this profile.
            Can be different per profile.
        first_name (str, optional): User's given/first name.
            Usually same across profiles but can be customized.
        last_name (str, optional): User's family/last name.
            Usually same across profiles but can be customized.
        avatar_url (str, optional): URL pointing to the user's profile avatar image for this profile.
            Can be different per role.
        profile_description (str, optional): Optional description of this profile's purpose.
            Helps users understand the role/context.
        timezone (str, optional): User's preferred timezone for this profile.
            May differ by role. Default: "UTC"
        language (str, optional): User's preferred language code for this profile.
            May differ by organizational context. Default: "en-US"
        theme (str, optional): User's preferred UI theme setting for this profile.
            May differ by role. Default: "light"
        notifications_enabled (bool, optional): Whether user wants notifications for this profile.
            May differ by role. Default: True
        last_login (datetime, optional): Timestamp of user's last login using this specific profile.
            Tracked separately per profile.
        created_at (datetime, optional): Profile creation timestamp in UTC.
            Set when this specific profile is first created.
        updated_at (datetime, optional): Last modification timestamp for this profile.
            Updated whenever any field in this profile changes.
        aws_account_id (str, optional): AWS Account ID associated with this user.
            Same across profiles for the same user.
        aws_user_arn (str, optional): Full AWS user ARN for detailed identification.
            Same across profiles for the same user.
        access_key_prefix (str, optional): First 8 characters of the user's access key.
            May differ if user has different keys per role.
        preferred_region (str, optional): User's preferred AWS region for this profile.
            May differ by role or organizational scope. Default: "us-east-1"
        permissions (dict, optional): User's permission levels and roles for this profile.
            Different per profile/role by design.
        preferences (dict, optional): Additional user preferences for this profile.
            Different per profile for role-specific UI customization.
        session_count (int, optional): Total authentication sessions for this specific profile.
            Tracked separately per profile for analytics. Default: 0
        is_active (bool, optional): Whether this specific profile is active and enabled.
            Allows disabling specific roles without affecting others. Default: True
        email_index (ProfileByEmailIndex): Global secondary index for email-based queries.
            Returns all profiles associated with an email address.
        user_profiles_index (ProfileByUserIdIndex): Local secondary index for user-based queries.
            Returns all profiles for a specific user.

    Warning:
        Security Notes:
        - AWS ARN and access key prefix are considered sensitive data
        - Different profiles may have different permission levels
        - Use exclude_sensitive=True in to_simple_dict() for client responses
        - Never log or expose full access keys, only the prefix
    """

    class Meta(DatabaseTable.Meta):
        """Meta class for ProfileModel DynamoDB table configuration.

        Inherits configuration from DatabaseTable.Meta including table naming,
        region settings, and billing mode.
        """

        pass

    # UserID and Password.  user_pwd is only stored on pfoile 'default'
    user_id = UnicodeAttribute(hash_key=True, attr_name="UserId")
    profile_name = UnicodeAttribute(range_key=True, attr_name="ProfileName", default="default")

    # Encrypted and stored credentials
    credentials = MapAttribute(attr_name="Credentials", null=True)

    # Basic profile information
    email = UnicodeAttribute(attr_name="Email", null=True)
    display_name = UnicodeAttribute(attr_name="DisplayName", null=True)
    first_name = UnicodeAttribute(attr_name="FirstName", null=True)
    last_name = UnicodeAttribute(attr_name="LastName", null=True)
    avatar_url = UnicodeAttribute(attr_name="AvatarUrl", null=True)
    profile_description = UnicodeAttribute(attr_name="ProfileDescription", null=True)

    # User preferences (can differ per profile)
    timezone = UnicodeAttribute(attr_name="Timezone", null=True, default="UTC")
    language = UnicodeAttribute(attr_name="Language", null=True, default="en-US")
    theme = UnicodeAttribute(attr_name="Theme", null=True, default="light")
    notifications_enabled = BooleanAttribute(attr_name="NotificationsEnabled", null=True, default=True)

    # Timestamps (per profile)
    last_login = UTCDateTimeAttribute(attr_name="LastLogin", null=True)
    created_at = UTCDateTimeAttribute(attr_name="CreatedAt", null=True)
    updated_at = UTCDateTimeAttribute(attr_name="UpdatedAt", null=True)

    # AWS-specific information (usually same across profiles)
    aws_account_id = UnicodeAttribute(attr_name="AwsAccountId", null=True)
    aws_user_arn = UnicodeAttribute(attr_name="AwsUserArn", null=True)
    access_key_prefix = UnicodeAttribute(attr_name="AccessKeyPrefix", null=True)
    preferred_region = UnicodeAttribute(attr_name="PreferredRegion", null=True, default="us-east-1")

    # Profile-specific attributes
    permissions = MapAttribute(attr_name="Permissions", null=True, default=dict)
    preferences = MapAttribute(attr_name="Preferences", null=True, default=dict)

    # Usage tracking (per profile)
    session_count = NumberAttribute(attr_name="SessionCount", null=True, default=0)
    is_active = BooleanAttribute(attr_name="IsActive", null=True, default=True)

    # Indexes
    email_index = ProfileByEmailIndex()

    def update_last_login(self) -> None:
        """Update the last login timestamp to current UTC time for this profile.

        Also updates the updated_at timestamp to reflect the change.
        """
        self.last_login = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def increment_session_count(self) -> None:
        """Increment the session count for this specific profile.

        Initializes to 1 if None, otherwise increments by 1.
        Also updates the updated_at timestamp.
        """
        if self.session_count is None:
            self.session_count = 1
        else:
            self.session_count += 1
        self.updated_at = datetime.now(timezone.utc)

    @classmethod
    def create_from_aws_identity(
        cls,
        user_identity: Dict[str, Any],
        access_key_prefix: str,
        profile_name: str = "default",
        email: Optional[str] = None,
        **kwargs,
    ) -> "ProfileModel":
        """Create a new profile from AWS STS get_caller_identity response.

        Args:
            user_identity (Dict[str, Any]): Response from STS get_caller_identity
            access_key_prefix (str): First 8 characters of access key
            profile_name (str): Name/role for this profile (default: 'default')
            email (Optional[str]): User's email address if available
            **kwargs: Additional profile attributes

        Returns:
            ProfileModel: New profile instance
        """
        user_arn = user_identity.get("Arn")
        user_id = user_identity.get("UserId", user_arn)  # Fallback to ARN if no UserId
        account_id = user_identity.get("Account")

        now = datetime.now(timezone.utc)

        return cls(
            user_id=user_id,
            profile_name=profile_name,
            email=email,
            aws_account_id=account_id,
            aws_user_arn=user_arn,
            access_key_prefix=access_key_prefix,
            created_at=now,
            updated_at=now,
            last_login=now,
            session_count=1,
            **kwargs,
        )

    def __repr__(self) -> str:
        """Return string representation of the ProfileModel.

        Returns:
            str: String representation showing key fields
        """
        return f"<Profile(user={self.user_id},profile={self.profile_name},email={self.email})>"


ProfileModelType = Type[ProfileModel]


class ProfileModelFactory:
    """Factory class for creating client-specific ProfileModel instances and managing tables.

    Provides methods for getting client-specific models, creating/deleting tables,
    and checking table existence. Acts as a wrapper around TableFactory for ProfileModel.
    """

    @classmethod
    def get_model(cls, client: str) -> ProfileModelType:
        """Get the ProfileModel class for the given client.

        Args:
            client (str): The client identifier

        Returns:
            ProfileModelType: Client-specific ProfileModel class
        """
        return TableFactory.get_model(ProfileModel, client=client)

    @classmethod
    def create_table(cls, client: str, wait: bool = True) -> bool:
        """Create the ProfileModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table creation to complete

        Returns:
            bool: True if table was created, False if it already exists
        """
        return TableFactory.create_table(ProfileModel, client, wait=wait)

    @classmethod
    def delete_table(cls, client: str, wait: bool = True) -> bool:
        """Delete the ProfileModel table for the given client.

        Args:
            client (str): The client identifier
            wait (bool): Whether to wait for table deletion to complete

        Returns:
            bool: True if table was deleted, False if it did not exist
        """
        return TableFactory.delete_table(ProfileModel, client, wait=wait)

    @classmethod
    def exists(cls, client: str) -> bool:
        """Check if the ProfileModel table exists for the given client.

        Args:
            client (str): The client identifier

        Returns:
            bool: True if the table exists, False otherwise
        """
        return TableFactory.exists(ProfileModel, client)


class UserProfile(DatabaseRecord):
    """Pydantic model for ProfileModel data validation and serialization.

    Provides type validation, serialization, and API-friendly representation
    of user profile data. Supports conversion to/from PynamoDB ProfileModel
    instances with automatic field mapping and validation.

    This model mirrors the ProfileModel structure but uses Python-native
    types and Pydantic validation for API endpoints, data transformation,
    and client-server communication.
    """

    # Primary key fields
    user_id: str = Field(
        ...,
        description="AWS user identifier (ARN or user ID) used as hash key",
        min_length=1,
        alias="UserId",
    )
    profile_name: str = Field(
        ...,
        description="Profile identifier/role name used as range key",
        min_length=1,
        alias="ProfileName",
    )
    # Credentials
    credentials: Optional[dict[str, Any]] = Field(
        None,
        alias="Credentials",
        description="Encrypted credentials for this profile",
    )
    # Basic profile information
    email: Optional[str] = Field(
        None,
        description="User's email address for contact and notifications",
        alias="Email",
    )
    display_name: Optional[str] = Field(
        None,
        description="User's preferred display name shown in UI for this profile",
        alias="DisplayName",
    )
    first_name: Optional[str] = Field(
        None,
        description="User's given/first name",
        alias="FirstName",
    )
    last_name: Optional[str] = Field(
        None,
        description="User's family/last name",
        alias="LastName",
    )
    avatar_url: Optional[str] = Field(
        None,
        description="URL pointing to user's profile avatar image for this profile",
        alias="AvatarUrl",
    )
    profile_description: Optional[str] = Field(
        None,
        description="Optional description of this profile's purpose",
        alias="ProfileDescription",
    )
    # User preferences (can differ per profile)
    timezone: Optional[str] = Field(
        None,
        description="User's preferred timezone for this profile",
        alias="Timezone",
    )
    language: Optional[str] = Field(
        None,
        description="User's preferred language code for this profile",
        alias="Language",
    )
    theme: Optional[str] = Field(
        None,
        description="User's preferred UI theme setting for this profile",
        alias="Theme",
    )
    notifications_enabled: Optional[bool] = Field(
        None,
        description="Whether user wants notifications for this profile",
        alias="NotificationsEnabled",
    )
    # Timestamps (per profile)
    last_login: Optional[datetime] = Field(
        None,
        description="Timestamp of user's last login using this specific profile",
        alias="LastLogin",
    )
    created_at: Optional[datetime] = Field(
        description="Profile creation timestamp in UTC",
        alias="CreatedAt",
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: Optional[datetime] = Field(
        description="Last modification timestamp for this profile",
        alias="UpdatedAt",
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # AWS-specific information
    aws_account_id: Optional[str] = Field(
        None,
        description="AWS Account ID associated with this user",
        alias="AwsAccountId",
    )
    aws_user_arn: Optional[str] = Field(
        None,
        description="Full AWS user ARN for detailed identification",
        alias="AwsUserArn",
    )
    access_key_prefix: Optional[str] = Field(
        None,
        description="First 8 characters of the user's access key",
        alias="AccessKeyPrefix",
    )
    preferred_region: Optional[str] = Field(
        None,
        description="User's preferred AWS region for this profile",
        alias="PreferredRegion",
    )
    # Profile-specific attributes
    permissions: Optional[Dict[str, Any]] = Field(
        None,
        description="User's permission levels and roles for this profile",
        alias="Permissions",
    )
    preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional user preferences for this profile",
        alias="Preferences",
    )
    # Usage tracking (per profile)
    session_count: Optional[int] = Field(
        None,
        description="Total authentication sessions for this specific profile",
        ge=0,
        alias="SessionCount",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether this specific profile is active and enabled",
        alias="IsActive",
    )

    @field_validator("email", mode="before")
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        """Validate email format if provided.

        Args:
            value (Optional[str]): Email address to validate

        Returns:
            Optional[str]: Validated email address or None
        """
        if value is None:
            return None

        if value.strip() == "":
            return None

        try:
            from email_validator import validate_email, EmailNotValidError

            # Validate the email format
            valid = validate_email(value, check_deliverability=False)
            return valid.email  # Returns the normalized email address
        except EmailNotValidError:
            raise ValueError("Invalid email format")

    @classmethod
    def from_model(cls, model: ProfileModel) -> "UserProfile":
        """Create UserProfile from PynamoDB ProfileModel instance.

        Args:
            model: PynamoDB ProfileModel instance

        Returns:
            UserProfile instance with data from the model
        """
        return cls(**model.to_simple_dict())

    def to_model(self, client: str) -> ProfileModel:
        """Convert UserProfile to PynamoDB ProfileModel instance.

        Args:
            client (str): The client identifier for the model

        Returns:
            ProfileModel: PynamoDB model instance with data from this UserProfile
        """
        model_class = self.model_class(client)

        return model_class(**self.model_dump(by_alias=False, exclude_none=True))

    @classmethod
    def model_class(cls, client: str) -> ProfileModelType:
        """Get the PynamoDB model class for the given client.

        Args:
            client (str): The name of the client

        Returns:
            ProfileModelType: Client-specific ProfileModel class
        """
        return ProfileModelFactory.get_model(client)

    def __repr__(self) -> str:
        """Return string representation of the UserProfile.

        Returns:
            String representation showing key fields
        """
        return f"<UserProfile(user={self.user_id},profile={self.profile_name},email={self.email})>"
