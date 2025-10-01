from typing import Tuple
from langchain_core.messages import HumanMessage
from core.optimizer_service.pydantic_models import DataOutput, ExceptionDuringQuery, ExceptionsFromCheck
from core.optimizer_service.prompts import VALIDATOR_MESSAGE_ERROR_TEMPLATE
from core.optimizer_service.trino_manager import TrinoClustersManager, execute_statement_in_trino


def validate(trino: TrinoClustersManager, llm_output: DataOutput) -> Tuple[bool, HumanMessage]:
    exceptions = []

    # ddls
    for ddl in llm_output.ddls:
        validate_check = execute_statement_in_trino(trino, ddl.ddl_script)

        if validate_check[0] == -1:
            exceptions.append(ExceptionDuringQuery(statement=ddl.ddl_script, msg=validate_check[1]))

    # migrations
    for mig in llm_output.migrations:
        validate_check = execute_statement_in_trino(trino, mig.statement)

        if validate_check[0] == -1:
            exceptions.append(ExceptionDuringQuery(statement=mig.statement, msg=validate_check[1]))

    # queries
    for q in llm_output.sqls:
        validate_check = execute_statement_in_trino(trino, q.query)

        if validate_check[0] == -1:
            exceptions.append(ExceptionDuringQuery(statement=q.query, msg=validate_check[1]))

    if len(exceptions) == 0:
        return (True, None)
    else:
        errors = ExceptionsFromCheck(exceptions=exceptions)
        msg = VALIDATOR_MESSAGE_ERROR_TEMPLATE.format(errors=errors)
        return (False, msg)
