from pydantic import Field, BaseModel
from typing import Optional
from datetime import datetime, timezone
from openai import OpenAI
from sqlmodel import SQLModel
from pydantic import BaseModel
import os

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

def populate(query):

    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {"role": "system", "content": "You are an administator populating a database. You will be given a query describing a goal and you will stucture it appropraitely into milestones, subtasks and metrics"},
            {
                "role": "user",
                "content": f"{query}",
            },
        ],
        text_format=Goal,
    )

    return response
 

advice = "## Steps to Achieve the Goal of Becoming a Michelin Chef\n\nBecoming a Michelin-star chef is a challenging and prestigious goal that requires dedication and extensive training. While Michelin stars are awarded to restaurants, not chefs, success in this field means leading a restaurant to achieve these stars. Here are the steps to help you on this journey:\n\n### 1. Obtain a Culinary Education\n- **Formal Training**: Enroll in a leading culinary school to gain foundational skills in cooking techniques, ingredient sourcing, and presentation. This education is crucial for understanding the industry and developing essential skills[1][2].\n- **Practical Experience**: During your education, participate in internships or work-study programs to gain hands-on experience in professional kitchens[2].\n\n### 2. Develop Advanced Culinary Skills\n- **Master Various Techniques**: Learn advanced cooking methods like molecular gastronomy, sous-vide cooking, and fermentation. These skills are essential for innovative and high-quality cooking[5].\n- **Experimentation**: Regularly experiment with new ingredients, flavor combinations, and presentation styles to develop your unique culinary style[5].\n\n### 3. Gain Experience in Fine Dining\n- **Work in Michelin-Starred Restaurants**: Strive to work in restaurants that already hold Michelin stars. This experience will expose you to the standards and expectations of Michelin-level cooking[1].\n- **Leadership Roles**: As you gain experience, aim for leadership positions, such as sous chef or executive chef, to develop your management and creative skills[1].\n\n### 4. Understand the Criteria for Michelin Stars\n- **Quality Ingredients**: Use only the highest quality ingredients available, focusing on freshness and seasonal availability[3].\n- **Culinary Technique**: Master a range of cooking techniques and ensure consistency in food preparation[3].\n- **Value for Money**: Ensure that your dishes offer excellent value for the price, considering both quality and cost[5].\n\n### 5. Stay Innovative and Adaptable\n- **Innovate Continuously**: Stay abreast of culinary trends and innovate by improving classic dishes or creating new ones[5].\n- **Stay Flexible**: Be open to feedback and willing to adjust your menu and techniques based on reviews and customer feedback[5].\n\n### 6. Build a Strong Team\n- **Collaboration**: Foster a collaborative environment in your kitchen where creativity and innovation are encouraged[1].\n- **Mentorship**: Seek mentorship from experienced chefs to guide you through your career[1].\n\n### 7. Location and Market Awareness\n- **Restaurant Location**: Ensure your restaurant is located in an area covered by the Michelin Guide[4].\n- **Market Awareness**: Understand local culinary trends and consumer preferences to tailor your offerings accordingly[4].\n\nBy following these steps and persisting through challenges, you can increase your chances of leading a restaurant to Michelin-star success."

if __name__ == "__main__":
    
    output = populate(advice)
    print(output)
