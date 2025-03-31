from typing import List, Dict, Optional
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
    post_length: str = Field(..., description="Length of the user post user prefers while posting")
    paragraph: str = Field(..., description="Paragraphing and formating of the post")

class Post(BaseModel):
    post_heading: str
    post_content: str

class LinkedInPostGeneration(BaseModel):
    generated_posts: List[Post]

class AnalysedPostKeys(str, Enum):
    WRITING_STYLE = "writing_style"
    PERSONAL_TOUCH = "personal_touch"
    TARGET_AUDIENCE = "target_audience"
    POST_LENGTH = "post_length"
    PARAGRAPHS = "paragraph"

class GeneratedPostKeys(str, Enum):
    POST_HEADING = "post_heading"
    POST_CONTENT = "post_content"

class LinkedInState(BaseModel):
    analysed_post: Dict[AnalysedPostKeys, str] = Field(default_factory=dict)
    generated_post: List[Dict[GeneratedPostKeys, str]] = Field(default_factory=list)

class LinkedinCustomPostRequest(BaseModel):
    length: int = Field(..., description="Length of the post in number of words")
    keywords: List[str] = Field(..., description="Keywords to include in the post")
    tone: str = Field(..., description="Tone of the post")
    post: str = Field(..., description="Content of the post")

class LinkedInPostFlowState(BaseModel):
    linkedin_post: str = ""
    feedback: Optional[str] = None
    valid: bool = False
    generated_post: List[Dict[GeneratedPostKeys, str]] = Field(default_factory=list)

class ValidationResult(BaseModel):
    valid: bool
    feedback: Optional[str] = None