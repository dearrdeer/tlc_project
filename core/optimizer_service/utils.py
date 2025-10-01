import re
from urllib.parse import urlparse, parse_qs
from core.optimizer_service.pydantic_models import DataOutput, DDL, SQL, Migration, DataInput


def parse_jdbc_url(jdbc_url: str) -> dict:
    """
    Parse a JDBC URL and extract connection information.

    :param jdbc_url: The JDBC URL string
    :return: A dictionary containing host, port, user, and password
    """
    # Remove the "jdbc:" prefix
    if jdbc_url.startswith("jdbc:"):
        jdbc_url = jdbc_url[5:]

    # Parse the URL
    parsed_url = urlparse(jdbc_url)

    # Extract host and port
    host = parsed_url.hostname
    port = parsed_url.port

    # Parse query parameters
    query_params = parse_qs(parsed_url.query)

    # Extract user and password
    user = query_params.get("user", [None])[0]
    password = query_params.get("password", [None])[0]

    return {"host": host, "port": port, "user": user, "password": password}


def get_catalog_and_schema_from_ddl(ddl: str):
    """
    Extract catalog and schema from a Trino DDL statement.

    :param ddl: The DDL statement string
    :return: A dictionary containing catalog and schema
    """

    # Pattern to match CREATE TABLE catalog.schema.table_name
    pattern = r"CREATE\s+TABLE\s+([^.]+)\.([^.]+)\."
    match = re.search(pattern, ddl, re.IGNORECASE)

    if match:
        catalog = match.group(1)
        schema = match.group(2)
        return {"catalog": catalog, "schema": schema}
    else:
        # If no catalog is specified, assume default structure
        pattern = r"CREATE\s+TABLE\s+([^.]+)\."
        match = re.search(pattern, ddl, re.IGNORECASE)
        if match:
            catalog = None  # No catalog specified
            schema = match.group(1)
            return {"catalog": catalog, "schema": schema}

    # If no match found, return None values
    return {"catalog": None, "schema": None}


def raw_output_to_model(msg_content: str) -> DataOutput:
    """Sorry for this code :("""

    ddls_start = msg_content.find("DDLS:\n") + 6
    migrations_start = msg_content.find("MIGRATIONS:\n") + 12
    queries_start = msg_content.find("QUERIES:\n") + 9

    ddl_rows = msg_content[ddls_start : migrations_start - 12]
    ddls = []

    for row in ddl_rows.split("\n"):
        statement = row[row.find(".") + 1 :].strip()
        if statement == "":
            continue
        ddls.append(DDL(ddl_script=statement))

    migration_rows = msg_content[migrations_start : queries_start - 9]
    migrations = []

    for row in migration_rows.split("\n"):
        statement = row[row.find(".") + 1 :].strip()
        if statement == "":
            continue
        migrations.append(Migration(statement=statement))

    sql_rows = msg_content[queries_start:]
    sqls = []

    for raw_query_row in sql_rows.split(";"):
        if raw_query_row == "":
            continue

        query_id = None
        query = None

        for row in raw_query_row.split("\n"):
            if row == "":
                continue

            if row.find("QUERY_ID:") != -1:
                query_id = row[row.find("QUERY_ID:") + 9 :].strip()
            else:
                query = row[row.find("QUERY:") + 6 :].strip()

        if query_id and query:
            sqls.append(SQL(query_id=query_id, query=query))

    return DataOutput(ddls=ddls, migrations=migrations, sqls=sqls)


def raw_input_to_model(input_json: dict) -> DataOutput:
    ddls = [row["statement"] for row in input_json["ddl"]]
    sqls_w_priority_and_id = [
        (row["queryid"], row["query"], row["runquantity"] * row["executiontime"]) for row in input_json["queries"]
    ]

    sqls = [i for i in sorted(sqls_w_priority_and_id, key=lambda k: -k[2])]

    ddls = [DDL(ddl_script=i) for i in ddls]
    sqls = [SQL(query_id=i[0], query=i[1]) for i in sqls]

    catalog, schema = get_catalog_and_schema_from_ddl(ddls[0].ddl_script)
    return DataInput(catalog=catalog, catalog_schema=schema, ddls=ddls, sqls=sqls)
