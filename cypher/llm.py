"""
Top-level Wrapper for LLM Setup & Adzuna API Integration.
"""

from src.llm import get_llm_model, get_adzuna_config, ADZUNA_APP_ID, ADZUNA_APP_KEY, OLLAMA_MODEL

if __name__ == "__main__":
    print("=== LLM & ADZUNA API MODULE CHECK ===")
    print("Configured Ollama Model:", OLLAMA_MODEL)
    print("Adzuna App ID Configured:", "YES" if ADZUNA_APP_ID else "NO (Optional)")
    print("Adzuna App Key Configured:", "YES" if ADZUNA_APP_KEY else "NO (Optional)")
    llm = get_llm_model()
    print("LLM Status:", "ChatOllama Connected" if llm else "Deterministic Fallback Synthesis Ready")
