import os
import yaml
import re
from dotenv import load_dotenv

load_dotenv()

def load_yaml_config(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing environment variable: {key}")
    return value

def clean_text(text: str) -> str:
    return re.sub(r'[^\x00-\x7F]+', '', text)
