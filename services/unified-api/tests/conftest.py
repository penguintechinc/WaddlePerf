"""Shared pytest fixtures for unified-api tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart


def make_mock_row(data: dict):
    """Create a mock row object that behaves like a penguin-dal row."""
    row = MagicMock()
    for key, value in data.items():
        setattr(row, key, value)
    row.as_dict.return_value = data
    return row


def make_mock_rowset(rows: list):
    """Create a mock rowset that supports .first() and iteration."""
    rowset = MagicMock()
    rowset.first.return_value = rows[0] if rows else None
    # Return a fresh iterator each time __iter__ is called
    rowset.__iter__ = MagicMock(side_effect=lambda: iter(rows))
    rowset.__len__ = MagicMock(return_value=len(rows))
    return rowset


@pytest.fixture
def mock_db():
    """Provide a mock AsyncDB for testing without a real database.

    The mock simulates penguin-dal's callable query interface:
        db(query).select()  -> returns rowset
        db(query).count()   -> returns int
        db(query).update()  -> coroutine
        db(query).delete()  -> coroutine
        db.table.async_insert(**kw) -> coroutine returning new row id
    """
    db = MagicMock()

    # Default: empty rowset for db(query).select()
    empty_rowset = make_mock_rowset([])
    query_proxy = MagicMock()
    query_proxy.select = AsyncMock(return_value=empty_rowset)
    query_proxy.count = AsyncMock(return_value=0)
    query_proxy.update = AsyncMock(return_value=None)
    query_proxy.delete = AsyncMock(return_value=None)
    db.__call__ = MagicMock(return_value=query_proxy)
    db.return_value = query_proxy

    # Mock field attributes that support penguin-dal comparison operators
    def make_comparable_field(field_name):
        """Create a mock field that supports comparison operators."""
        field_mock = MagicMock()
        # Return a query-like object when comparisons are made
        field_mock.__eq__ = MagicMock(return_value=query_proxy)
        field_mock.__ne__ = MagicMock(return_value=query_proxy)
        field_mock.__lt__ = MagicMock(return_value=query_proxy)
        field_mock.__le__ = MagicMock(return_value=query_proxy)
        field_mock.__gt__ = MagicMock(return_value=query_proxy)
        field_mock.__ge__ = MagicMock(return_value=query_proxy)
        return field_mock

    # Make query_proxy support & and | operators for combined queries
    query_proxy.__and__ = MagicMock(return_value=query_proxy)
    query_proxy.__or__ = MagicMock(return_value=query_proxy)

    # Default table insert returns id=1
    for table_name in [
        'users', 'refresh_tokens', 'password_reset_tokens',
        'auth_user', 'auth_user_role', 'auth_role',
        'organizations', 'organizational_units',
        'devices', 'enrollment_secrets', 'test_result'
    ]:
        table_mock = MagicMock()
        table_mock.async_insert = AsyncMock(return_value=1)
        # Add comparable field mocks (id, organization_id, etc.)
        table_mock.id = make_comparable_field('id')
        table_mock.organization_id = make_comparable_field('organization_id')
        table_mock.created_at = make_comparable_field('created_at')
        setattr(db, table_name, table_mock)

    return db


@pytest.fixture
def mock_config():
    """Test configuration object."""
    config = MagicMock()
    config.SECRET_KEY = 'test-secret-key-for-testing-only'
    config.JWT_SECRET = 'test-jwt-secret-for-testing-only'
    config.JWT_EXPIRATION_HOURS = 24
    config.DB_TYPE = 'sqlite'
    config.DB_HOST = 'localhost'
    config.DB_PORT = 5432
    config.DB_USER = 'test'
    config.DB_PASS = 'test'
    config.DB_NAME = 'test_db'
    config.DB_POOL_SIZE = 5
    config.FLASK_ENV = 'testing'
    config.DEBUG = False
    config.PORT = 5000
    config.CORS_ORIGINS = 'http://localhost:3000'
    config.LOG_LEVEL = 'WARNING'
    config.MFA_REQUIRED = False
    config.SECURITY_PASSWORD_SALT = 'test-salt'
    config.TESTSERVER_URL = 'http://testserver:8080'
    return config


@pytest.fixture
def app(mock_db, mock_config):
    """Create a minimal Quart test application with mocked services."""
    from unittest.mock import patch, AsyncMock as AM

    app = Quart(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_SECRET'] = 'test-jwt-secret-for-testing-only'
    app.config['JWT_EXPIRATION_HOURS'] = 24

    # Attach mock db to app
    app.db = mock_db

    # Register blueprints - patch dependencies so imports succeed
    with patch('database.connection.init_dal'), \
         patch('database.connection.get_db', return_value=mock_db), \
         patch('penguin_libs.validation.IsStrongPassword') as mock_validator_cls:

        mock_validator_result = MagicMock()
        mock_validator_result.is_valid = True
        mock_validator_result.error = None
        mock_validator = MagicMock(return_value=mock_validator_result)
        mock_validator_cls.return_value = mock_validator

        from services.auth_service import AuthService
        app.auth_service = AuthService(mock_db, mock_config)

        from routes.auth import auth_bp
        from routes.devices import devices_bp
        from routes.organizations import organizations_bp
        from routes.tests import tests_bp
        from routes.stats import stats_bp

        app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
        app.register_blueprint(devices_bp, url_prefix='/api/v1/devices')
        app.register_blueprint(organizations_bp, url_prefix='/api/v1/organizations')
        app.register_blueprint(tests_bp, url_prefix='/api/v1/tests')
        app.register_blueprint(stats_bp, url_prefix='/api/v1/stats')

    # Register error handlers
    @app.errorhandler(404)
    async def not_found(error):
        """Handle 404 Not Found errors"""
        from quart import jsonify
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404

    @app.errorhandler(500)
    async def internal_error(error):
        """Handle 500 Internal Server errors"""
        from quart import jsonify
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500

    return app


@pytest.fixture
def client(app):
    """Quart async test client."""
    return app.test_client()
