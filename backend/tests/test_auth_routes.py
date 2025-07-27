import pytest
import logging
import requests
from conftest import BASE_URL


logger = logging.getLogger(__name__)


@pytest.fixture
def test_user_data():
    """Create test user data"""
    return {
        "fullname": "Test User",
        "password": "password123",
        "email": "test@example.com"
    }


@pytest.fixture
def admin_user_data():
    """Create admin user data"""
    return {
        "fullname": "Admin User",
        "password": "admin123",
        "email": "admin@example.com"
    }


@pytest.fixture
def authenticated_user(client, test_user_data):
    """Create and authenticate a test user"""
    # First register the user
    register_url = f"{BASE_URL}/auth/register"
    register_response = client.post(register_url, json=test_user_data)
    
    if register_response.status_code == 200:
        auth_data = register_response.json()["data"]
        return {
            "user_data": test_user_data,
            "auth_data": auth_data,
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"]
        }
    
    logger.info(f"register_response: {register_response.status_code} - {register_response.text}")
    
    # If registration fails, try login (user might already exist)
    login_url = f"{BASE_URL}/auth/login"
    login_response = client.post(login_url, json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    if login_response.status_code == 200:
        auth_data = login_response.json()["data"]
        return {
            "user_data": test_user_data,
            "auth_data": auth_data,
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"]
        }
    
    logger.info(f"login_response: {login_response.status_code} - {login_response.text}")
    
    # If both fail, raise error
    raise Exception("Failed to authenticate test user")


@pytest.fixture
def authenticated_admin(client, admin_user_data):
    """Create and authenticate an admin user"""
    # Try to login first
    login_url = f"{BASE_URL}/auth/login"
    login_response = client.post(login_url, json={
        "email": admin_user_data["email"],
        "password": admin_user_data["password"]
    })
    
    if login_response.status_code == 200:
        auth_data = login_response.json()["data"]
        return {
            "user_data": admin_user_data,
            "auth_data": auth_data,
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"]
        }
    
    # If login fails, register and promote to admin (this would need API support)
    register_url = f"{BASE_URL}/auth/register"
    register_response = client.post(register_url, json=admin_user_data)
    
    if register_response.status_code == 200:
        auth_data = register_response.json()["data"]
        # Note: In a real system, you'd need a way to promote users to admin
        # This might be done through database manipulation or a separate admin API
        return {
            "user_data": admin_user_data,
            "auth_data": auth_data,
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"]
        }
    
    raise Exception("Failed to authenticate admin user")


class TestAuthRoutes:
    """Test class for authentication routes using end-to-end testing"""

    def test_register_success(self, client):
        """Test successful user registration"""
        import uuid
        url = f"{BASE_URL}/auth/register"
        # Use UUID to ensure unique email
        unique_suffix = str(uuid.uuid4())[:8]
        user_data = {
            "fullname": f"New User {unique_suffix}",
            "password": "password123",
            "email": f"newuser_{unique_suffix}@example.com"
        }
        
        response = client.post(url, json=user_data)
        
        logger.info(f"Register response: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "success"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["user"]["fullname"] == user_data["fullname"]
        assert data["data"]["user"]["email"] == user_data["email"]
        assert data["data"]["user"]["role"] == "user"
        assert data["data"]["user"]["is_active"] is True

    def test_register_validation_error_short_fullname(self, client):
        """Test registration with short fullname"""
        url = f"{BASE_URL}/auth/register"
        user_data = {
            "fullname": "A",  # Too short
            "password": "password123",
            "email": "test@example.com"
        }
        
        response = client.post(url, json=user_data)
        
        logger.info(f"Register short fullname response: {response.status_code} - {response.text}")
        assert response.status_code == 422

    def test_register_validation_error_short_password(self, client):
        """Test registration with short password"""
        url = f"{BASE_URL}/auth/register"
        user_data = {
            "fullname": "Test User",
            "password": "123",  # Too short
            "email": "test@example.com"
        }
        
        response = client.post(url, json=user_data)
        
        logger.info(f"Register short password response: {response.status_code} - {response.text}")
        assert response.status_code == 422

    def test_register_validation_error_invalid_email(self, client):
        """Test registration with invalid email"""
        url = f"{BASE_URL}/auth/register"
        user_data = {
            "fullname": "Test User",
            "password": "password123",
            "email": "invalid-email"  # Invalid email
        }
        
        response = client.post(url, json=user_data)
        
        logger.info(f"Register invalid email response: {response.status_code} - {response.text}")
        assert response.status_code == 422

    def test_register_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email"""
        url = f"{BASE_URL}/auth/register"
        
        # First registration
        response1 = client.post(url, json=test_user_data)
        logger.info(f"First registration response: {response1.status_code} - {response1.text}")
        
        # Second registration with same email but different fullname
        duplicate_data = {
            "fullname": "Different User",
            "password": "password123",
            "email": test_user_data["email"]  # Same email
        }
        response2 = client.post(url, json=duplicate_data)
        logger.info(f"Duplicate registration response: {response2.status_code} - {response2.text}")
        
        # Second registration should fail
        assert response2.status_code in [400, 422]

    def test_login_success(self, client, authenticated_user):
        """Test successful login"""
        url = f"{BASE_URL}/auth/login"
        login_data = {
            "email": authenticated_user["user_data"]["email"],
            "password": authenticated_user["user_data"]["password"]
        }
        
        response = client.post(url, json=login_data)
        
        logger.info(f"Login response: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["user"]["email"] == login_data["email"]
        assert data["data"]["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, authenticated_user):
        """Test login with invalid credentials"""
        url = f"{BASE_URL}/auth/login"
        login_data = {
            "email": authenticated_user["user_data"]["email"],
            "password": "wrongpassword"
        }
        
        response = client.post(url, json=login_data)
        
        logger.info(f"Login invalid credentials response: {response.status_code} - {response.text}")
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        url = f"{BASE_URL}/auth/login"
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post(url, json=login_data)
        
        logger.info(f"Login nonexistent user response: {response.status_code} - {response.text}")
        assert response.status_code == 401

    def test_get_auth_status(self, client):
        """Test get authentication status"""
        url = f"{BASE_URL}/auth/status"
        
        response = client.get(url)
        
        logger.info(f"Auth status response: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "authenticated" in data["data"]
        assert "auth_provider" in data["data"]

    def test_get_current_user_info(self, client, authenticated_user):
        """Test get current user information"""
        url = f"{BASE_URL}/auth/me"
        logger.info(f"authenticated_user: {authenticated_user}")
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = client.get(url, headers=headers)
        
        logger.info(f"Get current user response: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["fullname"] == authenticated_user["user_data"]["fullname"]
        assert data["data"]["email"] == authenticated_user["user_data"]["email"]
        assert data["data"]["role"] == "user"

    def test_get_current_user_info_unauthorized(self, client):
        """Test get current user information without authentication"""
        url = f"{BASE_URL}/auth/me"
        
        response = client.get(url)
        
        logger.info(f"Get current user unauthorized response: {response.status_code} - {response.text}")
        assert response.status_code == 401

    def test_get_current_user_info_invalid_token(self, client):
        """Test get current user information with invalid token"""
        url = f"{BASE_URL}/auth/me"
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get(url, headers=headers)
        
        logger.info(f"Get current user invalid token response: {response.status_code} - {response.text}")
        assert response.status_code == 401


    def test_refresh_token_success(self, client, authenticated_user):
        """Test successful token refresh"""
        url = f"{BASE_URL}/auth/refresh"
        refresh_data = {
            "refresh_token": authenticated_user["refresh_token"]
        }
        
        response = client.post(url, json=refresh_data)
        
        logger.info(f"Refresh token response: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    def test_refresh_token_invalid_token(self, client):
        """Test token refresh with invalid token"""
        url = f"{BASE_URL}/auth/refresh"
        refresh_data = {
            "refresh_token": "invalid_refresh_token"
        }
        
        response = client.post(url, json=refresh_data)
        
        logger.info(f"Refresh invalid token response: {response.status_code} - {response.text}")
        assert response.status_code == 401

    def test_logout_success(self, client, authenticated_user):
        """Test successful logout"""
        url = f"{BASE_URL}/auth/logout"
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = client.post(url, headers=headers)
        
        logger.info(f"Logout response: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["message"] == "Logout successful"

    def test_logout_unauthorized(self, client):
        """Test logout without authentication"""
        url = f"{BASE_URL}/auth/logout"
        
        response = client.post(url)
        
        logger.info(f"Logout unauthorized response: {response.status_code} - {response.text}")
        assert response.status_code == 401

    def test_logout_invalid_token(self, client):
        """Test logout with invalid token"""
        url = f"{BASE_URL}/auth/logout"
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.post(url, headers=headers)
        
        logger.info(f"Logout invalid token response: {response.status_code} - {response.text}")
        assert response.status_code == 401

    # Admin-only endpoint tests (these will need proper admin user setup)
    def test_get_user_by_id_forbidden_non_admin(self, client, authenticated_user):
        """Test get user by ID as non-admin (should be forbidden)"""
        url = f"{BASE_URL}/auth/user/some_user_id"
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = client.get(url, headers=headers)
        
        logger.info(f"Get user by ID non-admin response: {response.status_code} - {response.text}")
        assert response.status_code == 403

    def test_deactivate_user_forbidden_non_admin(self, client, authenticated_user):
        """Test user deactivation as non-admin (should be forbidden)"""
        url = f"{BASE_URL}/auth/user/some_user_id/deactivate"
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = client.post(url, headers=headers)
        
        logger.info(f"Deactivate user non-admin response: {response.status_code} - {response.text}")
        assert response.status_code == 403

    def test_activate_user_forbidden_non_admin(self, client, authenticated_user):
        """Test user activation as non-admin (should be forbidden)"""
        url = f"{BASE_URL}/auth/user/some_user_id/activate"
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = client.post(url, headers=headers)
        
        logger.info(f"Activate user non-admin response: {response.status_code} - {response.text}")
        assert response.status_code == 403

    # Integration tests combining multiple endpoints
    def test_complete_user_lifecycle(self, client):
        """Test complete user lifecycle: register -> login -> change password -> logout"""
        import uuid
        # Use UUID to ensure unique email
        unique_suffix = str(uuid.uuid4())[:8]
        user_data = {
            "fullname": f"Lifecycle User {unique_suffix}",
            "password": "password123",
            "email": f"lifecycle_{unique_suffix}@example.com"
        }
        
        # 1. Register
        register_url = f"{BASE_URL}/auth/register"
        register_response = client.post(register_url, json=user_data)
        logger.info(f"Lifecycle register response: {register_response.status_code} - {register_response.text}")
        assert register_response.status_code == 200
        
        # 2. Login
        login_url = f"{BASE_URL}/auth/login"
        login_response = client.post(login_url, json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        logger.info(f"Lifecycle login response: {login_response.status_code} - {login_response.text}")
        assert login_response.status_code == 200
        
        access_token = login_response.json()["data"]["access_token"]
        
        # 3. Change password
        change_password_url = f"{BASE_URL}/auth/change-password"
        headers = {"Authorization": f"Bearer {access_token}"}
        change_response = client.post(change_password_url, json={
            "old_password": user_data["password"],
            "new_password": "newpassword123"
        }, headers=headers)
        logger.info(f"Lifecycle change password response: {change_response.status_code} - {change_response.text}")
        assert change_response.status_code == 200
        
        # 4. Logout
        logout_url = f"{BASE_URL}/auth/logout"
        logout_response = client.post(logout_url, headers=headers)
        logger.info(f"Lifecycle logout response: {logout_response.status_code} - {logout_response.text}")
        assert logout_response.status_code == 200

    def test_token_refresh_workflow(self, client, authenticated_user):
        """Test token refresh workflow"""
        # Use refresh token to get new access token
        refresh_url = f"{BASE_URL}/auth/refresh"
        refresh_response = client.post(refresh_url, json={
            "refresh_token": authenticated_user["refresh_token"]
        })
        logger.info(f"Token refresh workflow response: {refresh_response.status_code} - {refresh_response.text}")
        assert refresh_response.status_code == 200
        
        new_access_token = refresh_response.json()["data"]["access_token"]
        
        # Use new access token to access protected endpoint
        me_url = f"{BASE_URL}/auth/me"
        headers = {"Authorization": f"Bearer {new_access_token}"}
        me_response = client.get(me_url, headers=headers)
        logger.info(f"Token refresh workflow me response: {me_response.status_code} - {me_response.text}")
        assert me_response.status_code == 200
        assert me_response.json()["data"]["email"] == authenticated_user["user_data"]["email"] 