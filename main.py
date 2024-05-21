from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler
)
from langchain.output_parsers import PydanticOutputParser
import os
import streamlit as st
from models.response import Response
from models.custom_thought_labeler import CustomThoughLabeler
import json
import re
from db.snowflake import Snowflake
from langchain_core.messages import HumanMessage, AIMessage
from agents.orchestrator import OrchestratorAgent
from dotenv import load_dotenv


st.set_page_config(page_title="CrystalCosts", page_icon="❄️", layout='wide')
st.title("❄️ CrystalCosts")
st.write('Get accurate snowflake cost analysis and forecasting using natural language!')

if "suggestion" not in st.session_state:
    st.session_state.suggestion = None


if "messages" not in st.session_state:
    st.session_state.messages = [AIMessage(type='ai', content="Welcome to CrystalCosts, How can I help you today?")]



@st.cache_resource(ttl='5h')
def get_db(account, username, password, warehouse, role):
    if( snowflake_account and snowflake_username and snowflake_password and snowflake_warehouse and snowflake_role):
        connection_uri = Snowflake(account, username, password, warehouse, role).get_snowflake_connection_url()
        db = SQLDatabase.from_uri(connection_uri, sample_rows_in_table_info=1, include_tables=['query_history','warehouse_metering_history'], view_support=True)

        return db


with st.sidebar:
    st.title('Secrets')
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    snowflake_account= st.text_input("Snowflake Account", key="snowflake_account")
    snowflake_username= st.text_input("Snowflake Username", key="snowflake_username")
    snowflake_password= st.text_input("Snowflake Password", key="snowflake_password", type="password")
    snowflake_warehouse= st.text_input("Snowflake Warehouse", key="snowflake_warehouse")
    snowflake_role= st.text_input("Snowflake Role", key="snowflake_role")

    st.info('Note - For using the forecasting tool, please follow the instructions mentioned [here](https://github.com/HousewareHQ/crystal-costs?tab=readme-ov-file#prerequisites)')
    
    if openai_api_key and snowflake_account and snowflake_username and snowflake_role and snowflake_password and snowflake_warehouse:
        st.session_state.snowflake_credentials = {
            "snowflake_account": snowflake_account,
            "snowflake_username": snowflake_username,
            "snowflake_password": snowflake_password,
            "snowflake_warehouse": snowflake_warehouse,
            "snowflake_role": snowflake_role
        }
        llm = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True, api_key=openai_api_key)
        parser = PydanticOutputParser(pydantic_object=Response)
        db=get_db(snowflake_account, snowflake_username, snowflake_password, snowflake_warehouse, snowflake_role)




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

messages_container=st.container()
with messages_container:
    for message in st.session_state.messages:
        with st.chat_message(human_assistant_messages[message.type]):
            if(message.type == "ai"):
                make_st_component(message.content)
            else:
                st.markdown(message.content)



suggestions_container=st.empty()
with suggestions_container:

    with st.container():
        def set_query(suggestion):
            st.session_state.suggestion = suggestion

        st.markdown(f'<p style="height:40vh"></p>', unsafe_allow_html = True)
        suggestions=[
            'Give me a daily trend of credit consumption in last 7 days',
            'Predict the credit consumption for the next 3 days',
            'Compare credit consumption by all warehouses yesterday',
        ]
        
        columns=st.columns(len(suggestions))
        for i, column in enumerate(columns):
            with column:
                st.button(suggestions[i], on_click=set_query, args=[suggestions[i]])
       
        


if prompt := st.chat_input("What's my credit consumption today?") or st.session_state.suggestion is not None:

    user_query=st.session_state.suggestion if st.session_state.suggestion else prompt
  
    
    if not openai_api_key or not snowflake_account or not snowflake_username or not snowflake_password or not snowflake_warehouse or not snowflake_role:
        messages_container.info("Please fill in the secrets")
        st.stop()

    suggestions_container.empty()
    st.session_state.suggestion = None

    messages_container.chat_message("user").markdown(user_query)
    st.session_state.messages.append(HumanMessage(type='human',content=user_query))

    with messages_container:
        with st.chat_message("assistant"):
            st_callback = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False, thought_labeler=CustomThoughLabeler())
            response= OrchestratorAgent(llm=llm,parser=parser, db=db, sf=Snowflake(**st.session_state.snowflake_credentials)).run(prompt,[st_callback],st.session_state.messages)

            output_to_print = response[-1].content      
            
            
            make_st_component(output_to_print)
            

        
