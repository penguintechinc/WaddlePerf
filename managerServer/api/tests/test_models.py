"""Unit tests for managerServer models and row converters."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

import bcrypt

from models import (
    OrganizationUnitRecord,
    UserRecord,
    SessionRecord,
    JWTTokenRecord,
    SystemConfigRecord,
    OUEnrollmentSecretRecord,
    DeviceEnrollmentRecord,
    ClientConfigRecord,
    hash_password,
    generate_api_key,
    generate_enrollment_secret,
    row_to_user,
    row_to_organization,
    row_to_session,
    row_to_jwt_token,
    row_to_system_config,
    row_to_enrollment_secret,
    row_to_device_enrollment,
    row_to_client_config,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _make_user_row(**overrides):
    row = MagicMock()
    row.id = overrides.get('id', 1)
    row.username = overrides.get('username', 'testuser')
    row.email = overrides.get('email', 'test@example.com')
    row.password_hash = overrides.get('password_hash', hash_password('secret'))
    row.api_key = overrides.get('api_key', 'abc123')
    row.role = overrides.get('role', 'global_admin')
    row.ou_id = overrides.get('ou_id', None)
    row.mfa_enabled = overrides.get('mfa_enabled', 0)
    row.mfa_secret = overrides.get('mfa_secret', None)
    row.is_active = overrides.get('is_active', 1)
    row.created_at = overrides.get('created_at', _dt('2025-01-01T00:00:00'))
    row.updated_at = overrides.get('updated_at', _dt('2025-01-02T00:00:00'))
    return row


def _make_org_row(**overrides):
    row = MagicMock()
    row.id = overrides.get('id', 10)
    row.name = overrides.get('name', 'HQ')
    row.description = overrides.get('description', 'Headquarters')
    row.created_at = overrides.get('created_at', _dt('2025-01-01T00:00:00'))
    row.updated_at = overrides.get('updated_at', _dt('2025-01-02T00:00:00'))
    return row


# ---------------------------------------------------------------------------
# OrganizationUnitRecord
# ---------------------------------------------------------------------------

class TestOrganizationUnitRecord:
    def test_to_dict_contains_required_keys(self):
        rec = OrganizationUnitRecord(
            id=1, name='HQ', description='Head office',
            created_at=_dt('2025-01-01T00:00:00'),
            updated_at=_dt('2025-01-02T00:00:00'),
        )
        d = rec.to_dict()
        assert set(d.keys()) >= {'id', 'name', 'description', 'created_at', 'updated_at'}

    def test_to_dict_isoformat_dates(self):
        ts = _dt('2025-06-15T12:00:00')
        rec = OrganizationUnitRecord(id=2, name='OU', description=None, created_at=ts, updated_at=ts)
        d = rec.to_dict()
        assert d['created_at'] == ts.isoformat()
        assert d['updated_at'] == ts.isoformat()

    def test_to_dict_none_dates(self):
        rec = OrganizationUnitRecord(id=3, name='X', description=None, created_at=None, updated_at=None)
        d = rec.to_dict()
        assert d['created_at'] is None
        assert d['updated_at'] is None

    def test_to_dict_none_description(self):
        rec = OrganizationUnitRecord(id=4, name='Y', description=None, created_at=None, updated_at=None)
        assert rec.to_dict()['description'] is None


# ---------------------------------------------------------------------------
# UserRecord
# ---------------------------------------------------------------------------

class TestUserRecord:
    def _make_user(self, **kwargs) -> UserRecord:
        defaults = dict(
            id=1, username='alice', email='alice@example.com',
            password_hash=hash_password('pass'), api_key='key1',
            role='global_admin', ou_id=None, mfa_enabled=False,
            mfa_secret=None, is_active=True,
            created_at=_dt('2025-01-01T00:00:00'),
            updated_at=_dt('2025-01-01T00:00:00'),
        )
        defaults.update(kwargs)
        return UserRecord(**defaults)

    def test_check_password_correct(self):
        user = self._make_user(password_hash=hash_password('correct'))
        assert user.check_password('correct') is True

    def test_check_password_wrong(self):
        user = self._make_user(password_hash=hash_password('correct'))
        assert user.check_password('wrong') is False

    def test_to_dict_excludes_sensitive_by_default(self):
        user = self._make_user(api_key='secret-key', mfa_secret='mfa-secret')
        d = user.to_dict()
        assert 'api_key' not in d
        assert 'mfa_secret' not in d

    def test_to_dict_includes_sensitive_when_requested(self):
        user = self._make_user(api_key='secret-key', mfa_secret='mfa-secret')
        d = user.to_dict(include_sensitive=True)
        assert d['api_key'] == 'secret-key'
        assert d['mfa_secret'] == 'mfa-secret'

    def test_to_dict_contains_base_fields(self):
        user = self._make_user()
        d = user.to_dict()
        assert set(d.keys()) >= {'id', 'username', 'email', 'role', 'ou_id', 'mfa_enabled', 'is_active'}

    def test_to_dict_isoformat_dates(self):
        ts = _dt('2025-03-01T10:00:00')
        user = self._make_user(created_at=ts, updated_at=ts)
        d = user.to_dict()
        assert d['created_at'] == ts.isoformat()

    def test_to_dict_none_dates(self):
        user = self._make_user(created_at=None, updated_at=None)
        d = user.to_dict()
        assert d['created_at'] is None
        assert d['updated_at'] is None

    def test_slots_are_set(self):
        user = self._make_user()
        # slots=True means no __dict__
        assert not hasattr(user, '__dict__')


# ---------------------------------------------------------------------------
# SystemConfigRecord
# ---------------------------------------------------------------------------

class TestSystemConfigRecord:
    def _make_config(self, **kwargs) -> SystemConfigRecord:
        defaults = dict(
            id=1, config_key='test_key', config_value='test_val',
            config_type='string', description='A test key',
            updated_by=None,
            created_at=_dt('2025-01-01T00:00:00'),
            updated_at=_dt('2025-01-02T00:00:00'),
        )
        defaults.update(kwargs)
        return SystemConfigRecord(**defaults)

    def test_to_dict_contains_required_keys(self):
        cfg = self._make_config()
        d = cfg.to_dict()
        assert set(d.keys()) >= {'config_key', 'config_value', 'config_type', 'description'}

    def test_to_dict_isoformat_updated_at(self):
        ts = _dt('2025-04-01T08:00:00')
        cfg = self._make_config(updated_at=ts)
        assert cfg.to_dict()['updated_at'] == ts.isoformat()

    def test_to_dict_none_updated_at(self):
        cfg = self._make_config(updated_at=None)
        assert cfg.to_dict()['updated_at'] is None


# ---------------------------------------------------------------------------
# OUEnrollmentSecretRecord
# ---------------------------------------------------------------------------

class TestOUEnrollmentSecretRecord:
    def _make(self, **kwargs) -> OUEnrollmentSecretRecord:
        defaults = dict(
            id=1, ou_id=5, secret='supersecret', name='Main Secret',
            is_active=True, created_by=1, created_at=_dt('2025-01-01T00:00:00'),
        )
        defaults.update(kwargs)
        return OUEnrollmentSecretRecord(**defaults)

    def test_to_dict_excludes_secret_by_default(self):
        rec = self._make()
        assert 'secret' not in rec.to_dict()

    def test_to_dict_includes_secret_when_requested(self):
        rec = self._make(secret='mysecret')
        assert rec.to_dict(include_secret=True)['secret'] == 'mysecret'

    def test_to_dict_isoformat_created_at(self):
        ts = _dt('2025-05-01T00:00:00')
        rec = self._make(created_at=ts)
        assert rec.to_dict()['created_at'] == ts.isoformat()


# ---------------------------------------------------------------------------
# DeviceEnrollmentRecord
# ---------------------------------------------------------------------------

class TestDeviceEnrollmentRecord:
    def _make(self, **kwargs) -> DeviceEnrollmentRecord:
        defaults = dict(
            id=1, ou_id=2, enrollment_secret_id=3,
            device_serial='SN-001', device_hostname='host1',
            device_os='Linux', device_os_version='5.15',
            client_type='container', client_version='1.0',
            enrolled_ip='10.0.0.1',
            enrolled_at=_dt('2025-01-01T00:00:00'),
            last_seen=_dt('2025-01-02T00:00:00'),
            is_active=True,
        )
        defaults.update(kwargs)
        return DeviceEnrollmentRecord(**defaults)

    def test_to_dict_contains_required_keys(self):
        d = self._make().to_dict()
        for key in ('id', 'ou_id', 'device_serial', 'device_hostname', 'device_os',
                    'device_os_version', 'client_type', 'enrolled_ip', 'is_active'):
            assert key in d

    def test_to_dict_isoformat_dates(self):
        ts = _dt('2025-06-01T00:00:00')
        rec = self._make(enrolled_at=ts, last_seen=ts)
        d = rec.to_dict()
        assert d['enrolled_at'] == ts.isoformat()
        assert d['last_seen'] == ts.isoformat()

    def test_to_dict_none_dates(self):
        rec = self._make(enrolled_at=None, last_seen=None)
        d = rec.to_dict()
        assert d['enrolled_at'] is None
        assert d['last_seen'] is None


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

class TestHashPassword:
    def test_returns_string(self):
        result = hash_password('mypassword')
        assert isinstance(result, str)

    def test_result_is_bcrypt_hash(self):
        pw = 'testpass'
        hashed = hash_password(pw)
        assert bcrypt.checkpw(pw.encode('utf-8'), hashed.encode('utf-8'))

    def test_different_inputs_give_different_hashes(self):
        h1 = hash_password('abc')
        h2 = hash_password('def')
        assert h1 != h2

    def test_same_input_gives_different_hash_each_call(self):
        # bcrypt uses random salt
        h1 = hash_password('same')
        h2 = hash_password('same')
        assert h1 != h2


class TestGenerateApiKey:
    def test_returns_string(self):
        assert isinstance(generate_api_key(), str)

    def test_length_is_64_chars(self):
        assert len(generate_api_key()) == 64

    def test_keys_are_unique(self):
        assert generate_api_key() != generate_api_key()

    def test_key_is_hex(self):
        key = generate_api_key()
        int(key, 16)  # should not raise


class TestGenerateEnrollmentSecret:
    def test_returns_string(self):
        assert isinstance(generate_enrollment_secret(), str)

    def test_secrets_are_unique(self):
        assert generate_enrollment_secret() != generate_enrollment_secret()

    def test_secret_is_non_empty(self):
        assert len(generate_enrollment_secret()) > 0


# ---------------------------------------------------------------------------
# Row converters
# ---------------------------------------------------------------------------

class TestRowToUser:
    def test_converts_row_to_user_record(self):
        row = _make_user_row()
        user = row_to_user(row)
        assert isinstance(user, UserRecord)
        assert user.id == row.id
        assert user.username == row.username
        assert user.email == row.email

    def test_bool_coercion_mfa_enabled(self):
        row = _make_user_row(mfa_enabled=1)
        user = row_to_user(row)
        assert user.mfa_enabled is True

    def test_bool_coercion_is_active(self):
        row = _make_user_row(is_active=0)
        user = row_to_user(row)
        assert user.is_active is False

    def test_all_fields_mapped(self):
        row = _make_user_row(
            role='ou_admin', ou_id=7, mfa_secret='TOTP123'
        )
        user = row_to_user(row)
        assert user.role == 'ou_admin'
        assert user.ou_id == 7
        assert user.mfa_secret == 'TOTP123'


class TestRowToOrganization:
    def test_converts_row_to_org_record(self):
        row = _make_org_row()
        org = row_to_organization(row)
        assert isinstance(org, OrganizationUnitRecord)
        assert org.id == row.id
        assert org.name == row.name

    def test_description_mapped(self):
        row = _make_org_row(description='Some OU')
        org = row_to_organization(row)
        assert org.description == 'Some OU'


class TestRowToSession:
    def test_converts_row_to_session_record(self):
        row = MagicMock()
        row.id = 1
        row.session_id = 'sess-abc'
        row.user_id = 2
        row.data = {}
        row.expires_at = _dt('2025-12-31T00:00:00')
        row.created_at = _dt('2025-01-01T00:00:00')
        session = row_to_session(row)
        assert isinstance(session, SessionRecord)
        assert session.session_id == 'sess-abc'
        assert session.user_id == 2


class TestRowToJwtToken:
    def test_converts_row_to_jwt_token_record(self):
        row = MagicMock()
        row.id = 5
        row.user_id = 3
        row.token_hash = 'hash123'
        row.expires_at = _dt('2025-12-31T00:00:00')
        row.issued_at = _dt('2025-01-01T00:00:00')
        row.revoked = 0
        token = row_to_jwt_token(row)
        assert isinstance(token, JWTTokenRecord)
        assert token.revoked is False

    def test_revoked_bool_coercion(self):
        row = MagicMock()
        row.id = 6
        row.user_id = 1
        row.token_hash = 'x'
        row.expires_at = _dt('2025-01-01T00:00:00')
        row.issued_at = _dt('2025-01-01T00:00:00')
        row.revoked = 1
        token = row_to_jwt_token(row)
        assert token.revoked is True


class TestRowToSystemConfig:
    def test_converts_all_fields(self):
        row = MagicMock()
        row.id = 1
        row.config_key = 'key'
        row.config_value = 'value'
        row.config_type = 'string'
        row.description = 'desc'
        row.updated_by = None
        row.created_at = _dt('2025-01-01T00:00:00')
        row.updated_at = _dt('2025-01-01T00:00:00')
        cfg = row_to_system_config(row)
        assert isinstance(cfg, SystemConfigRecord)
        assert cfg.config_key == 'key'


class TestRowToEnrollmentSecret:
    def test_converts_is_active_to_bool(self):
        row = MagicMock()
        row.id = 1
        row.ou_id = 2
        row.secret = 'sec'
        row.name = 'name'
        row.is_active = 1
        row.created_by = None
        row.created_at = _dt('2025-01-01T00:00:00')
        secret = row_to_enrollment_secret(row)
        assert isinstance(secret, OUEnrollmentSecretRecord)
        assert secret.is_active is True


class TestRowToDeviceEnrollment:
    def test_converts_is_active_to_bool(self):
        row = MagicMock()
        row.id = 1
        row.ou_id = 2
        row.enrollment_secret_id = 3
        row.device_serial = 'SN'
        row.device_hostname = 'host'
        row.device_os = 'Linux'
        row.device_os_version = '5.15'
        row.client_type = 'container'
        row.client_version = '1.0'
        row.enrolled_ip = '10.0.0.1'
        row.enrolled_at = _dt('2025-01-01T00:00:00')
        row.last_seen = _dt('2025-01-01T00:00:00')
        row.is_active = 0
        device = row_to_device_enrollment(row)
        assert device.is_active is False


class TestRowToClientConfig:
    def test_converts_is_default_to_bool(self):
        row = MagicMock()
        row.id = 1
        row.user_id = None
        row.ou_id = 2
        row.config_name = 'Default'
        row.config_data = {}
        row.is_default = 1
        row.created_at = _dt('2025-01-01T00:00:00')
        row.updated_at = _dt('2025-01-01T00:00:00')
        cc = row_to_client_config(row)
        assert isinstance(cc, ClientConfigRecord)
        assert cc.is_default is True
