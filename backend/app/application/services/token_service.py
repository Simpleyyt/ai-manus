import jwt
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from app.core.config import get_settings
from app.domain.models.user import User
import logging

import hashlib
import hmac
import urllib.parse

logger = logging.getLogger(__name__)


class TokenService:
    """Token manager for authentication and URL signing"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user"""
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=self.settings.jwt_access_token_expire_minutes)
        
        payload = {
            "sub": user.id,  # Subject (user ID)
            "fullname": user.fullname,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "iat": int(now.timestamp()),  # Issued at (timestamp)
            "exp": int(expire.timestamp()),  # Expiration time (timestamp)
            "type": "access"
        }
        
        try:
            token = jwt.encode(
                payload,
                self.settings.jwt_secret_key,
                algorithm=self.settings.jwt_algorithm
            )
            logger.debug(f"Created access token for user: {user.fullname}")
            return token
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token for user"""
        now = datetime.now(UTC)
        expire = now + timedelta(days=self.settings.jwt_refresh_token_expire_days)
        
        payload = {
            "sub": user.id,  # Subject (user ID)
            "fullname": user.fullname,
            "iat": int(now.timestamp()),  # Issued at (timestamp)
            "exp": int(expire.timestamp()),  # Expiration time (timestamp)
            "type": "refresh"
        }
        
        try:
            token = jwt.encode(
                payload,
                self.settings.jwt_secret_key,
                algorithm=self.settings.jwt_algorithm
            )
            logger.debug(f"Created refresh token for user: {user.fullname}")
            return token
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            # Check if token is not expired
            exp = payload.get("exp")
            if exp and exp < int(datetime.now(UTC).timestamp()):
                logger.warning("Token has expired")
                return None
            
            logger.debug(f"Token verified for user: {payload.get('fullname')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Extract user information from JWT token"""
        payload = self.verify_token(token)
        
        if not payload:
            return None
        
        # Return user info from token payload
        return {
            "id": payload.get("sub"),
            "fullname": payload.get("fullname"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "is_active": payload.get("is_active", True),
            "token_type": payload.get("type", "access")
        }
    
    def is_token_valid(self, token: str) -> bool:
        """Check if token is valid"""
        return self.verify_token(token) is not None
    
    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """Get token expiration time"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, UTC)
        return None
    
    def create_resource_access_token(self, resource_type: str, resource_id: str, user_id: str, expire_minutes: int = 60) -> str:
        """Create JWT resource access token for URL-based access
        
        Args:
            resource_type: Type of resource (file, vnc, etc.)
            resource_id: ID of the resource (file_id, session_id, etc.)
            user_id: User ID who requested the token
            expire_minutes: Token expiration time in minutes
        """
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=expire_minutes)
        
        payload = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "iat": int(now.timestamp()),  # Issued at (timestamp)
            "exp": int(expire.timestamp()),  # Expiration time (timestamp)
            "type": "resource_access"
        }
        
        try:
            token = jwt.encode(
                payload,
                self.settings.jwt_secret_key,
                algorithm=self.settings.jwt_algorithm
            )
            logger.debug(f"Created resource access token for {resource_type}: {resource_id}, user: {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to create resource access token: {e}")
            raise

    def revoke_token(self, token: str) -> bool:
        """Revoke token (placeholder for token blacklist implementation)"""
        # TODO:In a real implementation, you would add the token to a blacklist
        # stored in Redis or database with expiration time
        logger.warning(f"Token revoked (placeholder implementation)")
        return True

    def create_signed_url(self, base_url: str, expire_minutes: int = 60) -> str:
        """Create URL with signature for resource access
        
        Args:
            base_url: Base URL for the resource (e.g., '/api/v1/files/123' or '/api/v1/sessions/456/vnc')
            expire_minutes: URL expiration time in minutes
            
        Returns:
            Signed URL with signature and expiration parameters
        """
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=expire_minutes)
        expires_timestamp = int(expire.timestamp())
        
        # Use the base URL directly - no placeholder replacement needed
        final_url = base_url
        
        # Create signature payload - simplified to only include URL and expiration
        payload_data = f"{final_url}|{expires_timestamp}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.settings.jwt_secret_key.encode('utf-8'),
            payload_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Parse URL to add query parameters
        parsed_url = urllib.parse.urlparse(final_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Add signature parameters
        query_params['signature'] = [signature]
        query_params['expires'] = [str(expires_timestamp)]
        
        # Rebuild URL with signature parameters
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        signed_url = urllib.parse.urlunparse((
            '',
            '',
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
        logger.debug(f"Created signed URL for: {final_url}")
        return signed_url
    
    def verify_signed_url(self, request_url: str) -> bool:
        """Verify signed URL
        
        Args:
            request_url: Full request URL with query parameters
            
        Returns:
            True if valid, False if invalid
        """
        try:
            logger.info(f"Verifying signed URL: {request_url}")
            # Parse URL and extract query parameters
            parsed_url = urllib.parse.urlparse(request_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Extract required parameters
            signature = query_params.get('signature', [None])[0]
            expires_str = query_params.get('expires', [None])[0]
            
            if not all([signature, expires_str]):
                logger.warning("Missing required signature parameters in URL")
                return False
            
            # Check expiration
            expires_timestamp = int(expires_str)
            if expires_timestamp < int(datetime.now(UTC).timestamp()):
                logger.warning("Signed URL has expired")
                return False
            
            # Reconstruct base URL without signature parameters
            base_query_params = {k: v for k, v in query_params.items() 
                               if k not in ['signature', 'expires']}
            base_query = urllib.parse.urlencode(base_query_params, doseq=True)
            base_url = urllib.parse.urlunparse((
                '',
                '',
                parsed_url.path,
                parsed_url.params,
                base_query,
                parsed_url.fragment
            ))
            
            # Recreate payload for signature verification using simplified method
            payload_data = f"{base_url}|{expires_timestamp}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.settings.jwt_secret_key.encode('utf-8'),
                payload_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures using constant-time comparison to prevent timing attacks
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Invalid signature in signed URL")
                return False
            
            logger.debug(f"Signed URL verified for: {base_url}")
            return True
            
        except Exception as e:
            logger.error(f"Signed URL verification failed: {e}")
            return False
