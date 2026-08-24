import sqlite3

from channel_governance.storage import initialize_database


def test_database_schema_is_created(tmp_path) -> None:
    database = tmp_path / "governance.db"
    initialize_database(database)
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert {"evaluation_runs", "evaluation_results"}.issubset(tables)

