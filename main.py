from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

import os


username = os.environ["SNOWFLAKE_USERNAME"]
password = os.environ["SNOWFLAKE_PASSWORD"]
snowflake_account = os.environ["SNOWFLAKE_ACCOUNT"]
database = os.environ["SNOWFLAKE_DATABASE"]
schema = os.environ["SNOWFLAKE_SCHEMA"]
warehouse = os.environ["SNOWFLAKE_WAREHOUSE"]
role = os.environ["SNOWFLAKE_ROLE"]

snowflake_url = f"snowflake://{username}:{password}@{snowflake_account}/{database}/{schema}?warehouse={warehouse}&role={role}"
db = SQLDatabase.from_uri(snowflake_url,sample_rows_in_table_info=1, include_tables=['query_history','warehouse_metering_history'], view_support=True)


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
agent_executor.invoke(
    "How many credits were burned in the last 24 hours?"
)
