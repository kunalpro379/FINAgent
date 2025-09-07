
import os
import sys
import asyncio
import logging
import argparse
from agno.models.groq import Groq
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import ClientSession
from typing import Optional
from contextlib import AsyncExitStack
from mcp.client.sse import sse_client
from dotenv import load_dotenv

# Silence all logging
class SilentFilter(logging.Filter):
    def filter(self, record):
        return False

# Configure root logger to be silent
root_logger = logging.getLogger()
root_logger.addFilter(SilentFilter())
root_logger.setLevel(logging.CRITICAL)

# Silence specific loggers
for logger_name in ['agno', 'httpx', 'urllib3', 'asyncio']:
    logger = logging.getLogger(logger_name)
    logger.addFilter(SilentFilter())
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False

# Redirect stdout/stderr for the agno library
class DevNull:
    def write(self, msg): pass
    def flush(self): pass

sys.stderr = DevNull()

load_dotenv()

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        # Store the context managers so they stay alive
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        # Initialize
        await self.session.initialize()

        # List available tools to verify connection
        response = await self.session.list_tools()

    async def cleanup(self):
        """Properly clean up the session and streams"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    async def disconnect(self):
        """Disconnect from the MCP server"""
        await self.cleanup()

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MCP Client')
    parser.add_argument('--host', help='MCP server host (default: localhost)')
    parser.add_argument('--port', type=int, help='MCP server port (default: 4032)')
    args = parser.parse_args()

    # Get MCP host and port from args or environment variables
    mcp_host = args.host or "localhost"
    mcp_port = args.port or 4032  # Force port 4032 to match server
    mcp_url = f"http://{mcp_host}:{mcp_port}/sse"

    print(f"🔗 Connecting to MCP server at: {mcp_url}")
    
    try:
        mcp_client = MCPClient()
        await mcp_client.connect_to_sse_server(mcp_url)
        print("✅ Successfully connected to MCP server!")
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {str(e)}")
        print("💡 Make sure your MCP server is running on the specified host and port")
        return

    # List available tools
    print("🔧 Initializing MCP tools...")
    try:
        response = await mcp_client.session.list_tools()
        print(f"📋 Found {len(response.tools)} available tools")
        mcp_tools = MCPTools(session=mcp_client.session)
        await mcp_tools.initialize()
        print("✅ MCP tools initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize MCP tools: {str(e)}")
        return

    # Create the Agno agent
    print("🤖 Creating Agno agent with Groq Llama 8B...")
    try:
        agent = Agent(
        instructions="""
You are a Zerodha Trading Account Assistant, helping users securely manage their accounts, orders, portfolio, and positions using tools provided over MCP.

# Important Instructions:
- ALWAYS respond in plain text. NEVER use markdown formatting (no asterisks, hashes, or code blocks).
- Respond in human-like conversational, friendly, and professional tone in concise manner.
- ALWAYS show a menu with numbered options when the user starts or asks for help.

# Menu System:
When user starts or asks for help, ALWAYS show this menu:
1. Login to Zerodha Account
2. Check Portfolio Holdings
3. View Current Positions
4. Check Available Margins
5. Place New Order
6. View Today's Orders
7. Check User Profile
8. Exit

# Authentication Process:
- When user selects option 1, IMMEDIATELY call get_login_url() and display the URL clearly
- Ask user to visit the URL, login, and provide the request token
- When user provides request token, call get_access_token() with the token
- Confirm authentication success

# Responsibilities:
- Assist with order placement ('place_order'), modification ('modify_order'), and cancellation ('cancel_order').
- Provide insights on portfolio holdings ('get_holdings'), positions ('get_positions'), and available margin ('get_margins').
- Track order status ('get_orders'), execution details ('get_order_trades'), and trade history ('get_order_history').
- Check user profile ('get_user_profile') when needed.

# Limitations:
You do not provide real-time market quotes, historical data, or financial advice. Your role is to ensure secure, efficient, and compliant account management.
""",
        model=Groq(
            id="llama-3.1-8b-instant"
        ),
        add_history_to_messages=True,
        num_history_responses=10,
        tools=[mcp_tools],
        show_tool_calls=False,
        markdown=False,
        read_tool_call_history=True,
        read_chat_history=True,
        tool_call_limit=10,
        telemetry=False,
        add_datetime_to_instructions=True
    )
        print("✅ Agno agent created successfully!")
    except Exception as e:
        print(f"❌ Failed to create Agno agent: {str(e)}")
        return

    # Welcome message
    print("\n" + "="*60)
    print("🤖 Zerodha Trading Assistant")
    print("="*60)
    print("Welcome! I'm here to help you manage your trading account.")
    print("Type 'quit' or 'exit' to stop the chatbot.")
    print("="*60 + "\n")

    try:
        while True:
            # Get user input
            user_query = input("You: ").strip()
            
            # Check if user wants to quit
            if user_query.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye! Happy trading! 🚀")
                break
            
            if not user_query:
                continue

            print("\nAssistant: ", end="", flush=True)

            # Run the agent and stream the response
            result = await agent.arun(user_query, stream=True)
            async for response in result:
                if response.content:
                    print(response.content, end="", flush=True)

            print("\n" + "-"*60 + "\n")

    except KeyboardInterrupt:
        print("\n\nGoodbye! Happy trading! 🚀")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        # Disconnect from the MCP server
        await mcp_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())