"""Penguin-DAL database connection manager for runtime operations."""
import logging
from typing import TYPE_CHECKING

from penguin_dal.quart_ext import init_dal, get_db  # noqa: F401 — re-exported for callers

if TYPE_CHECKING:
    from penguin_dal import AsyncDB

logger = logging.getLogger(__name__)


def build_db_uri(config) -> str:
    """Build a SQLAlchemy-compatible database URI from the app config.

    Args:
        config: Configuration object with DB_TYPE, DB_HOST, DB_PORT,
                DB_USER, DB_PASS, DB_NAME.

    Returns:
        SQLAlchemy database URI string.

    Raises:
        ValueError: If DB_TYPE is unsupported.
    """
    db_type = config.DB_TYPE
    if db_type == 'mysql':
        return (
            f"mysql+aiomysql://{config.DB_USER}:{config.DB_PASS}"
            f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
        )
    elif db_type == 'postgres':
        return (
            f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASS}"
            f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
        )
    elif db_type == 'sqlite':
        return f"sqlite+aiosqlite:///{config.DB_NAME}.db"
    else:
        raise ValueError(
            f"Unsupported DB_TYPE: {db_type}. Must be one of: mysql, postgres, sqlite"
        )
