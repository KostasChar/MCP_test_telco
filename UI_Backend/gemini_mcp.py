import os
from dotenv import load_dotenv
from mcp_use import MCPClient, MCPAgent
from langchain_google_genai import ChatGoogleGenerativeAI

# Optional Ollama agent
try:
    from ollama_mcp import agent as ollama_agent_class
except ImportError:
    ollama_agent_class = None

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

if not GOOGLE_API_KEY or not MODEL_NAME or not MCP_SERVER_URL:
    raise ValueError("GOOGLE_API_KEY, GEMINI_MODEL_NAME, and MCP_SERVER_URL must be set in .env")

# System prompt for MCPAgent
PROMPT = """
You are an intelligent assistant that uses available tools to respond to user requests.

Instructions:
1. Identify the appropriate tool for the task.
2. Respond with the tool's result in natural language summarizing.
3. Provide any helpful context or next steps based on the result.
 
"""


llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0, google_api_key=GOOGLE_API_KEY)



def create_ollama_agent():
    if not ollama_agent_class:
        raise RuntimeError("Ollama agent not available")
    # Add any required constructor args here if needed
    return ollama_agent_class()

