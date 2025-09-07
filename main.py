import asyncio
import logging
from datetime import datetime
from default_config import DEFAULT_CONFIG
from Langgraph.TradingAgentGraph import TradingAgentsGraph

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "groq"  # Use Groq model
config["backend_url"] = "https://api.groq.com/openai/v1"  # Use Groq backend
config["deep_think_llm"] = "llama-3.1-8b-instant"  # Much cheaper model
config["quick_think_llm"] = "llama-3.1-8b-instant"  # Much cheaper model
config["max_debate_rounds"] = 0  # Disable debate to reduce API calls
config["max_risk_discuss_rounds"] = 0  # Disable risk discussion to reduce API calls
config["online_tools"] = False  # Disable online tools to avoid rate limiting
config["max_tokens"] = 1000  # Limit response length to reduce token usage
config["temperature"] = 0.1  # Lower temperature for more focused responses

# Create necessary directories
import os
os.makedirs("data", exist_ok=True)
os.makedirs("data/reddit_data", exist_ok=True)
os.makedirs("data/reddit_data/company_news", exist_ok=True)
os.makedirs("data/reddit_data/global_news", exist_ok=True)
os.makedirs("dataflows/data_cache", exist_ok=True)

# Initialize with custom config - only use market analyst to reduce API calls
ta = TradingAgentsGraph(
    selected_analysts=["market"],  # Only market analysis to minimize token usage
    debug=True, 
    config=config
)

# forward propagate with a more recent date to reduce data size
_, decision = ta.propagate("NVDA", "2025-06-01")
print(decision)
