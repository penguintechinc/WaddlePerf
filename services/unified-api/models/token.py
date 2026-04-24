"""APIKey and RefreshToken models for authentication"""

from datetime import datetime


def define_token_models(db):  # pragma: no cover
    """Define token-related tables for API authentication and authorization.

    Defines:
        - auth_api_key: Long-lived API keys for service-to-service auth
        - auth_refresh_token: Refresh tokens for JWT token renewal

    Args:
        db: PyDAL DAL instance
    """

    # API Key table for service-to-service authentication
    db.define_table(
        'auth_api_key',
        db.Field('key', 'string', length=255, unique=True, notnull=True,
                 comment='Hashed API key'),
        db.Field('key_prefix', 'string', length=10, notnull=True,
                 comment='First 10 chars of key for identification'),
        db.Field(
            'user_id',
            'reference auth_user',
            notnull=True,
            ondelete='CASCADE',
            comment='User who created/owns this key'
        ),
        db.Field('name', 'string', length=255, notnull=True,
                 comment='Human-readable name for the key'),
        db.Field('description', 'text', default=''),
        db.Field(
            'scopes',
            'text',
            default='',
            comment='Comma-separated OAuth2-style permission scopes'
        ),
        db.Field('active', 'boolean', default=True),
        db.Field('last_used_at', 'datetime', default=None),
        db.Field('expires_at', 'datetime', default=None,
                 comment='Optional expiration time'),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        db.Field('updated_at', 'datetime', default=datetime.utcnow,
                 update=datetime.utcnow),
        primarykey=['id'],
        indexes=[['key'], ['key_prefix'], ['user_id'], ['active']],
        migrate='auth_api_key'
    )

    # Refresh Token table for JWT token renewal
    db.define_table(
        'auth_refresh_token',
        db.Field('token', 'string', length=512, unique=True, notnull=True,
                 comment='Refresh token value (hashed)'),
        db.Field(
            'user_id',
            'reference auth_user',
            notnull=True,
            ondelete='CASCADE',
            comment='User associated with this refresh token'
        ),
        db.Field(
            'jti',
            'string',
            length=128,
            notnull=True,
            comment='JWT ID from original token'
        ),
        db.Field('ip_address', 'string', length=45, default='',
                 comment='IP address where token was issued'),
        db.Field('user_agent', 'string', length=512, default='',
                 comment='User-Agent from token request'),
        db.Field('active', 'boolean', default=True),
        db.Field('revoked_at', 'datetime', default=None),
        db.Field('expires_at', 'datetime', notnull=True,
                 comment='Token expiration time'),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        db.Field('updated_at', 'datetime', default=datetime.utcnow,
                 update=datetime.utcnow),
        primarykey=['id'],
        indexes=[['token'], ['user_id'], ['jti'], ['active']],
        migrate='auth_refresh_token'
    )
