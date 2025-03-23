import os
import yaml
import re
from dotenv import load_dotenv
from typing import Dict, Any
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CharacterCounterInput(BaseModel):
    """Input schema for CharacterCounterTool."""

    text: str = Field(..., description="The string to count characters in.")


class CharacterCounterTool(BaseTool):
    name: str = "Character Counter Tool"
    description: str = "Counts the number of characters in a given string."
    args_schema: Type[BaseModel] = CharacterCounterInput

    def _run(self, text: str) -> str:
        character_count = len(text)
        return f"The input string has {character_count} characters."

load_dotenv()

def load_yaml_config(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing environment variable: {key}")
    return value

def clean_text(text: str) -> str:
    return re.sub(r'[^\x00-\x7F]+', '', text)