from pathlib import Path

SQL_FILES = Path.cwd().joinpath("schemas").joinpath("sql")
CLICKHOUSE_FILES = Path.cwd().joinpath("schemas").joinpath("clickhouse_sql")


def read_sql_file(object_name: str, clickhouse: bool = False) -> str:
    base_path = SQL_FILES if not clickhouse else CLICKHOUSE_FILES
    with open(base_path.joinpath(f"{object_name}.sql")) as f:
        return f.read()
