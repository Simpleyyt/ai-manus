"""
Comprehensive tests for TokenService.create_access_token method
"""
import pytest
import jwt
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, UTC
import logging

from app.application.services.token_service import TokenService
from app.domain.models.user import User, UserRole
from app.core.config import Settings

logger = logging.getLogger(__name__)


# Fixtures for mocking dependencies
@pytest.fixture
def mock_settings():
    """Create mock settings for JWT configuration"""
    settings = Mock(spec=Settings)
    settings.jwt_secret_key = "test_secret_key_12345"
    settings.jwt_algorithm = "HS256"
    settings.jwt_access_token_expire_minutes = 30
    settings.jwt_refresh_token_expire_days = 7
    return settings


@pytest.fixture
def token_service(mock_settings):
    """Create TokenService instance with mocked dependencies"""
    with patch('app.application.services.token_service.get_settings', return_value=mock_settings):
        service = TokenService()
        return service


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        id="user_123",
        fullname="John Doe",
        email="john.doe@example.com",
        password_hash="hashed_password",
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@pytest.fixture
def admin_user():
    """Create an admin user for testing"""
    return User(
        id="admin_456",
        fullname="Admin User",
        email="admin@example.com",
        password_hash="hashed_admin_password",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@pytest.fixture
def inactive_user():
    """Create an inactive user for testing"""
    return User(
        id="inactive_789",
        fullname="Inactive User",
        email="inactive@example.com",
        password_hash="hashed_password",
        role=UserRole.USER,
        is_active=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


# Tests for create_access_token method
class TestCreateAccessToken:
    """Test suite for TokenService.create_access_token method"""

    def test_create_access_token_returns_string(self, token_service, sample_user):
        """Test that the method returns a JWT token as a string"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_is_valid_jwt(self, token_service, sample_user):
        """Test that the returned token is a valid JWT"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        # Should not raise an exception when decoding
        try:
            decoded = jwt.decode(
                token,
                token_service.settings.jwt_secret_key,
                algorithms=[token_service.settings.jwt_algorithm]
            )
            assert decoded is not None
        except jwt.InvalidTokenError:
            pytest.fail("Token is not a valid JWT")

    def test_create_access_token_contains_user_id(self, token_service, sample_user):
        """Test that the token contains the user ID in the 'sub' claim"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['sub'] == sample_user.id

    def test_create_access_token_contains_fullname(self, token_service, sample_user):
        """Test that the token contains the user's fullname"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['fullname'] == sample_user.fullname

    def test_create_access_token_contains_email(self, token_service, sample_user):
        """Test that the token contains the user's email"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['email'] == sample_user.email

    def test_create_access_token_contains_role(self, token_service, sample_user):
        """Test that the token contains the user's role"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['role'] == sample_user.role.value

    def test_create_access_token_contains_is_active(self, token_service, sample_user):
        """Test that the token contains the user's active status"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['is_active'] == sample_user.is_active

    def test_create_access_token_contains_iat_timestamp(self, token_service, sample_user):
        """Test that the token contains the 'iat' (issued at) timestamp"""
        # Arrange
        before = int(datetime.now(UTC).timestamp())

        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        after = int(datetime.now(UTC).timestamp())
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert 'iat' in decoded
        assert before <= decoded['iat'] <= after

    def test_create_access_token_contains_exp_timestamp(self, token_service, sample_user):
        """Test that the token contains the 'exp' (expiration) timestamp"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert 'exp' in decoded
        assert decoded['exp'] > decoded['iat']

    def test_create_access_token_expiration_time_is_correct(self, token_service, sample_user):
        """Test that the token expiration is set correctly based on settings"""
        # Arrange
        expected_expire_minutes = token_service.settings.jwt_access_token_expire_minutes

        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        iat = decoded['iat']
        exp = decoded['exp']
        actual_minutes = (exp - iat) / 60

        # Allow for 1-second tolerance due to execution time
        assert abs(actual_minutes - expected_expire_minutes) < 0.02

    def test_create_access_token_has_type_field(self, token_service, sample_user):
        """Test that the token contains the 'type' field set to 'access'"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['type'] == 'access'

    def test_create_access_token_for_admin_user(self, token_service, admin_user):
        """Test token creation for admin user with correct role"""
        # Act
        token = token_service.create_access_token(admin_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['role'] == UserRole.ADMIN.value
        assert decoded['sub'] == admin_user.id

    def test_create_access_token_for_inactive_user(self, token_service, inactive_user):
        """Test token creation for inactive user includes is_active=False"""
        # Act
        token = token_service.create_access_token(inactive_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['is_active'] is False

    def test_create_access_token_multiple_calls_unique_tokens(self, token_service, sample_user):
        """Test that multiple calls create unique tokens (different iat/exp)"""
        # Act
        token1 = token_service.create_access_token(sample_user)
        # Delay to ensure different timestamp (1 second for reliable difference)
        import time
        time.sleep(1)
        token2 = token_service.create_access_token(sample_user)

        # Assert
        assert token1 != token2

        decoded1 = jwt.decode(
            token1,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        decoded2 = jwt.decode(
            token2,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        # Timestamps should be different
        assert decoded1['iat'] < decoded2['iat']

    def test_create_access_token_uses_correct_algorithm(self, token_service, sample_user):
        """Test that the token uses the configured algorithm"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        # Decoding with the correct algorithm should succeed
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded is not None

        # Decoding with a different algorithm should fail
        with pytest.raises(jwt.InvalidAlgorithmError):
            jwt.decode(
                token,
                token_service.settings.jwt_secret_key,
                algorithms=['HS384']  # Different algorithm
            )

    def test_create_access_token_uses_correct_secret(self, token_service, sample_user):
        """Test that the token is signed with the correct secret"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        # Decoding with the correct secret should succeed
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded is not None

        # Decoding with a different secret should fail
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(
                token,
                "wrong_secret_key",
                algorithms=[token_service.settings.jwt_algorithm]
            )

    def test_create_access_token_with_special_characters_in_name(self, token_service):
        """Test token creation with special characters in user's name"""
        # Arrange
        user = User(
            id="user_special",
            fullname="José María O'Connor",
            email="jose@example.com",
            role=UserRole.USER,
            is_active=True
        )

        # Act
        token = token_service.create_access_token(user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['fullname'] == user.fullname

    def test_create_access_token_with_special_characters_in_email(self, token_service):
        """Test token creation with special characters in email"""
        # Arrange
        user = User(
            id="user_email",
            fullname="Test User",
            email="test+tag@example.com",
            role=UserRole.USER,
            is_active=True
        )

        # Act
        token = token_service.create_access_token(user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['email'] == user.email

    def test_create_access_token_does_not_include_password_hash(self, token_service, sample_user):
        """Test that the token does not include the password hash"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert 'password_hash' not in decoded
        assert 'password' not in decoded

    def test_create_access_token_does_not_modify_user_object(self, token_service, sample_user):
        """Test that creating a token doesn't modify the user object"""
        # Arrange
        original_id = sample_user.id
        original_fullname = sample_user.fullname
        original_email = sample_user.email
        original_is_active = sample_user.is_active

        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        assert sample_user.id == original_id
        assert sample_user.fullname == original_fullname
        assert sample_user.email == original_email
        assert sample_user.is_active == original_is_active

    @patch('app.application.services.token_service.jwt.encode')
    def test_create_access_token_handles_jwt_encoding_exception(self, mock_encode, token_service, sample_user):
        """Test that JWT encoding exceptions are properly raised"""
        # Arrange
        mock_encode.side_effect = Exception("JWT encoding failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            token_service.create_access_token(sample_user)
        assert "JWT encoding failed" in str(exc_info.value)

    @patch('app.application.services.token_service.logger')
    def test_create_access_token_logs_success(self, mock_logger, token_service, sample_user):
        """Test that successful token creation is logged"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        assert "Created access token" in call_args
        assert sample_user.fullname in call_args

    @patch('app.application.services.token_service.jwt.encode')
    @patch('app.application.services.token_service.logger')
    def test_create_access_token_logs_failure(self, mock_logger, mock_encode, token_service, sample_user):
        """Test that failed token creation is logged"""
        # Arrange
        mock_encode.side_effect = Exception("Encoding error")

        # Act & Assert
        with pytest.raises(Exception):
            token_service.create_access_token(sample_user)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "Failed to create access token" in call_args

    def test_create_access_token_token_size_reasonable(self, token_service, sample_user):
        """Test that the token size is reasonable"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        # JWT tokens should typically be between 200 and 2000 bytes
        assert 100 < len(token) < 2000

    def test_create_access_token_with_different_expire_settings(self, sample_user):
        """Test token creation with different expiration settings"""
        # Arrange
        custom_settings = Mock(spec=Settings)
        custom_settings.jwt_secret_key = "test_secret_key"
        custom_settings.jwt_algorithm = "HS256"
        custom_settings.jwt_access_token_expire_minutes = 60  # Different from default

        with patch('app.application.services.token_service.get_settings', return_value=custom_settings):
            service = TokenService()

            # Act
            token = service.create_access_token(sample_user)

            # Assert
            decoded = jwt.decode(
                token,
                custom_settings.jwt_secret_key,
                algorithms=[custom_settings.jwt_algorithm]
            )
            iat = decoded['iat']
            exp = decoded['exp']
            actual_minutes = (exp - iat) / 60

            assert abs(actual_minutes - 60) < 0.02

    def test_create_access_token_payload_structure(self, token_service, sample_user):
        """Test that the token payload has all required fields with correct types"""
        # Act
        token = token_service.create_access_token(sample_user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )

        # Check all required fields exist
        required_fields = ['sub', 'fullname', 'email', 'role', 'is_active', 'iat', 'exp', 'type']
        for field in required_fields:
            assert field in decoded, f"Required field '{field}' missing from token payload"

        # Check field types
        assert isinstance(decoded['sub'], str)
        assert isinstance(decoded['fullname'], str)
        assert isinstance(decoded['email'], str)
        assert isinstance(decoded['role'], str)
        assert isinstance(decoded['is_active'], bool)
        assert isinstance(decoded['iat'], int)
        assert isinstance(decoded['exp'], int)
        assert isinstance(decoded['type'], str)

    def test_create_access_token_with_long_user_name(self, token_service):
        """Test token creation with a very long user name"""
        # Arrange
        user = User(
            id="user_long_name",
            fullname="A" * 200,  # Very long name
            email="longname@example.com",
            role=UserRole.USER,
            is_active=True
        )

        # Act
        token = token_service.create_access_token(user)

        # Assert
        decoded = jwt.decode(
            token,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        assert decoded['fullname'] == user.fullname
        assert len(decoded['fullname']) == 200

    def test_create_access_token_consistent_for_same_user_at_same_time(self, token_service, sample_user):
        """Test that tokens created at the exact same time are identical"""
        # Arrange - Mock datetime to return the same timestamp
        fixed_time = datetime.now(UTC)

        with patch('app.application.services.token_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.timestamp = datetime.timestamp

            # Act
            token1 = token_service.create_access_token(sample_user)
            token2 = token_service.create_access_token(sample_user)

            # Assert
            # Tokens should be identical when created at the exact same timestamp
            assert token1 == token2

    def test_create_access_token_different_users_different_tokens(self, token_service, sample_user, admin_user):
        """Test that different users get different tokens"""
        # Act
        token1 = token_service.create_access_token(sample_user)
        token2 = token_service.create_access_token(admin_user)

        # Assert
        assert token1 != token2

        decoded1 = jwt.decode(
            token1,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )
        decoded2 = jwt.decode(
            token2,
            token_service.settings.jwt_secret_key,
            algorithms=[token_service.settings.jwt_algorithm]
        )

        assert decoded1['sub'] != decoded2['sub']
        assert decoded1['email'] != decoded2['email']
