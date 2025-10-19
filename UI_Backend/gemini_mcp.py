import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env")
if not MODEL_NAME:
    raise ValueError("MODEL_NAME not found in .env")
if not MCP_SERVER_URL:
    raise ValueError("MCP_SERVER_URL not found in .env")

# MCP + Gemini setup
config = {"mcpServers": {"http": {"url": MCP_SERVER_URL}}}
client = MCPClient(config)

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=1,
    google_api_key=GOOGLE_API_KEY,
)

# Exported agent
agent = MCPAgent(client=client, llm=llm)
