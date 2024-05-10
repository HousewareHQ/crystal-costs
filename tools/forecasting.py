import pandas as pd
from prophet import Prophet
from langchain.agents import tool
from db.snowflake import Snowflake


class ForecastingTool:
    def __init__(self):
        self.prophet = Prophet()
        self.sf = Snowflake()

    def sf_forecast_call(self, timestamp_column, value_column, days):
        return self.sf.sf_forecast_call(timestamp_column, value_column, days)

    def forecast_call(self, data, days):
        df = pd.DataFrame(data)
        df["ds"] = pd.to_datetime(df["ds"])
        df["ds"] = df["ds"].dt.strftime("%Y-%m-%d")
        self.prophet.fit(df)
        future = self.prophet.make_future_dataframe(periods=days)
        forecast = self.prophet.predict(future)
        print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())
        return forecast[["ds", "yhat"]]
    
# @tool("predict_values")
# def predict_values(data, days):
#     """Use this tool to predict the values of next n days. data needs to be given in [{'ds': 'value', 'y': value}, {'ds': 'value', 'y': value}, {'ds': 'value', 'y': value}].
#     """
#     return ForecastingTool().forecast_call(data, days)


@tool("predict_values")
def predict_values(timestamp_column, value_column, days):
    """
        Use this tool to predict or forecast the next n days value. This tool hits snowflake and makes use of snowflake forecasting the vlaues
    """
    return ForecastingTool().sf_forecast_call(timestamp_column, value_column, days)



