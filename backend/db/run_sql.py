#!/usr/bin/env python3
"""Run SQL scripts against Oracle XE 21c using python-oracledb Thin mode."""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
import oracledb


def run_sql_file(connection, file_path: Path):
    print(f"Executing: {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split on semicolons or execute statements
    cursor = connection.cursor()
    statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]

    for stmt in statements:
        # Skip SQL*Plus specific commands like COMMIT
        if stmt.upper() == "COMMIT":
            connection.commit()
            continue
        try:
            cursor.execute(stmt)
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            # Ignore table already exists or object already exists if rerunning
            if error_obj.code in (955, 942):  # ORA-00955: name already used, ORA-00942: table does not exist
                print(f"Notice: {error_obj.message.strip()}")
            else:
                print(f"Error executing statement: {stmt[:60]}... -> {error_obj.message}")
                raise

    connection.commit()
    cursor.close()
    print(f"Finished: {file_path.name}")


def main():
    print(f"Connecting to Oracle at {settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME}...")
    try:
        connection = oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE_NAME,
        )
        print("Connected successfully in Thin mode.")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    db_dir = Path(__file__).resolve().parent
    schema_file = db_dir / "001_schema.sql"
    seed_file = db_dir / "002_seed.sql"

    if schema_file.exists():
        run_sql_file(connection, schema_file)
    if seed_file.exists():
        run_sql_file(connection, seed_file)

    connection.close()
    print("Database initialization complete.")


if __name__ == "__main__":
    main()
