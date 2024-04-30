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
import json
import re

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

agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True, suffix=f"{SQL_FUNCTIONS_SUFFIX} YOU SHOULD STRICTLY FOLLOW THE FOLLOWING INSTRUCTIONS TO RETURN A VALID JSON IN THE FORM OF A STRING TO THE USER, DO NOT PROVIDE ANY SUMMARY AT ALL. - {parser.get_format_instructions()}")

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

def make_st_component(output):
    pattern = r'```json\n(.*?)\n```'

        # Use regular expression to find the JSON string in the API response
    match = re.search(pattern, output, re.DOTALL)

# Extract the matched group containing the JSON string
    if match:
        output = match.group(1)

        
    if is_json(output):
            
        parsed_response = json.loads((output))
        columns=[]
        for i in range(0, len(parsed_response['data'])):
            parsed_response['data'][i]= {**parsed_response['data'][i], **parsed_response['data'][i]['data']}
            columns= parsed_response['data'][i]['keys']
            
           

        st.line_chart(parsed_response['data'], x='period',y=columns )
        st.write(parsed_response['summary'])
    else:
        st.markdown(output)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        
        if(message["role"] == "assistant"):
            make_st_component(message["content"])
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

        make_st_component(response['output'])

        
        st.session_state.messages.append({"role": "assistant", "content": response['output']})
