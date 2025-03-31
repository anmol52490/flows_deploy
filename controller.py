import re
import json
import requests
import logging
from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow import Flow, listen, start
from models import LinkedInPostRequest, LinkedInPostAnalysis, LinkedInPostGeneration, LinkedInState
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
            temperature=0.7,
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
        with open("act.json", "w") as f:
            json.dump(self.cached_activities, f, indent=4)

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

        self.state.generated_post = [
            {
                "post_heading": post["post_heading"],
                "post_content": post["post_content"]
            } for post in result["generated_posts"]
        ]

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
