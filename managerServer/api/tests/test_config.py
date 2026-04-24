"""Unit tests for managerServer Config class."""
import os
from datetime import timedelta
import pytest

from config import Config


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_secret_key(self, monkeypatch):
        monkeypatch.delenv('SECRET_KEY', raising=False)
        cfg = Config()
        assert cfg.SECRET_KEY == 'dev-secret-key-change-in-production'

    def test_default_jwt_secret(self, monkeypatch):
        monkeypatch.delenv('JWT_SECRET', raising=False)
        cfg = Config()
        assert cfg.JWT_SECRET == 'dev-jwt-secret-change-in-production'

    def test_default_manager_key(self, monkeypatch):
        monkeypatch.delenv('MANAGER_KEY', raising=False)
        cfg = Config()
        assert cfg.MANAGER_KEY == '0' * 64

    def test_default_db_host(self, monkeypatch):
        monkeypatch.delenv('DB_HOST', raising=False)
        cfg = Config()
        assert cfg.DB_HOST == 'localhost'

    def test_default_db_port(self, monkeypatch):
        monkeypatch.delenv('DB_PORT', raising=False)
        cfg = Config()
        assert cfg.DB_PORT == '3306'

    def test_default_db_user(self, monkeypatch):
        monkeypatch.delenv('DB_USER', raising=False)
        cfg = Config()
        assert cfg.DB_USER == 'waddleperf'

    def test_default_db_name(self, monkeypatch):
        monkeypatch.delenv('DB_NAME', raising=False)
        cfg = Config()
        assert cfg.DB_NAME == 'waddleperf'

    def test_default_db_pool_size(self, monkeypatch):
        monkeypatch.delenv('DB_POOL_SIZE', raising=False)
        cfg = Config()
        assert cfg.DB_POOL_SIZE == 10

    def test_default_jwt_expiration_hours(self, monkeypatch):
        monkeypatch.delenv('JWT_EXPIRATION_HOURS', raising=False)
        cfg = Config()
        assert cfg.JWT_EXPIRATION_HOURS == 24

    def test_default_jwt_refresh_expiration_days(self):
        cfg = Config()
        assert cfg.JWT_REFRESH_EXPIRATION_DAYS == 7

    def test_default_mfa_required_false(self, monkeypatch):
        monkeypatch.delenv('MFA_REQUIRED', raising=False)
        cfg = Config()
        assert cfg.MFA_REQUIRED is False

    def test_default_mfa_issuer(self):
        cfg = Config()
        assert cfg.MFA_ISSUER == 'WaddlePerf'

    def test_default_log_level(self, monkeypatch):
        monkeypatch.delenv('LOG_LEVEL', raising=False)
        cfg = Config()
        assert cfg.LOG_LEVEL == 'INFO'

    def test_default_api_version(self):
        cfg = Config()
        assert cfg.API_VERSION == '1.0.0'

    def test_default_page_sizes(self):
        cfg = Config()
        assert cfg.DEFAULT_PAGE_SIZE == 50
        assert cfg.MAX_PAGE_SIZE == 100


class TestConfigEnvOverrides:
    """Test that env vars correctly override defaults."""

    def test_secret_key_from_env(self, monkeypatch):
        monkeypatch.setenv('SECRET_KEY', 'my-custom-secret')
        cfg = Config()
        assert cfg.SECRET_KEY == 'my-custom-secret'

    def test_jwt_secret_from_env(self, monkeypatch):
        monkeypatch.setenv('JWT_SECRET', 'custom-jwt-secret')
        cfg = Config()
        assert cfg.JWT_SECRET == 'custom-jwt-secret'

    def test_db_host_from_env(self, monkeypatch):
        monkeypatch.setenv('DB_HOST', 'db.example.com')
        cfg = Config()
        assert cfg.DB_HOST == 'db.example.com'

    def test_db_port_from_env(self, monkeypatch):
        monkeypatch.setenv('DB_PORT', '5432')
        cfg = Config()
        assert cfg.DB_PORT == '5432'

    def test_db_pool_size_from_env(self, monkeypatch):
        monkeypatch.setenv('DB_POOL_SIZE', '25')
        cfg = Config()
        assert cfg.DB_POOL_SIZE == 25

    def test_jwt_expiration_hours_from_env(self, monkeypatch):
        monkeypatch.setenv('JWT_EXPIRATION_HOURS', '48')
        cfg = Config()
        assert cfg.JWT_EXPIRATION_HOURS == 48

    def test_mfa_required_true_from_env(self, monkeypatch):
        monkeypatch.setenv('MFA_REQUIRED', 'true')
        cfg = Config()
        assert cfg.MFA_REQUIRED is True

    def test_mfa_required_false_from_env(self, monkeypatch):
        monkeypatch.setenv('MFA_REQUIRED', 'false')
        cfg = Config()
        assert cfg.MFA_REQUIRED is False

    def test_log_level_from_env(self, monkeypatch):
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        cfg = Config()
        assert cfg.LOG_LEVEL == 'DEBUG'

    def test_cors_origins_from_env(self, monkeypatch):
        monkeypatch.setenv('CORS_ORIGINS', 'http://localhost:3000,http://app.example.com')
        cfg = Config()
        assert 'http://localhost:3000' in cfg.CORS_ORIGINS
        assert 'http://app.example.com' in cfg.CORS_ORIGINS


class TestDatabaseURL:
    """Test DATABASE_URL construction."""

    def test_database_url_default(self, monkeypatch):
        for key in ('DB_USER', 'DB_PASS', 'DB_HOST', 'DB_PORT', 'DB_NAME'):
            monkeypatch.delenv(key, raising=False)
        cfg = Config()
        url = cfg.DATABASE_URL
        assert url.startswith('mysql+pymysql://')
        assert 'waddleperf' in url
        assert 'localhost' in url
        assert '3306' in url

    def test_database_url_custom_values(self, monkeypatch):
        monkeypatch.setenv('DB_USER', 'testuser')
        monkeypatch.setenv('DB_PASS', 'testpass')
        monkeypatch.setenv('DB_HOST', 'db.test.com')
        monkeypatch.setenv('DB_PORT', '5432')
        monkeypatch.setenv('DB_NAME', 'testdb')
        cfg = Config()
        url = cfg.DATABASE_URL
        assert 'testuser' in url
        assert 'testpass' in url
        assert 'db.test.com' in url
        assert '5432' in url
        assert 'testdb' in url

    def test_database_url_with_empty_pass(self, monkeypatch):
        monkeypatch.setenv('DB_PASS', '')
        cfg = Config()
        url = cfg.DATABASE_URL
        assert 'mysql+pymysql://' in url

    def test_database_url_format(self, monkeypatch):
        monkeypatch.setenv('DB_USER', 'u')
        monkeypatch.setenv('DB_PASS', 'p')
        monkeypatch.setenv('DB_HOST', 'h')
        monkeypatch.setenv('DB_PORT', '1234')
        monkeypatch.setenv('DB_NAME', 'db')
        cfg = Config()
        assert cfg.DATABASE_URL == 'mysql+pymysql://u:p@h:1234/db'


class TestJWTProperties:
    """Test JWT timedelta properties."""

    def test_jwt_expiration_is_timedelta(self, monkeypatch):
        monkeypatch.delenv('JWT_EXPIRATION_HOURS', raising=False)
        cfg = Config()
        assert isinstance(cfg.JWT_EXPIRATION, timedelta)

    def test_jwt_expiration_default_24h(self, monkeypatch):
        monkeypatch.delenv('JWT_EXPIRATION_HOURS', raising=False)
        cfg = Config()
        assert cfg.JWT_EXPIRATION == timedelta(hours=24)

    def test_jwt_expiration_custom_hours(self, monkeypatch):
        monkeypatch.setenv('JWT_EXPIRATION_HOURS', '12')
        cfg = Config()
        assert cfg.JWT_EXPIRATION == timedelta(hours=12)

    def test_jwt_refresh_expiration_is_timedelta(self):
        cfg = Config()
        assert isinstance(cfg.JWT_REFRESH_EXPIRATION, timedelta)

    def test_jwt_refresh_expiration_7_days(self):
        cfg = Config()
        assert cfg.JWT_REFRESH_EXPIRATION == timedelta(days=7)


class TestCorsOrigins:
    """Test CORS_ORIGINS list construction."""

    def test_cors_origins_default_wildcard(self, monkeypatch):
        monkeypatch.delenv('CORS_ORIGINS', raising=False)
        cfg = Config()
        assert cfg.CORS_ORIGINS == ['*']

    def test_cors_origins_multiple_values(self, monkeypatch):
        monkeypatch.setenv('CORS_ORIGINS', 'http://a.com,http://b.com,http://c.com')
        cfg = Config()
        assert len(cfg.CORS_ORIGINS) == 3

    def test_cors_origins_single_value(self, monkeypatch):
        monkeypatch.setenv('CORS_ORIGINS', 'http://only.com')
        cfg = Config()
        assert cfg.CORS_ORIGINS == ['http://only.com']
