
from agents.conversational_agent import get_snowflake_arctic_results
from agents.snowflake import SnowflakeAgent
from langchain_core.messages import AIMessage


class OrchestratorAgent:
    def __init__(self, llm,parser, db):
        self.snowflake_agent=SnowflakeAgent(llm=llm, parser=parser, db=db).get_agent()

    def run(self, prompt, callbacks, messages):
        conversation_response = get_snowflake_arctic_results(messages)
        
        if "Looking up data for this" in conversation_response:

            snowflake_response=self.snowflake_agent.invoke({
                "prompt": prompt,
                "messages": messages
            }, {
                'callbacks':callbacks
                })

            messages.append(AIMessage(type='ai', content=snowflake_response['output']))
            
        else: 
            messages.append(AIMessage(type="ai", content=conversation_response))
        
        return messages
        
    