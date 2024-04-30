from typing import List, Dict, Any, Optional

from langchain_core.pydantic_v1 import BaseModel, Field


class Response(BaseModel):
    """Final response to the question being asked"""
    answer: str = Field(description = "The final answer to respond to the user")
    summary: str = Field(description = "This should be a concise summary of the answer, if the answer is too long, then this should be a summary of the answer")
    data: List[Dict[str, Any]] = Field(description = "If the final answer has a time series data, then it should be formatted here, else this can be empty list")
    error:Optional[str] = Field(description = "If there is an error in the execution, this should be populated with the error message")
    # data: {}[] time series
    # summary: summary of chart
