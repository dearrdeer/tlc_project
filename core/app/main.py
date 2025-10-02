from fastapi import FastAPI, HTTPException
import uuid
import logging

from core.db.models import InputData, NewTaskResponse, StatusResponse, TaskResultResponse
from core.db.database import execute_query

app = FastAPI(title="TLC Project API", description="FastAPI service for TLC project")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/new", response_model=NewTaskResponse)
async def create_new_task(data: InputData):
    """
    Create a new task with the provided flights data.
    Validates JSON payload and stores records in PostgreSQL tables.
    """
    try:
        # Generate UUID4 for taskid
        task_id = str(uuid.uuid4())

        # Insert into tasks table
        task_query = """
            INSERT INTO public.tasks (taskid, url, status) 
            VALUES (:taskid, :url, :status)
        """
        execute_query(task_query, {"taskid": task_id, "url": data.url, "status": "RUNNING"})

        # Insert into ddls table
        for ddl in data.ddl:
            ddl_query = """
                INSERT INTO public.ddls (taskid, statement) 
                VALUES (:taskid, :statement)
            """
            execute_query(ddl_query, {"taskid": task_id, "statement": ddl.statement})

        # Insert into queries table
        for query in data.queries:
            query_insert = """
                INSERT INTO public.queries (queryid, taskid, runquantity, executiontime, query) 
                VALUES (:queryid, :taskid, :runquantity, :executiontime, :query)
            """
            execute_query(
                query_insert,
                {
                    "queryid": query.queryid,
                    "taskid": task_id,
                    "runquantity": query.runquantity,
                    "executiontime": query.executiontime,
                    "query": query.query,
                },
            )

        logger.info(f"Created new task with ID: {task_id}")
        return NewTaskResponse(taskid=task_id)

    except Exception as e:
        logger.error(f"Error creating new task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/status", response_model=StatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a given task.
    """
    try:
        status_query = """
            SELECT taskid, status FROM public.tasks WHERE taskid = :taskid
        """
        result = execute_query(status_query, {"taskid": task_id})

        if not result:
            raise HTTPException(status_code=404, detail="Task not found")

        task_data = result[0]
        return StatusResponse(status=task_data[1])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/getresult", response_model=TaskResultResponse)
async def get_task_result(task_id: str):
    """
    Get the result of a given task.
    Collects DDL statements, migration statements, and queries from the database.
    """
    try:
        # Check if task exists
        task_query = """
            SELECT taskid, status FROM public.tasks WHERE taskid = :taskid
        """
        task_result = execute_query(task_query, {"taskid": task_id})

        if not task_result:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get DDL statements
        ddl_query = """
            SELECT statement FROM public.result_ddls WHERE taskid = :taskid
        """
        ddl_results = execute_query(ddl_query, {"taskid": task_id}) or []
        ddl_list = [{"statement": row[0]} for row in ddl_results]

        # Get migration statements
        migration_query = """
            SELECT statement FROM public.result_migrations WHERE taskid = :taskid
        """
        migration_results = execute_query(migration_query, {"taskid": task_id}) or []
        migration_list = [{"statement": row[0]} for row in migration_results]

        # Get queries
        query_result_query = """
            SELECT queryid, query FROM public.result_queries WHERE taskid = :taskid
        """
        query_results = execute_query(query_result_query, {"taskid": task_id}) or []
        query_list = [{"queryid": row[0], "query": row[1]} for row in query_results]

        # Return the structured response
        return TaskResultResponse(ddl=ddl_list, migrations=migration_list, queries=query_list)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/")
async def root():
    return {"message": "TLC Project API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
