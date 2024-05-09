
from agents.conversational_agent import conversation_runnable
from agents.snowflake import SnowflakeAgent
from langchain_core.messages import AIMessage


class OrchestratorAgent:
    def __init__(self, llm,parser, db):
        self.conversation_agent=conversation_runnable
        self.snowflake_agent=SnowflakeAgent(llm=llm, parser=parser, db=db).get_agent()

    def run(self, prompt, callbacks, messages):

        conversation_response=self.conversation_agent.invoke({
            "messages": messages
        })
        
        print('Conversation Response\n\n\n\n')
        print(conversation_response)

        if "Looking up data for this" in conversation_response.content:

            snowflake_response=self.snowflake_agent.invoke({
                "prompt": prompt,
                "messages": messages
            }, {
                'callbacks':callbacks
                })

            messages.append(AIMessage(type='ai', content=snowflake_response['output']))
            
        else: 
            messages.append(conversation_response)
        
        return messages
        
    