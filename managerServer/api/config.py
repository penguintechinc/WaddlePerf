"""Configuration module for managerServer API"""
import os
import secrets
from datetime import timedelta
from dataclasses import dataclass, field

@dataclass
class Config:
    """Application configuration - reads env vars at __init__ time for test compatibility."""

    def __post_init__(self):
        """Initialize config from environment variables at instance creation time."""
        # Server
        self.SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
        self.JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_hex(32))
        self.MANAGER_KEY = os.getenv('MANAGER_KEY', secrets.token_hex(32))

        # Database
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = os.getenv('DB_PORT', '3306')
        self.DB_USER = os.getenv('DB_USER', 'waddleperf')
        self.DB_PASS = os.getenv('DB_PASS', '')
        self.DB_NAME = os.getenv('DB_NAME', 'waddleperf')

        self.DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))

        # JWT
        self.JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
        self.JWT_REFRESH_EXPIRATION_DAYS = 7

        # MFA
        self.MFA_REQUIRED = os.getenv('MFA_REQUIRED', 'false').lower() == 'true'
        self.MFA_ISSUER = 'WaddlePerf'

        # CORS
        cors_env = os.getenv('CORS_ORIGINS', '*')
        self.CORS_ORIGINS = [s.strip() for s in cors_env.split(',')]

        # API
        self.API_TITLE = 'WaddlePerf Manager API'
        self.API_VERSION = '1.0.0'

        # Pagination
        self.DEFAULT_PAGE_SIZE = 50
        self.MAX_PAGE_SIZE = 100

        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components."""
        return f'mysql+pymysql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def JWT_EXPIRATION(self) -> timedelta:
        """JWT expiration timedelta."""
        return timedelta(hours=self.JWT_EXPIRATION_HOURS)

    @property
    def JWT_REFRESH_EXPIRATION(self) -> timedelta:
        """JWT refresh expiration timedelta."""
        return timedelta(days=self.JWT_REFRESH_EXPIRATION_DAYS)
