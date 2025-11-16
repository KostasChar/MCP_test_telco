import os
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient

load_dotenv()
logging.getLogger("mcp_use").setLevel(logging.ERROR)

async def create_gemini_agent():
    """Create an MCPAgent using Google Gemini backend."""
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

    client = MCPClient({
        "mcpServers": {"http": {"url": MCP_SERVER_URL}}
    })
    await client.create_session("http")

    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0,
        google_api_key=GOOGLE_API_KEY,
    )

    PROMPT = """
    You are an intelligent assistant that uses available tools to respond to user requests.
    1. Identify the appropriate tool.
    2. Summarize the tool's result naturally.
    3. Offer helpful next steps.
    """

    agent = MCPAgent(
        client=client,
        max_steps=10,
        system_prompt=PROMPT,
        llm=llm,
        max_retries_per_step=3,
        verbose=True,
    )
    return agent
