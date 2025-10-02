import logging
import json
import time

from core.db.database import execute_query
from core.optimizer_service.run import run_pipeline, DataOutput

SLEEP_TIME = 5

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def get_next_task():
    query = """
        SELECT taskid
        FROM public.tasks
        WHERE status = 'RUNNING'
        LIMIT 1
    """
    result = execute_query(query)
    if result:
        return result[0][0]  # Return the first task ID
    return None


def get_json_by_task(task_id: str):
    # Get task information (URL)
    task_query = """
        SELECT url
        FROM public.tasks
        WHERE taskid = :taskid
    """
    task_result = execute_query(task_query, {"taskid": task_id})

    if not task_result:
        return {}

    url = task_result[0][0]

    # Get DDL statements
    ddl_query = """
        SELECT statement
        FROM public.ddls
        WHERE taskid = :taskid
    """
    ddl_results = execute_query(ddl_query, {"taskid": task_id})
    ddl_list = [{"statement": row[0]} for row in ddl_results] if ddl_results else []

    # Get queries
    queries_query = """
        SELECT queryid, query, runquantity, executiontime
        FROM public.queries
        WHERE taskid = :taskid
    """
    queries_results = execute_query(queries_query, {"taskid": task_id})
    queries_list = []

    if queries_results:
        for row in queries_results:
            query_obj = {
                "queryid": row[0],
                "query": row[1],
                "runquantity": row[2] if row[2] is not None else 0,
                "executiontime": row[3] if row[3] is not None else 0,
            }
            queries_list.append(query_obj)

    # Construct the final JSON object
    data = {"url": url, "ddl": ddl_list, "queries": queries_list}

    return data


def save_result(task_id: str, data: DataOutput):
    # Insert into result ddls table
    for ddl in data.ddls:
        task_query = """
                INSERT INTO public.result_ddls (taskid, statement) 
                VALUES (:taskid, :statement)
            """
        execute_query(task_query, {"taskid": task_id, "statement": ddl.ddl_script})

    # Insert into result migrations table
    for mig in data.migrations:
        task_query = """
                INSERT INTO public.result_migrations (taskid, statement) 
                VALUES (:taskid, :statement)
            """
        execute_query(task_query, {"taskid": task_id, "statement": mig.statement})

    # Insert into result sqls table
    for sql in data.sqls:
        task_query = """
                INSERT INTO public.result_queries (taskid, queryid, query) 
                VALUES (:taskid, :queryid, :query)
            """
        execute_query(task_query, {"taskid": task_id, "queryid": sql.query_id, "query": sql.query})

    # make task status DONE
    task_query = """
            UPDATE public.tasks
            SET status = 'DONE'
            WHERE taskid = :taskid
        """
    execute_query(task_query, {"taskid": task_id})


def fail_task(task_id: str):
    task_query = """
        UPDATE public.tasks
        SET status = 'FAILED'
        WHERE taskid = :taskid
    """
    execute_query(task_query, {"taskid": task_id})


def main():
    while True:
        logger.info("Choosing next task...")
        task_id = get_next_task()
        if not task_id:
            logger.info(f"No new tasks in DB. Sleeping for {SLEEP_TIME}")
            time.sleep(SLEEP_TIME)
            continue

        logger.info(f"Next task id {task_id}")
        logger.info(f"Getting JSON for task {task_id}")

        input_json = get_json_by_task(task_id)
        logger.info("Running pipeline...")

        is_success, data_output = run_pipeline(task_id, input_json)
        if is_success:
            logger.info(f"Successful optimization of task {task_id}")
            logger.info("Saving the results")
            save_result(task_id, data_output)
        else:
            logger.info("Optimization failed. Skipping the task")
            fail_task(task_id)


if __name__ == "__main__":
    main()
