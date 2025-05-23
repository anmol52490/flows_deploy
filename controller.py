import re
import requests
import logging
from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow import Flow, listen, start, router
from models import (
    LinkedInPostRequest, LinkedInPostAnalysis, LinkedInPostGeneration, LinkedInState,
    LinkedinCustomPostRequest, LinkedInPostFlowState, ValidationResult,RapidAPIRequest
)
from utils import load_yaml_config, get_env, clean_text

AGENTS = load_yaml_config("config/agents.yaml")
TASKS = load_yaml_config("config/tasks.yaml")
logger = logging.getLogger(__name__)


class LinkedinPostFlow(Flow[LinkedInState]):
    def __init__(self, request: LinkedInPostRequest):
        super().__init__(state=LinkedInState())
        self.request = request
        self.static_post = request.static_post
        self.rapidapi_key = get_env("RAPIDAPI_KEY")
        self.llm = LLM(
            model="gemini/gemini-2.0-flash-lite",
            temperature=0.35,
            api_key=get_env("GEMINI_API_KEY")
        )
        self.cached_activities = None

    def _extract_username(self):
        match = re.search(r"https://www\.linkedin\.com/in/([^/]+)", str(self.request.profile_url))
        if not match:
            raise ValueError("Invalid LinkedIn URL format")
        return match.group(1)

    def _fetch_activities(self):
        username = self._extract_username()
        response = requests.get(
            "https://linkedin-api8.p.rapidapi.com/get-profile-posts",
            headers={
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": "linkedin-api8.p.rapidapi.com"
            },
            params={"username": username}
        )
        if response.status_code != 200:
            raise ConnectionError("Failed to fetch LinkedIn activities")

        raw_data = response.json().get("data") or []
        self.cached_activities = [
            {
                "text": clean_text(post.get("text", "")),
                "totalReactionCount": post.get("totalReactionCount", 0),
                "commentsCount": post.get("commentsCount", 0)
            }
            for post in sorted(raw_data, key=lambda x: x.get("postedDate", 0), reverse=True)[:5]
        ]

    @start()
    def analysis_phase(self):
        if not self.cached_activities:
            raise RuntimeError("LinkedIn activities not loaded")

        agent = Agent(**AGENTS["linkedin_post_analysis_agent"], llm=self.llm)
        task = Task(config=TASKS["trend_analysis_task"], agent=agent, output_json=LinkedInPostAnalysis)
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

        result = crew.kickoff(inputs={"activities": self.cached_activities})
        self.state.analysed_post = {
            "writing_style": result["writing_style"],
            "personal_touch": result["personal_touch"],
            "target_audience": result["target_audience"],
            "post_length": result["post_length"],
            "paragraph": result["paragraph"]
        }

    @listen(analysis_phase)
    def generation_phase(self):
        agent = Agent(**AGENTS["post_generation_agent"], llm=self.llm)
        task = Task(config=TASKS["post_generation_task"], agent=agent, output_json=LinkedInPostGeneration)
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

        result = crew.kickoff(inputs={
            "static_linkedin_post": self.static_post,
            **self.state.analysed_post
        })

        self.state.generated_post = result["generated_posts"]


class LinkedInCustomPostFlow(Flow[LinkedInPostFlowState]):
    def __init__(self, request: LinkedinCustomPostRequest):
        super().__init__(state=LinkedInPostFlowState())
        self.llm = LLM(
            model="gemini/gemini-2.0-flash-lite",
            temperature=0.35,
            api_key=get_env("GEMINI_API_KEY")
        )
        self.request = request
        self.retry_count = 0

    @start()
    def generate_linkedin_post(self):
        agent = Agent(**AGENTS["linkedin_post_enhancer"], llm=self.llm)
        task = Task(config=TASKS["post_enhancement_task"], agent=agent, output_json=LinkedInPostGeneration)
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

        result = crew.kickoff(inputs={
            "feedback": self.state.feedback or "No feedback yet",
            "length": self.request.length,
            "keywords": self.request.keywords,
            "tone": self.request.tone,
            "post": self.request.post,
        })

        self.state.generated_post = result["generated_posts"]

    @router(generate_linkedin_post)
    def evaluate_linkedin_Post(self):
        if self.retry_count > 2:
            return "max_retry_exceeded"

        try:
            agent = Agent(**AGENTS["post_validator"], llm=self.llm)
            task = Task(config=TASKS["post_validation_task"], agent=agent, output_json=ValidationResult)
            crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

            result = crew.kickoff(inputs={
                "length": self.request.length,
                "keywords": self.request.keywords,
                "tone": self.request.tone,
                "post": self.state.generated_post,
            })

            self.state.valid = result["valid"]
            self.state.feedback = result["feedback"]

        except Exception as e:
            self.state.valid = False
            self.state.feedback = f"Evaluation error: {str(e)}"

        self.retry_count += 1
        return "completed" if self.state.valid else "retry"

    @listen("completed")
    def save_result(self):
        pass

    @listen("max_retry_exceeded")
    def max_retry_exceeded_exit(self):
        pass


class PostController:
    def execute_flow(self, request: LinkedInPostRequest):
        try:
            flow = LinkedinPostFlow(request)
            flow._fetch_activities()
            flow.kickoff()
            if not flow.state.generated_post:
                raise ValueError("Post generation failed")
            return flow.state.generated_post
        except Exception as e:
            logger.error(f"Flow execution failed: {e}", exc_info=True)
            raise

    def custom_post(self, request: LinkedinCustomPostRequest):
        try:
            flow = LinkedInCustomPostFlow(request)
            flow.kickoff()
            return flow.state.generated_post
        except Exception as e:
            logger.error(f"Flow execution failed: {e}", exc_info=True)
            raise
    
    def get_linkedin_profile_data(self, request: RapidAPIRequest):
        try:
            print(request.profile_url)
            self.rapidapi_key = get_env("RAPIDAPI_KEY")
            response = requests.get(
                "https://linkedin-api8.p.rapidapi.com/get-profile-data-by-url",
                headers={
                    "x-rapidapi-key": self.rapidapi_key,
                    "x-rapidapi-host": "linkedin-api8.p.rapidapi.com"
                },
                params={"url": request.profile_url}
            )
            if response.status_code != 200:
                raise ConnectionError("Failed to fetch LinkedIn activities")
            else:
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching LinkedIn profile data: {e}", exc_info=True)
            raise
