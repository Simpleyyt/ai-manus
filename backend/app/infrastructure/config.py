from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Self # Required for type hinting model_validator return

class Settings(BaseSettings):
    
    # Model provider configuration
    api_key: str | None = None
    gemini_api_key: str | None = None
    
    # Corrected api_base to be the true service base URL
    # The model name part will be appended dynamically
    api_base: str = "https://generativelanguage.googleapis.com/v1beta" 
    
    # Changed default from "deepseek" to "gemini" for consistency
    # with api_base and model_name defaults.
    # Options: "deepseek", "openai", "gemini"
    model_provider: str = "gemini" 
    
    # Model configuration
    model_name: str = "gemini-2.0-flash"
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # MongoDB configuration
    mongodb_uri: str = "mongodb://mongodb:27017"
    mongodb_database: str = "manus"
    mongodb_username: str | None = None
    mongodb_password: str | None = None
    
    # Redis configuration
    redis_url: str | None = None
    
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
    search_provider: str | None = None  # "google", "baidu"
    google_search_api_key: str | None = None
    google_search_engine_id: str | None = None
    
    # MCP configuration
    mcp_config_path: str = "/etc/mcp.json"
    
    # Logging configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    @model_validator(mode='after')
    def validate_api_keys(self) -> Self:
        """
        Performs cross-field validation after the settings model is initialized.
        Ensures that required API keys are present for the chosen model provider.
        """
        if self.model_provider in ["openai", "deepseek"] and not self.api_key:
            raise ValueError(f"API key is required for '{self.model_provider}' provider.")
        if self.model_provider == "gemini" and not self.gemini_api_key:
            raise ValueError("Gemini API key is required for 'gemini' provider.")
        return self # Important: Must return self for 'after' validators

    @property
    def gemini_generate_content_url(self) -> str:
        """
        Constructs the full Gemini generateContent API URL based on api_base and model_name.
        This property should only be accessed if model_provider is 'gemini'.
        """
        if self.model_provider == "gemini":
            # Ensure no trailing slashes on base to avoid double slashes in URL
            base = self.api_base.rstrip('/')
            return f"{base}/models/{self.model_name}:generateContent"
        raise AttributeError("gemini_generate_content_url is only available when model_provider is 'gemini'")


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings object.
    Settings are loaded from environment variables or .env file.
    Validation is performed automatically upon instantiation.
    """
    settings = Settings()
    # The validation is handled automatically by the @model_validator
    # within the Settings class, so no need for settings.validate() here.
    return settings