from fastapi import FastAPI, HTTPException
from controller import PostController
from models import LinkedInPostRequest, LinkedInPostResponse, LinkedinCustomPostRequest,RapidAPIResponse,RapidAPIRequest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
controller = PostController()

@app.post("/generate", response_model=LinkedInPostResponse)
def generate_posts(request: LinkedInPostRequest):
    try:
        posts = controller.execute_flow(request)
        return LinkedInPostResponse(posts=posts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/custom_generate", response_model=LinkedInPostResponse)
def custom_generate_posts(request: LinkedinCustomPostRequest):
    try:
        posts = controller.custom_post(request)
        return LinkedInPostResponse(posts=posts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/linkedin_profile_data",response_model=RapidAPIResponse)
def get_linkedin_profile_data(request: RapidAPIRequest):
    try:
        data = controller.get_linkedin_profile_data(request)
        return RapidAPIResponse(data=data)
    except Exception as e:
        logger.error(f"Error fetching LinkedIn profile data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))