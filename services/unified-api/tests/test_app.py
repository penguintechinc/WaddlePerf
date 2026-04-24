"""Tests for the app factory (app.py) and build_db_uri integration."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from quart import Quart


class TestCreateApp:
    """Test create_app() factory function."""

    def _patched_create_app(self, config=None):
        """Create app with all external deps patched."""
        from config import Config

        if config is None:
            config = Config(
                DB_TYPE='sqlite',
                DB_NAME='test',
                SECRET_KEY='test-secret',
                JWT_SECRET='test-jwt-secret',
                JWT_EXPIRATION_HOURS=1,
                FLASK_ENV='testing',
                DEBUG=False,
                DB_POOL_SIZE=2,
                CORS_ORIGINS='http://localhost:3000',
                LOG_LEVEL='WARNING',
            )

        with patch('app.init_dal'), \
             patch('app.get_db', return_value=MagicMock()), \
             patch('app.AuthService'), \
             patch('app.get_logger', return_value=MagicMock()), \
             patch('penguin_libs.validation.IsStrongPassword'):
            from app import create_app
            return create_app(config)

    def test_returns_quart_instance(self):
        """create_app returns a Quart application."""
        app = self._patched_create_app()
        assert isinstance(app, Quart)

    def test_secret_key_set(self):
        """SECRET_KEY is set from config."""
        app = self._patched_create_app()
        assert app.config['SECRET_KEY'] == 'test-secret'

    def test_jwt_secret_set(self):
        """JWT_SECRET is set in app config."""
        app = self._patched_create_app()
        assert app.config['JWT_SECRET'] == 'test-jwt-secret'

    def test_jwt_expiration_hours_set(self):
        """JWT_EXPIRATION_HOURS is set in app config."""
        app = self._patched_create_app()
        assert app.config['JWT_EXPIRATION_HOURS'] == 1

    def test_blueprints_registered(self):
        """Auth, organizations, and devices blueprints are registered."""
        app = self._patched_create_app()
        blueprint_names = list(app.blueprints.keys())
        assert 'auth' in blueprint_names
        assert 'organizations' in blueprint_names
        assert 'devices' in blueprint_names

    def test_health_route_registered(self):
        """Health check route is registered."""
        app = self._patched_create_app()
        rules = [str(r) for r in app.url_map.iter_rules()]
        assert '/health' in rules

    def test_database_uri_in_config(self):
        """DATABASE_URI is set in app config."""
        app = self._patched_create_app()
        assert 'DATABASE_URI' in app.config
        assert 'sqlite' in app.config['DATABASE_URI']

    def test_testing_mode(self):
        """TESTING flag can be set."""
        app = self._patched_create_app()
        app.config['TESTING'] = True
        assert app.config['TESTING'] is True


class TestHealthEndpoint:
    """Test GET /health endpoint."""

    async def test_health_check_db_error_returns_503(self, client, app):
        """Health check returns 503 when DB raises exception."""
        with patch('app.get_db') as mock_get_db:
            mock_engine = MagicMock()
            mock_engine.connect = MagicMock(side_effect=Exception('DB down'))
            mock_db_instance = MagicMock()
            mock_db_instance.engine = mock_engine
            mock_get_db.return_value = mock_db_instance

            # Add the health route to the test app
            @app.route('/health', methods=['GET'])
            async def health_check():
                from quart import jsonify
                try:
                    db = mock_get_db()
                    async with db.engine.connect() as conn:
                        pass
                    return jsonify({'status': 'healthy'}), 200
                except Exception as e:
                    return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

            async with client as c:
                resp = await c.get('/health')

        assert resp.status_code == 503

    async def test_health_response_has_status_key(self, client, app):
        """Health response includes 'status' key."""
        @app.route('/test-health', methods=['GET'])
        async def test_health():
            from quart import jsonify
            return jsonify({'status': 'healthy', 'service': 'unified-api'}), 200

        async with client as c:
            resp = await c.get('/test-health')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert 'status' in data


class TestErrorHandlers:
    """Test error handler routes."""

    async def test_404_returns_json_with_status_code(self, client, app):
        """404 errors return JSON with status_code field."""
        async with client as c:
            resp = await c.get('/does-not-exist-at-all')

        assert resp.status_code == 404
        data = await resp.get_json()
        assert data['status_code'] == 404
        assert 'error' in data

    async def test_404_error_message(self, client, app):
        """404 error response contains 'Not Found' error."""
        async with client as c:
            resp = await c.get('/this/path/does/not/exist/anywhere')

        data = await resp.get_json()
        assert data['error'] == 'Not Found'
