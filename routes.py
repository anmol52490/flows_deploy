from fastapi import FastAPI, HTTPException
from controller import PostController
from models import LinkedInPostRequest, LinkedInPostResponse
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()
controller = PostController()

def receive_signal(signalNumber, frame):
    print('Received:', signalNumber)
    sys.exit()


@app.on_event("startup")
async def startup_event():
    import signal
    signal.signal(signal.SIGINT, receive_signal)
    # startup tasks

@app.post("/generate", response_model=LinkedInPostResponse)
def generate_posts(request: LinkedInPostRequest):
    logger.info(f"🚀 Received request for profile: {request.profile_url}")
    try:
        logger.info("🔄 Starting LinkedIn post generation flow")
        posts = controller.execute_flow(request)
        
        return LinkedInPostResponse(posts=posts)
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.critical(f"💥 Critical error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))