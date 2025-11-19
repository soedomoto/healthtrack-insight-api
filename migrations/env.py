"""Alembic environment configuration.

This file contains the configuration for Alembic migrations.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

# Load .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.db.session import Base

# Automatically import all models from app.models package
import importlib
import pkgutil
import app.models

# Dynamically import all modules in app.models to register models with Base.metadata
for importer, modname, ispkg in pkgutil.iter_modules(app.models.__path__):
    if not modname.startswith("_"):
        importlib.import_module(f"app.models.{modname}")

# this is the Alembic Config object, which provides
# the values of the [alembic] section of the .ini file
# as Python variables within this module, represented as a dictionary;
# for example to get the value of some setting named "sqlalchemy.url"
# from the alembic.ini, you would do:
#
# my_setting = config.get_main_option("sqlalchemy.url")
#
# things can get even more advanced here
# if desired; see the documentation for further
# details.

config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically as specified in logging section
# of the file config.ini by referring to
# the "loggers" section (if it exists).
# A similar config is set up by default for you by init_script
# template as well as those in your migrating sqls.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the [alembic] section
# of the alembic.ini file, can be acquired:
# my_test_settings = config.get_section(config.config_ini_section)

# Get database URL from settings
settings = get_settings()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings.DATABASE_URL
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

    """
    configuration = config.get_section(config.config_ini_section) or {}
    # Convert asyncpg to psycopg for synchronous migration
    db_url = settings.DATABASE_URL
    if "asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")
    configuration["sqlalchemy.url"] = db_url
    connectable = engine_from_config(
        configuration,
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
