"""TestResult model for storing test execution results"""

from datetime import datetime


def define_test_models(db):  # pragma: no cover
    """Define test-related tables for test result storage and analysis.

    Defines:
        - test_result: Test execution results with flexible metadata

    Args:
        db: PyDAL DAL instance
    """

    # Test Result table for storing performance test results
    db.define_table(
        'test_result',
        db.Field('test_id', 'string', length=128, unique=True, notnull=True),
        db.Field(
            'name',
            'string',
            length=255,
            notnull=True,
            comment='Test name or description'
        ),
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
            ondelete='SET NULL',
            comment='Device that executed the test'
        ),
        db.Field(
            'organization_unit_id',
            'reference auth_organization_unit',
            default=None,
            ondelete='SET NULL',
            comment='Optional organizational unit context'
        ),
        db.Field(
            'status',
            'string',
            length=50,
            default='pending',
            comment='pending, running, completed, failed, skipped'
        ),
        db.Field(
            'duration_ms',
            'integer',
            default=0,
            comment='Test execution time in milliseconds'
        ),
        db.Field(
            'success',
            'boolean',
            default=False,
            comment='Overall test success/failure'
        ),
        db.Field('error_message', 'text', default='',
                 comment='Error message if test failed'),
        db.Field(
            'metrics',
            'text',
            default='{}',
            comment='Performance metrics: throughput, latency, memory, etc.'
        ),
        db.Field(
            'metadata',
            'text',
            default='{}',
            comment='Flexible JSON: test params, environment, tags, custom fields'
        ),
        db.Field('test_output', 'text', default='',
                 comment='Raw test output/logs'),
        db.Field('started_at', 'datetime', default=None),
        db.Field('completed_at', 'datetime', default=None),
        db.Field('created_at', 'datetime', default=datetime.utcnow),
        db.Field('updated_at', 'datetime', default=datetime.utcnow,
                 update=datetime.utcnow),
        primarykey=['id'],
        indexes=[['test_id'], ['organization_id'], ['device_id'], ['status'],
                 ['created_at']],
        migrate='test_result'
    )
