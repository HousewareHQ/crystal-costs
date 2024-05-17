import dotenv
dotenv.load_dotenv()

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

from agents.snowflake import SnowflakeAgent
from db.snowflake import Snowflake
from tools.forecasting import predict_values
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


from agents.orchestrator import OrchestratorAgent



st.set_page_config(page_title="CrystalCosts", page_icon="❄️")
st.title("❄️ CrystalCosts")
st.write('Get accurate snowflake cost analysis and forecasting using Natural Language')


@st.cache_resource(ttl='5h')
def get_db():
    if( snowflake_account and snowflake_username and snowflake_password and snowflake_warehouse and snowflake_role):
        # __connection_uri = Snowflake(username=snowflake_username, password=snowflake_password, account=snowflake_account, warehouse=snowflake_warehouse, role=snowflake_role).get_snowflake_connection_url()
        connection_uri = Snowflake().get_snowflake_connection_url()
        db = SQLDatabase.from_uri(connection_uri, sample_rows_in_table_info=1, include_tables=['query_history','warehouse_metering_history'], view_support=True)
        print("DEBUG", db)
        return db


with st.sidebar:
    st.title('Secrets')
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password", value=os.environ.get("OPENAI_API_KEY"))
    snowflake_account= st.text_input("Snowflake Account", key="snowflake_account", value=os.environ.get("SNOWFLAKE_ACCOUNT"))
    snowflake_username= st.text_input("Snowflake Username", key="snowflake_username", value=    os.environ.get("SNOWFLAKE_USERNAME"))
    snowflake_password= st.text_input("Snowflake Password", key="snowflake_password", type="password", value=os.environ.get("SNOWFLAKE_PASSWORD"))
    snowflake_warehouse= st.text_input("Snowflake Warehouse", key="snowflake_warehouse", value=os.environ.get("SNOWFLAKE_WAREHOUSE"))
    snowflake_role= st.text_input("Snowflake Role", key="snowflake_role", value=os.environ.get("SNOWFLAKE_ROLE"))


    
    
    if openai_api_key and snowflake_account and snowflake_username and snowflake_role and snowflake_password and snowflake_warehouse:

        os.environ["SNOWFLAKE_ACCOUNT"] = snowflake_account
        os.environ["SNOWFLAKE_USER"] = snowflake_username
        os.environ["SNOWFLAKE_PASSWORD"] = snowflake_password
        os.environ["SNOWFLAKE_WAREHOUSE"] = snowflake_warehouse
        os.environ["SNOWFLAKE_ROLE"] = snowflake_role
        llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, streaming=True, api_key=openai_api_key)
        parser = PydanticOutputParser(pydantic_object=Response)
        db=get_db()


if "messages" not in st.session_state:
    st.session_state.messages = [AIMessage(type='ai', content="Welcome to CrystalCosts, I can help you with your cost analysis")]




def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

def make_st_component(output):
    try:
        pattern = r'```json\n(.*?)\n```'

        match = re.search(pattern, output, re.DOTALL)

        if match:
            output = match.group(1)

            
        if is_json(output):
                
            parsed_response = json.loads((output))
            columns=set()
            for i in range(0, len(parsed_response['data'])):
                parsed_response['data'][i]= {**parsed_response['data'][i], **parsed_response['data'][i]['yAxis']}
                columns.update(parsed_response['data'][i]['keys'])
                
            st.write(parsed_response['answer'])
        
            columns= list(columns)

            if(len(parsed_response['data'])!=0):
                if parsed_response['chart_type'] == 'line':
                    st.line_chart(parsed_response['data'], x='xAxis',y=columns )
                elif parsed_response['chart_type'] == 'bar':
                    st.bar_chart(parsed_response['data'], x='xAxis',y=columns )
                elif parsed_response['chart_type'] == 'area':
                    st.area_chart(parsed_response['data'], x='xAxis',y=columns )
                else: 
                    st.write("I don't know how to plot this chart")
                st.write(parsed_response['summary'])
        else:
            st.markdown(output)


    except Exception as e:
        st.write(e)


human_assistant_messages={
    'human':'user',
    'ai':'assistant'
}

for message in st.session_state.messages:
    with st.chat_message(human_assistant_messages[message.type]):
        
        if(message.type == "ai"):
            make_st_component(message.content)
        else:
            st.markdown(message.content)




if prompt := st.chat_input("What is my credit consumption in the last 7 days?"):
    
    if not openai_api_key or not snowflake_account or not snowflake_username or not snowflake_password or not snowflake_warehouse or not snowflake_role:
        st.info("Please fill in the secrets")
        st.stop()

    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append(HumanMessage(type='human',content=prompt))

    
    
    with st.chat_message("assistant"):
        container= st.container()
        st_callback = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False, thought_labeler=CustomThoughLabeler())
        response= OrchestratorAgent(llm=llm,parser=parser, db=db).run(prompt,[st_callback],st.session_state.messages)

        output_to_print = response[-1].content      
        
        make_st_component(output_to_print)
        

        
