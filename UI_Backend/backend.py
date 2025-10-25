import os
import json
import asyncio
from dotenv import load_dotenv
from quart import Quart, request, jsonify, Response
from quart_cors import cors
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
from gemini_mcp import agent as gemini_agent

# Optional Ollama agent
try:
    from ollama_mcp import agent as ollama_agent
except ImportError:
    ollama_agent = None


# Quart app
app = Quart(__name__)
app = cors(app, allow_origin="*")


# Helper: SSE-compliant message builder
def sse_event(data: dict | str, event: str | None = None, id: int | None = None) -> str:
    """Format a proper SSE event."""
    msg = ""
    if id is not None:
        msg += f"id: {id}\n"
    if event is not None:
        msg += f"event: {event}\n"
    # JSON-encode if it's a dict
    if isinstance(data, (dict, list)):
        data = json.dumps(data)
    # According to SSE spec: each data line must start with "data:"
    for line in str(data).splitlines():
        msg += f"data: {line}\n"
    msg += "\n"
    return msg


# Streaming generator
async def stream_agent_response(agent, query):
    """Yields properly formatted SSE events."""
    try:
        event_id = 0

        if hasattr(agent, "astream"):
            async for chunk in agent.astream(query):
                if hasattr(chunk, "content"):
                    payload = {"chunk": chunk.content}
                elif isinstance(chunk, dict):
                    payload = {"chunk": chunk.get("output", str(chunk))}
                else:
                    payload = {"chunk": str(chunk)}

                yield sse_event(payload, event="message", id=event_id)
                event_id += 1
                await asyncio.sleep(0.01)
        else:
            # fallback: single full response
            result = await agent.run(query)
            for i in range(0, len(result), 100):
                yield sse_event({"chunk": result[i:i+100]}, event="message", id=event_id)
                event_id += 1
                await asyncio.sleep(0.05)

        yield sse_event({"done": True}, event="complete", id=event_id)

    except Exception as e:
        yield sse_event({"error": str(e)}, event="error")


# --- Non-streaming Gemini endpoint ---
@app.route("/gemini-mcp", methods=["POST"])
async def gemini_query():
    data = await request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        result = await gemini_agent.run(query)
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Streaming Gemini endpoint ---
@app.route("/gemini-mcp/stream", methods=["POST"])
async def gemini_stream():
    data = await request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    return Response(
        stream_agent_response(gemini_agent, query),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # For NGINX compatibility
        },
    )


# --- Non-streaming Ollama endpoint ---
@app.route("/ollama-mcp", methods=["POST"])
async def ollama_query():
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


# --- Streaming Ollama endpoint ---
@app.route("/ollama-mcp/stream", methods=["POST"])
async def ollama_stream():
    if not ollama_agent:
        return jsonify({"error": "Ollama agent not available"}), 500

    data = await request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    return Response(
        stream_agent_response(ollama_agent, query),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9009)
