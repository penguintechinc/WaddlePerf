"""Organization and OrganizationUnit models with hierarchy support"""

from datetime import datetime


def define_organization_models(db):  # pragma: no cover
    """Define organization-related tables with hierarchical structure.

    Defines:
        - auth_organization: Top-level organization/tenant
        - auth_organization_unit: Organizational units (teams/departments) with
          parent-child hierarchy

    Args:
        db: PyDAL DAL instance
    """

    # Organization (tenant) table
    db.define_table(
        'auth_organization',
        db.Field('name', 'string', length=255, notnull=True),
        db.Field('slug', 'string', length=128, unique=True, notnull=True),
        db.Field('description', 'text', default=''),
        db.Field('website', 'string', length=255, default=''),
        db.Field('logo_url', 'string', length=512, default=''),
        db.Field('active', 'boolean', default=True, notnull=True),
        db.Field(
            'tier',
            'string',
            length=50,
            default='free',
            comment='free, pro, enterprise'
        ),
        db.Field(
            'max_users',
            'integer',
            default=5,
            comment='Maximum number of users allowed'
        ),
        db.Field(
            'max_devices',
            'integer',
            default=10,
            comment='Maximum number of devices allowed'
        ),
        db.Field('metadata', 'text', default='{}',
                 comment='Flexible JSON metadata'),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        db.Field('updated_at', 'datetime', default=datetime.utcnow,
                 update=datetime.utcnow),
        primarykey=['id'],
        indexes=[['slug'], ['active']],
        migrate='auth_organization'
    )

    # Organization Unit (team/department) table with hierarchy
    db.define_table(
        'auth_organization_unit',
        db.Field('name', 'string', length=255, notnull=True),
        db.Field('description', 'text', default=''),
        db.Field(
            'organization_id',
            'reference auth_organization',
            notnull=True,
            ondelete='CASCADE'
        ),
        db.Field(
            'parent_id',
            'reference auth_organization_unit',
            default=None,
            ondelete='CASCADE',
            comment='Parent unit for hierarchical structure'
        ),
        db.Field('level', 'integer', default=0,
                 comment='Hierarchy level (0=top-level unit)'),
        db.Field('path', 'string', length=512, default='',
                 comment='Materialized path for hierarchy queries'),
        db.Field('active', 'boolean', default=True),
        db.Field('metadata', 'text', default='{}',
                 comment='Flexible JSON metadata'),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        db.Field('updated_at', 'datetime', default=datetime.utcnow,
                 update=datetime.utcnow),
        primarykey=['id'],
        indexes=[['organization_id'], ['parent_id'], ['active']],
        migrate='auth_organization_unit'
    )
