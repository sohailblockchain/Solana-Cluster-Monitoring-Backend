# # app/core/config.py
# from typing import List
# from pydantic_settings import BaseSettings


# class Settings(BaseSettings):
#     # Project Information
#     PROJECT_NAME: str = "Solana Cluster Monitoring Backend"
#     VERSION: str = "1.0.0"
#     DESCRIPTION: str = "FastAPI backend for Solana parent-child wallet detection"
#     API_V1_STR: str = "/api/v1"
    
#     # Database
#     DATABASE_URL: str = "sqlite:///./app.db"
    
#     # Helius API
#     HELIUS_API_KEY: str = "29dce386-f700-47b7-a61d-6562b1145a45"
#     HELIUS_BASE_URL: str = "https://api.helius.xyz/v0"
    
#     # Detection Settings
#     MIN_CHILD_WALLETS: int = 5  # Minimum child wallets to trigger parent detection
#     DETECTION_WINDOW_MINUTES: int = 5  # Time window for parent-child detection
    
#     # Environment
#     ENVIRONMENT: str = "development"
#     DEBUG: bool = True
    
#     class Config:
#         env_file = ".env"
#         case_sensitive = True


# settings = Settings()




# Sohail code here

# app/core/config.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "Solana Cluster Monitoring Backend"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "FastAPI backend for Solana parent-child wallet detection"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Helius
    HELIUS_API_KEY: str                       # must be set in .env
    HELIUS_BASE_URL: str = "https://api.helius.xyz/v0"
    # Optional direct URL template. If set, it will be used instead of BASE_URL.
    # Example: https://api.helius.xyz/v0/addresses/{address}/transactions?api-key={api_key}
    HELIUS_TRANSACTIONS_URL: Optional[str] = None

    # Detection defaults
    MIN_CHILD_WALLETS: int = 5
    DETECTION_WINDOW_MINUTES: int = 5

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Read .env and ignore any extra keys
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
