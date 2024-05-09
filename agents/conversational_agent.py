from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_openai import ChatOpenAI

prompt_initial = """
            You are a Cost Monitoring tool for data warehouses like Snowflake, designed to ease the effort of developers. Your primary responsibilities include
            answering users' questions. If the user seems to be asking to get the credits consumed, or the cost of a query, or predicting use of credits, you should
            "Looking up data for this". 
            Remember to exaclty reply with this sentence only - "Looking up data for this". 
            It must be present in your output.
            You have context of previous messages. If user has asked for a summary of the previous message, you don't need to look up data for that.
            If the user is asking a question that does not require looking up data, then simply reply by answering their question based on the context of the messages till now.
        """

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(prompt_initial),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

model = ChatOpenAI(temperature=0, streaming=True, model="gpt-4-turbo")
conversation_runnable = prompt | model