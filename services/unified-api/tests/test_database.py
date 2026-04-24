"""Unit tests for database/connection.py"""
import pytest
from unittest.mock import MagicMock, patch


class TestBuildDbUri:
    """Test build_db_uri() for all supported DB_TYPE values."""

    def test_mysql_uri(self):
        """MySQL produces mysql+aiomysql:// URI."""
        from database.connection import build_db_uri

        config = MagicMock()
        config.DB_TYPE = 'mysql'
        config.DB_USER = 'wpuser'
        config.DB_PASS = 'secret'
        config.DB_HOST = 'mysqlhost'
        config.DB_PORT = 3306
        config.DB_NAME = 'wpdb'

        uri = build_db_uri(config)
        assert uri.startswith('mysql+aiomysql://')
        assert 'wpuser:secret@mysqlhost:3306/wpdb' in uri

    def test_postgres_uri(self):
        """PostgreSQL produces postgresql+asyncpg:// URI."""
        from database.connection import build_db_uri

        config = MagicMock()
        config.DB_TYPE = 'postgres'
        config.DB_USER = 'pguser'
        config.DB_PASS = 'pgpass'
        config.DB_HOST = 'pghost'
        config.DB_PORT = 5432
        config.DB_NAME = 'pgdb'

        uri = build_db_uri(config)
        assert uri.startswith('postgresql+asyncpg://')
        assert 'pguser:pgpass@pghost:5432/pgdb' in uri

    def test_sqlite_uri(self):
        """SQLite produces sqlite+aiosqlite:/// URI."""
        from database.connection import build_db_uri

        config = MagicMock()
        config.DB_TYPE = 'sqlite'
        config.DB_NAME = 'testdb'

        uri = build_db_uri(config)
        assert uri.startswith('sqlite+aiosqlite:///')
        assert 'testdb' in uri

    def test_unsupported_db_type_raises(self):
        """Unsupported DB_TYPE raises ValueError."""
        from database.connection import build_db_uri

        config = MagicMock()
        config.DB_TYPE = 'oracle'

        with pytest.raises(ValueError, match='Unsupported DB_TYPE'):
            build_db_uri(config)

    def test_mysql_uri_includes_port(self):
        """MySQL URI includes the port number."""
        from database.connection import build_db_uri

        config = MagicMock()
        config.DB_TYPE = 'mysql'
        config.DB_USER = 'u'
        config.DB_PASS = 'p'
        config.DB_HOST = 'h'
        config.DB_PORT = 13306
        config.DB_NAME = 'db'

        uri = build_db_uri(config)
        assert '13306' in uri

    def test_postgres_uri_includes_port(self):
        """PostgreSQL URI includes port."""
        from database.connection import build_db_uri

        config = MagicMock()
        config.DB_TYPE = 'postgres'
        config.DB_USER = 'u'
        config.DB_PASS = 'p'
        config.DB_HOST = 'h'
        config.DB_PORT = 15432
        config.DB_NAME = 'db'

        uri = build_db_uri(config)
        assert '15432' in uri

    def test_mysql_uri_contains_db_name(self):
        """MySQL URI path ends with the database name."""
        from database.connection import build_db_uri

        config = MagicMock()
        config.DB_TYPE = 'mysql'
        config.DB_USER = 'u'
        config.DB_PASS = 'p'
        config.DB_HOST = 'h'
        config.DB_PORT = 3306
        config.DB_NAME = 'myspecialdb'

        uri = build_db_uri(config)
        assert uri.endswith('/myspecialdb')

    def test_sqlite_db_name_in_path(self):
        """SQLite URI ends with <DB_NAME>.db."""
        from database.connection import build_db_uri

        config = MagicMock()
        config.DB_TYPE = 'sqlite'
        config.DB_NAME = 'waddleperf'

        uri = build_db_uri(config)
        assert 'waddleperf' in uri


class TestDatabaseReExports:
    """Test that init_dal and get_db are re-exported from connection module."""

    def test_init_dal_is_importable(self):
        """init_dal can be imported from database.connection."""
        from database.connection import init_dal
        assert callable(init_dal)

    def test_get_db_is_importable(self):
        """get_db can be imported from database.connection."""
        from database.connection import get_db
        assert callable(get_db)
