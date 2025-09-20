from quart import Quart, request, jsonify
from quart_cors import cors
from ai_mcp import agent  # Import the AI agent

# Quart app
app = Quart(__name__)
app = cors(app, allow_origin="*")  # allow React frontend

# Async route
@app.route("/query", methods=["POST"])
async def query_endpoint():
    data = await request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    try:
        result = await agent.run(query)  # use imported agent
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9009)
