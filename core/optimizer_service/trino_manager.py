from trino.auth import BasicAuthentication
import trino
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class TrinoClustersManager:
    def __init__(
        self,
        local_trino_connection: trino.dbapi.Connection,
        server_trino_connection: Optional[trino.dbapi.Connection],
        local_catalog_name: Optional[str],
        server_catalog_name: Optional[str],
    ):
        self.local_trino_connection = local_trino_connection
        self.server_trino_connection = server_trino_connection
        self.server_catalog_name = server_catalog_name
        self.local_catalog_name = local_catalog_name

    def get_local_conn(self) -> trino.dbapi.Connection:
        return self.local_trino_connection

    def get_server_conn(self) -> trino.dbapi.Connection:
        return self.server_trino_connection


def get_trino(server_catalog_name, local_catalog_name):
    local_host_name = os.getenv("TRINO_HOST", "trino")
    local_port_name = int(os.getenv("TRINO_PORT", "8081"))
    local_catalog_name = local_catalog_name

    conn = trino.dbapi.trino.dbapi.connect(
        host=local_host_name,
        port=local_port_name,
        catalog=local_catalog_name,
        auth=BasicAuthentication("user", ""),
    )
    return TrinoClustersManager(conn, None, local_catalog_name, server_catalog_name)


def execute_statement_in_trino(trino: TrinoClustersManager, statement: str):
    # replace server catalog name with local name
    exec_statement = statement.replace(f"{trino.server_catalog_name}.", f"{trino.local_catalog_name}.")
    cursor = trino.get_local_conn().cursor()
    try:
        cursor.execute(exec_statement.replace(";", ""))
        return (0, "")
    except Exception as e:
        print(e)
        return (-1, e)
