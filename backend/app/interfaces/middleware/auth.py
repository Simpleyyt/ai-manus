from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

from app.core.config import get_settings
from app.interfaces.dependencies import get_token_service, get_auth_service
from app.domain.models.user import User, UserRole

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for API requests"""
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.settings = get_settings()
        self.auth_service = get_auth_service()
        self.token_service = get_token_service()
        
        # Default paths that don't require authentication
        self.excluded_paths = excluded_paths or [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/status",
            "/api/v1/auth/refresh",
            "/api/v1/auth/send-verification-code",
            "/api/v1/auth/reset-password",
            '/api/v1/sessions/share'
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process authentication for each request"""
        
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Check if this is a resource access request with token parameter
        if self._is_resource_access_with_token(request):
            return await call_next(request)
        
        # Skip authentication if auth_provider is 'none'
        if self.settings.auth_provider == "none":
            # Add anonymous user to request state
            request.state.user = User(
                id="anonymous",
                fullname="anonymous",
                email="anonymous@localhost",
                role=UserRole.USER,
                is_active=True
            )
            return await call_next(request)
        
        signature = request.query_params.get("signature")
        if signature:
            if not self.token_service.verify_signed_url(signature):
                return self._unauthorized_response("Invalid signature")
        
        # Extract authentication information
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._unauthorized_response("Missing Authorization header")
        
        try:
            # For basic auth
            if auth_header.startswith("Basic "):
                user = await self._handle_basic_auth(auth_header)
            # For bearer token (if implemented)
            elif auth_header.startswith("Bearer "):
                user = await self._handle_bearer_auth(auth_header)
            else:
                return self._unauthorized_response("Invalid authentication scheme")
            
            if not user:
                return self._unauthorized_response("Authentication failed")
            
            if not user.is_active:
                return self._unauthorized_response("User account is inactive")
            
            # Add user to request state
            request.state.user = user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return self._unauthorized_response("Authentication failed")
            
        return await call_next(request)
    
    async def _handle_basic_auth(self, auth_header: str) -> Optional[User]:
        """Handle HTTP Basic Authentication"""
        try:
            import base64
            
            # Extract credentials
            encoded_credentials = auth_header.split(" ")[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(":", 1)
            
            # Authenticate user
            user = await self.auth_service.authenticate_user(username, password)
            return user
            
        except Exception as e:
            logger.warning(f"Basic auth failed: {e}")
            return None
    
    async def _handle_bearer_auth(self, auth_header: str) -> Optional[User]:
        """Handle Bearer Token Authentication"""
        try:
            # Extract token
            token = auth_header.split(" ")[1]
            
            # Verify token and get user
            user = await self.auth_service.verify_token(token)
            return user
            
        except Exception as e:
            logger.warning(f"Bearer token auth failed: {e}")
            return None
    
    def _is_resource_access_with_token(self, request: Request) -> bool:
        """Check if request is resource access with valid token parameter or signed URL"""
        try:
            signature = request.query_params.get("signature")
            if signature:
                return self._verify_signed_url_access(request)
            
            return False
                
        except Exception as e:
            logger.error(f"Error checking resource access: {e}")
            return False

    def _verify_signed_url_access(self, request: Request) -> bool:
        """Verify signed URL access"""
        try:
            # Verify the signed URL directly
            full_url = str(request.url)
            is_valid = self.token_service.verify_signed_url(full_url)
            
            if is_valid:
                logger.info(f"Access authenticated via signed URL for path: {request.url.path}")
                return True
            else:
                logger.warning(f"Invalid signed URL for path: {request.url.path}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking signed URL access: {e}")
            return False

    def _unauthorized_response(self, message: str) -> JSONResponse:
        """Return unauthorized response"""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "code": 401,
                "msg": message,
                "data": None
            }
        )
        