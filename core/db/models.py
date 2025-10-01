from pydantic import BaseModel
from typing import List


# Pydantic models for JSON payload validation
class DDLStatement(BaseModel):
    statement: str


class Query(BaseModel):
    queryid: str
    query: str
    runquantity: int
    executiontime: int


class InputData(BaseModel):
    url: str
    ddl: List[DDLStatement]
    queries: List[Query]


# Database models for SQLAlchemy
class TaskDB(BaseModel):
    taskid: str
    url: str
    status: str  # 'RUNNING', 'DONE', 'FAILED'

    class Config:
        from_attributes = True


class DDLDB(BaseModel):
    taskid: str
    statement: str

    class Config:
        from_attributes = True


class QueryDB(BaseModel):
    queryid: str
    taskid: str
    runquantity: int
    executiontime: int
    query: str

    class Config:
        from_attributes = True


# Response models
class NewTaskResponse(BaseModel):
    taskid: str


class StatusResponse(BaseModel):
    taskid: str
    status: str
