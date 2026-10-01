import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add parent dir to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import SQLModel
from app.config import settings

config = context.config
# Honour an explicit override (alembic -x url=... or $ALEMBIC_DATABASE_URL)
# for migrations against a copy/staging database. Without this, env.py always
# used the live DSN, so it was impossible to rehearse an upgrade anywhere but
# production -- an early version of this change silently pointed a `stamp
# --purge` at the real database.
_url_override = os.environ.get("ALEMBIC_DATABASE_URL") or (
    (context.get_x_argument(as_dictionary=True) or {}).get("url")
)
if _url_override:
    config.set_main_option("sqlalchemy.url", _url_override)
elif not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Revision-id width: every pre-existing database has
            # alembic_version.version_num as VARCHAR(32), because the table
            # came from a non-alembic path. Alembic's own default here is
            # VARCHAR(255) and it never reads the column width (only
            # `SELECT version_num`), so existing 32-wide tables keep working
            # without an ALTER. Two consequences to keep in mind:
            #   * a merge revision writes comma-joined parents (here 44
            #     chars), which will NOT fit a 32-wide column -- stamp such a
            #     database with the leaf head only, not the merge point;
            #   * databases created by alembic itself get the 255-wide column.
            # If this ever needs enforcing, override version_table_impl
            # (alembic.runtime.migration.MigrationContext passes
            # version_table/version_table_pk through opts); there is no
            # `version_num_chars` option.
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
