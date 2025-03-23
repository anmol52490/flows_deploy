# # from pydantic import BaseModel, HttpUrl
# # from typing import List, Optional, Dict, Any, Union


# # class LinkedInPostFlowState(BaseModel):
# #     linkedin_post: str = ""
# #     feedback: Optional[str] = None
# #     valid: Optional[bool] = False
# #     retry_count: int = 0
# #     retry_count_analysis: Optional[int] = 0 
# #     activities: Optional[List[Dict[str, Any]]] = []
# #     user_preferences: Dict[str, str] = {}
# #     analysis_report: Optional[str] = None
    




# # class LinkedInPostFlowState1(BaseModel):
# #     linkedin_post: str = ""
# #     feedback: str = None
# #     valid: bool = False
# #     retry_count: int = 0
# #     activities: Optional[List[Dict]] = []
# #     user_preferences: Optional[Dict] = {}

# from pydantic import BaseModel, Field, HttpUrl
# from typing import List, Dict, Union
# from enum import Enum


# class LinkedInPostResponse(BaseModel):
#     posts: List[Dict[str, str]]
#     #feedback: Optional[str]
#     #retry_count: int
#     #status: str

# class LinkedInPostRequest(BaseModel):
#     profile_url: HttpUrl

# class PostAnalysisOutput(BaseModel):
#     theme: str = Field("General Professionalism", description="The central theme derived from the user's LinkedIn profile.")
#     writing_style: str = Field("Formal and Informative", description="The writing style the user typically employs in their posts.")
#     interests: str = Field("Technology, Leadership", description="Key interests and topics the user frequently discusses.")
#     career_goals: str = Field("Executive Leadership", description="Long-term career aspirations identified from the user's profile.")
#     interaction_style: str = Field("Engaging and Responsive", description="How the user typically interacts with their LinkedIn network.")
#     values: str = Field("Integrity, Innovation", description="Core values evident in the user's professional activities.")
#     personal_touch: str = Field("Personal anecdotes", description="Personal elements the user likes to include in their posts.")
#     target_audience: str = Field("Industry Professionals", description="The primary audience the user targets with their posts.")
#     area_of_expertise: str = Field("Technology, Business Strategy", description="The user's primary area of expertise.")
#     area_of_improvement: str = Field("Engagement with followers", description="An area where the user could improve their LinkedIn presence.")

# class LinkedInPost(BaseModel):
#     post_heading: str = Field(..., description="The title or heading of the LinkedIn post.")
#     post_content: str = Field(..., description="The main content of the LinkedIn post, adhering to character limits and content guidelines.")

# class PostGenerationOutput(BaseModel):
#     posts: List[LinkedInPost] = Field(..., description="A list of LinkedIn posts, each structured according to the specified guidelines and content requirements.")

# class GeneratedPostKeys(str, Enum):
#     POST_HEADING = "post_heading"
#     POST_CONTENT = "post_content"

# class AnalysedPostKeys(str, Enum):
#     THEME = "theme"
#     WRITING_STYLE = "writing_style"
#     INTERESTS = "interests"
#     CAREER_GOALS = "career_goals"
#     INTERACTION_STYLE = "interaction_style"
#     VALUES = "values"
#     PERSONAL_TOUCH = "personal_touch"
#     TARGET_AUDIENCE = "target_audience"
#     AREA_OF_EXPERTISE = "area_of_expertise"
#     AREA_OF_IMPROVEMENT = "area_of_improvement"

# class linkedinPostFlowState(BaseModel):
#     hidevs: str = (
#         "Hidevs is a platform which has a vision to help people in their professional journey. "
#         "We aim to provide a platform where people can learn, grow and share their knowledge. "
#     )
#     analysed_post: Dict[AnalysedPostKeys, str] = Field(
#         description="Dictionary of analysed post attributes",
#         default_factory=dict,
#         example={"theme": "AI", "writing_style": "professional", "interests": "machine learning"}
#     )
#     generated_post: List[Dict[GeneratedPostKeys, str]] = Field(
#         description="List of generated posts containing: post_heading, post_content",
#         default_factory=list,
#         example=[{"post_heading": "AI Trends", "post_content": "Recent developments in..."},
#                  {"post_heading": "Data Science", "post_content": "The future of data science..."}]
#     )

from typing import List, Dict, Union
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum



class LinkedInPostRequest(BaseModel):
    profile_url: HttpUrl
    static_post: str = Field(..., description="Static post content")

class LinkedInPostResponse(BaseModel):
    posts: List[Dict[str, str]]


class LinkedInPostAnalysis(BaseModel):
    writing_style: str = Field(..., description="Detected writing style")
    personal_touch: str = Field(..., description="Personal touch in the post")
    target_audience: str = Field(..., description="Target audience for the post")
class Post(BaseModel):
    post_heading: str = Field(..., description="Title/headline of the post")
    post_content: str = Field(..., description="Full text content of the post")

# List of dicts for post generation
class LinkedInPostGeneration(BaseModel):
    generated_posts: List[Post] = Field(
        ...,
        description="List of generated posts as dictionaries"
    )



class AnalysedPostKeys(str, Enum):
    WRITING_STYLE = "writing_style"
    PERSONAL_TOUCH = "personal_touch"
    TARGET_AUDIENCE = "target_audience"

class GeneratedPostKeys(str, Enum):
    POST_HEADING = "post_heading"
    POST_CONTENT = "post_content"

class EvaluatedPostKeys(str, Enum):
    FEEDBACK = "feedback"
    VALID = "valid"

class LinkedInState(BaseModel):
    analysed_post: Dict[AnalysedPostKeys, str] = Field(
        description="Dictionary of analysed post attributes",
        default_factory=dict,
    )
    
    generated_post: List[Dict[GeneratedPostKeys, str]]= Field(
        description="Generated post containing: post_content",
        default_factory=list,
    )