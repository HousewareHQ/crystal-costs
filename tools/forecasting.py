import pandas as pd
from prophet import Prophet
from langchain.agents import tool
from db.snowflake import Snowflake
import streamlit as st

class ForecastingTool:
    def __init__(self):
        self.prophet = Prophet()
        self.sf = Snowflake(**st.session_state.snowflake_credentials)

    def sf_forecast_call(self, timestamp_column, value_column, warehouse_column, warehouse_name, days):
        return self.sf.sf_forecast_call(timestamp_column, value_column, warehouse_column, warehouse_name, days)

    def forecast_call(self, data, days):
        df = pd.DataFrame(data)
        df["ds"] = pd.to_datetime(df["ds"])
        df["ds"] = df["ds"].dt.strftime("%Y-%m-%d")
        self.prophet.fit(df)
        future = self.prophet.make_future_dataframe(periods=days)
        forecast = self.prophet.predict(future)
        return forecast[["ds", "yhat"]]
    

@tool("predict_values")
def predict_values(timestamp_column, value_column, warehouse_column, warehouse_name, days):
    """
        Use this tool to predict or forecast the next n days value. This tool hits snowflake and makes use of snowflake forecasting the values
        BEFORE USING THIS TOOL, YOU NEED TO CALL THE LIST TABLES AND VIEW SCHEMA OF THE TABLE. DO NOT CALL THIS TOOL FIRST ITSELF.
    """
    return ForecastingTool().sf_forecast_call(timestamp_column, value_column, warehouse_column, warehouse_name, days)



