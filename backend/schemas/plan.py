from pydantic import BaseModel
from typing import List

class PlanRequest(BaseModel):
    user_context: str = "I am ready for the day."

class PlanResponse(BaseModel):
    date: str
    focus: str
    tasks: List[str]
    message: str