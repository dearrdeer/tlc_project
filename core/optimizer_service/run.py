import logging

from typing import Tuple
from core.optimizer_service.agent import get_qwen3_8b, get_agent
from core.optimizer_service.prompts import ARCHITECT_AI_AGENT_SYSTEM_PROMPT_TEMPLATE, HUMAN_INIT_MESSAGE_TEMPLATE
from core.optimizer_service.validator import validate
from core.optimizer_service.trino_manager import get_trino, execute_statement_in_trino
from core.optimizer_service.utils import get_catalog_and_schema_from_ddl, raw_input_to_model, raw_output_to_model
from core.optimizer_service.pydantic_models import DataOutput

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ITERATIONS_LIMIT = 5
LOCAL_SCHEMA_NAME = "team320"


def run_pipeline(task_id: str, input_json: dict) -> Tuple[bool, DataOutput]:
    # parse input
    data_input = raw_input_to_model(input_json)
    logging.info("Parsed input")
    # get server catalog
    server_additional_data = get_catalog_and_schema_from_ddl(data_input.ddls[0].ddl_script)
    server_catalog_name, server_schema_name = server_additional_data["catalog"], server_additional_data["schema"]
    # recreate data model in local trino
    logging.info("Recreating current tables in local Trino...")
    trino = get_trino(server_catalog_name)
    # create schema where server ddl will be run
    statement = f"CREATE SCHEMA {trino.local_catalog_name}.{server_schema_name};"
    try:
        execute_statement_in_trino(trino, statement)
    except Exception as e:
        logging.error(f"Error while processing task {task_id}\n {e}")
        return (False, None)

    # create same tables
    for ddl in data_input.ddls:
        try:
            execute_statement_in_trino(trino, ddl.ddl_script)
        except Exception as e:
            logging.error(f"Bad input in task {task_id}\n {e}")
            return (False, None)

    # we recreated tables in local in order to check migration queries

    # prepare agent
    logging.info("Preparing AI Agent...")
    agent = get_agent(get_qwen3_8b())
    system_msg = ARCHITECT_AI_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
        catalog=trino.local_catalog_name, new_schema_name=LOCAL_SCHEMA_NAME
    )
    human_msg = HUMAN_INIT_MESSAGE_TEMPLATE.format(data_input=data_input)

    messages = [system_msg, human_msg]
    last_solution = None

    # leeeets go
    _it = 0
    while _it < ITERATIONS_LIMIT:
        logger.info(f"Starting iteration {_it}")
        try:
            invoke_result = agent.invoke({"messages": messages})
        except Exception as e:
            logger.error(f"Exception during invoke {e}\n Skip iteration")
            _it += 1

        raw_content = invoke_result["messages"][-1].content
        logger.info(f"AI Message:\n {raw_content}")
        data_output = raw_output_to_model(raw_content)
        last_solution = data_output
        validation_result = validate(trino, data_output)
        logger.info(f"Validation errors:\n {validation_result[1].content}")
        if validation_result[0]:
            return True, last_solution
        else:
            _it += 1
            messages.append(validation_result[1])

    # if we are here
    # then something still does not work properly
    # but we will save it - at least something)

    return True, last_solution
