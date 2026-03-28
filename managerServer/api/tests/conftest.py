"""Shared pytest fixtures for managerServer/api tests."""
import sys
from unittest.mock import MagicMock, patch

# Mock missing dependencies before imports
mock_utils = MagicMock()
mock_utils.logging.get_logger = MagicMock(return_value=MagicMock())

sys.modules['penguin_dal'] = MagicMock()
sys.modules['penguin_dal.flask_ext'] = MagicMock()
sys.modules['penguin_licensing'] = MagicMock()
sys.modules['penguintechinc_utils'] = mock_utils
sys.modules['penguintechinc_utils.logging'] = mock_utils.logging
sys.modules['penguin_libs'] = MagicMock()

import pytest


class FirstMockWrapper:
    """Wrapper for .first that supports both auth and subsequent lookups."""
    def __init__(self):
        self._return_value = None
        self._side_effects = []
        self._auth_set = False  # Track if auth was configured
        self._using_side_effects = False  # Track if side_effects are in use
        self.side_effect = None  # Allow direct side_effect assignment

    def __call__(self):
        """Call handler - returns either side_effect (if set) or return_value."""
        # If side_effect was explicitly set, use it
        if self.side_effect is not None:
            if isinstance(self.side_effect, list) and self.side_effect:
                return self.side_effect.pop(0)
        # If we're using internal side_effects, pop from them
        if self._using_side_effects and self._side_effects:
            return self._side_effects.pop(0)
        # Once side_effects are empty or not in use, return_value
        return self._return_value

    @property
    def return_value(self):
        return self._return_value

    @return_value.setter
    def return_value(self, value):
        """Smart setter: if setting non-None after being None, treat as auth setup.
        If setting None later, add it to side_effects to support multiple lookups."""
        if value is not None and self._return_value is None and not self._auth_set:
            # First time setting a non-None value - this is auth setup
            self._auth_set = True
            self._using_side_effects = True
            # Set up side_effects with the auth value first, then None for subsequent checks
            self._side_effects = [value, None, None]
            self._return_value = value
        elif value is None and self._auth_set and self._using_side_effects:
            # Setting to None after auth was set - this is for username/email checks
            # The side_effects already has the values from above, so do nothing
            pass
        else:
            # Any other assignment (including test overrides) - switch to return_value mode
            self._using_side_effects = False
            self._return_value = value


class DualModeSelect:
    """Select result that supports both .first() and iteration."""
    def __init__(self):
        # Use custom wrapper to allow both return_value and multiple calls
        self.first = FirstMockWrapper()
        self._iter_value = None

    def __iter__(self):
        """Support iteration."""
        if self._iter_value is not None:
            if hasattr(self._iter_value, '__iter__') and not isinstance(self._iter_value, str):
                return iter(self._iter_value)
        return iter([])


class SelectPropertyMock(MagicMock):
    """MagicMock for the .select method that intercepts return_value assignments."""
    def __init__(self, dual_select, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dual_select = dual_select
        super(MagicMock, self).__setattr__('return_value', dual_select)

    def __setattr__(self, name, value):
        """Intercept return_value to update _iter_value instead."""
        if name == 'return_value':
            # Update the DualModeSelect's iter value
            self._dual_select._iter_value = value
        else:
            super().__setattr__(name, value)


@pytest.fixture
def mock_db():
    """Mock penguin-dal DB instance with query support and MagicMock compatibility."""
    db = MagicMock()

    # Create a mock field that supports comparison operators
    class MockField:
        """Mock database field that supports comparison operations."""

        def __init__(self, name="field"):
            self.name = name

        def __eq__(self, other):
            return MagicMock()

        def __ne__(self, other):
            return MagicMock()

        def __gt__(self, other):
            return MagicMock()

        def __lt__(self, other):
            return MagicMock()

        def __ge__(self, other):
            return MagicMock()

        def __le__(self, other):
            return MagicMock()

        def __and__(self, other):
            return MagicMock()

        def __or__(self, other):
            return MagicMock()

    # Override table fields to support comparison operators
    db.sessions.session_id = MockField('sessions.session_id')
    db.sessions.expires_at = MockField('sessions.expires_at')
    db.sessions.user_id = MockField('sessions.user_id')

    db.users.id = MockField('users.id')
    db.users.username = MockField('users.username')
    db.users.is_active = MockField('users.is_active')
    db.users.email = MockField('users.email')
    db.users.mfa_secret = MockField('users.mfa_secret')

    db.jwt_tokens.token_hash = MockField('jwt_tokens.token_hash')
    db.jwt_tokens.revoked = MockField('jwt_tokens.revoked')

    db.devices.user_id = MockField('devices.user_id')

    db.organization_units.id = MockField('organization_units.id')

    # Setup query chain: db(condition).select()
    # Use DualModeSelect that supports both .first() and iteration
    dual_select = DualModeSelect()
    select_mock = SelectPropertyMock(dual_select)
    db.return_value.select = select_mock

    return db


@pytest.fixture
def app(mock_db):
    """Flask test application with mocked DB."""
    from app import create_app
    from config import Config

    # Create config object and set test values
    cfg = Config()
    cfg.SECRET_KEY = 'test-secret-key'
    cfg.JWT_SECRET = 'test-secret-key-32-chars-minimum!!'
    # Set DB params for the property
    cfg.DB_HOST = 'localhost'
    cfg.DB_PORT = '3306'
    cfg.DB_NAME = 'test_db'
    cfg.DB_USER = 'test_user'
    cfg.DB_PASS = ''

    # Create app with config object
    application = create_app(cfg)
    application.config['TESTING'] = True

    # Patch get_db at the module level for routes that import it
    with patch('routes.devices.get_db', return_value=mock_db):
        with patch('routes.auth.get_db', return_value=mock_db):
            with patch('routes.users.get_db', return_value=mock_db):
                with patch('routes.enrollment.get_db', return_value=mock_db):
                    with patch('routes.organizations.get_db', return_value=mock_db):
                        with patch('routes.results.get_db', return_value=mock_db):
                            with patch('routes.statistics.get_db', return_value=mock_db):
                                with patch('routes.config.get_db', return_value=mock_db):
                                    yield application


@pytest.fixture
def client(app):
    """Flask test client."""
    with app.test_client() as c:
        yield c


@pytest.fixture
def admin_token():
    """Valid JWT token for admin user."""
    import jwt
    import time
    payload = {
        'sub': '1',
        'email': 'admin@test.com',
        'role': 'Admin',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
    }
    return jwt.encode(payload, 'test-secret-key-32-chars-minimum!!', algorithm='HS256')


@pytest.fixture
def auth_headers(admin_token):
    """Authorization headers with admin JWT."""
    return {'Authorization': f'Bearer {admin_token}'}
