from pydantic import BaseModel, Field
from typing import List


class DDL(BaseModel):
    """DDL of the single table"""

    ddl_script: str = Field(description="Full CREATE TABLE.... statement that created a table in the user's database")


class SQL(BaseModel):
    """Single SQL query"""

    query_id: str = Field(description="Unique identifier of the query. Is needed to map to a new optimized query")
    query: str = Field(description="A single user's query that user wants to be optimized")


class DataInput(BaseModel):
    catalog: str = Field(description="Catalog name where tables are located")
    catalog_schema: str = Field(description="Schema name where tables are located")
    ddls: List[DDL] = Field(description="DDLs of all tables")
    sqls: List[SQL] = Field(description="All SQL queries of user. Ordered by importance. From the most important to the least")


class Migration(BaseModel):
    statement: str = Field(description="An SQL statement that inserts data to the table")


class DataOutput(BaseModel):
    ddls: List[DDL] = Field(description="Set of DDLS for new tables in the optimized data model")
    migrations: List[Migration] = Field(
        description="Set of SQL statements that migrate data from old schema to a new optimized one"
    )
    sqls: List[SQL] = Field(description="All new optimized variants of the user queries")


class ExceptionDuringQuery(BaseModel):
    """A single exception when checking LLM's queries"""

    statement: str = Field(description="What statement raised an error")
    msg: str = Field(description="Message that describes error")


class ExceptionsFromCheck(BaseModel):
    exceptions: List[ExceptionDuringQuery] = Field(description="All exceptions after running LLM's queries")
