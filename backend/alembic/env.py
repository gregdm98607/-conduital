"""
Alembic environment configuration

Includes optional migration integrity validation hooks.
Set ALEMBIC_SKIP_VALIDATION=1 to skip validation during migrations.
"""

import logging
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import all models to ensure they're registered with SQLAlchemy
from app.core.config import settings
from app.models import (
    ActivityLog,
    Area,
    Base,
    Context,
    Goal,
    InboxItem,
    PhaseTemplate,
    Project,
    ProjectPhase,
    SyncState,
    Task,
    Vision,
)

logger = logging.getLogger("alembic.env")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def should_skip_validation() -> bool:
    """Check if validation should be skipped."""
    return os.environ.get("ALEMBIC_SKIP_VALIDATION", "").lower() in ("1", "true", "yes")


def run_pre_migration_validation(connection) -> bool:
    """Run pre-migration validation checks.

    Returns True if validation passes or is skipped.
    """
    if should_skip_validation():
        logger.info("Skipping pre-migration validation (ALEMBIC_SKIP_VALIDATION set)")
        return True

    try:
        from sqlalchemy import create_engine
        from app.migrations.chain import validate_chain

        # Validate migration chain
        chain_result = validate_chain()
        if not chain_result.is_valid:
            logger.warning("Migration chain issues detected:")
            for error in chain_result.errors:
                logger.warning(f"  - {error}")
            # Don't block on chain issues, just warn
        else:
            logger.info("Pre-migration validation: chain OK")

        return True

    except ImportError:
        # Migration utilities not yet installed
        logger.debug("Migration utilities not available, skipping validation")
        return True
    except Exception as e:
        logger.warning(f"Pre-migration validation error: {e}")
        return True  # Don't block migrations on validation errors


def run_post_migration_validation(connection) -> bool:
    """Run post-migration validation checks.

    Returns True if validation passes or is skipped.
    """
    if should_skip_validation():
        return True

    try:
        from sqlalchemy import create_engine
        from app.migrations.integrity import run_all_checks

        # Create engine from connection for integrity checks
        engine = connection.engine

        report = run_all_checks(engine)
        if report.is_healthy:
            logger.info("Post-migration validation: data integrity OK")
        else:
            logger.warning(f"Post-migration validation: {report.error_count} errors, {report.warning_count} warnings")
            for issue in report.issues:
                logger.warning(f"  - {issue.table}.{issue.column}: {issue.message}")

        return True

    except ImportError:
        logger.debug("Migration utilities not available, skipping validation")
        return True
    except Exception as e:
        logger.warning(f"Post-migration validation error: {e}")
        return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Includes pre/post migration validation hooks.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        # Pre-migration validation
        run_pre_migration_validation(connection)

        with context.begin_transaction():
            context.run_migrations()

        # Post-migration validation
        run_post_migration_validation(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
