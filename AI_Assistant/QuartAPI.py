import os
from quart import Quart, request, jsonify
from quart_cors import cors
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient

# Load env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env")

# Quart app
app = Quart(__name__)
app = cors(app, allow_origin="*")  # allow React frontend

# MCP + Gemini setup
config = {"mcpServers": {"http": {"url": "http://localhost:8000/mcp"}}}
client = MCPClient(config)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)
agent = MCPAgent(client=client, llm=llm)

# Async route
@app.route("/query", methods=["POST"])
async def query_endpoint():
    data = await request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    try:
        result = await agent.run(query)  # ✅ safe, single event loop
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9009)
