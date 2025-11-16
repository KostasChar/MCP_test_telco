import os
import json
import asyncio
import logging
from quart import Quart, request, jsonify, Response
from quart_cors import cors
from dotenv import load_dotenv
import objgraph

from agents.gemini_agent import create_gemini_agent
from agents.groq_agent import create_groq_agent

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Quart app
app = Quart(__name__)
app = cors(app, allow_origin="*")


# --- SSE Helper ---
def sse_event(data, event="message", id=None, retry=None):
    lines = []
    if id is not None:
        lines.append(f"id: {id}")
    if event is not None:
        lines.append(f"event: {event}")
    if retry is not None:
        lines.append(f"retry: {retry}")

    if isinstance(data, str):
        for line in data.splitlines():
            lines.append(f"data: {line}")
    else:
        json_data = json.dumps(data)
        for line in json_data.splitlines():
            lines.append(f"data: {line}")

    return "\n".join(lines) + "\n\n"


# --- Common SSE Stream Helper ---
async def stream_agent_response(agent, query):
    chunk_size = 50
    async def generator():
        event_id = 0
        try:
            result = await agent.run(query)
            for i in range(0, len(result), chunk_size):
                yield sse_event({"chunk": result[i:i + chunk_size]}, id=event_id)
                event_id += 1
                await asyncio.sleep(0.01)
            yield sse_event({"done": True}, event="complete", id=event_id)
        except Exception as e:
            yield sse_event({"error": str(e)}, event="error", id=event_id)
        finally:
            await agent.close()
            logging.info("Agent closed after streaming")
    return generator


# --- GEMINI ROUTES ---
@app.route("/gemini-mcp", methods=["POST"])
async def gemini_query():
    data = await request.get_json()
    query = data.get("query") if data else None
    if not query:
        return jsonify({"error": "No query provided"}), 400

    agent = await create_gemini_agent()
    try:
        result = await agent.run(query)
        return jsonify({"response": result})
    except Exception as e:
        logging.error(f"Error in gemini_query: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        await agent.close()


@app.route("/gemini-mcp/stream", methods=["GET"])
async def gemini_stream():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    agent = await create_gemini_agent()
    generator = await stream_agent_response(agent, query)
    return Response(
        generator(),
        content_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


# --- GROQ ROUTES ---
@app.route("/groq-mcp", methods=["POST"])
async def groq_query():
    data = await request.get_json()
    query = data.get("query") if data else None
    if not query:
        return jsonify({"error": "No query provided"}), 400

    agent = await create_groq_agent()
    try:
        result = await agent.run(query)
        return jsonify({"response": result})
    except Exception as e:
        logging.error(f"Error in groq_query: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        await agent.close()


@app.route("/groq-mcp/stream", methods=["GET"])
async def groq_stream():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    agent = await create_groq_agent()
    generator = await stream_agent_response(agent, query)
    return Response(
        generator(),
        content_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


# --- HEALTH + DEBUG ---
@app.route("/health", methods=["GET"])
async def health_check():
    return jsonify({
        "status": "healthy",
        "service": "mcp",
        "mcp_server": os.getenv("MCP_SERVER_URL"),
        "models": {
            "gemini": os.getenv("GEMINI_MODEL_NAME"),
            "groq": os.getenv("GROQ_MODEL_NAME")
        }
    })


@app.route("/debug/objgraph", methods=["GET"])
async def debug_objgraph():
    import io, sys
    buf = io.StringIO()
    sys.stdout = buf
    objgraph.show_growth(limit=10)
    sys.stdout = sys.__stdout__
    return Response(buf.getvalue(), mimetype="text/plain")


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "9013"))
    app.run(host=host, port=port, debug=False, use_reloader=False)
