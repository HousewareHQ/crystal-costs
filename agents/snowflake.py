
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from db.snowflake import Snowflake
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.prompt import SQL_PREFIX, SQL_FUNCTIONS_SUFFIX
from tools.forecasting import predict_values
from datetime import datetime

class SnowflakeAgent:
    def __init__(self, llm, parser,db):
        self.llm = llm
        __connection_uri = Snowflake().get_snowflake_connection_url()
        # self.db = SQLDatabase.from_uri(__connection_uri)
        # self.db = SQLDatabase.from_uri(__connection_uri, sample_rows_in_table_info=1, include_tables=['query_history','warehouse_metering_history'], view_support=True)
        self.db=db
        self.sql_toolkit = SQLDatabaseToolkit(llm=self.llm, db=self.db)
        self.parser = parser
    
    def __get_tools(self):
        return self.sql_toolkit.get_tools() + [predict_values]

    def get_agent(self):
        tools = self.__get_tools()
        llm_with_tools = self.llm.bind_tools(tools)
        #"To use the predicting tool, you need to remember to: Provide the data at a day level. The date field should be in format YYYY-MM-DD format. CURRENT DATE IS {current_date}"
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                SQL_PREFIX.format(dialect=self.sql_toolkit.dialect, top_k=25) + "To use the predicting tool: Use the existing table to figure out what is the column name of the timestamp and the column needed for prediction. Pass the same to the tool. CURRENT_DATE IS {current_date}\n\n. Here is your chat history: \n\n{messages}"
            ),
            (
                "user",
                """
                The instruction is: {instruction}
                """
            ),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            (
                "system", 
                """MAKE USE OF THE DATABASE SCHEMAS TO UNDERSTAND WHICH TABLE YOU CAN QUERY, YOU SHOULD STRICTLY FOLLOW THE FOLLOWING INSTRUCTIONS TO RETURN A VALID JSON IN THE FORM OF A STRING TO THE USER, DO NOT PROVIDE ANY SUMMARY AT ALL. - {parse_information}"""
            )
        ])

        agent = (
            {"messages":lambda x: x["messages"],
                "instruction": lambda x: x["prompt"],
                "agent_scratchpad": lambda x: format_to_openai_tool_messages(x.get("intermediate_steps", "")),
                "parse_information": lambda x: self.parser.get_format_instructions(),
                "current_date": lambda x: datetime.now().strftime("%Y-%m-%d"),
            }
            | prompt
            | llm_with_tools
            | OpenAIToolsAgentOutputParser()
        )
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
    