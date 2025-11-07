import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient

load_dotenv()
logging.getLogger("mcp_use").setLevel(logging.ERROR)

async def create_groq_agent():
    """Create an MCPAgent using Groq backend."""
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "deepseek-r1-distill-llama-70b")

    client = MCPClient({
        "mcpServers": {"http": {"url": MCP_SERVER_URL}}
    })
    await client.create_session("http")

    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=0,
        max_tokens=None,
        reasoning_format="parsed",
        timeout=None,
        max_retries=2,
        api_key=GROQ_API_KEY
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
