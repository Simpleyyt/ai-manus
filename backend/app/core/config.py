from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import secrets
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):

    # Model provider configuration
    api_key: str | None = None
    api_base: str = "https://api.deepseek.com/v1"

    # Model configuration
    model_name: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 2000

    # MongoDB configuration
    mongodb_uri: str = "mongodb://mongodb:27017"
    mongodb_database: str = "manus"
    mongodb_username: str | None = None
    mongodb_password: str | None = None

    # Redis configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    # Sandbox configuration
    sandbox_address: str | None = None
    sandbox_image: str | None = None
    sandbox_name_prefix: str | None = None
    sandbox_ttl_minutes: int | None = 30
    sandbox_network: str | None = None  # Docker network bridge name
    sandbox_chrome_args: str | None = ""
    sandbox_https_proxy: str | None = None
    sandbox_http_proxy: str | None = None
    sandbox_no_proxy: str | None = None

    # Search engine configuration
    search_provider: str | None = "bing"  # "baidu", "google", "bing"
    google_search_api_key: str | None = None
    google_search_engine_id: str | None = None

    # Auth configuration
    auth_provider: str = "password"  # "password", "none", "local"
    password_salt: str | None = None  # Global salt (combined with per-user salt)
    password_hash_rounds: int = 100000  # OWASP recommended minimum for PBKDF2-SHA256
    password_hash_algorithm: str = "pbkdf2_sha256"
    local_auth_email: str = "admin@example.com"
    local_auth_password: str = "admin"

    # Email configuration
    email_host: str | None = None  # "smtp.gmail.com"
    email_port: int | None = None  # 587
    email_username: str | None = None
    email_password: str | None = None
    email_from: str | None = None

    # JWT configuration
    jwt_secret_key: str = ""  # Must be set in production
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # CORS configuration
    cors_origins: str = ""  # Comma-separated list of allowed origins, empty = allow all in dev

    # MCP configuration
    mcp_config_path: str = "/etc/mcp.json"

    # Logging configuration
    log_level: str = "INFO"

    # Environment mode
    environment: str = "development"  # "development", "staging", "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        """Get list of allowed CORS origins"""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate(self):
        """Validate configuration settings"""
        if not self.api_key:
            raise ValueError("API key is required")

        # Security validations for production
        if self.is_production:
            # JWT secret validation
            if not self.jwt_secret_key or self.jwt_secret_key == "your-secret-key-here":
                raise ValueError(
                    "JWT_SECRET_KEY must be set to a secure value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )

            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")

            # Password salt validation
            if not self.password_salt:
                raise ValueError(
                    "PASSWORD_SALT must be set in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(16))\""
                )

            # CORS validation
            if not self.cors_origins_list:
                logger.warning(
                    "CORS_ORIGINS is not set in production - all origins will be allowed. "
                    "Consider setting specific allowed origins for security."
                )
        else:
            # Development mode warnings
            if not self.jwt_secret_key or self.jwt_secret_key == "your-secret-key-here":
                # Generate a random secret for development
                self.jwt_secret_key = secrets.token_urlsafe(32)
                logger.warning(
                    "Using auto-generated JWT secret for development. "
                    "Set JWT_SECRET_KEY in production."
                )

            if not self.password_salt:
                self.password_salt = secrets.token_urlsafe(16)
                logger.warning(
                    "Using auto-generated password salt for development. "
                    "Set PASSWORD_SALT in production."
                )

@lru_cache()
def get_settings() -> Settings:
    """Get application settings"""
    settings = Settings()
    settings.validate()
    return settings 
