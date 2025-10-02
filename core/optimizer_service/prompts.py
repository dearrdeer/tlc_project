from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage

ARCHITECT_AI_AGENT_SYSTEM_MESSAGE = SystemMessage("""
You are Senior Data Engineer with advanced expertise in SQL, Trino, Apache Iceberg, Big Data and Data Modeling.
You are extremely experienced in optimization of Trino SQL requests in Iceberg.
You can easily identify poor design choices in data modeing and can fix them.

Your job will be to help users with optimizing their SQL scripts in Trino.
User's will show you DDLs (Data Definition Language) of the tables in DB, and will provide with list of SQL queries they often run.
""")

HUMAN_DDL_AND_MIGRATION_TEMPLATE = HumanMessagePromptTemplate.from_template(
    """
I have a set of Trino queries that work too long. In the cluser Trino using Iceberg connector and local file system.
I want you to help me recreate schema
with new tables, such that it would be possible to rewrite queries in a much optimized way.

In your output, write ONLY DDLS on new tables, and SQL statements to migrate data to new tables.
Technical requirements:
    1. You first DDL always have to be creation of new schema called "{local_schema}" in the catalog "{catalog}"
    For example "CREATE SCHEMA my_own_catalog.super_cool_name_for_schema"
    2. You are allowed to create only {max_tables} or less tables!
    3. Create only essential tables, that definitely will be use in the optimized SQLs! Do not make additional tables with no use! 
    4. In all your DDLS and migration queries you shold use full path for table: catalog_name.schema_name.table_name
    5. In your migration queries you should read tables from initial schema and write to your new tables in new schema.
    For example "SELECT * FROM {catalog}.{server_schema}.table1"

MAIN REQUIREMENT - It has to be possible to rewrite ALL my queries in a more optimized way using ONLY YOUR NEW TABLES!
This is the most crucial requirement! 

Hint: if you want to use partitioning in the table, you can use parametr 'partitioning'.
Example: 
CREATE TABLE example_table (
    c1 INTEGER,
    c2 DATE,
    c3 DOUBLE
)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['c1', 'c2'],
    sorted_by = ARRAY['c3'],
);

Write down your answer in a following format, without any additional notes (do not forget to add token #END# at the end of the message
if you have finished):
DDLS:
1. CREATE SCHEMA ....;
2. CREATE TABLE catalog.schema.t1 ....;
......
                                    
MIGRATIONS:
1. INSERT INTO catalog.schema.t1 ...;
2. INSERT INTO catalog.schema.t2 ...;
#END#
    
Here are the initial DDLs and queries that I want to optimize:
{data_input}
"""
)

HUMAN_SQL_QUERY_TEMPLATE = HumanMessagePromptTemplate.from_template(
    """
I am trying to migrate my Trino queries to a new schema. I already created new schema and tables in a new schema.
I want you to help me rewrite my query, that I used to run on a previous schema in a most efficient way.

Technical requirements:
    1. Results has to be the same as the result of the original query. THIS IS THE MOST CRUCIAL REQUIREMENT
    2. In your query use full paths to the tables: catalog_name.schema_name.table_name
    3. A single DDL or SQL statement have to be in a single line.

In your output write ONLY full SQL query, without any additional notes or explanations!!!!
If it is impossible to rewrite this SQL using only new tables, then write just one word "IMPOSSIBLE"
    
Here is my set of new tables (Note: in a original schema there were different tables (different data model)):
{new_ddls}

Here is the query I want to rewrite using new schema:
{query}
"""
)

VALIDATOR_MESSAGE_ERROR_TEMPLATE = HumanMessagePromptTemplate.from_template(
    """
I tried to run your query, and failed with errors.
Fix your errors and return your answer in the same format as before, with all SQL statements (even those without error)!

Here is the statement that I tried to run:
{statement}
                                                                            
Here are the descriptions of error:                                                                  
{errors}                                          
"""
)
