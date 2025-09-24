
from quart import Quart, request, jsonify
from quart_cors import cors
from ollama_mcp import agent as ollama_agent  # Import Ollama-specific agent
from gemini_mcp import agent as gemini_agent  # Import Gemini specific agent
# Quart app
app = Quart(__name__)
app = cors(app, allow_origin="*")  # Allow React frontend

# Async route for generic agent
@app.route("/gemini-mcp", methods=["POST"])
async def query_endpoint():
    data = await request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        result = await gemini_agent.run(query)
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Async route for Ollama MCP agent
@app.route("/ollama-mcp", methods=["POST"])
async def ollama_mcp_endpoint():
    data = await request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        result = await ollama_agent.run(query)
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9009)
