"""Database migration utilities.

Schema management is handled via Alembic (one-time CREATE TABLE) and
penguin-dal (runtime reflection). This module provides migration helpers
for data-only migrations that need to run between schema versions.
"""
import logging
from typing import Optional

from penguin_dal import AsyncDB

logger = logging.getLogger(__name__)


async def validate_schema(db: AsyncDB) -> bool:  # pragma: no cover
    """Validate that all required tables have been reflected.

    Args:
        db: penguin-dal AsyncDB instance (must have reflect() already called).

    Returns:
        True if all required tables are present, False otherwise.
    """
    required_tables = ['users', 'api_keys', 'audit_logs', 'health_checks']
    try:
        for table_name in required_tables:
            if table_name not in db.tables:
                logger.error(f"Required table '{table_name}' not found in reflected schema")
                return False
        logger.info("Schema validation passed")
        return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False
