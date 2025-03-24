from fastapi import FastAPI, HTTPException
from controller import PostController
from models import LinkedInPostRequest, LinkedInPostResponse
import logging
import signal
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
controller = PostController()

@app.on_event("startup")
async def startup_event():
    signal.signal(signal.SIGINT, lambda *_: sys.exit())

@app.post("/generate", response_model=LinkedInPostResponse)
def generate_posts(request: LinkedInPostRequest):
    try:
        logger.info(f"Received request for profile: {request.profile_url}")
        posts = controller.execute_flow(request)
        return LinkedInPostResponse(posts=posts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
