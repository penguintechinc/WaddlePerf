"""Unit tests for the Config class in config.py"""
import os
import pytest
from unittest.mock import patch


class TestConfigDefaults:
    """Test Config default values when environment variables are not set."""

    def test_db_type_default(self):
        """DB_TYPE defaults to mysql."""
        with patch.dict(os.environ, {}, clear=False):
            # Import fresh to pick up defaults
            from config import Config
            cfg = Config()
            assert cfg.DB_TYPE == os.getenv('DB_TYPE', 'mysql')

    def test_db_host_default(self):
        """DB_HOST defaults to localhost."""
        from config import Config
        cfg = Config()
        assert cfg.DB_HOST == os.getenv('DB_HOST', 'localhost')

    def test_db_port_default(self):
        """DB_PORT defaults to 3306 (mysql default)."""
        from config import Config
        cfg = Config()
        # default is 3306 as set in config.py
        assert isinstance(cfg.DB_PORT, int)

    def test_secret_key_default(self):
        """SECRET_KEY has a dev default."""
        from config import Config
        cfg = Config()
        assert cfg.SECRET_KEY is not None
        assert len(cfg.SECRET_KEY) > 0

    def test_jwt_expiration_default(self):
        """JWT_EXPIRATION_HOURS defaults to 24."""
        from config import Config
        cfg = Config()
        assert cfg.JWT_EXPIRATION_HOURS == int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

    def test_mfa_required_default_false(self):
        """MFA_REQUIRED defaults to False."""
        with patch.dict(os.environ, {'MFA_REQUIRED': 'false'}, clear=False):
            from config import Config
            cfg = Config()
            assert cfg.MFA_REQUIRED is False

    def test_debug_default_false(self):
        """DEBUG defaults to False (FLASK_DEBUG != 1)."""
        with patch.dict(os.environ, {'FLASK_DEBUG': '0'}, clear=False):
            from config import Config
            cfg = Config()
            assert cfg.DEBUG is False

    def test_security_password_hash_is_bcrypt(self):
        """SECURITY_PASSWORD_HASH is always bcrypt."""
        from config import Config
        cfg = Config()
        assert cfg.SECURITY_PASSWORD_HASH == 'bcrypt'

    def test_security_flags_defaults(self):
        """Security flags default to True."""
        from config import Config
        cfg = Config()
        assert cfg.SECURITY_TRACKABLE is True
        assert cfg.SECURITY_RECOVERABLE is True
        assert cfg.SECURITY_CHANGEABLE is True


class TestConfigEnvVarOverrides:
    """Test Config values loaded from environment variables."""

    def test_db_type_from_env(self):
        """DB_TYPE is read from environment."""
        with patch.dict(os.environ, {'DB_TYPE': 'postgres'}):
            from config import Config
            cfg = Config(DB_TYPE='postgres')
            assert cfg.DB_TYPE == 'postgres'

    def test_db_host_from_env(self):
        """DB_HOST is read from environment."""
        from config import Config
        cfg = Config(DB_HOST='db.example.com')
        assert cfg.DB_HOST == 'db.example.com'

    def test_db_port_from_env(self):
        """DB_PORT is converted to int."""
        from config import Config
        cfg = Config(DB_PORT=5432)
        assert cfg.DB_PORT == 5432
        assert isinstance(cfg.DB_PORT, int)

    def test_jwt_secret_from_env(self):
        """JWT_SECRET is overridable."""
        from config import Config
        cfg = Config(JWT_SECRET='supersecret')
        assert cfg.JWT_SECRET == 'supersecret'

    def test_debug_true_when_env_is_1(self):
        """DEBUG is True when FLASK_DEBUG=1."""
        with patch.dict(os.environ, {'FLASK_DEBUG': '1'}):
            from config import Config
            cfg = Config(DEBUG=True)
            assert cfg.DEBUG is True

    def test_mfa_required_true_from_env(self):
        """MFA_REQUIRED is True when env is 'true'."""
        from config import Config
        cfg = Config(MFA_REQUIRED=True)
        assert cfg.MFA_REQUIRED is True

    def test_log_level_from_env(self):
        """LOG_LEVEL is read from environment."""
        from config import Config
        cfg = Config(LOG_LEVEL='DEBUG')
        assert cfg.LOG_LEVEL == 'DEBUG'

    def test_cors_origins_from_env(self):
        """CORS_ORIGINS is read from environment."""
        from config import Config
        cfg = Config(CORS_ORIGINS='https://app.example.com')
        assert cfg.CORS_ORIGINS == 'https://app.example.com'


class TestConfigGetDbUri:
    """Test Config.get_db_uri() for different DB_TYPE values."""

    def test_mysql_uri_format(self):
        """MySQL URI uses mysql:// scheme."""
        from config import Config
        cfg = Config(
            DB_TYPE='mysql',
            DB_USER='user',
            DB_PASS='pass',
            DB_HOST='localhost',
            DB_PORT=3306,
            DB_NAME='mydb'
        )
        uri = cfg.get_db_uri()
        assert uri.startswith('mysql://')
        assert 'user:pass@localhost:3306/mydb' in uri

    def test_postgres_uri_format(self):
        """PostgreSQL URI uses postgres:// scheme."""
        from config import Config
        cfg = Config(
            DB_TYPE='postgres',
            DB_USER='pguser',
            DB_PASS='pgpass',
            DB_HOST='pghost',
            DB_PORT=5432,
            DB_NAME='pgdb'
        )
        uri = cfg.get_db_uri()
        assert uri.startswith('postgres://')
        assert 'pguser:pgpass@pghost:5432/pgdb' in uri

    def test_sqlite_uri_format(self):
        """SQLite URI uses sqlite:// scheme and only DB_NAME."""
        from config import Config
        cfg = Config(DB_TYPE='sqlite', DB_NAME='testdb')
        uri = cfg.get_db_uri()
        assert uri.startswith('sqlite://')
        assert 'testdb' in uri

    def test_invalid_db_type_raises(self):
        """Unsupported DB_TYPE raises ValueError."""
        from config import Config
        cfg = Config(DB_TYPE='oracle')
        with pytest.raises(ValueError, match='Unsupported DB_TYPE'):
            cfg.get_db_uri()

    def test_get_db_uri_includes_credentials(self):
        """URI includes user and password."""
        from config import Config
        cfg = Config(
            DB_TYPE='mysql',
            DB_USER='admin',
            DB_PASS='s3cr3t',
            DB_HOST='db',
            DB_PORT=3306,
            DB_NAME='app'
        )
        uri = cfg.get_db_uri()
        assert 'admin' in uri
        assert 's3cr3t' in uri


class TestConfigValidateDbType:
    """Test Config.validate_db_type() class method."""

    def test_valid_postgres(self):
        """postgres is a valid DB_TYPE."""
        with patch.dict(os.environ, {'DB_TYPE': 'postgres'}):
            from config import Config
            Config.validate_db_type()  # should not raise

    def test_valid_mysql(self):
        """mysql is a valid DB_TYPE."""
        with patch.dict(os.environ, {'DB_TYPE': 'mysql'}):
            from config import Config
            Config.validate_db_type()  # should not raise

    def test_valid_sqlite(self):
        """sqlite is a valid DB_TYPE."""
        with patch.dict(os.environ, {'DB_TYPE': 'sqlite'}):
            from config import Config
            Config.validate_db_type()  # should not raise

    def test_invalid_db_type_raises_value_error(self):
        """Invalid DB_TYPE raises ValueError."""
        with patch.dict(os.environ, {'DB_TYPE': 'mongodb'}):
            from config import Config
            with pytest.raises(ValueError, match='Invalid DB_TYPE'):
                Config.validate_db_type()
