"""User, Role, and UserRole models with Flask-Security-Too compatibility"""

from datetime import datetime


def define_user_models(db):  # pragma: no cover
    """Define user-related tables for Flask-Security-Too integration.

    Defines:
        - auth_user: User accounts with hashed passwords
        - auth_role: Role definitions for RBAC
        - auth_user_role: Many-to-many relationship between users and roles

    Args:
        db: PyDAL DAL instance
    """

    # User table - compatible with Flask-Security-Too
    db.define_table(
        'auth_user',
        db.Field('email', 'string', length=255, unique=True, notnull=True),
        db.Field('username', 'string', length=128, unique=True, notnull=True),
        db.Field('password', 'string', length=255, notnull=True),
        db.Field('first_name', 'string', length=128, default=''),
        db.Field('last_name', 'string', length=128, default=''),
        db.Field('active', 'boolean', default=True, notnull=True),
        db.Field('fs_uniquifier', 'string', length=64, unique=True),
        db.Field(
            'confirmed_at',
            'datetime',
            default=None,
            comment='Email confirmation timestamp'
        ),
        db.Field(
            'last_login_at',
            'datetime',
            default=None,
            comment='Last successful login'
        ),
        db.Field(
            'current_login_at',
            'datetime',
            default=None,
            comment='Current session login'
        ),
        db.Field('last_login_ip', 'string', length=45, default=''),
        db.Field('current_login_ip', 'string', length=45, default=''),
        db.Field('login_count', 'integer', default=0),
        db.Field(
            'organization_id',
            'reference auth_organization',
            ondelete='CASCADE'
        ),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        db.Field('updated_at', 'datetime', default=datetime.utcnow,
                 update=datetime.utcnow),
        primarykey=['id'],
        indexes=[['email'], ['username'], ['organization_id']],
        migrate='auth_user'
    )

    # Role table - standard RBAC roles
    db.define_table(
        'auth_role',
        db.Field('name', 'string', length=128, unique=True, notnull=True),
        db.Field('description', 'text', default=''),
        db.Field(
            'scopes',
            'text',
            default='',
            comment='Comma-separated list of OAuth2-style permission scopes'
        ),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        db.Field('updated_at', 'datetime', default=datetime.utcnow,
                 update=datetime.utcnow),
        primarykey=['id'],
        indexes=[['name']],
        migrate='auth_role'
    )

    # User-Role association table for many-to-many relationship
    db.define_table(
        'auth_user_role',
        db.Field('user_id', 'reference auth_user', notnull=True,
                 ondelete='CASCADE'),
        db.Field('role_id', 'reference auth_role', notnull=True,
                 ondelete='CASCADE'),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        primarykey=['id'],
        indexes=[['user_id'], ['role_id'], [['user_id', 'role_id']]],
        migrate='auth_user_role'
    )
