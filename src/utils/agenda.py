from pydantic import Field, BaseModel
from typing import Optional
import os
from pydantic import BaseModel

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
class Resources(BaseModel):
    citations: list[str]
    advice: str

class Subtask(BaseModel):
    description: str
    estimated_minutes: int

class Metric(BaseModel):
    measurement: str
    target_value: Optional[int] = None
    
class Milestone(BaseModel):
    title: str
    description: Optional[str] = None
    expected_completion_date: Optional[str] = Field(None, description="Expected completion date in ISO format (YYYY-MM-DD)")
    estimated_hours: Optional[int] = None
    # resources: Resources = None
    subtasks: Optional[list[Subtask]] = None
    metric: Optional[Metric] = None

class Goal(BaseModel):
    title: str
    description: str
    target_date: str = Field(description="Target date in ISO format (YYYY-MM-DD)")
    estimated_total_hours: int
    milestones: list[Milestone]
