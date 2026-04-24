"""Data record types for managerServer.

These dataclasses provide type hints and helper methods.
All database access is via penguin_dal (get_db()), not ORM classes.
Table schemas are defined by Alembic migrations — penguin_dal reflects them at startup.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import bcrypt
import secrets


# ---------------------------------------------------------------------------
# Dataclass records (type hints + to_dict helpers)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class OrganizationUnitRecord:
    id: int
    name: str
    description: Optional[str]
    created_at: Any
    updated_at: Any

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass(slots=True)
class UserRecord:
    id: int
    username: str
    email: str
    password_hash: str
    api_key: str
    role: str
    ou_id: Optional[int]
    mfa_enabled: bool
    mfa_secret: Optional[str]
    is_active: bool
    created_at: Any
    updated_at: Any

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self, include_sensitive: bool = False) -> dict:
        data: dict = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'ou_id': self.ou_id,
            'mfa_enabled': self.mfa_enabled,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_sensitive:
            data['api_key'] = self.api_key
            data['mfa_secret'] = self.mfa_secret
        return data


@dataclass(slots=True)
class SessionRecord:
    id: int
    session_id: str
    user_id: int
    data: Any
    expires_at: Any
    created_at: Any


@dataclass(slots=True)
class JWTTokenRecord:
    id: int
    user_id: int
    token_hash: str
    expires_at: Any
    issued_at: Any
    revoked: bool


@dataclass(slots=True)
class SystemConfigRecord:
    id: int
    config_key: str
    config_value: Optional[str]
    config_type: str
    description: Optional[str]
    updated_by: Optional[int]
    created_at: Any
    updated_at: Any

    def to_dict(self) -> dict:
        return {
            'config_key': self.config_key,
            'config_value': self.config_value,
            'config_type': self.config_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass(slots=True)
class OUEnrollmentSecretRecord:
    id: int
    ou_id: int
    secret: str
    name: Optional[str]
    is_active: bool
    created_by: Optional[int]
    created_at: Any

    def to_dict(self, include_secret: bool = False) -> dict:
        data: dict = {
            'id': self.id,
            'ou_id': self.ou_id,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_secret:
            data['secret'] = self.secret
        return data


@dataclass(slots=True)
class DeviceEnrollmentRecord:
    id: int
    ou_id: int
    enrollment_secret_id: int
    device_serial: str
    device_hostname: str
    device_os: str
    device_os_version: str
    client_type: str
    client_version: Optional[str]
    enrolled_ip: str
    enrolled_at: Any
    last_seen: Any
    is_active: bool

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ou_id': self.ou_id,
            'device_serial': self.device_serial,
            'device_hostname': self.device_hostname,
            'device_os': self.device_os,
            'device_os_version': self.device_os_version,
            'client_type': self.client_type,
            'client_version': self.client_version,
            'enrolled_ip': self.enrolled_ip,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_active': self.is_active,
        }


@dataclass(slots=True)
class ClientConfigRecord:
    id: int
    user_id: Optional[int]
    ou_id: Optional[int]
    config_name: str
    config_data: Any
    is_default: bool
    created_at: Any
    updated_at: Any

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ou_id': self.ou_id,
            'config_name': self.config_name,
            'config_data': self.config_data,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# Utility functions (previously static methods on model classes)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def generate_api_key() -> str:
    """Generate a secure 64-character API key."""
    return secrets.token_hex(32)


def generate_enrollment_secret() -> str:
    """Generate a secure enrollment secret (similar to FleetDM)."""
    return secrets.token_urlsafe(48)


# ---------------------------------------------------------------------------
# Row → Record converters
# ---------------------------------------------------------------------------

def row_to_user(row: Any) -> UserRecord:
    """Convert a penguin_dal Row to a UserRecord."""
    return UserRecord(
        id=row.id,
        username=row.username,
        email=row.email,
        password_hash=row.password_hash,
        api_key=row.api_key,
        role=row.role,
        ou_id=row.ou_id,
        mfa_enabled=bool(row.mfa_enabled),
        mfa_secret=row.mfa_secret,
        is_active=bool(row.is_active),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def row_to_organization(row: Any) -> OrganizationUnitRecord:
    """Convert a penguin_dal Row to an OrganizationUnitRecord."""
    return OrganizationUnitRecord(
        id=row.id,
        name=row.name,
        description=row.description,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def row_to_session(row: Any) -> SessionRecord:
    """Convert a penguin_dal Row to a SessionRecord."""
    return SessionRecord(
        id=row.id,
        session_id=row.session_id,
        user_id=row.user_id,
        data=row.data,
        expires_at=row.expires_at,
        created_at=row.created_at,
    )


def row_to_jwt_token(row: Any) -> JWTTokenRecord:
    """Convert a penguin_dal Row to a JWTTokenRecord."""
    return JWTTokenRecord(
        id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        issued_at=row.issued_at,
        revoked=bool(row.revoked),
    )


def row_to_system_config(row: Any) -> SystemConfigRecord:
    """Convert a penguin_dal Row to a SystemConfigRecord."""
    return SystemConfigRecord(
        id=row.id,
        config_key=row.config_key,
        config_value=row.config_value,
        config_type=row.config_type,
        description=row.description,
        updated_by=row.updated_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def row_to_enrollment_secret(row: Any) -> OUEnrollmentSecretRecord:
    """Convert a penguin_dal Row to an OUEnrollmentSecretRecord."""
    return OUEnrollmentSecretRecord(
        id=row.id,
        ou_id=row.ou_id,
        secret=row.secret,
        name=row.name,
        is_active=bool(row.is_active),
        created_by=row.created_by,
        created_at=row.created_at,
    )


def row_to_device_enrollment(row: Any) -> DeviceEnrollmentRecord:
    """Convert a penguin_dal Row to a DeviceEnrollmentRecord."""
    return DeviceEnrollmentRecord(
        id=row.id,
        ou_id=row.ou_id,
        enrollment_secret_id=row.enrollment_secret_id,
        device_serial=row.device_serial,
        device_hostname=row.device_hostname,
        device_os=row.device_os,
        device_os_version=row.device_os_version,
        client_type=row.client_type,
        client_version=row.client_version,
        enrolled_ip=row.enrolled_ip,
        enrolled_at=row.enrolled_at,
        last_seen=row.last_seen,
        is_active=bool(row.is_active),
    )


def row_to_client_config(row: Any) -> ClientConfigRecord:
    """Convert a penguin_dal Row to a ClientConfigRecord."""
    return ClientConfigRecord(
        id=row.id,
        user_id=row.user_id,
        ou_id=row.ou_id,
        config_name=row.config_name,
        config_data=row.config_data,
        is_default=bool(row.is_default),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
