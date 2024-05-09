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
import dotenv

from models.custom_decorator import with_streamlit_context
from agents.orchestrator import OrchestratorAgent

dotenv.load_dotenv()



st.set_page_config(page_title="CrystalCosts", page_icon="❄️")
st.title("CrystalCosts")
st.write('Get accurate cost analysis using Natural Language')

if "messages" not in st.session_state:
    st.session_state.messages = [AIMessage(type='ai', content="Welcome to CrystalCosts, I can help you with your cost analysis")]

if "data" not in st.session_state:
    st.session_state.data = []

@st.cache_resource(ttl='5h')
def get_db():
    __connection_uri = Snowflake().get_snowflake_connection_url()
    return SQLDatabase.from_uri(__connection_uri, sample_rows_in_table_info=1, include_tables=['query_history','warehouse_metering_history'], view_support=True)

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, streaming=True)
parser = PydanticOutputParser(pydantic_object=Response)
db=get_db()


def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

def make_st_component(output):
    try:
        pattern = r'```json\n(.*?)\n```'

            # Use regular expression to find the JSON string in the API response
        match = re.search(pattern, output, re.DOTALL)

    # Extract the matched group containing the JSON string
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

with st.sidebar:
    st.title('Chat History')
    
    for data in st.session_state.data:
        with st.expander(f"User: {data['user']}"):
            make_st_component(data['assistant'])

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
   
    st.chat_message("user").markdown(prompt)
    
    st.session_state.messages.append(HumanMessage(type='human',content=prompt))

    
    
    with st.chat_message("assistant"):
        container= st.container()
        st_callback = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False, thought_labeler=CustomThoughLabeler())
        response= OrchestratorAgent(llm=llm,parser=parser, db=db).run(prompt,[st_callback],st.session_state.messages)

        print('\n\n\n\n')
        print('Response\n\n')
        print(response)
        print('\n\n\n\n')
        output_to_print = response[-1].content      
        
        st.session_state.data.append({"user": prompt, "assistant": output_to_print})
        make_st_component(output_to_print)
        

        
