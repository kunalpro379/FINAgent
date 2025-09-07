import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")), "data"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "groq",  # Changed to groq as default
    "deep_think_llm": "llama-3.3-70b-versatile",
    "quick_think_llm": "llama-3.3-70b-versatile",
    "backend_url": "https://api.groq.com/openai/v1",  # Changed to groq
    # Vector database settings
    "use_vector_db": True,
    "use_local_embeddings": True,  # Use local sentence-transformers instead of API calls
    # Debate and discussion settings
    "max_debate_rounds": 2,
    "max_risk_discuss_rounds": 2,
    "max_recur_limit": 100,
    # Tool settings
    "online_tools": True,
}