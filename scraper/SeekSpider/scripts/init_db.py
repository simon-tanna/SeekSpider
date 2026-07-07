"""
Initialize the Seek jobs table in PostgreSQL/Supabase.

The scraper only INSERTs/UPDATEs rows — it assumes the table already exists.
On a fresh database this raises: relation "seek_jobs" does not exist.
This script creates the table (idempotently) with the exact columns the
spider, pipeline, and post-processing utilities read and write.

Usage:
    cd scraper
    python -m SeekSpider.scripts.init_db --dry-run   # print the SQL, change nothing
    python -m SeekSpider.scripts.init_db             # create the table
"""

import argparse
import logging

from SeekSpider.core.config import Config
from SeekSpider.core.database import DatabaseManager


def build_sql(table: str) -> str:
    """Return CREATE TABLE + index DDL for the given table name.

    Column types are chosen to match how the code writes each field:
    - Id .......... integer PK (compared via `= ANY(%s::integer[])`)
    - MinSalary/MaxSalary ... int() in salary_normalizer -> INTEGER
    - PostedDate ... raw Seek `listingDate` string (sometimes "") -> TEXT
    - CreatedAt/UpdatedAt/ExpiryDate ... set via now() -> TIMESTAMPTZ
    - IsActive/IsNew ... boolean flags
    """
    return f'''
        CREATE TABLE IF NOT EXISTS "{table}" (
            "Id"             BIGINT PRIMARY KEY,
            "JobTitle"       TEXT,
            "BusinessName"   TEXT,
            "WorkType"       TEXT,
            "JobType"        TEXT,
            "PayRange"       TEXT,
            "MinSalary"      INTEGER,
            "MaxSalary"      INTEGER,
            "Region"         TEXT,
            "Area"           TEXT,
            "Suburb"         TEXT,
            "JobDescription" TEXT,
            "TechStack"      TEXT,
            "Url"            TEXT,
            "AdvertiserId"   TEXT,
            "PostedDate"     TEXT,
            "IsActive"       BOOLEAN DEFAULT TRUE,
            "IsNew"          BOOLEAN DEFAULT TRUE,
            "CreatedAt"      TIMESTAMPTZ DEFAULT now(),
            "UpdatedAt"      TIMESTAMPTZ DEFAULT now(),
            "ExpiryDate"     TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS "idx_{table}_region"   ON "{table}" ("Region");
        CREATE INDEX IF NOT EXISTS "idx_{table}_isactive" ON "{table}" ("IsActive");
        CREATE INDEX IF NOT EXISTS "idx_{table}_pending_techstack"
            ON "{table}" ("Id") WHERE "TechStack" IS NULL;
    '''


def main():
    parser = argparse.ArgumentParser(description="Create the Seek jobs table")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the SQL without executing it")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("init_db")

    config = Config()
    config.validate()  # ensures POSTGRESQL_* are present
    table = config.POSTGRESQL_TABLE
    sql = build_sql(table)

    if args.dry_run:
        logger.info("Dry run — SQL that would be executed:\n%s", sql)
        return

    db = DatabaseManager(config)
    db.set_logger(logger)
    with db.get_cursor() as cur:
        cur.execute(sql)
    logger.info('Table "%s" is ready (created if it did not exist).', table)


if __name__ == "__main__":
    main()
