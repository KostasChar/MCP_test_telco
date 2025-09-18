import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient

async def main():
    """Run the example using a configuration file."""
    # Load environment variables
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    # Configuration for MCP
    config = {
        "mcpServers": {
            "http": {
                "url": "http://localhost:8000/mcp"
            }
        }
    }

    # Initialize MCP client
    client = MCPClient(config)

    # Initialize Gemini LLM (Chat model)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=google_api_key
    )

    # Wrap in an MCP agent
    agent = MCPAgent(client=client, llm=llm)

    # Example query
    response = await agent.run("Get user location with id 1234123")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
