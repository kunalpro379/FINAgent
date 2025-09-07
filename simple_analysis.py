#!/usr/bin/env python3
"""
Simple FINAgent Analysis - Minimal API Usage
This script uses the cheapest Groq model with minimal API calls
"""

import time
from default_config import DEFAULT_CONFIG
from Langgraph.TradingAgentGraph import TradingAgentsGraph

# Configure for minimal API usage
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "groq"
config["backend_url"] = "https://api.groq.com/openai/v1"
config["deep_think_llm"] = "llama-3.1-8b-instant"  # Cheapest model
config["quick_think_llm"] = "llama-3.1-8b-instant"  # Cheapest model
config["max_debate_rounds"] = 0  # No debates
config["max_risk_discuss_rounds"] = 0  # No risk discussions
config["online_tools"] = False  # No online tools
config["max_tokens"] = 200  # Very short responses
config["temperature"] = 0.1  # Focused responses

# Create directories
import os
os.makedirs("data", exist_ok=True)
os.makedirs("data/reddit_data", exist_ok=True)
os.makedirs("data/reddit_data/company_news", exist_ok=True)
os.makedirs("data/reddit_data/global_news", exist_ok=True)
os.makedirs("dataflows/data_cache", exist_ok=True)

print("🚀 Starting Simple FINAgent Analysis...")
print("💰 Using cheapest Groq model: llama-3.1-8b-instant")
print("⏱️  Cost: ₹0.37 per day (10x cheaper than 70B model)")
print("📊 Analysis: Market indicators only")
print("⏳ Waiting 10 seconds to avoid rate limits...")

time.sleep(10)

# Initialize with minimal configuration
ta = TradingAgentsGraph(
    selected_analysts=["market"],  # Only market analysis
    debug=False,  # No debug output
    config=config
)

print("🔍 Analyzing NVDA...")
_, decision = ta.propagate("NVDA", "2025-06-01")

print("\n" + "="*50)
print("🎯 FINAL TRADING DECISION:")
print("="*50)
print(decision)
print("="*50)
print("✅ Analysis complete!")
print("💰 Total cost: ~₹0.01 (very cheap!)")
