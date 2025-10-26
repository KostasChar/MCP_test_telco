import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from mcp_use import MCPAgent, MCPClient

# Load environment variables
load_dotenv()

# Env variables
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_NAME")
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

prompt = f"""
You are an intelligent assistant that must always use the tool
to respond to any user request. 

Instructions:
1. Begin by acknowledging the user's request clearly.
2. Explain briefly why is the most appropriate tool for this task.
3. Use the tool to generate the output or solution.
4. Provide any extra helpful information or clarification after using the tool.
5. Always conclude with a summary of what the tool produced and any next steps.

"""

# Exported agent
agent = MCPAgent(client=client, system_prompt=prompt, llm=llm)
