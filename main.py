from langchain.agents import create_sql_agent
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,LLMThoughtLabeler
)
from langchain.output_parsers import PydanticOutputParser
import os
import streamlit as st
from models.response import Response
from langchain_community.agent_toolkits import SQLDatabaseToolkit

from langchain_community.agent_toolkits.sql.prompt import (
    SQL_FUNCTIONS_SUFFIX,
)
from models.custom_thought_labeler import CustomThoughLabeler


username = os.environ["SNOWFLAKE_USERNAME"]
password = os.environ["SNOWFLAKE_PASSWORD"]
snowflake_account = os.environ["SNOWFLAKE_ACCOUNT"]
database = os.environ["SNOWFLAKE_DATABASE"]
schema = os.environ["SNOWFLAKE_SCHEMA"]
warehouse = os.environ["SNOWFLAKE_WAREHOUSE"]
role = os.environ["SNOWFLAKE_ROLE"]

st.set_page_config(page_title="CrystalCosts", page_icon="❄️")
st.title("CrystalCosts")
st.write('Get accurate cost analysis using Natural Language')

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you today?"}]


snowflake_url = f"snowflake://{username}:{password}@{snowflake_account}/{database}/{schema}?warehouse={warehouse}&role={role}"

@st.cache_resource(ttl="2h")
def get_db():
    return SQLDatabase.from_uri(snowflake_url,sample_rows_in_table_info=1, include_tables=['query_history','warehouse_metering_history'], view_support=True)

db = get_db()

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, streaming=True)
parser = PydanticOutputParser(pydantic_object=Response)

agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True, suffix=f"{SQL_FUNCTIONS_SUFFIX} YOU SHOULD STRICTLY FOLLOW THE FOLLOWING INSTRUCTIONS TO RETURN A VALID JSON TO THE USER, DO NOT PROVIDE ANY SUMMARY AT ALL. - {parser.get_format_instructions()}")



for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        
        if(message["role"] == "assistant"):
            if "data" in message["content"]:
                st.dataframe(message["content"]["data"])
            else:
                st.markdown(message["content"])
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
   
    st.chat_message("user").markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    
    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False, thought_labeler=CustomThoughLabeler())
        response = agent_executor.invoke(
            {"input": prompt}, {"callbacks": [st_callback]}
        )
        
        if 'data' in response['output'] :
            st.dataframe(response["output"]['data'])
        else:
            st.markdown(response['output'])

        parsed_response = parser.invoke(response['output'])
        st.session_state.messages.append({"role": "assistant", "content": response['output']})
