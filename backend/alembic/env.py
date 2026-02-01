from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import our models and config
from app.core.config import settings
from app.models import Base  # This imports all models via __init__.py

# Alembic Config object
config = context.config

# Set up loggers from config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from our settings
# Alembic runs synchronously, so we need to convert async URL to sync
# postgresql+asyncpg:// -> postgresql://
database_url = settings.database_url.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", database_url)

# This is what Alembic uses to detect model changes
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode - generates SQL without connecting."""
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
    """Run migrations in 'online' mode - connects to database and applies changes."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
