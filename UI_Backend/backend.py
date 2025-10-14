import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
from quart import Quart, request, jsonify, Response
from quart_cors import cors
import json
import asyncio
from gemini_mcp import agent as gemini_agent
# Import Ollama agent (assumed to be configured similarly)
try:
    from ollama_mcp import agent as ollama_agent
except ImportError:
    ollama_agent = None



# Quart app
app = Quart(__name__)
app = cors(app, allow_origin="*")

# Helper function to create SSE formatted messages
def format_sse(data: str, event: str = None) -> str:
    msg = f"data: {data}\n"
    if event:
        msg = f"event: {event}\n{msg}"
    return f"{msg}\n"


# Async generator for streaming responses
async def stream_agent_response(agent, query):
    try:
        # Check if agent has astream method
        if hasattr(agent, 'astream'):
            # Stream the agent response
            async for chunk in agent.astream(query):
                # Handle different chunk formats
                if hasattr(chunk, 'content'):
                    yield format_sse(json.dumps({"chunk": chunk.content}))
                elif isinstance(chunk, dict):
                    yield format_sse(json.dumps({"chunk": chunk.get("output", str(chunk))}))
                else:
                    yield format_sse(json.dumps({"chunk": str(chunk)}))

                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
        else:
            # Fallback: use run() and send as single chunk
            result = await agent.run(query)
            # Send result in small chunks to simulate streaming
            chunk_size = 50
            result_str = str(result)
            for i in range(0, len(result_str), chunk_size):
                chunk = result_str[i:i + chunk_size]
                yield format_sse(json.dumps({"chunk": chunk}))
                await asyncio.sleep(0.05)

        # Send completion signal
        yield format_sse(json.dumps({"done": True}), event="complete")

    except Exception as e:
        yield format_sse(json.dumps({"error": str(e)}), event="error")


# Non-streaming endpoint (backwards compatible)
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


# Streaming endpoint for Gemini
@app.route("/gemini-mcp/stream", methods=["POST"])
async def gemini_stream_endpoint():
    data = await request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    return Response(
        stream_agent_response(gemini_agent, query),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# Non-streaming Ollama endpoint (backwards compatible)
@app.route("/ollama-mcp", methods=["POST"])
async def ollama_mcp_endpoint():
    if not ollama_agent:
        return jsonify({"error": "Ollama agent not available"}), 500

    data = await request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        result = await ollama_agent.run(query)
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Streaming endpoint for Ollama
@app.route("/ollama-mcp/stream", methods=["POST"])
async def ollama_stream_endpoint():
    if not ollama_agent:
        return jsonify({"error": "Ollama agent not available"}), 500

    data = await request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    return Response(
        stream_agent_response(ollama_agent, query),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9009)