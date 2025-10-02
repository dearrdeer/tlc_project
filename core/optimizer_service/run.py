import logging
import time
from dotenv import load_dotenv
from typing import Tuple
from core.optimizer_service.agent import get_qwen3_8b, get_agent
from core.optimizer_service.prompts import (
    ARCHITECT_AI_AGENT_SYSTEM_MESSAGE,
    HUMAN_DDL_AND_MIGRATION_TEMPLATE,
    HUMAN_SQL_QUERY_TEMPLATE,
    VALIDATOR_MESSAGE_ERROR_TEMPLATE,
)
from core.optimizer_service.trino_manager import get_trino, execute_statement_in_trino
from core.optimizer_service.utils import (
    get_catalog_and_schema_from_ddl,
    raw_input_to_model,
    get_ddls_and_migrations_from_raw_output,
)
from core.optimizer_service.pydantic_models import DataOutput, SQL

load_dotenv()

logger = logging.getLogger(__name__)


DDL_CHECK_ITERATIONS_LIMIT = 5
QUERY_ITERATIONS_LIMIT = 3
LOCAL_SCHEMA_NAME = "team320"
LOCAL_CATALOG_NAME = "iceberg"
MAX_CREATED_TABLES = 10
MAX_TABLES_IN_SCHEMA = 7


def drop_schema(trino, catalog: str, schema: str):
    drop_statement = (
        f"DROP SCHEMA IF EXISTS {catalog}.{schema} CASCADE;"  # catalog is replaced to local one inside execute_statement_in_trino
    )
    execute_statement_in_trino(trino, drop_statement)


def run_pipeline(task_id: str, input_json: dict) -> Tuple[bool, DataOutput]:
    # parse input
    data_input = raw_input_to_model(input_json)
    logger.info("Parsed input")
    # get server catalog
    server_additional_data = get_catalog_and_schema_from_ddl(data_input.ddls[0].ddl_script)
    server_catalog_name, server_schema_name = server_additional_data["catalog"], server_additional_data["schema"]
    # recreate data model in local trino
    logger.info("Recreating current tables in local Trino...")
    trino = get_trino(server_catalog_name, LOCAL_CATALOG_NAME)
    # drop schema if exists
    drop_schema(trino, server_catalog_name, server_schema_name)
    # create schema where server ddl will be run
    create_statement = f"CREATE SCHEMA {trino.server_catalog_name}.{server_schema_name};"
    try:
        execute_statement_in_trino(trino, create_statement)
    except Exception as e:
        logger.error(f"Error while processing task {task_id}\n {e}")
        return (False, None)

    # create same tables
    for ddl in data_input.ddls:
        try:
            execute_statement_in_trino(trino, ddl.ddl_script)
        except Exception as e:
            logger.error(f"Bad input in task {task_id}\n {e}")
            return (False, None)

    # we recreated tables in local in order to check migration queries

    # prepare agent
    logger.info("Preparing AI Agent...")
    agent = get_agent(get_qwen3_8b())

    system_msg = ARCHITECT_AI_AGENT_SYSTEM_MESSAGE

    # Part 1: generating ddls and migrations:
    human_msg = HUMAN_DDL_AND_MIGRATION_TEMPLATE.format(
        max_tables=MAX_TABLES_IN_SCHEMA,
        local_schema=LOCAL_SCHEMA_NAME,
        server_schema=server_schema_name,
        catalog=server_catalog_name,
        data_input=data_input,
    )
    init_messages = [system_msg, human_msg]
    messages = init_messages
    ddls = []
    migrations = []

    # leeeets go
    _it = 0
    while _it < DDL_CHECK_ITERATIONS_LIMIT:
        _it += 1
        logger.info(f"Starting iteration {_it} for DDL and Migrations")

        try:
            invoke_result = agent.invoke({"messages": messages})
        except Exception as e:
            logger.error(f"Exception during invoke {e}\n Skip iteration")
            continue

        messages = init_messages + [invoke_result["messages"][-1]]
        raw_content = invoke_result["messages"][-1].content

        if raw_content.strip() == "":
            time.sleep(10)
            messages = init_messages
            continue

        logger.info(f"AI Message:\n {raw_content}")
        if "#END#" not in raw_content:
            continue

        ddls, migrations = get_ddls_and_migrations_from_raw_output(raw_content)

        error_msg = None
        # validate ddls
        logger.info("Start validating ddls")
        drop_schema(trino, server_catalog_name, LOCAL_SCHEMA_NAME)
        for i, ddl in enumerate(ddls):
            validate_check, error = execute_statement_in_trino(trino, ddl.ddl_script)
            if validate_check == -1:
                error_msg = VALIDATOR_MESSAGE_ERROR_TEMPLATE.format(statement=ddl.ddl_script, errors=str(error))
                messages.append(error_msg)
                logger.info(f"Validation error for DDL {i}. Error: {error}")
                break

            logger.info(f"Validated DDL {i}")

        if error_msg:
            continue

        # validate migrations
        logger.info("Start validating migrations")

        for i, mig in enumerate(migrations):
            validate_check, error = execute_statement_in_trino(trino, mig.statement)
            if validate_check == -1:
                error_msg = VALIDATOR_MESSAGE_ERROR_TEMPLATE.format(statement=mig.statement, errors=str(error))
                messages.append(error_msg)
                logger.info(f"Validation error for DDL {i}. Error: {error}")
                break

            logger.info(f"Validated Migration {i}")

        if not error_msg:
            logger.info("All DDLs and Migrations are validated!")
            break

    # Part 2: generating queries
    sqls = []
    for q in data_input.sqls:
        logger.info(f"Optimizing Query with id {q.query_id}")
        human_msg = HUMAN_SQL_QUERY_TEMPLATE.format(new_ddls=ddls, query=q.query)
        init_messages = [system_msg, human_msg]
        messages = init_messages
        _it = 0

        while _it < QUERY_ITERATIONS_LIMIT:
            _it += 1
            logger.info(f"Starting iteration {_it} for Query Generating")

            try:
                invoke_result = agent.invoke({"messages": messages})
            except Exception as e:
                logger.error(f"Exception during invoke {e}\n Skip iteration")
                _it += 1
                continue

            messages = init_messages + [invoke_result["messages"][-1]]
            logger.info(f"AI Message:\n {invoke_result['messages'][-1].content}")

            if invoke_result["messages"][-1].content.strip() == "":
                time.sleep(10)
                messages = init_messages
                continue

            if invoke_result["messages"][-1].content.strip() == "IMPOSSIBLE":
                break

            sql = SQL(query_id=q.query_id, query=invoke_result["messages"][-1].content)
            logger.info(sql.query)
            # validating

            validate_check, error = execute_statement_in_trino(trino, sql.query)
            if validate_check == -1:
                error_msg = VALIDATOR_MESSAGE_ERROR_TEMPLATE.format(statement=sql.query, errors=str(error))
                messages.append(error_msg)
                logger.info(f"Validation error for DDL {i}. Error: {error}")
                continue

            logger.info(f"Validated SQL {q.query_id}")
            sqls.append(sql)
            break

    return True, DataOutput(ddls=ddls, migrations=migrations, sqls=sqls)
