"""Shared pytest fixtures for webClient/api tests."""
import sys
import os
from unittest.mock import MagicMock, patch

def pytest_configure(config):
    """Mock missing dependencies at pytest startup, before any imports."""
    mock_logging = MagicMock()
    mock_logging.get_logger = MagicMock(return_value=MagicMock())

    sys.modules['penguin_licensing'] = MagicMock()
    sys.modules['penguintechinc_utils'] = mock_logging
    sys.modules['penguintechinc_utils.logging'] = mock_logging
    sys.modules['penguin_libs'] = MagicMock()
    sys.modules['pymysql'] = MagicMock()
    sys.modules['pymysql.cursors'] = MagicMock()

import pytest


@pytest.fixture(autouse=True)
def disable_real_db(monkeypatch):
    """Prevent any real database connections during tests."""
    monkeypatch.setenv('AUTH_ENABLED', 'false')
    monkeypatch.setenv('DB_HOST', 'localhost')
    monkeypatch.setenv('DB_USER', 'test')
    monkeypatch.setenv('DB_PASS', 'test')
    monkeypatch.setenv('DB_NAME', 'test')
    monkeypatch.setenv('MANAGER_URL', 'http://manager.test')
    monkeypatch.setenv('TESTSERVER_URL', 'http://testserver.test')


@pytest.fixture
def app():
    """Return the Flask app with TESTING enabled.

    webClient/api uses a module-level ``app`` (not an app factory), so we
    import it directly and set TESTING mode on the existing instance.

    The app module must be imported AFTER env vars are set (via disable_real_db fixture).
    """
    import importlib
    import sys

    # Reload app module to pick up env var changes from disable_real_db
    if 'app' in sys.modules:
        del sys.modules['app']

    import app as app_module
    flask_app = app_module.app
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret'
    flask_app.config['SESSION_COOKIE_SECURE'] = False
    return flask_app


@pytest.fixture
def client(app):
    """Flask test client."""
    with app.test_client() as c:
        yield c
