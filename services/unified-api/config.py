"""Configuration module for WaddlePerf Unified API"""
import os
import secrets
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration with environment variable support"""

    # Database configuration
    DB_TYPE: str = os.getenv('DB_TYPE', 'mysql')  # postgres, mysql, sqlite
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '3306'))
    DB_USER: str = os.getenv('DB_USER', 'waddleperf')
    DB_PASS: str = os.getenv('DB_PASS', secrets.token_hex(16))
    DB_NAME: str = os.getenv('DB_NAME', 'waddleperf')
    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '10'))

    # Flask/Quart configuration
    SECRET_KEY: str = os.getenv('SECRET_KEY', secrets.token_hex(32))
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')
    DEBUG: bool = os.getenv('FLASK_DEBUG', '0') == '1'
    PORT: int = int(os.getenv('PORT', '5000'))

    # Security configuration
    JWT_SECRET: str = os.getenv('JWT_SECRET', secrets.token_hex(32))
    JWT_EXPIRATION_HOURS: int = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    SECURITY_PASSWORD_SALT: str = os.getenv('SECURITY_PASSWORD_SALT', secrets.token_hex(32))
    SECURITY_PASSWORD_HASH: str = 'bcrypt'
    SECURITY_TRACKABLE: bool = True
    SECURITY_RECOVERABLE: bool = True
    SECURITY_CHANGEABLE: bool = True

    # CORS configuration
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001')

    # External services
    TESTSERVER_URL: str = os.getenv('TESTSERVER_URL', 'http://testserver:8080')

    # MFA configuration
    MFA_REQUIRED: bool = os.getenv('MFA_REQUIRED', 'false').lower() == 'true'

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate_db_type(cls) -> None:
        """Validate DB_TYPE environment variable"""
        valid_types = ['postgres', 'mysql', 'sqlite']
        db_type = os.getenv('DB_TYPE', 'mysql')
        if db_type not in valid_types:
            raise ValueError(
                f"Invalid DB_TYPE: {db_type}. Must be one of {valid_types}"
            )

    def get_db_uri(self) -> str:
        """Build database connection URI based on DB_TYPE"""
        if self.DB_TYPE == 'postgres':
            return f"postgres://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == 'mysql':
            return f"mysql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == 'sqlite':
            return f"sqlite://{self.DB_NAME}.db"
        else:
            raise ValueError(f"Unsupported DB_TYPE: {self.DB_TYPE}")
