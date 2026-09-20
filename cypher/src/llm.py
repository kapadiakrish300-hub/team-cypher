"""
LLM Setup & Provider Configuration Module for Patient Record Simplifier & Health Companion Agent.
Configures ChatOllama (target model qwen2.5:0.5b or qwen3:0.6b), handles API key loading (Adzuna, OpenAI, etc.),
and provides fallback LLM synthesis.
"""

import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Environment Configurations
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_llm_model(model_name: Optional[str] = None, base_url: Optional[str] = None):
    """
    Initializes ChatOllama model if server is reachable, otherwise returns None for fallback synthesis.
    """
    target_model = model_name or OLLAMA_MODEL
    target_url = base_url or OLLAMA_BASE_URL

    try:
        res = requests.get(f"{target_url}/api/tags", timeout=1.5)
        if res.status_code == 200:
            from langchain_ollama import ChatOllama
            print(f"[LLM] Initialized ChatOllama with model '{target_model}'")
            return ChatOllama(
                model=target_model,
                base_url=target_url,
                temperature=0.2
            )
    except Exception as e:
        print(f"[LLM] ChatOllama server not reachable at {target_url}. Using fallback synthesis: {e}")

    return None


def get_adzuna_config() -> Dict[str, str]:
    """
    Returns configured Adzuna API credentials.
    """
    return {
        "app_id": os.getenv("ADZUNA_APP_ID", ""),
        "app_key": os.getenv("ADZUNA_APP_KEY", "")
    }
