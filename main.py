from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)
from langchain.output_parsers import PydanticOutputParser
import os
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import AIMessage, SystemMessage

from models.response import Response


username = os.environ["SNOWFLAKE_USERNAME"]
password = os.environ["SNOWFLAKE_PASSWORD"]
snowflake_account = os.environ["SNOWFLAKE_ACCOUNT"]
database = os.environ["SNOWFLAKE_DATABASE"]
schema = os.environ["SNOWFLAKE_SCHEMA"]
warehouse = os.environ["SNOWFLAKE_WAREHOUSE"]
role = os.environ["SNOWFLAKE_ROLE"]

st.title("CrystalCosts")
st.write('Get accurate cost analysis using Natural Language')

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you today?"}]


snowflake_url = f"snowflake://{username}:{password}@{snowflake_account}/{database}/{schema}?warehouse={warehouse}&role={role}"
db = SQLDatabase.from_uri(snowflake_url,sample_rows_in_table_info=1, include_tables=['query_history','warehouse_metering_history'], view_support=True)


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, streaming=True).with_structured_output(Response, method="json_mode")
parser = PydanticOutputParser(pydantic_object=Response)

# prompt = PromptTemplate(
#     template="""
#     You are an agent designed to interact with a SQL database.
#     Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
#     Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
#     You can order the results by a relevant column to return the most interesting examples in the database.
#     Never query for all the columns from a specific table, only ask for the relevant columns given the question.
#     You have access to tools for interacting with the database.
#     Only use the given tools. Only use the information returned by the tools to construct your final answer.
#     You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

#     DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

#     If the question does not seem related to the database, just return "I don't know" as the answer.

#     {format_instructions}
#     """,
#     input_variables=["input", "dialect", "top_k"],
#     partial_variables={"format_instructions": parser.get_format_instructions()},
#     output_parser=parser
# )
# messages = [
#     SystemMessage(content=cast(str, prefix)),
#     HumanMessagePromptTemplate.from_template("{input}"),
#     AIMessage(content=suffix or SQL_FUNCTIONS_SUFFIX),
#     MessagesPlaceholder(variable_name="agent_scratchpad"),
# ]
# prompt = ChatPromptTemplate.from_messages(messages)

agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)#, suffix=parser.get_format_instructions())



for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("What is up?"):
   
    st.chat_message("user").markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    # response = agent_executor.invoke(prompt)
    
    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent_executor.invoke(
            {"input": prompt}, {"callbacks": [st_callback]}
        )
        
        st.markdown(response['output'])
        print(type(response['output']))
        response['output'] = Response.parse_raw(response['output'])
        print(type(response['output']))
        st.session_state.messages.append({"role": "assistant", "content": response['output']})
        

