# ==========================================================
# JARVIS v9.0 - Configuration Management
# Pydantic-based settings
# ==========================================================

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class JarvisSettings(BaseSettings):
    """JARVIS configuration settings"""

    # API Keys
    groq_api_key: str = Field(..., env='GROQ_API_KEY')
    openai_api_key: Optional[str] = Field(None, env='OPENAI_API_KEY')

    # Security
    jwt_secret: str = Field(..., env='JWT_SECRET')
    jwt_algorithm: str = Field('HS256', env='JWT_ALGORITHM')
    jwt_access_expiration: int = Field(1800, env='JWT_ACCESS_EXPIRATION')  # 30 min
    jwt_refresh_expiration: int = Field(86400, env='JWT_REFRESH_EXPIRATION')  # 24 hours

    # Redis
    redis_host: str = Field('localhost', env='REDIS_HOST')
    redis_port: int = Field(6379, env='REDIS_PORT')
    redis_db: int = Field(0, env='REDIS_DB')

    # Server
    host: str = Field('0.0.0.0', env='HOST')
    port: int = Field(8000, env='PORT')
    log_level: str = Field('info', env='LOG_LEVEL')

    # Performance
    max_concurrent_requests: int = Field(100, env='MAX_CONCURRENT_REQUESTS')
    request_timeout: int = Field(30, env='REQUEST_TIMEOUT')
    retry_attempts: int = Field(3, env='RETRY_ATTEMPTS')

    # Features
    autonomous_mode: bool = Field(False, env='AUTONOMOUS_MODE')
    sea_enabled: bool = Field(True, env='SEA_ENABLED')
    health_check_enabled: bool = Field(True, env='HEALTH_CHECK_ENABLED')
    metrics_collection_enabled: bool = Field(True, env='METRICS_COLLECTION_ENABLED')

    # Paths
    skills_path: str = Field('./skills', env='SKILLS_PATH')
    data_path: str = Field('./data', env='DATA_PATH')
    logs_path: str = Field('./logs', env='LOGS_PATH')

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


# Global settings instance (lazy-safe to avoid import-time hard fail)
try:
    settings = JarvisSettings()
except Exception:
    settings = None


def get_settings() -> JarvisSettings:
    """Load settings with explicit validation when needed."""
    return JarvisSettings()

REQUIRED_ENV_KEYS = ("JWT_SECRET",)
OPTIONAL_ENV_KEYS = (
    "GROQ_API_KEY",
    "REDIS_HOST",
    "REDIS_PORT",
    "GRPC_PORT",
    "WHATSAPP_PORT",
)


def validate_env_contract() -> dict:
    """Return missing required/optional environment keys."""
    missing_required = [k for k in REQUIRED_ENV_KEYS if not os.getenv(k)]
    missing_optional = [k for k in OPTIONAL_ENV_KEYS if not os.getenv(k)]
    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
    }


def env_contract_summary() -> str:
    result = validate_env_contract()
    required = result["missing_required"]
    optional = result["missing_optional"]
    if not required and not optional:
        return "Environment contract satisfied"
    parts = []
    if required:
        parts.append(f"missing_required={','.join(required)}")
    if optional:
        parts.append(f"missing_optional={','.join(optional)}")
    return "Environment contract warning: " + " | ".join(parts)
