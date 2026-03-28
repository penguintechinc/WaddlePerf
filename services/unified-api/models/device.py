"""Device and EnrollmentSecret models for device management"""

from datetime import datetime


def define_device_models(db):  # pragma: no cover
    """Define device-related tables with enrollment support.

    Defines:
        - device_device: Registered devices with enrollment status
        - device_enrollment_secret: Enrollment secrets for device onboarding

    Args:
        db: PyDAL DAL instance
    """

    # Device table for managing connected devices
    db.define_table(
        'device_device',
        db.Field('name', 'string', length=255, notnull=True),
        db.Field('device_id', 'string', length=128, unique=True, notnull=True),
        db.Field(
            'serial_number',
            'string',
            length=255,
            default='',
            comment='Hardware serial number'
        ),
        db.Field(
            'type',
            'string',
            length=50,
            default='generic',
            comment='Device type: generic, testbed, iot, edge'
        ),
        db.Field('status', 'string', length=50, default='offline',
                 comment='online, offline, error, maintenance'),
        db.Field(
            'organization_id',
            'reference auth_organization',
            notnull=True,
            ondelete='CASCADE'
        ),
        db.Field(
            'organization_unit_id',
            'reference auth_organization_unit',
            default=None,
            ondelete='SET NULL',
            comment='Optional assignment to organizational unit'
        ),
        db.Field('ip_address', 'string', length=45, default='',
                 comment='Current IPv4 or IPv6 address'),
        db.Field('mac_address', 'string', length=17, default='',
                 comment='MAC address for network identification'),
        db.Field('firmware_version', 'string', length=128, default=''),
        db.Field('last_seen', 'datetime', default=None),
        db.Field('last_reported_at', 'datetime', default=None),
        db.Field('enrolled_at', 'datetime', default=None),
        db.Field(
            'metadata',
            'text',
            default='{}',
            comment='Flexible JSON metadata: OS, CPU, memory, etc.'
        ),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        db.Field('updated_at', 'datetime', default=datetime.utcnow,
                 update=datetime.utcnow),
        primarykey=['id'],
        indexes=[['device_id'], ['organization_id'], ['status']],
        migrate='device_device'
    )

    # Enrollment Secret table for secure device onboarding
    db.define_table(
        'device_enrollment_secret',
        db.Field('secret', 'string', length=255, unique=True, notnull=True,
                 comment='Secure enrollment token'),
        db.Field(
            'organization_id',
            'reference auth_organization',
            notnull=True,
            ondelete='CASCADE'
        ),
        db.Field(
            'device_id',
            'reference device_device',
            default=None,
            ondelete='CASCADE',
            comment='Associated device after enrollment'
        ),
        db.Field('status', 'string', length=50, default='active',
                 comment='active, used, expired, revoked'),
        db.Field('used_at', 'datetime', default=None),
        db.Field('expires_at', 'datetime', default=None,
                 comment='Expiration time for enrollment secret'),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        db.Field('updated_at', 'datetime', default=datetime.utcnow,
                 update=datetime.utcnow),
        primarykey=['id'],
        indexes=[['secret'], ['organization_id'], ['status']],
        migrate='device_enrollment_secret'
    )
