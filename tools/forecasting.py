import pandas as pd
from prophet import Prophet
from langchain.agents import tool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import List

from langchain_core.language_models import BaseLanguageModel
from langchain_core.pydantic_v1 import Field

from langchain_community.agent_toolkits.base import BaseToolkit
from langchain_community.tools import BaseTool
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from langchain_community.utilities.sql_database import SQLDatabase
from db.snowflake import Snowflake


class ForecastingTool:
    def __init__(self):
        self.prophet = Prophet()
        self.sf = Snowflake()

    def sf_forecast_call(self, data, days):
        # self.sf =
        pass

    def forecast_call(self, data, days):
        df = pd.DataFrame(data)
        df["ds"] = pd.to_datetime(df["ds"])
        df["ds"] = df["ds"].dt.strftime("%Y-%m-%d")
        self.prophet.fit(df)
        future = self.prophet.make_future_dataframe(periods=days)
        forecast = self.prophet.predict(future)
        print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())
        return forecast[["ds", "yhat"]]
    
@tool("predict_values")
def predict_values(data, days):
    """Use this tool to predict the values of next n days. data needs to be given in [{'ds': 'value', 'y': value}, {'ds': 'value', 'y': value}, {'ds': 'value', 'y': value}].
    """
    return ForecastingTool().forecast_call(data, days)


# class ForecastingToolKit(SQLDatabaseToolkit):
#     db: SQLDatabase = Field(exclude=True)
#     llm: BaseLanguageModel = Field(exclude=True)

#     def get_tools() -> List[BaseTool]:
#         sql_tools = SQLDatabaseToolkit.get_tools()



