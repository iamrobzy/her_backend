from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, Field


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
    expected_completion_date: Optional[str] = Field(
        None, description="Expected completion date in ISO format (YYYY-MM-DD)"
    )
    estimated_hours: Optional[int] = None
    subtasks: Optional[list[Subtask]] = None
    metric: Optional[Metric] = None


class Goal(BaseModel):
    title: str
    description: str
    target_date: str = Field(
        description="Target date in ISO format (YYYY-MM-DD)"
    )
    estimated_total_hours: int
    milestones: list[Milestone]


def populate(query, OPENAI_API_KEY):
    print(f"Starting populate function with query of length: {len(query)}")

    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is empty or None")
        raise ValueError("OpenAI API key is required")

    print("Initializing OpenAI client")
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        print("Sending request to OpenAI for response parsing")
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an administator populating a database. "
                        "You will be given a query describing a goal and "
                        "you will stucture it appropraitely into milestones, "
                        "subtasks and metrics"
                    ),
                },
                {
                    "role": "user",
                    "content": f"{query}",
                },
            ],
            text_format=Goal,
        )
        print("Successfully received and parsed response into Goal format")
        print(f"Generated goal with title: {response}")

        return response
    except Exception as e:
        print(f"Error in populate function: {str(e)}")
        import traceback

        traceback.print_exc()
        raise


# Long advice string moved to separate file or shortened for linting purposes
advice = """
## Steps to Achieve the Goal of Becoming a Michelin Chef

Becoming a Michelin-star chef requires dedication and extensive training.
Here are the key steps:

1. Obtain a Culinary Education
2. Develop Advanced Culinary Skills
3. Gain Experience in Fine Dining
4. Understand the Criteria for Michelin Stars
5. Stay Innovative and Adaptable
6. Build a Strong Team
7. Choose the Right Location and Understand the Market
"""

if __name__ == "__main__":

    output = populate(advice)
    print(output)
