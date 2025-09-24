import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from mcp_use import MCPAgent, MCPClient

# Load environment variables
load_dotenv()

# Env variables
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

# Validation
if not OLLAMA_MODEL:
    raise ValueError("OLLAMA_MODEL not found in .env")
if not MCP_SERVER_URL:
    raise ValueError("MCP_SERVER_URL not found in .env")

# MCP setup
config = {"mcpServers": {"http": {"url": MCP_SERVER_URL}}}
client = MCPClient(config)

# Ollama LLM setup
llm = ChatOllama(
    model=OLLAMA_MODEL,
    temperature=1,
)

# Exported agent
agent = MCPAgent(client=client, llm=llm)
