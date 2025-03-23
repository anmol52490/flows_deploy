import asyncio
import logging
import re
import requests
import json
from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow import Flow, listen, start, router
from models import  LinkedInPostRequest,LinkedInPostAnalysis,LinkedInPostGeneration, LinkedInState
from utils import load_yaml_config, get_env, clean_text
import os
from utils import CharacterCounterTool
# Load configurations
AGENTS = load_yaml_config("config/agents.yaml")
TASKS = load_yaml_config("config/tasks.yaml")

logger = logging.getLogger(__name__)

class LinkedinPostFlow(Flow[LinkedInState]):
    def __init__(self, request: LinkedInPostRequest):
        super().__init__(state=(LinkedInState))
        self.request = request
        self.rapidapi_key = get_env("RAPIDAPI_KEY")
        self.gemini_key = get_env("GEMINI_API_KEY")
        self.llm = LLM(
            model="gemini/gemini-2.0-flash-lite",
            temperature=0.7,
            api_key=self.gemini_key
        )
        self.cached_report = None
        self.cached_activities = None
        self.static_linkedin_post = request.static_post
        

    def _extract_username(self):
        match = re.search(r"https://www\.linkedin\.com/in/([^/]+)", str(self.request.profile_url))
        if not match:
            raise ValueError("Invalid LinkedIn URL format")
        return match.group(1)

    def _fetch_activities(self):

        # if os.path.exists("act.json"):
        #     try:
        #         with open("act.json", "r") as json_file:
        #             self.cached_activities = json.load(json_file)
        #         logger.info("✅ Successfully loaded LinkedIn activities from act.json")
        #         return  # Exit the function if we successfully read the file
        #     except Exception as e:
        #         logger.warning("⚠️ Failed to read act.json: %s", str(e))
        username = self._extract_username()
        response = requests.get(
            "https://linkedin-api8.p.rapidapi.com/get-profile-posts",
            headers={
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": "linkedin-api8.p.rapidapi.com"
            },
            params={"username": username}
        )
        
        if response.status_code == 200:
            raw_data = response.json().get("data") or []
            self.cached_activities = [
                {
                    "text": clean_text(post.get("text", "")),
                    "totalReactionCount": post.get("totalReactionCount", 0),
                    "commentsCount": post.get("commentsCount", 0)
                }
                for post in sorted(raw_data, 
                                key=lambda x: x.get("postedDate", 0), 
                                reverse=True)[:5]
            ]
            logger.info("✅ Successfully fetched LinkedIn activities")
        
            with open("act.json", "w") as json_file:
                json.dump(self.cached_activities, json_file, indent=4)
        
            logger.info("✅ Successfully fetched LinkedIn activities and saved to act.json")

        else:
            raise ConnectionError("Failed to fetch LinkedIn activities")


    @start()
    def analysis_phase(self):
        if not self.cached_activities:
            raise RuntimeError("LinkedIn activities not loaded. Make sure _fetch_activities() was successful.")

        logger.info("🚀 Starting generation phase")
        
        if self.cached_report is None:
            
            logger.info("🔍 Performing initial trend analysis")
            trend_analyzer = Agent(**AGENTS["linkedin_post_analysis_agent"], llm=self.llm)
            analysis_task = Task(
                config=TASKS["trend_analysis_task"],
                agent=trend_analyzer,
                output_json=LinkedInPostAnalysis
            )
            
            analysis_crew = Crew(
                agents=[trend_analyzer],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=True
            )
            
            crew_output = analysis_crew.kickoff(inputs={"activities": self.cached_activities})
            print("Hi--")
            # Convert CrewOutput to dict, then parse into your model
            result_dict = crew_output
            print(result_dict)
            
            analysis_result = result_dict
            print(analysis_result)
            self.state.analysed_post = {
                "writing_style": analysis_result["writing_style"],
                "personal_touch": analysis_result["personal_touch"],
                "target_audience": analysis_result["target_audience"]
            }
            
        
   
    @listen(analysis_phase)
    def generation_phase(self):
        # Post generation with cached analysis
        post_generator = Agent(**AGENTS["post_generation_agent"], llm=self.llm,
                               )
        generation_task = Task(
            config=TASKS["post_generation_task"],
            agent=post_generator,
            output_json=LinkedInPostGeneration
        )

        generation_crew = Crew(
            agents=[post_generator],
            tasks=[generation_task],
            process=Process.sequential,
            verbose=True
        )
        
            # Use a simple dictionary with a single key if analysis result can't be unpacked
        # inputs = {"analysis_result": str(self.state.analysed_post)}
        result = generation_crew.kickoff(
            inputs = {
                "static_linkedin_post": self.static_linkedin_post,
                "writing_style": self.state.analysed_post["writing_style"],
                "personal_touch": self.state.analysed_post["personal_touch"],
                "target_audience": self.state.analysed_post["target_audience"],
            }
                
        )
        
        # Enhanced JSON processing
        try:
            # raw_output = result
            # clean_json = re.sub(r'^```json|```$', '', raw_output, flags=re.MULTILINE)
            # parsed = json.loads(clean_json.strip())
            
            # if not isinstance(parsed, list) or len(parsed) != 4:
            #     raise ValueError("Exactly 4 posts required")
                
            self.state.generated_post = [
            {
                "post_heading": post["post_heading"],
                "post_content": post["post_content"]
            }
            for post in result["generated_posts"]
        ]
            logger.debug("✅ Generated posts validated structurally")
            
        except Exception as e:
            logger.error(f"Post generation failed: {str(e)}")
            

class PostController:
    def execute_flow(self, request: LinkedInPostRequest):
        try:
            logger.info("🔧 Initializing LinkedinPostFlow")
            flow = LinkedinPostFlow(request)
            
            logger.info("📥 Fetching LinkedIn activities")
            flow._fetch_activities()

            logger.info("⚙️ Starting flow execution")
            flow.kickoff()
            if not flow.state.generated_post:
                raise ValueError("Post generation failed or returned no posts.")


            generated_posts = []
            if flow.state.generated_post:
                for post in flow.state.generated_post:
                    # If post is an object with attributes
                    generated_posts.append({
                    "post_heading": post.get("post_heading", ""),
                    "post_content": post.get("post_content", "")
                })
                    
            logger.debug(f"Generated posts: {generated_posts}")
            return generated_posts

        except Exception as e:
            logger.error(f"🔴 Flow execution failed: {str(e)}", exc_info=True)
            raise