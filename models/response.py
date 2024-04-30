from typing import List, Dict, Any

from langchain_core.pydantic_v1 import BaseModel, Field


class Response(BaseModel):
    """Final response to the question being asked"""
    answer: str = Field(description = "The final answer to respond to the user")
    summary: str = Field(description = "This should be a concise summary based on the time-series data")
    data: List[Dict[str, Any]] = Field(description = "If the final answer has a time series data, then it should be formatted here, else this can be empty list")
