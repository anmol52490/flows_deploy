from typing import List, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from typing import Any
class LinkedInPostRequest(BaseModel):
    profile_url: HttpUrl
    static_post: str

class LinkedInPostResponse(BaseModel):
    posts: List[Dict[str, str]]

class LinkedInPostAnalysis(BaseModel):
    writing_style: str
    personal_touch: str
    target_audience: str
    post_length: str
    paragraph: str

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
    length: int
    keywords: List[str]
    tone: str
    post: str

class LinkedInPostFlowState(BaseModel):
    feedback: Optional[str] = None
    valid: bool = False
    generated_post: List[Dict[GeneratedPostKeys, str]] = Field(default_factory=list)

class ValidationResult(BaseModel):
    valid: bool
    feedback: Optional[str]

class RapidAPIResponse(BaseModel):
    data: Dict[str, Any]

class RapidAPIRequest(BaseModel):
    profile_url: str