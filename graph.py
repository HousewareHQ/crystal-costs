import json
import operator
import os
import time
from typing import Annotated, Any, Dict, List, Sequence, TypedDict, Union

from dotenv import load_dotenv
from langchain.agents.openai_assistant import OpenAIAssistantRunnable
from langchain_core.messages import BaseMessage, FunctionMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END,  StateGraph


from langchain.output_parsers import PydanticOutputParser
from models.response import Response
from models.custom_thought_labeler import CustomThoughLabeler
from agents.snowflake import SnowflakeAgent
from agents.conversational_agent import conversation_runnable
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,LLMThoughtLabeler
)

load_dotenv()




class AgentState(TypedDict):
  
    prompt: Annotated[BaseMessage, "The user prompt message"]
    messages: Annotated[Sequence[BaseMessage], operator.add]
    container:Any

    

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, streaming=True)
parser = PydanticOutputParser(pydantic_object=Response)

snowflake_agent = SnowflakeAgent(llm=llm, parser=parser ).get_agent()




def should_continue(state):
    messages = state['messages']
    last_message = messages[-1]
    if "Looking up data for this" in last_message.content:
       
        state['prompt_message'] = BaseMessage(type="user", content=last_message.content)
        return "continue"
    else:
        return "end"

def call_model(state):
    messages = state['messages']
    print("\033[33minvoked conversation agent\033[0m\n")
          
    response = conversation_runnable.invoke({
        "messages": messages
    })

    return {"messages": [response]}

def call_snowflake(state):
    
    prompt = state['prompt'].content
    print("\033[33minvoked snowflake agent\033[0m\n")
    
    response = snowflake_agent.invoke({
        "prompt": prompt,
        "messages": state['messages']
    })

    state['messages'].append(AIMessage(type='ai', content=response['output']))

    return {
        'messages': state['messages']
    }


workflow = StateGraph(AgentState)

workflow.add_node("conversation_agent", call_model)
workflow.add_node("snowflake", call_snowflake)


workflow.set_entry_point("conversation_agent")
workflow.add_conditional_edges(
    "conversation_agent",
    should_continue,
    {
        "continue": "snowflake",
        "end": END
    }
)

workflow.add_edge("snowflake", END)

graph_app = workflow.compile()
