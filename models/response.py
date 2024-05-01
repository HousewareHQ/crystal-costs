from typing import List, Dict, Any, Optional

from langchain_core.pydantic_v1 import BaseModel, Field


class TimeSeries(BaseModel):
    xAxis: str = Field(description = "The value that is present on the x Axis of the chart. If it's a 'line' chart it should be the value of - period. The period of the time series data, it should be of the format YYYY-MM-DDTHH:MM:SS")
    # credits_consumed: float = Field(description = "The number of credits consumed in the period for a particular key")
    # key_name: str = Field(description = "The name of the key for which the credits are consumed. This key should be unique and should be used to plot line using the series data ")
    yAxis:Dict[str, float]= Field(description = "The data to be shown on the y Axis of the chart. It can be a dictionary with the key as the name of the key and the value as the number of credits consumed in the period for that key")
    keys:List[str] = Field(description = "The list of keys for which the credits are consumed in the period, this should be the same as the keys in the yAxis dictionary")


class Response(BaseModel):
    """Final response to the question being asked"""
    answer: str = Field(description = "The final answer to respond to the user")
    summary: str = Field(description = "This should be a concise summary of the answer, if the answer is too long, then this should be a summary of the answer")
    data: List[TimeSeries] = Field(description = "If the final answer has a time series data, then it should be formatted here, else this can be empty list")
    chart_type:str = Field(description = "The type of chart to be plotted based on the user input, The values can be 'line', 'bar', 'area'. If the type of chart can't be figured out from the prompt, then this should be 'line' by default")
    error:Optional[str] = Field(description = "If there is an error in the execution, this should be populated with the error message")
