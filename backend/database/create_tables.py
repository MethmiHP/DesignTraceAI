from sqlalchemy import inspect, text

from database.connection import Base, engine
import database.models


def main():
    print("Connecting to Neon PostgreSQL...")

    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        print(f"Connected to database: {database_name}")

    # Creates only tables that do not already exist.
    # Does not modify existing table definitions.
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    expected_tables = [
        "projects",
        "workflow_runs",
        "module_executions",
        "artifact_versions",
        "review_decisions",
        "workflow_events",
    ]

    existing_tables = inspector.get_table_names()

    print("\nCoordinator database tables:")

    for table in expected_tables:
        if table in existing_tables:
            print(f"  OK: {table}")
        else:
            raise RuntimeError(
                f"Table was not created: {table}"
            )

    print("\nSUCCESS: All six tables exist in Neon!")


if __name__ == "__main__":
    main()
