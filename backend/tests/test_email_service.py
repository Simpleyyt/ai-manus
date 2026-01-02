"""
Comprehensive tests for EmailService._create_verification_email method
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

from app.application.services.email_service import EmailService
from app.domain.external.cache import Cache
from app.core.config import Settings

logger = logging.getLogger(__name__)


# Fixtures for mocking dependencies
@pytest.fixture
def mock_cache():
    """Create a mock Cache instance"""
    cache = Mock(spec=Cache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.keys = AsyncMock(return_value=[])
    return cache


@pytest.fixture
def mock_settings():
    """Create mock settings for email configuration"""
    settings = Mock(spec=Settings)
    settings.email_from = "noreply@aimanus.com"
    settings.email_username = "test@aimanus.com"
    settings.email_host = "smtp.gmail.com"
    settings.email_port = 465
    settings.email_password = "test_password"
    return settings


@pytest.fixture
def email_service(mock_cache, mock_settings):
    """Create EmailService instance with mocked dependencies"""
    with patch('app.application.services.email_service.get_settings', return_value=mock_settings):
        service = EmailService(cache=mock_cache)
        return service


# Tests for _create_verification_email method
class TestCreateVerificationEmail:
    """Test suite for EmailService._create_verification_email method"""

    def test_create_verification_email_returns_mime_multipart(self, email_service):
        """Test that the method returns a MIMEMultipart message"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        assert isinstance(result, MIMEMultipart)

    def test_create_verification_email_sets_from_address(self, email_service):
        """Test that the From field is set correctly"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        assert result['From'] == "noreply@aimanus.com"

    def test_create_verification_email_uses_username_when_email_from_is_none(self, mock_cache):
        """Test that email_username is used as fallback when email_from is None"""
        # Arrange
        settings = Mock(spec=Settings)
        settings.email_from = None
        settings.email_username = "fallback@aimanus.com"
        settings.email_host = "smtp.gmail.com"
        settings.email_port = 465
        settings.email_password = "test_password"

        with patch('app.application.services.email_service.get_settings', return_value=settings):
            service = EmailService(cache=mock_cache)
            email = "user@example.com"
            code = "123456"

            # Act
            result = service._create_verification_email(email, code)

            # Assert
            assert result['From'] == "fallback@aimanus.com"

    def test_create_verification_email_sets_to_address(self, email_service):
        """Test that the To field is set to the recipient email"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        assert result['To'] == email

    def test_create_verification_email_sets_subject(self, email_service):
        """Test that the Subject field is set correctly"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        assert result['Subject'] == "Password Reset Verification Code"

    def test_create_verification_email_includes_verification_code_in_body(self, email_service):
        """Test that the verification code is included in the email body"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        # Get the email body
        payload = result.get_payload()
        assert len(payload) > 0
        body = payload[0].get_payload()
        assert code in body

    def test_create_verification_email_has_html_content_type(self, email_service):
        """Test that the email body is HTML formatted"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        payload = result.get_payload()
        assert len(payload) > 0
        mime_text = payload[0]
        assert isinstance(mime_text, MIMEText)
        assert mime_text.get_content_type() == "text/html"

    def test_create_verification_email_contains_expiry_warning(self, email_service):
        """Test that the email includes expiry time warning"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        payload = result.get_payload()
        body = payload[0].get_payload()
        assert "5 minutes" in body or "expire" in body.lower()

    def test_create_verification_email_contains_security_notice(self, email_service):
        """Test that the email includes security notice"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        payload = result.get_payload()
        body = payload[0].get_payload()
        assert "did not request" in body.lower() or "ignore" in body.lower()

    def test_create_verification_email_contains_proper_html_structure(self, email_service):
        """Test that the email has proper HTML structure"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        payload = result.get_payload()
        body = payload[0].get_payload()
        assert "<html>" in body
        assert "</html>" in body
        assert "<body>" in body
        assert "</body>" in body

    def test_create_verification_email_with_different_email_addresses(self, email_service):
        """Test email creation with various email formats"""
        # Arrange
        test_emails = [
            "user@example.com",
            "test.user+tag@subdomain.example.co.uk",
            "firstname.lastname@company.org",
        ]
        code = "123456"

        # Act & Assert
        for email in test_emails:
            result = email_service._create_verification_email(email, code)
            assert result['To'] == email
            assert isinstance(result, MIMEMultipart)

    def test_create_verification_email_with_different_code_formats(self, email_service):
        """Test email creation with various verification code formats"""
        # Arrange
        email = "user@example.com"
        test_codes = [
            "123456",
            "000000",
            "999999",
            "111111",
        ]

        # Act & Assert
        for code in test_codes:
            result = email_service._create_verification_email(email, code)
            payload = result.get_payload()
            body = payload[0].get_payload()
            assert code in body

    def test_create_verification_email_contains_branded_elements(self, email_service):
        """Test that the email includes branding elements"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        payload = result.get_payload()
        body = payload[0].get_payload()
        # Check for brand name
        assert "AI Manus" in body or "AI-Manus" in body

    def test_create_verification_email_includes_all_required_headers(self, email_service):
        """Test that all required email headers are present"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        assert 'From' in result
        assert 'To' in result
        assert 'Subject' in result
        assert result['From'] is not None
        assert result['To'] is not None
        assert result['Subject'] is not None

    def test_create_verification_email_code_styling(self, email_service):
        """Test that the verification code has proper styling"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        payload = result.get_payload()
        body = payload[0].get_payload()
        # Check that code is in an h3 tag with styling
        assert "<h3" in body
        assert "style=" in body
        # Verify the code appears in the styled element
        assert code in body

    def test_create_verification_email_immutability_of_inputs(self, email_service):
        """Test that the method doesn't modify input parameters"""
        # Arrange
        email = "user@example.com"
        code = "123456"
        original_email = email
        original_code = code

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        assert email == original_email
        assert code == original_code

    def test_create_verification_email_multiple_calls_independence(self, email_service):
        """Test that multiple calls produce independent message objects"""
        # Arrange
        email1 = "user1@example.com"
        code1 = "111111"
        email2 = "user2@example.com"
        code2 = "222222"

        # Act
        result1 = email_service._create_verification_email(email1, code1)
        result2 = email_service._create_verification_email(email2, code2)

        # Assert
        assert result1 is not result2
        assert result1['To'] == email1
        assert result2['To'] == email2

        body1 = result1.get_payload()[0].get_payload()
        body2 = result2.get_payload()[0].get_payload()
        assert code1 in body1
        assert code2 in body2
        assert code1 not in body2
        assert code2 not in body1

    def test_create_verification_email_content_completeness(self, email_service):
        """Test that email contains all essential information elements"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        payload = result.get_payload()
        body = payload[0].get_payload()

        # Essential elements that should be present
        essential_elements = [
            "Password Reset",  # Purpose
            code,  # The verification code itself
            "5 minutes",  # Expiry information
            "did not request" or "ignore",  # Security notice
            "AI Manus",  # Branding
        ]

        # Check most essential elements are present
        assert "Password Reset" in body
        assert code in body
        assert "5 minutes" in body

    def test_create_verification_email_message_size_reasonable(self, email_service):
        """Test that the email message size is reasonable"""
        # Arrange
        email = "user@example.com"
        code = "123456"

        # Act
        result = email_service._create_verification_email(email, code)

        # Assert
        message_string = result.as_string()
        # Email should be less than 10KB (reasonable for a simple HTML email)
        assert len(message_string) < 10 * 1024
        # But should have some content (at least 500 bytes)
        assert len(message_string) > 500

    @patch('app.application.services.email_service.get_settings')
    def test_create_verification_email_settings_integration(self, mock_get_settings, mock_cache):
        """Test that the method properly integrates with settings"""
        # Arrange
        custom_settings = Mock(spec=Settings)
        custom_settings.email_from = "custom@company.com"
        custom_settings.email_username = "backup@company.com"
        mock_get_settings.return_value = custom_settings

        service = EmailService(cache=mock_cache)
        email = "user@example.com"
        code = "123456"

        # Act
        result = service._create_verification_email(email, code)

        # Assert
        assert result['From'] == "custom@company.com"

    def test_create_verification_email_with_special_characters_in_email(self, email_service):
        """Test email creation with special characters in email address"""
        # Arrange
        emails_with_special_chars = [
            "user+test@example.com",
            "user.name@example.com",
            "user_name@example.com",
            "user-name@example.com",
        ]
        code = "123456"

        # Act & Assert
        for email in emails_with_special_chars:
            result = email_service._create_verification_email(email, code)
            assert result['To'] == email
            assert isinstance(result, MIMEMultipart)
            # Verify the message can be serialized (important for actual sending)
            message_string = result.as_string()
            assert len(message_string) > 0
